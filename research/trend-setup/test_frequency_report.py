#!/usr/bin/env python3
"""Synthetic tests for frequency_report.py (same author as the code; they check counting and carry logic, not any edge).
Run: python -I -B research/trend-setup/test_frequency_report.py
"""
import sys
import unittest
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import frequency_report as F  # noqa: E402
import test_trendsetup as TT  # noqa: E402
import trendsetup as T  # noqa: E402


class Counting(unittest.TestCase):
    def test_signal_events(self):
        sig = np.array([0, 0, .2, .2, .6, .6, 0, 0, .2])
        ready = np.ones(9, bool)
        self.assertEqual(F.signal_events(sig, ready), (2, 1, 1))

    def test_events_ignore_bars_before_ready(self):
        sig = np.array([0, .2, .4, .4, 0])
        ready = np.array([False, False, True, True, True])
        self.assertEqual(F.signal_events(sig, ready), (0, 1, 0))  # only the 0.4 -> 0 exit is counted

    def test_carry_weights_hold_until_the_next_signal_change(self):
        sig = np.array([0, 0, .2, .2, .6, .6, 0])
        w = np.array([0, 0, .1, .12, .3, .33, 0])
        ready = np.array([False, True, True, True, True, True, True])
        out = F.carry_weights(sig, w, ready)
        self.assertTrue(np.allclose(out, [0, 0, .1, .1, .3, .3, 0]))

    def test_carry_starts_from_the_first_ready_bar(self):
        sig = np.array([.4, .4, .4, .4])
        w = np.array([.3, .31, .29, .3])
        ready = np.array([False, False, True, True])
        out = F.carry_weights(sig, w, ready)
        self.assertTrue(np.allclose(out, [0, 0, .29, .29]))


class EndToEnd(unittest.TestCase):
    def test_build_on_synthetic_universe(self):
        raw = TT.synth(12, 1500, 21, 0)
        datas = {sym: dict(raw[k], symbol=sym) for k, sym in zip(sorted(raw), T.UNIVERSE)}
        rep = F.build(datas, [], T.code_sha256())
        self.assertEqual([b["n"] for b in rep["baskets"]], [1, 2, 5, 10, 12])  # the last basket is capped by the coins available
        for s, c in rep["coin"].items():
            self.assertLessEqual(c["weight_change_days_v1"], c["weight_change_days_v0"])
            self.assertEqual(c["events"], c["entries"] + c["exits"] + c["steps"])
            self.assertLessEqual(c["turnover_per_year_v1"], c["turnover_per_year_v0"] * 1.0001 + 1e-9)
        self.assertTrue(all(np.isfinite(b["events_per_week"]) for b in rep["baskets"]))
        self.assertIn("btc", rep["variants"])
        md = F.summary_md(rep)
        self.assertIn("signal events per week", md)
        self.assertEqual(rep["code_sha256"], T.code_sha256())

    def test_baskets_arithmetic(self):
        raw = TT.synth(6, 1500, 5, 0)
        datas = {sym: dict(raw[k], symbol=sym) for k, sym in zip(sorted(raw), T.UNIVERSE)}
        rep = F.build(datas, [], T.code_sha256())
        b5 = [b for b in rep["baskets"] if b["n"] == 5][0]
        ev = sum(rep["coin"][s]["events"] for s in b5["members"])
        yrs = np.mean([rep["coin"][s]["years"] for s in b5["members"]])
        self.assertAlmostEqual(b5["events_per_week"], ev / (yrs * 52.0), places=12)


if __name__ == "__main__":
    unittest.main()
