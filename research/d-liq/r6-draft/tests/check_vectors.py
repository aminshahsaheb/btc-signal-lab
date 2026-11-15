#!/usr/bin/env python3
"""Checks of the r6 conformance vectors (journal contract v3, r6-draft, contract section 10).

  python3 -I -B check_vectors.py [VECTORS_DIR]      # default: ./vectors ; exit code 0 only if every check passes

For every vector (journal.jsonl + expect.json) it checks:
  S   structure: canonical lines, seq == line (except the one vector that tests SEQ_GAP), strict canonical base64 and a matching hash of every MSG / CANDLE (a line is bad exactly when the
      expectation names RAW_HASH_MISMATCH for it), expect.json fields and the 8.2 verdict rule
  O   the ORACLE (oracle_r6.py, the rules that are new in r6) reproduces exactly the expected findings that are NEW in r6 (detail compared for the two FORCE findings)
  R5  the unchanged rules: the journal is handed to the existing r5 verifier (../../r5-draft/src/dliq_journal_verify_v2.py) after a documented transformation
      (see transform_for_r5), and its findings must equal  expected - r6_only + r5_only_extra  (name and where), with the same `slots` and `missing`. Because the SLOT
      fields of the vectors were written by hand (make_vectors.py) and the r5 verifier REPLAYS them, an absent SLOT_MISMATCH is an independent check of the hand-derived values
  D   the report keys that do not depend on the findings (vectors/EXPECT_DERIVED.json): n_events and head_hex against the oracle, outcomes against the r5 verifier
  C   coverage: every conformance case 1..27 of contract section 10 is named by at least one vector
  G   the vectors on disk are what make_vectors.py generates; V06's SLOT is identical to V01's (a KLINE connection changes no SLOT field)
What a pass means: the vectors agree with a second derivation (oracle) and with the existing, separately tested r5 verifier on the unchanged rules.
What it does NOT mean: nothing here is independent of the author of the contract text, there is no r6 verifier yet, and no real journal exists.
"""
import base64
import copy
import hashlib
import importlib.util
import json
import os
import sys
import tempfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import oracle_r6 as ORACLE            # noqa: E402

R5_SRC = HERE.parent.parent / "r5-draft" / "src"
HARD = {"BAD_ENCODING", "NOT_CANONICAL", "BAD_EVENT", "RAW_HASH_MISMATCH", "SEQ_GAP", "HEAD_MISMATCH", "RECEIPT_INVALID", "CHECKPOINT_ORDER",
        "TRUNCATION_OR_REPLACEMENT", "SLOT_OFF_GRID", "SLOT_HAS_OUTCOME_FIELDS", "DUPLICATE_SLOT", "DUPLICATE_OUTCOME", "OUTCOME_ORPHAN",
        "OUTCOME_BEFORE_ANCHOR", "OUTCOME_FOR_NONE_SLOT", "OUTCOME_TIMING", "OUTCOME_MISMATCH", "OUTCOME_UNLINKED", "CANDLE_CONFLICT", "CANDLE_NOT_LIVE",
        "SLOT_MISMATCH", "SLOT_EARLY_WRITE", "REPLAY_NOT_RUN", "CONN_FEED_CONFLICT", "MSG_CONN_UNKNOWN", "FORCE_MSG_STRUCTURE", "CANDLE_LINK",
        "CANDLE_PARSE", "CANDLE_FIELD_MISMATCH", "CANDLE_LAG_UNSET"}
SOFT = {"SLOT_LATE_ANCHOR", "SLOT_UNANCHORED", "SLOT_MISSING", "OUTCOME_UNCOVERED", "FORCE_UNKNOWN_KEY"}
ORACLE_NAMES = {"BAD_EVENT", "CONN_FEED_CONFLICT", "MSG_CONN_UNKNOWN", "FORCE_MSG_STRUCTURE", "FORCE_UNKNOWN_KEY", "CANDLE_LAG_UNSET", "HEAD_MISMATCH", "RAW_HASH_MISMATCH",
                "OUTCOME_UNLINKED"}
