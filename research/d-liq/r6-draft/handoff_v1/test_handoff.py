"""Unit tests of the handoff tools (builder, harness, comparator). SYNTHETIC; written by the author of the tools: NOT independent.
Tests that need the pinned sources run only when DLIQ_R6_VECTORS (the directory `vectors` of PR #40 at 7bb06f0) and DLIQ_R6_CONTRACT (JOURNAL_CONTRACT_v3.md of PR #39 at 53a7a3a) are set;
otherwise they are SKIPPED with a message (a skip is not a pass). CI sets both.
usage: python3 -I -B test_handoff.py"""
import copy
import hashlib
import json
import os
import shutil
import subprocess
import sys
import tempfile
import unittest
import zipfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(HERE / "author_src"))
import compare_outputs as CMP      # noqa: E402
import make_handoff as MH          # noqa: E402
import run_inputs as RI            # noqa: E402

VECTORS = os.environ.get("DLIQ_R6_VECTORS")
CONTRACT = os.environ.get("DLIQ_R6_CONTRACT")
NEEDS_SOURCES = unittest.skipUnless(VECTORS and CONTRACT, "DLIQ_R6_VECTORS / DLIQ_R6_CONTRACT not set (NOT a pass)")
PINS = json.loads((HERE / "HANDOFF_PINS.json").read_text(encoding="utf-8"))
FORBIDDEN_IN_AUTHOR_DOCS = ("oracle", "EXPECT_DERIVED", "dliq_journal_verify", "r6_rules", "primary verifier", "expect.json", "PROVENANCE", "make_vectors", "run_vectors", "sanity_mutants", "r6_only", "r5_only_extra", "contract_refs")


def report(**over):
    r = {"verdict": "FAIL", "findings": [["CANDLE_LAG_UNSET", 0, "L is unset"], ["OUTCOME_UNLINKED", 14, "endpoint=entry: x"], ["OUTCOME_UNLINKED", 14, "endpoint=exit: y"]],
         "hard": ["CANDLE_LAG_UNSET", "OUTCOME_UNLINKED"], "soft": [], "n_events": 15, "head_hex": "ab" * 32, "slots": {"1785600000000": "OK"}, "missing": [4, 8],
         "outcomes": {"1785600000000": "COVERED"}, "candles": {}, "replayed": True, "analysis_eligible": False}
    r.update(over)
    return r


def expected(**over):
    r = report(**over)
    r["findings"] = [[n, w, (None if n not in ("FORCE_MSG_STRUCTURE", "FORCE_UNKNOWN_KEY") and not n.startswith("OUTCOME_UNLINKED") else d)] for n, w, d in r["findings"]]
    for f in r["findings"]:
        if f[0] == "OUTCOME_UNLINKED":
            f[2] = "endpoint=entry" if "entry" in str(report()["findings"][1][2]) and f is r["findings"][1] else "endpoint=exit"
    return r


