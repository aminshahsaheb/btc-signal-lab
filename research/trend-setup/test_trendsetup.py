#!/usr/bin/env python3
"""Synthetic tests for trendsetup.py. Same author as the code: they show the code does what the specification says, not that the rule earns money.
Run: python -I -B research/trend-setup/test_trendsetup.py
"""
import datetime as dt
import json
import math
import sys
import unittest
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import trendsetup as T  # noqa: E402

DAY = T.DAY_MS
MASK = (1 << 64) - 1


def stream(seed):
    x = seed & MASK
    while True:
        x = (6364136223846793005 * x + 1442695040888963407) & MASK
        yield (x >> 11) / float(1 << 53)


def synth(n, Tn, seed, stagger):
    """Deterministic pure-python generator (no numpy RNG): AR(0.15) log returns, small drift, stagger = listing delay per coin in bars."""
    u = stream(seed)
    out = {}
    for a in range(n):
        st = stagger * a
        m = Tn - st
        o_, h_, l_, c_ = [], [], [], []
        prev, r_prev = 100.0, 0.0
        for _ in range(m):
            r = 0.15 * r_prev + (next(u) - 0.5) * 0.12 + 0.0004
            o = prev
            c = o * math.exp(r)
            h = max(o, c) * (1 + 0.01 * next(u))
            l = min(o, c) * (1 - 0.01 * next(u))
            o_.append(o); h_.append(h); l_.append(l); c_.append(c)
            prev, r_prev = c, r
        out[f"C{a}USDT"] = dict(t=T.START_MS + DAY * (st + np.arange(m, dtype=np.int64)), o=np.array(o_), h=np.array(h_), l=np.array(l_), c=np.array(c_),
                                symbol=f"C{a}USDT", missing_days=0)
    return out


def trending(n, Tn, g, start=0):
    out = {}
    for a in range(n):
        c = 100.0 * (1 + g) ** np.arange(1, Tn + 1)
        o = np.r_[100.0, c[:-1]]
        out[f"T{a}USDT"] = dict(t=T.START_MS + DAY * (start + np.arange(Tn, dtype=np.int64)), o=o, h=np.maximum(o, c) * 1.0001, l=np.minimum(o, c) * 0.9999, c=c,
                                symbol=f"T{a}USDT", missing_days=0)
    return out


class Constants(unittest.TestCase):
    def test_t0_and_universe(self):
        self.assertEqual(dt.datetime.fromtimestamp(T.T0_MS / 1000, dt.timezone.utc), dt.datetime(2026, 11, 22, tzinfo=dt.timezone.utc))
        self.assertEqual(T.T0_MS % DAY, 0)
        self.assertEqual(len(T.UNIVERSE), 26)
        self.assertEqual(len(set(T.UNIVERSE)), 26)
        for s in ("BTCUSDT", "ETHUSDT", "SOLUSDT"):
            self.assertIn(s, T.UNIVERSE)
        self.assertEqual(T.ENS_N, (10, 20, 30, 55, 100))
        self.assertEqual((T.TARGET_VOL, T.VOL_WINDOW, T.WARMUP_BARS, T.C_SIDE), (0.50, 30, 260, 0.0008))


class Rule(unittest.TestCase):
    def test_donchian_hand_checked(self):
        c = np.array([1, 1, 1, 1, 2, 3, 3, 0.5, 2, 2], float)
        np.testing.assert_array_equal(T.donchian_state(c, c, c, 4), [0, 0, 0, 0, 1, 1, 1, 0, 0, 0])

    def test_exit_uses_half_length(self):
        # N=4 -> exit channel of 2 bars. A close below the 2-bar low (but above the 4-bar low) must exit.
        c = np.array([1, 1, 1, 1, 5, 6, 7, 6.5, 6.4], float)
        h = c.copy(); l = c.copy()
        st = T.donchian_state(h, l, c, 4)
        self.assertEqual(list(st[:6]), [0, 0, 0, 0, 1, 1])
        self.assertEqual(st[7], 1)  # 6.5 is not below min(l[5:7]) = 6
        self.assertEqual(st[8], 0)  # 6.4 < min(l[6:8]) = 6.5 -> exit although well above the 4-bar low

    def test_signal_levels_and_ensemble_average(self):
        d = list(trending(1, 400, 0.01).values())[0]
        cc = T.coin_calc(d)
        self.assertTrue(set(np.round(cc["sig"], 6)) <= {0.0, 0.2, 0.4, 0.6, 0.8, 1.0})
        np.testing.assert_allclose(cc["sig"], cc["S"].mean(axis=1))
        self.assertEqual(cc["sig"][-1], 1.0)  # a steady uptrend: all five states are long

    def test_causal_no_future_leak(self):
        d = list(synth(1, 700, 5, 0).values())[0]
        full = T.coin_calc(d)
        for cut in (150, 260, 333, 500, 699):
            part = T.coin_calc({k: (v[:cut + 1] if isinstance(v, np.ndarray) else v) for k, v in d.items()})
            for key in ("sig", "vol", "scale", "w"):
                np.testing.assert_allclose(np.nan_to_num(part[key][cut]), np.nan_to_num(full[key][cut]), atol=1e-12, err_msg=f"{key} at {cut}")

    def test_vol_scale_and_cap(self):
        n = 120
        for r, expect_cap in ((0.01, True), (0.05, False)):
            ret = np.where(np.arange(n) % 2 == 0, r, -r)
            c = 100 * np.cumprod(1 + ret)
            v = T.vol30(c)
            self.assertTrue(np.isnan(v[29]) and np.isfinite(v[30]))
            self.assertAlmostEqual(v[-1], r * math.sqrt(365), delta=0.02 * r * math.sqrt(365))
            d = dict(h=c, l=c, c=c)
            sc = T.coin_calc(d)["scale"][-1]
            self.assertLessEqual(sc, 1.0)
            if expect_cap:
                self.assertEqual(sc, 1.0)
            else:
                self.assertAlmostEqual(sc, 0.5 / v[-1], places=9)

    def test_zero_vol_gives_zero_weight(self):
        c = np.full(400, 100.0)
        cc = T.coin_calc(dict(h=c, l=c, c=c))
        self.assertEqual(float(np.abs(cc["w"]).max()), 0.0)

    def test_warmup_260(self):
        d = list(trending(1, 400, 0.01).values())[0]
        cc = T.coin_calc(d)
        self.assertEqual(float(cc["w"][:260].max()), 0.0)
        self.assertGreater(float(cc["w"][260:].max()), 0.0)


