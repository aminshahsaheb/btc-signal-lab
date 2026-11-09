"""D-LIQ G-1 (draft): CANDLE provenance -- shared kline-frame parser and reference CANDLE checker.

STATUS: DRAFT, not locked, not integrated into any verifier. Python 3 standard library only. Opens no socket and reads no market data.
Written from GPT's audit of 2026-11-07 (section A) and docs/G1_CANDLE_CONTRACT_PROPOSAL.md. Every field name of the exchange frame is
marked [VERIFY]: it follows the public documentation / a third-party client, NOT a real capture (the exchange is unreachable from the
owner's location). Parameters that GPT left open (the maximum receipt lag) are explicit arguments with NO default.

parse_kline_frame(raw)  -> {"ok": True, ...parsed values...} | {"ok": False, "reason": <code>}
candle_checks(events, max_lag_ms)  -> (findings, candles, refs)   reference implementation of the CANDLE rules of the proposal (section 3).
"""
import base64
import json
import re
from decimal import Decimal

EXPECTED_STREAM = "btcusdt@kline_1m"      # [VERIFY] stream name of the 1-minute kline subscription
SYMBOL = "BTCUSDT"
INTERVAL = "1m"
MINUTE_MS = 60_000
TS_MIN = 1_700_000_000_000                # same bounds as the message contract (dliq_msg_contract_v1)
TS_MAX = 4_102_444_800_000
DEC_RE = re.compile(r"(0|[1-9][0-9]*)(\.[0-9]+)?")
CLOCK_UNCERTAINTY_MS = 250                # = max_clock_offset_ms of the message contract; the clock offset is bounded by it
HARD_NAMES = ("CANDLE_LINK", "CANDLE_PARSE", "CANDLE_FIELD_MISMATCH", "CANDLE_CONFLICT", "CANDLE_NOT_LIVE", "CANDLE_LAG_UNSET")


class _Dup(Exception):
    pass


def _no_dups(pairs):
    d = {}
    for k, v in pairs:
        if k in d:
            raise _Dup(k)
        d[k] = v
    return d


def _bad_const(x):
    raise ValueError("non-finite JSON constant " + x)


def _is_int(x):
    return isinstance(x, int) and not isinstance(x, bool)


def _fail(reason):
    return {"ok": False, "reason": reason}


def parse_kline_frame(raw, expected_stream=EXPECTED_STREAM):
    """Parse ONE recorded kline frame (bytes). Accepts the raw stream form {"e":"kline",...} and the combined-stream form
    {"stream": <expected_stream>, "data": {...}}; rejects everything else (REST arrays, other events, other streams/symbols/intervals)."""
    if not isinstance(raw, (bytes, bytearray)):
        return _fail("not_bytes")
    try:
        text = bytes(raw).decode("utf-8", errors="strict")
    except Exception:
        return _fail("utf8")
    try:
        top = json.loads(text, object_pairs_hook=_no_dups, parse_constant=_bad_const)
    except _Dup:
        return _fail("duplicate_key")
    except Exception:
        return _fail("json")
    if isinstance(top, list):
        return _fail("rest_array")                    # a REST klines response is an array: forbidden (no backfill)
    if not isinstance(top, dict):
        return _fail("not_object")
    if "stream" in top:
        form = "COMBINED"
        if set(top) != {"stream", "data"}:
            return _fail("combined_keys")
        if top["stream"] != expected_stream:
            return _fail("stream_name")
        msg = top["data"]
        if not isinstance(msg, dict):
            return _fail("data_not_object")
    else:
        form, msg = "RAW", top
    if msg.get("e") != "kline":
        return _fail("event_type")                    # e.g. "continuous_kline"
    E = msg.get("E")
    if not _is_int(E) or not (TS_MIN <= E <= TS_MAX):
        return _fail("E_type_or_range")
    if msg.get("s") != SYMBOL:
        return _fail("symbol_outer")
    k = msg.get("k")
    if not isinstance(k, dict):
        return _fail("k_not_object")
    if k.get("s") != SYMBOL:
        return _fail("symbol_k")
    if k.get("i") != INTERVAL:
        return _fail("interval")
    t, T = k.get("t"), k.get("T")
    if not _is_int(t) or not (TS_MIN <= t <= TS_MAX):
        return _fail("t_type_or_range")
    if t % MINUTE_MS != 0:
        return _fail("t_not_minute")
    if not _is_int(T) or T != t + MINUTE_MS - 1:
        return _fail("T_mismatch")
    o = k.get("o")
    if not isinstance(o, str) or len(o) > 30 or DEC_RE.fullmatch(o) is None:
        return _fail("o_grammar")
    if Decimal(o) == 0:
        return _fail("o_zero")
    x = k.get("x")
    if not isinstance(x, bool):
        return _fail("x_type")
    return {"ok": True, "form": form, "E": E, "t": t, "T": T, "o": o, "x": x}


def _decode(b64):
    try:
        return base64.b64decode(b64, validate=True)
    except Exception:
        return None


