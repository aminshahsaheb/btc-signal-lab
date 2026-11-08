"""r5 patch 5: tests. Existing section-level assertions keep their meaning through an explicit adapter that (a) asserts the 7.6 markers on EVERY opt-out call and (b) removes them;
new tests state the G-2 contract directly."""
import os
import sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from _lib import replace_once

root = sys.argv[1]

# ------------------------------------------------------------------------------------------------- primary verifier tests
T1 = "src/test_dliq_journal_v2.py"
replace_once(root, T1, "Part 1 writer guards; Part 2 verifier on clean journals; Part 3 the strict anchoring deadline; Part 4 one test per finding; Part 5 tamper matrix (each manipulation\n",
             "Part 1 writer guards; Part 2 verifier on clean journals; Part 3 the strict anchoring deadline; Part 4 one test per finding; Part 5 tamper matrix (each manipulation\n"
             "r5: Part 8 states the replay contract (7.6); the helper run() below opts out of the replay EXPLICITLY (most fixtures are hand-built) and asserts the REPLAY_NOT_RUN markers on every such call.\n")
replace_once(root, T1,
             "def run(jp, ap, vt=TAU + 40 * H, **kw):\n    return V.verify(jp, anchor_of(ap), JID, vt, **kw)\n",
             'def sections_view(res):\n'
             '    """r5: the result of sections 1-6 only. The 7.6 markers are asserted here on every opt-out call and then removed, so that the section-level assertions below keep their meaning."""\n'
             '    assert res["replayed"] is False and res["analysis_eligible"] is False and res["verdict"] in ("INCOMPLETE", "FAIL"), (res["verdict"], res["replayed"])\n'
             '    assert "REPLAY_NOT_RUN" in res["hard"] and [f for f in res["findings"] if f[0] == "REPLAY_NOT_RUN"][0][1] == 0\n'
             '    out = dict(res)\n'
             '    out["findings"] = [f for f in res["findings"] if f[0] != "REPLAY_NOT_RUN"]\n'
             '    out["hard"] = [h for h in res["hard"] if h != "REPLAY_NOT_RUN"]\n'
             '    out["verdict"] = "FAIL" if out["hard"] else "PASS"\n'
             '    del out["replayed"], out["analysis_eligible"]\n'
             '    return out\n\n\n'
             'def run(jp, ap, vt=TAU + 40 * H, **kw):\n'
             '    kw.setdefault("replay_slots", False)          # explicit opt-out (r5: the verifier default is True)\n'
             '    res = V.verify(jp, anchor_of(ap), JID, vt, **kw)\n'
             '    return res if kw["replay_slots"] is True else sections_view(res)\n')
