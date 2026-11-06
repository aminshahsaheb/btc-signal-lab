#!/usr/bin/env python3
"""Partially independent verifier for the D-LIQ evidence journal, contract v2.

Written only from JOURNAL_CONTRACT_v2.md.  Standard library only; runs under
`python3 -I`.  Public entry point: verify(path, anchor, journal_id, verify_time_ms).

Section numbers in comments refer to the contract.  Every place where the contract
is silent or ambiguous is listed in QUESTIONS.md (numbered Q1, Q2, ...) and the
corresponding code carries a "Qn" marker.
"""
import base64
import binascii
import bisect
import hashlib
import json
import math
import re

GRID_MS = 14_400_000
ENTRY_DELAY_MS = 300_000
HORIZON_MS = 14_400_000
GENESIS = b"DLIQ-JOURNAL-v2-GENESIS"

HARD_NAMES = frozenset((
    "BAD_ENCODING", "NOT_CANONICAL", "BAD_EVENT", "RAW_HASH_MISMATCH", "SEQ_GAP",
    "HEAD_MISMATCH", "RECEIPT_INVALID", "CHECKPOINT_ORDER", "TRUNCATION_OR_REPLACEMENT",
    "SLOT_OFF_GRID", "SLOT_HAS_OUTCOME_FIELDS", "DUPLICATE_SLOT", "DUPLICATE_OUTCOME",
    "OUTCOME_ORPHAN", "OUTCOME_BEFORE_ANCHOR", "OUTCOME_FOR_NONE_SLOT", "OUTCOME_TIMING", "OUTCOME_MISMATCH",
    "OUTCOME_UNLINKED", "CANDLE_CONFLICT", "CANDLE_NOT_LIVE", "SLOT_MISMATCH",
    "SLOT_EARLY_WRITE",  # r4 integrator patch: name of the replay layer (contract 7.3/7.4); this verifier does NOT run the replay
))
SOFT_NAMES = frozenset(("SLOT_LATE_ANCHOR", "SLOT_UNANCHORED", "SLOT_MISSING", "OUTCOME_UNCOVERED"))   # r4 integrator patch: OUTCOME_UNCOVERED (contract 6.4)
INFO_NAMES = frozenset(("NO_CHECKPOINT", "TAIL_UNANCHORED", "ANCHOR_AHEAD_BENIGN"))

# Q19: safety valve for SLOT_MISSING enumeration (a legal but absurd tau range would
# otherwise run forever / exhaust memory).  Exceeding it raises ValueError.
MAX_GRID_POINTS = 20_000_000

_DEC_RE = re.compile(r"(0|[1-9][0-9]*)(\.[0-9]+)?")
# Q17: what counts as a usable numeric r_bps string.
_NUM_RE = re.compile(r"[+-]?(?:[0-9]+(?:\.[0-9]*)?|\.[0-9]+)(?:[eE][+-]?[0-9]+)?")

_EVENT_TYPES = ("SESSION", "CONN", "PING", "MSG", "CLOCK", "CANDLE", "SLOT", "OUTCOME",
                "CHECKPOINT")
_OUTCOME_KEYS = ("entry_open_ms", "exit_open_ms", "entry_price", "exit_price", "r_bps",
                 "outcome")

# ---------------------------------------------------------------------------
# 1. Parsing
# ---------------------------------------------------------------------------


def _no_constant(name):
    raise ValueError("forbidden JSON constant %s" % name)


def _no_fraction(token):
    raise ValueError("number token with fraction/exponent: %s" % token)


def _unique_pairs(pairs):
    d = {}
    for k, v in pairs:
        if k in d:
            raise ValueError("duplicate key %r" % (k,))
        d[k] = v
    return d


def _parse_line(raw):
    """Return (event_dict, None) or (None, reason)."""
    try:
        text = raw.decode("utf-8", "strict")
    except UnicodeDecodeError as exc:
        return None, "invalid UTF-8 (%s)" % exc
    try:
        ev = json.loads(text, object_pairs_hook=_unique_pairs, parse_float=_no_fraction,
                        parse_constant=_no_constant)
    except (ValueError, RecursionError) as exc:  # JSONDecodeError is a ValueError
        return None, "invalid JSON (%s)" % exc
    if not isinstance(ev, dict):
        return None, "JSON value is not an object"
    return ev, None