class Golden(unittest.TestCase):
    def test_reproduces_search_lab_vectors(self):
        g = json.loads((HERE / "golden_vectors.json").read_text())
        gen = g["provenance"]["generator"]
        datas = synth(gen["n"], gen["T"], gen["seed"], gen["stagger"])
        G = T.grid(datas)
        self.assertEqual(G["names"], g["names"])
        W = np.nan_to_num(G["W"]).T
        np.testing.assert_allclose(W, np.array(g["weights"]), atol=1e-9)
        t0 = T.START_MS + g["provenance"]["t0_index"] * DAY
        tr = T.paper_track(datas, t0_ms=t0, c_side=g["provenance"]["c_side"], start_flat=False)
        got = tr["R"][tr["t"] >= t0]
        want = np.array([np.nan if x is None else x for x in g["paper_returns"]])
        self.assertEqual(len(got), len(want))
        self.assertTrue((np.isnan(got) == np.isnan(want)).all())
        np.testing.assert_allclose(got[np.isfinite(got)], want[np.isfinite(want)], atol=1e-9)
        self.assertGreater(int(np.isfinite(want).sum()), 100)

    def test_live_differential_if_search_lab_is_present(self):
        p = HERE.parent / "search-lab"
        if not (p / "searchlab.py").exists():
            self.skipTest("search-lab engine not in this tree (the golden-vector test above carries its output)")
        sys.path.insert(0, str(p))
        import searchlab as S
        datas = synth(5, 700, 12345, 60)
        P = S.build_panel({k: {kk: v[kk] for kk in ("t", "o", "h", "l", "c")} for k, v in datas.items()}, S.START_MS, S.START_MS + 700 * DAY)
        pos = [x for x in S.VARIANTS if x["id"] == "ENSEMBLE:DONCH5LF"][0]["fn"](P)
        np.testing.assert_allclose(np.nan_to_num(T.grid(datas)["W"]), np.where(P["ready"], pos * P["scale"], 0.0), atol=1e-12)


class Paper(unittest.TestCase):
    def setUp(self):
        self.g = 0.004
        self.datas = trending(3, 420, self.g)
        self.t0 = T.START_MS + 350 * DAY

    def test_first_day_pays_entry_cost_then_none(self):
        tr = T.paper_track(self.datas, t0_ms=self.t0)
        j0 = 350
        self.assertAlmostEqual(tr["R"][j0], self.g - T.C_SIDE, places=9)
        self.assertAlmostEqual(tr["R"][j0 + 1], self.g, places=9)
        self.assertAlmostEqual(tr["Rb"][j0], self.g - T.C_SIDE, places=9)

    def test_counts_only_bars_from_t0_and_not_the_last_bar(self):
        tr = T.paper_track(self.datas, t0_ms=self.t0)
        fin = np.isfinite(tr["R"])
        self.assertEqual(int(fin.sum()), 420 - 350 - 1)
        self.assertFalse(fin[:350].any())
        self.assertFalse(fin[-1])

    def test_needs_three_active_coins(self):
        tr = T.paper_track(trending(2, 420, self.g), t0_ms=self.t0)
        self.assertFalse(np.isfinite(tr["R"]).any())

    def test_equity_stats(self):
        s = T._equity_stats(np.array([0.1, -0.5, 0.2, np.nan]))
        self.assertEqual(s["days"], 3)
        self.assertAlmostEqual(s["cum"], 1.1 * 0.5 * 1.2 - 1, places=12)
        self.assertAlmostEqual(s["maxdd"], 0.5, places=12)
        self.assertEqual(T._equity_stats(np.array([np.nan]))["days"], 0)

    def test_render_paper_makes_no_early_performance_claim(self):
        tr = T.paper_track(self.datas, t0_ms=self.t0)
        txt = T.render_paper(tr, self.datas, "x" * 64, [dict(symbol="A", status="OK")])
        self.assertIn("UNPROVEN", txt)
        self.assertIn("fewer than 90", txt)