class ComparatorTests(unittest.TestCase):
    def test_a_report_equal_to_its_expectation_agrees(self):
        self.assertEqual(CMP.compare(report(), expected()), [])

    def test_every_one_of_the_twelve_keys_is_compared(self):
        changes = {"verdict": "INCOMPLETE", "hard": ["CANDLE_LAG_UNSET"], "soft": ["SLOT_MISSING"], "n_events": 16, "head_hex": "cd" * 32, "slots": {"1785600000000": "LATE"},
                   "missing": [4], "outcomes": {"1785600000000": "UNCOVERED"}, "candles": {"1": "USABLE"}, "replayed": False, "analysis_eligible": True}
        self.assertEqual(sorted(list(changes) + ["findings"]), sorted(CMP.KEYS))
        for key, value in changes.items():
            with self.subTest(key=key):
                self.assertTrue(CMP.compare(report(**{key: value}), expected()), key)
        self.assertTrue(CMP.compare(report(findings=report()["findings"][:2]), expected()))

    def test_the_order_of_missing_is_not_compared_but_its_content_is(self):
        self.assertEqual(CMP.compare(report(missing=[8, 4]), expected()), [])
        self.assertTrue(CMP.compare(report(missing=[4, 8, 12]), expected()))

    def test_integer_keys_and_their_decimal_strings_are_the_same_key(self):
        self.assertEqual(CMP.compare(report(slots={1785600000000: "OK"}, outcomes={1785600000000: "COVERED"}), expected()), [])

    def test_extra_report_keys_are_ignored_but_missing_ones_are_not(self):
        r = report()
        r["debug"] = [1]
        self.assertEqual(CMP.compare(r, expected()), [])
        del r["debug"], r["head_hex"]
        self.assertTrue(CMP.compare(r, expected()))

    def test_findings_are_a_multiset_of_name_and_where(self):
        got = report()["findings"]
        self.assertTrue(CMP.compare(report(findings=got + [["SLOT_MISSING", 4, "d"]]), expected()))
        self.assertTrue(CMP.compare(report(findings=[["CANDLE_LAG_UNSET", 1, "d"]] + got[1:]), expected()))
        self.assertTrue(CMP.compare(report(findings=got + [got[0]]), expected()))
        self.assertEqual(CMP.compare(report(findings=[got[0], [got[1][0], got[1][1], "endpoint=entry: other text"], got[2]]), expected()), [])
        self.assertEqual(CMP.compare(report(findings=[["CANDLE_LAG_UNSET", 0, "other text"]] + got[1:]), expected()), [])

    def test_the_two_unlinked_findings_are_compared_by_endpoint_and_by_order(self):
        got = report()["findings"]
        self.assertTrue(CMP.compare(report(findings=[got[0], got[2], got[1]]), expected()), "exit before entry")
        self.assertTrue(CMP.compare(report(findings=[got[0], [got[1][0], got[1][1], "x endpoint=entry"], got[2]]), expected()), "the detail must BEGIN with the endpoint")
        self.assertTrue(CMP.compare(report(findings=[got[0], [got[1][0], got[1][1], "endpoint=entryX"], got[2]]), expected()))
        self.assertTrue(CMP.compare(report(findings=[got[0], [got[1][0], got[1][1], "entry"], got[2]]), expected()))

    def test_force_findings_are_compared_by_their_exact_detail(self):
        want = expected(findings=[["FORCE_MSG_STRUCTURE", 5, "conn_id=1 reason=ps_type"]])
        self.assertEqual(want["findings"][0][2], "conn_id=1 reason=ps_type")
        self.assertEqual(CMP.compare(report(findings=[["FORCE_MSG_STRUCTURE", 5, "conn_id=1 reason=ps_type"]]), want), [])
        self.assertTrue(CMP.compare(report(findings=[["FORCE_MSG_STRUCTURE", 5, "conn_id=1 reason=ps_ne_s"]]), want))
        self.assertTrue(CMP.compare(report(findings=[["FORCE_MSG_STRUCTURE", 5, "conn_id=1 reason=ps_type "]]), want))

    def test_malformed_findings_are_a_problem(self):
        for bad in ([["CANDLE_LAG_UNSET", "0", "d"]], [["CANDLE_LAG_UNSET", 0, None]], [["CANDLE_LAG_UNSET", True, "d"]], [["CANDLE_LAG_UNSET", 0]], [("A", 0, "d", 1)], "none"):
            with self.subTest(bad=bad):
                self.assertTrue(CMP.compare(report(findings=bad), expected(findings=[["CANDLE_LAG_UNSET", 0, None]])))

    def test_the_capability_boundary_is_fail_closed(self):
        unsupported = {"unsupported_journal": True}
        self.assertEqual(CMP.compare(unsupported, unsupported), [])
        self.assertTrue(CMP.compare(report(), unsupported), "a verdict where none is allowed")
        self.assertTrue(CMP.compare({"error": "ValueError: x"}, unsupported))
        self.assertTrue(CMP.compare({}, unsupported))
        self.assertTrue(CMP.compare({"unsupported_journal": False}, unsupported))
        self.assertTrue(CMP.compare(unsupported, expected()), "no verdict where one is expected")
        self.assertTrue(CMP.compare({"error": "ValueError: x"}, expected()))
        self.assertTrue(CMP.compare([], expected()))

    def test_main_reports_missing_unexpected_and_empty(self):
        with tempfile.TemporaryDirectory() as tmp:
            e, o = Path(tmp, "e"), Path(tmp, "o")
            e.mkdir()
            o.mkdir()
            self.assertEqual(CMP.main(["--expected", str(e), "--outputs", str(o)]), 1, "no expectations at all")
            (e / "V01.json").write_text(json.dumps(expected()))
            self.assertEqual(CMP.main(["--expected", str(e), "--outputs", str(o)]), 1, "no output for V01")
            (o / "V01.json").write_text(json.dumps(report()))
            self.assertEqual(CMP.main(["--expected", str(e), "--outputs", str(o)]), 0)
            (o / "V99.json").write_text(json.dumps(report()))
            self.assertEqual(CMP.main(["--expected", str(e), "--outputs", str(o)]), 1, "an output with no expectation")
            os.remove(o / "V99.json")
            (o / "V01.json").write_text(json.dumps(report(verdict="PASS")))
            self.assertEqual(CMP.main(["--expected", str(e), "--outputs", str(o)]), 1)


