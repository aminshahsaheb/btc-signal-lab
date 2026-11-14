"""The r6-specific rules of the primary verifier (journal contract v3), written from the contract text
(PR #39, commit 8969b65e716ba290041571ebf2ada64a7cc847db, research/d-liq/r6-draft/contract/JOURNAL_CONTRACT_v3.md) sections 2.3, 3.2, 7.2, 7.5a, 7.7 and 8.4.

This module is the ONLY place where the r6 rules live; the rest of the package is the r5 code with small, listed changes (see README.md and the two
PROVENANCE_*.diff files). It does not import the conformance-vector oracle (research/d-liq/r6-draft/tests/oracle_r6.py) and must not: the primary verifier is
only evidence if it is run against the vectors without having read their reference implementation (GPT, 2026-11-11).

DRAFT. Written by the author of the contract text and of the vectors: not independent. Python 3 standard library only; no network, no wall clock.
"""
import base64
import json

GENESIS_V3 = b"DLIQ-JOURNAL-v3-GENESIS"                       # 3.2
FEEDS = ("FORCE", "KLINE")                                     # 2.1, 2.3
STRUCTURE_REASONS = ("st_top_level", "ps_type", "ps_no_s", "ps_ne_s", "st_type", "st_ne_1")      # 7.5a, in this order
KNOWN_TOP_KEYS = frozenset(("e", "E", "o"))                    # 7.5a (a top-level `st` is the forbidden key, not an unknown one)
KNOWN_O_KEYS = frozenset(("s", "S", "o", "f", "q", "p", "ap", "X", "l", "z", "T", "ps", "st"))


class _DuplicateKey(Exception):
    pass


def _no_duplicates(pairs):
    out = {}
    for key, value in pairs:
        if key in out:
            raise _DuplicateKey(key)
        out[key] = value
    return out


def _no_constants(token):
    raise ValueError("non-finite JSON constant " + token)


def is_json_integer(x):
    """A JSON integer as 7.5a means it: a boolean is not one, a number with a fraction or an exponent is not one."""
    return isinstance(x, int) and not isinstance(x, bool)


def decode_raw(event):
    """The bytes of a MSG event's raw_b64, or None when they cannot be decoded (QUESTIONS.md Q1)."""
    try:
        return base64.b64decode(event["raw_b64"])
    except Exception:
        return None


def parse_strict_object(raw):
    """7.7a: the frame is parsable iff it is strict UTF-8, JSON without a duplicate key at any depth and without NaN / Infinity, and a JSON object.
    Returns the parsed dict, else None."""
    if raw is None:
        return None
    try:
        value = json.loads(raw.decode("utf-8"), object_pairs_hook=_no_duplicates, parse_constant=_no_constants)
    except Exception:
        return None
    return value if isinstance(value, dict) else None


def structure_reason(msg):
    """7.5a: the FIRST applicable reason, in the order of STRUCTURE_REASONS, for a parsed forceOrder object; None if none applies.
    The reasons that look inside `o` apply only when `o` is a JSON object; `st_top_level` looks at the top level only."""
    o = msg.get("o")
    o = o if isinstance(o, dict) else None
    ps = o.get("ps") if o is not None else None
    ps_is_string = o is not None and "ps" in o and isinstance(ps, str)
    tests = (
        ("st_top_level", "st" in msg),
        ("ps_type", o is not None and "ps" in o and not isinstance(ps, str)),
        ("ps_no_s", ps_is_string and "s" not in o),
        ("ps_ne_s", ps_is_string and "s" in o and ps != o["s"]),
        ("st_type", o is not None and "st" in o and not is_json_integer(o["st"])),
        ("st_ne_1", o is not None and "st" in o and is_json_integer(o["st"]) and o["st"] != 1),
    )
    for name, applies in tests:
        if applies:
            return name
    return None


def unknown_key_entries(msg):
    """7.7c: one entry per unknown key OCCURRENCE: a top-level key as its name, a key inside `o` as `o.<name>`; sorted by code point, nothing dropped."""
    entries = [key for key in msg if key not in KNOWN_TOP_KEYS and key != "st"]
    o = msg.get("o")
    if isinstance(o, dict):
        entries.extend("o." + key for key in o if key not in KNOWN_O_KEYS)
    return sorted(entries)


def first_opens(valid):
    """2.3a: conn_id -> (line, feed) of the FIRST valid `open` CONN event of that connection id. `valid` maps line -> event (valid per 2.1)."""
    opens = {}
    for line in sorted(valid):
        ev = valid[line]
        if ev["t"] == "CONN" and ev["ev"] == "open" and ev["conn_id"] not in opens:
            opens[ev["conn_id"]] = (line, ev["feed"])
    return opens


def feed_at(opens, conn_id, line):
    """2.3a / 2.3c: the feed of an event of connection `conn_id` recorded at `line`: the feed of the first valid open if that open is at this line or an earlier one,
    else None (no feed, never given one retroactively)."""
    found = opens.get(conn_id)
    if found is not None and found[0] <= line:
        return found[1]
    return None


def is_kline_event(opens, conn_id, line):
    """7.2: an event of a connection recorded from its first valid open on, when that open names KLINE, is no input of the replay."""
    return feed_at(opens, conn_id, line) == "KLINE"


def feed_findings(valid, opens):
    """2.3b CONN_FEED_CONFLICT and 2.3c MSG_CONN_UNKNOWN. `where` = the physical line of the event."""
    out = []
    for line in sorted(valid):
        ev = valid[line]
        found = opens.get(ev.get("conn_id"))
        if ev["t"] == "CONN":
            if found is not None and line > found[0] and ev["feed"] != found[1]:
                out.append(["CONN_FEED_CONFLICT", line, "conn_id=%d names feed %s after the first open (line %d) named %s" % (ev["conn_id"], ev["feed"], found[0], found[1])])
        elif ev["t"] == "MSG":
            if found is None or found[0] > line:
                out.append(["MSG_CONN_UNKNOWN", line, "conn_id=%d has no valid open before this MSG" % ev["conn_id"]])
    return out


def run_level_findings(valid, opens):
    """7.7: for EVERY valid MSG whose connection feed is FORCE or which has no feed at its line, exactly once, independent of any SLOT:
    FORCE_MSG_STRUCTURE (hard; detail exactly `conn_id=<int> reason=<reason>`) and FORCE_UNKNOWN_KEY (soft; detail exactly `conn_id=<int> keys=<e1,e2,...>`).
    `where` = the physical line of the MSG."""
    out = []
    for line in sorted(valid):
        ev = valid[line]
        if ev["t"] != "MSG" or is_kline_event(opens, ev["conn_id"], line):
            continue
        msg = parse_strict_object(decode_raw(ev))
        if msg is None:
            continue
        reason = structure_reason(msg)
        if reason is not None:
            out.append(["FORCE_MSG_STRUCTURE", line, "conn_id=%d reason=%s" % (ev["conn_id"], reason)])
        keys = unknown_key_entries(msg)
        if keys:
            out.append(["FORCE_UNKNOWN_KEY", line, "conn_id=%d keys=%s" % (ev["conn_id"], ",".join(keys))])
    return out
