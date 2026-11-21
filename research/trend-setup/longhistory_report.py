#!/usr/bin/env python3
"""Long-history STRUCTURE check of the FROZEN Trend Setup v0 rule (imports trendsetup.py unchanged; pre-registered in specs/trend-setup/PREREG_LONGHISTORY_v1.md).

The rule is applied, one market at a time, to public daily OHLC history that the lab never used for this rule family: 13 non-crypto markets (equity indices,
metal/energy/copper futures, a bond future) from 1970 or their first valid bar, and Bitstamp BTC/USD from 2011-09 to 2017-08-16 (before the Binance window).
Nothing is tuned. Annualisation is by observations per year of each series; the frozen code's sqrt(365) inside vol30 is left as is.
What a pass means: the rule behaves like a trend rule elsewhere (smaller drawdowns). It does NOT show that it will earn money in crypto going forward.
"""
from __future__ import annotations

import datetime as dt
import json
import math
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent))
import trendsetup as T  # noqa: E402

EPOCH_ORD = 719163  # date.toordinal() of 1970-01-01
START_DAY = dt.date(1970, 1, 1).toordinal() - EPOCH_ORD
END_DAY = dt.date(2026, 11, 19).toordinal() - EPOCH_ORD  # last complete bar before the paper track starts
BTC_END_DAY = dt.date(2017, 8, 16).toordinal() - EPOCH_ORD
MARKETS = (
    ("^GSPC", "S&P 500", "equity"), ("^IXIC", "Nasdaq Composite", "equity"), ("^DJI", "Dow Jones", "equity"), ("^N225", "Nikkei 225", "equity"),
    ("^FTSE", "FTSE 100", "equity"), ("^GDAXI", "DAX", "equity"), ("^HSI", "Hang Seng", "equity"), ("^FCHI", "CAC 40", "equity"),
    ("GC=F", "Gold futures", "commodity"), ("SI=F", "Silver futures", "commodity"), ("CL=F", "Crude oil futures", "commodity"), ("HG=F", "Copper futures", "commodity"),
    ("ZN=F", "10y Treasury note futures", "bond"),
)
MIN_YEARS = 10.0
P1_RATIO, P1_SHARE, P2_SHARE, P3_RATIO = 0.75, 0.70, 0.50, 0.75
MIN_ELIGIBLE = 8  # added after run 44920801539 produced a verdict on 2 markets; stricter, see the PREREG change log
BAD_SHARE_MAX = 0.01
YAHOO_HOSTS = ("query1.finance.yahoo.com", "query2.finance.yahoo.com")
YAHOO = "https://{host}/v8/finance/chart/{sym}?period1={p1}&period2={p2}&interval=1d&includePrePost=false"
CHUNK_DAYS = 8 * 365  # request daily bars in 8-year windows: a single range=max request was answered with MONTHLY bars (run 44920458906)
MAX_MEDIAN_GAP_DAYS = 4
BITSTAMP = "https://www.bitstamp.net/api/v2/ohlc/btcusd/?step=86400&limit=1000&start={start}"


class SourceError(Exception):
    pass


def http_get(url, timeout=40):
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0 (btc-signal-lab-longhistory/1)"})
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return r.read().decode("utf-8")


def iso(day):
    return dt.date.fromordinal(int(day) + EPOCH_ORD).isoformat()


def clean_rows(rows):
    """rows = (day, o, h, l, c). Keep strictly increasing days, finite positive prices, consistent OHLC. Returns arrays and the number of rejected rows."""
    seen, out, bad = set(), [], 0
    for day, o, h, l, c in sorted(rows, key=lambda r: r[0]):
        ok = day not in seen and all(v is not None and math.isfinite(v) and v > 0 for v in (o, h, l, c)) and h >= max(o, c) - 1e-12 * h and l <= min(o, c) + 1e-12 * l and h >= l
        if not ok:
            bad += 1
            continue
        seen.add(day)
        out.append((day, o, h, l, c))
    if not out:
        raise SourceError("no usable rows")
    a = np.array(out, dtype=float)
    return dict(day=a[:, 0].astype(np.int64), o=a[:, 1], h=a[:, 2], l=a[:, 3], c=a[:, 4]), bad, len(rows)


