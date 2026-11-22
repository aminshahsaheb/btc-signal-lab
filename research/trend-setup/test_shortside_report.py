#!/usr/bin/env python3
"""Synthetic tests for shortside_report.py. Same author as the code: they check that the mirrored rule is the mirror of the frozen rule, that the long leg is the frozen
rule unchanged, the arithmetic of costs/alerts and the mechanical verdict. They say nothing about whether a short side earns money.
Run: python -I -B research/trend-setup/test_shortside_report.py
"""
import json
import math
import sys
import unittest
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import longhistory_report as LH  # noqa: E402
import robustness_report as RB  # noqa: E402
import shortside_report as S  # noqa: E402
import test_trendsetup as TT  # noqa: E402
import trendsetup as T  # noqa: E402

DAY = T.DAY_MS


def to_market(d, day0=10000):
    n = len(d["c"])
    return dict(day=day0 + np.arange(n, dtype=np.int64), o=d["o"], h=d["h"], l=d["l"], c=d["c"])


def drift_series(n, mu, seed):
    u = TT.stream(seed)
    o_, h_, l_, c_ = [], [], [], []
    prev = 100.0
    for _ in range(n):
        r = mu + (next(u) - 0.5) * 0.06
        o = prev
        c = o * math.exp(r)
        h = max(o, c) * (1 + 0.004 * next(u))
        l = min(o, c) * (1 - 0.004 * next(u))
        o_.append(o); h_.append(h); l_.append(l); c_.append(c)
        prev = c
    return dict(o=np.array(o_), h=np.array(h_), l=np.array(l_), c=np.array(c_), t=T.START_MS + DAY * np.arange(n, dtype=np.int64), day=10000 + np.arange(n, dtype=np.int64))


def plain_short_state(h, l, c, N):
    """Independent plain-loop short rule: enter short when close < min(low of the previous N bars); exit when close > max(high of the previous N//2 bars)."""
    M, st, out = N // 2, 0, []
    for i in range(len(c)):
        if st == 1 and i >= M and c[i] > max(h[i - M:i]):
            st = 0
        elif st == 0 and i >= N and c[i] < min(l[i - N:i]):
            st = 1
        out.append(st)
    return np.array(out, float)


class MirrorRule(unittest.TestCase):
    def test_matches_independent_loop(self):
        for seed in (1, 2, 3):
            d = drift_series(900, -0.001, seed)
            got = S.short_states(d)
            for k, N in enumerate(T.ENS_N):
                np.testing.assert_array_equal(got[:, k], plain_short_state(d["h"], d["l"], d["c"], N))

    def test_equals_frozen_long_rule_on_the_reciprocal_price_series(self):
        """Mapping every price p to K/p swaps highs and lows and turns 'close above the N-bar high' into 'close below the N-bar low'."""
        d = drift_series(900, 0.0003, 7)
        K = 1000.0
        for k, N in enumerate(T.ENS_N):
            np.testing.assert_array_equal(S.short_states(d)[:, k], T.donchian_state(K / d["l"], K / d["h"], K / d["c"], N))

    def test_no_short_in_a_rising_market_and_short_in_a_falling_one(self):
        up, down = drift_series(700, 0.004, 4), drift_series(700, -0.004, 4)
        self.assertLess(S.short_states(up)[300:].mean(), 0.1)
        self.assertGreater(S.short_states(down)[300:].mean(), 0.5)
        self.assertLess(T.coin_calc(down)["S"][300:].mean(), 0.1)  # the frozen long states are mostly off in the same market
        self.assertGreater(T.coin_calc(up)["S"][300:].mean(), 0.5)

    def test_short_state_uses_only_bars_up_to_i(self):
        d = drift_series(600, -0.001, 9)
        full = S.short_states(d)
        cut = {k: v[:400] for k, v in d.items()}
        np.testing.assert_array_equal(S.short_states(cut), full[:400])


