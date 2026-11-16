"""Deliberate breakages of the handoff tools; the unit tests (test_handoff.py) must notice each. Sanity check that the tests are not vacuous; written by the author of the tools; NOT independent.

usage:  python3 -I -B sanity_mutants.py            (the comparator, harness and document mutants need nothing else)
        DLIQ_R6_VECTORS=... DLIQ_R6_CONTRACT=... python3 -I -B sanity_mutants.py     (the builder mutants then run too; without the sources they are listed as SKIPPED, which is not a pass)
        ... and DLIQ_R6_SPEC=...                                                       (the mutants of the `spec/` part of the builder then run too; without it they are listed as SKIPPED, which is not a pass)
Each mutant is applied to a temporary copy of the package directory; exit status of the whole run is 1 if a mutant survives or does not apply exactly once."""
import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
NEEDS_SOURCES = {"B", "S"}
NEEDS_SPEC = {"S"}
MUTANTS = [
    # (kind, name, file, old, new)
    ("C", "the comparator ignores n_events", "compare_outputs.py", '("verdict", "replayed", "analysis_eligible", "n_events", "head_hex", "hard", "soft")', '("verdict", "replayed", "analysis_eligible", "head_hex", "hard", "soft")'),
    ("C", "the comparator ignores head_hex", "compare_outputs.py", '("verdict", "replayed", "analysis_eligible", "n_events", "head_hex", "hard", "soft")', '("verdict", "replayed", "analysis_eligible", "n_events", "hard", "soft")'),
    ("C", "the comparator ignores the verdict", "compare_outputs.py", '("verdict", "replayed", "analysis_eligible", "n_events", "head_hex", "hard", "soft")', '("replayed", "analysis_eligible", "n_events", "head_hex", "hard", "soft")'),
    ("C", "the comparator ignores hard and soft", "compare_outputs.py", '("verdict", "replayed", "analysis_eligible", "n_events", "head_hex", "hard", "soft")', '("verdict", "replayed", "analysis_eligible", "n_events", "head_hex")'),
    ("C", "the comparator ignores missing", "compare_outputs.py", 'if sorted(got["missing"]) != sorted(want["missing"]):', 'if False:'),
    ("C", "the comparator ignores outcomes", "compare_outputs.py", 'for key in ("slots", "outcomes", "candles"):', 'for key in ("slots", "candles"):'),
    ("C", "the comparator ignores slots", "compare_outputs.py", 'for key in ("slots", "outcomes", "candles"):', 'for key in ("outcomes", "candles"):'),
    ("C", "the comparator ignores the order of OUTCOME_UNLINKED", "compare_outputs.py", 'if order_got != order_want:', 'if False:'),
    ("C", "the comparator ignores the endpoint of OUTCOME_UNLINKED", "compare_outputs.py", 'return (name, where, m.group(0) if m else detail)', 'return (name, where, None)'),
    ("C", "the comparator ignores the detail of the FORCE findings", "compare_outputs.py", 'DETAIL_NAMES = ("FORCE_MSG_STRUCTURE", "FORCE_UNKNOWN_KEY")', 'DETAIL_NAMES = ()'),
    ("C", "the comparator accepts any output where UnsupportedJournal is expected", "compare_outputs.py", 'return [] if got == UNSUPPORTED else ["expected UnsupportedJournal', 'return [] if True else ["expected UnsupportedJournal'),
    ("C", "the comparator does not check the form of a finding", "compare_outputs.py", 'bad = well_formed(got["findings"])', 'bad = []'),
    ("C", "the comparator accepts an output without an expectation", "compare_outputs.py", 'for i in sorted(set(got_ids) - set(want_ids)):', 'for i in []:'),
    ("C", "the comparator does not compare findings as a multiset", "compare_outputs.py", 'have = Counter(finding_key(*f) for f in got["findings"])', 'have = Counter(set(finding_key(*f) for f in got["findings"]))'),
    ("H", "the harness does not recognise UnsupportedJournal", "author_src/run_inputs.py", 'if type(exc).__name__ == "UnsupportedJournal":', 'if False:'),
    ("H", "the anchor latest() is off by one", "author_src/run_inputs.py", 'return max(self.entries) if self.entries else 0', 'return max(self.entries) + 1 if self.entries else 0'),
    ("H", "the anchor get() looks at the wrong index", "author_src/run_inputs.py", 'return self.entries.get(index)', 'return self.entries.get(index - 1)'),
    ("H", "the harness records no code hash of helper files", "author_src/run_inputs.py", 'if n.endswith(".py")}', 'if n == os.path.basename(args.module)}'),
    ("H", "the harness does not catch ordinary exceptions as errors", "author_src/run_inputs.py", 'return {"error": "%s: %s" % (type(exc).__name__, exc)}', 'raise'),
    ("B", "the blind input.json carries the title", "make_handoff.py", 'INPUT_KEYS = ("journal_id", "verify_time_ms", "anchor")', 'INPUT_KEYS = ("journal_id", "verify_time_ms", "anchor", "title")'),
    ("B", "the boundary event lacks msg_seq", "make_handoff.py", '"sha256": sha256_bytes(b"{}"), "msg_seq": 1}', '"sha256": sha256_bytes(b"{}")}'),
    ("B", "the vector directory names are kept", "make_handoff.py", 'write(inp / "inputs" / vid / "journal.jsonl"', 'write(inp / "inputs" / name / "journal.jsonl"'),
    ("B", "the contract is not copied byte for byte", "make_handoff.py", 'write(inp / "contract" / "JOURNAL_CONTRACT_v3.md", contract.read_bytes())', 'write(inp / "contract" / "JOURNAL_CONTRACT_v3.md", contract.read_bytes().replace(b"MUST", b"must"))'),
    ("B", "the expected package takes a derived key from the wrong place", "make_handoff.py", 'expected.update({k: derived[vid][k] for k in DERIVED_KEYS})', 'expected.update({k: derived[vid][k] for k in DERIVED_KEYS if k != "head_hex"}); expected["head_hex"] = "0" * 64'),
    ("B", "the build is not deterministic (zip timestamp)", "make_handoff.py", 'date_time=(1980, 1, 1, 0, 0, 0)', 'date_time=__import__("time").localtime()[:6]'),
    ("B", "an output directory that is not empty is accepted", "make_handoff.py", 'if out.exists() and any(out.iterdir()):', 'if False:'),
    ("B", "the vector pin is not checked", "make_handoff.py", 'if got != want:', 'if False:'),
    ("B", "the partial marker is not written", "make_handoff.py", 'inp / "spec" / "PARTIAL_BUILD_DO_NOT_HAND_OVER.txt"', 'inp / "spec" / "NOTE.txt"'),
    ("S", "the specification documents are not copied byte for byte", "make_handoff.py", 'write(inp / "spec" / name, data)', 'write(inp / "spec" / name, data + b"\\n")'),
    ("S", "the pin of a specification document is not checked", "make_handoff.py", 'if sha256_bytes(data) != spec["files"][name]:', 'if False:'),
    ("S", "a missing specification document is not refused cleanly", "make_handoff.py", 'if not (spec_dir / name).is_file():', 'if False:'),
    ("S", "a build with a specification directory is built as a partial one", "make_handoff.py", 'if spec_dir is not None:\n        spec_dir = Path(spec_dir)', 'if False:\n        spec_dir = Path(spec_dir)'),
    ("S", "SPEC_PINS.txt does not say where the documents come from", "make_handoff.py", '"sha256 of each file in this directory, verbatim copies:\\n%s\\norigin: %s\\n" % ("".join(lines), spec["origin"])', '"sha256 of each file in this directory, verbatim copies:\\n%s\\n" % "".join(lines)'),
    ("D", "the interface says again 'exactly these twelve keys'", "author_src/INTERFACE.md", 'The report MUST contain these twelve required keys. Additional keys are ignored.', 'A dict with exactly these twelve keys (more keys are ignored)'),
    ("D", "the interface no longer says that candles is always {}", "author_src/INTERFACE.md", '`candles` is `{}` in every report', '`candles` may be empty'),
    ("D", "the interface no longer says where CANDLE_LAG_UNSET is reported", "author_src/INTERFACE.md", 'once, with `where` = 0', 'at least once'),
    ("D", "the interface leaves the order of the OUTCOME_UNLINKED findings open", "author_src/INTERFACE.md", 'first `endpoint=entry`, then `endpoint=exit`', 'in any order'),
    ("D", "the interface no longer says what a CANDLE that violates 2.1 is", "author_src/INTERFACE.md", 'it is a `BAD_EVENT` (2.1)', 'it is ignored (2.1)'),
    ("D", "the interface no longer says that NO_PRICE gets no OUTCOME_UNLINKED", "author_src/INTERFACE.md", 'For an OUTCOME with status `NO_PRICE`', 'For an OUTCOME with status `X`'),
    ("D", "the interface no longer lists the reference-CANDLE rules as excluded", "author_src/INTERFACE.md", 'the reference-CANDLE rules (6.7)', 'the reference-CANDLE rules (6.4)'),
    ("D", "the interface no longer says that 7.5a overrides st_not_1", "author_src/INTERFACE.md", 'REMOVES the rule `st_not_1`', 'keeps the rule `st_not_1`'),
    ("D", "the interface no longer names one of the specification documents", "author_src/INTERFACE.md", '* `spec/protocol_r3_appendixB_params.md`: the machine-readable', '* `spec/params.md`: the machine-readable'),
    ("D", "the readme no longer says that the revision notes cannot be removed", "author_src/README_FOR_AUTHOR.md", 'cannot be removed', 'can be ignored'),
    ("D", "the readme no longer points to the pin list of the specification documents", "author_src/README_FOR_AUTHOR.md", 'in `spec/SPEC_PINS.txt`', 'somewhere'),
    ("B", "the blind documents name the oracle", "author_src/INTERFACE.md", '## 1. Scope', '## 1. Scope (see also the oracle)'),
]


