#!/usr/bin/env python3
"""Synthetic tests for longhistory_report.py. Same author as the code: they show the tool does what it says (parsing, the single-market evaluation equals the frozen
paper track, annualisation, the mechanical criteria), not that the rule earns money.
Run: python -I -B research/trend-setup/test_longhistory_report.py
"""
import json
import sys
import unittest
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import longhistory_report as L  # noqa: E402
import test_trendsetup as TT  # noqa: E402
import trendsetup as T  # noqa: E402


def to_market(d, day0=10000):
    n = len(d["c"])
    return dict(day=day0 + np.arange(n, dtype=np.int64), o=d["o"], h=d["h"], l=d["l"], c=d["c"])


class Parsing(unittest.TestCase):
    def test_yahoo_rows_none_duplicates_and_bad_ohlc(self):
        ts0 = 86400 * 12000
        payload = {"chart": {"result": [{"meta": {"gmtoffset": 3600}, "timestamp": [ts0, ts0 + 86400, ts0 + 86400 * 2, ts0 + 86400 * 2, ts0 + 86400 * 3, ts0 + 86400 * 4, ts0 + 86400 * 5],
                                          "indicators": {"quote": [{"open": [10, None, 10, 10, 10, 10, None], "high": [11, 11, 11, 11, 9, 11, None], "low": [9, 9, 9, 9, 8, 9, None], "close": [10.5, 10, 10.5, 10.5, 10, 10.5, None]}]}}]}}
        rows = L.parse_yahoo(json.dumps(payload))
        self.assertEqual(rows[0][0], 12000)  # gmtoffset 3600 does not cross midnight
        d, bad, total = L.clean_rows(rows)
        self.assertEqual(total, 6)  # the all-missing row is a holiday placeholder and is not counted
        self.assertEqual(bad, 3)  # partly missing row, duplicate day, high below open
        self.assertEqual(d["rejected_by"], dict(partial_missing=1, non_positive_or_non_finite=0, inconsistent_ohlc=1, duplicate_day=1, placeholder_rows_dropped=1))
        self.assertEqual(list(d["day"]), [12000, 12002, 12004])

    def test_yahoo_error_payload(self):
        with self.assertRaises(L.SourceError):
            L.parse_yahoo(json.dumps({"chart": {"result": None, "error": {"code": "Not Found"}}}))

    def test_fetch_yahoo_retries_then_fails_cleanly(self):
        calls = []

        def get(url, timeout=40):
            calls.append(url)
            raise OSError("boom")
        with self.assertRaises(L.SourceError):
            L.fetch_yahoo("^GSPC", get=get, retries=3, sleep=lambda s: None)
        self.assertEqual(len(calls), 3)
        self.assertIn("%5EGSPC", calls[0])

    def test_fetch_yahoo_requests_daily_windows_and_tolerates_empty_early_windows(self):
        urls = []
        first_trading = 5000  # days since 1970: earlier windows answer "no result"

        def get(url, timeout=40):
            urls.append(url)
            p1 = int(url.split("period1=")[1].split("&")[0]) // 86400
            p2 = int(url.split("period2=")[1].split("&")[0]) // 86400
            days = [x for x in range(max(p1, first_trading), p2) if x % 7 not in (5, 6)]
            if not days:
                return json.dumps({"chart": {"result": None, "error": {"code": "Not Found"}}})
            q = {"open": [10.0] * len(days), "high": [11.0] * len(days), "low": [9.0] * len(days), "close": [10.5] * len(days)}
            return json.dumps({"chart": {"result": [{"meta": {"gmtoffset": 0}, "timestamp": [x * 86400 for x in days], "indicators": {"quote": [q]}}]}})
        d, bad, total = L.fetch_yahoo("^GSPC", get=get, sleep=lambda s: None)
        self.assertTrue(all("interval=1d" in u and "period1=" in u for u in urls))
        self.assertGreaterEqual(len(urls), 7)  # 1970 .. 2026 in 8-year windows
        self.assertEqual(int(d["day"][0]) >= first_trading, True)
        self.assertEqual(bad, 0)
        self.assertEqual(len(set(d["day"].tolist())), len(d["day"]))
        self.assertLessEqual(int(d["day"][-1]), L.END_DAY)

    def test_http_400_for_windows_before_the_first_trading_day_is_an_empty_window(self):
        first_trading = 11000

        def get(url, timeout=40):
            p1 = int(url.split("period1=")[1].split("&")[0]) // 86400
            p2 = int(url.split("period2=")[1].split("&")[0]) // 86400
            days = [x for x in range(max(p1, first_trading), p2) if x % 7 not in (5, 6)]
            if not days:
                raise L.urllib.error.HTTPError(url, 400, "Bad Request", {}, None)
            q = {"open": [10.0] * len(days), "high": [11.0] * len(days), "low": [9.0] * len(days), "close": [10.5] * len(days)}
            return json.dumps({"chart": {"result": [{"meta": {"gmtoffset": 0}, "timestamp": [x * 86400 for x in days], "indicators": {"quote": [q]}}]}})
        d, bad, total = L.fetch_yahoo("^DJI", get=get, sleep=lambda s: None)
        self.assertGreaterEqual(int(d["day"][0]), first_trading)
        # a persistent server error (500) is still a failure
        def boom(url, timeout=40):
            raise L.urllib.error.HTTPError(url, 500, "Server Error", {}, None)
        with self.assertRaises(L.SourceError):
            L.fetch_yahoo("^DJI", get=boom, retries=2, sleep=lambda s: None)

    def test_monthly_bars_are_refused(self):
        def get(url, timeout=40):
            p1 = int(url.split("period1=")[1].split("&")[0]) // 86400
            p2 = int(url.split("period2=")[1].split("&")[0]) // 86400
            days = list(range(max(p1, 6000), p2, 30))  # a source that answers with monthly bars whatever was asked
            if not days:
                return json.dumps({"chart": {"result": None, "error": {}}})
            q = {"open": [10.0] * len(days), "high": [11.0] * len(days), "low": [9.0] * len(days), "close": [10.5] * len(days)}
            return json.dumps({"chart": {"result": [{"meta": {"gmtoffset": 0}, "timestamp": [x * 86400 for x in days], "indicators": {"quote": [q]}}]}})
        with self.assertRaises(L.SourceError) as cm:
            L.fetch_yahoo("^DJI", get=get, sleep=lambda s: None)
        self.assertIn("not daily", str(cm.exception))

    def test_bitstamp_pagination_and_end_cut(self):
        base = int(__import__("datetime").datetime(2011, 9, 1, tzinfo=__import__("datetime").timezone.utc).timestamp())
        end_ts = (L.BTC_END_DAY + 5) * 86400
        pages = []

        def get(url, timeout=40):
            start = int(url.split("start=")[1])
            pages.append(start)
            ts = list(range(start, min(start + 1000 * 86400, end_ts + 86400), 86400))
            return json.dumps({"data": {"ohlc": [{"timestamp": str(t), "open": "10", "high": "11", "low": "9", "close": "10", "volume": "1"} for t in ts]}})
        d, bad, total = L.fetch_bitstamp(get=get, sleep=lambda s: None)
        self.assertGreaterEqual(len(pages), 2)
        self.assertEqual(int(d["day"][-1]), L.BTC_END_DAY)  # later rows are cut
        self.assertEqual(bad, 0)
        self.assertTrue((np.diff(d["day"]) == 1).all())
        self.assertEqual(pages[0], base)


