#!/usr/bin/env python3
"""Synthetic tests for robustness_report.py (same author as the code; they check arithmetic and bookkeeping, not that the rule earns money).
Run: python -I -B research/trend-setup/test_robustness_report.py
"""
import sys
import unittest
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import robustness_report as RR  # noqa: E402
import trendsetup as T  # noqa: E402
from test_trendsetup import synth, trending  # noqa: E402


def named_panel():
    d = synth(6, 900, 99, 30)
    ren = {"C0USDT": "BTCUSDT", "C1USDT": "ETHUSDT", "C2USDT": "BNBUSDT", "C3USDT": "XRPUSDT", "C4USDT": "ADAUSDT", "C5USDT": "SOLUSDT"}
    return {ren[k]: dict(v, symbol=ren[k]) for k, v in d.items()}


class Port(unittest.TestCase):
    def test_baseline_equals_paper_track(self):
        datas = named_panel()
        G = T.grid(datas)
        R, H, E = RR.port(G, list(range(len(G["names"]))))
        tr = T.paper_track(datas, t0_ms=0, start_flat=False)
        self.assertTrue((np.isnan(R) == np.isnan(tr["R"])).all())
        np.testing.assert_allclose(R[np.isfinite(R)], tr["R"][np.isfinite(tr["R"])], atol=1e-12)
        self.assertGreater(int(np.isfinite(R).sum()), 200)

    def test_subset_equals_paper_track_on_subset(self):
        datas = named_panel()
        G = T.grid(datas)
        cols = [G["names"].index(s) for s in ("BTCUSDT", "ETHUSDT", "BNBUSDT", "XRPUSDT")]
        R, _, _ = RR.port(G, cols)
        sub = {k: datas[k] for k in ("BTCUSDT", "ETHUSDT", "BNBUSDT", "XRPUSDT")}
        tr = T.paper_track(sub, t0_ms=0, start_flat=False)
        a, b = R[np.isfinite(R)], tr["R"][np.isfinite(tr["R"])]
        self.assertEqual(len(a), len(b))
        np.testing.assert_allclose(a, b, atol=1e-12)

    def test_lag_delays_entry_by_one_day_and_keeps_steady_state(self):
        g = 0.004
        G = T.grid(trending(3, 420, g))
        cols = [0, 1, 2]
        R0, _, _ = RR.port(G, cols)
        R1, _, _ = RR.port(G, cols, lag=1)
        f0, f1 = int(np.argmax(np.isfinite(R0))), int(np.argmax(np.isfinite(R1)))
        self.assertEqual(f1, f0 + 1)
        self.assertAlmostEqual(R0[f0 + 10], g, places=9)
        self.assertAlmostEqual(R1[f1 + 10], g, places=9)
        self.assertAlmostEqual(R1[f1], g - T.C_SIDE, places=9)  # entry cost paid on the first held day

    def test_cost_reduces_return(self):
        G = T.grid(named_panel())
        a, _, _ = RR.port(G, list(range(6)), c_side=0.0008)
        b, _, _ = RR.port(G, list(range(6)), c_side=0.0030)
        m = np.isfinite(a)
        self.assertLess(float(np.nansum(b[m])), float(np.nansum(a[m])))

    def test_min_active_two_allows_a_pair(self):
        G = T.grid(named_panel())
        R3, _, _ = RR.port(G, [0, 1], min_active=3)
        R2, _, _ = RR.port(G, [0, 1], min_active=2)
        self.assertFalse(np.isfinite(R3).any())
        self.assertTrue(np.isfinite(R2).any())


class Pieces(unittest.TestCase):
    def test_rolling_constant_returns(self):
        t = T.START_MS + T.DAY_MS * np.arange(800, dtype=np.int64)
        r = RR.rolling(t, np.full(800, 0.001), np.full(800, 0.0005), 365)
        self.assertEqual(r["windows"], 800 - 365)
        self.assertEqual(r["share_rule_beats_hold"], 1.0)
        self.assertAlmostEqual(r["rule_median"], 1.001 ** 365 - 1, places=9)
        self.assertIsNone(RR.rolling(t[:300], np.full(300, 0.001), np.full(300, 0.001), 365))

    def test_cash_spells(self):
        t = T.START_MS + T.DAY_MS * np.arange(7, dtype=np.int64)
        c = RR.cash_spells(t, np.array([0, 0, 0, 0.5, 0, 0, 0.0]))
        self.assertEqual(c["longest_days"], 3)
        self.assertEqual(c["current_days"], 3)
        self.assertAlmostEqual(c["share_zero"], 6 / 7)
        self.assertEqual(c["longest_end"], RR.B.date_of(t[2]))

    def test_bootstrap_is_deterministic_and_ordered(self):
        rng = np.random.default_rng(1)
        r = rng.normal(0.0008, 0.01, 600)
        h = rng.normal(0.0004, 0.02, 600)
        a = RR.bootstrap(r, h, reps=200)
        b = RR.bootstrap(r, h, reps=200)
        self.assertEqual(a, b)
        self.assertLessEqual(a["rule_sharpe_p5"], a["rule_sharpe_p50"])
        self.assertLessEqual(a["rule_sharpe_p50"], a["rule_sharpe_p95"])
        self.assertTrue(0.0 <= a["share_rule_sharpe_above_hold"] <= 1.0)


class Build(unittest.TestCase):
    def test_structure(self):
        rep = RR.build(named_panel(), notes=[], code_sha="b" * 64)
        names = [v["name"] for v in rep["variants"]]
        for n in ("baseline", "lag1", "cost15", "cost30", "lag1_cost15", "btc_eth", "large8", "old11", "new15"):
            self.assertIn(n, names)
        self.assertEqual(len(rep["leave_one_out"]["rows"]), 6)
        self.assertEqual(len(rep["start_dates"]), 6)
        for k in ("rolling_365", "cash", "bootstrap"):
            self.assertIn(k, rep)
        md = RR.summary_md(rep)
        self.assertIn("In-sample description, not evidence", md)
        self.assertIn("Leave-one-coin-out", md)
        import json
        self.assertGreater(len(json.dumps(rep)), 1000)

    def test_frozen_files_unchanged(self):
        import hashlib
        for line in (HERE / "CODE_SHA256.txt").read_text().splitlines():
            h, name = line.split()
            self.assertEqual(hashlib.sha256((HERE / name).read_bytes()).hexdigest(), h, name)


if __name__ == "__main__":
    unittest.main(verbosity=1)
