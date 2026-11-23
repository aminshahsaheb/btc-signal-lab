#!/usr/bin/env python3
"""Synthetic tests for backtest_report.py (same author as the code; they check arithmetic and bookkeeping, not that the rule earns money).
Run: python -I -B research/trend-setup/test_backtest_report.py
"""
import math
import sys
import unittest
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import backtest_report as B  # noqa: E402
import trendsetup as T  # noqa: E402
from test_trendsetup import synth, trending  # noqa: E402

DAY = T.DAY_MS


class Stats(unittest.TestCase):
    def test_constant_return(self):
        t = T.START_MS + DAY * np.arange(365, dtype=np.int64)
        s = B.stats(t, np.full(365, 0.001))
        self.assertAlmostEqual(s["total"], 1.001 ** 365 - 1, places=9)
        self.assertAlmostEqual(s["cagr"], 1.001 ** 365 - 1, places=9)
        self.assertEqual(s["maxdd"], 0.0)

    def test_drawdown_and_nan_days(self):
        t = T.START_MS + DAY * np.arange(5, dtype=np.int64)
        s = B.stats(t, np.array([0.1, -0.5, np.nan, 0.2, 0.0]))
        self.assertEqual(s["days"], 4)
        self.assertAlmostEqual(s["maxdd"], 0.5, places=12)
        self.assertAlmostEqual(s["total"], 1.1 * 0.5 * 1.2 - 1, places=12)

    def test_too_short_series(self):
        self.assertEqual(B.stats(np.array([0, 1]), np.array([0.1, 0.1])), dict(days=2))

    def test_yearly_compounds_inside_calendar_years(self):
        t = np.array([1_704_067_200_000 - DAY, 1_704_067_200_000, 1_704_067_200_000 + DAY], dtype=np.int64)  # 2023-12-31, 2024-01-01, 2024-01-02
        y = B.yearly(t, np.array([0.10, 0.20, 0.30]))
        self.assertAlmostEqual(y["2023"]["ret"], 0.10)
        self.assertAlmostEqual(y["2024"]["ret"], 1.2 * 1.3 - 1)

    def test_window_is_half_open(self):
        t = T.START_MS + DAY * np.arange(10, dtype=np.int64)
        tw, rw = B.window(t, np.arange(10.0), t[3], t[7])
        self.assertEqual(list(rw), [3.0, 4.0, 5.0, 6.0])

    def test_sample_includes_last_point_and_starts_at_one_step(self):
        t = T.START_MS + DAY * np.arange(20, dtype=np.int64)
        s = B.sample(t, np.full(20, 0.01))
        self.assertEqual(s[-1][0], B.date_of(t[-1]))
        self.assertAlmostEqual(s[-1][1], 1.01 ** 20, places=4)
        self.assertEqual(s[0][0], B.date_of(t[0]))


class Engine(unittest.TestCase):
    def test_single_coin_steady_uptrend(self):
        g = 0.004
        d = list(trending(1, 400, g).values())[0]
        t, R, Rs, Rr, w = B.single_coin(d)
        j = 261  # first bar after warm-up: weight decided at close of bar 260
        self.assertTrue(np.isnan(R[260]))
        self.assertAlmostEqual(Rr[j], g, places=9)
        self.assertAlmostEqual(R[j + 5], g, places=9)  # steady state: full weight, no cost
        self.assertAlmostEqual(R[j], g - T.C_SIDE, places=9)  # entry cost on the first held day

    def test_raw_hold_and_exposure(self):
        g = 0.004
        datas = trending(3, 400, g)
        t, raw, expo = B.raw_hold_and_exposure(datas)
        self.assertAlmostEqual(raw[300], g, places=9)
        self.assertAlmostEqual(expo[300], 1.0, places=6)
        self.assertTrue(np.isnan(raw[0]) and np.isnan(raw[-1]))

    def test_report_structure_and_consistency(self):
        datas = synth(5, 900, 4242, 30)
        datas["BTCUSDT"] = datas.pop("C0USDT")
        rep = B.build_report(datas, notes=[], code_sha="a" * 64)
        for k in ("portfolio", "btc_only"):
            self.assertIn(k, rep)
        p = rep["portfolio"]
        for part in ("strategy", "scaled_hold", "raw_hold"):
            self.assertEqual(set(p[part]), {"label", "full", "pre2023", "from2023", "yearly"})
        self.assertEqual(p["series"]["strategy"][0][1] > 0, True)
        # the sampled strategy curve ends at the strategy's total return
        self.assertAlmostEqual(p["series"]["strategy"][-1][1], 1 + p["strategy"]["full"]["total"], places=4)
        self.assertLessEqual(rep["portfolio"]["avg_gross_exposure"], 1.0 + 1e-9)
        self.assertGreaterEqual(rep["portfolio"]["avg_gross_exposure"], 0.0)
        json_ok = __import__("json").dumps(rep)
        self.assertGreater(len(json_ok), 1000)

    def test_summary_markdown_flags_in_sample(self):
        datas = synth(5, 900, 4242, 30)
        datas["BTCUSDT"] = datas.pop("C0USDT")
        md = B.summary_md(B.build_report(datas))
        self.assertIn("In-sample description, not evidence", md)
        self.assertIn("BTC alone", md)

    def test_frozen_tool_is_unchanged(self):
        import hashlib
        want = {}
        for line in (HERE / "CODE_SHA256.txt").read_text().splitlines():
            h, name = line.split()
            want[name] = h
        for name, h in want.items():
            self.assertEqual(hashlib.sha256((HERE / name).read_bytes()).hexdigest(), h, name)


if __name__ == "__main__":
    unittest.main(verbosity=1)
