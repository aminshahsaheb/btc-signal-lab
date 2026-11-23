#!/usr/bin/env python3
"""Synthetic tests for searchlab.py. Run: python -I -B research/search-lab/test_searchlab.py

Written by the same author as the code: they check that the code does what it says (causality, lag, cost, no leakage between the discovery and
confirmation stages, verdict logic, fetching) on constructed data. They are NOT evidence that any rule works and not an independent review.
No network is used: the fetcher is driven by a fake server."""
import datetime as dt
import json
import os
import sys
import unittest
import urllib.error

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import searchlab as S  # noqa: E402

DAY = S.DAY_MS


def make_datas(n_assets, T, seed, drift=0.0, vol=0.04, t0=S.START_MS, stagger=60):
    """Synthetic coins (log random walks, optional drift); coin a is listed `stagger*a` days late."""
    rng = np.random.default_rng(seed)
    out = {}
    for a in range(n_assets):
        n = T - stagger * a
        c = 100 * np.exp(np.cumsum(rng.normal(drift, vol, n)))
        o = np.r_[100.0, c[:-1]] * np.exp(rng.normal(0, 0.003, n))
        h = np.maximum(o, c) * (1 + np.abs(rng.normal(0, 0.01, n)))
        l = np.minimum(o, c) * (1 - np.abs(rng.normal(0, 0.01, n)))
        out[f"C{a:02d}"] = dict(t=t0 + DAY * (stagger * a + np.arange(n, dtype=np.int64)), o=o, h=h, l=l, c=c)
    return out


def prefix_panel(P, m):
    return S.prep(dict(names=P["names"], t=P["t"][:m], O=P["O"][:m], H=P["H"][:m], L=P["L"][:m], C=P["C"][:m]))


