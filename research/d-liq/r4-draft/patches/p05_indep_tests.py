"""r4 patch 05: independent-verifier suite -- coverage + tamper/omit/tail tests (integrator-added; NOT written by the independent author). usage: python3 p05_indep_tests.py <tree>"""
import sys
tree = sys.argv[1]
p = tree + "/indep_verifier/test_indep.py"
s = open(p, encoding="utf-8").read()
def rep(a, b):
    global s
    assert s.count(a) == 1, (a[:90], s.count(a))
    s = s.replace(a, b)
rep('''        self.assertEqual(sorted(res), sorted(["verdict", "findings", "hard", "soft", "n_events",
                                              "head_hex", "slots", "missing"]))''','''        self.assertEqual(res["outcomes"], {TAU0: "COVERED"})
        self.assertEqual(sorted(res), sorted(["verdict", "findings", "hard", "soft", "n_events",
                                              "head_hex", "slots", "missing", "outcomes"]))''')
new = '''

def _canon_line(ev):
    return json.dumps(ev, sort_keys=True, separators=(",", ":"), ensure_ascii=True, allow_nan=False).encode("ascii")


class TestOutcomeCoverageR4(unittest.TestCase):
    """r4 integrator-added tests (contract 6.4; GPT audit orders 1 and 4): the independent author's own suite did not contain them."""

    def build(self, final_ck, dup=False, eval_=False):
        a, jw = mk()
        jw.add(e_session())                                    # 1
        jw.add(e_slot(TAU0))                                   # 2
        jw.ck(time_ms=TAU0 + 5)                                # 3 covers the SLOT
        if eval_:
            jw.add(e_candle(TAU0 + D, "100.5"))                # 4
            jw.add(e_candle(TAU0 + D + H, "101.5"))            # 5
            jw.add(e_outcome(TAU0))                            # 6
        else:
            jw.add({"t": "OUTCOME", "tau_ms": TAU0, "status": "NO_PRICE"})   # 4
        if dup:
            jw.add({"t": "OUTCOME", "tau_ms": TAU0, "status": "NO_PRICE"})
        if final_ck:
            jw.ck(time_ms=TAU0 + 9)
        return a, jw

    def test_covered(self):
        a, jw = self.build(True)
        res = run(jw, a, vt=TAU0 + 10 * G)
        self.assertEqual((res["verdict"], res["hard"], res["soft"], res["outcomes"]), ("PASS", [], [], {TAU0: "COVERED"}))

    def test_uncovered_tail(self):
        a, jw = self.build(False)
        res = run(jw, a, vt=TAU0 + 10 * G)
        self.assertEqual((res["verdict"], res["hard"], res["soft"], res["outcomes"]), ("PASS", [], ["OUTCOME_UNCOVERED"], {TAU0: "UNCOVERED"}))
        self.assertEqual(wheres(res, "OUTCOME_UNCOVERED"), [TAU0])

    def test_duplicate_outcome_is_not_entered_twice(self):
        a, jw = self.build(True, dup=True)
        res = run(jw, a, vt=TAU0 + 10 * G)
        self.assertEqual(res["hard"], ["DUPLICATE_OUTCOME"])
        self.assertEqual(res["outcomes"], {TAU0: "COVERED"})
        self.assertEqual(sum(1 for f in res["findings"] if f[0] == "OUTCOME_UNCOVERED"), 0)

    def test_checkpoint_before_the_outcome_does_not_cover_it(self):
        a, jw = mk()
        jw.add(e_session())
        jw.add(e_slot(TAU0))
        jw.ck(time_ms=TAU0 + 5)                                # line 3, anchored_seq 2
        jw.add({"t": "OUTCOME", "tau_ms": TAU0, "status": "NO_PRICE"})   # line 4
        jw.add({"t": "PING", "conn_id": 1, "ms": 1})           # line 5, no checkpoint after
        res = run(jw, a, vt=TAU0 + 10 * G)
        self.assertEqual(res["outcomes"], {TAU0: "UNCOVERED"})

    def test_checkpoint_anchoring_an_older_head_does_not_cover_a_later_outcome(self):
        # a checkpoint line AFTER the outcome whose anchored_seq lies BEFORE the outcome line must not cover it (anchored_seq >= j is required)
        a, jw = mk()
        jw.add(e_session())                                    # 1
        jw.add(e_slot(TAU0))                                   # 2
        jw.ck(time_ms=TAU0 + 5)                                # 3 anchors 2
        k_old = 3
        jw.add({"t": "OUTCOME", "tau_ms": TAU0, "status": "NO_PRICE"})   # 4
        jw.ck(k=k_old, time_ms=TAU0 + 9)                       # 5 a valid, later checkpoint that anchors head 3 (< 4): it comes after the outcome but does not cover it
        res = run(jw, a, vt=TAU0 + 10 * G)
        self.assertEqual(res["hard"], [])
        self.assertEqual(res["outcomes"], {TAU0: "UNCOVERED"})

    def test_tampered_outcome_after_its_covering_checkpoint(self):
        a, jw = self.build(True, eval_=True)
        lines = jw.bytes_().split(b"\\n")[:-1]
        ev = json.loads(lines[5])                              # line 6, the EVAL OUTCOME
        self.assertEqual(ev["t"], "OUTCOME")
        ev["r_bps"] = "999.0"
        lines[5] = _canon_line(ev)
        res = run(b"\\n".join(lines) + b"\\n", a, vt=TAU0 + 10 * G)
        self.assertEqual(res["verdict"], "FAIL")
        self.assertIn("HEAD_MISMATCH", res["hard"])
        self.assertIn("OUTCOME_MISMATCH", res["hard"])

    def test_tampered_outcome_that_stays_arithmetically_consistent_is_still_caught_by_the_chain(self):
        a, jw = self.build(True, eval_=True)
        lines = jw.bytes_().split(b"\\n")[:-1]
        ev = json.loads(lines[5])
        ev["r_bps"] = repr(1e4 * math.log(101.5 / 100.5) + 0.0)   # unchanged value written back
        ev["status"] = "EVAL"
        # change the price pair consistently with a consistent r_bps: candles would no longer link, but the chain alone already differs
        ev["exit_price"], ev["r_bps"] = "102.5", repr(1e4 * math.log(102.5 / 100.5))
        lines[5] = _canon_line(ev)
        res = run(b"\\n".join(lines) + b"\\n", a, vt=TAU0 + 10 * G)
        self.assertEqual(res["verdict"], "FAIL")
        self.assertIn("HEAD_MISMATCH", res["hard"])

    def test_omitted_outcome(self):
        a, jw = self.build(True, eval_=True)
        lines = jw.bytes_().split(b"\\n")[:-1]
        del lines[5]                                           # drop the OUTCOME line; the later checkpoint still anchors the old head
        res = run(b"\\n".join(lines) + b"\\n", a, vt=TAU0 + 10 * G)
        self.assertEqual(res["verdict"], "FAIL")
        self.assertTrue({"SEQ_GAP", "HEAD_MISMATCH"} & set(res["hard"]))
        self.assertNotIn(TAU0, res["outcomes"])

    def test_tail_outcome_can_be_replaced_without_a_hard_finding_but_is_flagged_uncovered(self):
        # documented limit 4.4: lines after the last checkpoint are not authenticated; r4 makes the consequence visible per OUTCOME
        a, jw = self.build(False, eval_=True)
        lines = jw.bytes_().split(b"\\n")[:-1]
        ev = json.loads(lines[5])
        ev["exit_price"], ev["r_bps"] = "101.0", repr(1e4 * math.log(101.0 / 100.5))   # arithmetically consistent, but no candle has that open
        lines[5] = _canon_line(ev)
        res = run(b"\\n".join(lines) + b"\\n", a, vt=TAU0 + 10 * G)
        self.assertEqual(res["outcomes"], {TAU0: "UNCOVERED"})
        self.assertIn("OUTCOME_UNCOVERED", res["soft"])
'''
marker = '\n\nclass ZZ_Coverage(unittest.TestCase):'
rep(marker, new + marker)
open(p, "w", encoding="utf-8").write(s)
print("ok")