def run_tests(tmp, with_sources, with_spec):
    env = dict(os.environ)
    if not with_sources:
        env.pop("DLIQ_R6_VECTORS", None)
        env.pop("DLIQ_R6_CONTRACT", None)
    if not (with_sources and with_spec):
        env.pop("DLIQ_R6_SPEC", None)
    r = subprocess.run([sys.executable, "-I", "-B", "test_handoff.py"], cwd=tmp, env=env, capture_output=True, text=True)
    return r.returncode


def main():
    have = bool(os.environ.get("DLIQ_R6_VECTORS") and os.environ.get("DLIQ_R6_CONTRACT"))
    have_spec = have and bool(os.environ.get("DLIQ_R6_SPEC"))
    base = tempfile.mkdtemp()
    try:
        tmp0 = Path(base, "base")
        shutil.copytree(HERE, tmp0, ignore=shutil.ignore_patterns("__pycache__"))
        if run_tests(tmp0, have, have_spec) != 0:
            print("baseline: the unmutated copy FAILS its tests")
            return 1
        print("baseline: unmutated copy passes the tests (builder tests %s; tests of the spec/ directory %s)" % ("run" if have else "SKIPPED", "run" if have_spec else "SKIPPED"))
        bad = 0
        killed = skipped = 0
        for n, (kind, name, rel, old, new) in enumerate(MUTANTS):
            if (kind in NEEDS_SOURCES and not have) or (kind in NEEDS_SPEC and not have_spec):
                print("SKIPPED  %s (needs %s; NOT a pass)" % (name, "the specification directory" if kind in NEEDS_SPEC and have else "the sources"))
                skipped += 1
                continue
            tmp = Path(base, "m%d" % n)
            shutil.copytree(HERE, tmp, ignore=shutil.ignore_patterns("__pycache__"))
            text = (tmp / rel).read_text(encoding="utf-8")
            if text.count(old) != 1:
                print("INVALID  %s: pattern occurs %d times" % (name, text.count(old)))
                bad += 1
                continue
            (tmp / rel).write_text(text.replace(old, new), encoding="utf-8")
            if run_tests(tmp, have, have_spec) == 0:
                print("SURVIVED %s" % name)
                bad += 1
            else:
                print("KILLED   %s" % name)
                killed += 1
        print("mutants: %d, killed: %d, skipped: %d, survived/invalid: %d" % (len(MUTANTS), killed, skipped, bad))
        return 1 if bad else 0
    finally:
        shutil.rmtree(base, ignore_errors=True)


if __name__ == "__main__":
    sys.exit(main())
