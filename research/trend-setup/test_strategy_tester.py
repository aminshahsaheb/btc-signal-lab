#!/usr/bin/env python3
"""Synthetic tests for strategy_tester.py. Same author as the code, no independent review. They check the arithmetic and the replay mechanics against the engine's own
documented rules (ALERT_RULES_v1) and against the frozen trend code; they say nothing about whether any rule earns money.
Run: python -I -B research/trend-setup/test_strategy_tester.py
"""
import json
import math
import sys
import unittest
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import robustness_report as RB  # noqa: E402
import strategy_tester as S  # noqa: E402
import test_trendsetup as TT  # noqa: E402
import trendsetup as T  # noqa: E402

D, H = S.DAY, S.H_MS


def bars(t0, ms, closes, spread=1.0, opens=None):
    n = len(closes)
    c = np.array(closes, dtype=float)
    o = np.array(opens, dtype=float) if opens is not None else c.copy()
    h = np.maximum(o, c) + spread
    l = np.minimum(o, c) - spread
    t = t0 + ms * np.arange(n, dtype=np.int64)
    return dict(symbol="X", t=t, o=o, h=h, l=l, c=c, close_ms=t + ms - 1, missing=0)


def flat_daily(n=25, hi=100.0, lo=90.0, c=95.0):
    t = np.arange(n, dtype=np.int64) * D
    return dict(symbol="X", t=t, o=np.full(n, c), h=np.full(n, hi), l=np.full(n, lo), c=np.full(n, c), close_ms=t + D - 1, missing=0)


def hourly_after(day_idx, closes, hl=None):
    """Hourly bars starting at the open of daily bar day_idx. hl: optional list of (high, low) per bar."""
    t0 = day_idx * D
    hb = bars(t0, H, closes, spread=0.0)
    if hl is not None:
        hb["h"] = np.array([a for a, _ in hl], dtype=float)
        hb["l"] = np.array([b for _, b in hl], dtype=float)
    return hb


def engine_atr14(bars_):
    """Verbatim copy of scripts/alerts.py atr14 (dict bars) for the comparison."""
    n = len(bars_)
    out = [None] * n
    if n <= 14:
        return out
    tr = [bars_[0]["h"] - bars_[0]["l"]]
    for i in range(1, n):
        pc = bars_[i - 1]["c"]
        tr.append(max(bars_[i]["h"] - bars_[i]["l"], abs(bars_[i]["h"] - pc), abs(bars_[i]["l"] - pc)))
    a = sum(tr[1:15]) / 14.0
    out[14] = a
    for i in range(15, n):
        a = (a * 13.0 + tr[i]) / 14.0
        out[i] = a
    return out


class TestAtr(unittest.TestCase):
    def test_matches_engine_copy(self):
        u = TT.stream(11)
        c = 100.0
        rows = []
        for _ in range(80):
            o = c
            c = o * math.exp((next(u) - 0.5) * 0.05)
            rows.append(dict(o=o, h=max(o, c) * (1 + 0.01 * next(u)), l=min(o, c) * (1 - 0.01 * next(u)), c=c))
        ref = engine_atr14(rows)
        got = S.atr14(np.array([r["h"] for r in rows]), np.array([r["l"] for r in rows]), np.array([r["c"] for r in rows]))
        for a, b in zip(ref, got):
            if a is None:
                self.assertTrue(np.isnan(b))
            else:
                self.assertEqual(a, b)

    def test_flat_atr_is_range(self):
        d = flat_daily(40)
        a = S.atr14(d["h"], d["l"], d["c"])
        self.assertTrue(np.isnan(a[13]))
        self.assertAlmostEqual(a[14], 10.0, places=12)
        self.assertAlmostEqual(a[39], 10.0, places=12)