def candle_checks(events, max_lag_ms):
    """events: list of (line_no, event_dict) for the events that are VALID per contract 2.1, in file order (line numbers are 1-based and
    equal to `seq` in a good journal). Returns (findings, candles, refs):
      findings = list of [name, where, detail]; candles = dict open_time_ms -> "USABLE" | reason code (reference CANDLE of each declared open_time_ms);
      refs = dict open_time_ms -> (line of the reference CANDLE, its declared open).
    max_lag_ms: int, or None while the owner has not fixed it. None => hard finding CANDLE_LAG_UNSET (where 0) and no minute is USABLE."""
    findings = []
    by_line = {ln: ev for ln, ev in events}
    # connection table (contract 7.2 convention): first open event defines open_ms and feed; last close event defines close_ms
    opens, closes, feeds = {}, {}, {}
    for ln, ev in events:
        if ev.get("t") != "CONN":
            continue
        c = ev["conn_id"]
        if ev["ev"] == "open" and c not in opens:
            opens[c] = (ln, ev["ms"])
            feeds[c] = ev.get("feed")
        elif ev["ev"] == "close":
            closes[c] = ev["ms"]
    clock_lines = [(ln, ev["offset_ms"]) for ln, ev in events if ev.get("t") == "CLOCK"]

    def offset_before(line):
        off = 0
        for ln, o in clock_lines:
            if ln < line:
                off = o
        return off

    if max_lag_ms is None:
        findings.append(["CANDLE_LAG_UNSET", 0, "the maximum receipt lag is not fixed; no minute can be declared usable"])
    ref_line, ref_open, defect, parsed_of = {}, {}, {}, {}
    seen_conflict = set()
    for ln, ev in events:
        if ev.get("t") != "CANDLE":
            continue
        ot, declared_open = ev["open_time_ms"], ev["open"]
        bad = None                                      # first integrity defect of THIS record (for the reference rule)
        # --- link to the recorded MSG (proposal 3.1)
        m = ev.get("msg_seq")
        msg = by_line.get(m) if isinstance(m, int) and not isinstance(m, bool) else None
        why = None
        if msg is None or msg.get("t") != "MSG" or not (m < ln):
            why = "msg_seq does not name an earlier valid MSG"
        elif msg["raw_b64"] != ev["raw_b64"] or msg["sha256"] != ev["sha256"]:
            why = "raw bytes differ from the linked MSG"
        elif msg["recv_ms"] != ev["recv_ms"]:
            why = "recv_ms differs from the linked MSG"
        else:
            c = msg["conn_id"]
            if c not in opens or opens[c][0] >= m:
                why = "linked MSG belongs to a connection without an earlier open event"
            elif feeds.get(c) != "KLINE":
                why = "linked MSG belongs to a connection whose feed is not KLINE"
            elif not (opens[c][1] <= msg["recv_ms"] and (c not in closes or msg["recv_ms"] <= closes[c])):
                why = "linked MSG was not received while its connection was open"
        if why:
            findings.append(["CANDLE_LINK", ln, why])
            bad = bad or "LINK"
        # --- parse the raw bytes of the CANDLE (the shared parser)
        raw = _decode(ev["raw_b64"])
        p = _fail("base64") if raw is None else parse_kline_frame(raw)
        if not p["ok"]:
            findings.append(["CANDLE_PARSE", ln, "raw frame is not an acceptable kline frame: " + p["reason"]])
            bad = bad or "PARSE"
        elif p["t"] != ot or p["o"] != declared_open:
            findings.append(["CANDLE_FIELD_MISMATCH", ln, "declared open_time_ms/open differ from the values parsed from the raw frame"])
            bad = bad or "FIELD_MISMATCH"
        else:
            parsed_of[ln] = p
        # --- liveness (hard): certainly received before the candle opened, after correcting the clock and allowing its uncertainty
        off = offset_before(ln)
        if ev["recv_ms"] - off + CLOCK_UNCERTAINTY_MS < ot:
            findings.append(["CANDLE_NOT_LIVE", ln, "candle received before its open time (clock-corrected, uncertainty allowed)"])
            bad = bad or "NOT_LIVE"
        # --- first record per declared open_time_ms is the reference; later records can never replace it
        if ot in ref_line:
            if ref_open[ot] != declared_open and ot not in seen_conflict:
                seen_conflict.add(ot)
                findings.append(["CANDLE_CONFLICT", ln, "two candles with open_time_ms %d disagree on open" % ot])
        else:
            ref_line[ot], ref_open[ot], defect[ot] = ln, declared_open, bad
    # --- usability of each reference record (proposal 3.4); decides OUTCOME_UNLINKED, creates no finding of its own
    candles = {}
    for ot, ln in ref_line.items():
        ev = by_line[ln]
        off = offset_before(ln)
        p = parsed_of.get(ln)
        if defect[ot]:
            candles[ot] = "DEFECT_" + defect[ot]
        elif abs(off) > CLOCK_UNCERTAINTY_MS:
            candles[ot] = "CLOCK"
        elif not (p["t"] <= p["E"] <= p["T"]):
            candles[ot] = "E_RANGE"
        elif ev["recv_ms"] - off + CLOCK_UNCERTAINTY_MS > p["T"]:
            candles[ot] = "LATE_MINUTE"
        elif ev["recv_ms"] - off - p["E"] < -CLOCK_UNCERTAINTY_MS:
            candles[ot] = "LAG_NEGATIVE"
        elif max_lag_ms is None:
            candles[ot] = "LAG_UNSET"
        elif ev["recv_ms"] - off - p["E"] > max_lag_ms:
            candles[ot] = "LAG_TOO_OLD"
        else:
            candles[ot] = "USABLE"
    return findings, candles, {ot: (ref_line[ot], ref_open[ot]) for ot in ref_line}


def outcome_unlinked(outcome_line, open_time_ms, price, refs, candles):
    """Proposal 3.5: the referenced entry/exit candle must be the reference CANDLE of that minute, written before the OUTCOME, USABLE, with open == price."""
    ref = refs.get(open_time_ms)
    return ref is None or ref[0] >= outcome_line or candles.get(open_time_ms) != "USABLE" or ref[1] != price