DETAIL_NAMES = {"FORCE_MSG_STRUCTURE", "FORCE_UNKNOWN_KEY", "OUTCOME_UNLINKED"}
DERIVED_FILE = "EXPECT_DERIVED.json"
DERIVED_KEYS = {"n_events", "head_hex", "outcomes"}
EXPECT_KEYS = {"id", "title", "cases", "contract_refs", "description", "journal_id", "verify_time_ms", "anchor", "findings", "r6_only", "r5_only_extra",
               "verdict", "hard", "soft", "replayed", "analysis_eligible", "slots", "missing", "candles"}
SEQ_GAP_VECTORS = ("V14",)


def canon(ev):
    return json.dumps(ev, sort_keys=True, separators=(",", ":"), ensure_ascii=True, allow_nan=False).encode("ascii")


def load(vdir):
    out = []
    for d in sorted(p for p in Path(vdir).iterdir() if p.is_dir()):
        out.append({"dir": d.name, "data": (d / "journal.jsonl").read_bytes(), "expect": json.loads((d / "expect.json").read_text(encoding="utf-8"))})
    return out


def split(data):
    lines = data.split(b"\n")
    assert lines[-1] == b"", "journal does not end with a newline"
    lines = lines[:-1]
    return lines, [json.loads(l.decode("ascii")) for l in lines]


def pairs(findings):
    return sorted((f[0], f[1]) for f in findings)


def verdict_rule(hard):
    """contract 8.2"""
    if any(h not in ("REPLAY_NOT_RUN", "CANDLE_LAG_UNSET") for h in hard):
        return "FAIL"
    return "INCOMPLETE" if hard else "PASS"


# --------------------------------------------------------------------------------------------------------------------------------------------------------
def strict_hash_ok(ev):
    """2.2, by the method `validate=True` + re-encoding (the oracle derives the same rule by hand): the text is canonical standard base64 and its bytes have the recorded SHA-256."""
    try:
        raw = base64.b64decode(ev["raw_b64"], validate=True)
    except Exception:
        return False
    return base64.b64encode(raw).decode("ascii") == ev["raw_b64"] and hashlib.sha256(raw).hexdigest() == ev["sha256"]


def check_structure(v):
    p, ex = [], v["expect"]
    vid = v["dir"].split("_")[0]
    if set(ex) != EXPECT_KEYS:
        p.append("expect.json keys differ: %s" % sorted(set(ex) ^ EXPECT_KEYS))
        return p
    if ex["id"] != vid:
        p.append("id %s does not match the directory %s" % (ex["id"], v["dir"]))
    if not v["data"].endswith(b"\n"):
        return p + ["journal does not end with a newline"]
    lines, events = split(v["data"])
    rhm = {f[1] for f in ex["findings"] if f[0] == "RAW_HASH_MISMATCH"}
    for n, (line, ev) in enumerate(zip(lines, events), 1):
        if canon(ev) != line:
            p.append("line %d is not canonical" % n)
        if ev["seq"] != n and vid not in SEQ_GAP_VECTORS:
            p.append("line %d has seq %r" % (n, ev["seq"]))
        if ev["t"] in ("MSG", "CANDLE"):
            good = strict_hash_ok(ev)
            if good == (n in rhm):
                p.append("line %d: raw_b64 / sha256 are %s under 2.2 but the expectation %s RAW_HASH_MISMATCH for it" % (n, "valid" if good else "invalid", "names" if good else "lacks"))
    if vid in SEQ_GAP_VECTORS and all(ev["seq"] == n for n, ev in enumerate(events, 1)):
        p.append("the SEQ_GAP vector has no seq difference")
    fl = ex["findings"]
    if fl != sorted(fl, key=lambda f: (f[1], f[0])):
        p.append("findings are not sorted by (where, name)")
    if len(fl) != len({(f[0], f[1], f[2]) for f in fl}):
        p.append("duplicate findings in expect.json")
    for f in fl:
        if len(f) != 3 or not isinstance(f[1], int) or (f[0] in DETAIL_NAMES) != isinstance(f[2], str):
            p.append("malformed finding %r (the two FORCE findings need a detail string, no other finding has one)" % (f,))
    if ex["hard"] != sorted({f[0] for f in fl if f[0] in HARD}) or ex["soft"] != sorted({f[0] for f in fl if f[0] in SOFT}):
        p.append("hard/soft lists do not match the findings")
    if ex["verdict"] != verdict_rule(ex["hard"]):
        p.append("verdict %s does not follow 8.2 from the hard list" % ex["verdict"])
    if ex["verdict"] == "PASS" or ex["analysis_eligible"] is not False or ex["replayed"] is not True:
        p.append("verdict PASS / analysis_eligible / replayed not as required while L is unset")
    if ("CANDLE_LAG_UNSET", 0) not in pairs(fl):
        p.append("CANDLE_LAG_UNSET@0 is missing (case 13)")
    if ex["candles"] != {}:
        p.append("`candles` must be empty: no CANDLE event exists in these vectors")
    names = pairs(fl)
    for x in ex["r6_only"]:
        if tuple(x) not in names:
            p.append("%r is listed as r6_only but is not an expected finding" % (x,))
    for x in ex["r5_only_extra"]:
        if tuple(x) in names:
            p.append("%r is listed as r5_only_extra but is also an expected finding" % (x,))
    taus = sorted({ev["tau_ms"] for ev in events if ev["t"] == "SLOT"})
    if sorted(int(k) for k in ex["slots"]) != taus:
        p.append("`slots` keys do not match the SLOT events")
    return p