replace_once(root, T1,
             '    check("SLOT written exactly at tau+10 s: no SLOT_EARLY_WRITE (boundary)", "SLOT_EARLY_WRITE" not in r["hard"] and r["hard"] == [], (r["hard"], rec["status"]))\n\nfinally:\n',
             '    check("SLOT written exactly at tau+10 s: no SLOT_EARLY_WRITE (boundary)", "SLOT_EARLY_WRITE" not in r["hard"] and r["hard"] == [], (r["hard"], rec["status"]))\n\n'
             '    # ---- Part 8 (r5, contract 7.6): the replay cannot be skipped silently ----------------------------------------------------\n'
             '    jp, ap, rec = replay_slot_journal("g2", TAU + 10_000)\n'
             '    VT = TAU + 40 * H\n'
             '    on = V.verify(jp, anchor_of(ap), JID, VT)                                      # the DEFAULT call: no replay_slots argument\n'
             '    check("G-2: the default call runs the replay (replayed, PASS, analysis_eligible, no hard finding)", on["replayed"] is True and on["verdict"] == "PASS" and on["analysis_eligible"] is True and on["hard"] == [], (on["verdict"], on["hard"]))\n'
             '    check("G-2: no REPLAY_NOT_RUN finding when the replay ran", all(f[0] != "REPLAY_NOT_RUN" for f in on["findings"]))\n'
             '    check("G-2: the report keys are exactly the contract keys (8.2)", sorted(on) == sorted(["verdict", "findings", "hard", "soft", "n_events", "head_hex", "slots", "missing", "outcomes", "replayed", "analysis_eligible"]), sorted(on))\n'
             '    off = V.verify(jp, anchor_of(ap), JID, VT, replay_slots=False)\n'
             '    check("G-2: explicit opt-out -> verdict INCOMPLETE, replayed false, analysis_eligible false, hard == [REPLAY_NOT_RUN] at where 0",\n'
             '          off["verdict"] == "INCOMPLETE" and off["replayed"] is False and off["analysis_eligible"] is False and off["hard"] == ["REPLAY_NOT_RUN"]\n'
             '          and [f[1] for f in off["findings"] if f[0] == "REPLAY_NOT_RUN"] == [0], (off["verdict"], off["hard"]))\n'
             '    check("G-2: the opt-out result equals the replayed result in everything except the replay markers", all(off[k] == on[k] for k in ("n_events", "head_hex", "slots", "missing", "outcomes", "soft")))\n'
             '    for val in (None, 0, 1, "yes", [], 2):\n'
             '        r = V.verify(jp, anchor_of(ap), JID, VT, replay_slots=val)\n'
             '        check("G-2: replay_slots=%r is a fail-closed opt-out (only exactly True runs the replay)" % (val,),\n'
             '              r["replayed"] is False and r["verdict"] == "INCOMPLETE" and r["analysis_eligible"] is False and "REPLAY_NOT_RUN" in r["hard"])\n'
             '    evs = evs_of(jp)\n'
             '    k = [n for n, e in enumerate(evs) if e["t"] == "SLOT"][0]\n'
             '    evs[k]["n_messages"] += 1\n'
             '    tp = os.path.join(tmp, "g2_tamper.jsonl")\n'
             '    write_evs(tp, evs)\n'
             '    t_off = V.verify(tp, anchor_of(ap), JID, VT, replay_slots=False)\n'
             '    t_on = V.verify(tp, anchor_of(ap), JID, VT)\n'
             '    check("G-2: a tampered journal without the replay is FAIL (not INCOMPLETE), lists REPLAY_NOT_RUN next to the real finding, and is not eligible",\n'
             '          t_off["verdict"] == "FAIL" and "REPLAY_NOT_RUN" in t_off["hard"] and len(t_off["hard"]) > 1 and t_off["analysis_eligible"] is False, t_off["hard"])\n'
             '    check("G-2: the same tampered journal WITH the replay is FAIL, replayed, not eligible, and has no REPLAY_NOT_RUN", t_on["verdict"] == "FAIL" and t_on["replayed"] is True and t_on["analysis_eligible"] is False and "REPLAY_NOT_RUN" not in t_on["hard"], t_on["hard"])\n'
             '    check("G-2: analysis_eligible == (verdict is PASS and replayed) in every report above", all(r["analysis_eligible"] == (r["verdict"] == "PASS" and r["replayed"]) for r in (on, off, t_off, t_on)))\n'
             '    check("G-2: PASS never occurs without the replay", all(not (r["verdict"] == "PASS" and not r["replayed"]) for r in (on, off, t_off, t_on)))\n\n'
             'finally:\n')

# ------------------------------------------------------------------------------------------------- independent verifier tests
T2 = "indep_verifier/test_indep.py"
replace_once(root, T2, "import hashlib\nimport json\nimport math\nimport os\nimport shutil\nimport sys\nimport tempfile\nimport unittest\n",
             "import hashlib\nimport inspect\nimport json\nimport math\nimport os\nimport shutil\nimport sys\nimport tempfile\nimport unittest\n")
replace_once(root, T2, 'def run(src, anchor, vt=0, newline=True, jid=JID):\n    """src: JW or raw bytes.  Returns the verify() result and records seen findings."""\n',
             'def run_raw(src, anchor, vt=0, newline=True, jid=JID):\n    """src: JW or raw bytes.  Returns the RAW verify() result (r5: with the REPLAY_NOT_RUN markers) and records seen findings."""\n')
replace_once(root, T2, '    for f in res["findings"]:\n        SEEN.add(f[0])\n    return res\n',
             '    for f in res["findings"]:\n        SEEN.add(f[0])\n'
             '    assert res["verdict"] != "PASS" and res["replayed"] is False and res["analysis_eligible"] is False, res["verdict"]      # r5: this verifier has no replay\n'
             '    return res\n\n\n'
             'def sections_view(res):\n'
             '    """r5: the result of sections 1-6 only (REPLAY_NOT_RUN and the markers removed; INCOMPLETE read as the old PASS), so the section-level assertions keep their meaning."""\n'
             '    assert "REPLAY_NOT_RUN" in res["hard"] and [f[1] for f in res["findings"] if f[0] == "REPLAY_NOT_RUN"] == [0]\n'
             '    out = dict(res)\n'
             '    out["findings"] = [f for f in res["findings"] if f[0] != "REPLAY_NOT_RUN"]\n'
             '    out["hard"] = [h for h in res["hard"] if h != "REPLAY_NOT_RUN"]\n'
             '    out["verdict"] = "FAIL" if out["hard"] else "PASS"\n'
             '    del out["replayed"], out["analysis_eligible"]\n'
             '    return out\n\n\n'
             'def run(src, anchor, vt=0, newline=True, jid=JID):\n    return sections_view(run_raw(src, anchor, vt, newline, jid))\n')