class Evaluation(unittest.TestCase):
    def test_single_market_equals_frozen_paper_track(self):
        """Three identical coins through trendsetup.paper_track (start_flat=False, all days counted) = one market through evaluate()."""
        d = TT.synth(1, 700, 7, 0)["C0USDT"]
        datas = {f"C{k}USDT": dict(d, symbol=f"C{k}USDT") for k in range(3)}
        tr = T.paper_track(datas, t0_ms=0, start_flat=False)
        m = to_market(d, day0=int(d["t"][0] // T.DAY_MS))
        D, R, H, E = L.evaluate(m)
        by_day = {int(t // T.DAY_MS): r for t, r in zip(tr["t"], tr["R"])}
        got = np.array([by_day[int(x)] for x in D])
        self.assertTrue(np.isfinite(got).all())
        self.assertLess(float(np.max(np.abs(got - R))), 1e-12)
        self.assertEqual(int(np.isfinite(tr["R"]).sum()), len(D))

    def test_hold_is_open_to_open_on_the_same_bars_and_no_lookahead(self):
        d = TT.synth(1, 500, 11, 0)["C0USDT"]
        m = to_market(d)
        D, R, H, E = L.evaluate(m)
        j0 = int(D[0] - m["day"][0])
        self.assertEqual(j0, T.WARMUP_BARS + 1)  # first counted bar is the one after the first ready bar
        self.assertAlmostEqual(H[0], m["o"][j0 + 1] / m["o"][j0] - 1.0, places=14)
        # changing the FUTURE (everything from bar j0+5 on) must not change the first returns
        m2 = {k: (v.copy() if isinstance(v, np.ndarray) else v) for k, v in m.items()}
        cut = j0 + 5
        for k in ("o", "h", "l", "c"):
            m2[k][cut:] = m2[k][cut:] * 1.37
        m2["h"] = np.maximum.reduce([m2["h"], m2["o"], m2["c"]]); m2["l"] = np.minimum.reduce([m2["l"], m2["o"], m2["c"]])
        D2, R2, H2, E2 = L.evaluate(m2)
        self.assertLess(float(np.max(np.abs(R2[:3] - R[:3]))), 1e-15)  # bar cut-1 uses open[cut] only for the return of bar cut-1
        self.assertTrue(np.array_equal(E2[:4], E[:4]))

    def test_flat_in_a_falling_market_and_close_to_hold_in_a_steady_rise(self):
        n = 900
        c = 100.0 * (1 + 0.002) ** np.arange(1, n + 1)
        up = dict(day=np.arange(n, dtype=np.int64) + 1000, o=np.r_[100.0, c[:-1]], h=np.maximum(np.r_[100.0, c[:-1]], c) * 1.0001, l=np.minimum(np.r_[100.0, c[:-1]], c) * 0.9999, c=c)
        D, R, H, E = L.evaluate(up)
        self.assertGreater(E.mean(), 0.9)
        self.assertGreater(float(np.prod(1 + R) / np.prod(1 + H)), 0.97)
        dn = dict(up, c=c[::-1].copy(), o=np.r_[c[::-1][0], c[::-1][:-1]])
        dn["h"] = np.maximum(dn["o"], dn["c"]) * 1.0001
        dn["l"] = np.minimum(dn["o"], dn["c"]) * 0.9999
        D, R, H, E = L.evaluate(dn)
        self.assertLess(E.mean(), 0.05)


class Statistics(unittest.TestCase):
    def test_annualisation_uses_observations_per_year(self):
        days = np.array([d for d in range(1000, 1000 + 365 * 10) if (d % 7) not in (5, 6)])
        r = np.full(len(days), 0.001)
        r[::2] = 0.002  # variable so sd > 0
        s = L.describe(days, r)
        self.assertTrue(250 < s["obs_per_year"] < 266)
        self.assertAlmostEqual(s["sharpe"], float(r.mean() / r.std(ddof=1) * np.sqrt(s["obs_per_year"])), places=9)

    def test_maxdd_and_cagr(self):
        days = np.arange(2000, 2000 + 730)
        r = np.zeros(730)
        r[100] = -0.5
        r[200] = 1.0
        s = L.describe(days, r)
        self.assertAlmostEqual(s["maxdd"], 0.5, places=12)
        self.assertAlmostEqual(s["total"], 0.0, places=12)

    def test_average_aligns_by_date_and_needs_three_markets(self):
        mk = lambda off: (np.arange(off, off + 40, dtype=np.int64), np.full(40, 0.01), np.full(40, 0.02))
        av = L.average_block([mk(0), mk(0), mk(0), mk(20)])
        self.assertEqual(av["markets"], 4)
        self.assertEqual(av["rule"]["obs"], 40)  # days 0..39 have >= 3 markets; days 40..59 have only one and are dropped

    def test_average_value(self):
        a = (np.arange(0, 40, dtype=np.int64), np.full(40, 0.01), np.full(40, 0.02))
        b = (np.arange(0, 40, dtype=np.int64), np.full(40, 0.03), np.full(40, 0.00))
        c = (np.arange(0, 40, dtype=np.int64), np.full(40, 0.02), np.full(40, 0.01))
        av = L.average_block([a, b, c])
        self.assertAlmostEqual(av["rule"]["total"], 1.02 ** 40 - 1, places=9)
        self.assertAlmostEqual(av["hold"]["total"], 1.01 ** 40 - 1, places=9)


class Summary(unittest.TestCase):
    def test_summary_survives_when_almost_every_source_failed(self):
        rows = [dict(symbol=sym, name=n, kind=k, status="SOURCE_ERROR", reason="429") for sym, n, k in L.MARKETS]
        rep = dict(markets=rows, btc_pre2017=dict(symbol="BTCUSD-Bitstamp", status="SOURCE_ERROR", reason="x"), average=dict(markets=2, rule=dict(obs=5), hold=dict(obs=5)),
                   verdict=L.verdict(rows, None))
        md = L.summary_md(rep)
        self.assertIn("too few overlapping", md)
        self.assertIn("NO_ELIGIBLE_MARKETS", md)


class Verdict(unittest.TestCase):
    @staticmethod
    def row(rdd, hdd, rsh, hsh, years=12.0):
        return dict(status="OK", rule=dict(years=years, maxdd=rdd, sharpe=rsh), hold=dict(years=years, maxdd=hdd, sharpe=hsh))

    def test_consistent(self):
        rows = [self.row(0.3, 0.6, 0.6, 0.5)] * 8 + [self.row(0.5, 0.6, 0.4, 0.5)] * 2
        v = L.verdict(rows, dict(status="OK", rule=dict(maxdd=0.5), hold=dict(maxdd=0.9)))
        self.assertTrue(v["p1_met"] and v["p2_met"])
        self.assertEqual(v["markets_verdict"], "CONSISTENT")
        self.assertTrue(v["p3_met"])

    def test_partial_and_not_consistent(self):
        rows = [self.row(0.3, 0.6, 0.3, 0.5)] * 8 + [self.row(0.5, 0.6, 0.6, 0.5)] * 2
        self.assertEqual(L.verdict(rows, None)["markets_verdict"], "PARTIAL")
        rows = [self.row(0.55, 0.6, 0.3, 0.5)] * 10
        self.assertEqual(L.verdict(rows, None)["markets_verdict"], "NOT_CONSISTENT")

    def test_too_few_eligible_markets_give_no_verdict(self):
        rows = [self.row(0.3, 0.6, 0.6, 0.5)] * 7
        v = L.verdict(rows, None)
        self.assertEqual(v["eligible"], 7)
        self.assertEqual(v["markets_verdict"], "INSUFFICIENT_DATA")
        self.assertEqual(L.verdict(rows + [self.row(0.3, 0.6, 0.6, 0.5)], None)["markets_verdict"], "CONSISTENT")

    def test_short_markets_are_not_eligible(self):
        v = L.verdict([self.row(0.3, 0.6, 0.6, 0.5, years=5.0)] * 5, None)
        self.assertEqual(v["eligible"], 0)
        self.assertEqual(v["markets_verdict"], "NO_ELIGIBLE_MARKETS")

    def test_thresholds_are_the_preregistered_numbers(self):
        self.assertEqual((L.MIN_YEARS, L.P1_RATIO, L.P1_SHARE, L.P2_SHARE, L.P3_RATIO, L.MIN_ELIGIBLE), (10.0, 0.75, 0.70, 0.50, 0.75, 8))
        self.assertEqual(len(L.MARKETS), 13)
        self.assertEqual(L.iso(L.END_DAY), "2026-11-19")
        self.assertEqual(L.iso(L.BTC_END_DAY), "2017-08-16")


class EndToEnd(unittest.TestCase):
    def test_build_with_injected_data_and_source_errors(self):
        feeds = {}
        for k, (sym, _, _) in enumerate(L.MARKETS):
            d = TT.synth(1, 4500, 100 + k, 0)["C0USDT"]
            feeds[sym] = (to_market(d, day0=3650), 0, len(d["c"]))
        del feeds["SI=F"]  # missing source -> reported, not fatal
        feeds["CL=F"] = (feeds["CL=F"][0], 100, 4500)  # > 1% rejected rows -> excluded
        feeds["BTC-BITSTAMP"] = (to_market(TT.synth(1, 2000, 5, 0)["C0USDT"], day0=15000), 0, 2000)
        rep = L.build(feeds)
        st = {r["symbol"]: r["status"] for r in rep["markets"]}
        self.assertEqual(st["SI=F"], "SOURCE_ERROR")
        self.assertEqual(st["CL=F"], "EXCLUDED_BAD_DATA")
        self.assertEqual(sum(1 for v in st.values() if v == "OK"), 11)
        self.assertEqual(rep["btc_pre2017"]["status"], "OK")
        self.assertEqual(rep["verdict"]["eligible"], 11)
        self.assertEqual(rep["code_sha256"], T.code_sha256())
        md = L.summary_md(rep)
        self.assertIn("markets verdict", md)
        json.dumps(rep)  # serialisable


if __name__ == "__main__":
    unittest.main()
