#!/usr/bin/env python3
"""Independent (clean-room) implementation of the SLOT replay of the D-LIQ journal
contract v2 r4-draft, section 7.

Written from the specification files only (JOURNAL_CONTRACT_v2_r4draft.md,
07_MESSAGE_CONTRACT_v1.md, protocol section 4 (Persian), protocol appendix B,
messages.jsonl).  Python 3 standard library only.  Run as ``python3 -I``.

PUBLIC API
    replay_journal(path) -> list of dict, one per reference SLOT, in file order
    check_journal(path)  -> list of (name, where, detail)   [SLOT_MISMATCH, SLOT_EARLY_WRITE]
    classify_frame(raw)  -> (class, reason_label)           [message contract, for tests]
    CLI: python3 -I replay_indep.py JOURNAL.jsonl   (prints check_journal(...) as JSON)

LINE NUMBERING
    ``line`` is the 1-based number of the physical line of the SLOT event: the first
    byte-run terminated by 0x0A is line 1, the next is line 2, ...  (This is the
    contract's ``where`` for SLOT_MISMATCH / SLOT_EARLY_WRITE, section 8.4.)

WHAT IS CHECKED TO DECIDE WHICH EVENTS ARE "VALID" (replay input)
    No hash chain, anchor, checkpoint or outcome check is performed.  Only:
      1.3  the file is cut into 0x0A-terminated lines; a final partial line (no 0x0A)
           is discarded; each line must be strict UTF-8, JSON, a JSON object, without
           duplicate keys at any depth, without NaN/Infinity/-Infinity and without any
           number token carrying a fraction or exponent.  The first line that violates
           this ends the parse: it and every later line are ignored.
           (NOT_CANONICAL lines are used as parsed; seq != line number does NOT make an
           event invalid; a RAW_HASH_MISMATCH does NOT make an event invalid.)
      2.1  `t` is a string and one of the nine known types; `seq` and `rec_ms` are
           JSON integers (not booleans); the per-type required fields exist and have the
           listed types (booleans are never accepted as integers; `dec` strings must
           match the grammar over the WHOLE string, a trailing newline is not allowed).
           An event violating 2.1 is excluded (BAD_EVENT).
    Only CONN, PING, MSG, CLOCK and SLOT events influence the replay; the other types
    are parsed and validated like all lines but never used.
"""

import base64
import decimal
import json
import re
import sys
from decimal import Decimal

# --------------------------------------------------------------------------- constants
V_PRE_MS = 960_000          # V = [tau - 960_000, tau + 10_000]  (closed)
LATE_MS = 10_000            # late rule / V upper edge
WINDOW_MS = 900_000         # W = [tau - 900_000, tau)           (half-open, on E)
MAX_GAP_MS = 200_000        # health: successive points at most this far apart
MIN_N_TOTAL = 5
MAX_CLOCK_OFFSET_MS = 250
TS_MIN = 1_700_000_000_000  # E, T range (protocol 4.2 item 3, exact values)
TS_MAX = 4_102_444_800_000
MAX_DEC_CHARS = 30

EVENT_TYPES = ("SESSION", "CONN", "PING", "MSG", "CLOCK", "CANDLE", "SLOT", "OUTCOME", "CHECKPOINT")
LEDGER_KEYS = ("MALFORMED", "NO_PRIMARY", "NON_PRIMARY", "OUT_OF_WINDOW", "LATE", "INELIGIBLE", "COUNTED")
SLOT_FIELDS = ("status", "reasons", "primary_conn", "N_total", "N_BUY", "N_SELL", "sumW_BUY",
               "sumW_SELL", "side", "malformed_voids", "ledger", "n_messages", "X_sn")

MALFORMED, INELIGIBLE, ELIGIBLE = "MALFORMED", "INELIGIBLE", "ELIGIBLE"

_DEC_RE = re.compile(r"(0|[1-9][0-9]*)(\.[0-9]+)?")      # used with fullmatch (no `$` newline quirk)

