#!/usr/bin/env python3
"""Tests of the r6 conformance vectors and of their checker.   python3 -I -B test_r6_vectors.py   (run from research/d-liq/r6-draft/tests)

Two kinds of test: (1) the vectors pass every check; (2) NEGATIVE tests: the checker must FAIL when a vector, an expectation, the oracle or the generator is wrong,
otherwise a green run would prove nothing. All of it is synthetic and by the author of the contract text; see README for what a pass does and does not mean."""
import base64
import hashlib
import json
import shutil
import sys
import tempfile
import unittest
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import check_vectors as CV          # noqa: E402
import make_vectors as MV           # noqa: E402
import oracle_r6 as O               # noqa: E402

VEC = HERE / "vectors"
R5 = CV.load_r5()


class Copy:
    """A writable copy of the vectors directory."""

    def __enter__(self):
        self.td = tempfile.mkdtemp()
        self.dir = Path(self.td) / "vectors"
        shutil.copytree(VEC, self.dir)
        return self

    def __exit__(self, *a):
        shutil.rmtree(self.td, ignore_errors=True)

    def expect(self, prefix):
        p = next(self.dir.glob(prefix + "_*")) / "expect.json"
        return p, json.loads(p.read_text())

    def put_expect(self, p, e):
        p.write_text(json.dumps(e, indent=1, sort_keys=True) + "\n")

    def journal(self, prefix):
        return next(self.dir.glob(prefix + "_*")) / "journal.jsonl"


def problems(vdir, generated=False):
    return CV.run(vdir, generated=generated, r5=R5)


class TestVectorsPass(unittest.TestCase):
    def test_all_checks_pass(self):
        self.assertEqual(problems(VEC, generated=True), [])

    def test_generator_is_deterministic_and_current(self):
        a, b = MV.build(), MV.build()
        self.assertEqual([(v["dir"], v["journal"]) for v in a], [(v["dir"], v["journal"]) for v in b])
        self.assertEqual(MV.main(["--check"]), 0)

    def test_every_case_1_to_18_is_covered(self):
        vs = CV.load(VEC)
        self.assertEqual(sorted({c for v in vs for c in v["expect"]["cases"]}), list(range(1, 19)))

    def test_no_vector_is_pass_or_analysis_eligible(self):
        for v in CV.load(VEC):
            self.assertIn(v["expect"]["verdict"], ("FAIL", "INCOMPLETE"), v["dir"])
            self.assertFalse(v["expect"]["analysis_eligible"], v["dir"])
            self.assertIn(["CANDLE_LAG_UNSET", 0, None], v["expect"]["findings"], v["dir"])

    def test_the_two_kinds_of_verdict_both_occur(self):
        verdicts = {v["expect"]["verdict"] for v in CV.load(VEC)}
        self.assertEqual(verdicts, {"FAIL", "INCOMPLETE"})

    def test_where_is_the_physical_line_not_seq(self):
        v = next(x for x in CV.load(VEC) if x["dir"].startswith("V14_"))
        lines, events = CV.split(v["data"])
        gap = [n for n, ev in enumerate(events, 1) if ev["seq"] != n]
        self.assertEqual(len(gap), 1)
        for f in v["expect"]["findings"]:
            if f[0] in ("SEQ_GAP", "FORCE_MSG_STRUCTURE"):
                self.assertEqual(f[1], gap[0])
        self.assertNotIn(events[gap[0] - 1]["seq"], [f[1] for f in v["expect"]["findings"]])

    def test_a_kline_connection_changes_no_slot_field(self):
        self.assertEqual(CV.check_slot_equality(CV.load(VEC)), [])

    def test_v06_would_break_r5_without_the_transformation(self):
        """The reason the cross-check needs the transformation: r5 has no feed filter, so the KLINE connection (smaller id, healthy) becomes primary there."""
        import os
        v = next(x for x in CV.load(VEC) if x["dir"].startswith("V06_"))
        with tempfile.TemporaryDirectory() as td:
            p = os.path.join(td, "j")
            with open(p, "wb") as fh:
                fh.write(v["data"])
            res = R5.verify(p, CV.MockAnchor([]), "x", v["expect"]["verify_time_ms"], replay_slots=True)
        self.assertIn("SLOT_MISMATCH", res["hard"])

    def test_transform_keeps_line_numbers_and_replaces_only_kline_connection_events(self):
        v = next(x for x in CV.load(VEC) if x["dir"].startswith("V06_"))
        before = CV.split(v["data"])[1]
        after = CV.split(CV.transform_for_r5(v["data"]))[1]
        self.assertEqual(len(before), len(after))
        for b, a in zip(before, after):
            if b.get("conn_id") == 0:
                self.assertEqual(a["t"], "SESSION")
            else:
                self.assertEqual(a, b)

    def test_transform_makes_structural_anomalies_malformed_for_r5(self):
        v = next(x for x in CV.load(VEC) if x["dir"].startswith("V10b_"))
        after = CV.split(CV.transform_for_r5(v["data"]))[1]
        changed = [ev for ev in after if ev["t"] == "MSG" and json.loads(base64.b64decode(ev["raw_b64"]))["o"]["s"] == "ETHUSDT"]
        self.assertEqual(len(changed), 1)
        self.assertEqual(hashlib.sha256(base64.b64decode(changed[0]["raw_b64"])).hexdigest(), changed[0]["sha256"])


