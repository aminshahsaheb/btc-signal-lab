"""D-LIQ evidence journal -- PRIMARY VERIFIER v3 (journal contract v3, r6 text: PR #39, commit 8969b65e716ba290041571ebf2ada64a7cc847db). Python 3 standard library only.
DRAFT, not locked, not reviewed; written by the author of the contract text and of the conformance vectors: NOT an independent verifier.

DERIVED from research/d-liq/r5-draft/src/dliq_journal_verify_v2.py (the diff is PROVENANCE_verify.diff; README.md lists what is unchanged r5 code, what is changed and what is new).
All r6-specific logic is in r6_rules.py. This module does not import the writer and does not import the conformance-vector oracle.

verify(path, anchor, journal_id, verify_time_ms, replay_slots=True) -> dict(verdict, findings, hard, soft, n_events, head_hex, slots, missing, outcomes, candles, replayed, analysis_eligible)
Scope of this version (GPT, 2026-11-12, Q5): the CANDLE rules 6.2, 6.3 and 6.5-6.9 are NOT implemented. A journal with a valid CANDLE event raises UnsupportedJournal; it never gets a verdict.
`candles` is therefore always {}. CANDLE_LAG_UNSET (6.8) is reported on every journal while L is unset, so the verdict is never PASS.
r5 (contract 7.6, GPT audit G-2): the SLOT replay runs only when replay_slots is exactly True. Otherwise: hard REPLAY_NOT_RUN (where 0), replayed=False, analysis_eligible=False.
"""
import base64
import hashlib
import json
import math
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import r6_rules as R6      # noqa: E402  (the r6-specific logic)

GENESIS = R6.GENESIS_V3       # r6, 3.2 (r5: DLIQ-JOURNAL-v2-GENESIS)
GRID_MS = 14_400_000
ENTRY_DELAY_MS = 300_000
HORIZON_MS = 14_400_000
DEC_RE = re.compile(r"(0|[1-9][0-9]*)(\.[0-9]+)?")
HARD = {"BAD_ENCODING", "NOT_CANONICAL", "BAD_EVENT", "RAW_HASH_MISMATCH", "SEQ_GAP", "HEAD_MISMATCH", "RECEIPT_INVALID", "CHECKPOINT_ORDER",
        "TRUNCATION_OR_REPLACEMENT", "SLOT_OFF_GRID", "SLOT_HAS_OUTCOME_FIELDS", "DUPLICATE_SLOT", "DUPLICATE_OUTCOME", "OUTCOME_ORPHAN",
        "OUTCOME_BEFORE_ANCHOR", "OUTCOME_FOR_NONE_SLOT", "OUTCOME_TIMING", "OUTCOME_MISMATCH", "OUTCOME_UNLINKED", "CANDLE_CONFLICT", "CANDLE_NOT_LIVE", "SLOT_MISMATCH",
        "SLOT_EARLY_WRITE", "REPLAY_NOT_RUN",
        # r6 (8.1); CANDLE_LINK, CANDLE_PARSE and CANDLE_FIELD_MISMATCH are listed because the contract lists them, this version cannot produce them (scope above)
        "CONN_FEED_CONFLICT", "MSG_CONN_UNKNOWN", "FORCE_MSG_STRUCTURE", "CANDLE_LINK", "CANDLE_PARSE", "CANDLE_FIELD_MISMATCH", "CANDLE_LAG_UNSET"}
SOFT = {"SLOT_LATE_ANCHOR", "SLOT_UNANCHORED", "SLOT_MISSING", "OUTCOME_UNCOVERED", "FORCE_UNKNOWN_KEY"}
INCOMPLETE_CLASS = {"REPLAY_NOT_RUN", "CANDLE_LAG_UNSET"}      # 8.2: these two make the verdict INCOMPLETE, never FAIL on their own
OUTCOME_KEYS = ("entry_open_ms", "exit_open_ms", "entry_price", "exit_price", "r_bps", "outcome")
EVENT_TYPES = ("SESSION", "CONN", "PING", "MSG", "CLOCK", "CANDLE", "SLOT", "OUTCOME", "CHECKPOINT")


class UnsupportedJournal(Exception):
    """The journal needs a rule this verifier version does not implement (a valid CANDLE event). No verdict is given."""


class _Dup(Exception):
    pass


def _pairs(pairs):
    d = {}
    for k, v in pairs:
        if k in d:
            raise _Dup(k)
        d[k] = v
    return d