# 200-digit decimal context, used for every product / sum / difference / quotient.
_CTX = decimal.Context(prec=200, rounding=decimal.ROUND_HALF_EVEN,
                       Emin=decimal.MIN_EMIN, Emax=decimal.MAX_EMAX, capitals=1, clamp=0,
                       flags=[], traps=[decimal.InvalidOperation, decimal.DivisionByZero,
                                        decimal.Overflow])


# --------------------------------------------------------------------------- strict JSON
class _StrictJSONError(ValueError):
    pass


class _DuplicateKey(_StrictJSONError):
    pass


def _pairs_hook(pairs):
    d = {}
    for k, v in pairs:
        if k in d:
            raise _DuplicateKey(k)
        d[k] = v
    return d


def _reject_float(token):
    raise _StrictJSONError("number token with fraction/exponent: " + token)


def _reject_constant(token):
    raise _StrictJSONError("constant not allowed: " + token)


def _safe_int(token):
    """int() of a JSON integer token that also works beyond the 4300-digit str->int limit."""
    try:
        return int(token)
    except ValueError:
        neg = token.startswith("-")
        digits = token[1:] if neg else token
        v = 0
        for i in range(0, len(digits), 1000):
            chunk = digits[i:i + 1000]
            v = v * (10 ** len(chunk)) + int(chunk)
        return -v if neg else v


def _strict_loads(text):
    """json.loads with: duplicate keys rejected, NaN/Infinity rejected, floats rejected."""
    if text.startswith("﻿"):                     # a BOM is not JSON
        raise _StrictJSONError("BOM")
    return json.loads(text, object_pairs_hook=_pairs_hook, parse_float=_reject_float,
                      parse_constant=_reject_constant, parse_int=_safe_int)


def _is_int(v):
    """JSON integer: Python int but NOT bool."""
    return type(v) is int


# --------------------------------------------------------------------------- message contract
class _FrameFloat(float):
    """marker for number tokens with fraction/exponent inside a *frame* (never an integer)."""


def _frame_float(token):
    return _FrameFloat(0.0)


def _frame_loads(text):
    if text.startswith("﻿"):
        raise _StrictJSONError("BOM")
    return json.loads(text, object_pairs_hook=_pairs_hook, parse_float=_frame_float,
                      parse_constant=_reject_constant, parse_int=_safe_int)


def _valid_ts(v):
    return _is_int(v) and TS_MIN <= v <= TS_MAX


def _dec_ok(s):
    return isinstance(s, str) and len(s) <= MAX_DEC_CHARS and _DEC_RE.fullmatch(s) is not None


_O_REQUIRED = ("s", "S", "o", "f", "q", "p", "ap", "X", "l", "z", "T")
_O_STRINGS = ("s", "S", "o", "f", "q", "p", "ap", "X", "l", "z")


def _classify(raw):
    """-> (class, reason, E_valid_or_None, side_or_None, weight_or_None)

    `E_valid` is the value of E when the frame parsed as a JSON object (strict rules) and
    E is a JSON integer inside [TS_MIN, TS_MAX]; it is reported even when the frame is
    MALFORMED for another reason (needed for the void interval).
    """
    if raw is None:                                    # undecodable base64: no usable bytes
        return (MALFORMED, "base64", None, None, None)
    try:
        text = raw.decode("utf-8")                     # strict
    except UnicodeDecodeError:
        return (MALFORMED, "utf8", None, None, None)
    try:
        obj = _frame_loads(text)
    except _DuplicateKey:
        return (MALFORMED, "duplicate_key", None, None, None)
    except (ValueError, RecursionError):
        return (MALFORMED, "json", None, None, None)
    if not isinstance(obj, dict):
        return (MALFORMED, "not_object", None, None, None)
    E_valid = obj["E"] if ("E" in obj and _valid_ts(obj["E"])) else None

    def bad(reason):
        return (MALFORMED, reason, E_valid, None, None)

    for k in ("e", "E", "o"):
        if k not in obj:
            return bad("missing_" + k)
    o = obj["o"]
    if not isinstance(o, dict):
        return bad("o_not_object")
    for k in _O_REQUIRED:
        if k not in o:
            return bad("missing_o." + k)
    if not _valid_ts(obj["E"]):
        return bad("E_type_or_range")
    if not _valid_ts(o["T"]):
        return bad("T_type_or_range")
    for k in _O_STRINGS:
        if not isinstance(o[k], str):
            return bad("type_o." + k)
    if obj["e"] != "forceOrder":
        return bad("event_type")
    if o["s"] != "BTCUSDT":
        return bad("symbol")
    if "st" in obj and not (_is_int(obj["st"]) and obj["st"] == 1):
        return bad("st_not_1")
    if o["S"] not in ("BUY", "SELL"):
        return bad("side")
    for k in ("q", "p", "ap", "l", "z"):
        if not _dec_ok(o[k]):
            return bad("decimal_grammar." + k)
    # structurally valid
    z = Decimal(o["z"])
    ap = Decimal(o["ap"])
    if o["X"] != "FILLED":
        return (INELIGIBLE, "status", E_valid, o["S"], None)
    if z == 0:
        return (INELIGIBLE, "z_zero", E_valid, o["S"], None)
    if ap == 0:
        return (INELIGIBLE, "ap_zero", E_valid, o["S"], None)
    return (ELIGIBLE, None, E_valid, o["S"], _CTX.multiply(z, ap))