def _canon(ev):
    return json.dumps(ev, sort_keys=True, separators=(",", ":"), ensure_ascii=True,
                      allow_nan=False).encode("ascii")


# ---------------------------------------------------------------------------
# 2. Event validation
# ---------------------------------------------------------------------------


def _is_int(x):  # Q3: bool is never an int, for every integer field
    return type(x) is int


def _is_str(x):
    return type(x) is str


def _is_dec(x):  # fullmatch: a trailing "\n" is rejected (Q7)
    return type(x) is str and _DEC_RE.fullmatch(x) is not None


def _kind_ok(kind, v):
    if kind == "int":
        return _is_int(v)
    if kind == "str":
        return _is_str(v)
    if kind == "dec":
        return _is_dec(v)
    if kind == "int|null":
        return v is None or _is_int(v)
    if kind == "str|null":
        return v is None or _is_str(v)
    if kind == "list[str]":
        return type(v) is list and all(_is_str(x) for x in v)
    if kind == "dict[int]":
        return type(v) is dict and all(_is_int(x) for x in v.values())
    if kind == "dict":
        return type(v) is dict
    if kind.startswith("enum:"):
        return _is_str(v) and v in kind[5:].split("|")
    raise AssertionError(kind)


_SCHEMA = {
    "SESSION": (),
    "CONN": (("conn_id", "int"), ("ev", "enum:open|close"), ("ms", "int")),
    "PING": (("conn_id", "int"), ("ms", "int")),
    "MSG": (("conn_id", "int"), ("recv_ms", "int"), ("raw_b64", "str"), ("sha256", "str")),
    "CLOCK": (("offset_ms", "int"), ("ms", "int")),
    "CANDLE": (("open_time_ms", "int"), ("open", "dec"), ("recv_ms", "int"),
               ("raw_b64", "str"), ("sha256", "str")),
    # Q4: "side" is read as int because the "(int)" annotation follows the whole list.
    "SLOT": (("tau_ms", "int"), ("status", "enum:VALID|NONE"), ("reasons", "list[str]"),
             ("primary_conn", "int|null"), ("N_total", "int"), ("N_BUY", "int"),
             ("N_SELL", "int"), ("side", "int"), ("malformed_voids", "int"),
             ("n_messages", "int"), ("sumW_BUY", "dec"), ("sumW_SELL", "dec"),
             ("X_sn", "str|null"), ("ledger", "dict[int]")),
    "OUTCOME": (("tau_ms", "int"), ("status", "enum:EVAL|NO_PRICE")),
    "CHECKPOINT": (("anchored_seq", "int"), ("anchored_head", "str"), ("receipt", "dict")),
}
_OUTCOME_EVAL = (("entry_open_ms", "int"), ("exit_open_ms", "int"), ("entry_price", "dec"),
                 ("exit_price", "dec"), ("r_bps", "str"))
_RECEIPT = (("anchor_id", "str"), ("index", "int"), ("seq", "int"), ("head", "str"),
            ("time_ms", "int"), ("time_resolution_ms", "int"), ("time_uncertainty_ms", "int"))


def _validate(ev):
    """Return None if ev satisfies 2.1, else a reason string."""
    t = ev.get("t")
    if not _is_str(t):
        return "t missing or not a string"
    if t not in _SCHEMA:
        return "unknown event type %r" % (t,)
    if not _is_int(ev.get("seq")):
        return "seq missing or not an integer"
    if not _is_int(ev.get("rec_ms")):
        return "rec_ms missing or not an integer"
    specs = list(_SCHEMA[t])
    if t == "OUTCOME" and ev.get("status") == "EVAL":
        specs += list(_OUTCOME_EVAL)
    for name, kind in specs:
        if name not in ev:
            return "%s: missing field %s" % (t, name)
        if not _kind_ok(kind, ev[name]):
            return "%s: field %s is not %s" % (t, name, kind)
    if t == "CHECKPOINT":
        rc = ev["receipt"]
        for name, kind in _RECEIPT:
            if name not in rc:
                return "CHECKPOINT: receipt missing field %s" % name
            if not _kind_ok(kind, rc[name]):
                return "CHECKPOINT: receipt.%s is not %s" % (name, kind)
    return None