STUB = '''
class UnsupportedJournal(Exception):
    pass

def verify(path, anchor, journal_id, verify_time_ms):
    data = open(path, "rb").read()
    if b"CANDLE" in data:
        raise UnsupportedJournal("x")
    if b"BOOM" in data:
        raise ValueError("boom")
    if b"NOTDICT" in data:
        return [1]
    return {"verdict": "PASS", "n_events": len(data), "slots": {5: "OK"}, "got": [journal_id, verify_time_ms, anchor.latest(journal_id), anchor.get(journal_id, 2), anchor.get(journal_id, 9)]}
'''


class HarnessTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)

    def make_input(self, group, name, journal, anchor):
        d = self.root / "pkg" / group / name
        d.mkdir(parents=True)
        (d / "journal.jsonl").write_bytes(journal)
        (d / "input.json").write_text(json.dumps({"journal_id": "j-" + name, "verify_time_ms": 7, "anchor": anchor}))

    def run_stub(self, source=STUB):
        mod = self.root / "mod"
        mod.mkdir(exist_ok=True)
        (mod / "stub.py").write_text(source)
        out = self.root / "out"
        rc = RI.main(["--module", str(mod / "stub.py"), "--inputs", str(self.root / "pkg"), "--out", str(out)])
        return rc, out

    def test_anchor_methods_follow_the_documented_definition(self):
        a = RI.Anchor([{"index": 1, "seq": 3}, {"index": 2, "seq": 5}])
        self.assertEqual(a.get("any", 2), {"index": 2, "seq": 5})
        self.assertIsNone(a.get("any", 3))
        self.assertIsNone(a.get("any", 0))
        self.assertEqual(a.latest("any"), 2)
        self.assertEqual(RI.Anchor([]).latest("any"), 0)
        self.assertIsNone(RI.Anchor([]).get("any", 1))

    def test_reports_boundary_errors_and_non_dicts_are_recorded_as_such(self):
        self.make_input("inputs", "V01", b"{}\n", [{"index": 2, "seq": 1}])
        self.make_input("inputs", "V02", b"BOOM\n", [])
        self.make_input("inputs", "V03", b"NOTDICT\n", [])
        self.make_input("boundary", "B01", b"CANDLE\n", [])
        rc, out = self.run_stub()
        self.assertEqual(rc, 0)
        got = {p.stem: json.loads(p.read_text()) for p in (out / "outputs").glob("*.json")}
        self.assertEqual(sorted(got), ["B01", "V01", "V02", "V03"])
        self.assertEqual(got["V01"]["slots"], {"5": "OK"}, "integer keys are written as decimal strings")
        self.assertEqual(got["V01"]["got"], ["j-V01", 7, 2, {"index": 2, "seq": 1}, None])
        self.assertEqual(got["B01"], {"unsupported_journal": True})
        self.assertEqual(got["V02"], {"error": "ValueError: boom"})
        self.assertTrue(got["V03"]["error"].startswith("TypeError"))

    def test_the_record_holds_the_hashes_of_the_code_the_outputs_and_their_digest(self):
        self.make_input("inputs", "V01", b"{}\n", [])
        (self.root / "mod").mkdir()
        (self.root / "mod" / "helper.py").write_text("X = 1\n")
        rc, out = self.run_stub()
        rec = json.loads((out / "OUTPUT_RECORD.json").read_text())
        self.assertEqual(sorted(rec["code_files_sha256"]), ["helper.py", "stub.py"])
        self.assertEqual(rec["code_files_sha256"]["stub.py"], hashlib.sha256(STUB.encode()).hexdigest())
        self.assertEqual(rec["outputs_sha256"], {"V01.json": hashlib.sha256((out / "outputs" / "V01.json").read_bytes()).hexdigest()})
        self.assertEqual(rec["outputs_digest"], RI.digest_of(rec["outputs_sha256"]))
        self.assertEqual(rec["harness_sha256"], hashlib.sha256((HERE / "author_src" / "run_inputs.py").read_bytes()).hexdigest())
        self.assertEqual(rec["inputs"], 1)

    def test_no_inputs_is_an_error(self):
        (self.root / "pkg").mkdir()
        rc, _ = self.run_stub()
        self.assertEqual(rc, 1)

    def test_the_documented_digest_definition_is_the_shell_one(self):
        d = self.root / "d"
        (d / "sub").mkdir(parents=True)
        (d / "b.json").write_bytes(b"1")
        (d / "a.json").write_bytes(b"2")
        (d / "sub" / "B.json").write_bytes(b"3")
        (d / "sub" / "a.json").write_bytes(b"4")
        named = {"b.json": hashlib.sha256(b"1").hexdigest(), "a.json": hashlib.sha256(b"2").hexdigest(), "sub/B.json": hashlib.sha256(b"3").hexdigest(), "sub/a.json": hashlib.sha256(b"4").hexdigest()}
        self.assertEqual(RI.digest_of(named), MH.tree_digest(d)[0])
        if shutil.which("bash"):
            sh = subprocess.run(["bash", "-c", "find . -type f | LC_ALL=C sort | xargs sha256sum | sha256sum"], cwd=d, capture_output=True, text=True).stdout.split()[0]
            self.assertEqual(sh, MH.tree_digest(d)[0])