def classify_frame(raw):
    """Message contract class of one raw frame: (class, reason_label).  The class is
    the contract; the reason label is diagnostic."""
    c = _classify(raw)
    return (c[0], c[1])


# --------------------------------------------------------------------------- journal parsing
def _decode_b64(s):
    try:
        return base64.b64decode(s, validate=True)
    except (ValueError, TypeError):
        return None


def _is_dec(v):
    return isinstance(v, str) and _DEC_RE.fullmatch(v) is not None


def _all_str_list(v):
    return isinstance(v, list) and all(isinstance(x, str) for x in v)


def _ledger_ok(v):
    return isinstance(v, dict) and all(_is_int(x) for x in v.values())


_REQUIRED = {
    "SESSION": {},
    "CONN": {"conn_id": _is_int, "ev": lambda v: isinstance(v, str) and v in ("open", "close"),
             "ms": _is_int},
    "PING": {"conn_id": _is_int, "ms": _is_int},
    "MSG": {"conn_id": _is_int, "recv_ms": _is_int, "raw_b64": lambda v: isinstance(v, str),
            "sha256": lambda v: isinstance(v, str)},
    "CLOCK": {"offset_ms": _is_int, "ms": _is_int},
    "CANDLE": {"open_time_ms": _is_int, "open": _is_dec, "recv_ms": _is_int,
               "raw_b64": lambda v: isinstance(v, str), "sha256": lambda v: isinstance(v, str)},
    "SLOT": {"tau_ms": _is_int,
             "status": lambda v: isinstance(v, str) and v in ("VALID", "NONE"),
             "reasons": _all_str_list,
             "primary_conn": lambda v: v is None or _is_int(v),
             "N_total": _is_int, "N_BUY": _is_int, "N_SELL": _is_int, "side": _is_int,
             "malformed_voids": _is_int, "n_messages": _is_int,
             "sumW_BUY": _is_dec, "sumW_SELL": _is_dec,
             "X_sn": lambda v: v is None or isinstance(v, str),
             "ledger": _ledger_ok},
    "OUTCOME": {"tau_ms": _is_int,
                "status": lambda v: isinstance(v, str) and v in ("EVAL", "NO_PRICE")},
    "CHECKPOINT": {"anchored_seq": _is_int, "anchored_head": lambda v: isinstance(v, str),
                   "receipt": lambda v: isinstance(v, dict)},
}


def _valid_event(ev):
    """Section 2.1 (generic part + per-type required fields)."""
    t = ev.get("t")
    if not isinstance(t, str) or t not in EVENT_TYPES:
        return False
    if "seq" not in ev or not _is_int(ev["seq"]):
        return False
    if "rec_ms" not in ev or not _is_int(ev["rec_ms"]):
        return False
    for key, check in _REQUIRED[t].items():
        if key not in ev or not check(ev[key]):
            return False
    if t == "OUTCOME" and ev["status"] == "EVAL":
        for key, check in (("entry_open_ms", _is_int), ("exit_open_ms", _is_int),
                           ("entry_price", _is_dec), ("exit_price", _is_dec),
                           ("r_bps", lambda v: isinstance(v, str))):
            if key not in ev or not check(ev[key]):
                return False
    if t == "CHECKPOINT":
        r = ev["receipt"]
        for key, check in (("anchor_id", lambda v: isinstance(v, str)), ("index", _is_int),
                           ("seq", _is_int), ("head", lambda v: isinstance(v, str)),
                           ("time_ms", _is_int), ("time_resolution_ms", _is_int),
                           ("time_uncertainty_ms", _is_int)):
            if key not in r or not check(r[key]):
                return False
    return True