class TestReplay(unittest.TestCase):
    def test_engine_selftest_scenario_long(self):
        # the engine's own selftest: 25 flat daily bars (high 100, low 90, close 95), hourly closes 95,95,95,96,100,102 -> LONG ref 102 level 100 stop 92 target 122
        d1 = flat_daily(25)
        h1 = hourly_after(25, [95, 95, 95, 96, 100, 102])
        ev = S.replay_alert_b(h1, d1)
        self.assertEqual(len(ev), 1)
        e = ev[0]
        self.assertEqual((e["side"], e["ref"], e["level"]), ("LONG", 102.0, 100.0))
        self.assertAlmostEqual(e["stop"], 92.0, places=9)
        self.assertAlmostEqual(e["target"], 122.0, places=9)
        self.assertEqual(e["bar_open_ms"], 25 * D + 5 * H)

    def test_short_mirror(self):
        d1 = flat_daily(25)
        h1 = hourly_after(25, [95, 95, 95, 94, 90, 88])
        ev = S.replay_alert_b(h1, d1)
        self.assertEqual(len(ev), 1)
        e = ev[0]
        self.assertEqual((e["side"], e["ref"], e["level"]), ("SHORT", 88.0, 90.0))
        self.assertAlmostEqual(e["stop"], 98.0, places=9)
        self.assertAlmostEqual(e["target"], 68.0, places=9)

    def test_touching_the_level_is_not_a_break(self):
        d1 = flat_daily(25)
        self.assertEqual(S.replay_alert_b(hourly_after(25, [95, 95, 100, 100]), d1), [])  # close == level: not above it
        self.assertEqual(S.replay_alert_b(hourly_after(25, [95, 95, 90, 90]), d1), [])

    def test_cooldown_blocks_inside_24h_and_releases_after(self):
        d1 = flat_daily(30)
        closes = [95, 95, 95, 101, 95, 95, 95, 95, 95, 95, 101] + [95] * 14 + [101] + [95] * 3 + [101]  # breaks at hours 3, 10, 25, 29
        h1 = hourly_after(30, closes)
        ev = S.replay_alert_b(h1, d1)
        opens = [(e["bar_open_ms"] - 30 * D) // H for e in ev]
        self.assertEqual(opens, [3, 29])  # 10 and 25 are less than 24 h after the sent alert at 3; 29 is 26 h after it
        # the other side is not affected by a LONG cooldown
        closes2 = [95, 95, 95, 101, 95, 89, 95]
        ev2 = S.replay_alert_b(hourly_after(30, closes2), d1)
        self.assertEqual([e["side"] for e in ev2], ["LONG", "SHORT"])

    def test_cooldown_counts_from_last_sent_not_last_blocked(self):
        d1 = flat_daily(30)
        closes = [95, 95, 95, 101] + [95, 101] * 12 + [95] * 3 + [101]  # breaks every 2 h from hour 3; the sent one at 3, next release at >= 27
        ev = S.replay_alert_b(hourly_after(30, closes), d1)
        opens = [(e["bar_open_ms"] - 30 * D) // H for e in ev]
        self.assertEqual(opens[0], 3)
        self.assertTrue(all(b - a >= 24 for a, b in zip(opens, opens[1:])))

    def test_daily_bar_completed_only_if_it_closed_before_the_hour_closed(self):
        # day 24 has a high of 120. While day 24 is running (including its last hour, whose close time equals the daily close time) that bar is not completed: level 100.
        d1 = flat_daily(26)
        d1["h"][24] = 120.0
        ev = S.replay_alert_b(hourly_after(24, [95] * 23 + [101.0]), d1)  # break at the last hour of day 24
        self.assertEqual([(e["side"], e["level"], e["ref"]) for e in ev], [("LONG", 100.0, 101.0)])
        # from the first hour of day 25 the bar of day 24 is completed: level 120
        ev2 = S.replay_alert_b(hourly_after(24, [95] * 24 + [95, 119.0, 121.0]), d1)
        self.assertEqual([(e["side"], e["level"], e["ref"]) for e in ev2], [("LONG", 120.0, 121.0)])

    def test_needs_21_completed_daily_bars(self):
        d1 = flat_daily(20)
        self.assertEqual(S.replay_alert_b(hourly_after(20, [95, 95, 101]), d1), [])


class TestOutcome(unittest.TestCase):
    def setup_long(self):
        d1 = flat_daily(25)
        h1 = hourly_after(25, [95, 95, 95, 96, 100, 102] + [102] * 200)
        ev = S.replay_alert_b(h1, d1)[0]
        return h1, ev

    def test_target_hit_r_net_formula(self):
        h1, ev = self.setup_long()
        h1["h"][ev["j"] + 3] = 125.0  # touches the target 122
        out = S.resolve(ev, h1)
        self.assertEqual(out["status"], "TARGET")
        self.assertAlmostEqual(out["r_gross"], 2.0, places=12)
        self.assertAlmostEqual(out["r_net"], (20.0 - 0.0016 * 102.0) / 10.0, places=12)
        self.assertEqual(out["hours"], 3.0)

    def test_stop_first_when_both_touched_on_one_bar(self):
        h1, ev = self.setup_long()
        h1["h"][ev["j"] + 2] = 130.0
        h1["l"][ev["j"] + 2] = 80.0
        out = S.resolve(ev, h1)
        self.assertEqual(out["status"], "STOP")
        self.assertTrue(out["both_touched"])
        self.assertAlmostEqual(out["r_gross"], -1.0, places=12)
        self.assertAlmostEqual(out["r_net"], (-10.0 - 0.0016 * 102.0) / 10.0, places=12)

    def test_short_signs(self):
        d1 = flat_daily(25)
        h1 = hourly_after(25, [95, 95, 95, 94, 90, 88] + [88] * 200)
        ev = S.replay_alert_b(h1, d1)[0]
        h1["l"][ev["j"] + 4] = 60.0  # target 68
        out = S.resolve(ev, h1)
        self.assertEqual(out["status"], "TARGET")
        self.assertAlmostEqual(out["r_net"], (20.0 - 0.0016 * 88.0) / 10.0, places=12)
        h1b = hourly_after(25, [95, 95, 95, 94, 90, 88] + [88] * 200)
        h1b["h"][ev["j"] + 1] = 99.0  # stop 98
        self.assertEqual(S.resolve(ev, h1b)["status"], "STOP")

    def test_expiry_at_close_168h_after_reference_close(self):
        h1, ev = self.setup_long()
        j = ev["j"]
        h1["c"][j + 168] = 105.0
        h1["h"][j + 168] = max(105.0, 102.0)
        out = S.resolve(ev, h1)
        self.assertEqual(out["status"], "EXPIRED")
        self.assertEqual(out["exit_ms"], int(h1["close_ms"][j + 168]))
        self.assertAlmostEqual(out["hours"], 168.0, places=9)
        self.assertAlmostEqual(out["r_gross"], 0.3, places=12)

    def test_pending_until_window_complete(self):
        d1 = flat_daily(25)
        h1 = hourly_after(25, [95, 95, 95, 96, 100, 102] + [102] * 50)
        ev = S.replay_alert_b(h1, d1)[0]
        out = S.resolve(ev, h1)
        self.assertEqual(out["status"], "PENDING")
        self.assertIsNone(out["r_net"])
        # a touch inside the incomplete window still resolves
        h1["l"][ev["j"] + 10] = 50.0
        self.assertEqual(S.resolve(ev, h1)["status"], "STOP")

    def test_alert_bar_itself_is_not_in_the_window(self):
        h1, ev = self.setup_long()
        h1["l"][ev["j"]] = 0.5  # the alert bar's own low must be ignored
        self.assertEqual(S.resolve(ev, h1)["status"], "EXPIRED")


class TestStats(unittest.TestCase):
    def trades(self, rs):
        out = []
        for i, r in enumerate(rs):
            out.append(dict(status="TARGET" if r > 0 else "STOP", r_net=r, exit_ms=(i + 1) * H, bar_open_ms=i * H, side="LONG", hours=2.0))
        return out

    def test_numbers(self):
        s = S.trade_stats(self.trades([1.9, -1.0, -1.0, 1.9, -1.0]), risk_frac=0.01)
        self.assertEqual(s["n"], 5)
        self.assertAlmostEqual(s["pct_profitable"], 0.4)
        self.assertAlmostEqual(s["sum_r"], 0.8)
        self.assertAlmostEqual(s["mean_r"], 0.16)
        self.assertAlmostEqual(s["profit_factor"], 3.8 / 3.0)
        self.assertEqual(s["max_losing_streak"], 2)
        eq = 1.0
        peak = 1.0
        dd = 0.0
        for r in [1.9, -1.0, -1.0, 1.9, -1.0]:
            eq *= 1 + 0.01 * r
            peak = max(peak, eq)
            dd = max(dd, (peak - eq) / peak)
        self.assertAlmostEqual(s["equity_end"], eq, places=12)
        self.assertAlmostEqual(s["equity_maxdd"], dd, places=12)

    def test_pending_excluded_and_empty(self):
        t = self.trades([1.0]) + [dict(status="PENDING", r_net=None, exit_ms=None, bar_open_ms=0, side="LONG", hours=None)]
        s = S.trade_stats(t)
        self.assertEqual((s["n"], s["pending"]), (1, 1))
        self.assertEqual(S.trade_stats([])["n"], 0)

    def test_baseline_alternates_sides_and_uses_same_resolver(self):
        d1 = flat_daily(30)
        h1 = hourly_after(30, [95.0] * 24 * 12)
        ev = S.baseline_events(h1, d1, step_h=24)
        self.assertEqual([e["side"] for e in ev][:4], ["LONG", "SHORT", "LONG", "SHORT"])
        res = [S.resolve(e, h1) for e in ev]
        self.assertTrue(all(r["status"] in ("EXPIRED", "PENDING") for r in res))  # flat price: nothing is touched


class TestEpisodes(unittest.TestCase):
    def make(self, n_up=320, n_down=120, seed=5, symbol="AAAUSDT"):
        u = TT.stream(seed)
        o_, h_, l_, c_ = [], [], [], []
        prev = 100.0
        for i in range(n_up + n_down):
            mu = 0.006 if i < n_up else -0.012
            r = mu + (next(u) - 0.5) * 0.02
            o = prev
            c = o * math.exp(r)
            h = max(o, c) * (1 + 0.003 * next(u))
            l = min(o, c) * (1 - 0.003 * next(u))
            o_.append(o); h_.append(h); l_.append(l); c_.append(c)
            prev = c
        n = len(c_)
        t = np.arange(n, dtype=np.int64) * D + 1_600_000_000_000 // D * D
        return dict(symbol=symbol, t=t, o=np.array(o_), h=np.array(h_), l=np.array(l_), c=np.array(c_), missing_days=0)

    def test_episode_returns_match_portfolio_bar_by_bar(self):
        d = self.make()
        eps, bar_r = S.episodes(d)
        G = T.grid({d["symbol"]: d})
        R, Hd, E = RB.port(G, [0], min_active=1)
        ok = np.isfinite(bar_r) & np.isfinite(R)
        self.assertGreater(ok.sum(), 100)
        np.testing.assert_allclose(bar_r[ok], R[ok], rtol=0, atol=1e-12)
        # product of all episode returns equals the compounded bar returns of the bars in an episode (bars outside any episode have return 0 except none)
        closed = [e for e in eps if e["status"] == "CLOSED"]
        self.assertGreaterEqual(len(closed), 1)
        prod = np.prod([1 + e["ret"] for e in closed])
        last_exit_idx = max(i for i, tt in enumerate(d["t"]) if iso(tt) == closed[-1]["exit"])
        bars = bar_r[:last_exit_idx + 1]
        self.assertAlmostEqual(prod, float(np.prod(1.0 + bars[np.isfinite(bars)])), places=10)

    def test_open_episode_marked_to_last_close(self):
        d = self.make(n_up=400, n_down=0)
        eps, _ = S.episodes(d)
        self.assertEqual(eps[-1]["status"], "OPEN")
        self.assertAlmostEqual(eps[-1]["exit_price"], float(d["c"][-1]))

    def test_downtrend_has_no_episode_after_exit(self):
        d = self.make()
        eps, _ = S.episodes(d)
        self.assertEqual(eps[-1]["status"], "CLOSED")
        self.assertGreater(eps[-1]["days"], 5)
        self.assertLessEqual(eps[-1]["avg_size"], 1.0 + 1e-12)

    def test_ep_stats(self):
        eps = [dict(status="CLOSED", ret=0.2, days=10), dict(status="CLOSED", ret=-0.05, days=4), dict(status="CLOSED", ret=-0.05, days=6), dict(status="OPEN", ret=0.5, days=3)]
        s = S.ep_stats(eps)
        self.assertEqual((s["n"], s["open"]), (3, 1))
        self.assertAlmostEqual(s["pct_profitable"], 1 / 3)
        self.assertAlmostEqual(s["profit_factor"], 0.2 / 0.1)
        self.assertAlmostEqual(s["avg_days"], 20 / 3)


def iso(ms):
    return S.iso_ms(ms)[:10]


class TestFetch(unittest.TestCase):
    def test_pagination_dedup_and_forming_bar_filter(self):
        ms = H
        total = 2500
        start = 1_600_000_000_000 // ms * ms
        rows = [[start + i * ms, "10", "11", "9", "10.5", "1", start + (i + 1) * ms - 1] for i in range(total)]
        now = start + 2400 * ms + 1000  # bars 0..2399 closed, 2400 is forming
        calls = []

        def fake_get(url, timeout=30):
            calls.append(url)
            q = dict(p.split("=") for p in url.split("?")[1].split("&"))
            s, e = int(q["startTime"]), int(q["endTime"])
            return json.dumps([r for r in rows if s <= r[0] <= e][:int(q["limit"])])

        d = S.fetch_interval("BTCUSDT", "1h", ms, start, now + 10 * ms, now, http_get=fake_get, sleep=lambda x: None)
        self.assertEqual(len(d["t"]), 2400)
        self.assertEqual(d["missing"], 0)
        self.assertGreaterEqual(len(calls), 3)
        self.assertTrue((d["close_ms"] < now).all())

    def test_rejects_bad_rows(self):
        base = 1_600_000_000_000 // H * H
        good = [[base + i * H, "10", "11", "9", "10", "1"] for i in range(3)]
        S.validate_bars("X", good, H, base + 10 * H)
        for bad in ([[base, "10", "9", "9", "10", "1"]], [[base, "0", "1", "0", "1", "1"]], [[base + 5, "10", "11", "9", "10", "1"]],
                    [[base, "10", "11", "9", "10", "1"], [base, "10", "11", "9", "10", "1"]]):
            with self.assertRaises(T.DataError):
                S.validate_bars("X", bad, H, base + 10 * H)

    def test_gap_counted(self):
        base = 1_600_000_000_000 // H * H
        rows = [[base + i * H, "10", "11", "9", "10", "1"] for i in (0, 1, 4)]
        self.assertEqual(S.validate_bars("X", rows, H, base + 100 * H)["missing"], 2)


class TestReproduction(unittest.TestCase):
    def test_reproduction_matches_and_misses(self):
        d1 = flat_daily(25)
        h1 = hourly_after(25, [95, 95, 95, 96, 100, 102] + [102] * 200)
        events = S.replay_alert_b(h1, d1)
        trades = {e["bar_open_ms"]: S.resolve(e, h1) for e in events}
        saved = S.LIVE_ALERTS
        try:
            e = events[0]
            S.LIVE_ALERTS = (dict(name="match", side="LONG", bar_open_ms=e["bar_open_ms"], ref=e["ref"], level=e["level"], atr=e["atr"], stop=e["stop"], target=e["target"], tol=1e-4, source="t"),
                             dict(name="miss", side="LONG", bar_open_ms=e["bar_open_ms"], ref=e["ref"] + 50, level=None, atr=None, stop=e["stop"], target=e["target"], tol=1e-4, source="t"))
            rows = S.reproduction(events, trades)
        finally:
            S.LIVE_ALERTS = saved
        self.assertEqual([r["reproduced"] for r in rows], [True, False])
        self.assertIn("status", rows[0])

    def test_break_suppressed_by_cooldown_is_found_raw_and_names_the_blocker(self):
        d1 = flat_daily(30)
        closes = [95, 95, 95, 101, 95, 95, 95, 95, 95, 95, 101]  # breaks at hours 3 and 10 (7 h apart)
        h1 = hourly_after(30, closes)
        events = S.replay_alert_b(h1, d1)
        raw = S.replay_alert_b(h1, d1, cooldown_ms=0)
        self.assertEqual((len(events), len(raw)), (1, 2))
        trades = {e["bar_open_ms"]: S.resolve(e, h1) for e in events}
        raw_trades = {e["bar_open_ms"]: S.resolve(e, h1) for e in raw}
        second = raw[1]
        saved = S.LIVE_ALERTS
        try:
            S.LIVE_ALERTS = (dict(name="second", side="LONG", bar_open_ms=second["bar_open_ms"], ref=second["ref"], level=second["level"], atr=second["atr"], stop=second["stop"],
                                  target=second["target"], tol=1e-4, source="t"),)
            row = S.reproduction(events, trades, raw, raw_trades)[0]
        finally:
            S.LIVE_ALERTS = saved
        self.assertFalse(row["reproduced"])
        self.assertTrue(row["reproduced_raw"])
        self.assertEqual(row["blocked_gap_hours"], 7.0)
        self.assertEqual(row["blocked_by"], S.iso_ms(events[0]["bar_open_ms"]) + " UTC")


class TestEndToEnd(unittest.TestCase):
    def test_build_runs_and_is_json_serialisable(self):
        # 450 days of hourly random walk for BTC; daily bars aggregated from it; six more coins as daily series
        u = TT.stream(21)
        n_h = 450 * 24
        px = 100.0
        o_, h_, l_, c_ = [], [], [], []
        for i in range(n_h):
            o = px
            px = o * math.exp((next(u) - 0.5) * 0.012 + 0.00002)
            o_.append(o); c_.append(px); h_.append(max(o, px) * (1 + 0.002 * next(u))); l_.append(min(o, px) * (1 - 0.002 * next(u)))
        t0 = 1_600_000_000_000 // D * D
        th = t0 + H * np.arange(n_h, dtype=np.int64)
        h1 = dict(symbol="BTCUSDT", t=th, o=np.array(o_), h=np.array(h_), l=np.array(l_), c=np.array(c_), close_ms=th + H - 1, missing=0)
        k = n_h // 24
        td = t0 + D * np.arange(k, dtype=np.int64)
        O, Hh, Ll, C = np.array(o_), np.array(h_), np.array(l_), np.array(c_)
        d1 = dict(symbol="BTCUSDT", t=td, o=O[::24][:k], h=Hh.reshape(k, 24).max(axis=1), l=Ll.reshape(k, 24).min(axis=1), c=C[23::24][:k], close_ms=td + D - 1, missing=0)
        datas = {}
        for i, s in enumerate(S.COINS7 + ("LINKUSDT",)):
            if s == "BTCUSDT":
                dd = dict(symbol=s, t=td, o=d1["o"], h=d1["h"], l=d1["l"], c=d1["c"], missing_days=0)
            else:
                g = TestEpisodes().make(n_up=250 + 10 * i, n_down=k - 250 - 10 * i, seed=30 + i, symbol=s)
                g["t"] = td.copy()
                dd = g
            datas[s] = dd
        asof = int(td[-1]) + D
        rep = S.build(h1, d1, datas, asof, notes=[], code_sha="x")
        text = json.dumps(rep)
        self.assertIn("reproduction", text)
        self.assertIn("episodes_7_all", rep["B"])
        self.assertGreaterEqual(rep["A"]["raw_breaks"], rep["A"]["alerts_total"])
        self.assertEqual(rep["C"]["active"], 7)
        self.assertGreater(rep["A"]["alerts_total"], 0)
        self.assertIn("BTC", rep["B"]["baskets"])
        md = S.summary_md(rep)
        self.assertIn("## A. Alert B replay", md)
        # every completed trade has an outcome consistent with its status
        for tr in rep["A"]["trades"]:
            if tr["status"] == "TARGET":
                self.assertAlmostEqual(tr["r_gross"], 2.0, places=9)
            if tr["status"] == "STOP":
                self.assertAlmostEqual(tr["r_gross"], -1.0, places=9)


if __name__ == "__main__":
    unittest.main(verbosity=1)
