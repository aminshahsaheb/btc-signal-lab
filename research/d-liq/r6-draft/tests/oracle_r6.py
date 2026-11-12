"""A small ORACLE for the rules that are NEW in contract r6 (journal contract v3). Written from the r6 TEXT (research/d-liq/r6-draft/contract/JOURNAL_CONTRACT_v3.md,
pull request #39) by the same author as the text and the vectors: it is a second derivation of the hand-written vector expectations, not independent evidence.

Revision 2026-11-12: follows the text as amended by GPT's four answers of that day (unknown keys per occurrence with location, reason ps_no_s, feed from the first
valid open on, `o` not an object); the amended text is on the branch of PR #39.

Scope (exactly these findings; everything else is out of scope and is cross-checked against the r5 verifier instead, see check_vectors.py):
  BAD_EVENT for a CONN event whose `feed` is missing or not "FORCE" / "KLINE"   (2.1)
  CONN_FEED_CONFLICT (2.3b), MSG_CONN_UNKNOWN (2.3c)
  FORCE_MSG_STRUCTURE and FORCE_UNKNOWN_KEY (7.5a, 7.7)
  CANDLE_LAG_UNSET (6.8, while L is unset)
  HEAD_MISMATCH computed with the v3 genesis string (3.2, 3.3, 4.2b)
No journal, network, clock or file other than the bytes passed in is used."""
import base64
import hashlib
import json

GENESIS_V3 = b"DLIQ-JOURNAL-v3-GENESIS"
FEEDS = ("FORCE", "KLINE")
TOP_KNOWN = ("e", "E", "o")
O_KNOWN = ("s", "S", "o", "f", "q", "p", "ap", "X", "l", "z", "T", "ps", "st")
REASONS = ("st_top_level", "ps_type", "ps_no_s", "ps_ne_s", "st_type", "st_ne_1")


def _no_dups(pairs):
    d = {}
    for k, v in pairs:
        if k in d:
            raise ValueError("duplicate key")
        d[k] = v
    return d


def _bad_const(name):
    raise ValueError("bad constant " + name)


def parse_object(raw):
    """The strict parse of 7.7a: UTF-8, no duplicate key at any depth, no NaN / Infinity, a JSON object. None if it fails."""
    try:
        obj = json.loads(raw.decode("utf-8"), object_pairs_hook=_no_dups, parse_constant=_bad_const)
    except Exception:
        return None
    return obj if isinstance(obj, dict) else None


def _is_int(x):
    return isinstance(x, int) and not isinstance(x, bool)


def structure_reason(obj):
    """The FIRST of the six reasons of 7.5a that applies to a parsed forceOrder object, else None. If `o` is not an object only st_top_level can apply."""
    if "st" in obj:
        return "st_top_level"
    o = obj.get("o")
    if isinstance(o, dict):
        if "ps" in o:
            if not isinstance(o["ps"], str):
                return "ps_type"
            if "s" not in o:
                return "ps_no_s"
            if o["ps"] != o["s"]:
                return "ps_ne_s"
        if "st" in o:
            if not _is_int(o["st"]):
                return "st_type"
            if o["st"] != 1:
                return "st_ne_1"
    return None


def unknown_keys(obj):
    """Unknown keys (7.5a, 7.7c): top level other than e, E, o and the forbidden st (written as the name); inside o other than the known ones (written o.<name>).
    One entry per occurrence, sorted by code point of the written string, none dropped as a duplicate."""
    names = [k for k in obj if k not in TOP_KNOWN and k != "st"]
    o = obj.get("o")
    if isinstance(o, dict):
        names += ["o." + k for k in o if k not in O_KNOWN]
    return sorted(names)


def parse_journal(data):
    lines = data.split(b"\n")
    if lines and lines[-1] == b"":
        lines = lines[:-1]
    return lines, [json.loads(l.decode("ascii")) for l in lines]


def findings(data):
    """data: the journal file bytes. Returns a sorted list of [name, where, detail] (detail is "" except for the two FORCE findings)."""
    lines, events = parse_journal(data)
    out = []
    valid_conn = set()               # lines of CONN events that are valid with respect to `feed`
    first_open = {}                  # conn_id -> (line, feed) of its first valid open; the feed applies from that line on (2.3a)
    for n, ev in enumerate(events, 1):
        if ev.get("t") != "CONN":
            continue
        if ev.get("feed") not in FEEDS:
            out.append(["BAD_EVENT", n, ""])
            continue
        valid_conn.add(n)
        if ev["ev"] == "open" and ev["conn_id"] not in first_open:
            first_open[ev["conn_id"]] = (n, ev["feed"])
    for n, ev in enumerate(events, 1):
        if n in valid_conn and ev["conn_id"] in first_open and first_open[ev["conn_id"]][0] < n and ev["feed"] != first_open[ev["conn_id"]][1]:
            out.append(["CONN_FEED_CONFLICT", n, ""])
    for n, ev in enumerate(events, 1):
        if ev.get("t") != "MSG":
            continue
        c = ev["conn_id"]
        feed = first_open[c][1] if c in first_open and first_open[c][0] < n else None     # the feed of the connection AT THIS LINE (None: no feed)
        if feed is None:
            out.append(["MSG_CONN_UNKNOWN", n, ""])
        if feed == "KLINE":
            continue                                   # a KLINE message is never examined by 7.7; a message without a feed is (2.3c)
        obj = parse_object(base64.b64decode(ev["raw_b64"]))
        if obj is None:
            continue
        reason = structure_reason(obj)
        if reason is not None:
            out.append(["FORCE_MSG_STRUCTURE", n, "conn_id=%d reason=%s" % (c, reason)])
        keys = unknown_keys(obj)
        if keys:
            out.append(["FORCE_UNKNOWN_KEY", n, "conn_id=%d keys=%s" % (c, ",".join(keys))])
    heads = [hashlib.sha256(GENESIS_V3).digest()]
    for line in lines:
        heads.append(hashlib.sha256(heads[-1] + line).digest())
    for n, ev in enumerate(events, 1):
        if ev.get("t") == "CHECKPOINT":
            k = ev["anchored_seq"]
            if 0 < k <= len(events) and heads[k].hex() != ev["anchored_head"]:
                out.append(["HEAD_MISMATCH", n, ""])
    out.append(["CANDLE_LAG_UNSET", 0, ""])
    return sorted(out, key=lambda f: (f[1], f[0], f[2]))