def _read_events(path):
    """Yield (line_no, event_dict) for every parsed line, in file order, stopping at the
    first line that violates 1.3 (BAD_ENCODING).  A final partial line is discarded."""
    with open(path, "rb") as fh:
        data = fh.read()
    if not data:
        return
    pieces = data.split(b"\n")
    lines = pieces[:-1]            # pieces[-1] is b"" (file ends with 0x0A) or the partial line
    for n, line in enumerate(lines, 1):
        try:
            text = line.decode("utf-8")
            obj = _strict_loads(text)
        except (UnicodeDecodeError, ValueError, RecursionError):
            return                                     # BAD_ENCODING: parsing stops here
        if not isinstance(obj, dict):
            return
        yield n, obj


# --------------------------------------------------------------------------- replay
class _Msg(object):
    __slots__ = ("conn", "recv", "cls", "E", "side", "w")

    def __init__(self, conn, recv, cls, E, side, w):
        self.conn, self.recv, self.cls, self.E, self.side, self.w = conn, recv, cls, E, side, w


class _State(object):
    def __init__(self):
        self.msgs = []             # replay input messages, file order
        self.open_ms = {}          # conn_id -> ms of FIRST open
        self.close_ms = {}         # conn_id -> ms of LAST close
        self.ftimes = {}           # conn_id -> [frame times] (MSG recv_ms and PING ms)
        self.clock = 0             # offset_ms of the LAST CLOCK event


def _ingest(state, ev):
    t = ev["t"]
    if t == "MSG":
        raw = _decode_b64(ev["raw_b64"])
        cls, _reason, E, side, w = _classify(raw)
        state.msgs.append(_Msg(ev["conn_id"], ev["recv_ms"], cls, E, side, w))
        state.ftimes.setdefault(ev["conn_id"], []).append(ev["recv_ms"])
    elif t == "PING":
        state.ftimes.setdefault(ev["conn_id"], []).append(ev["ms"])
    elif t == "CONN":
        if ev["ev"] == "open":
            state.open_ms.setdefault(ev["conn_id"], ev["ms"])
        else:
            state.close_ms[ev["conn_id"]] = ev["ms"]
    elif t == "CLOCK":
        state.clock = ev["offset_ms"]


def _primary_conn(state, tau, rec):
    v0, v1 = tau - V_PRE_MS, tau + LATE_MS
    best = None
    for c, op in state.open_ms.items():
        if best is not None and c >= best:
            continue
        stop = state.close_ms[c] if c in state.close_ms else rec
        pts = [op] + sorted(t for t in state.ftimes.get(c, ()) if op <= t <= stop)
        runs = []
        s = p = pts[0]
        for t in pts[1:]:
            if t - p <= MAX_GAP_MS:
                p = t
            else:
                runs.append((s, p))
                s = p = t
        runs.append((s, p))
        if any(rs <= v0 and min(rp + MAX_GAP_MS, stop) >= v1 for rs, rp in runs):
            best = c
    return best