class Legs(unittest.TestCase):
    def test_long_leg_is_the_frozen_rule_unchanged(self):
        d = drift_series(900, 0.0005, 11)
        e = S.evaluate(d)
        D, R, H, E = LH.evaluate(d)
        np.testing.assert_array_equal(e["day"], D)
        np.testing.assert_allclose(e["L"], R, rtol=0, atol=1e-15)
        np.testing.assert_allclose(e["hold"], H, rtol=0, atol=1e-15)

    def test_long_short_equals_sum_of_legs_without_costs_and_beats_it_with_costs_only_by_netting(self):
        d = drift_series(900, -0.0004, 12)
        e0 = S.evaluate(d, c_side=0.0)
        np.testing.assert_allclose(e0["LS"], e0["L"] + e0["S"], rtol=0, atol=1e-15)
        e = S.evaluate(d)
        diff = e["LS"] - (e["L"] + e["S"])
        self.assertTrue((diff >= -1e-15).all())  # one combined position pays no more cost than two separate ones

    def test_directions(self):
        up, down = drift_series(1500, 0.004, 21), drift_series(1500, -0.004, 21)
        eu, ed = S.evaluate(up), S.evaluate(down)
        self.assertGreater(float((1 + eu["L"]).prod()), 1.0)
        self.assertLess(float((1 + eu["S"]).prod()), 1.0)
        self.assertGreater(float((1 + ed["S"]).prod()), 1.0)
        self.assertGreater(eu["long_share"], 0.5)
        self.assertGreater(ed["short_share"], 0.5)

    def test_decision_uses_the_previous_close(self):
        """Changing the last bar's close must not change any earlier counted return (no look-ahead)."""
        d = drift_series(700, -0.001, 5)
        base = S.evaluate(d)
        d2 = {k: v.copy() for k, v in d.items()}
        d2["c"][-1] *= 0.5
        d2["l"][-1] = min(d2["l"][-1], d2["c"][-1])
        other = S.evaluate(d2)
        n = len(base["LS"]) - 2
        np.testing.assert_array_equal(base["LS"][:n], other["LS"][:n])


class Alerts(unittest.TestCase):
    def test_direction_state(self):
        ready = np.ones(4, bool)
        st = S.direction_state(np.array([.4, .2, .2, 0.]), np.array([.2, .4, .2, .6]), ready)
        self.assertEqual(list(st), [1, -1, 0, -1])
        self.assertEqual(list(S.direction_state(np.array([.4, .2, .2, 0.]), np.array([.2, .4, .2, .6]), ready, long_only=True)), [1, 1, 1, 0])
        self.assertEqual(list(S.direction_state(np.array([.4, .2]), np.array([0., 0.]), np.array([False, True]))), [0, 1])

    def test_alert_counts(self):
        state = np.array([0, 0, 1, 1, -1, 0, 0, -1, 0])
        c = S.alert_counts(state, np.ones(9, bool))
        self.assertEqual((c["enter_long"], c["enter_short"], c["flip"], c["exit"], c["total"]), (1, 1, 1, 2, 5))
        ready = np.array([False, False, False, True, True, True, True, True, True])
        c2 = S.alert_counts(state, ready)  # the 0 -> 1 change at index 2 involves unready bars
        self.assertEqual((c2["enter_long"], c2["flip"], c2["exit"], c2["enter_short"]), (0, 1, 2, 1))
        c3 = S.alert_counts(state, np.ones(9, bool), lo=5)  # only changes at index >= 5
        self.assertEqual((c3["exit"], c3["enter_short"], c3["total"]), (2, 1, 3))

    def test_baskets_arithmetic(self):
        raw = TT.synth(6, 1500, 5, 0)
        datas = {sym: dict(raw[k], symbol=sym) for k, sym in zip(sorted(raw), T.UNIVERSE)}
        out = S.alert_baskets(datas)
        self.assertEqual([a["n"] for a in out], [1, 2, 5, 6, 6])  # baskets larger than the available coins are capped (in the real run all 26 exist)
        per = {s: S.coin_alerts(datas[s]) for s in datas}
        a5 = [a for a in out if a["n"] == 5][0]
        yrs = np.mean([per[s]["full"]["bars"] for s in a5["members"]]) / 365.0
        ev = sum(per[s]["full"]["LS"]["total"] for s in a5["members"])
        self.assertAlmostEqual(a5["full_LS_per_week"], ev / (yrs * 52.0), places=12)
        parts = sum(a5[f"full_LS_{k}_per_week"] for k in ("enter_long", "enter_short", "flip", "exit"))
        self.assertAlmostEqual(parts, a5["full_LS_per_week"], places=12)
        for a in out:  # a direction alert needs a signal change, long-short alerts are at least the long-only ones
            self.assertGreaterEqual(a["full_LS_per_week"] + 1e-12, a["full_L_per_week"])


