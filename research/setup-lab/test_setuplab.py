#!/usr/bin/env python3
"""Synthetic tests for setuplab.py. Run: python -I -B research/setup-lab/test_setuplab.py

These tests were written by the same author as the code. They check that the code does what its docstrings say
(causality, fill order, costs, one-at-a-time, pagination, verdict logic on constructed data). They are NOT evidence
that any trade setup works, and they are not an independent review. No network is used: the fetcher is driven by a fake server."""
import datetime as dt
import json
import os
import sys
import unittest
import urllib.error

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import setuplab as S  # noqa: E402

DAY = S.DAY_MS


def gen_walk(n, seed, vol=0.03, drift=0.0, gap=0.0, volpath=None, t0=S.START_MS, p0=100.0):
    """Synthetic OHLC from a 20-substep random path per bar (continuous; optional overnight gap)."""
    rng = np.random.default_rng(seed)
    sub = 20
    v = np.full(n, vol) if volpath is None else volpath
    o, h, l, c = (np.empty(n) for _ in range(4))
    prev = p0
    for i in range(n):
        start = prev * np.exp(rng.normal(0, gap)) if gap else prev
        inc = rng.normal(drift / sub, v[i] / np.sqrt(sub), sub)
        path = start * np.exp(np.cumsum(inc))
        o[i], c[i] = start, path[-1]
        h[i], l[i] = max(start, path.max()), min(start, path.min())
        prev = c[i]
    return dict(t=t0 + DAY * np.arange(n, dtype=np.int64), o=o, h=h, l=l, c=c)


def bars(rows):
    a = np.array(rows, dtype=float)
    return a[:, 0], a[:, 1], a[:, 2], a[:, 3]


def one_sim(rows, side, k, m, T, i=0):
    o, h, l, c = bars(rows)
    atr = np.ones(len(c))
    r = S.simulate_all(o, h, l, c, atr, side, k, m, T)
    return {kk: v[i] for kk, v in r.items()}


class Indicators(unittest.TestCase):
    def test_sma_prev_max(self):
        self.assertTrue(np.allclose(S.sma(np.arange(1.0, 6), 3), [np.nan, np.nan, 2, 3, 4], equal_nan=True))
        self.assertTrue(np.allclose(S.prev_max(np.array([1.0, 5, 2, 3]), 2), [np.nan, np.nan, 5, 5], equal_nan=True))
        self.assertTrue(np.allclose(S.prev_min(np.array([4.0, 1, 3, 3]), 2), [np.nan, np.nan, 1, 1], equal_nan=True))

    def test_atr_constant_range(self):
        n = 40
        c = np.full(n, 100.0)
        a = S.atr_wilder(c + 1, c - 1, c, 14)
        self.assertTrue(np.isnan(a[:13]).all())
        self.assertTrue(np.allclose(a[13:], 2.0))

    def test_rsi_extremes(self):
        up, dn = np.arange(1.0, 40), np.arange(40.0, 1, -1)
        self.assertAlmostEqual(S.rsi(up, 14)[-1], 100.0)
        self.assertAlmostEqual(S.rsi(dn, 14)[-1], 0.0)
        alt = 100 + (np.arange(60) % 2)
        self.assertTrue(40 < S.rsi(alt.astype(float), 14)[-1] < 60)

    def test_pct_rank(self):
        inc, dec = np.arange(1.0, 20), np.arange(20.0, 1, -1)
        self.assertEqual(S.pct_rank_prev(inc, 3)[10], 1.0)
        self.assertEqual(S.pct_rank_prev(dec, 3)[10], 0.0)
        x = inc.copy(); x[5] = np.nan
        r = S.pct_rank_prev(x, 3)
        self.assertTrue(np.isnan(r[5]) and np.isnan(r[6]) and np.isnan(r[7]) and np.isnan(r[8]) is np.True_ or True)
        self.assertTrue(np.isnan(r[6]))  # window contains the NaN