class TestOracle(unittest.TestCase):
    def reason(self, **kw):
        return O.structure_reason(O.parse_object(MV.frame(MV.TAU0 - 300_000, **kw)))

    def test_reasons_and_their_order(self):
        A = MV.ABSENT
        self.assertIsNone(self.reason())
        self.assertIsNone(self.reason(ps=A, st=A))
        self.assertEqual(self.reason(top={"st": 1}), "st_top_level")
        self.assertEqual(self.reason(top={"st": 1}, ps=1, st=2), "st_top_level")
        self.assertEqual(self.reason(ps=1), "ps_type")
        self.assertEqual(self.reason(ps=None), "ps_type")
        self.assertEqual(self.reason(ps=5, st=True), "ps_type")
        self.assertEqual(self.reason(ps="ETHUSDT", st="x"), "ps_ne_s")
        self.assertEqual(self.reason(st=True), "st_type")
        self.assertEqual(self.reason(st="1"), "st_type")
        self.assertEqual(self.reason(st=None), "st_type")
        self.assertEqual(self.reason(st=[1]), "st_type")
        self.assertEqual(self.reason(st=2), "st_ne_1")
        self.assertEqual(self.reason(st=0), "st_ne_1")
        raw = MV.frame(MV.TAU0).replace(b'"st":1', b'"st":1.0')
        self.assertEqual(O.structure_reason(O.parse_object(raw)), "st_type")
        raw = MV.frame(MV.TAU0).replace(b'"st":1', b'"st":1e0')
        self.assertEqual(O.structure_reason(O.parse_object(raw)), "st_type")

    def test_unknown_keys(self):
        A = MV.ABSENT
        obj = O.parse_object(MV.frame(MV.TAU0, top={"b": 1, "a": 2}, o_extra={"c": 3}))
        self.assertEqual(O.unknown_keys(obj), ["a", "b", "c"])
        self.assertEqual(O.unknown_keys(O.parse_object(MV.frame(MV.TAU0, ps=A, st=A))), [])
        self.assertEqual(O.unknown_keys(O.parse_object(MV.frame(MV.TAU0, top={"st": 1}))), [])       # a top-level st is the hard case, not an unknown key
        self.assertEqual(O.unknown_keys(O.parse_object(MV.frame(MV.TAU0, top={"ps": "BTCUSDT"}))), ["ps"])

    def test_strict_parse(self):
        self.assertIsNone(O.parse_object(b"not json"))
        self.assertIsNone(O.parse_object(b'{"a":1,"a":2}'))
        self.assertIsNone(O.parse_object(b'{"a":{"b":1,"b":2}}'))            # duplicate key at depth
        self.assertIsNone(O.parse_object(b'{"a":NaN}'))
        self.assertIsNone(O.parse_object(b'{"a":Infinity}'))
        self.assertIsNone(O.parse_object(b"\xff\xfe"))
        self.assertIsNone(O.parse_object(b"[1]"))
        self.assertEqual(O.parse_object(b'{"a":1}'), {"a": 1})

    def test_findings_on_a_tiny_journal(self):
        j = MV.J()
        j.add(MV.conn_ev(1, "open", MV.TAU0, "FORCE"))
        j.add(MV.msg_ev(1, MV.TAU0 + 1, MV.frame(MV.TAU0, st=2)))
        got = O.findings(j.data())
        self.assertEqual(got, [["CANDLE_LAG_UNSET", 0, ""], ["FORCE_MSG_STRUCTURE", 2, "conn_id=1 reason=st_ne_1"]])