def parse_yahoo(text):
    j = json.loads(text)
    res = (j.get("chart") or {}).get("result")
    if not res:
        raise SourceError(f"no result ({str((j.get('chart') or {}).get('error'))[:100]})")
    r = res[0]
    off = int((r.get("meta") or {}).get("gmtoffset") or 0)
    q = r["indicators"]["quote"][0]
    rows = [((int(ts) + off) // 86400, q["open"][i], q["high"][i], q["low"][i], q["close"][i]) for i, ts in enumerate(r.get("timestamp") or [])]
    return rows


def require_daily(d, sym):
    """Guard added after run 44920458906: a series whose median gap between bars exceeds a few days is not daily data and must never be fed to the rule."""
    gaps = np.diff(d["day"])
    if len(gaps) == 0 or float(np.median(gaps)) > MAX_MEDIAN_GAP_DAYS:
        raise SourceError(f"{sym}: not daily bars (median gap {float(np.median(gaps)) if len(gaps) else 'n/a'} days)")


def _yahoo_chunk(sym, lo, hi, get, retries, sleep):
    last = None
    for k in range(retries):
        try:
            url = YAHOO.format(host=YAHOO_HOSTS[k % 2], sym=urllib.parse.quote(sym), p1=lo * 86400, p2=(hi + 1) * 86400)
            return parse_yahoo(get(url))
        except SourceError as e:  # an answer without data for this window (e.g. before the first trading day) is an empty window, not a failure
            if "no result" in str(e):
                return []
            last = f"SourceError {str(e)[:120]}"
        except urllib.error.HTTPError as e:
            if e.code in (400, 404):  # Yahoo answers HTTP 400 for a window that lies before the first trading day (run 44920801539)
                return []
            last = f"HTTPError {e.code}"
        except (urllib.error.URLError, OSError, ValueError, KeyError) as e:
            last = f"{type(e).__name__} {str(e)[:120]}"
        sleep(2.0 * (k + 1))
    raise SourceError(f"{sym}: {last}")


def fetch_yahoo(sym, get=http_get, retries=4, sleep=time.sleep):
    by_day, lo = {}, START_DAY
    while lo <= END_DAY:
        hi = min(lo + CHUNK_DAYS - 1, END_DAY)
        for r in _yahoo_chunk(sym, lo, hi, get, retries, sleep):
            if START_DAY <= r[0] <= END_DAY:
                by_day.setdefault(r[0], r)
        lo = hi + 1
        sleep(0.5)
    d, bad, total = clean_rows(list(by_day.values()))
    require_daily(d, sym)
    return d, bad, total


def fetch_bitstamp(get=http_get, retries=4, sleep=time.sleep):
    rows, start = [], int(dt.datetime(2011, 9, 1, tzinfo=dt.timezone.utc).timestamp())
    while True:
        last = None
        for k in range(retries):
            try:
                page = json.loads(get(BITSTAMP.format(start=start)))["data"]["ohlc"]
                break
            except (urllib.error.URLError, OSError, ValueError, KeyError) as e:
                last, page = f"{type(e).__name__} {str(e)[:100]}", None
                sleep(2.0 * (k + 1))
        if page is None:
            raise SourceError(f"bitstamp: {last}")
        if not page:
            break
        rows += [(int(p["timestamp"]) // 86400, float(p["open"]), float(p["high"]), float(p["low"]), float(p["close"])) for p in page]
        nxt = int(page[-1]["timestamp"]) + 86400
        if len(page) < 1000 or nxt <= start or nxt // 86400 > BTC_END_DAY:
            break
        start = nxt
        sleep(0.3)
    rows = [r for r in rows if r[0] <= BTC_END_DAY]
    d, bad, total = clean_rows(rows)
    require_daily(d, "bitstamp")
    return d, bad, total


def describe(days, r):
    """Descriptive stats of a return series with one observation per counted bar; annualised by observations per calendar year of the span."""
    x = np.asarray(r, dtype=float)
    n = len(x)
    if n < 30:
        return dict(obs=n)
    span = (int(days[-1]) - int(days[0]) + 1) / 365.25
    k = n / span
    eq = np.cumprod(1.0 + x)
    peak = np.maximum.accumulate(np.r_[1.0, eq])[1:]
    sd = x.std(ddof=1)
    return dict(obs=n, first=iso(days[0]), last=iso(days[-1]), years=float(span), obs_per_year=float(k), total=float(eq[-1] - 1), cagr=float(eq[-1] ** (1 / span) - 1),
                vol=float(sd * math.sqrt(k)), sharpe=float(x.mean() / sd * math.sqrt(k)) if sd > 0 else None, maxdd=float(((peak - eq) / peak).max()))


def evaluate(d, c_side=T.C_SIDE):
    """One market: weights from the frozen coin_calc, decided at the close of bar j-1, held from the open of j to the open of j+1 (same convention as trendsetup.paper_track).
    Returns day index, rule returns (after costs), hold returns (gross, always long, same bars), exposure."""
    cc = T.coin_calc(d)
    W, ready, o, day = cc["w"], cc["ready"], d["o"], d["day"]
    D, R, H, E = [], [], [], []
    for j in range(2, len(o) - 1):
        if not ready[j - 1]:
            continue
        ro = o[j + 1] / o[j] - 1.0
        R.append(W[j - 1] * ro - c_side * abs(W[j - 1] - W[j - 2]))
        H.append(ro)
        E.append(W[j - 1])
        D.append(day[j])
    return np.array(D, dtype=np.int64), np.array(R), np.array(H), np.array(E)


def market_block(sym, name, kind, d, bad, total):
    D, R, H, E = evaluate(d)
    if len(D) < 30:
        return dict(symbol=sym, name=name, kind=kind, status="TOO_SHORT", bars=int(len(d["c"])))
    row = dict(symbol=sym, name=name, kind=kind, status="OK", bars=int(len(d["c"])), first_bar=iso(d["day"][0]), last_bar=iso(d["day"][-1]), rejected_rows=int(bad), raw_rows=int(total),
               flat_bars_share=float(np.mean(d["h"] == d["l"])), rule=describe(D, R), hold=describe(D, H), avg_exposure=float(E.mean()), invested_share=float((E > 0).mean()))
    return row, (D, R, H)


def average_block(series):
    """Equal-weight average over the markets available on each date (rule and hold separately). Alignment is by calendar date of the bar."""
    if not series:
        return None
    days = sorted(set(int(x) for D, _, _ in series for x in D))
    idx = {d_: i for i, d_ in enumerate(days)}
    sr, sh, cnt = np.zeros(len(days)), np.zeros(len(days)), np.zeros(len(days))
    for D, R, H in series:
        ii = np.array([idx[int(x)] for x in D])
        sr[ii] += R
        sh[ii] += H
        cnt[ii] += 1
    keep = cnt >= 3
    days_a = np.array(days)[keep]
    return dict(markets=len(series), rule=describe(days_a, sr[keep] / cnt[keep]), hold=describe(days_a, sh[keep] / cnt[keep]))


def verdict(rows, btc):
    """The pre-registered criteria (PREREG_LONGHISTORY_v1.md), applied mechanically."""
    elig = [r for r in rows if r.get("status") == "OK" and r["rule"].get("years", 0) >= MIN_YEARS]
    out = dict(eligible=len(elig), markets_total=len(rows))
    if elig:
        p1 = [r["rule"]["maxdd"] <= P1_RATIO * r["hold"]["maxdd"] for r in elig]
        p2 = [(r["rule"]["sharpe"] or -9) >= (r["hold"]["sharpe"] or -9) for r in elig]
        out.update(p1_share=float(np.mean(p1)), p1_met=bool(np.mean(p1) >= P1_SHARE), p2_share=float(np.mean(p2)), p2_met=bool(np.mean(p2) >= P2_SHARE),
                   median_maxdd_ratio=float(np.median([r["rule"]["maxdd"] / r["hold"]["maxdd"] for r in elig])),
                   median_sharpe_diff=float(np.median([(r["rule"]["sharpe"] or 0) - (r["hold"]["sharpe"] or 0) for r in elig])))
        out["markets_verdict"] = "CONSISTENT" if (out["p1_met"] and out["p2_met"]) else ("PARTIAL" if out["p1_met"] else "NOT_CONSISTENT")
        if len(elig) < MIN_ELIGIBLE:
            out["markets_verdict"] = "INSUFFICIENT_DATA"
    else:
        out["markets_verdict"] = "NO_ELIGIBLE_MARKETS"
    if btc and btc.get("status") == "OK":
        out["p3_met"] = bool(btc["rule"]["maxdd"] <= P3_RATIO * btc["hold"]["maxdd"])
        out["btc_maxdd_ratio"] = float(btc["rule"]["maxdd"] / btc["hold"]["maxdd"])
    return out


def build(fetchers_ok=None):
    """fetchers_ok: optional dict sym -> (d, bad, total) for tests; otherwise fetch live."""
    rows, series, errors = [], [], []
    for sym, name, kind in MARKETS:
        if fetchers_ok is None:
            time.sleep(1.5)
        try:
            d, bad, total = fetchers_ok[sym] if fetchers_ok is not None else fetch_yahoo(sym)
        except (SourceError, KeyError) as e:
            rows.append(dict(symbol=sym, name=name, kind=kind, status="SOURCE_ERROR", reason=str(e)[:160]))
            print(f"{sym}: SOURCE_ERROR {str(e)[:160]}", flush=True)
            continue
        print(f"{sym}: fetched {total} rows, rejected {bad}", flush=True)
        if bad / max(total, 1) > BAD_SHARE_MAX:
            rows.append(dict(symbol=sym, name=name, kind=kind, status="EXCLUDED_BAD_DATA", rejected_rows=int(bad), raw_rows=int(total)))
            continue
        res = market_block(sym, name, kind, d, bad, total)
        if isinstance(res, dict):
            rows.append(res)
        else:
            rows.append(res[0]); series.append(res[1])
    btc = None
    try:
        d, bad, total = fetchers_ok["BTC-BITSTAMP"] if fetchers_ok is not None else fetch_bitstamp()
        res = market_block("BTCUSD-Bitstamp", "BTC/USD Bitstamp to 2017-08-16", "crypto_pre2017", d, bad, total)
        btc = res if isinstance(res, dict) else res[0]
    except (SourceError, KeyError) as e:
        btc = dict(symbol="BTCUSD-Bitstamp", status="SOURCE_ERROR", reason=str(e)[:160])
    return dict(version="trend-setup-v0-longhistory", code_sha256=T.code_sha256(), markets=rows, btc_pre2017=btc, average=average_block(series), verdict=verdict(rows, btc))


def pct(x):
    return "n/a" if x is None else f"{x * 100:+.1f}%"


def summary_md(rep):
    L = ["# Trend Setup v0: long-history structure check (frozen rule, unchanged)", "",
         "**Pre-registered descriptive check on history this lab never used for this rule. A pass is not evidence of future crypto returns; costs 0.08% per side everywhere; hold = always long, no cost.**", "",
         "| market | kind | first counted | years | rule per year | hold per year | rule Sharpe | hold Sharpe | rule max DD | hold max DD | avg exposure |", "|---|---|---|---|---|---|---|---|---|---|---|"]
    for r in rep["markets"] + ([rep["btc_pre2017"]] if rep["btc_pre2017"] else []):
        if r.get("status") != "OK":
            L.append(f"| {r.get('name', r['symbol'])} | {r.get('kind', '')} | {r['status']} {r.get('reason', '')} | | | | | | | | |")
            continue
        a, b = r["rule"], r["hold"]
        sh = lambda s: "n/a" if s.get("sharpe") is None else f"{s['sharpe']:.2f}"
        L.append(f"| {r['name']} | {r['kind']} | {a['first']} | {a['years']:.1f} | {pct(a['cagr'])} | {pct(b['cagr'])} | {sh(a)} | {sh(b)} | -{a['maxdd'] * 100:.0f}% | -{b['maxdd'] * 100:.0f}% | {r['avg_exposure'] * 100:.0f}% |")
    av = rep.get("average")
    if av and "cagr" not in av["rule"]:
        L += ["", f"Equal-weight average: too few overlapping observations ({av['rule'].get('obs', 0)}); not computed."]
    elif av:
        a, b = av["rule"], av["hold"]
        L += ["", f"Equal-weight average of {av['markets']} non-crypto markets by date: rule {pct(a['cagr'])} per year, Sharpe {a['sharpe']:.2f}, max DD -{a['maxdd'] * 100:.0f}%; hold {pct(b['cagr'])}, Sharpe {b['sharpe']:.2f}, max DD -{b['maxdd'] * 100:.0f}% ({a['first']} to {a['last']})."]
    v = rep["verdict"]
    L += ["", "## Pre-registered criteria", f"- eligible markets (>= {MIN_YEARS:.0f} counted years): {v['eligible']} of {v['markets_total']} (a verdict needs at least {MIN_ELIGIBLE})"]
    if v["eligible"]:
        L += [f"- P1 rule max DD <= {P1_RATIO:.2f} x hold max DD in >= {P1_SHARE * 100:.0f}% of eligible markets: {v['p1_share'] * 100:.0f}% -> {'MET' if v['p1_met'] else 'NOT MET'}",
              f"- P2 rule Sharpe >= hold Sharpe in >= {P2_SHARE * 100:.0f}%: {v['p2_share'] * 100:.0f}% -> {'MET' if v['p2_met'] else 'NOT MET'}",
              f"- median max-DD ratio (rule / hold): {v['median_maxdd_ratio']:.2f}; median Sharpe difference (rule - hold): {v['median_sharpe_diff']:+.2f}"]
    L.append(f"- markets verdict: {v['markets_verdict']}")
    if "p3_met" in v:
        L.append(f"- P3 BTC 2011-2017: rule max DD <= {P3_RATIO:.2f} x hold: ratio {v['btc_maxdd_ratio']:.2f} -> {'MET' if v['p3_met'] else 'NOT MET'}")
    return "\n".join(L)


def main(argv):
    opts = dict(zip(argv[1::2], argv[2::2]))
    outdir = Path(opts.get("--out", "longhistory_out"))
    outdir.mkdir(parents=True, exist_ok=True)
    rep = build()
    (outdir / "longhistory.json").write_text(json.dumps(rep, separators=(",", ":")), encoding="utf-8")
    print("LONGHISTORY_JSON_BEGIN")
    print(json.dumps(rep, separators=(",", ":")))
    print("LONGHISTORY_JSON_END")
    md = summary_md(rep)
    (outdir / "longhistory.md").write_text(md, encoding="utf-8")
    print(md)
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