def check_oracle(v):
    ex = v["expect"]
    want = sorted([f[0], f[1], f[2] if f[0] in DETAIL_NAMES else ""] for f in ex["findings"] if f[0] in ORACLE_NAMES)
    got = sorted([f[0], f[1], f[2] if f[0] in DETAIL_NAMES else ""] for f in ORACLE.findings(v["data"]))
    if want != got:
        return ["oracle differs: expected %r, oracle %r" % (want, got)]
    return []


def transform_for_r5(data):
    """The r5 verifier does not know r6 (feed, the structural reasons). To compare it with the vectors on everything that did NOT change:
    (1) every CONN / PING / MSG event of a connection recorded FROM its first valid `open` on, when that `open` has feed KLINE, becomes a SESSION event (same line number, so every
        `where` is kept); an event of that connection recorded before the `open` has no feed (2.3a) and stays;
    (2) every FORCE-side MSG whose frame is a parsable object with an r6 structural reason (st_top_level, ps_type, ps_ne_s, st_type, st_ne_1) gets o.s = "ETHUSDT",
        i.e. it is MALFORMED (symbol) for r5 exactly as it is MALFORMED (that reason) for r6, with the same E, the same recv_ms and therefore the same ledger and voids;
    (3) every MSG whose raw_b64 is UNDECODABLE under 2.2 (r5 decodes permissively, or fails, where r6 has no bytes) gets the canonical base64 of b"undecodable" with its sha256 kept: a
        non-JSON frame, MALFORMED for r5 as `undecodable_base64` is for r6 (same recv_ms, same ledger and voids), and RAW_HASH_MISMATCH for r5 too (the hash no longer matches).
    Nothing else is touched; the hash chain of the result is not the chain of the original (only the checkpoint vectors have a chain, and they need no change)."""
    lines, events = split(data)
    first = {}                       # conn_id -> (line, feed) of the first valid open
    for n, ev in enumerate(events, 1):
        if ev["t"] == "CONN" and ev["ev"] == "open" and ev.get("feed") in ORACLE.FEEDS and ev["conn_id"] not in first:
            first[ev["conn_id"]] = (n, ev["feed"])
    kline_from = {c: n for c, (n, f) in first.items() if f == "KLINE"}
    out = []
    for n, ev in enumerate(events, 1):
        if ev["t"] in ("CONN", "PING", "MSG") and ev["conn_id"] in kline_from and n >= kline_from[ev["conn_id"]]:
            ev = {"t": "SESSION", "seq": ev["seq"], "rec_ms": ev["rec_ms"]}
        elif ev["t"] == "MSG":
            raw = ORACLE.decode_raw(ev["raw_b64"])
            if raw is None:
                ev = dict(ev, raw_b64=base64.b64encode(b"undecodable").decode("ascii"))          # sha256 is kept, so r5 reports RAW_HASH_MISMATCH as well
            else:
                obj = ORACLE.parse_object(raw)
                if obj is not None and ORACLE.structure_reason(obj) is not None and isinstance(obj.get("o"), dict):
                    obj["o"]["s"] = "ETHUSDT"
                    raw = json.dumps(obj, separators=(",", ":")).encode("ascii")
                    ev = dict(ev, raw_b64=base64.b64encode(raw).decode("ascii"), sha256=hashlib.sha256(raw).hexdigest())
        out.append(canon(ev))
    return b"".join(l + b"\n" for l in out)