class CryptoAndVerdict(unittest.TestCase):
    def test_crypto_long_leg_equals_frozen_portfolio(self):
        raw = TT.synth(8, 1400, 3, 0)
        datas = {sym: dict(raw[k], symbol=sym) for k, sym in zip(sorted(raw), T.UNIVERSE)}
        out = S.crypto(datas)
        G = T.grid(datas)
        R, H, _ = RB.port(G, list(range(8)), min_active=3)
        exp = RB.brief(*RB.cut(G["t"], R))
        for k in ("cagr", "sharpe", "maxdd", "total", "days"):
            self.assertAlmostEqual(out["all"]["results"]["full"]["L"][k], exp[k], places=12)
        expH = RB.brief(*RB.cut(G["t"], H))
        self.assertAlmostEqual(out["all"]["results"]["full"]["hold"]["total"], expH["total"], places=12)

    def _row(self, sh_l, sh_ls, tot_s, years=12.0):
        return dict(status="OK", L=dict(sharpe=sh_l, years=years), LS=dict(sharpe=sh_ls), S=dict(total=tot_s))

    def _cry(self, s_total, ls_sh, l_sh):
        r = dict(S=dict(total=s_total), LS=dict(sharpe=ls_sh), L=dict(sharpe=l_sh))
        return dict(all=dict(results=dict(full=r, from2023=r)))

    def test_verdict_mechanics(self):
        good = [self._row(0.5, 0.6, 0.1) for _ in range(8)]
        self.assertEqual(S.verdict(good, self._cry(0.2, 1.1, 1.0))["verdict"], "SUPPORTED")
        self.assertEqual(S.verdict(good, self._cry(-0.2, 1.1, 1.0))["verdict"], "MIXED")  # S3 fails
        bad = [self._row(0.5, 0.4, -0.1) for _ in range(8)]
        self.assertEqual(S.verdict(bad, self._cry(-0.2, 0.9, 1.0))["verdict"], "NOT_SUPPORTED")
        self.assertEqual(S.verdict(good[:7], self._cry(0.2, 1.1, 1.0))["verdict"], "INSUFFICIENT_DATA")
        short_hist = [self._row(0.5, 0.6, 0.1, years=9.9) for _ in range(8)]
        self.assertEqual(S.verdict(short_hist, self._cry(0.2, 1.1, 1.0))["verdict"], "INSUFFICIENT_DATA")  # fewer than 10 counted years does not count
        half = [self._row(0.5, 0.6, 0.1) for _ in range(4)] + [self._row(0.5, 0.4, -0.1) for _ in range(4)]
        v = S.verdict(half, self._cry(0.2, 1.1, 1.0))
        self.assertTrue(v["s1_met"] and v["s2_met"] and v["s3_met"])  # exactly 50% is enough ("at least")

    def test_end_to_end_on_synthetic_inputs(self):
        raw = TT.synth(13, 4500, 41, 0)
        fetched = {}
        for (sym, _, _), key in zip(LH.MARKETS, sorted(raw)):
            fetched[sym] = (to_market(raw[key]), 0, 4500)
        fetched["BTC-BITSTAMP"] = (to_market(raw[sorted(raw)[0]]), 0, 4500)
        craw = TT.synth(12, 1500, 21, 0)
        datas = {sym: dict(craw[k], symbol=sym) for k, sym in zip(sorted(craw), T.UNIVERSE)}
        rep = S.build(datas, [], T.code_sha256(), fetched=fetched)
        self.assertEqual(len(rep["markets"]), 13)
        self.assertTrue(all(r["status"] == "OK" for r in rep["markets"]))
        self.assertEqual(rep["verdict"]["eligible"], 13)
        self.assertIn(rep["verdict"]["verdict"], ("SUPPORTED", "MIXED", "NOT_SUPPORTED"))
        json.dumps(rep)  # the JSON the workflow prints must serialise (no numpy scalars)
        md = S.summary_md(rep)
        for s in ("Alerts per week", "Pre-registered criteria", "verdict:"):
            self.assertIn(s, md)
        self.assertEqual(rep["code_sha256"], T.code_sha256())

    def test_excluded_and_source_error_markets_are_not_evaluated(self):
        raw = TT.synth(13, 4500, 41, 0)
        fetched = {}
        for (sym, _, _), key in zip(LH.MARKETS, sorted(raw)):
            fetched[sym] = (to_market(raw[key]), 0, 4500)
        fetched["BTC-BITSTAMP"] = (to_market(raw[sorted(raw)[0]]), 0, 4500)
        fetched[LH.MARKETS[0][0]] = (to_market(raw[sorted(raw)[0]]), 100, 4500)  # 2.2% bad rows > 1%
        del fetched[LH.MARKETS[1][0]]  # missing -> SOURCE_ERROR
        rows, btc = S.noncrypto(fetched)
        self.assertEqual(rows[0]["status"], "EXCLUDED_BAD_DATA")
        self.assertEqual(rows[1]["status"], "SOURCE_ERROR")
        self.assertEqual(btc["status"], "OK")


if __name__ == "__main__":
    unittest.main()