class AuthorDocumentTests(unittest.TestCase):
    def test_the_interface_defines_both_anchor_methods_precisely(self):
        text = (HERE / "author_src" / "INTERFACE.md").read_text(encoding="utf-8")
        for needle in ("anchor.get(journal_id, index)", "anchor.latest(journal_id)", "or `None` if there is none", "`0` if there are none", "UnsupportedJournal", "capability boundary", "fail closed", "CANDLE", "msg_seq"):
            self.assertIn(needle, text)
        self.assertIn("`SLOT` events with a field `status`", text, "the terminology note on SLOT.status against the `slots` of the report")

    def test_the_documents_for_the_author_name_no_implementation_artifact(self):
        for name in ("README_FOR_AUTHOR.md", "INTERFACE.md", "run_inputs.py"):
            text = (HERE / "author_src" / name).read_text(encoding="utf-8")
            for word in FORBIDDEN_IN_AUTHOR_DOCS:
                with self.subTest(file=name, word=word):
                    self.assertNotIn(word, text)

    def test_the_comparison_rules_of_the_interface_and_of_the_script_say_the_same_thing(self):
        text = (HERE / "author_src" / "INTERFACE.md").read_text(encoding="utf-8")
        for needle in ("FORCE_MSG_STRUCTURE", "FORCE_UNKNOWN_KEY", "OUTCOME_UNLINKED", "endpoint=entry", "endpoint=exit", "sorted list", "extra keys"):
            self.assertIn(needle, text)
            self.assertIn(needle.split()[0] if needle != "extra keys" else "Extra keys", CMP.__doc__ if needle != "extra keys" else CMP.__doc__.replace("extra keys", "Extra keys"))