class MockAnchor:
    def __init__(self, entries):
        self.e = {x["index"]: x for x in entries}

    def get(self, journal_id, index):
        return self.e.get(index)

    def latest(self, journal_id):
        return max(self.e) if self.e else 0


def load_r5():
    sys.path.insert(0, str(R5_SRC))
    spec = importlib.util.spec_from_file_location("dliq_journal_verify_v2", R5_SRC / "dliq_journal_verify_v2.py")
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m


def check_r5(v, r5, derived=None):
    ex = v["expect"]
    data = transform_for_r5(v["data"])
    with tempfile.TemporaryDirectory() as td:
        path = os.path.join(td, "j.jsonl")
        with open(path, "wb") as fh:
            fh.write(data)
        res = r5.verify(path, MockAnchor(ex["anchor"]), ex["journal_id"], ex["verify_time_ms"], replay_slots=True)
    want = pairs(ex["findings"])
    for x in ex["r6_only"]:
        want.remove(tuple(x))
    want = sorted(want + [tuple(x) for x in ex["r5_only_extra"]])
    got = pairs(res["findings"])
    p = []
    if want != got:
        p.append("r5 verifier differs: expected %r, r5 %r" % (want, got))
    if {str(k): s for k, s in res["slots"].items()} != ex["slots"] or res["missing"] != ex["missing"]:
        p.append("r5 slots/missing differ: %r %r" % (res["slots"], res["missing"]))
    if res["n_events"] != v["data"].count(b"\n") or not res["replayed"]:
        p.append("r5 n_events / replayed differ")
    if derived is not None and {str(k): x for k, x in res["outcomes"].items()} != derived["outcomes"]:
        p.append("r5 outcomes differ from EXPECT_DERIVED.json: %r against %r" % (res["outcomes"], derived["outcomes"]))
    return p


def load_derived(vdir):
    """vectors/EXPECT_DERIVED.json -> {vector id: {n_events, head_hex, outcomes}}, or None when the file does not exist."""
    path = Path(vdir) / DERIVED_FILE
    if not path.exists():
        return None
    return json.loads(path.read_text(encoding="utf-8"))["vectors"]


def check_derived(vs, vdir, derived):
    """D: the supplement covers exactly the vectors, has exactly the three keys with sane values, and n_events / head_hex are what the oracle computes from the journal bytes
    (the r5 verifier cannot be asked for head_hex: its genesis differs); `outcomes` is compared with the r5 verifier in check_r5."""
    if derived is None:
        return ["%s is missing" % DERIVED_FILE]
    p = []
    ids = {v["dir"].split("_")[0] for v in vs}
    if set(derived) != ids:
        p.append("%s covers other vectors than the directories: %s" % (DERIVED_FILE, sorted(set(derived) ^ ids)))
    for v in vs:
        vid = v["dir"].split("_")[0]
        d = derived.get(vid)
        if d is None:
            continue
        if set(d) != DERIVED_KEYS:
            p.append("%s [D] keys differ: %s" % (v["dir"], sorted(set(d) ^ DERIVED_KEYS)))
            continue
        want = ORACLE.derived(v["data"])
        if d["n_events"] != want["n_events"] or isinstance(d["n_events"], bool):
            p.append("%s [D] n_events %r, oracle %r" % (v["dir"], d["n_events"], want["n_events"]))
        if d["head_hex"] != want["head_hex"]:
            p.append("%s [D] head_hex differs from the chain the oracle computes (v3 genesis)" % v["dir"])
        if not isinstance(d["outcomes"], dict) or any(x not in ("COVERED", "UNCOVERED") for x in d["outcomes"].values()):
            p.append("%s [D] outcomes must map tau_ms to COVERED or UNCOVERED" % v["dir"])
        taus = {str(e["tau_ms"]) for e in split(v["data"])[1] if e["t"] == "OUTCOME"}
        if set(d["outcomes"]) != taus:
            p.append("%s [D] outcomes name %s but the journal has OUTCOME events for %s" % (v["dir"], sorted(d["outcomes"]), sorted(taus)))
    return p