replace_once(root, T2, "class ZZ_Coverage(unittest.TestCase):\n",
             'class ZA_ReplayMarkers(unittest.TestCase):\n'
             '    """r5, contract 7.6: this verifier has no SLOT replay, so it must never look like a complete verification."""\n\n'
             '    def test_clean_journal_is_incomplete_not_pass(self):\n'
             '        a, jw = clean_journal()\n'
             '        res = run_raw(jw, a, vt=TAU0 + 2 * G + D + 1)\n'
             '        self.assertEqual(res["verdict"], "INCOMPLETE")\n'
             '        self.assertEqual(res["hard"], ["REPLAY_NOT_RUN"])\n'
             '        self.assertEqual([f[:2] for f in res["findings"]], [["REPLAY_NOT_RUN", 0]])\n'
             '        self.assertIs(res["replayed"], False)\n'
             '        self.assertIs(res["analysis_eligible"], False)\n'
             '        self.assertEqual(res["soft"], [])\n\n'
             '    def test_tampered_journal_is_fail_and_still_lists_replay_not_run(self):\n'
             '        a, jw = clean_journal()\n'
             '        lines = jw.bytes_().split(b"\\n")[:-1]\n'
             '        lines[3] = lines[3].replace(b\'"N_total":3\', b\'"N_total":4\')\n'
             '        res = run_raw(b"\\n".join(lines) + b"\\n", a, vt=TAU0 + 2 * G + D + 1)\n'
             '        self.assertEqual(res["verdict"], "FAIL")\n'
             '        self.assertIn("REPLAY_NOT_RUN", res["hard"])\n'
             '        self.assertGreater(len(res["hard"]), 1)\n'
             '        self.assertIs(res["analysis_eligible"], False)\n\n'
             '    def test_there_is_no_way_to_enable_a_replay(self):\n'
             '        self.assertEqual(list(inspect.signature(verify).parameters), ["path", "anchor", "journal_id", "verify_time_ms"])\n\n'
             '    def test_replay_not_run_is_a_hard_name(self):\n'
             '        self.assertIn("REPLAY_NOT_RUN", verify_indep.HARD_NAMES)\n\n\n'
             'class ZZ_Coverage(unittest.TestCase):\n')

# ------------------------------------------------------------------------------------------------- builder end-to-end tests
T3 = "builder/test_build_slots_v2_e2e.py"
replace_once(root, T3,
             '        self.assertEqual((c.p["verdict"], c.i["verdict"], c.p["hard"], c.i["hard"]), ("PASS", "PASS", [], []))\n'
             '        self.assertIs(c.p["replayed"], True)\n'
             '        summary, primary, control = c.build()\n',
             '        self.assertEqual((c.p["verdict"], c.i["verdict"], c.p["hard"], c.i["hard"]), ("PASS", "INCOMPLETE", [], ["REPLAY_NOT_RUN"]))\n'
             '        self.assertIs(c.p["replayed"], True)\n'
             '        self.assertIs(c.p["analysis_eligible"], True)\n'
             '        self.assertIs(c.i["replayed"], False)\n'
             '        self.assertIs(c.i["analysis_eligible"], False)\n'
             '        # r5 / G-2: with the default policy no build is analysis-eligible while the independent verifier has no replay\n'
             '        with self.assertRaisesRegex(BUILDER.BuildError, "analysis_eligible=False"):\n'
             '            c.build()\n'
             '        diag, _, _ = c.diag()\n'
             '        self.assertTrue(diag["registry_ok"])\n'
             '        self.assertFalse(diag["analysis_eligible"])\n'
             '        self.assertTrue(diag["independent_replay_required"])\n'
             '        self.assertFalse(diag["independent_replayed"])\n'
             '        self.assertNotIn("REPLAY_NOT_RUN", diag["hard_findings"])\n'
             '        with mock.patch.object(BUILDER, "REQUIRE_INDEPENDENT_REPLAY", False):      # exercises the row/CSV path only; the policy default is True\n'
             '            summary, primary, control = c.build()\n'
             '        self.assertTrue(summary["analysis_eligible"])\n')
