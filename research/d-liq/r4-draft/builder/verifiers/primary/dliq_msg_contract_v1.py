"""D-LIQ-SNAPSHOT-CONT4H-v1 -- executable message-validity and slot-building contract (spec r2 sections 4.1-4.5).

Reference implementation operating on RECORDED frames only. It opens no socket and reads no market data.
Python 3 standard library only. Not locked; part of the r2 audit package.

classify(raw_bytes)         -> dict(class = MALFORMED | INELIGIBLE | ELIGIBLE, reason, E, side, z, ap, X)
health_intervals(...)       -> list of (start_ms, end_ms) intervals in which a connection counts as "healthy"
build_slot(...)             -> slot record (VALID / NONE with reasons), including a per-message disposition ledger whose
                               counts always add up to the number of input messages (no silent loss)
"""
import json
import re
from decimal import Decimal, localcontext

TS_MIN = 1_700_000_000_000          # 2023-11-14 UTC in ms
TS_MAX = 4_102_444_800_000          # 2100-01-01 UTC in ms
DEC_RE = re.compile(r"(0|[1-9][0-9]*)(\.[0-9]+)?")          # used with fullmatch; ASCII digits only
O_REQUIRED = ("s", "S", "o", "f", "q", "p", "ap", "X", "l", "z", "T")
O_STRINGS = ("s", "S", "o", "f", "q", "p", "ap", "X", "l", "z")
DEC_FIELDS = ("q", "p", "ap", "l", "z")

PARAMS = {
    "window_ms": 900_000,           # feature window [tau - 15 min, tau)
    "void_pre_ms": 960_000,         # V(tau) = [tau - 16 min, tau + L]
    "late_ms": 10_000,              # L
    "min_n_total": 5,               # k
    "max_clock_offset_ms": 250,
    "max_frame_gap_ms": 200_000,    # health rule
    "accepted_status": "FILLED",
}


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


def classify(raw):
    """Classify one received frame (bytes) exactly as spec r2 section 4.2."""
    out = {"class": "MALFORMED", "reason": None, "E": None, "side": None, "z": None, "ap": None, "X": None}
    try:
        text = raw.decode("utf-8", errors="strict")
    except Exception:
        out["reason"] = "utf8"
        return out
    try:
        msg = json.loads(text, object_pairs_hook=_no_dups, parse_constant=_bad_const)
    except _Dup:
        out["reason"] = "duplicate_key"
        return out
    except Exception:
        out["reason"] = "json"
        return out
    if not isinstance(msg, dict):
        out["reason"] = "not_object"
        return out
    # E is recorded as soon as it is a valid integer in range, even if the message is malformed for another reason
    if _is_int(msg.get("E")) and TS_MIN <= msg["E"] <= TS_MAX:
        out["E"] = msg["E"]
    for k in ("e", "E", "o"):
        if k not in msg:
            out["reason"] = "missing_" + k
            return out
    if not _is_int(msg["E"]) or not (TS_MIN <= msg["E"] <= TS_MAX):
        out["reason"] = "E_type_or_range"
        return out
    o = msg["o"]
    if not isinstance(o, dict):
        out["reason"] = "o_not_object"
        return out
    for k in O_REQUIRED:
        if k not in o:
            out["reason"] = "missing_o." + k
            return out
    for k in O_STRINGS:
        if not isinstance(o[k], str):
            out["reason"] = "type_o." + k
            return out
    if not _is_int(o["T"]) or not (TS_MIN <= o["T"] <= TS_MAX):
        out["reason"] = "T_type_or_range"
        return out
    if msg["e"] != "forceOrder":
        out["reason"] = "event_type"
        return out
    if o["s"] != "BTCUSDT":
        out["reason"] = "symbol"
        return out
    if "st" in msg and not (_is_int(msg["st"]) and msg["st"] == 1):
        out["reason"] = "st_not_1"
        return out
    if o["S"] not in ("BUY", "SELL"):
        out["reason"] = "side"
        return out
    for k in DEC_FIELDS:
        v = o[k]
        if len(v) > 30 or DEC_RE.fullmatch(v) is None:
            out["reason"] = "decimal_grammar." + k
            return out
    z, ap = Decimal(o["z"]), Decimal(o["ap"])
    out.update(side=o["S"], z=z, ap=ap, X=o["X"])
    if o["X"] != PARAMS["accepted_status"]:
        out.update({"class": "INELIGIBLE", "reason": "status"})
        return out
    if z == 0:
        out.update({"class": "INELIGIBLE", "reason": "z_zero"})
        return out
    if ap == 0:
        out.update({"class": "INELIGIBLE", "reason": "ap_zero"})
        return out
    out.update({"class": "ELIGIBLE", "reason": None})
    return out