def _raw_hash_problem(ev):
    """2.2.  Returns None if fine or not checkable, else a detail string (Q5)."""
    b64, digest = ev.get("raw_b64"), ev.get("sha256")
    if not (_is_str(b64) and _is_str(digest)):
        return None  # field absent / mistyped: reported as BAD_EVENT only
    try:
        enc = b64.encode("ascii")
        data = base64.b64decode(enc, validate=True)
    except (ValueError, binascii.Error):
        return "raw_b64 is not valid standard base64"
    if base64.b64encode(data) != enc:  # Q6: strict canonical base64 only
        return "raw_b64 is not canonical base64"
    if hashlib.sha256(data).hexdigest() != digest:
        return "sha256 of decoded raw_b64 is %s, event says %s" % (
            hashlib.sha256(data).hexdigest(), digest)
    return None


# ---------------------------------------------------------------------------
# Anchor access
# ---------------------------------------------------------------------------


def _anchor_get(anchor, journal_id, idx):
    try:
        e = anchor.get(journal_id, idx)
    except (KeyError, IndexError):  # Q18
        return None
    return e


def _entry_field(e, name):
    if isinstance(e, dict):
        return e.get(name)
    return getattr(e, name, None)


# ---------------------------------------------------------------------------
# 6.1 d: OUTCOME arithmetic
# ---------------------------------------------------------------------------


def _outcome_mismatch(ev):
    """Return None if r_bps agrees with the prices, else a detail string."""
    r_s = ev["r_bps"]
    if _NUM_RE.fullmatch(r_s) is None:
        return "r_bps %r is not numeric" % (r_s,)
    try:
        r = float(r_s)
        ep = float(ev["entry_price"])
        xp = float(ev["exit_price"])
        if ep == 0.0 or xp == 0.0:
            return "a price is zero (entry %s, exit %s)" % (ev["entry_price"], ev["exit_price"])
        calc = 10000.0 * math.log(xp / ep)
    except (ValueError, OverflowError, ZeroDivisionError) as exc:
        return "cannot compute log return (%s)" % exc
    if not (math.isfinite(r) and math.isfinite(calc)):
        return "non-finite value (r_bps=%r, computed=%r)" % (r, calc)
    if abs(r - calc) > 1e-6:
        return "r_bps %s differs from recomputed %.9f by %.3e" % (r_s, calc, abs(r - calc))
    return None


# ---------------------------------------------------------------------------
# Main entry point
# ---------------------------------------------------------------------------