replace_once(root, T3, '        self.assertEqual(c.i["hard"], [])\n        self.assertEqual(c.i["verdict"], "PASS")\n',
             '        self.assertEqual(c.i["hard"], ["REPLAY_NOT_RUN"])          # r5: nothing else, but never a PASS: it has no replay\n        self.assertEqual(c.i["verdict"], "INCOMPLETE")\n')
replace_once(root, T3, "    def test_pinned_hashes_are_those_of_the_shipped_verifier_files(self):\n",
             '    def test_cli_writes_no_csv_without_independent_replay(self):\n'
             '        c = Case(self, CLEAN)\n'
             '        for required, rc, csv_exists in ((True, 2, False), (False, 0, True)):\n'
             '            prefix = os.path.join(c.dir, "out_%s" % required)\n'
             '            with mock.patch.object(BUILDER, "REQUIRE_INDEPENDENT_REPLAY", required), mock.patch.object(BUILDER.sys, "argv", ["b", c.journal, c.r1, c.r2, c.snap, "--out-prefix", prefix]):\n'
             '                with contextlib.redirect_stdout(io.StringIO()), contextlib.redirect_stderr(io.StringIO()):\n'
             '                    self.assertEqual(BUILDER.main(), rc)\n'
             '            self.assertEqual(os.path.exists(prefix + ".csv"), csv_exists)\n'
             '            self.assertEqual(_load(prefix + ".summary.json")["analysis_eligible"], not required)\n\n'
             '    def test_report_without_replay_markers_is_refused(self):\n'
             '        c = Case(self, CLEAN[:1])\n'
             '        for key in ("replayed", "analysis_eligible"):\n'
             '            rep = {k: v for k, v in c.p.items() if k != key}\n'
             '            _dump(rep, c.r1)\n'
             '            with self.assertRaisesRegex(BUILDER.BuildError, "replay markers"):\n'
             '                c.diag()\n\n'
             '    def _with_expected(self, primary=None, independent=None):\n'
             '        real = BUILDER.run_pinned_verifiers\n\n'
             '        def fake(journal, snap):\n'
             '            p, i, h = real(journal, snap)\n'
             '            return (primary if primary is not None else p), (independent if independent is not None else i), h\n'
             '        return mock.patch.object(BUILDER, "run_pinned_verifiers", fake)\n\n'
             '    def test_primary_report_without_replay_is_a_hard_failure_even_when_it_matches_the_execution(self):\n'
             '        c = Case(self, CLEAN[:1])\n'
             '        p2 = dict(c.p, replayed=False, analysis_eligible=False, verdict="INCOMPLETE", hard=sorted(set(c.p["hard"]) | {"REPLAY_NOT_RUN"}),\n'
             '                  findings=c.p["findings"] + [["REPLAY_NOT_RUN", 0, "forged: the primary verifier did not replay"]])\n'
             '        _dump(p2, c.r1)\n'
             '        with self._with_expected(primary=p2):\n'
             '            summary, _, _ = c.diag()\n'
             '        self.assertIn("PRIMARY_REPLAY_NOT_RUN", summary["hard_findings"])\n'
             '        self.assertFalse(summary["registry_ok"])\n'
             '        self.assertFalse(summary["analysis_eligible"])\n'
             '        self.assertFalse(summary["primary_replayed"])\n\n'
             '    def test_report_claiming_eligibility_without_a_replay_is_inconsistent(self):\n'
             '        c = Case(self, CLEAN[:1])\n'
             '        i2 = dict(c.i, analysis_eligible=True)\n'
             '        _dump(i2, c.r2)\n'
             '        with self._with_expected(independent=i2):\n'
             '            summary, _, _ = c.diag()\n'
             '        self.assertIn("VERIFIER_REPORT_INCONSISTENT", summary["hard_findings"])\n'
             '        self.assertFalse(summary["registry_ok"])\n'
             '        self.assertFalse(summary["analysis_eligible"])\n\n'
             '    def test_forged_report_that_differs_from_the_execution_is_refused(self):\n'
             '        c = Case(self, CLEAN[:1])\n'
             '        _dump(dict(c.i, analysis_eligible=True), c.r2)\n'
             '        with self.assertRaisesRegex(BUILDER.BuildError, "does not match execution"):\n'
             '            c.diag()\n\n'
             '    def test_pinned_hashes_are_those_of_the_shipped_verifier_files(self):\n')
print("p05 ok")