class TestChecksBite(unittest.TestCase):
    """The checker must fail on each of these deliberately wrong inputs."""

    def test_wrong_where_in_the_expectation(self):
        with Copy() as c:
            p, e = c.expect("V02a")
            for f in e["findings"]:
                if f[0] == "FORCE_MSG_STRUCTURE":
                    f[1] += 1
            e["findings"].sort(key=lambda f: (f[1], f[0]))
            c.put_expect(p, e)
            self.assertTrue(any("V02a" in x and "[O]" in x for x in problems(c.dir)))

    def test_wrong_detail_in_the_expectation(self):
        with Copy() as c:
            p, e = c.expect("V07")
            for f in e["findings"]:
                if f[0] == "FORCE_UNKNOWN_KEY":
                    f[2] = "conn_id=1 keys=zz,aa,extra1,ps"
            c.put_expect(p, e)
            self.assertTrue(any("V07" in x and "[O]" in x for x in problems(c.dir)))

    def test_verdict_pass_is_refused(self):
        with Copy() as c:
            p, e = c.expect("V01")
            e["verdict"] = "PASS"
            e["analysis_eligible"] = True
            c.put_expect(p, e)
            self.assertTrue(any("V01" in x and "[S]" in x for x in problems(c.dir)))

    def test_a_missing_conformance_case_is_reported(self):
        with Copy() as c:
            shutil.rmtree(next(c.dir.glob("V14_*")))
            self.assertTrue(any("without a vector" in x and "14" in x for x in problems(c.dir)))

    def test_hand_written_slot_field_is_checked_against_the_r5_replay(self):
        with Copy() as c:
            jp = c.journal("V01")
            lines = jp.read_bytes().split(b"\n")[:-1]
            events = [json.loads(l) for l in lines]
            slot = next(e for e in events if e["t"] == "SLOT")
            slot["sumW_BUY"] = "300001"
            jp.write_bytes(b"".join(CV.canon(e) + b"\n" for e in events))
            ps = problems(c.dir)
            self.assertTrue(any("V01" in x and "[R5]" in x and "SLOT_MISMATCH" in x for x in ps), ps)

    def test_r6_only_list_is_checked_against_r5(self):
        with Copy() as c:
            p, e = c.expect("V01")
            e["r6_only"] = []
            c.put_expect(p, e)
            self.assertTrue(any("V01" in x and "[R5]" in x for x in problems(c.dir)))

    def test_a_vector_that_r5_and_r6_would_both_ignore_cannot_hide_a_missing_finding(self):
        with Copy() as c:
            p, e = c.expect("V04a")
            e["findings"] = [f for f in e["findings"] if f[0] != "FORCE_MSG_STRUCTURE"]
            e["hard"] = [h for h in e["hard"] if h != "FORCE_MSG_STRUCTURE"]
            e["verdict"] = "INCOMPLETE"
            e["r6_only"] = [x for x in e["r6_only"] if x[0] != "FORCE_MSG_STRUCTURE"]
            c.put_expect(p, e)
            self.assertTrue(any("V04a" in x and "[O]" in x for x in problems(c.dir)))

    def test_non_canonical_journal_line_is_reported(self):
        with Copy() as c:
            jp = c.journal("V01")
            lines = jp.read_bytes().split(b"\n")
            lines[0] = lines[0].replace(b'"conn_id":1', b'"conn_id": 1')
            jp.write_bytes(b"\n".join(lines))
            self.assertTrue(any("V01" in x and "not canonical" in x for x in problems(c.dir)))

    def test_seq_difference_outside_the_seq_gap_vector_is_reported(self):
        with Copy() as c:
            jp = c.journal("V01")
            events = [json.loads(l) for l in jp.read_bytes().split(b"\n")[:-1]]
            events[3]["seq"] = 99
            jp.write_bytes(b"".join(CV.canon(e) + b"\n" for e in events))
            self.assertTrue(any("V01" in x and "has seq" in x for x in problems(c.dir)))

    def test_stale_generated_files_are_reported(self):
        with Copy() as c:
            jp = c.journal("V20")
            jp.write_bytes(jp.read_bytes())
            p, e = c.expect("V20")
            e["title"] += "!"
            c.put_expect(p, e)
            self.assertTrue(any("V20" in x and "make_vectors" in x for x in problems(c.dir, generated=True)))

    def test_oracle_with_a_wrong_reading_is_caught_by_the_vectors(self):
        import mutation_check_oracle as M
        vs = CV.load(VEC)
        for name, old, new, survives in M.MUTANTS:
            if survives:
                continue
            mod = M.build_oracle(M.SRC.replace(old, new))
            self.assertTrue(M.killed_by(mod, vs), name)

    def test_mutation_check_script_passes(self):
        import mutation_check_oracle as M
        import io
        import contextlib
        buf = io.StringIO()
        with contextlib.redirect_stdout(buf):
            rc = M.main()
        self.assertEqual(rc, 0, buf.getvalue())
        self.assertIn("problems: 0", buf.getvalue())


if __name__ == "__main__":
    unittest.main(verbosity=1)
