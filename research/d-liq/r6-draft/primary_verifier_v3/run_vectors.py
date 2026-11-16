"""Run the primary verifier (dliq_journal_verify_v3) UNCHANGED on a directory of D-LIQ r6 conformance vectors and compare its report with each expect.json.

usage:  python3 -I -B run_vectors.py --vectors DIR [--expect-digest HEX] [--expect-count N] [--require-derived]

What this does and does not do (GPT, 2026-11-12: the primary verifier must not import the oracle and must be run unchanged on all vectors):
- the same code path for EVERY vector: verify(journal.jsonl, anchor, journal_id, verify_time_ms) with the default replay; no vector is special-cased, no expectation is edited;
- it reads from expect.json only the EXPECTED OUTPUT fields: verdict, hard, soft, findings, slots, missing, candles, replayed, analysis_eligible, plus journal_id,
  verify_time_ms and anchor (inputs). It does not read r6_only, r5_only_extra, cases or contract_refs and it does not import the oracle or the vector generator;
- the other three report keys of contract 8.2, n_events, head_hex and outcomes, are NORMATIVE outputs (3.2 defines head_hex, 6.4 outcomes) and are compared when the vectors directory
  holds EXPECT_DERIVED.json (vectors of PR #40 from commit 7bb06f0 on); the two earlier pins (d10ba97, 0b2dc95) have no such file and the run says plainly that these three keys were
  NOT COMPARED for them. --require-derived makes a missing or incomplete file an error. All twelve report keys of 8.2 are therefore compared on a vector set that has the file;
- findings are compared as multisets of (name, where) and, for FORCE_MSG_STRUCTURE and FORCE_UNKNOWN_KEY, also of the exact detail string (7.7b, 7.7c, 7.7f); for OUTCOME_UNLINKED also of the
  endpoint (the detail BEGINS `endpoint=entry` or `endpoint=exit`, the rest is diagnostic, 6.9) and the two findings of one OUTCOME must come in the order entry, then exit. NOT compared
  (diagnostic only): every other detail string, and the relative order of findings other than the OUTCOME_UNLINKED ones;
- it prints the vector-set digest: sha256 of the `sha256sum` lines of every file, sorted by BYTE order of the path with the prefix `vectors/`
  (= `find vectors -type f | LC_ALL=C sort | xargs sha256sum | sha256sum` run next to the directory), and the sha256 of every verifier source file that ran.
A pass means: this verifier agrees with the hand-written expectations of the vectors, which have one author with the verifier and the oracle. It is not independent evidence.
"""
import argparse
import hashlib
import json
import os
import re
import sys
from collections import Counter
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import dliq_journal_verify_v3 as V      # noqa: E402

DETAIL_NAMES = ("FORCE_MSG_STRUCTURE", "FORCE_UNKNOWN_KEY")      # compared by their exact detail string
ENDPOINT = re.compile(r"endpoint=(entry|exit)(?![A-Za-z0-9_])")  # OUTCOME_UNLINKED: only this prefix of the detail is compared (6.9)
DERIVED_FILE = "EXPECT_DERIVED.json"
DERIVED_KEYS = ("n_events", "head_hex", "outcomes")
VERIFIER_FILES = ("dliq_journal_verify_v3.py", "dliq_msg_contract_v3.py", "r6_rules.py")


class MockAnchor:
    """The anchor interface of contract 4.1 over the entries listed in expect.json (a list of dicts with an `index`)."""

    def __init__(self, entries):
        self.entries = {e["index"]: e for e in entries}

    def get(self, journal_id, index):
        return self.entries.get(index)

    def latest(self, journal_id):
        return max(self.entries) if self.entries else 0


def vector_set_digest(vdir):
    paths = []
    for base, _dirs, names in os.walk(vdir):
        for name in names:
            rel = os.path.relpath(os.path.join(base, name), vdir).replace(os.sep, "/")
            paths.append("vectors/" + rel)
    lines = []
    for p in sorted(paths, key=lambda x: x.encode("utf-8")):
        with open(os.path.join(vdir, p[len("vectors/"):]), "rb") as fh:
            lines.append("%s  %s\n" % (hashlib.sha256(fh.read()).hexdigest(), p))
    return hashlib.sha256("".join(lines).encode("utf-8")).hexdigest(), len(paths)


def finding_key(name, where, detail):
    """What is compared of one finding: (name, where, detail-or-None)."""
    if name in DETAIL_NAMES:
        return (name, where, detail)
    if name == "OUTCOME_UNLINKED":
        m = ENDPOINT.match(detail if isinstance(detail, str) else "")
        return (name, where, m.group(0) if m else detail)          # a detail without the prefix never equals an expected `endpoint=...`
    return (name, where, None)


def finding_keys(findings):
    return Counter(finding_key(name, where, detail) for name, where, detail in findings)


def unlinked_order(findings):
    """The OUTCOME_UNLINKED findings in the order they were reported: (where, endpoint) (6.9: entry, then exit, for each OUTCOME)."""
    return [finding_key(n, w, d)[1:] for n, w, d in findings if n == "OUTCOME_UNLINKED"]