def _bad_number(tok):
    raise ValueError("fractional or exponent number " + tok)


def _bad_const(tok):
    raise ValueError("constant " + tok)


def _isint(x):
    return isinstance(x, int) and not isinstance(x, bool)


def _isstr(x):
    return isinstance(x, str)


def _isdec(x):
    return isinstance(x, str) and DEC_RE.fullmatch(x) is not None


def _canon(ev):
    return json.dumps(ev, sort_keys=True, separators=(",", ":"), ensure_ascii=True, allow_nan=False).encode("ascii")


def _valid_event(ev):
    """contract 2.1: returns True if the event has the required common and per-type fields with the right types."""
    if not (_isstr(ev.get("t")) and ev["t"] in EVENT_TYPES and _isint(ev.get("seq")) and _isint(ev.get("rec_ms"))):
        return False
    t = ev["t"]
    g = ev.get
    if t == "CONN":
        return _isint(g("conn_id")) and g("ev") in ("open", "close") and _isint(g("ms")) and g("feed") in R6.FEEDS     # r6: feed required
    if t == "PING":
        return _isint(g("conn_id")) and _isint(g("ms"))
    if t == "MSG":
        return _isint(g("conn_id")) and _isint(g("recv_ms")) and _isstr(g("raw_b64")) and _isstr(g("sha256"))
    if t == "CLOCK":
        return _isint(g("offset_ms")) and _isint(g("ms"))
    if t == "CANDLE":
        return (_isint(g("open_time_ms")) and _isdec(g("open")) and _isint(g("recv_ms")) and _isstr(g("raw_b64")) and _isstr(g("sha256"))
                and _isint(g("msg_seq")))      # r6: msg_seq required
    if t == "SLOT":
        led = g("ledger")
        return (_isint(g("tau_ms")) and g("status") in ("VALID", "NONE") and isinstance(g("reasons"), list) and all(_isstr(x) for x in g("reasons"))
                and "primary_conn" in ev and (g("primary_conn") is None or _isint(g("primary_conn")))
                and all(_isint(g(k)) for k in ("N_total", "N_BUY", "N_SELL", "side", "malformed_voids", "n_messages"))
                and _isdec(g("sumW_BUY")) and _isdec(g("sumW_SELL")) and "X_sn" in ev and (g("X_sn") is None or _isstr(g("X_sn")))
                and isinstance(led, dict) and all(_isint(v) for v in led.values()))
    if t == "OUTCOME":
        if not (_isint(g("tau_ms")) and g("status") in ("EVAL", "NO_PRICE")):
            return False
        if g("status") == "EVAL":
            return (_isint(g("entry_open_ms")) and _isint(g("exit_open_ms")) and _isdec(g("entry_price")) and _isdec(g("exit_price")) and _isstr(g("r_bps")))
        return True
    if t == "CHECKPOINT":
        r = g("receipt")
        return (_isint(g("anchored_seq")) and _isstr(g("anchored_head")) and isinstance(r, dict) and _isstr(r.get("anchor_id")) and _isint(r.get("index"))
                and _isint(r.get("seq")) and _isstr(r.get("head")) and _isint(r.get("time_ms")) and _isint(r.get("time_resolution_ms")) and _isint(r.get("time_uncertainty_ms")))
    return True      # SESSION


def parse_file(path):
    with open(path, "rb") as fh:          # r6 package: closes the file (the r5 line leaked the handle; behaviour unchanged)
        data = fh.read()
    findings, events, lines = [], [], []
    if data and not data.endswith(b"\n"):
        findings.append(["BAD_ENCODING", data.count(b"\n") + 1, "file does not end with a newline (torn final line discarded)"])
        data = data[:data.rfind(b"\n") + 1]
    raw_lines = data.split(b"\n")[:-1] if data else []
    for i, line in enumerate(raw_lines, 1):
        try:
            ev = json.loads(line.decode("utf-8"), object_pairs_hook=_pairs, parse_float=_bad_number, parse_constant=_bad_const)
            if not isinstance(ev, dict):
                raise ValueError("not an object")
        except Exception as e:
            findings.append(["BAD_ENCODING", i, "%s" % type(e).__name__])
            break
        # json.loads accepts exponent integers such as 1e3 only through parse_float, which we reject; ints stay ints
        if _canon(ev) != line:
            findings.append(["NOT_CANONICAL", i, "line is not in canonical form"])
        events.append(ev)
        lines.append(line)
    return events, lines, findings