class Table(unittest.TestCase):
    def test_weights_stale_and_warmup(self):
        datas = trending(4, 400, 0.004)
        late = trending(1, 100, 0.004, start=300)  # listed 100 bars ago: warm-up
        datas["NEWUSDT"] = list(late.values())[0]
        stale = trending(1, 380, 0.004)  # ends 20 days early
        datas["OLDUSDT"] = list(stale.values())[0]
        asof = T.START_MS + 400 * DAY
        rows, n = T.table_rows(datas, asof)
        by = {r["symbol"]: r for r in rows}
        self.assertEqual(n, 4)
        self.assertFalse(by["OLDUSDT"]["fresh"])
        self.assertFalse(by["NEWUSDT"]["ready"])
        self.assertEqual(by["OLDUSDT"]["w_eq"], 0.0)
        self.assertEqual(by["NEWUSDT"]["w_eq"], 0.0)
        for r in rows:
            if r["ready"]:
                self.assertAlmostEqual(r["w_eq"], r["w_coin"] / n)
        self.assertLessEqual(sum(r["w_eq"] for r in rows), 1.0 + 1e-12)
        txt = T.render_table(rows, n, asof, 10000, [dict(symbol="A", status="OK")], "y" * 64)
        self.assertIn("UNPROVEN", txt)
        self.assertIn("stale", txt)
        self.assertIn("warm-up", txt)

    def test_changed_flag(self):
        c = np.r_[np.full(300, 100.0) * (1 + 0.01 * np.sin(np.arange(300))), np.linspace(100, 400, 100)]
        d = dict(t=T.START_MS + DAY * np.arange(400, dtype=np.int64), o=c, h=c * 1.001, l=c * 0.999, c=c, symbol="X", missing_days=0)
        datas = {"XUSDT": d, "YUSDT": dict(d, symbol="Y"), "ZUSDT": dict(d, symbol="Z")}
        for asof in (T.START_MS + 400 * DAY,):
            rows, n = T.table_rows(datas, asof)
            self.assertEqual(n, 3)
            txt = T.render_table(rows, n, asof, 1000, [], "z" * 64)
            self.assertTrue("CHANGED" in txt or all(abs(r["sig"] - r["prev_sig"]) < 1e-9 for r in rows))


def rows_for(symbol, n, start=T.START_MS):
    out = []
    for i in range(n):
        t = start + i * DAY
        out.append([t, "10", "11", "9", "10.5", "1", t + DAY - 1, "1", 1, "1", "1", "0"])
    return out


class Fetch(unittest.TestCase):
    def fake(self, bars_by_symbol, fail=()):
        calls = []

        def http_get(url):
            calls.append(url)
            sym = url.split("symbol=")[1].split("&")[0]
            if sym in fail:
                raise OSError("boom")
            st = int(url.split("startTime=")[1].split("&")[0])
            en = int(url.split("endTime=")[1].split("&")[0])
            rows = [r for r in bars_by_symbol[sym] if st <= r[0] <= en][:1000]
            return json.dumps(rows)
        return http_get, calls

    def test_pagination_end_exclusive_and_hash(self):
        rows = rows_for("A", 2500)
        hg, calls = self.fake({"A": rows})
        end = T.START_MS + 2400 * DAY
        d = T.fetch_klines("A", http_get=hg, end_ms=end, sleep=lambda s: None)
        self.assertEqual(len(d["c"]), 2400)
        self.assertEqual(int(d["t"][-1]), end - DAY)
        self.assertGreaterEqual(len(calls), 3)
        self.assertEqual(len(T.data_hash(d)), 64)

    def test_malformed_rows_rejected(self):
        bad = rows_for("A", 10)
        bad[3][2] = "5"  # high below close
        hg, _ = self.fake({"A": bad})
        with self.assertRaises(T.DataError):
            T.fetch_klines("A", http_get=hg, end_ms=T.START_MS + 10 * DAY, sleep=lambda s: None)

    def test_universe_excludes_failures_and_requires_enough_coins(self):
        syms = tuple(f"S{i}USDT" for i in range(10))
        data = {s: rows_for(s, 300) for s in syms}
        hg, _ = self.fake(data, fail=("S0USDT",))
        got, notes = T.load_universe(T.START_MS + 300 * DAY, http_get=hg, sleep=lambda s: None, symbols=syms)
        self.assertEqual(len(got), 9)
        self.assertEqual([n["status"] for n in notes].count("EXCLUDED"), 1)
        hg2, _ = self.fake(data, fail=syms[:5])
        with self.assertRaises(T.DataError):
            T.load_universe(T.START_MS + 300 * DAY, http_get=hg2, sleep=lambda s: None, symbols=syms)


if __name__ == "__main__":
    unittest.main(verbosity=1)
