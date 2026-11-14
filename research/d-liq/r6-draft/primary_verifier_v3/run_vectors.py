"""Run the primary verifier (dliq_journal_verify_v3) UNCHANGED on a directory of D-LIQ r6 conformance vectors and compare its report with each expect.json.

usage:  python3 -I -B run_vectors.py --vectors DIR [--expect-digest HEX] [--expect-count N]

What this does and does not do (GPT, 2026-11-12: the primary verifier must not import the oracle and must be run unchanged on all vectors):
- the same code path for EVERY vector: verify(journal.jsonl, anchor, journal_id, verify_time_ms) with the default replay; no vector is special-cased, no expectation is edited;
- it reads from expect.json only the EXPECTED OUTPUT fields: verdict, hard, soft, findings, slots, missing, candles, replayed, analysis_eligible, plus journal_id,
  verify_time_ms and anchor (inputs). It does not read r6_only, r5_only_extra, cases or contract_refs and it does not import the oracle or the vector generator;
- findings are compared as multisets of (name, where) and, for FORCE_MSG_STRUCTURE and FORCE_UNKNOWN_KEY, also of the exact detail string (7.7b, 7.7c, 7.7f);
- it prints the vector-set digest: sha256 of the `sha256sum` lines of every file, sorted by BYTE order of the path with the prefix `vectors/`
  (= `find vectors -type f | LC_ALL=C sort | xargs sha256sum | sha256sum` run next to the directory), and the sha256 of every verifier source file that ran.
A pass means: this verifier agrees with the hand-written expectations of the vectors, which have one author with the verifier and the oracle. It is not independent evidence.
"""
import argparse
import hashlib
import json
import os
import sys
from collections import Counter
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import dliq_journal_verify_v3 as V      # noqa: E402

DETAIL_NAMES = ("FORCE_MSG_STRUCTURE", "FORCE_UNKNOWN_KEY")
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


def finding_keys(findings):
    out = []
    for name, where, detail in findings:
        out.append((name, where, detail if name in DETAIL_NAMES else None))
    return Counter(out)


def compare(report, expect):
    """Returns a list of problem strings (empty = the report equals the expectation)."""
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
    return problems


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--vectors", required=True, help="directory that holds one sub-directory per vector (journal.jsonl + expect.json)")
    ap.add_argument("--expect-digest", help="fail unless the vector-set digest equals this value")
    ap.add_argument("--expect-count", type=int, help="fail unless this many vectors are present")
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
            found = compare(report, expect)
        except Exception as exc:                       # a crash is a failure of the verifier, never a pass
            found = ["verifier raised %s: %s" % (type(exc).__name__, exc)]
        if found:
            problems += 1
            print("FAIL %s" % name)
            for line in found:
                print("     " + line)
        else:
            print("OK   %s  verdict=%s findings=%d" % (name, report["verdict"], len(report["findings"])))
    print("problems: %d" % problems)
    return 1 if problems else 0


if __name__ == "__main__":
    sys.exit(main())