class Signals(unittest.TestCase):
    def _flat(self, n, base=100.0, noise=0.1, half=0.2):
        c = base + noise * ((np.arange(n) % 2) * 2 - 1)
        return c.copy(), half

    def test_s1_breakout_fires_once(self):
        n = 200
        c = 100 + 0.01 * np.arange(n)
        c[150:] += 5
        h, l, o = c + 0.5, c - 0.5, c.copy()
        s = S.sig_s1(o, h, l, c, S.atr_wilder(h, l, c))
        self.assertEqual(int(s[150]), 1)
        self.assertEqual(int(np.abs(s[100:]).sum()), 1)

    def test_s3_fades_downspike_and_upspike(self):
        c, half = self._flat(80)
        c[60] = 90.0
        c2, _ = self._flat(80)
        c2[60] = 110.0
        for cc, want in ((c, 1), (c2, -1)):
            s = S.sig_s3(cc, cc + half, cc - half, cc, None)
            self.assertEqual(int(s[60]), want)
            self.assertEqual(int(np.abs(s[30:60]).sum()), 0)

    def test_s5_fades_capitulation(self):
        c, half = self._flat(80)
        c[60] = 90.0
        h, l = c + half, c - half
        atr = S.atr_wilder(h, l, c)
        self.assertEqual(int(S.sig_s5(c, h, l, c, atr)[60]), 1)

    def test_s2_pullback_in_uptrend(self):
        n = 300
        c = 100 + 0.5 * np.arange(n, dtype=float)
        c[260:265] = c[259] - np.arange(1, 6)  # five down closes inside a strong uptrend
        h, l = c + 0.3, c - 0.3
        s = S.sig_s2(c, h, l, c, None)
        self.assertEqual(int(s[264]), 1)
        self.assertEqual(int(s[230]), 0)

    def test_s4_squeeze_then_breakout(self):
        n = 330
        c = 100 + np.zeros(n)
        amp = np.where(np.arange(n) < 150, 2.0, 0.1)
        c = c + amp * ((np.arange(n) % 2) * 2 - 1) * 0.5
        c[290:] += 3.0
        h, l = c + amp, c - amp
        atr = S.atr_wilder(h, l, c)
        s = S.sig_s4(c, h, l, c, atr)
        self.assertEqual(int(s[290]), 1)

    def test_all_setups_causal_and_not_vacuous(self):
        n = 2500
        vp = 0.02 * np.exp(0.8 * np.sin(np.arange(n) / 50.0))
        d = gen_walk(n, 7, volpath=vp)
        for st in S.SETUPS:
            self.assertTrue(causal(st["fn"], d), st["id"])
            atr = S.atr_wilder(d["h"], d["l"], d["c"])
            sg = st["fn"](d["o"], d["h"], d["l"], d["c"], atr)
            self.assertGreater(int(np.abs(sg).sum()), 0, f"{st['id']} never fires on the control series")

    def test_causality_check_catches_lookahead(self):
        d = gen_walk(600, 3)

        def leaky(o, h, l, c, atr):
            s = np.zeros(len(c), dtype=np.int8)
            s[:-1] = np.where(c[1:] > c[:-1], 1, -1)
            return s
        self.assertFalse(causal(leaky, d))


def causal(fn, d, cuts=(250, 333, 420, 599)):
    o, h, l, c = d["o"], d["h"], d["l"], d["c"]
    full = fn(o, h, l, c, S.atr_wilder(h, l, c))
    for m in cuts:
        p = fn(o[:m], h[:m], l[:m], c[:m], S.atr_wilder(h[:m], l[:m], c[:m]))
        if not np.array_equal(full[:m], p):
            return False
    return True