def _replay_slot(state, tau, rec):
    v0, v1 = tau - V_PRE_MS, tau + LATE_MS
    primary = _primary_conn(state, tau, rec)

    ledger = dict((k, 0) for k in LEDGER_KEYS)
    voids = 0
    n_buy = n_sell = 0
    sum_buy = Decimal(0)
    sum_sell = Decimal(0)
    for m in state.msgs:
        if m.cls == MALFORMED:
            ledger["MALFORMED"] += 1
            if v0 <= m.recv <= v1 or (m.E is not None and v0 <= m.E <= v1):
                voids += 1
        elif primary is None:
            ledger["NO_PRIMARY"] += 1
        elif m.conn != primary:
            ledger["NON_PRIMARY"] += 1
        elif not (tau - WINDOW_MS <= m.E < tau):
            ledger["OUT_OF_WINDOW"] += 1
        elif m.recv > tau + LATE_MS:
            ledger["LATE"] += 1
        elif m.cls == INELIGIBLE:
            ledger["INELIGIBLE"] += 1
        else:
            ledger["COUNTED"] += 1
            if m.side == "BUY":
                n_buy += 1
                sum_buy = _CTX.add(sum_buy, m.w)
            else:
                n_sell += 1
                sum_sell = _CTX.add(sum_sell, m.w)
    n_total = n_buy + n_sell

    reasons = []
    if primary is None:
        reasons.append("GAP")
    if abs(state.clock) > MAX_CLOCK_OFFSET_MS:
        reasons.append("CLOCK")
    if voids > 0:
        reasons.append("MALFORMED")
    if primary is not None and n_total < MIN_N_TOTAL:
        reasons.append("N_TOTAL")
    if n_total > 0 and sum_buy == sum_sell and "N_TOTAL" not in reasons:
        reasons.append("ZERO")

    status = "NONE" if reasons else "VALID"
    if reasons:
        side = 0
    else:
        side = 1 if sum_buy > sum_sell else -1
    if n_total == 0:
        x_sn = None
    else:
        q = _CTX.divide(_CTX.subtract(sum_buy, sum_sell), _CTX.add(sum_buy, sum_sell))
        x_sn = repr(float(q))
    return {
        "status": status,
        "reasons": reasons,
        "primary_conn": primary,
        "N_total": n_total,
        "N_BUY": n_buy,
        "N_SELL": n_sell,
        "sumW_BUY": format(sum_buy, "f"),
        "sumW_SELL": format(sum_sell, "f"),
        "side": side,
        "malformed_voids": voids,
        "ledger": ledger,
        "n_messages": len(state.msgs),
        "X_sn": x_sn,
    }


def replay_journal(path):
    """One dict per reference SLOT (the first valid SLOT of each tau_ms), in file order."""
    results = []
    state = _State()
    seen_tau = set()
    for line_no, ev in _read_events(path):
        if not _valid_event(ev):
            continue                                   # BAD_EVENT: excluded from everything
        if ev["t"] != "SLOT":
            _ingest(state, ev)                         # state = valid events at lines < current
            continue
        tau = ev["tau_ms"]
        if tau in seen_tau:
            continue                                   # DUPLICATE_SLOT: not a reference SLOT
        seen_tau.add(tau)
        rec = ev["rec_ms"]
        replayed = _replay_slot(state, tau, rec)
        journalled = {}
        for k in SLOT_FIELDS:
            v = ev[k]
            if k == "reasons":
                v = list(v)
            elif k == "ledger":
                v = dict(v)
            journalled[k] = v
        results.append({
            "line": line_no,           # 1-based physical line number of the SLOT event
            "tau_ms": tau,
            "rec_ms": rec,
            "fields": replayed,
            "journalled": journalled,
            "early_write": rec < tau + LATE_MS,        # contract 7.4
        })
    return results


def check_journal(path):
    """Section 7 findings: (name, where, detail) tuples, per reference SLOT in file order
    (SLOT_MISMATCH first, then SLOT_EARLY_WRITE for the same SLOT)."""
    findings = []
    for r in replay_journal(path):
        a, b = r["fields"], r["journalled"]
        diff = sorted(k for k in SLOT_FIELDS if not (type(a[k]) is type(b[k]) and a[k] == b[k]))
        if diff:
            findings.append(("SLOT_MISMATCH", r["line"], ",".join(diff)))
        if r["early_write"]:
            findings.append(("SLOT_EARLY_WRITE", r["line"], ""))
    return findings


def _main(argv):
    if len(argv) != 2:
        sys.stderr.write("usage: python3 -I replay_indep.py JOURNAL.jsonl\n")
        return 2
    print(json.dumps([list(f) for f in check_journal(argv[1])]))
    return 0


if __name__ == "__main__":
    sys.exit(_main(sys.argv))