def compare(report, expect, derived=None):
    """Returns a list of problem strings (empty = the report equals the expectation). `derived` = {n_events, head_hex, outcomes} of this vector from EXPECT_DERIVED.json, or None when the
    vector set has no such file (those three keys are then NOT compared, and main() says so)."""
    problems = []
    for key in ("verdict", "hard", "soft", "missing", "replayed", "analysis_eligible"):
        if report[key] != expect[key]:
            problems.append("%s: got %r, expected %r" % (key, report[key], expect[key]))
    if {str(k): v for k, v in report["slots"].items()} != expect["slots"]:
        problems.append("slots: got %r, expected %r" % (report["slots"], expect["slots"]))
    if {str(k): v for k, v in report["candles"].items()} != expect["candles"]:
        problems.append("candles: got %r, expected %r" % (report["candles"], expect["candles"]))
    got = finding_keys(report["findings"])
    want = finding_keys(expect["findings"])
    for key in sorted((got - want).elements(), key=repr):
        problems.append("unexpected finding %r" % (key,))
    for key in sorted((want - got).elements(), key=repr):
        problems.append("missing finding %r" % (key,))
    if unlinked_order(report["findings"]) != unlinked_order(expect["findings"]):
        problems.append("OUTCOME_UNLINKED order: got %r, expected %r" % (unlinked_order(report["findings"]), unlinked_order(expect["findings"])))
    if derived is not None:
        for key in ("n_events", "head_hex"):
            if report[key] != derived[key]:
                problems.append("%s: got %r, expected %r" % (key, report[key], derived[key]))
        if {str(k): v for k, v in report["outcomes"].items()} != derived["outcomes"]:
            problems.append("outcomes: got %r, expected %r" % (report["outcomes"], derived["outcomes"]))
    return problems


def load_derived(vdir, names):
    """(derived, problems): {vector id: {n_events, head_hex, outcomes}} from vectors/EXPECT_DERIVED.json, or None when the file does not exist. A file that exists must name exactly
    the vectors present and exactly the three keys for each."""
    path = os.path.join(vdir, DERIVED_FILE)
    if not os.path.isfile(path):
        return None, []
    with open(path, encoding="utf-8") as fh:
        data = json.load(fh)
    derived = data["vectors"]
    problems = []
    ids = {n.split("_")[0] for n in names}
    if set(derived) != ids:
        problems.append("%s names other vectors than the directories: %s" % (DERIVED_FILE, sorted(set(derived) ^ ids)))
    for vid, d in derived.items():
        if set(d) != set(DERIVED_KEYS):
            problems.append("%s: %s has keys %s, expected %s" % (DERIVED_FILE, vid, sorted(d), sorted(DERIVED_KEYS)))
    return derived, problems


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--vectors", required=True, help="directory that holds one sub-directory per vector (journal.jsonl + expect.json)")
    ap.add_argument("--expect-digest", help="fail unless the vector-set digest equals this value")
    ap.add_argument("--expect-count", type=int, help="fail unless this many vectors are present")
    ap.add_argument("--require-derived", action="store_true", help="fail unless EXPECT_DERIVED.json is present (n_events, head_hex and outcomes are then compared for every vector)")
    args = ap.parse_args(argv)
    vdir = os.path.abspath(args.vectors)
    problems = 0
    names = sorted(d for d in os.listdir(vdir) if os.path.isdir(os.path.join(vdir, d)))
    digest, nfiles = vector_set_digest(vdir)
    print("verifier files (sha256):")
    for name in VERIFIER_FILES:
        with open(HERE / name, "rb") as fh:
            print("  %s  %s" % (hashlib.sha256(fh.read()).hexdigest(), name))
    print("vectors: %d (files: %d)" % (len(names), nfiles))
    print("vector-set digest: %s" % digest)
    if args.expect_digest is not None and digest != args.expect_digest:
        print("DIGEST MISMATCH: expected %s" % args.expect_digest)
        problems += 1
    if args.expect_count is not None and len(names) != args.expect_count:
        print("COUNT MISMATCH: expected %d vectors" % args.expect_count)
        problems += 1
    if not names:
        print("NO VECTORS FOUND")
        problems += 1
    derived, dproblems = load_derived(vdir, names)
    for line in dproblems:
        print("DERIVED FILE PROBLEM: " + line)
        problems += 1
    if derived is None and args.require_derived:
        print("DERIVED FILE MISSING: %s is required (--require-derived)" % DERIVED_FILE)
        problems += 1
    compared = 0
    for name in names:
        jpath = os.path.join(vdir, name, "journal.jsonl")
        epath = os.path.join(vdir, name, "expect.json")
        if not (os.path.isfile(jpath) and os.path.isfile(epath)):
            print("FAIL %s: journal.jsonl or expect.json is missing" % name)
            problems += 1
            continue
        with open(epath, encoding="utf-8") as fh:
            expect = json.load(fh)
        try:
            report = V.verify(jpath, MockAnchor(expect["anchor"]), expect["journal_id"], expect["verify_time_ms"])
            d = None if derived is None else derived.get(name.split("_")[0])
            if d is not None and set(d) == set(DERIVED_KEYS):
                compared += 1
                found = compare(report, expect, d)
            else:
                found = compare(report, expect)
                if derived is not None:
                    found.append("no complete entry for this vector in %s" % DERIVED_FILE)
        except Exception as exc:                       # a crash is a failure of the verifier, never a pass
            found = ["verifier raised %s: %s" % (type(exc).__name__, exc)]
        if found:
            problems += 1
            print("FAIL %s" % name)
            for line in found:
                print("     " + line)
        else:
            print("OK   %s  verdict=%s findings=%d" % (name, report["verdict"], len(report["findings"])))
    if compared == len(names) and names:
        print("report keys n_events, head_hex, outcomes: compared for %d of %d vectors (all twelve report keys of 8.2 are compared)" % (compared, len(names)))
    else:
        print("report keys n_events, head_hex, outcomes: NOT COMPARED for %d of %d vectors (no %s for them)" % (len(names) - compared, len(names), DERIVED_FILE))
    print("problems: %d" % problems)
    return 1 if problems else 0


if __name__ == "__main__":
    sys.exit(main())