@NEEDS_SOURCES
class PackageTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.tmp = tempfile.TemporaryDirectory()
        cls.out = Path(cls.tmp.name, "a")
        cls.result = MH.build(VECTORS, CONTRACT, cls.out, PINS)
        cls.inp, cls.exp = cls.out / MH.INPUTS, cls.out / MH.EXPECTED

    @classmethod
    def tearDownClass(cls):
        cls.tmp.cleanup()

    def test_the_digests_and_file_counts_are_the_pinned_ones(self):
        self.assertEqual(self.result["inputs"], (PINS["input_package"]["digest"], PINS["input_package"]["files"]))
        self.assertEqual(self.result["expected"], (PINS["expected_package"]["digest"], PINS["expected_package"]["files"]))
        self.assertNotEqual(self.result["inputs"][0], self.result["expected"][0])

    def test_the_build_and_the_archives_are_deterministic(self):
        again = Path(self.tmp.name, "b")
        self.assertEqual(MH.build(VECTORS, CONTRACT, again, PINS), self.result)
        for name in (MH.INPUTS, MH.EXPECTED):
            MH.write_zip(self.out / name, Path(self.tmp.name, name + "_1.zip"))
            MH.write_zip(again / name, Path(self.tmp.name, name + "_2.zip"))
            self.assertEqual(Path(self.tmp.name, name + "_1.zip").read_bytes(), Path(self.tmp.name, name + "_2.zip").read_bytes())
            with zipfile.ZipFile(Path(self.tmp.name, name + "_1.zip")) as zf:
                infos = zf.infolist()
                self.assertEqual([i.filename for i in infos], sorted((i.filename for i in infos), key=lambda x: x.encode()))
                self.assertTrue(all(i.date_time == (1980, 1, 1, 0, 0, 0) and i.compress_type == zipfile.ZIP_STORED and i.external_attr == 0o644 << 16 for i in infos))
                self.assertTrue(all(i.filename.startswith(name + "/") for i in infos))

    def test_ids_are_bare_labels_and_there_are_forty_six_plus_the_boundary(self):
        ids = sorted(os.listdir(self.inp / "inputs"))
        self.assertEqual(len(ids), 46)
        self.assertTrue(all(__import__("re").fullmatch(r"V[0-9]+[a-z]?", i) for i in ids), ids)
        self.assertEqual(os.listdir(self.inp / "boundary"), ["B01"])
        self.assertEqual(sorted(p.stem for p in (self.exp / "expected").glob("*.json")), sorted(ids + ["B01"]))
        for i in ids:
            self.assertEqual(sorted(os.listdir(self.inp / "inputs" / i)), ["input.json", "journal.jsonl"])

    def test_no_removed_field_and_no_expected_value_is_in_the_blind_package(self):
        for p in self.inp.rglob("input.json"):
            spec = json.loads(p.read_text())
            self.assertEqual(sorted(spec), ["anchor", "journal_id", "verify_time_ms"], p)
        blind_text = "\n".join(p.read_text(encoding="utf-8", errors="replace") for p in self.inp.rglob("*") if p.is_file() and p.suffix in (".json", ".md", ".txt", ".py"))
        # the documents of the package (not the journals and the input.json files: a journal that extends another one carries heads of the shared prefix in its anchors, which is part of the contract's design)
        doc_text = "\n".join(p.read_text(encoding="utf-8") for p in self.inp.rglob("*") if p.is_file() and p.suffix in (".md", ".txt", ".py"))
        for field in MH.REMOVED:
            for p in self.exp.rglob("*.json"):
                self.assertNotIn('"%s"' % field, p.read_text(), (field, p))
            if field not in ("cases", "description", "title"):
                self.assertNotIn('"%s"' % field, blind_text, field)
        for p in (self.exp / "expected").glob("V*.json"):
            want = json.loads(p.read_text())
            self.assertEqual(sorted(want), sorted(MH.KEYS), p)
            self.assertNotIn(want["head_hex"], doc_text, "an expected head_hex must not be written in a document of the blind package: %s" % p)

    def test_the_contract_in_the_blind_package_is_the_pinned_file_byte_for_byte(self):
        data = (self.inp / "contract" / "JOURNAL_CONTRACT_v3.md").read_bytes()
        self.assertEqual(data, Path(CONTRACT).read_bytes())
        self.assertEqual(hashlib.sha256(data).hexdigest(), PINS["contract"]["sha256"])
        pin = (self.inp / "CONTRACT_PIN.txt").read_text()
        self.assertIn(PINS["contract"]["commit"], pin)
        self.assertIn(PINS["contract"]["sha256"], pin)

    def test_journals_are_copied_byte_for_byte(self):
        for d in sorted(os.listdir(VECTORS)):
            if os.path.isdir(os.path.join(VECTORS, d)):
                src = Path(VECTORS, d, "journal.jsonl").read_bytes()
                self.assertEqual((self.inp / "inputs" / MH.short_id(d) / "journal.jsonl").read_bytes(), src, d)

    def test_the_boundary_input_is_one_canonical_candle_event_valid_per_2_1(self):
        data = (self.inp / "boundary" / "B01" / "journal.jsonl").read_bytes()
        self.assertTrue(data.endswith(b"\n") and data.count(b"\n") == 1)
        ev = json.loads(data)
        self.assertEqual(sorted(ev), sorted(["t", "seq", "rec_ms", "open_time_ms", "open", "recv_ms", "raw_b64", "sha256", "msg_seq"]))
        self.assertEqual(ev["t"], "CANDLE")
        self.assertTrue(all(type(ev[k]) is int for k in ("seq", "rec_ms", "open_time_ms", "recv_ms", "msg_seq")))
        self.assertEqual(data, (json.dumps(ev, sort_keys=True, separators=(",", ":")) + "\n").encode())
        self.assertEqual(json.loads((self.exp / "expected" / "B01.json").read_text()), {"unsupported_journal": True})

    def test_the_package_digest_equals_the_shell_definition(self):
        if not shutil.which("bash"):
            self.skipTest("no bash")
        for root, key in ((self.inp, "inputs"), (self.exp, "expected")):
            sh = subprocess.run(["bash", "-c", "find . -type f | LC_ALL=C sort | xargs sha256sum | sha256sum | cut -d' ' -f1; find . -type f | wc -l"], cwd=root, capture_output=True, text=True).stdout.split()
            self.assertEqual((sh[0], int(sh[1])), self.result[key])

    def test_the_builder_refuses_other_sources_and_a_used_output_directory(self):
        bad_vectors = Path(self.tmp.name, "badvec")
        shutil.copytree(VECTORS, bad_vectors)
        victim = next(bad_vectors.glob("V01*/journal.jsonl"))
        victim.write_bytes(victim.read_bytes() + b" ")
        with self.assertRaises(SystemExit):
            MH.build(bad_vectors, CONTRACT, Path(self.tmp.name, "c"), PINS)
        bad_contract = Path(self.tmp.name, "contract.md")
        bad_contract.write_bytes(Path(CONTRACT).read_bytes() + b"\n")
        with self.assertRaises(SystemExit):
            MH.build(VECTORS, bad_contract, Path(self.tmp.name, "d"), PINS)
        with self.assertRaises(SystemExit):
            MH.build(VECTORS, CONTRACT, self.out, PINS)


if __name__ == "__main__":
    unittest.main(verbosity=1)