def health_intervals(open_ms, frame_times_ms, close_ms=None, end_ms=None):
    """Healthy intervals of one connection: consecutive points (open, every received frame incl. server pings) may be at most
    max_frame_gap_ms apart; a run ends at its last point + max gap, capped by close/end of observation."""
    gap = PARAMS["max_frame_gap_ms"]
    stop = close_ms if close_ms is not None else end_ms
    pts = [open_ms] + sorted(t for t in frame_times_ms if t >= open_ms and (stop is None or t <= stop))
    runs, start, prev = [], pts[0], pts[0]
    for t in pts[1:]:
        if t - prev > gap:
            runs.append((start, prev + gap))
            start = t
        prev = t
    runs.append((start, prev + gap))
    if stop is not None:
        runs = [(a, min(b, stop)) for a, b in runs if a <= stop]
    return runs


def _covers(intervals, a, b):
    return any(s <= a and b <= e for s, e in intervals)


def build_slot(tau_ms, messages, health, clock_offset_ms=0):
    """messages: list of dict(conn_id:int, recv_ms:int, raw:bytes); health: dict conn_id -> list of (start, end) intervals."""
    P = PARAMS
    v_lo, v_hi = tau_ms - P["void_pre_ms"], tau_ms + P["late_ms"]
    w_lo, w_hi = tau_ms - P["window_ms"], tau_ms
    cls = [classify(m["raw"]) for m in messages]
    # primary connection: smallest id healthy over the whole V(tau)
    cands = sorted(c for c, iv in health.items() if _covers(iv, v_lo, v_hi))
    primary = cands[0] if cands else None
    reasons = []
    if primary is None:
        reasons.append("GAP")
    if abs(clock_offset_ms) > P["max_clock_offset_ms"]:
        reasons.append("CLOCK")
    # disposition ledger: exactly one label per input message
    ledger = {"MALFORMED": 0, "NO_PRIMARY": 0, "NON_PRIMARY": 0, "OUT_OF_WINDOW": 0, "LATE": 0, "INELIGIBLE": 0, "COUNTED": 0}
    void = 0
    buy = sell = Decimal(0)
    n_buy = n_sell = 0
    with localcontext() as ctx:
        ctx.prec = 200
        for m, c in zip(messages, cls):
            if c["class"] == "MALFORMED":
                ledger["MALFORMED"] += 1
                if v_lo <= m["recv_ms"] <= v_hi or (c["E"] is not None and v_lo <= c["E"] <= v_hi):
                    void += 1
                continue
            if primary is None:
                ledger["NO_PRIMARY"] += 1
                continue
            if m["conn_id"] != primary:
                ledger["NON_PRIMARY"] += 1
                continue
            E = None
            # E of a structurally valid message is always present
            E = json.loads(m["raw"].decode("utf-8"))["E"]
            if not (w_lo <= E < w_hi):
                ledger["OUT_OF_WINDOW"] += 1
                continue
            if m["recv_ms"] > v_hi:
                ledger["LATE"] += 1
                continue
            if c["class"] == "INELIGIBLE":
                ledger["INELIGIBLE"] += 1
                continue
            ledger["COUNTED"] += 1
            w = c["z"] * c["ap"]
            if c["side"] == "BUY":
                buy += w
                n_buy += 1
            else:
                sell += w
                n_sell += 1
        n_total = n_buy + n_sell
        if void:
            reasons.append("MALFORMED")
        if primary is not None and n_total < P["min_n_total"]:
            reasons.append("N_TOTAL")
        x = None
        side = 0
        if n_total > 0:
            tot = buy + sell
            x = (buy - sell) / tot
            side = 1 if buy > sell else (-1 if sell > buy else 0)
            if side == 0 and "N_TOTAL" not in reasons:
                reasons.append("ZERO")
    rec = {"tau_ms": tau_ms, "status": "NONE" if reasons else "VALID", "reasons": reasons, "primary_conn": primary,
           "N_total": n_total, "N_BUY": n_buy, "N_SELL": n_sell, "sumW_BUY": format(buy, "f"), "sumW_SELL": format(sell, "f"),
           "X_sn": None if x is None else float(x), "side": side if not reasons else 0, "malformed_voids": void,
           "ledger": ledger, "n_messages": len(messages)}
    assert sum(ledger.values()) == len(messages), "ledger does not add up"
    return rec