def check_coverage(vs):
    have = {c for v in vs for c in v["expect"]["cases"]}
    miss = sorted(set(range(1, 28)) - have)
    return ["conformance cases without a vector: %s" % miss] if miss else []


def check_slot_equality(vs):
    byid = {v["dir"].split("_")[0]: v for v in vs}
    if "V01" not in byid or "V06" not in byid:
        return ["V01 / V06 missing"]
    s1 = [e for e in split(byid["V01"]["data"])[1] if e["t"] == "SLOT"]
    s6 = [e for e in split(byid["V06"]["data"])[1] if e["t"] == "SLOT"]
    s1[0] = {k: x for k, x in s1[0].items() if k not in ("seq",)}
    s6[0] = {k: x for k, x in s6[0].items() if k not in ("seq",)}
    return [] if s1 == s6 else ["V06's SLOT differs from V01's: a KLINE connection must change no SLOT field"]


def check_generated(vdir):
    spec = importlib.util.spec_from_file_location("make_vectors", HERE / "make_vectors.py")
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    p = []
    want = {v["dir"]: v for v in m.build()}
    have = {d.name for d in Path(vdir).iterdir() if d.is_dir()}
    if set(want) != have:
        p.append("vector directories differ from the generator: %s" % sorted(set(want) ^ have))
    if not (Path(vdir) / DERIVED_FILE).exists() or (Path(vdir) / DERIVED_FILE).read_text(encoding="utf-8") != m.derived_text(list(want.values())):
        p.append("%s is not what make_vectors.py generates" % DERIVED_FILE)
    for name, v in want.items():
        d = Path(vdir) / name
        if not (d / "journal.jsonl").exists() or (d / "journal.jsonl").read_bytes() != v["journal"]:
            p.append("%s/journal.jsonl is not what make_vectors.py generates" % name)
        if not (d / "expect.json").exists() or (d / "expect.json").read_text(encoding="utf-8") != json.dumps(v["expect"], indent=1, sort_keys=True) + "\n":
            p.append("%s/expect.json is not what make_vectors.py generates" % name)
    return p


def run(vdir, *, generated=True, r5=None, oracle_check=check_oracle):
    """Returns the list of problems (empty = pass)."""
    vs = load(vdir)
    r5 = r5 or load_r5()
    derived = load_derived(vdir)
    problems = []
    for v in vs:
        for tag, fn in (("S", check_structure), ("O", oracle_check)):
            for msg in fn(v):
                problems.append("%s [%s] %s" % (v["dir"], tag, msg))
        if not any(x.startswith(v["dir"] + " [S]") for x in problems):
            for msg in check_r5(v, r5, (derived or {}).get(v["dir"].split("_")[0])):
                problems.append("%s [R5] %s" % (v["dir"], msg))
    for msg in check_derived(vs, vdir, derived) + check_coverage(vs) + check_slot_equality(vs):
        problems.append(msg)
    if generated:
        problems += check_generated(vdir)
    return problems


def main(argv):
    vdir = Path(argv[0]) if argv else HERE / "vectors"
    problems = run(vdir)
    vs = load(vdir)
    print("vectors: %d, cases covered: %s" % (len(vs), sorted({c for v in vs for c in v["expect"]["cases"]})))
    for p in problems:
        print("PROBLEM", p)
    print("problems: %d" % len(problems))
    return 1 if problems else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
