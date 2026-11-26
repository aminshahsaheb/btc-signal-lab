#!/usr/bin/env python3
"""Synthetic tests for zeropip_v2.py (the v1 tests, adapted where the ingest policy changed, plus tests of the new ingest policy).
Run: python -I -B research/zero-pip-lab/test_zeropip_v2.py

Written by the same author as the code: they check that the code does what it says (causality of every feature, the bracket outcome
mechanics against a brute-force reference, the mirror used for shorts, no use of the holdout by the discovery stage, the verdict logic
including the lift over the all-free-hours policy, fetching and validation) on constructed data. They are NOT evidence that any pattern works and not an independent review.
No network is used: the fetcher is driven by a fake server."""
import ast
import contextlib
import hashlib
import io
import json
import os
import sys
import tempfile
import unittest
import unittest.mock
import urllib.error
from pathlib import Path

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import zeropip as Z1  # noqa: E402  (the frozen v1 code, only used to compare)
import zeropip_v2 as Z  # noqa: E402

H = Z.HOUR_MS
ARR = ("o", "h", "l", "c", "v", "tb", "ref_o", "ref_c")


def make_series(n, seed, split_frac=None, drift=0.0, vol=0.004, p0=20000.0, gaps=(), hour_drift=None, symbol="SYN"):
    """Random-walk hourly bars. split_frac puts the 2023-01-01 boundary at that fraction of the series.
    hour_drift = {hour_of_day: drift per bar} plants a drift on bars that START in those hours."""
    rng = np.random.default_rng(seed)
    t0 = (Z.SPLIT_MS - int(n * split_frac) * H) if split_frac is not None else Z.START_MS + 4 * H
    t = t0 + H * np.arange(n, dtype=np.int64)
    r = rng.normal(drift, vol, n)
    if hour_drift:
        hrs = (t // H) % 24
        for hr, d in hour_drift.items():
            r = r + np.where(hrs == hr, d, 0.0)
    c = p0 * np.exp(np.cumsum(r))
    o = np.r_[p0, c[:-1]]
    hi = np.maximum(o, c) * (1 + np.abs(rng.normal(0, vol / 2, n)))
    lo = np.minimum(o, c) * (1 - np.abs(rng.normal(0, vol / 2, n)))
    v = 100.0 * (1 + np.abs(rng.normal(0, 0.5, n)))
    tb = v * rng.uniform(0.3, 0.7, n)
    S = dict(symbol=symbol, t=t, o=o, h=hi, l=lo, c=c, v=v, tb=tb, ref_o=o.copy(), ref_c=c.copy(), bars=n, missing=0, mirrored=False)
    for g in gaps:
        for k in ARR:
            S[k][g] = np.nan
    S["missing"] = len(gaps)
    return S


def truncate(S, m):
    T = dict(S)
    T["t"] = S["t"][:m]
    for k in ARR:
        T[k] = S[k][:m]
    return T


def same(a, b):
    return np.allclose(np.asarray(a, dtype=float), np.asarray(b, dtype=float), rtol=1e-12, atol=1e-12, equal_nan=True)


def brute_atr(S, n=14):
    N = len(S["c"])
    tr = np.full(N, np.nan)
    for i in range(1, N):
        tr[i] = np.max([S["h"][i] - S["l"][i], abs(S["h"][i] - S["c"][i - 1]), abs(S["l"][i] - S["c"][i - 1])])  # NaN propagates
    out = np.full(N, np.nan)
    for i in range(n - 1, N):
        w = tr[i - n + 1:i + 1]
        out[i] = w.mean()  # NaN if any NaN
    return out


def brute_outcome(S, i, a_mult, k, h, atr14, short=False):
    """reference bracket outcome written as a plain loop; short=True works directly on the original series (no mirror)"""
    n = len(S["c"])
    if i + 1 >= n or not (atr14[i] > 0):
        return None
    e = i + 1
    entry = S["o"][e]
    sd = a_mult * atr14[i]
    if np.isnan(entry) or not sd > 0:
        return None
    mae = 0.0
    if e + h - 1 >= n or np.isnan(S["l"][e:e + h]).any() or np.isnan(S["h"][e:e + h]).any():
        return None  # validity needs the whole window, whatever the outcome
    for b in range(e, e + h):
        adverse = (S["h"][b] - entry) / sd if short else (entry - S["l"][b]) / sd
        mae = max(mae, adverse)
        stop_hit = S["h"][b] >= entry + sd if short else S["l"][b] <= entry - sd
        tp_hit = S["l"][b] <= entry - k * sd if short else S["h"][b] >= entry + k * sd
        if stop_hit:
            return (2, -1.0, b, mae, sd)
        if tp_hit:
            return (1, k, b, mae, sd)
    b = e + h - 1
    pnl = (entry - S["c"][b]) / sd if short else (S["c"][b] - entry) / sd
    return (3, pnl, b, mae, sd)


def flat_series(n=80, price=100.0, half=0.5):
    """every bar has range 1 and closes where it opened: ATR14 = 1 for every bar from index 14"""
    t = Z.START_MS + 4 * H + H * np.arange(n, dtype=np.int64)
    o = np.full(n, price)
    S = dict(symbol="FLAT", t=t, o=o.copy(), h=o + half, l=o - half, c=o.copy(), v=np.full(n, 100.0), tb=np.full(n, 50.0),
             ref_o=o.copy(), ref_c=o.copy(), bars=n, missing=0, mirrored=False)
    return S


def set_bar(S, i, o, h, l, c):
    S["o"][i], S["h"][i], S["l"][i], S["c"][i] = o, h, l, c
    S["ref_o"][i], S["ref_c"][i] = o, c


class Outcomes(unittest.TestCase):
    def test_atr_matches_brute_force_with_gap(self):
        S = make_series(300, 1, gaps=(100,))
        mine, ref = Z.atr(S, 14), brute_atr(S, 14)
        self.assertTrue(same(mine, ref))
        self.assertTrue(np.isnan(mine[100]) and np.isnan(mine[101]) and np.isnan(mine[113]) and not np.isnan(mine[115]))

    def test_matches_brute_force_long_and_short(self):
        S = make_series(900, 7, gaps=(200, 555))
        a = brute_atr(S)
        for am, k, h in ((0.5, 2.0, 12), (1.0, 3.0, 24), (2.0, 3.0, 24), (1.0, 2.0, 12)):
            for short, view in ((False, S), (True, Z.mirror(S))):
                out = Z.outcomes(view, am, k, h, 0.001)
                for i in range(len(S["c"])):
                    ref = brute_outcome(S, i, am, k, h, a, short=short)
                    if ref is None:
                        self.assertEqual(out["res"][i], 0, (am, k, h, short, i))
                        continue
                    res, gross, eb, mae, sd = ref
                    self.assertEqual(out["res"][i], res, (am, k, h, short, i))
                    self.assertAlmostEqual(out["gross"][i], gross, 9)
                    self.assertEqual(out["exit_bar"][i], eb)
                    self.assertAlmostEqual(out["mae"][i], mae, 9)
                    self.assertAlmostEqual(out["net"][i], gross - 0.001 * S["o"][i + 1] / sd, 9)  # cost is on the ORIGINAL price

    def test_handmade_bracket_cases(self):
        S = flat_series()
        i = 40
        # entry at the open of bar 41 = 100, stop distance 1 (a_mult 1, ATR 1): stop 99, take profit 103 (k=3)
        set_bar(S, 41, 100.0, 100.2, 99.9, 100.1)   # mae 0.1
        set_bar(S, 42, 100.1, 103.2, 100.0, 103.0)  # take profit; the bar's own low (100.0) is not adverse
        out = Z.outcomes(S, 1.0, 3.0, 24, 0.0)
        self.assertEqual((out["res"][i], out["exit_bar"][i]), (1, 42))
        self.assertAlmostEqual(out["gross"][i], 3.0)
        self.assertAlmostEqual(out["mae"][i], 0.1)
        self.assertTrue(out["clean"][i])
        # an adverse excursion of 0.4 stops it being clean
        set_bar(S, 41, 100.0, 100.2, 99.6, 100.1)
        out = Z.outcomes(S, 1.0, 3.0, 24, 0.0)
        self.assertEqual(out["res"][i], 1)
        self.assertAlmostEqual(out["mae"][i], 0.4)
        self.assertFalse(out["clean"][i])
        # stop and target inside the same bar: the stop is assumed first
        set_bar(S, 41, 100.0, 103.5, 98.5, 101.0)
        out = Z.outcomes(S, 1.0, 3.0, 24, 0.0)
        self.assertEqual((out["res"][i], out["gross"][i], out["exit_bar"][i]), (2, -1.0, 41))
        # nothing happens for h bars: timeout at the close of bar i+h
        S2 = flat_series()
        set_bar(S2, 41, 100.0, 100.4, 99.8, 100.3)
        out = Z.outcomes(S2, 1.0, 3.0, 12, 0.0)
        self.assertEqual((out["res"][i], out["exit_bar"][i]), (3, i + 12))
        self.assertAlmostEqual(out["gross"][i], 0.0)
        # cost in R: round trip 0.1% of price 100 = 0.1 price units = 0.1 R when the stop distance is 1
        out = Z.outcomes(S2, 1.0, 3.0, 12, 0.001)
        self.assertAlmostEqual(out["net"][i], -0.1, 9)
        # a stop half as wide doubles the cost in R
        out = Z.outcomes(S2, 0.5, 3.0, 12, 0.001)
        self.assertAlmostEqual(out["net"][i] - out["gross"][i], -0.2, 9)

    def test_entry_is_next_open_and_the_future_is_not_read(self):
        S = make_series(500, 3)
        a = Z.outcomes(S, 1.0, 3.0, 24, 0.001)
        T = dict(S)
        for k in ARR:
            T[k] = S[k].copy()
        m = 300
        rng = np.random.default_rng(5)
        for k in ARR[:4]:
            T[k][m:] = S[k][m:] * rng.uniform(0.5, 1.5, len(S[k]) - m)
        b = Z.outcomes(T, 1.0, 3.0, 24, 0.001)
        for i in range(0, m - 24 - 1):
            for key in ("res", "gross", "net", "mae", "exit_bar"):
                self.assertTrue(same(a[key][i:i + 1], b[key][i:i + 1]), (key, i))

    def test_nesting_properties(self):
        """a win at 3 stops is also a win at 2 stops; a win within 12 bars is also a win within 24; clean implies win"""
        S = make_series(4000, 11)
        w = lambda am, k, h: Z.outcomes(S, am, k, h, 0.0)["res"] == 1  # noqa: E731
        ok24 = Z.outcomes(S, 1.0, 3.0, 24, 0.0)["res"] > 0  # the last 24 bars have no full window; compare where both are defined
        for am in (0.5, 1.0, 2.0):
            self.assertTrue(np.all(w(am, 3.0, 24) <= w(am, 2.0, 24)))
            self.assertTrue(np.all((w(am, 3.0, 12) <= w(am, 3.0, 24))[ok24]))
        out = Z.outcomes(S, 1.0, 3.0, 24, 0.0)
        self.assertTrue(np.all(out["clean"] <= (out["res"] == 1)))

    def test_mirror_is_an_involution_of_prices(self):
        S = make_series(200, 2)
        M = Z.mirror(Z.mirror(S))
        for k in ("o", "h", "l", "c", "tb"):
            self.assertTrue(np.allclose(M[k], S[k]))
        self.assertTrue(np.all(Z.mirror(S)["h"] >= Z.mirror(S)["l"]))
        self.assertTrue(same(Z.atr(Z.mirror(S)), Z.atr(S)))


class Features(unittest.TestCase):
    def test_every_feature_is_causal(self):
        S = make_series(1500, 4, gaps=(700,))
        for view in (S, Z.mirror(S)):
            full = Z.features(view)
            for m in (600, 701, 905, 1234):
                part = Z.features(truncate(view, m))
                for name in Z.CONT + Z.BOOLS:
                    self.assertTrue(same(full[name][:m], part[name]), (name, m, view["mirrored"]))

    def test_known_values(self):
        S = make_series(900, 9)
        F = Z.features(S)
        a = brute_atr(S)
        i = 700
        self.assertAlmostEqual(F["dlow24"][i], (S["c"][i] - S["l"][i - 23:i + 1].min()) / a[i], 9)
        self.assertAlmostEqual(F["dlow480"][i], (S["c"][i] - S["l"][i - 479:i + 1].min()) / a[i], 9)
        self.assertAlmostEqual(F["ret6"][i], (S["c"][i] - S["c"][i - 6]) / a[i], 9)
        self.assertAlmostEqual(F["lowwick"][i], (min(S["o"][i], S["c"][i]) - S["l"][i]) / (S["h"][i] - S["l"][i]), 9)
        self.assertAlmostEqual(F["volratio"][i], S["v"][i] / S["v"][i - 24:i].mean(), 9)
        self.assertAlmostEqual(F["tbr24"][i], S["tb"][i - 23:i + 1].sum() / S["v"][i - 23:i + 1].sum(), 9)
        p = S["c"][i]
        lvl = 10 ** (np.floor(np.log10(p)) - 1)
        self.assertAlmostEqual(F["rounddist"][i], abs(p - round(p / lvl) * lvl) / a[i], 9)
        # time flags describe the hour that OPENS after the decision bar (t+1h)
        hr = ((S["t"][i] + H) // H) % 24
        self.assertEqual((F["s_asia"][i], F["s_eu"][i], F["s_us"][i]), (float(hr < 8), float(8 <= hr < 16), float(hr >= 16)))
        self.assertEqual(float(np.sum([F["s_asia"][i], F["s_eu"][i], F["s_us"][i]])), 1.0)

    def test_downrun_counts_and_resets(self):
        S = flat_series(60)
        for j in (30, 31, 32):
            set_bar(S, j, 100.0, 100.5, 99.5, 99.8)  # down closes
        F = Z.features(S)
        self.assertEqual([F["downrun"][j] for j in (29, 30, 31, 32, 33)], [0.0, 1.0, 2.0, 3.0, 0.0])

    def test_sweep_and_reclaim(self):
        S = flat_series(300)
        set_bar(S, 250, 100.0, 100.4, 98.0, 100.2)  # takes out the 24-bar low (99.5) and closes back above it
        set_bar(S, 251, 100.0, 100.4, 98.0, 98.5)   # takes it out and closes below: no reclaim
        F = Z.features(S)
        self.assertEqual(F["sweep24"][250], 1.0)
        self.assertEqual(F["sweep24"][251], 0.0)
        self.assertEqual(F["sweep24"][249], 0.0)

    def test_mirror_features_are_the_short_view(self):
        S = make_series(900, 6)
        M = Z.mirror(S)
        F, G = Z.features(S), Z.features(M)
        a = brute_atr(S)
        i = 650
        self.assertAlmostEqual(G["dlow24"][i], (S["h"][i - 23:i + 1].max() - S["c"][i]) / a[i], 9)  # distance below the 24h HIGH
        self.assertAlmostEqual(G["lowwick"][i], (S["h"][i] - max(S["o"][i], S["c"][i])) / (S["h"][i] - S["l"][i]), 9)  # upper wick
        self.assertAlmostEqual(G["tbr"][i], 1.0 - F["tbr"][i], 9)
        self.assertAlmostEqual(G["ret6"][i], -F["ret6"][i], 9)
        self.assertAlmostEqual(G["rounddist"][i], F["rounddist"][i], 9)
        self.assertTrue(same(G["s_asia"], F["s_asia"]))

    def test_declared_family_size(self):
        singles, pairs = Z.rule_list()
        self.assertEqual((len(singles), len(pairs)), (34, 547))
        self.assertEqual(len(set(singles + pairs)), 34 + 547)
        self.assertTrue(all(Z.base_feature(p.split(" & ")[0]) != Z.base_feature(p.split(" & ")[1]) for p in pairs))


class Stats(unittest.TestCase):
    def test_sequential_policy_never_overlaps(self):
        S = make_series(3000, 12)
        out = Z.outcomes(S, 1.0, 3.0, 24, 0.001)
        sig = (np.arange(3000) % 3 == 0)
        idx = Z.sequential_trades(sig, out)
        self.assertGreater(len(idx), 20)
        for a, b in zip(idx[:-1], idx[1:]):
            self.assertGreaterEqual(b, out["exit_bar"][a])
        # and it is greedy: nothing eligible was skipped
        taken = set(idx.tolist())
        free = -1
        for i in np.flatnonzero(sig & (out["res"] > 0)):
            if i >= free:
                self.assertIn(int(i), taken)
                free = out["exit_bar"][i]

    def test_bootstrap_interval_contains_the_mean_and_shrinks(self):
        rng = np.random.default_rng(1)
        wk = np.repeat(np.arange(300), 4)
        x = rng.normal(0.2, 1.0, len(wk))
        lo, hi = Z.boot_ci([(x, wk)], dict(Z.CFG, boot_b=500))
        self.assertLess(lo, x.mean())
        self.assertGreater(hi, x.mean())
        lo2, hi2 = Z.boot_ci([(np.tile(x, 4), np.tile(wk, 4))], dict(Z.CFG, boot_b=500))
        self.assertLess(hi2 - lo2, hi - lo + 0.05)
        self.assertEqual(Z.boot_ci([]), (None, None))

    def test_year_and_week_helpers(self):
        t = np.array([Z.SPLIT_MS - H, Z.SPLIT_MS, Z.SPLIT_MS + 400 * Z.DAY_MS])
        self.assertEqual(Z.year_of(t).tolist(), [2022, 2023, 2024])

    def test_costs_scale_with_the_stop(self):
        S = make_series(1500, 13)
        net = lambda am: Z.outcomes(S, am, 3.0, 24, 0.001)  # noqa: E731
        a, b = net(0.5), net(2.0)
        m = (a["res"] > 0)
        self.assertTrue(np.allclose((a["gross"] - a["net"])[m] / (b["gross"] - b["net"])[m], 4.0))


def small_cfg(**kw):
    c = dict(Z.CFG, n_min=120, boot_b=200, warmup=480, min_weeks=10)
    c.update(kw)
    return c


def easy_cfg(**kw):
    """verdict thresholds lowered so that small synthetic samples reach the H1-H3 logic (a PASS becomes EASIER, never harder)"""
    return small_cfg(min_trades_btc=30, min_trades_others=60, min_year_trades=3, years_needed=1, **kw)


class Study(unittest.TestCase):
    def test_discovery_never_reads_the_holdout(self):
        cfg = small_cfg()
        A = make_series(9000, 21, split_frac=0.7)
        B = make_series(9000, 21, split_frac=0.7)
        sp = int(np.searchsorted(B["t"], Z.SPLIT_MS))
        rng = np.random.default_rng(99)
        for k in ("o", "h", "l", "c", "ref_o", "ref_c"):
            B[k][sp:] = B[k][sp:] * rng.uniform(0.6, 1.6, len(B[k]) - sp)
        B["h"] = np.maximum.reduce([B["h"], B["o"], B["c"]])
        B["l"] = np.minimum.reduce([B["l"], B["o"], B["c"]])
        ta, _ = Z.discover(Z.prepare(A, cfg), cfg)
        tb, _ = Z.discover(Z.prepare(B, cfg), cfg)
        for d in ("long", "short"):
            self.assertEqual(ta[d]["names"], tb[d]["names"])
            for key in ("n", "weeks", "t", "theta", "mean_gross", "mean_net", "win", "clean"):
                self.assertTrue(np.array_equal(ta[d][key], tb[d][key]), (d, key))
            self.assertEqual(ta[d]["thr"], tb[d]["thr"])

    def test_cluster_t_matches_direct_computation(self):
        rng = np.random.default_rng(5)
        n = 400
        wk = np.repeat(np.arange(40), 10)
        x = rng.normal(0, 1, n) + np.repeat(rng.normal(0, 0.5, 40), 10)
        M = (rng.random((6, n)) < np.array([0.5, 0.3, 0.2, 0.1, 0.05, 0.8])[:, None]).astype(np.float32)
        theta, t, N, G = Z.cluster_t(M, x, wk, chunk=4)
        for r in range(6):
            m = M[r] > 0
            th = x[m].mean()
            aw = np.array([x[m & (wk == w)].sum() for w in range(40)])
            nw = np.array([(m & (wk == w)).sum() for w in range(40)], dtype=float)
            g = int((nw > 0).sum())
            se = np.sqrt(g / (g - 1.0) * ((aw - th * nw) ** 2).sum()) / nw.sum()
            self.assertAlmostEqual(theta[r], th, 12)
            self.assertAlmostEqual(t[r], th / se, 9)
            self.assertEqual((N[r], G[r]), (nw.sum(), g))

    def test_month_demeaning(self):
        S = make_series(3000, 22, split_frac=0.5)
        idx = np.arange(500, 2500)
        mon = Z.month_ids(S, idx)
        x = np.random.default_rng(1).normal(3.0, 1.0, len(idx)) + (mon - mon.min()) * 5.0  # a different level in every month
        y = Z.demean_by_month(x, mon)
        for m in np.unique(mon):
            self.assertAlmostEqual(float(y[mon == m].mean()), 0.0, 12)
        self.assertTrue(np.all(np.diff(mon) >= 0))

    def test_boot_diff_ci(self):
        rng = np.random.default_rng(3)
        wk = np.repeat(np.arange(200), 5)
        a = rng.normal(0.5, 1.0, len(wk))
        b = rng.normal(0.0, 1.0, len(wk))
        lo, hi, pt = Z.boot_diff_ci([(a, wk)], [(b, wk)], dict(Z.CFG, boot_b=400))
        self.assertAlmostEqual(pt, a.mean() - b.mean(), 12)
        self.assertLess(lo, pt)
        self.assertGreater(hi, pt)
        self.assertGreater(lo, 0.0)  # a true difference of 0.5 with 1000 trades per side is clearly positive
        lo, hi, pt = Z.boot_diff_ci([(a, wk)], [(a, wk)], dict(Z.CFG, boot_b=400))
        self.assertEqual(pt, 0.0)
        self.assertLessEqual(lo, 0.0)
        self.assertGreaterEqual(hi, 0.0)
        self.assertEqual(Z.boot_diff_ci([], [(a, wk)]), (None, None, None))

    def test_verdict_branches(self):
        cfg = Z.CFG
        ci = lambda lo, hi: (lo, hi)  # noqa: E731
        base = dict(btc_holdout=dict(n=100, mean=0.2, ci90=ci(0.05, 0.35)), others_holdout=dict(n=300, mean=0.1, ci90=ci(0.02, 0.2)),
                    btc_holdout_lift=dict(point=0.2, ci90=ci(0.04, 0.3)), others_holdout_lift=dict(point=0.1, ci90=ci(0.01, 0.2)),
                    btc_holdout_years={2023: dict(n=30, mean=0.1), 2024: dict(n=30, mean=0.2), 2025: dict(n=30, mean=0.1), 2026: dict(n=30, mean=-0.1)})

        def mod(**kw):
            e = {k: dict(v) if isinstance(v, dict) else v for k, v in base.items()}
            for k, v in kw.items():
                e[k] = v
            return e
        self.assertEqual(Z.verdict(mod(), cfg)["label"], "PASS")
        # a rising market alone: positive absolute mean but no lift over the all-free-hours policy
        self.assertEqual(Z.verdict(mod(btc_holdout_lift=dict(point=0.0, ci90=ci(-0.1, 0.1))), cfg)["label"], "FAIL")
        self.assertEqual(Z.verdict(mod(others_holdout_lift=dict(point=0.0, ci90=ci(-0.1, 0.1))), cfg)["label"], "FAIL")
        self.assertEqual(Z.verdict(mod(btc_holdout=dict(n=100, mean=0.05, ci90=ci(0.01, 0.1))), cfg)["label"], "FAIL")  # below the practical size
        self.assertEqual(Z.verdict(mod(btc_holdout=dict(n=100, mean=0.2, ci90=ci(-0.01, 0.4))), cfg)["label"], "FAIL")
        years = {2023: dict(n=30, mean=0.1), 2024: dict(n=30, mean=-0.2), 2025: dict(n=30, mean=0.1), 2026: dict(n=30, mean=-0.1)}
        self.assertEqual(Z.verdict(mod(btc_holdout_years=years), cfg)["label"], "FAIL")
        years2 = {2023: dict(n=5, mean=0.1), 2024: dict(n=30, mean=0.2), 2025: dict(n=30, mean=0.1), 2026: dict(n=30, mean=-0.1)}  # 5 trades do not count
        self.assertEqual(Z.verdict(mod(btc_holdout_years=years2), cfg)["label"], "FAIL")
        self.assertEqual(Z.verdict(mod(btc_holdout=dict(n=60, mean=0.2, ci90=ci(0.05, 0.35))), cfg)["label"], "INCONCLUSIVE")
        self.assertEqual(Z.verdict(mod(others_holdout=dict(n=100, mean=0.1, ci90=ci(0.02, 0.2))), cfg)["label"], "INCONCLUSIVE")
        self.assertEqual(Z.verdict(mod(btc_holdout=dict(n=0, mean=None, ci90=(None, None))), cfg)["label"], "INCONCLUSIVE")

    def test_no_false_pass_in_random_walks_with_and_without_drift(self):
        """pure noise, and noise with a strong common drift (a rising market): a PASS must not appear; with the drift the plain absolute
        criterion WOULD have approved rules, which is why the lift over the all-free-hours policy is part of the verdict"""
        cfg = easy_cfg()
        passes, abs_only = 0, 0
        for drift, seeds in ((0.0, range(8)), (0.0004, range(8))):
            for seed in seeds:
                ser = {Z.BTC: make_series(16000, 300 + seed, split_frac=0.5, drift=drift)}
                for k, nm in enumerate(("AAA", "BBB")):
                    ser[nm] = make_series(16000, 400 + seed * 3 + k, split_frac=0.5, drift=drift, symbol=nm)
                res = Z.run_study(ser, cfg)
                for e in res["evaluations"]:
                    passes += e["verdict"]["label"] == "PASS"
                    h, o = e["btc_holdout"], e["others_holdout"]
                    pos = lambda ci: ci[0] is not None and ci[0] > 0  # noqa: E731
                    abs_only += bool(e["direction"] == "long" and h["n"] >= cfg["min_trades_btc"] and h["mean"] is not None
                                     and h["mean"] >= cfg["min_effect_r"] and pos(h["ci90"]) and o["n"] >= cfg["min_trades_others"]
                                     and o["mean"] is not None and o["mean"] > 0 and pos(o["ci90"]))
        self.assertEqual(passes, 0)
        self.assertGreater(abs_only, 0, "the drifting market should have approved something under the absolute criterion alone")

    def test_a_planted_pattern_is_found_and_survives(self):
        """drift planted on bars that start in the Asian hours: a time-of-day rule must rank first, stay positive on the holdout and the
        other coins, and beat the all-free-hours policy"""
        cfg = easy_cfg()
        plant = {h: 0.004 for h in range(0, 8)}
        S = make_series(12000, 31, split_frac=0.6, hour_drift=plant)
        others = {"AAA": make_series(12000, 32, split_frac=0.6, hour_drift=plant, symbol="AAA"),
                  "BBB": make_series(12000, 33, split_frac=0.6, hour_drift=plant, symbol="BBB")}
        res = Z.run_study({Z.BTC: S, **others}, cfg)
        first = [e for e in res["evaluations"] if e["direction"] == "long" and e["rank"] == 1][0]
        self.assertIn("s_asia==1", first["rule"])
        self.assertGreater(first["t"], 4.0)
        self.assertGreater(first["btc_holdout"]["mean"], 0.0)
        self.assertGreater(first["others_holdout"]["mean"], 0.0)
        self.assertGreater(first["btc_holdout_lift"]["ci90"][0], 0.0)
        self.assertEqual(first["verdict"]["label"], "PASS")
        self.assertEqual(res["overall"], "CANDIDATE_FOR_FORWARD_TEST")

    def test_end_to_end_structure_and_encoding(self):
        cfg = small_cfg()
        S = make_series(8000, 41, split_frac=0.7)
        res = Z.run_study({Z.BTC: S, "AAA": make_series(8000, 42, split_frac=0.7, symbol="AAA")}, cfg)
        for key in ("oracle", "evaluations", "top_rules", "top_clean_rules", "clean_profile", "family", "overall"):
            self.assertIn(key, res)
        for d in ("long", "short"):
            pc = [r["p_clean"] for r in res["top_clean_rules"][d]]
            self.assertEqual(pc, sorted(pc, reverse=True))
            self.assertEqual(len(pc), 12)
        self.assertEqual(res["family"]["singles"], 34)
        self.assertIn(res["overall"], ("CANDIDATE_FOR_FORWARD_TEST", "NO_CANDIDATE"))
        self.assertEqual(len(res["evaluations"]), 2 * cfg["top_n"])
        for e in res["evaluations"]:
            self.assertIn(e["verdict"]["label"], ("PASS", "FAIL", "INCONCLUSIVE"))
            self.assertIn(e["rank"], (1, 2, 3))
        for d in ("long", "short"):  # the evaluated rules are the top of the printed ranking, in order
            ranked = [t["rule"] for t in res["top_rules"][d]][:cfg["top_n"]]
            self.assertEqual([e["rule"] for e in res["evaluations"] if e["direction"] == d], ranked)
            ts = [t["t"] for t in res["top_rules"][d]]
            self.assertEqual(ts, sorted(ts, reverse=True))
        rows = [r for r in res["oracle"] if r["dir"] == "long" and r["period"] == "discovery"]
        self.assertEqual(len(rows), 12)
        for r in rows:
            self.assertLessEqual(r["p_clean"], r["p_win"])
        for am in (0.5, 1.0, 2.0):  # a win at 3 stops is also a win at 2 stops
            a = [r for r in rows if r["a"] == am and r["k"] == 2.0 and r["h"] == 24][0]
            b = [r for r in rows if r["a"] == am and r["k"] == 3.0 and r["h"] == 24][0]
            self.assertGreaterEqual(a["p_win"], b["p_win"])
        back = Z.decode_chunks(Z.encode_chunks(res))
        self.assertEqual(back["overall"], res["overall"])
        txt = Z.render(res, [dict(symbol="BTCUSDT", status="OK", bars=1, missing_hours=0, sha256="x")], "0" * 64)
        self.assertIn("Zero-Pip Lab", txt)

    def test_discovery_and_holdout_samples_are_disjoint(self):
        S = make_series(6000, 51, split_frac=0.5)
        for d, view in (("long", S), ("short", Z.mirror(S))):
            out = Z.outcomes(view, 1.0, 3.0, 24, 0.001)
            m = Z.masks_for(view, out)
            self.assertFalse(np.any(m["disc"] & m["hold"]))
            self.assertTrue(np.all(out["exit_bar"][m["disc"]] < m["split_idx"]))
            self.assertTrue(np.all(view["t"][np.flatnonzero(m["hold"]) + 1] >= Z.SPLIT_MS))
        a = Z.masks_for(S, Z.outcomes(S, 1.0, 3.0, 24, 0.001))["disc"]
        b = Z.masks_for(Z.mirror(S), Z.outcomes(Z.mirror(S), 1.0, 3.0, 24, 0.001))["disc"]
        self.assertTrue(np.array_equal(a, b))

    def test_thresholds_come_from_before_the_split(self):
        S = make_series(7000, 61, split_frac=0.6)
        T = make_series(7000, 61, split_frac=0.6)
        sp = int(np.searchsorted(T["t"], Z.SPLIT_MS))
        T["c"][sp:] *= 3.0
        T["o"][sp:] *= 3.0
        T["h"][sp:] *= 3.0
        T["l"][sp:] *= 3.0
        self.assertEqual(Z.thresholds(Z.features(S), S), Z.thresholds(Z.features(T), T))


def klines_rows(S):
    rows = []
    for i in range(len(S["t"])):
        if np.isnan(S["c"][i]):
            continue
        t = int(S["t"][i])
        rows.append([t, str(S["o"][i]), str(S["h"][i]), str(S["l"][i]), str(S["c"][i]), str(S["v"][i]), t + H - 1, "0", 1,
                     str(S["tb"][i]), "0", "0"])
    return rows


def fake_server(rows, bad_hosts=(), log=None):
    def get(url):
        host = url.split("/")[2]
        if log is not None:
            log.append(host)
        if host in bad_hosts:
            raise urllib.error.URLError("down")
        q = dict(p.split("=") for p in url.split("?")[1].split("&"))
        st, en, lim = int(q["startTime"]), int(q["endTime"]), int(q["limit"])
        sel = [r for r in rows if st <= r[0] <= en][:lim]
        return json.dumps(sel).encode()
    return get


class Data(unittest.TestCase):
    sleep = staticmethod(lambda s: None)

    def test_pagination_failover_and_gap(self):
        S = make_series(2600, 71, gaps=(1500,))
        rows = klines_rows(S)
        end = int(S["t"][-1]) + H
        log = []
        got = Z.fetch_klines("X", fake_server(rows, bad_hosts=(Z.HOSTS[0],), log=log), start_ms=int(S["t"][0]), end_ms=end, sleep=self.sleep)
        self.assertEqual(len(got), 2599)
        self.assertIn(Z.HOSTS[1], log)
        B = Z.build_series("X", got, end)
        self.assertEqual((B["missing"], B["bars"], len(B["c"])), (1, 2599, 2600))
        self.assertTrue(np.isnan(B["c"][1500]))
        self.assertTrue(np.array_equal(B["t"], S["t"]))
        with self.assertRaises(Z.DataError):
            Z.fetch_klines("X", fake_server(rows, bad_hosts=Z.HOSTS), start_ms=int(S["t"][0]), end_ms=end, sleep=self.sleep)

    def test_validation(self):
        S = make_series(100, 72)
        rows = klines_rows(S)
        end = int(S["t"][-1]) + H
        good, bad = Z.parse_rows("X", rows, end)
        self.assertEqual((len(good), len(bad)), (100, 0))
        with self.assertRaises(Z.DataError):
            Z.parse_rows("X", rows[:10] + rows[9:], end)  # not strictly increasing: still fatal
        off = [list(r) for r in rows]
        off[3][0] += 1000
        with self.assertRaises(Z.DataError):
            Z.parse_rows("X", off, end)  # open time off the hour: still fatal
        with self.assertRaises(Z.DataError):
            Z.parse_rows("X", rows, end - H)  # a bar that ends after the data end: still fatal
        with self.assertRaises(Z.DataError):
            Z.parse_rows("X", [], end)
        # per-row problems are no longer fatal: the hour becomes invalid and the row is never used
        flawed = [list(r) for r in rows]
        flawed[5][2] = str(float(flawed[5][3]) - 1.0)  # high below low
        flawed[7][6] = flawed[7][0] + 1_753_419  # partial-hour bar
        flawed[9][6] = flawed[9][0]  # close time == open time
        flawed[11][5], flawed[11][9] = "1.0", "2.0"  # taker-buy volume larger than volume
        flawed[13][3] = "0"  # non-positive low
        good, bad = Z.parse_rows("X", flawed, end)
        self.assertEqual(len(good), 95)
        self.assertEqual([t for t, _ in bad], [int(flawed[i][0]) for i in (5, 7, 9, 11, 13)])
        self.assertEqual([w for _, w in bad], [["malformed_bar"], ["close_time"], ["close_time"], ["malformed_bar"], ["malformed_bar"]])
        # the file is rejected only when nothing valid is left
        with self.assertRaises(Z.DataError):
            Z.parse_rows("X", [flawed[5]], end)

    def test_load_all_excludes_a_gappy_coin(self):
        S = make_series(1500, 73)
        gappy = make_series(1500, 74, gaps=tuple(range(100, 140)))
        srv = {"OK": klines_rows(S), "GAP": klines_rows(gappy)}
        end = int(S["t"][-1]) + H

        def http_get(url):
            return fake_server(srv[url.split("symbol=")[1].split("&")[0]])(url)
        got, notes = Z.load_all(("OK", "GAP"), http_get=http_get, end_ms=end, sleep=self.sleep)
        self.assertEqual(list(got), ["OK"])
        self.assertEqual({n["symbol"]: n["status"] for n in notes}, {"OK": "OK", "GAP": "EXCLUDED"})

    def test_chunk_round_trip(self):
        obj = {"a": list(range(5000)), "b": {"x": 1.5, "y": None}}
        chunks = Z.encode_chunks(obj, width=500)
        self.assertGreater(len(chunks), 1)
        self.assertTrue(all(len(c) <= 500 for c in chunks))
        self.assertEqual(Z.decode_chunks(chunks), obj)


def irregular(rows, idx, kind):
    """a copy of klines rows where row idx is replaced by one of the three kinds of irregular rows seen in public Binance history"""
    out = [list(r) for r in rows]
    r = out[idx]
    if kind == "placeholder":  # zero-volume filler: flat bar, close time == open time
        o = r[1]
        r[1] = r[2] = r[3] = r[4] = o
        r[5] = r[9] = "0.00000000"
        r[6] = r[0]
    elif kind == "partial_long":
        r[6] = r[0] + 1_753_419
    elif kind == "partial_short":
        r[6] = r[0] + 14_838
    return out


class Ingest(unittest.TestCase):
    sleep = staticmethod(lambda s: None)

    def test_irregular_rows_become_invalid_hours(self):
        S = make_series(2600, 81)
        rows = klines_rows(S)
        end = int(S["t"][-1]) + H
        mixed = irregular(irregular(irregular(rows, 400, "placeholder"), 900, "partial_long"), 1700, "partial_short")
        B = Z.build_series("X", mixed, end)
        self.assertEqual((B["bars"], B["invalid"], B["missing"], len(B["c"])), (2597, 3, 3, 2600))
        self.assertEqual([t for t, _ in B["invalid_rows"]], [int(S["t"][i]) for i in (400, 900, 1700)])
        for i in (400, 900, 1700):
            for k in ("o", "h", "l", "c", "v", "tb", "ref_o", "ref_c"):
                self.assertTrue(np.isnan(B[k][i]), (k, i))
        keep = np.ones(2600, dtype=bool)
        keep[[400, 900, 1700]] = False
        for k in ("o", "h", "l", "c", "v", "tb"):
            self.assertTrue(np.array_equal(B[k][keep], S[k][keep]), k)  # nothing else is touched or repaired

    def test_an_invalid_hour_behaves_exactly_like_an_absent_hour(self):
        S = make_series(2600, 82)
        rows = klines_rows(S)
        end = int(S["t"][-1]) + H
        for kind in ("placeholder", "partial_long", "partial_short"):
            A = Z.build_series("X", irregular(rows, 1200, kind), end)
            G = Z.build_series("X", rows[:1200] + rows[1201:], end)  # the same hour simply absent
            for k in ("t", "o", "h", "l", "c", "v", "tb", "ref_o", "ref_c"):
                self.assertTrue(same(A[k], G[k]), (kind, k))
            FA, FG = Z.features(A), Z.features(G)
            self.assertEqual(list(FA), list(FG))
            for k in FA:
                self.assertTrue(same(FA[k], FG[k]), (kind, k))
            for a_mult, kk, h in ((1.0, 3.0, 24), (0.5, 2.0, 12)):
                OA, OG = Z.outcomes(A, a_mult, kk, h, 0.001), Z.outcomes(G, a_mult, kk, h, 0.001)
                for k in ("res", "gross", "net", "mae", "exit_bar", "sd", "entry"):
                    self.assertTrue(same(OA[k], OG[k]), (kind, k))
            # and the poisoned decisions are exactly those whose bars or windows touch the invalid hour
            res = Z.outcomes(A, 1.0, 3.0, 24, 0.001)["res"]
            self.assertTrue(np.all(res[1176:1200] == 0))  # the entry bar or a bar of the 24-bar window is the invalid hour

    def test_clean_rows_are_ingested_identically_to_v1(self):
        S = make_series(2600, 83, gaps=(700, 701, 1900))
        rows = klines_rows(S)
        end = int(S["t"][-1]) + H
        B1, B2 = Z1.build_series("X", rows, end), Z.build_series("X", rows, end)
        for k in ("t", "o", "h", "l", "c", "v", "tb", "ref_o", "ref_c"):
            self.assertTrue(same(B1[k], B2[k]), k)
        self.assertEqual((B1["bars"], B1["missing"]), (B2["bars"], B2["missing"]))
        self.assertEqual(Z1.data_hash(B1), Z.data_hash(B2))
        self.assertEqual(B2["invalid"], 0)

    def test_cap_counts_invalid_rows(self):
        S = make_series(1500, 84)
        base = klines_rows(S)
        end = int(S["t"][-1]) + H
        few = base
        for i in (100, 600, 1200):
            few = irregular(few, i, "partial_long")
        many = base
        for i in range(100, 130):  # 30 of 1500 = 2% > the 1% cap
            many = irregular(many, i, "partial_short")
        srv = {"FEW": few, "MANY": many}

        def http_get(url):
            return fake_server(srv[url.split("symbol=")[1].split("&")[0]])(url)
        got, notes = Z.load_all(("FEW", "MANY"), http_get=http_get, end_ms=end, sleep=self.sleep)
        self.assertEqual(list(got), ["FEW"])
        by = {n["symbol"]: n for n in notes}
        self.assertEqual((by["FEW"]["status"], by["FEW"]["invalid_rows"], by["FEW"]["missing_hours"]), ("OK", 3, 3))
        self.assertEqual(by["FEW"]["invalid_open_ms"], [int(S["t"][i]) for i in (100, 600, 1200)])
        self.assertEqual((by["MANY"]["status"], by["MANY"]["invalid_rows"]), ("EXCLUDED", 30))
        self.assertIn("missing_frac", by["MANY"]["reason"])

    def test_main_prints_the_data_notes_before_it_stops(self):
        notes = [dict(symbol="BTCUSDT", status="EXCLUDED", reason="missing_frac=0.5000", missing_hours=5, invalid_rows=1)]
        buf = io.StringIO()
        with tempfile.TemporaryDirectory() as tmp, unittest.mock.patch.object(Z, "load_all", return_value=({}, notes)), \
                contextlib.redirect_stdout(buf):
            with self.assertRaises(SystemExit) as cm:
                Z.main(["zeropip_v2.py", os.path.join(tmp, "out")])
        self.assertIn("infrastructure failure", str(cm.exception))
        line = [x for x in buf.getvalue().splitlines() if x.startswith("DATA_NOTE ")]
        self.assertEqual(len(line), 1)
        self.assertEqual(json.loads(line[0][len("DATA_NOTE "):]), notes[0])

    def test_render_data_table_shows_invalid_rows(self):
        S = make_series(1500, 85, split_frac=0.6)
        notes = [dict(symbol="X", status="OK", bars=1497, missing_hours=3, invalid_rows=3, sha256="abc"),
                 dict(symbol="Y", status="EXCLUDED", reason="missing_frac=0.0200", missing_hours=30, invalid_rows=30)]
        res = dict(overall="NO_CANDIDATE", oracle=[], family={}, top_rules={"long": [], "short": [], "long_base": dict(p_win=0.1, p_clean=0.1, mean_gross=0.0, mean_net=0.0),
                                                                "short_base": dict(p_win=0.1, p_clean=0.1, mean_gross=0.0, mean_net=0.0)},
                   top_clean_rules={"long": [], "short": []}, clean_profile={"long": {}, "short": {}}, evaluations=[])
        txt = Z.render(res, notes, "deadbeef")
        self.assertIn("| X | OK | 1497 | 3 | 3 | abc |", txt)
        self.assertIn("| Y | EXCLUDED |  | 30 missing_frac=0.0200 | 30 |  |", txt)
        self.assertIn("Zero-Pip Lab v2 report", txt)
        self.assertEqual(len(S["c"]), 1500)


class V2ChangesOnlyIngest(unittest.TestCase):
    """The analysis code of v2 must be the analysis code of v1: compare the syntax trees of every top-level definition."""
    INGEST = {"parse_rows", "build_series", "load_all", "render", "main", "VERSION"}
    NEW = {"row_problems"}

    @staticmethod
    def top_level(path):
        tree = ast.parse(Path(path).read_text(encoding="utf-8"))
        out = {}
        for node in tree.body:
            if isinstance(node, (ast.FunctionDef, ast.ClassDef)):
                out[node.name] = ast.dump(node)
            elif isinstance(node, ast.Assign) and len(node.targets) == 1 and isinstance(node.targets[0], ast.Name):
                out[node.targets[0].id] = ast.dump(node)
            elif isinstance(node, (ast.Import, ast.ImportFrom)):
                out["import:" + ast.dump(node)] = ast.dump(node)
        return out

    def test_every_other_definition_is_identical(self):
        here = Path(__file__).resolve().parent
        a, b = self.top_level(here / "zeropip.py"), self.top_level(here / "zeropip_v2.py")
        self.assertEqual(set(b) - set(a), self.NEW)
        self.assertEqual(set(a) - set(b), set())
        differing = {k for k in a if a[k] != b[k]}
        self.assertEqual(differing, self.INGEST)
        self.assertGreater(len(a), 60)  # the comparison really covers the analysis code

    def test_v1_file_is_still_the_frozen_one(self):
        here = Path(__file__).resolve().parent
        want = (here / "CODE_SHA256.txt").read_text().split()[0]
        self.assertEqual(hashlib.sha256((here / "zeropip.py").read_bytes()).hexdigest(), want)
        self.assertEqual(want, "b93e1f997819e778e029adc2fd68a221cc03c99f3824209065466800d1ec6b2b")


if __name__ == "__main__":
    unittest.main(verbosity=1)