def verify(path, anchor, journal_id, verify_time_ms):
    with open(path, "rb") as fh:
        data = fh.read()

    findings = []

    def add(name, where, detail):
        findings.append([name, where, detail])

    # ---- 1.1 / 1.3: split into complete lines and an optional partial tail ----------
    if data == b"":
        complete, partial = [], None
    else:
        parts = data.split(b"\n")
        complete, partial = parts[:-1], (parts[-1] if parts[-1] != b"" else None)

    recs = []  # one per parsed line: dict(n, raw, ev, valid)
    heads = [hashlib.sha256(GENESIS).hexdigest()]  # heads[k] = hex(h_k)
    h = hashlib.sha256(GENESIS).digest()
    stopped = False
    seq_gap_done = False

    for n, raw in enumerate(complete, 1):
        ev, why = _parse_line(raw)
        if ev is None:
            add("BAD_ENCODING", n, why)
            stopped = True
            break
        # parsed line: enters the chain, whatever else is wrong with it
        h = hashlib.sha256(h + raw).digest()
        heads.append(h.hex())
        try:
            canon_ok = _canon(ev) == raw
        except (ValueError, RecursionError, UnicodeError):
            canon_ok = False
        if not canon_ok:
            add("NOT_CANONICAL", n, "line bytes differ from canonical serialisation")
        problem = _validate(ev)
        valid = problem is None
        if not valid:
            add("BAD_EVENT", n, problem)
        if ev.get("t") in ("MSG", "CANDLE"):  # Q5: also for BAD_EVENT lines
            rp = _raw_hash_problem(ev)
            if rp is not None:
                add("RAW_HASH_MISMATCH", n, rp)
        if not seq_gap_done and not (_is_int(ev.get("seq")) and ev["seq"] == n):
            add("SEQ_GAP", n, "event at line %d has seq %r" % (n, ev.get("seq")))
            seq_gap_done = True
        recs.append({"n": n, "raw": raw, "ev": ev, "valid": valid})

    if partial is not None:  # Q2 (contract 1.3: torn-line finding is reported even when parsing stopped earlier)
        add("BAD_ENCODING", len(complete) + 1,
            "file does not end with a newline: final partial line discarded")

    N = len(recs)
    head_hex = heads[N]
    valid_recs = [r for r in recs if r["valid"]]

    # ---- 4.2 checkpoints ------------------------------------------------------------
    ckpts = [(r["n"], r["ev"]) for r in valid_recs if r["ev"]["t"] == "CHECKPOINT"]
    M = len(ckpts)
    prev_k = 0
    prev_index = 0
    for i, ev in ckpts:
        k = ev["anchored_seq"]
        rc = ev["receipt"]
        idx = rc["index"]
        why = []
        if not (0 < k < i):
            why.append("anchored_seq %d not in (0, %d)" % (k, i))
        if k <= prev_k:
            why.append("anchored_seq %d <= previous %d" % (k, prev_k))
        if idx != prev_index + 1:
            why.append("receipt.index %d != previous index %d + 1" % (idx, prev_index))
        if why:  # Q9: one finding per checkpoint line
            add("CHECKPOINT_ORDER", i, "; ".join(why))
        prev_k = max(prev_k, k)
        prev_index = idx

        if 0 < k <= N and heads[k] != ev["anchored_head"]:
            add("HEAD_MISMATCH", i, "hex(h_%d)=%s but anchored_head=%s" % (
                k, heads[k], ev["anchored_head"]))

        bad = []
        e = _anchor_get(anchor, journal_id, idx)
        if e is None:
            bad.append("anchor has no entry with index %r" % (idx,))
        else:
            if _entry_field(e, "head") != ev["anchored_head"]:
                bad.append("anchor entry head differs from anchored_head")
            if _entry_field(e, "seq") != k:
                bad.append("anchor entry seq differs from anchored_seq")
            if _entry_field(e, "time_ms") != rc["time_ms"]:
                bad.append("anchor entry time_ms differs from receipt")
            if _entry_field(e, "time_resolution_ms") != rc["time_resolution_ms"]:
                bad.append("anchor entry time_resolution_ms differs from receipt")
            if _entry_field(e, "time_uncertainty_ms") != rc["time_uncertainty_ms"]:
                bad.append("anchor entry time_uncertainty_ms differs from receipt")
            if _entry_field(e, "anchor_id") != rc["anchor_id"]:
                bad.append("anchor entry anchor_id differs from receipt")
        if rc["head"] != ev["anchored_head"]:
            bad.append("receipt.head differs from anchored_head")
        if rc["seq"] != k:
            bad.append("receipt.seq differs from anchored_seq")
        if rc["time_resolution_ms"] < 1:
            bad.append("receipt.time_resolution_ms < 1")
        if rc["time_uncertainty_ms"] < 0:
            bad.append("receipt.time_uncertainty_ms < 0")
        if bad:  # Q9
            add("RECEIPT_INVALID", i, "; ".join(bad))

    # ---- 4.3 anchor ahead of / contradicting the journal -----------------------------
    top = anchor.latest(journal_id)
    if not _is_int(top):  # Q18: None / garbage means "no entries"
        top = 0
    for idx in range(M + 1, top + 1):
        e = _anchor_get(anchor, journal_id, idx)
        benign = False
        if e is not None:
            eseq, ehead = _entry_field(e, "seq"), _entry_field(e, "head")
            if _is_int(eseq) and 0 <= eseq <= N and heads[eseq] == ehead:
                benign = True
        if benign:
            add("ANCHOR_AHEAD_BENIGN", idx, "anchor index %d (seq %d) matches the journal "
                "prefix; journal has %d checkpoints" % (idx, _entry_field(e, "seq"), M))
        else:
            add("TRUNCATION_OR_REPLACEMENT", idx, "anchor index %d (%s) is not consistent "
                "with the journal (N=%d, checkpoints=%d)" % (
                    idx, "missing" if e is None else "seq %r" % (_entry_field(e, "seq"),),
                    N, M))

    # ---- 4.4 informational ------------------------------------------------------------
    if M == 0:
        add("NO_CHECKPOINT", 0, "journal has no valid CHECKPOINT event")
    else:
        last_c = ckpts[-1][0]
        if N > last_c:  # Q11
            add("TAIL_UNANCHORED", last_c + 1, "%d parsed line(s) after the last CHECKPOINT "
                "(line %d)" % (N - last_c, last_c))

    # ---- 5. SLOTs ----------------------------------------------------------------------
    ref_slot = {}  # tau -> line of reference SLOT
    slot_event_by_tau = {}
    for r in valid_recs:
        ev = r["ev"]
        if ev["t"] != "SLOT":
            continue
        i, tau = r["n"], ev["tau_ms"]
        if tau % GRID_MS != 0:
            add("SLOT_OFF_GRID", i, "SLOT at line %d: tau_ms %d is not a multiple of %d"
                % (i, tau, GRID_MS))
        present = [k for k in _OUTCOME_KEYS if k in ev]
        if present:
            add("SLOT_HAS_OUTCOME_FIELDS", i, "SLOT at line %d carries %s" % (i, present))
        if tau in ref_slot:
            add("DUPLICATE_SLOT", i, "SLOT at line %d repeats tau_ms of line %d"
                % (i, ref_slot[tau]))
        else:
            ref_slot[tau] = i
            slot_event_by_tau[tau] = ev

    slots = {}
    ck_lines = [c for c, _ in ckpts]
    for tau, i in ref_slot.items():
        cover = None
        for pos in range(bisect.bisect_right(ck_lines, i), len(ckpts)):
            c, cev = ckpts[pos]
            if cev["anchored_seq"] >= i:  # first valid CHECKPOINT line c > i
                cover = (c, cev)
                break
        deadline = tau + ENTRY_DELAY_MS
        if cover is not None:
            rc = cover[1]["receipt"]
            upper = rc["time_ms"] + rc["time_resolution_ms"] - 1 + rc["time_uncertainty_ms"]
            if upper < deadline:
                slots[tau] = "OK"
            else:
                slots[tau] = "LATE"
                add("SLOT_LATE_ANCHOR", tau, "SLOT line %d: covering checkpoint line %d has "
                    "anchor_upper_ms %d >= deadline %d" % (i, cover[0], upper, deadline))
        else:
            if verify_time_ms >= deadline:
                slots[tau] = "UNANCHORED"
                add("SLOT_UNANCHORED", tau, "SLOT line %d has no covering checkpoint and "
                    "verify_time_ms %d >= %d" % (i, verify_time_ms, deadline))
            else:
                slots[tau] = "PENDING"

    # 5.4 grid completeness
    missing = []
    on_grid = [t for t in ref_slot if t % GRID_MS == 0]
    if on_grid:
        tmin, tmax = min(on_grid), max(on_grid)
        if (tmax - tmin) // GRID_MS + 1 > MAX_GRID_POINTS:
            raise ValueError("grid between %d and %d too large to enumerate" % (tmin, tmax))
        t = tmin
        while t <= tmax:
            if t not in ref_slot:
                missing.append(t)
                add("SLOT_MISSING", t, "no SLOT for grid point %d (between %d and %d)"
                    % (t, tmin, tmax))
            t += GRID_MS

    # ---- 6.2 / 6.3 candles ---------------------------------------------------------------
    candles = {}  # open_time_ms -> [(line, open)] in file order
    for r in valid_recs:
        ev = r["ev"]
        if ev["t"] == "CANDLE":
            candles.setdefault(ev["open_time_ms"], []).append((r["n"], ev["open"]))
            if ev["recv_ms"] < ev["open_time_ms"]:
                add("CANDLE_NOT_LIVE", r["n"], "recv_ms %d < open_time_ms %d"
                    % (ev["recv_ms"], ev["open_time_ms"]))
    for ot, lst in candles.items():
        first_line, first_open = lst[0]
        for ln, op in lst[1:]:
            if op != first_open:  # Q16: reported at the first differing candle
                add("CANDLE_CONFLICT", ln, "open_time_ms %d: open %r (line %d) vs %r "
                    "(line %d)" % (ot, op, ln, first_open, first_line))
                break

    # ---- 6.1 outcomes -----------------------------------------------------------------------
    seen_outcome = {}
    outcomes = {}  # r4 integrator patch (contract 6.4): reference OUTCOME of each tau -> COVERED / UNCOVERED
    for r in valid_recs:
        ev = r["ev"]
        if ev["t"] != "OUTCOME":
            continue
        j, tau = r["n"], ev["tau_ms"]
        if tau in seen_outcome:
            add("DUPLICATE_OUTCOME", j, "OUTCOME tau_ms %d repeats line %d"
                % (tau, seen_outcome[tau]))
        else:
            seen_outcome[tau] = j
            if any(c > j and cev["anchored_seq"] >= j for c, cev in ckpts):
                outcomes[tau] = "COVERED"
            else:
                outcomes[tau] = "UNCOVERED"
                add("OUTCOME_UNCOVERED", tau, "no valid CHECKPOINT after line %d anchors the OUTCOME" % j)
        i = ref_slot.get(tau)
        if i is None or i > j:
            add("OUTCOME_ORPHAN", j, "no reference SLOT for tau_ms %d before line %d" % (tau, j))
        if i is not None:  # Q14: also when the reference SLOT lies after the OUTCOME
            if slot_event_by_tau.get(tau, {}).get("status") != "VALID":
                add("OUTCOME_FOR_NONE_SLOT", j, "OUTCOME refers to a SLOT whose status is not VALID")
            if not any(i < c < j and cev["anchored_seq"] >= i for c, cev in ckpts):
                add("OUTCOME_BEFORE_ANCHOR", j, "no CHECKPOINT between SLOT line %d and "
                    "OUTCOME line %d anchors the SLOT" % (i, j))
        if ev["status"] != "EVAL":
            continue
        entry_open = ev["entry_open_ms"]
        exit_open = ev["exit_open_ms"]
        if not (entry_open == tau + ENTRY_DELAY_MS and exit_open == entry_open + HORIZON_MS):
            add("OUTCOME_TIMING", j, "entry_open_ms %d / exit_open_ms %d, expected %d / %d"
                % (entry_open, exit_open, tau + ENTRY_DELAY_MS,
                   tau + ENTRY_DELAY_MS + HORIZON_MS))
        why = _outcome_mismatch(ev)
        if why is not None:
            add("OUTCOME_MISMATCH", j, why)
        for label, open_ms, price in (("entry", entry_open, ev["entry_price"]),
                                      ("exit", exit_open, ev["exit_price"])):
            lst = candles.get(open_ms)
            if not lst or lst[0][0] >= j:
                add("OUTCOME_UNLINKED", j, "no CANDLE before line %d with open_time_ms %d (%s)"
                    % (j, open_ms, label))
            elif lst[0][1] != price:  # Q10: one finding per failing side
                add("OUTCOME_UNLINKED", j, "first CANDLE (line %d) for %s has open %r, "
                    "OUTCOME says %r" % (lst[0][0], label, lst[0][1], price))

    # ---- 8.2 result ----------------------------------------------------------------------------
    hard = sorted({f[0] for f in findings if f[0] in HARD_NAMES})
    soft = sorted({f[0] for f in findings if f[0] in SOFT_NAMES})
    return {
        "verdict": "FAIL" if hard else "PASS",
        "findings": findings,
        "hard": hard,
        "soft": soft,
        "n_events": N,
        "head_hex": head_hex,
        "slots": slots,
        "missing": missing,
        "outcomes": outcomes,
    }


if __name__ == "__main__":  # tiny CLI: verify_indep.py FILE  (no anchor: empty mock)
    import sys

    class _EmptyAnchor:
        def get(self, journal_id, index):
            return None

        def latest(self, journal_id):
            return 0

    res = verify(sys.argv[1], _EmptyAnchor(), "cli", 0)
    print(json.dumps(res, indent=1, sort_keys=True, default=str))
