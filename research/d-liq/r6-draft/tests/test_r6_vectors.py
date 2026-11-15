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

    def derived(self):
        p = self.dir / CV.DERIVED_FILE
        return p, json.loads(p.read_text())

    def put_derived(self, p, d):
        p.write_text(json.dumps(d, indent=1, sort_keys=True) + "\n")


def problems(vdir, generated=False):
    return CV.run(vdir, generated=generated, r5=R5)


class TestVectorsPass(unittest.TestCase):
    def test_all_checks_pass(self):
        self.assertEqual(problems(VEC, generated=True), [])

    def test_generator_is_deterministic_and_current(self):
        a, b = MV.build(), MV.build()
        self.assertEqual([(v["dir"], v["journal"]) for v in a], [(v["dir"], v["journal"]) for v in b])
        self.assertEqual(MV.main(["--check"]), 0)

    def test_every_case_1_to_27_is_covered(self):
        vs = CV.load(VEC)
        self.assertEqual(sorted({c for v in vs for c in v["expect"]["cases"]}), list(range(1, 28)))

    def test_the_36_vectors_of_the_previous_revision_are_unchanged(self):
        """The vector-set digest of the 36 directories of commit 0b2dc95 (`find vectors -type f | LC_ALL=C sort | xargs sha256sum | sha256sum`, restricted to them) is the one recorded
        in that revision: the new vectors are new directories only."""
        new_ids = ("V24a", "V24b", "V24c", "V25a", "V25b", "V26", "V27", "V28a", "V28b", "V28c")
        lines = []
        for d in sorted(p for p in VEC.iterdir() if p.is_dir() and p.name.split("_")[0] not in new_ids):
            for f in sorted(d.iterdir()):
                lines.append("%s  vectors/%s/%s\n" % (hashlib.sha256(f.read_bytes()).hexdigest(), d.name, f.name))
        self.assertEqual(len(lines), 72)
        # byte-order sort of the paths, as `LC_ALL=C sort` does
        lines.sort(key=lambda l: l.split("  ", 1)[1].encode())
        self.assertEqual(hashlib.sha256("".join(lines).encode()).hexdigest(), "80fd19cbb9c2a4e861bbd692f72d5bed7cc2b43846f579de144399be05ab17a1")

    def test_the_undecodable_vectors_are_traps_for_a_permissive_decoder(self):
        """Every text of cases 23 to 25 that Python's permissive decoder (or `validate=True` alone) still decodes gives bytes whose hash MATCHES the journal: a verifier that is
        more permissive than 2.2 would not report RAW_HASH_MISMATCH, would count the message and (V24b, V24c, V25b) report a FORCE finding. The strict oracle rejects all of them."""
        raising = {("V24c", 9), ("V24c", 11)}                   # texts that no decoder accepts (padding stripped, length cut): the vector tests 'no crash' only
        n = 0
        for v in CV.load(VEC):
            vid = v["dir"].split("_")[0]
            if not vid.startswith(("V24", "V25", "V26")):
                continue
            events = CV.split(v["data"])[1]
            bad = [f[1] for f in v["expect"]["findings"] if f[0] == "RAW_HASH_MISMATCH"]
            self.assertTrue(bad, vid)
            for line in bad:
                ev = events[line - 1]
                self.assertIsNone(O.decode_raw(ev["raw_b64"]), (vid, line))
                try:
                    raw = base64.b64decode(ev["raw_b64"])
                except Exception:
                    self.assertIn((vid, line), raising)
                    continue
                self.assertEqual(hashlib.sha256(raw).hexdigest(), ev["sha256"], (vid, line))
                n += 1
        self.assertEqual(n, 8)                                  # V24a 1, V24b 2, V24c 1 (m2), V25a 1, V25b 1, V26 2

    def test_no_vector_contains_a_valid_candle_event(self):
        """Case 26: the only CANDLE event of the package has no msg_seq (BAD_EVENT). No vector asks a verifier to implement the CANDLE rules or gives it a valid CANDLE event."""
        found = []
        for v in CV.load(VEC):
            for n, ev in enumerate(CV.split(v["data"])[1], 1):
                if ev["t"] == "CANDLE":
                    found.append((v["dir"], n, "msg_seq" in ev))
                    self.assertIn(["BAD_EVENT", n, None], v["expect"]["findings"])
            self.assertEqual(v["expect"]["candles"], {})
        self.assertEqual([(d.split("_")[0], w) for d, _, w in found], [("V27", False)])

    def test_the_eval_outcome_vectors_say_entry_then_exit(self):
        by = {v["dir"].split("_")[0]: v for v in CV.load(VEC)}
        for vid in ("V28a", "V28c"):
            unl = [f for f in by[vid]["expect"]["findings"] if f[0] == "OUTCOME_UNLINKED"]
            self.assertEqual([f[2] for f in unl], ["endpoint=entry", "endpoint=exit"], vid)
            self.assertEqual(unl[0][1], unl[1][1])                                   # both at the OUTCOME line
        self.assertEqual([f for f in by["V28b"]["expect"]["findings"] if f[0] == "OUTCOME_UNLINKED"], [])
        self.assertEqual(by["V28b"]["expect"]["verdict"], "INCOMPLETE")
        outs = [e for e in CV.split(by["V28b"]["data"])[1] if e["t"] == "OUTCOME"]
        self.assertEqual([e["status"] for e in outs], ["NO_PRICE"])

    def test_derived_keys_of_the_outcome_vectors(self):
        d = CV.load_derived(VEC)
        self.assertEqual(d["V28a"]["outcomes"], {"1785600000000": "COVERED"})
        self.assertEqual(d["V28b"]["outcomes"], {"1785600000000": "COVERED"})
        self.assertEqual(d["V28c"]["outcomes"], {"1785600000000": "UNCOVERED"})
        self.assertEqual(d["V01"]["outcomes"], {})
        self.assertEqual(sorted(d), sorted(v["dir"].split("_")[0] for v in CV.load(VEC)))

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

    def test_transform_keeps_events_recorded_before_the_first_open(self):
        v = next(x for x in CV.load(VEC) if x["dir"].startswith("V12f_"))
        before = CV.split(v["data"])[1]
        after = CV.split(CV.transform_for_r5(v["data"]))[1]
        first_open = next(n for n, ev in enumerate(before, 1) if ev["t"] == "CONN" and ev["ev"] == "open")
        self.assertGreater(first_open, 1)
        for n, (b, a) in enumerate(zip(before, after), 1):
            if b.get("conn_id") == 0 and n >= first_open:
                self.assertEqual(a["t"], "SESSION")
            elif b["t"] != "MSG":
                self.assertEqual(a, b)
        self.assertEqual(after[first_open - 2]["t"], "MSG")            # the pre-open MSG is still a message for r5

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
        self.assertEqual(self.reason(s=A, ps="BTCUSDT"), "ps_no_s")
        self.assertEqual(self.reason(s=A, ps="BTCUSDT", st=2), "ps_no_s")            # ps_no_s comes before the st reasons
        self.assertEqual(self.reason(s=A, ps=1), "ps_type")                          # a non-string ps is ps_type whether or not s exists
        self.assertEqual(self.reason(s=A, ps=A, st=1), None)                         # no ps: s may be absent without a ps/st reason
        self.assertEqual(self.reason(s=5, ps="BTCUSDT"), "ps_ne_s")                  # s present but not equal (not a string)
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
        self.assertEqual(O.unknown_keys(obj), ["a", "b", "o.c"])
        both = O.parse_object(MV.frame(MV.TAU0, top={"zz": 1}, o_extra={"zz": 2}))
        self.assertEqual(O.unknown_keys(both), ["o.zz", "zz"])
        same = O.parse_object(MV.frame(MV.TAU0, top={"o.zz": 1}, o_extra={"zz": 2}))
        self.assertEqual(O.unknown_keys(same), ["o.zz", "o.zz"])                      # no de-duplication
        self.assertEqual(O.unknown_keys(O.parse_object(MV.frame(MV.TAU0, ps=A, st=A))), [])
        self.assertEqual(O.unknown_keys(O.parse_object(MV.frame(MV.TAU0, top={"st": 1}))), [])       # a top-level st is the hard case, not an unknown key
        self.assertEqual(O.unknown_keys(O.parse_object(MV.frame(MV.TAU0, top={"ps": "BTCUSDT"}))), ["ps"])
        self.assertEqual(O.unknown_keys({"e": "x", "E": 1, "o": "not an object"}), [])

    def test_o_not_an_object(self):
        for raw in (b'{"e":"forceOrder","E":1,"o":"x"}', b'{"e":"forceOrder","E":1,"o":null}', b'{"e":"forceOrder","E":1,"o":5}', b'{"e":"forceOrder","E":1,"o":[1]}', b'{"e":"forceOrder","E":1}'):
            self.assertIsNone(O.structure_reason(O.parse_object(raw)), raw)
        self.assertEqual(O.structure_reason(O.parse_object(b'{"e":"forceOrder","E":1,"st":1,"o":null}')), "st_top_level")
        self.assertEqual(O.structure_reason(O.parse_object(b'{"e":"forceOrder","E":1,"st":1}')), "st_top_level")

    def test_strict_base64(self):
        self.assertEqual(O.decode_raw("e30="), b"{}")
        self.assertEqual(O.decode_raw(""), b"")
        for bad in ("e!30=", "e30=\n", "e3 0=", " e30=", "e31=", "e30==", "e30", "=e30", "e30=x", "AAB=", "AB==", "AAA=\n", "\u00e9AAA", "e30=\x00"):
            self.assertIsNone(O.decode_raw(bad), repr(bad))
        self.assertIsNone(O.decode_raw(None))
        self.assertIsNone(O.decode_raw(b"e30="))

    def test_the_hand_derived_strict_decoder_agrees_with_validate_plus_reencoding(self):
        """Two methods for one rule (2.2): the oracle's grammar + trailing-bit check, and the verifier-style `validate=True` + comparison with the re-encoding. Exhaustive over all
        strings of length 0 to 6 over a small alphabet that contains a canonical and a non-canonical last character, padding, a bad character and whitespace."""
        import itertools

        def other(t):
            try:
                raw = base64.b64decode(t, validate=True)
            except Exception:
                return None
            return raw if base64.b64encode(raw).decode("ascii") == t else None
        n = 0
        for k in range(7):
            for tup in itertools.product("AQRY=!\n", repeat=k):
                t = "".join(tup)
                self.assertEqual(O.decode_raw(t), other(t), repr(t))
                n += 1
        self.assertGreater(n, 100_000)

    def test_derived_of_a_tiny_journal(self):
        j = MV.J()
        j.add(MV.conn_ev(1, "open", MV.TAU0, "FORCE"))
        d = O.derived(j.data())
        self.assertEqual(d["n_events"], 1)
        self.assertEqual(d["head_hex"], hashlib.sha256(hashlib.sha256(MV.V3).digest() + j.lines()[0]).hexdigest())

    def test_a_valid_eval_outcome_and_the_other_new_findings_on_a_tiny_journal(self):
        j = MV.J()
        j.add({"t": "OUTCOME", "rec_ms": 5, "tau_ms": MV.TAU0, "status": "EVAL", "entry_open_ms": MV.TAU0 + 300_000, "exit_open_ms": MV.TAU0 + 14_700_000, "entry_price": "1", "exit_price": "1", "r_bps": "0.0"})
        j.add({"t": "OUTCOME", "rec_ms": 6, "tau_ms": MV.TAU0, "status": "NO_PRICE"})
        j.add({"t": "OUTCOME", "rec_ms": 7, "tau_ms": MV.TAU0, "status": "EVAL", "entry_open_ms": 1})          # not valid per 2.1: no oracle finding
        j.add({"t": "CANDLE", "rec_ms": 8, "open_time_ms": 1, "open": "1", "recv_ms": 1, "raw_b64": "", "sha256": hashlib.sha256(b"").hexdigest(), "msg_seq": True})
        got = [f for f in O.findings(j.data()) if f[0] != "CANDLE_LAG_UNSET"]
        self.assertEqual(got, [["OUTCOME_UNLINKED", 1, "endpoint=entry"], ["OUTCOME_UNLINKED", 1, "endpoint=exit"], ["BAD_EVENT", 4, ""]])      # a boolean msg_seq is not an integer

    def test_strict_parse(self):
        self.assertIsNone(O.parse_object(b"not json"))
        self.assertIsNone(O.parse_object(b'{"a":1,"a":2}'))
        self.assertIsNone(O.parse_object(b'{"a":{"b":1,"b":2}}'))            # duplicate key at depth
        self.assertIsNone(O.parse_object(b'{"a":NaN}'))
        self.assertIsNone(O.parse_object(b'{"a":Infinity}'))
        self.assertIsNone(O.parse_object(b"\xff\xfe"))
        self.assertIsNone(O.parse_object(b"[1]"))
        self.assertEqual(O.parse_object(b'{"a":1}'), {"a": 1})

    def test_the_feed_applies_from_the_first_valid_open_on(self):
        T = MV.TAU0
        bad = MV.frame(T, ps=1)
        j = MV.J()
        j.add(MV.msg_ev(7, T, bad))                                   # before the open: no feed, although the connection later opens as KLINE
        j.add(MV.conn_ev(7, "close", T + 1, "FORCE"))                 # before the open: no feed to conflict with
        j.add(MV.conn_ev(7, "open", T + 2, "KLINE"))
        j.add(MV.msg_ev(7, T + 3, bad))                               # after the open: a KLINE message, never examined
        j.add(MV.conn_ev(7, "close", T + 4, "FORCE"))                 # after the open, other feed: conflict
        got = O.findings(j.data())
        self.assertEqual(got, [["CANDLE_LAG_UNSET", 0, ""], ["FORCE_MSG_STRUCTURE", 1, "conn_id=7 reason=ps_type"], ["MSG_CONN_UNKNOWN", 1, ""], ["CONN_FEED_CONFLICT", 5, ""]])

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

    def test_a_missing_raw_hash_mismatch_in_the_expectation_is_reported(self):
        with Copy() as c:
            p, e = c.expect("V24a")
            e["findings"] = [f for f in e["findings"] if f[0] != "RAW_HASH_MISMATCH"]
            e["hard"] = [h for h in e["hard"] if h != "RAW_HASH_MISMATCH"]
            e["verdict"] = "INCOMPLETE"
            c.put_expect(p, e)
            self.assertTrue(any("V24a" in x and "[S]" in x and "lacks RAW_HASH_MISMATCH" in x for x in problems(c.dir)))

    def test_a_raw_hash_mismatch_on_a_valid_line_in_the_expectation_is_reported(self):
        with Copy() as c:
            p, e = c.expect("V01")
            e["findings"] = sorted(e["findings"] + [["RAW_HASH_MISMATCH", 3, None]], key=lambda f: (f[1], f[0]))
            e["hard"] = sorted(e["hard"] + ["RAW_HASH_MISMATCH"])
            e["verdict"] = "FAIL"
            c.put_expect(p, e)
            self.assertTrue(any("V01" in x and "[S]" in x and "names RAW_HASH_MISMATCH" in x for x in problems(c.dir)))

    def test_a_text_made_valid_without_changing_the_expectation_is_reported(self):
        with Copy() as c:
            jp = c.journal("V24a")
            events = [json.loads(l) for l in jp.read_bytes().split(b"\n")[:-1]]
            events[8]["raw_b64"] = base64.b64encode(base64.b64decode(events[8]["raw_b64"].replace("!", ""))).decode("ascii")
            jp.write_bytes(b"".join(CV.canon(e) + b"\n" for e in events))
            self.assertTrue(any("V24a" in x and "lacks" not in x and "names RAW_HASH_MISMATCH" in x for x in problems(c.dir)))

    def test_the_derived_file_is_required_and_checked(self):
        with Copy() as c:
            p, d = c.derived()
            p.unlink()
            self.assertTrue(any("EXPECT_DERIVED.json is missing" in x for x in problems(c.dir)))
        with Copy() as c:
            p, d = c.derived()
            d["vectors"]["V01"]["n_events"] += 1
            c.put_derived(p, d)
            self.assertTrue(any("V01" in x and "[D]" in x and "n_events" in x for x in problems(c.dir)))
        with Copy() as c:
            p, d = c.derived()
            d["vectors"]["V02a"]["head_hex"] = "0" * 64
            c.put_derived(p, d)
            self.assertTrue(any("V02a" in x and "[D]" in x and "head_hex" in x for x in problems(c.dir)))
        with Copy() as c:
            p, d = c.derived()
            d["vectors"]["V28a"]["outcomes"] = {"1785600000000": "UNCOVERED"}
            c.put_derived(p, d)
            ps = problems(c.dir)
            self.assertTrue(any("V28a" in x and "[R5]" in x and "outcomes" in x for x in ps), ps)
        with Copy() as c:
            p, d = c.derived()
            d["vectors"]["V01"]["outcomes"] = {"1785600000000": "COVERED"}
            c.put_derived(p, d)
            self.assertTrue(any("V01" in x and "[D]" in x and "outcomes name" in x for x in problems(c.dir)))
        with Copy() as c:
            p, d = c.derived()
            del d["vectors"]["V03"]
            c.put_derived(p, d)
            self.assertTrue(any("covers other vectors" in x for x in problems(c.dir)))

    def test_a_wrong_outcome_detail_in_the_expectation_is_reported(self):
        with Copy() as c:
            p, e = c.expect("V28a")
            for f in e["findings"]:
                if f[0] == "OUTCOME_UNLINKED":
                    f[2] = "endpoint=entry"
            c.put_expect(p, e)
            self.assertTrue(any("V28a" in x and "[O]" in x for x in problems(c.dir)))

    def test_the_transformation_for_r5_replaces_an_undecodable_text_and_keeps_its_hash(self):
        v = next(x for x in CV.load(VEC) if x["dir"].startswith("V24a_"))
        before, after = CV.split(v["data"])[1], CV.split(CV.transform_for_r5(v["data"]))[1]
        self.assertEqual(len(before), len(after))
        changed = [(b, a) for b, a in zip(before, after) if b != a]
        self.assertEqual(len(changed), 1)
        b, a = changed[0]
        self.assertEqual(base64.b64decode(a["raw_b64"], validate=True), b"undecodable")
        self.assertEqual(a["sha256"], b["sha256"])

    def test_oracle_with_a_wrong_reading_is_caught_by_the_vectors(self):
        import mutation_check_oracle as M
        vs = CV.load(VEC)
        derived = CV.load_derived(VEC)
        for name, old, new, survives in M.MUTANTS:
            if survives:
                continue
            mod = M.build_oracle(M.SRC.replace(old, new))
            self.assertTrue(M.killed_by(mod, vs, derived), name)

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
