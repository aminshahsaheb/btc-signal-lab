"""D-LIQ evidence journal -- VERIFIER v2 (spec r3 Appendix A; normative text: JOURNAL_CONTRACT_v2.md). Python 3 standard library only. DRAFT, not locked.
Does not import the writer. The optional SLOT-replay layer (contract section 7) imports dliq_msg_contract_v1 lazily.
Primary implementation. The partially independent verifier is in indep_verifier/verify_indep.py; see the README for its limits.

verify(path, anchor, journal_id, verify_time_ms, replay_slots=False) -> dict(verdict, findings, hard, soft, n_events, head_hex, slots, missing)
"""
import base64
import hashlib
import json
import math
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

GENESIS = b"DLIQ-JOURNAL-v2-GENESIS"
GRID_MS = 14_400_000
ENTRY_DELAY_MS = 300_000
HORIZON_MS = 14_400_000
DEC_RE = re.compile(r"(0|[1-9][0-9]*)(\.[0-9]+)?")
HARD = {"BAD_ENCODING", "NOT_CANONICAL", "BAD_EVENT", "RAW_HASH_MISMATCH", "SEQ_GAP", "HEAD_MISMATCH", "RECEIPT_INVALID", "CHECKPOINT_ORDER",
        "TRUNCATION_OR_REPLACEMENT", "SLOT_OFF_GRID", "SLOT_HAS_OUTCOME_FIELDS", "DUPLICATE_SLOT", "DUPLICATE_OUTCOME", "OUTCOME_ORPHAN",
        "OUTCOME_BEFORE_ANCHOR", "OUTCOME_FOR_NONE_SLOT", "OUTCOME_TIMING", "OUTCOME_MISMATCH", "OUTCOME_UNLINKED", "CANDLE_CONFLICT", "CANDLE_NOT_LIVE", "SLOT_MISMATCH"}
SOFT = {"SLOT_LATE_ANCHOR", "SLOT_UNANCHORED", "SLOT_MISSING"}
OUTCOME_KEYS = ("entry_open_ms", "exit_open_ms", "entry_price", "exit_price", "r_bps", "outcome")
EVENT_TYPES = ("SESSION", "CONN", "PING", "MSG", "CLOCK", "CANDLE", "SLOT", "OUTCOME", "CHECKPOINT")


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
        return _isint(g("conn_id")) and g("ev") in ("open", "close") and _isint(g("ms"))
    if t == "PING":
        return _isint(g("conn_id")) and _isint(g("ms"))
    if t == "MSG":
        return _isint(g("conn_id")) and _isint(g("recv_ms")) and _isstr(g("raw_b64")) and _isstr(g("sha256"))
    if t == "CLOCK":
        return _isint(g("offset_ms")) and _isint(g("ms"))
    if t == "CANDLE":
        return _isint(g("open_time_ms")) and _isdec(g("open")) and _isint(g("recv_ms")) and _isstr(g("raw_b64")) and _isstr(g("sha256"))
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
    data = open(path, "rb").read()
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


def verify(path, anchor, journal_id, verify_time_ms, replay_slots=False):
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
    # 6 candles and outcomes
    first_candle = {}
    seen_conflict = set()
    for i, ev in sorted(valid.items()):
        if ev["t"] != "CANDLE":
            continue
        ot = ev["open_time_ms"]
        if ev["recv_ms"] < ot:
            F(["CANDLE_NOT_LIVE", i, "candle received before its open time"])
        if ot in first_candle:
            if first_candle[ot][1] != ev["open"] and ot not in seen_conflict:
                seen_conflict.add(ot)
                F(["CANDLE_CONFLICT", i, "two candles with open_time_ms %d disagree on open" % ot])
        else:
            first_candle[ot] = (i, ev["open"])
    seen_outcome = set()
    for j, ev in sorted(valid.items()):
        if ev["t"] != "OUTCOME":
            continue
        tau = ev["tau_ms"]
        if tau in seen_outcome:
            F(["DUPLICATE_OUTCOME", j, "second OUTCOME for tau_ms %d" % tau])
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
            for key_t, key_p in (("entry_open_ms", "entry_price"), ("exit_open_ms", "exit_price")):
                c = first_candle.get(ev[key_t])
                if c is None or c[0] >= j or c[1] != ev[key_p]:
                    F(["OUTCOME_UNLINKED", j, "no earlier CANDLE (first by line) with open_time_ms %d and open %s" % (ev[key_t], ev[key_p])])
    # 7 optional replay
    if replay_slots:
        import dliq_msg_contract_v1 as MC
        for tau, i in sorted(ref_slot.items()):
            ev = valid[i]
            msgs, frames, opens, closes, clock = [], {}, {}, {}, 0
            for k, e in sorted(valid.items()):
                if k >= i:
                    break
                t = e["t"]
                if t == "MSG":
                    msgs.append({"conn_id": e["conn_id"], "recv_ms": e["recv_ms"], "raw": base64.b64decode(e["raw_b64"])})
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
    hard = sorted(set(f[0] for f in findings if f[0] in HARD))
    soft = sorted(set(f[0] for f in findings if f[0] in SOFT))
    return {"verdict": "FAIL" if hard else "PASS", "findings": findings, "hard": hard, "soft": soft, "n_events": N, "head_hex": heads[-1].hex(),
            "slots": slots, "missing": missing}


if __name__ == "__main__":
    print("library module; see test_dliq_journal_v2.py")