def small_cfg(T, t0=S.START_MS, **kw):
    c = dict(S.CFG, disc_lo_ms=t0 + 300 * DAY, split_ms=t0 + (T * 2 // 3) * DAY, reps=300, min_days=100, warmup_bars=100, min_active=3, t0=t0)
    c.update(kw)
    return c


class Variants(unittest.TestCase):
    def test_declared_set(self):
        self.assertEqual(len(S.VARIANTS), 97)
        self.assertEqual(len({v["id"] for v in S.VARIANTS}), 97)
        self.assertEqual(len({v["family"] for v in S.VARIANTS}), 11)

    def test_all_variants_causal(self):
        P = S.build_panel(make_datas(6, 900, 3), S.START_MS, S.START_MS + 900 * DAY)
        for v in S.VARIANTS:
            full = v["fn"](P)
            for m in (400, 555, 777):
                part = v["fn"](prefix_panel(P, m))
                k = m - 1  # the day-of-week rule looks one calendar day ahead by construction (the weekday is a calendar fact)
                self.assertTrue(np.array_equal(full[:k], part[:k]), (v["id"], m))

    def test_causality_check_catches_lookahead(self):
        P = S.build_panel(make_datas(4, 600, 5), S.START_MS, S.START_MS + 600 * DAY)

        def leaky(P_):
            C = P_["C"]
            pos = np.zeros(C.shape)
            pos[:-1] = np.where(C[1:] > C[:-1], 1.0, 0.0)
            return pos
        full = leaky(P)
        part = leaky(prefix_panel(P, 400))
        self.assertFalse(np.array_equal(full[:400], part[:400]))

    def test_donchian_enters_and_exits(self):
        T = 200
        c = np.full(T, 100.0)
        c[120:140] = np.linspace(101, 130, 20)
        c[140:] = 90.0
        d = {f"C{a}": dict(t=S.START_MS + DAY * np.arange(T, dtype=np.int64), o=c.copy(), h=c + 0.5, l=c - 0.5, c=c.copy()) for a in range(3)}
        P = S.build_panel(d, S.START_MS, S.START_MS + T * DAY)
        pos = S.f_donch(P, 20, 10, False)
        self.assertEqual(pos[119, 0], 0.0); self.assertEqual(pos[121, 0], 1.0); self.assertEqual(pos[139, 0], 1.0); self.assertEqual(pos[160, 0], 0.0)

    def test_volbo_holds_exactly_hold_bars(self):
        T = 400
        rng = np.random.default_rng(1)
        amp = np.where(np.arange(T) < 200, 3.0, 0.1)
        c = 100 + amp * rng.normal(0, 1, T) * 0.3
        c[300:] += 5.0
        d = {f"C{a}": dict(t=S.START_MS + DAY * np.arange(T, dtype=np.int64), o=c.copy(), h=c + amp, l=c - amp, c=c.copy()) for a in range(3)}
        P = S.build_panel(d, S.START_MS, S.START_MS + T * DAY)
        pos = S.f_volbo(P, 7, False)[:, 0]
        runs = np.flatnonzero(np.diff(np.r_[0, (pos > 0).astype(int), 0]) == -1) - np.flatnonzero(np.diff(np.r_[0, (pos > 0).astype(int), 0]) == 1)
        self.assertTrue(len(runs) >= 1 and all(r % 7 == 0 for r in runs))

    def test_cross_sectional_momentum_picks_the_leaders(self):
        T = 120
        t = S.START_MS + DAY * np.arange(T, dtype=np.int64)
        d = {}
        for a in range(9):
            c = 100 * (1 + 0.01 * (a - 4)) ** np.arange(T)  # coin 8 rises fastest, coin 0 falls fastest
            d[f"C{a}"] = dict(t=t, o=c.copy(), h=c * 1.001, l=c * 0.999, c=c.copy())
        P = S.build_panel(d, S.START_MS, S.START_MS + T * DAY, dict(S.CFG, warmup_bars=5))
        pos = S.f_csmom(P, 14, True)
        row = pos[70]
        self.assertTrue((row[6:] == 1).all() and (row[:3] == -1).all() and (row[3:6] == 0).all())

    def test_day_of_week_mapping(self):
        t0 = 1_672_531_200_000  # 2023-01-01, a Sunday
        d = {f"C{a}": dict(t=t0 + DAY * np.arange(30, dtype=np.int64), o=np.full(30, 100.0), h=np.full(30, 101.0), l=np.full(30, 99.0), c=np.full(30, 100.0)) for a in range(3)}
        P = S.build_panel(d, t0, t0 + 30 * DAY)
        mon = S.f_dow(P, 0)[:, 0]
        self.assertEqual(list(mon[:8]), [1, 0, 0, 0, 0, 0, 0, 1])  # decided on Sunday, held on Monday
        wk = S.f_dow(P, "WK")[:, 0]
        self.assertEqual(list(wk[:7]), [1, 1, 1, 1, 1, 0, 0])  # decided Sun..Thu close -> held Mon..Fri; Fri and Sat closes -> weekend, flat


class Engine(unittest.TestCase):
    def setUp(self):
        T = 60
        rng = np.random.default_rng(2)
        self.cfg = dict(S.CFG, target_vol=1e9, warmup_bars=0, min_active=1)
        c = 100 * np.exp(np.cumsum(rng.normal(0, 0.02, T)))
        o = np.r_[100.0, c[:-1]]
        self.d = {"A": dict(t=S.START_MS + DAY * np.arange(T, dtype=np.int64), o=o, h=np.maximum(o, c) * 1.01, l=np.minimum(o, c) * 0.99, c=c)}
        self.P = S.build_panel(self.d, S.START_MS, S.START_MS + T * DAY, self.cfg)
        self.T = T

    def test_lag_and_cost(self):
        i0 = 45  # (volatility needs a 30-day window before the scale is non-zero)
        pos = np.zeros((self.T, 1)); pos[i0, 0] = 1.0  # decided at the close of bar i0 -> held in bar i0+1
        R = S.portfolio_returns(self.P, pos, 0.001, self.cfg)
        o = self.P["O"][:, 0]
        self.assertAlmostEqual(R[i0 + 1], (o[i0 + 2] / o[i0 + 1] - 1) - 0.001)  # earns the open-to-open return of the NEXT bar, pays entry cost
        self.assertAlmostEqual(R[i0 + 2], -0.001)  # flat again: exit cost only
        self.assertAlmostEqual(R[i0], 0.0)
        self.assertAlmostEqual(R[i0 + 8], 0.0)

    def test_scale_caps_at_one_and_shrinks_with_vol(self):
        cfg = dict(S.CFG, warmup_bars=0, min_active=1, target_vol=0.2)
        P = S.build_panel(self.d, S.START_MS, S.START_MS + self.T * DAY, cfg)
        sc = P["scale"][40:, 0]
        self.assertTrue((sc <= 1.0).all() and (sc > 0).all() and (sc < 1.0).any())

    def test_inactive_coins_and_thin_days(self):
        d = make_datas(4, 500, 9, stagger=100)
        P = S.build_panel(d, S.START_MS, S.START_MS + 500 * DAY, dict(S.CFG, warmup_bars=50))
        R = S.portfolio_returns(P, np.ones_like(P["C"]), 0.0)
        n_active = (np.vstack([np.zeros((1, 4), bool), P["ready"][:-1]]) & np.isfinite(P["ropen"])).sum(1)
        self.assertTrue(np.isnan(R[n_active < 3]).all() and np.isfinite(R[n_active >= 3]).all())

    def test_long_only_equals_benchmark(self):
        P = S.build_panel(make_datas(5, 700, 4), S.START_MS, S.START_MS + 700 * DAY)
        R = S.portfolio_returns(P, np.ones_like(P["C"]), 0.0)
        sc = np.vstack([np.zeros((1, 5)), P["scale"][:-1]])
        act = np.vstack([np.zeros((1, 5), bool), P["ready"][:-1]]) & np.isfinite(P["ropen"])
        j = 650
        want = np.where(act[j], sc[j] * P["ropen"][j], 0.0).sum() / act[j].sum()
        self.assertAlmostEqual(R[j], want)

    def test_no_leakage_between_stages(self):
        T, cut = 900, 800
        datas = make_datas(6, T, 11)
        Pf = S.build_panel(datas, S.START_MS, S.START_MS + T * DAY)
        Pt = S.build_panel({k: {kk: (v[kk][v["t"] < S.START_MS + cut * DAY]) for kk in ("t", "o", "h", "l", "c")} for k, v in datas.items()}, S.START_MS, S.START_MS + cut * DAY)
        for v in S.VARIANTS:
            a = S.portfolio_returns(Pf, v["fn"](Pf), 0.0008)[: cut - 1]
            b = S.portfolio_returns(Pt, v["fn"](Pt), 0.0008)[: cut - 1]
            self.assertTrue(np.allclose(a, b, equal_nan=True, atol=1e-12), v["id"])


class Stats(unittest.TestCase):
    def test_dsr(self):
        trials = np.random.default_rng(1).normal(0, 0.03, 97)
        self.assertTrue(np.isnan(S.deflated_sharpe(0.1, 1000, 0, 3, np.array([0.1]))))
        hi = S.deflated_sharpe(0.12, 1000, 0, 3, trials)
        self.assertGreater(hi, 0.95)
        self.assertLess(S.deflated_sharpe(0.0, 1000, 0, 3, trials), 0.5)
        more = np.random.default_rng(1).normal(0, 0.03, 5000)
        self.assertLess(S.deflated_sharpe(0.08, 1000, 0, 3, more), S.deflated_sharpe(0.08, 1000, 0, 3, trials[:10]))

    def test_block_bootstrap_bounds(self):
        rng = np.random.default_rng(3)
        noise = rng.normal(0, 0.02, 1500)
        lo, hi = S.block_sharpe_bounds(noise, 30, 2000, rng, 1.667, 98.333)
        self.assertTrue(lo < 0 < hi)
        lo2, hi2 = S.block_sharpe_bounds(noise + 0.01, 30, 2000, rng, 1.667, 98.333)
        self.assertGreater(lo2, 0)

    def test_sharpe_and_drawdown(self):
        x = np.array([0.01, -0.01, 0.02, -0.02, 0.0])
        self.assertAlmostEqual(S.sharpe(x), x.mean() / x.std(ddof=1) * math_sqrt365())
        self.assertAlmostEqual(S.max_drawdown(np.array([0.1, -0.5, 0.1])), 0.5)


def math_sqrt365():
    return 365 ** 0.5


class Pipeline(unittest.TestCase):
    def test_selection_is_mechanical_and_distinct_families(self):
        P = S.build_panel(make_datas(6, 900, 21), S.START_MS, S.START_MS + 900 * DAY)
        cfg = small_cfg(900, split_ms=S.START_MS + 900 * DAY)
        a, b = S.discover(P, cfg), S.discover(P, cfg)
        self.assertEqual(a["selected"], b["selected"])
        self.assertEqual(len(a["selected"]), 3)
        self.assertEqual(len({s.split(":")[0] for s in a["selected"]}), 3)
        top = a["rows"][0]
        self.assertEqual(a["selected"][0], top["id"])
        self.assertEqual(a["n_variants"], 97)

    def test_reference_candidate_is_always_confirmed_and_never_duplicated(self):
        P = S.build_panel(make_datas(6, 900, 21), S.START_MS, S.START_MS + 900 * DAY)
        cfg = small_cfg(900, split_ms=S.START_MS + 900 * DAY)
        d = S.discover(P, cfg)
        self.assertIn("ENSEMBLE:DONCH5LF", d["candidates"])
        self.assertEqual(len(d["candidates"]), len(set(d["candidates"])))
        self.assertEqual(d["candidates"][: len(d["selected"])], d["selected"])
        self.assertLessEqual(len(d["candidates"]), cfg["k_select"] + 1)
        d2 = S.discover(P, dict(cfg, ref_id="NO_SUCH_ID"))
        self.assertEqual(d2["candidates"], d2["selected"])

    def test_bonferroni_percentiles_match_k_plus_one(self):
        k = S.CFG["k_select"] + 1
        self.assertAlmostEqual(S.CFG["lo_pct"], 100 * 0.05 / k, places=6)
        self.assertAlmostEqual(S.CFG["hi_pct"], 100 - 100 * 0.05 / k, places=6)

    def test_oracle_is_confirmed_and_random_selection_is_not(self):
        T = 1200
        cfg = small_cfg(T)
        Pn = S.build_panel(make_datas(9, T, 31, stagger=20), S.START_MS, S.START_MS + T * DAY)
        Po = S.build_panel(make_datas(8, T, 32, stagger=20), S.START_MS, S.START_MS + T * DAY)

        def oracle(P):  # peeks at the next bar's open-to-open return: leaky on purpose, only to prove the verdict logic can say PASS
            ro = P["ropen"]
            pos = np.zeros(ro.shape)
            pos[:-1] = np.where(ro[1:] > 0, 1.0, 0.0)
            return pos
        res = S.confirm(["ORACLE"], Pn, Po, cfg, variants=[dict(id="ORACLE", family="X", fn=oracle)])[0]
        self.assertEqual(res["verdict"], "PASS", res["failed"])

    def test_false_pass_rate_after_best_of_97_selection(self):
        T, passes = 1300, 0
        for seed in range(12):
            cfg = small_cfg(T)
            Pold_pre = S.build_panel({k: {kk: v[kk][v["t"] < cfg["split_ms"]] for kk in ("t", "o", "h", "l", "c")} for k, v in make_datas(8, T, 100 + seed, drift=0.0004, stagger=20).items()},
                                     S.START_MS, cfg["split_ms"])
            disc = S.discover(Pold_pre, cfg)
            Pn = S.build_panel(make_datas(9, T, 500 + seed, drift=0.0004, stagger=20), S.START_MS, S.START_MS + T * DAY)
            Po = S.build_panel(make_datas(8, T, 100 + seed, drift=0.0004, stagger=20), S.START_MS, S.START_MS + T * DAY)
            out = S.confirm(disc["selected"], Pn, Po, cfg, seed_offset=seed)
            passes += sum(r["verdict"] == "PASS" for r in out)
        self.assertLessEqual(passes, 1, passes)

    def test_fail_needs_power_and_tight_bound(self):
        T = 1500
        cfg = small_cfg(T)
        Pn = S.build_panel(make_datas(9, T, 41, stagger=20), S.START_MS, S.START_MS + T * DAY)
        Po = S.build_panel(make_datas(8, T, 42, stagger=20), S.START_MS, S.START_MS + T * DAY)
        short = [dict(id="SHORT", family="X", fn=lambda P: -np.ones(P["C"].shape))]
        r = S.confirm(["SHORT"], Pn, Po, cfg, variants=short)[0]
        self.assertIn(r["verdict"], ("FAIL", "INCONCLUSIVE"))
        r2 = S.confirm(["SHORT"], Pn, Po, dict(cfg, min_days=10 ** 6), variants=short)[0]
        self.assertEqual(r2["verdict"], "INCONCLUSIVE")

    def test_render(self):
        T = 900
        cfg = small_cfg(T)
        P = S.build_panel(make_datas(6, T, 51), S.START_MS, S.START_MS + T * DAY)
        disc = S.discover(P, cfg)
        conf = S.confirm(disc["candidates"], P, P, cfg)
        txt = S.render(disc, conf, [dict(symbol="A", status="OK")], [dict(symbol="B", status="OK")], "x" * 64, cfg)
        self.assertIn("Nothing here is self-certified", txt)
        self.assertIn("Stage 2", txt)


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
        self.assertEqual((S.START_MS, S.DISC_START_MS, S.SPLIT_MS, S.WARMUP_END_MS, S.END_MS),
                         (f("2017-08-17"), f("2018-06-01"), f("2023-01-01"), f("2022-04-30"), f("2026-11-17")))
        self.assertFalse(set(S.OLD) & set(S.NEW)); self.assertEqual((len(S.OLD), len(S.NEW)), (10, 15))
        self.assertNotIn("BTCUSDT", S.OLD + S.NEW)

    def test_pagination_and_end_exclusive(self):
        d = make_datas(1, 2500, 2)["C00"]
        got = S.fetch_klines("X", fake_server(klines_rows(d)), start_ms=S.START_MS, end_ms=S.START_MS + 2200 * DAY, sleep=self.sleep)
        self.assertEqual(len(got["c"]), 2200); self.assertLess(int(got["t"][-1]), S.START_MS + 2200 * DAY)

    def test_fallback_host(self):
        d = make_datas(1, 300, 2)["C00"]; log = []
        got = S.fetch_klines("X", fake_server(klines_rows(d), bad_hosts=(S.HOSTS[0],), log=log), start_ms=S.START_MS, end_ms=S.START_MS + 300 * DAY, sleep=self.sleep)
        self.assertEqual(len(got["c"]), 300); self.assertIn(S.HOSTS[1], log)
        with self.assertRaises(S.DataError):
            S.fetch_klines("X", fake_server(klines_rows(d), bad_hosts=S.HOSTS), start_ms=S.START_MS, end_ms=S.START_MS + 300 * DAY, sleep=self.sleep)

    def test_validation_and_exclusions(self):
        d = make_datas(1, 1200, 2)["C00"]; rows = klines_rows(d)
        bad = [list(r) for r in rows]; bad[10][2] = str(float(bad[10][3]) - 1)
        with self.assertRaises(S.DataError):
            S.validate_rows("X", bad)
        with self.assertRaises(S.DataError):
            S.validate_rows("X", rows[:10] + rows[9:])
        self.assertEqual(S.validate_rows("X", rows[:100] + rows[103:])["missing_days"], 3)
        srv = {"OK": rows, "GAP": rows[:100] + rows[110:], "LATE": klines_rows(d, 900), "EMPTY": []}

        def http_get(url):
            return fake_server(srv[url.split("symbol=")[1].split("&")[0]])(url)
        end = S.START_MS + 1200 * DAY
        got, notes = S.load_assets(("OK", "GAP", "LATE", "EMPTY"), end, http_get=http_get, sleep=self.sleep, min_bars=100, need_by_ms=S.START_MS + 500 * DAY)
        self.assertEqual(list(got), ["OK"])
        self.assertEqual({n["symbol"]: n["status"] for n in notes}, {"OK": "OK", "GAP": "EXCLUDED", "LATE": "EXCLUDED", "EMPTY": "EXCLUDED"})


if __name__ == "__main__":
    unittest.main(verbosity=1)