def verify(path, anchor, journal_id, verify_time_ms, replay_slots=True):
    events, lines, findings = parse_file(path)
    F = findings.append
    N = len(events)
    heads = [hashlib.sha256(GENESIS).digest()]
    for line in lines:
        heads.append(hashlib.sha256(heads[-1] + line).digest())
    # 3.1 sequence
    for i, ev in enumerate(events, 1):
        if ev.get("seq") != i or not _isint(ev.get("seq")):
            F(["SEQ_GAP", i, "line %d carries seq=%r" % (i, ev.get("seq"))])
            break
    # 2.1 validity (lines are 1-based)
    valid = {}
    for i, ev in enumerate(events, 1):
        if _valid_event(ev):
            valid[i] = ev
        else:
            F(["BAD_EVENT", i, "event violates the per-type field contract"])
    # 2.2 raw hashes
    for i, ev in enumerate(events, 1):
        if ev.get("t") in ("MSG", "CANDLE") and _isstr(ev.get("raw_b64")) and _isstr(ev.get("sha256")):
            try:
                raw = base64.b64decode(ev["raw_b64"], validate=True)
                ok = hashlib.sha256(raw).hexdigest() == ev["sha256"] and base64.b64encode(raw).decode("ascii") == ev["raw_b64"]
            except Exception:
                ok = False
            if not ok:
                F(["RAW_HASH_MISMATCH", i, "sha256 does not match raw bytes (or base64 not canonical)"])
    # 4.2 checkpoints
    cps = [(i, ev) for i, ev in sorted(valid.items()) if ev["t"] == "CHECKPOINT"]
    prev_k, prev_index = 0, 0
    for i, ev in cps:
        k, hx, rc = ev["anchored_seq"], ev["anchored_head"], ev["receipt"]
        idx = rc["index"]
        if not (0 < k < i) or k <= prev_k or idx != prev_index + 1:
            F(["CHECKPOINT_ORDER", i, "anchored_seq=%d index=%d (previous k=%d index=%d)" % (k, idx, prev_k, prev_index)])
        prev_k, prev_index = max(prev_k, k), idx
        if 0 < k <= N and heads[k].hex() != hx:
            F(["HEAD_MISMATCH", i, "recomputed h_%d differs from anchored_head" % k])
        e = anchor.get(journal_id, idx)
        bad = (e is None or e["head"] != hx or e["seq"] != k or e["time_ms"] != rc["time_ms"] or e["time_resolution_ms"] != rc["time_resolution_ms"]
               or e["time_uncertainty_ms"] != rc["time_uncertainty_ms"] or e["anchor_id"] != rc["anchor_id"] or rc["head"] != hx or rc["seq"] != k
               or rc["time_resolution_ms"] < 1 or rc["time_uncertainty_ms"] < 0)
        if bad:
            F(["RECEIPT_INVALID", i, "receipt index %d does not match the anchor entry" % idx])
    # 4.3 anchor ahead
    M = len(cps)
    top = anchor.latest(journal_id)
    for idx in range(M + 1, top + 1):
        e = anchor.get(journal_id, idx)
        if e is not None and e["seq"] <= N and heads[e["seq"]].hex() == e["head"]:
            F(["ANCHOR_AHEAD_BENIGN", idx, "anchor entry %d is reproduced by the journal but has no CHECKPOINT event" % idx])
        else:
            F(["TRUNCATION_OR_REPLACEMENT", idx, "anchor holds entry %d which the journal cannot reproduce" % idx])
    if M == 0:
        F(["NO_CHECKPOINT", 0, "nothing in this journal is authenticated"])
    elif cps[-1][0] < N:
        F(["TAIL_UNANCHORED", cps[-1][0] + 1, "%d line(s) after the last checkpoint are not authenticated" % (N - cps[-1][0])])
    # 5 slots
    ref_slot = {}
    for i, ev in sorted(valid.items()):
        if ev["t"] != "SLOT":
            continue
        tau = ev["tau_ms"]
        if tau % GRID_MS != 0:
            F(["SLOT_OFF_GRID", i, "tau_ms %d is not on the 4 h UTC grid" % tau])
        if set(ev) & set(OUTCOME_KEYS):
            F(["SLOT_HAS_OUTCOME_FIELDS", i, "SLOT carries outcome fields"])
        if tau in ref_slot:
            F(["DUPLICATE_SLOT", i, "second SLOT for tau_ms %d" % tau])
        else:
            ref_slot[tau] = i
    slots = {}
    for tau, i in sorted(ref_slot.items()):
        cov = next(((c, e) for c, e in cps if c > i and e["anchored_seq"] >= i), None)
        if cov is not None:
            rc = cov[1]["receipt"]
            upper = rc["time_ms"] + rc["time_resolution_ms"] - 1 + rc["time_uncertainty_ms"]
            if upper < tau + ENTRY_DELAY_MS:
                slots[tau] = "OK"
            else:
                slots[tau] = "LATE"
                F(["SLOT_LATE_ANCHOR", tau, "anchor_upper_ms %d is not < tau + 5 min = %d" % (upper, tau + ENTRY_DELAY_MS)])
        elif verify_time_ms >= tau + ENTRY_DELAY_MS:
            slots[tau] = "UNANCHORED"
            F(["SLOT_UNANCHORED", tau, "no covering checkpoint and verify_time_ms is at or past tau + 5 min"])
        else:
            slots[tau] = "PENDING"
    on_grid = sorted(t for t in ref_slot if t % GRID_MS == 0)
    missing = []
    if on_grid:
        t = on_grid[0]
        while t <= on_grid[-1]:
            if t not in ref_slot:
                missing.append(t)
                F(["SLOT_MISSING", t, "no SLOT for grid point inside the observed range"])
            t += GRID_MS
    # 6 outcomes (r6: the CANDLE rules 6.2, 6.3, 6.5-6.9 are not implemented in this version; QUESTIONS.md Q2)
    if any(ev["t"] == "CANDLE" for ev in valid.values()):
        raise UnsupportedJournal("the journal has a valid CANDLE event; the CANDLE rules (6.2, 6.3, 6.5-6.9) are not implemented in this verifier version")
    seen_outcome = set()
    outcomes = {}
    for j, ev in sorted(valid.items()):
        if ev["t"] != "OUTCOME":
            continue
        tau = ev["tau_ms"]
        if tau in seen_outcome:
            F(["DUPLICATE_OUTCOME", j, "second OUTCOME for tau_ms %d" % tau])
        else:
            # 6.4: the covering checkpoint of the reference OUTCOME is the first valid checkpoint line c > j with anchored_seq >= j
            if any(c > j and e["anchored_seq"] >= j for c, e in cps):
                outcomes[tau] = "COVERED"
            else:
                outcomes[tau] = "UNCOVERED"
                F(["OUTCOME_UNCOVERED", tau, "no valid checkpoint after line %d anchors this OUTCOME" % j])
        seen_outcome.add(tau)
        i = ref_slot.get(tau)
        if i is None or i >= j:
            F(["OUTCOME_ORPHAN", j, "no SLOT for tau_ms %d before this OUTCOME" % tau])
        if i is not None and valid.get(i, {}).get("status") != "VALID":
            F(["OUTCOME_FOR_NONE_SLOT", j, "OUTCOME refers to a SLOT whose status is not VALID"])
        if i is not None and not any(i < c < j and e["anchored_seq"] >= i for c, e in cps):
            F(["OUTCOME_BEFORE_ANCHOR", j, "OUTCOME written before any checkpoint covering its SLOT"])
        if ev["status"] == "EVAL":
            if not (ev["entry_open_ms"] == tau + ENTRY_DELAY_MS and ev["exit_open_ms"] == ev["entry_open_ms"] + HORIZON_MS):
                F(["OUTCOME_TIMING", j, "entry/exit candle times violate tau + 5 min and entry + 4 h"])
            try:
                r = float(ev["r_bps"])
                calc = 10000.0 * math.log(float(ev["exit_price"]) / float(ev["entry_price"]))
                good = math.isfinite(r) and abs(r - calc) <= 1e-6
            except Exception:
                good = False
            if not good:
                F(["OUTCOME_MISMATCH", j, "r_bps does not equal 1e4*ln(exit/entry)"])
            # r6 6.9 with L unset (6.8): no minute is USABLE, so the entry reference and the exit reference are both unlinked (at most two findings per OUTCOME, 8.4)
            # QUESTIONS.md Q4 (GPT, 2026-11-14): the detail names the endpoint, so the two findings of one OUTCOME are distinguishable
            for key_t, endpoint in (("entry_open_ms", "entry"), ("exit_open_ms", "exit")):
                F(["OUTCOME_UNLINKED", j, "endpoint=%s: no USABLE reference CANDLE for open_time_ms %d (L is unset, 6.8)" % (endpoint, ev[key_t])])
    # r6: feed of every connection (2.3a), feed findings (2.3b, 2.3c) and the run-level pass over every FORCE message (7.7). They do not depend on any SLOT and are
    # reported also when the replay is switched off (QUESTIONS.md Q3: the reading that reports more hard findings).
    opens_by_conn = R6.first_opens(valid)
    for f in R6.feed_findings(valid, opens_by_conn):
        F(f)
    for f in R6.run_level_findings(valid, opens_by_conn):
        F(f)
    # 7 replay (mandatory for the analysis pipeline; r4)
    if replay_slots is True:
        import dliq_msg_contract_v3 as MC
        for tau, i in sorted(ref_slot.items()):
            ev = valid[i]
            msgs, frames, opens, closes, clock = [], {}, {}, {}, 0
            for k, e in sorted(valid.items()):
                if k >= i:
                    break
                t = e["t"]
                if t in ("MSG", "PING", "CONN") and R6.is_kline_event(opens_by_conn, e["conn_id"], k):
                    continue      # r6 (7.2, A): no event of a KLINE connection, recorded from its first valid open on, is an input of the replay
                if t == "MSG":
                    # QUESTIONS.md Q1 (GPT, 2026-11-14): an undecodable raw_b64 stays a replay candidate with raw = None, which the contract module classifies as MALFORMED
                    # (explicit reason `undecodable_base64`); RAW_HASH_MISMATCH is reported by the hash check above; no bytes are invented.
                    msgs.append({"conn_id": e["conn_id"], "recv_ms": e["recv_ms"], "raw": R6.decode_raw(e)})
                    frames.setdefault(e["conn_id"], []).append(e["recv_ms"])
                elif t == "PING":
                    frames.setdefault(e["conn_id"], []).append(e["ms"])
                elif t == "CONN":
                    if e["ev"] == "open":
                        opens.setdefault(e["conn_id"], e["ms"])
                    else:
                        closes[e["conn_id"]] = e["ms"]
                elif t == "CLOCK":
                    clock = e["offset_ms"]
            health = {c: MC.health_intervals(o, frames.get(c, []), close_ms=closes.get(c), end_ms=ev["rec_ms"]) for c, o in opens.items()}
            rec = MC.build_slot(tau, msgs, health, clock_offset_ms=clock)
            want = {k: rec[k] for k in ("status", "reasons", "primary_conn", "N_total", "N_BUY", "N_SELL", "sumW_BUY", "sumW_SELL", "side", "malformed_voids", "ledger", "n_messages")}
            want["X_sn"] = None if rec["X_sn"] is None else repr(rec["X_sn"])
            diff = sorted(k for k in want if ev.get(k) != want[k])
            if diff:
                F(["SLOT_MISMATCH", i, "recomputed slot differs in " + ",".join(diff)])
            if ev["rec_ms"] < tau + 10_000:
                F(["SLOT_EARLY_WRITE", i, "SLOT written at rec_ms %d < tau_ms + 10 s = %d" % (ev["rec_ms"], tau + 10_000)])
    else:
        F(["REPLAY_NOT_RUN", 0, "the SLOT replay was not run (replay_slots is not exactly True); this report is not evidence for the analysis (contract 7.6)"])
    # r6 6.8: the maximum receipt lag L is UNSET (decision B): reported on EVERY journal, no minute is USABLE, the verdict is never PASS
    F(["CANDLE_LAG_UNSET", 0, "L is unset (6.8); no CANDLE minute is USABLE"])
    hard = sorted(set(f[0] for f in findings if f[0] in HARD))
    soft = sorted(set(f[0] for f in findings if f[0] in SOFT))
    replayed = replay_slots is True
    verdict = "FAIL" if any(h not in INCOMPLETE_CLASS for h in hard) else ("INCOMPLETE" if hard else "PASS")      # 8.2
    return {"verdict": verdict, "findings": findings, "hard": hard, "soft": soft, "n_events": N, "head_hex": heads[-1].hex(),
            "slots": slots, "missing": missing, "outcomes": outcomes, "candles": {}, "replayed": replayed, "analysis_eligible": verdict == "PASS" and replayed}


if __name__ == "__main__":
    print("library module; see test_primary_v3.py and run_vectors.py")