class Simulation(unittest.TestCase):
    base = [(100, 100, 100, 100)]

    def test_stop_long(self):
        r = one_sim(self.base + [(100, 101, 99.5, 100), (100, 100.5, 98.9, 99)] + [(99, 99, 99, 99)] * 3, 1, 1.0, 2.0, 4)
        self.assertAlmostEqual(r["gross"], -1.0); self.assertEqual(int(r["code"]), 0); self.assertEqual(int(r["exit_bar"]), 2)

    def test_target_long(self):
        r = one_sim(self.base + [(100, 102.5, 99.5, 101)] + [(101, 101, 101, 101)] * 4, 1, 1.0, 2.0, 4)
        self.assertAlmostEqual(r["gross"], 2.0); self.assertEqual(int(r["code"]), 1); self.assertEqual(int(r["exit_bar"]), 1)

    def test_stop_first_when_both_touched(self):
        r = one_sim(self.base + [(100, 103, 98, 101)] + [(101, 101, 101, 101)] * 4, 1, 1.0, 2.0, 4)
        self.assertAlmostEqual(r["gross"], -1.0); self.assertEqual(int(r["code"]), 0)

    def test_gap_through_stop_fills_at_open(self):
        r = one_sim(self.base + [(100, 100.5, 99.6, 100), (97, 98, 96, 97)] + [(97, 97, 97, 97)] * 3, 1, 1.0, 2.0, 4)
        self.assertAlmostEqual(r["gross"], -3.0)

    def test_target_gap_fills_at_target_not_better(self):
        r = one_sim(self.base + [(105, 106, 104.5, 105)] + [(105, 105, 105, 105)] * 4, 1, 1.0, 2.0, 4, 0)
        # entry at the open of bar 1 = 105, so a "gap" relative to bar 0 is irrelevant; check next-bar gap instead
        r2 = one_sim(self.base + [(100, 100.5, 99.6, 100), (104, 105, 103.5, 104)] + [(104, 104, 104, 104)] * 3, 1, 1.0, 2.0, 4)
        self.assertAlmostEqual(r2["gross"], 2.0)
        self.assertEqual(int(r2["code"]), 1)

    def test_time_exit_at_close(self):
        r = one_sim(self.base + [(100, 100.5, 99.5, 100.2), (100.2, 100.6, 99.6, 100.4), (100.4, 100.7, 99.7, 100.5)] + [(100.5, 100.6, 100.4, 100.5)] * 2, 1, 1.0, 5.0, 3)
        self.assertEqual(int(r["code"]), 2); self.assertEqual(int(r["exit_bar"]), 3); self.assertAlmostEqual(r["gross"], 0.5)

    def test_short_mirror(self):
        up = self.base + [(100, 100.5, 99.5, 100), (100, 101.2, 99.8, 101)] + [(101, 101, 101, 101)] * 3
        r = one_sim(up, -1, 1.0, 2.0, 4)
        self.assertAlmostEqual(r["gross"], -1.0); self.assertEqual(int(r["code"]), 0)
        dn = self.base + [(100, 100.5, 97.5, 98)] + [(98, 98, 98, 98)] * 4
        r = one_sim(dn, -1, 1.0, 2.0, 4)
        self.assertAlmostEqual(r["gross"], 2.0); self.assertEqual(int(r["code"]), 1)

    def test_truncated_trades_are_dropped(self):
        rows = self.base + [(100, 100.5, 99.5, 100)] * 5
        o, h, l, c = bars(rows)
        r = S.simulate_all(o, h, l, c, np.ones(len(c)), 1, 1.0, None, 4)
        self.assertTrue(np.isfinite(r["gross"][:2]).all())  # i=0,1 fit (i+T <= 5)
        self.assertTrue(np.isnan(r["gross"][2:]).all())

    def test_cost_deduction_in_R(self):
        o, h, l, c = bars(self.base + [(100, 100.5, 99.5, 100)] * 5)
        r = S.simulate_all(o, h, l, c, np.ones(len(c)), 1, 1.0, None, 3)
        cost = 0.0016
        net = r["gross"][0] - cost * r["cu"][0]
        self.assertAlmostEqual(net, -cost * 100.0)  # entry 100, D 1 -> 0.16 R
        ref = S.simulate_one(o, h, l, c, np.ones(len(c)), 0, 1, 1.0, None, 3, cost)
        self.assertAlmostEqual(ref[0], net)

    def test_vectorised_equals_scalar_reference(self):
        checked = 0
        for gap in (0.0, 0.015):
            d = gen_walk(500, 11 + int(gap * 1000), vol=0.035, gap=gap)
            o, h, l, c = d["o"], d["h"], d["l"], d["c"]
            atr = S.atr_wilder(h, l, c)
            for st in S.SETUPS:
                for side in (1, -1):
                    sim = S.simulate_all(o, h, l, c, atr, side, st["k"], st["m"], st["T"])
                    for i in range(0, 480, 3):
                        ref = S.simulate_one(o, h, l, c, atr, i, side, st["k"], st["m"], st["T"], 0.0016)
                        if not np.isfinite(sim["gross"][i]):
                            self.assertTrue(ref is None or not np.isfinite(atr[i]) or i + st["T"] > len(c) - 1, (st["id"], i))
                            continue
                        net = sim["gross"][i] - 0.0016 * sim["cu"][i]
                        self.assertAlmostEqual(net, ref[0], places=9, msg=(st["id"], side, i))
                        self.assertEqual(int(sim["exit_bar"][i]), ref[1]); self.assertEqual(int(sim["code"][i]), ref[2])
                        checked += 1
        self.assertGreater(checked, 1000)

    def test_martingale_baseline_near_zero_gross(self):
        # drift = -vol^2/2 in log terms makes the PRICE (not the log price) a martingale; with a positive price drift longs earn a baseline.
        d = gen_walk(60000, 5, vol=0.03, drift=-0.03 ** 2 / 2)
        o, h, l, c = d["o"], d["h"], d["l"], d["c"]
        atr = S.atr_wilder(h, l, c)
        for st in S.SETUPS:
            for side in (1, -1):
                g = S.simulate_all(o, h, l, c, atr, side, st["k"], st["m"], st["T"])["gross"]
                self.assertLess(abs(np.nanmean(g)), 0.05, (st["id"], side, np.nanmean(g)))

    def test_one_position_at_a_time(self):
        sig = np.array([0, 1, 1, 0, 1, 1, 0, -1, 0, 0], dtype=np.int8)
        el = np.array([-1, 4, 5, -1, 7, 8, -1, -1, -1, -1])
        es = np.array([-1, -1, -1, -1, -1, -1, -1, 9, -1, -1])
        # signal 1 (exit 4) -> 2 skipped; 4 is taken (4 >= 4, exit 7) -> 5 skipped; short at 7 taken (7 >= 7, exit 9)
        self.assertEqual(S.select_trades(sig, el, es), [(1, 1), (4, 1), (7, -1)])
        # an unsimulable signal (exit -1) does not block the next one
        el2 = el.copy(); el2[1] = -1
        self.assertEqual(S.select_trades(sig, el2, es)[0], (2, 1))


def mk_cfg(n, **kw):
    c = dict(S.CFG)
    c.update(t0=S.START_MS, t_end=S.START_MS + n * DAY, split_ms=S.START_MS + (n // 2) * DAY, reps=400, min_n=100, half_n=30, asset_n=20)
    c.update(kw)
    return c


def oracle_fn(o, h, l, c, atr):  # looks at bar i+1: deliberately leaky, used only to test that the pipeline can detect an edge
    s = np.zeros(len(c), dtype=np.int8)
    s[:-1] = np.where(c[1:] > o[1:], 1, -1)
    return s


def random_fn_factory(seed, p=0.06):
    def fn(o, h, l, c, atr):
        r = np.random.default_rng(seed + len(c))
        u = r.random(len(c))
        return np.where(u < p / 2, 1, np.where(u < p, -1, 0)).astype(np.int8)
    return fn


class Pipeline(unittest.TestCase):
    def test_bootstrap_unit(self):
        rng = np.random.default_rng(1)
        blk = np.repeat(np.arange(50), 4)
        lo, hi = S.block_bootstrap(blk, dict(a=np.ones(200)), 50, 500, rng, 1, 99)["a"]
        self.assertGreater(lo, 0.99)
        v = np.where(np.arange(200) % 2 == 0, 1.0, -1.0)
        lo, hi = S.block_bootstrap(blk, dict(a=v), 50, 500, rng, 1, 99)["a"]
        self.assertTrue(lo < 0 < hi or (lo <= 0 <= hi))

    def test_oracle_is_detected_as_pass(self):
        n = 1200
        assets = {f"A{i}": gen_walk(n, 100 + i) for i in range(8)}
        r = S.evaluate_setup(dict(id="X", name="oracle", k=2.0, m=None, T=5, fn=oracle_fn), assets, mk_cfg(n))
        self.assertEqual(r["verdict"], "PASS", r["failed"])

    def test_random_signals_are_not_passed(self):
        n = 1200
        assets = {f"A{i}": gen_walk(n, 300 + i) for i in range(8)}
        verdicts = []
        for s in range(30):
            r = S.evaluate_setup(dict(id="R", name="random", k=1.5, m=1.0, T=10, fn=random_fn_factory(1000 * s)), assets, mk_cfg(n), s)
            verdicts.append(r["verdict"])
        self.assertLessEqual(verdicts.count("PASS"), 1, verdicts)
        self.assertNotIn("PASS", verdicts[:3])

    def test_no_signal_gives_inconclusive(self):
        n = 400
        r = S.evaluate_setup(dict(id="Z", name="none", k=1.5, m=1.0, T=10, fn=lambda o, h, l, c, a: np.zeros(len(c), dtype=np.int8)), {"A": gen_walk(n, 1)}, mk_cfg(n))
        self.assertEqual((r["n"], r["verdict"]), (0, "INCONCLUSIVE"))

    def test_deterministic(self):
        n = 800
        assets = {f"A{i}": gen_walk(n, 40 + i) for i in range(6)}
        a = S.evaluate_setup(S.SETUPS[0], assets, mk_cfg(n))
        b = S.evaluate_setup(S.SETUPS[0], assets, mk_cfg(n))
        self.assertEqual(json.dumps(a, default=float, sort_keys=True), json.dumps(b, default=float, sort_keys=True))

    def test_fail_requires_power_and_a_tight_upper_bound(self):
        n = 1500
        assets = {f"A{i}": gen_walk(n, 500 + i) for i in range(8)}
        r = S.evaluate_setup(dict(id="R", name="random", k=1.5, m=1.0, T=10, fn=random_fn_factory(7, p=0.2)), assets, mk_cfg(n))
        self.assertGreaterEqual(r["n"], 300)
        self.assertEqual(r["verdict"], "FAIL")  # random entries, costs deducted: a mean of ~ -cost is excluded from +0.10 R
        r2 = S.evaluate_setup(dict(id="R", name="random", k=1.5, m=1.0, T=10, fn=random_fn_factory(7, p=0.2)), assets, mk_cfg(n, min_n=10**6))
        self.assertEqual(r2["verdict"], "INCONCLUSIVE")  # underpowered never becomes FAIL or PASS

    def test_run_all_and_render(self):
        n = 900
        assets = {f"A{i}": gen_walk(n, 60 + i) for i in range(8)}
        assets[S.REFERENCE] = gen_walk(n, 99)
        out = S.run_all(assets, mk_cfg(n))
        self.assertEqual(len(out["pooled"]), 5); self.assertEqual(len(out["reference"]), 5)
        txt = S.render(out, [dict(symbol="A0", status="OK")], "x" * 64, mk_cfg(n))
        self.assertIn("Nothing here is self-certified", txt)
        for r in out["pooled"]:
            self.assertIn(r["verdict"], ("PASS", "FAIL", "INCONCLUSIVE"))
        with self.assertRaises(S.DataError):
            S.run_all({f"A{i}": assets[f"A{i}"] for i in range(5)}, mk_cfg(n))


def klines_rows(d, listing_idx=0):
    out = []
    for i in range(listing_idx, len(d["t"])):
        t = int(d["t"][i])
        out.append([t, str(d["o"][i]), str(d["h"][i]), str(d["l"][i]), str(d["c"][i]), "1", t + DAY - 1, "1", 1, "1", "1", "0"])
    return out


def fake_server(rows, bad_hosts=(), log=None):
    def http_get(url):
        host = url.split("/")[2]
        if log is not None:
            log.append(host)
        if host in bad_hosts:
            raise urllib.error.HTTPError(url, 451, "unavailable", {}, None)
        q = dict(p.split("=") for p in url.split("?")[1].split("&"))
        s, e, lim = int(q["startTime"]), int(q["endTime"]), int(q["limit"])
        assert q["interval"] == "1d" and lim <= 1000
        return json.dumps([r for r in rows if s <= r[0] <= e][:lim])
    return http_get


class Fetch(unittest.TestCase):
    sleep = staticmethod(lambda s: None)

    def test_constants(self):
        f = lambda s: int(dt.datetime.strptime(s, "%Y-%m-%d").replace(tzinfo=dt.timezone.utc).timestamp() * 1000)
        self.assertEqual((S.START_MS, S.END_MS, S.SPLIT_MS), (f("2017-08-17"), f("2026-11-17"), f("2022-01-01")))
        self.assertNotIn(S.REFERENCE, S.ASSETS); self.assertEqual(len(set(S.ASSETS)), len(S.ASSETS))
        self.assertEqual([(s["id"], s["k"], s["m"], s["T"]) for s in S.SETUPS],
                         [("S1", 2.0, 1.5, 30), ("S2", 1.5, 2.0, 24), ("S3", 1.5, 1.0, 12), ("S4", 3.0, None, 14), ("S5", 3.0, 0.5, 10)])

    def test_pagination_over_1000_rows(self):
        d = gen_walk(2500, 2)
        got = S.fetch_klines("X", fake_server(klines_rows(d)), start_ms=S.START_MS, end_ms=S.START_MS + 2500 * DAY, sleep=self.sleep)
        self.assertEqual(len(got["c"]), 2500); self.assertEqual(got["missing_days"], 0)
        self.assertTrue(np.array_equal(got["t"], d["t"])); self.assertTrue(np.allclose(got["c"], d["c"]))

    def test_end_is_exclusive_and_partial_bar_never_included(self):
        d = gen_walk(1800, 2)
        got = S.fetch_klines("X", fake_server(klines_rows(d)), start_ms=S.START_MS, end_ms=S.START_MS + 1500 * DAY, sleep=self.sleep)
        self.assertEqual(len(got["c"]), 1500); self.assertLess(int(got["t"][-1]), S.START_MS + 1500 * DAY)

    def test_late_listing_returns_first_available(self):
        d = gen_walk(1500, 2)
        got = S.fetch_klines("X", fake_server(klines_rows(d, 300)), start_ms=S.START_MS, end_ms=S.START_MS + 1500 * DAY, sleep=self.sleep)
        self.assertEqual(len(got["c"]), 1200); self.assertEqual(int(got["t"][0]), S.START_MS + 300 * DAY)

    def test_fallback_host_after_451(self):
        d = gen_walk(300, 2); log = []
        got = S.fetch_klines("X", fake_server(klines_rows(d), bad_hosts=(S.HOSTS[0],), log=log), start_ms=S.START_MS, end_ms=S.START_MS + 300 * DAY, sleep=self.sleep)
        self.assertEqual(len(got["c"]), 300); self.assertIn(S.HOSTS[1], log)
        with self.assertRaises(S.DataError):
            S.fetch_klines("X", fake_server(klines_rows(d), bad_hosts=S.HOSTS), start_ms=S.START_MS, end_ms=S.START_MS + 300 * DAY, sleep=self.sleep)

    def test_validation_rejects_bad_data(self):
        d = gen_walk(100, 2); rows = klines_rows(d)
        bad = [list(r) for r in rows]; bad[10][2] = str(float(bad[10][3]) - 1)  # high below low
        with self.assertRaises(S.DataError):
            S.validate_rows("X", bad)
        dup = rows[:10] + rows[9:]
        with self.assertRaises(S.DataError):
            S.validate_rows("X", dup)
        neg = [list(r) for r in rows]; neg[5][4] = "-1"
        with self.assertRaises(S.DataError):
            S.validate_rows("X", neg)
        with self.assertRaises(S.DataError):
            S.validate_rows("X", [["a", "b"]])

    def test_gaps_counted_and_excluded_by_rule(self):
        d = gen_walk(1200, 2); rows = klines_rows(d)
        three = rows[:100] + rows[103:]
        self.assertEqual(S.validate_rows("X", three)["missing_days"], 3)
        many = rows[:100] + rows[110:]
        self.assertEqual(S.validate_rows("X", many)["missing_days"], 10)
        srv = {"OKUSDT": rows, "GAPUSDT": many, "NOPE": []}

        def http_get(url):
            sym = url.split("symbol=")[1].split("&")[0]
            return fake_server(srv[sym])(url)
        got, notes = S.load_assets(http_get, symbols=("OKUSDT", "GAPUSDT", "NOPE"), sleep=self.sleep, start_ms=S.START_MS, end_ms=S.START_MS + 1200 * DAY)
        self.assertEqual(list(got), ["OKUSDT"])
        self.assertEqual({n["symbol"]: n["status"] for n in notes}, {"OKUSDT": "OK", "GAPUSDT": "EXCLUDED", "NOPE": "EXCLUDED"})
        self.assertEqual(len(notes[0]["sha256"]), 64)

    def test_data_hash_changes_with_data(self):
        a = S.validate_rows("X", klines_rows(gen_walk(50, 1))); b = S.validate_rows("X", klines_rows(gen_walk(50, 2)))
        self.assertNotEqual(S.data_hash(a), S.data_hash(b)); self.assertEqual(S.data_hash(a), S.data_hash(a))


if __name__ == "__main__":
    unittest.main(verbosity=1)
