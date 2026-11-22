#!/usr/bin/env python3
"""Does a MIRRORED short side of the frozen Trend Setup v0 rule add anything? (pre-registered in specs/trend-setup/PREREG_SHORTSIDE_v1.md)

Short mirror, no new parameters: five short states with the same windows N = 10, 20, 30, 55, 100; a short state turns on when close < min(low of the previous N bars)
and off when close > max(high of the previous N//2 bars) (the frozen donchian_state applied to the negated, swapped series). Short signal = mean of the five short
states; weights: long leg = signal_long x vol scale (the frozen weight), short leg = -signal_short x the same vol scale; long-short = long leg + short leg.
Costs 0.08% per side on weight changes; funding, borrow and margin are NOT modelled. Imports trendsetup.py and longhistory_report.py unchanged.
"""
from __future__ import annotations

import calendar
import json
import sys
import time
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent))
import longhistory_report as LH  # noqa: E402
import robustness_report as RB  # noqa: E402
import trendsetup as T  # noqa: E402

DAY = T.DAY_MS
MIN_YEARS, MIN_ELIGIBLE, S_SHARE = LH.MIN_YEARS, LH.MIN_ELIGIBLE, 0.50
FROM_2023_MS = int(calendar.timegm((2023, 1, 1, 0, 0, 0)) * 1000)
BASKETS = (1, 2, 5, 10, 26)  # the first n coins of the fixed UNIVERSE order (fixed before any result)
ALERT_WINDOW = 730  # "recent" alert frequency = the last 730 daily bars of each coin


def short_states(d):
    """Mirror of the frozen long state: donchian_state on (-low, -high, -close)."""
    return np.column_stack([T.donchian_state(-d["l"], -d["h"], -d["c"], N) for N in T.ENS_N])


def calc(d):
    cc = T.coin_calc(d)
    sig_s = short_states(d).mean(axis=1)
    wS = np.where(cc["ready"], sig_s * cc["scale"], 0.0)  # positive number = size of the short leg
    return dict(ready=cc["ready"], sig_l=cc["sig"], sig_s=sig_s, wL=cc["w"], wS=wS, wLS=cc["w"] - wS)


def evaluate(d, c_side=T.C_SIDE):
    """One market. Decision at the close of bar j-1, held from the open of j to the open of j+1 (the frozen convention). Returns day, long-only, short-only, long-short and
    hold returns plus the share of counted bars with a long and with a short position."""
    k = calc(d)
    o, day, ready = d["o"], d["day"], k["ready"]
    D, RL, RS, RLS, H, SL, SS = [], [], [], [], [], [], []
    for j in range(2, len(o) - 1):
        if not ready[j - 1]:
            continue
        ro = o[j + 1] / o[j] - 1.0
        wl1, wl2 = k["wL"][j - 1], k["wL"][j - 2]
        ws1, ws2 = -k["wS"][j - 1], -k["wS"][j - 2]
        D.append(day[j]); H.append(ro)
        RL.append(wl1 * ro - c_side * abs(wl1 - wl2))
        RS.append(ws1 * ro - c_side * abs(ws1 - ws2))
        RLS.append((wl1 + ws1) * ro - c_side * abs((wl1 + ws1) - (wl2 + ws2)))
        SL.append(wl1 > 0); SS.append(ws1 < 0)
    return dict(day=np.array(D, dtype=np.int64), L=np.array(RL), S=np.array(RS), LS=np.array(RLS), hold=np.array(H), long_share=float(np.mean(SL)) if SL else 0.0, short_share=float(np.mean(SS)) if SS else 0.0)


def direction_state(sig_l, sig_s, ready, long_only=False):
    """+1 long, -1 short, 0 flat. Direction = sign of (long signal - short signal); long-only = sign of the long signal. Bars before warm-up are 0 and never counted."""
    net = np.asarray(sig_l) if long_only else np.asarray(sig_l) - np.asarray(sig_s)
    st = np.where(net > 1e-12, 1, np.where(net < -1e-12, -1, 0))
    return np.where(ready, st, 0)


def alert_counts(state, ready, lo=1):
    """Direction-change alerts on bars i >= max(lo, 1) with bars i and i-1 both ready: enter_long (0 -> +1), enter_short (0 -> -1), flip (+1 <-> -1), exit (+-1 -> 0).
    Size changes inside one direction are NOT alerts."""
    c = dict(enter_long=0, enter_short=0, flip=0, exit=0)
    for i in range(max(lo, 1), len(state)):
        if not (ready[i] and ready[i - 1]) or state[i] == state[i - 1]:
            continue
        a, b = state[i - 1], state[i]
        if a == 0:
            c["enter_long" if b > 0 else "enter_short"] += 1
        elif b == 0:
            c["exit"] += 1
        else:
            c["flip"] += 1
    c["total"] = c["enter_long"] + c["enter_short"] + c["flip"] + c["exit"]
    return c


def coin_alerts(d, window=ALERT_WINDOW):
    k = calc(d)
    ready = k["ready"]
    n = len(ready)
    sets = dict(LS=direction_state(k["sig_l"], k["sig_s"], ready), L=direction_state(k["sig_l"], k["sig_s"], ready, long_only=True))
    out = {}
    for label, lo in (("full", 1), ("last2y", max(1, n - window))):
        bars = int(ready[max(lo, 1):].sum())
        out[label] = dict(bars=bars, **{name: alert_counts(st, ready, lo) for name, st in sets.items()})
    return out


def alert_baskets(datas):
    """Alerts per week for the first n coins of the fixed order: sum of alerts over the members / (mean counted years of the members x 52)."""
    order = [s for s in T.UNIVERSE if s in datas]
    per = {s: coin_alerts(datas[s]) for s in order}
    out = []
    for nb in BASKETS:
        mem = order[:nb]
        row = dict(n=len(mem), members=mem)
        for label in ("full", "last2y"):
            yrs = float(np.mean([per[s][label]["bars"] for s in mem])) / 365.0
            for name in ("LS", "L"):
                tot = sum(per[s][label][name]["total"] for s in mem)
                row[f"{label}_{name}_per_week"] = float(tot / (yrs * 52.0)) if yrs > 0 else None
            if label == "full":
                for kind in ("enter_long", "enter_short", "flip", "exit"):
                    row[f"full_LS_{kind}_per_week"] = float(sum(per[s]["full"]["LS"][kind] for s in mem) / (yrs * 52.0)) if yrs > 0 else None
        out.append(row)
    return out


def market_row(sym, name, kind, d, bad, total):
    e = evaluate(d)
    if len(e["day"]) < 30:
        return dict(symbol=sym, name=name, kind=kind, status="TOO_SHORT")
    desc = {k: LH.describe(e["day"], e[k]) for k in ("L", "S", "LS", "hold")}
    return dict(symbol=sym, name=name, kind=kind, status="OK", rejected_rows=int(bad), raw_rows=int(total), first=desc["L"]["first"], years=desc["L"]["years"],
                long_share=e["long_share"], short_share=e["short_share"], **desc)


def noncrypto(fetched=None):
    rows, errors = [], []
    for sym, name, kind in LH.MARKETS:
        if fetched is None:
            time.sleep(1.5)
        try:
            d, bad, total = fetched[sym] if fetched is not None else LH.fetch_yahoo(sym)
        except (LH.SourceError, KeyError) as e:
            rows.append(dict(symbol=sym, name=name, kind=kind, status="SOURCE_ERROR", reason=str(e)[:120]))
            continue
        if bad / max(total, 1) > LH.BAD_SHARE_MAX:
            rows.append(dict(symbol=sym, name=name, kind=kind, status="EXCLUDED_BAD_DATA", rejected_rows=int(bad), raw_rows=int(total)))
            continue
        rows.append(market_row(sym, name, kind, d, bad, total))
    try:
        d, bad, total = fetched["BTC-BITSTAMP"] if fetched is not None else LH.fetch_bitstamp()
        btc = market_row("BTCUSD-Bitstamp", "BTC/USD Bitstamp to 2017-08-16", "crypto_pre2017", d, bad, total)
    except (LH.SourceError, KeyError) as e:
        btc = dict(symbol="BTCUSD-Bitstamp", status="SOURCE_ERROR", reason=str(e)[:120])
    return rows, btc


def crypto(datas):
    """The 26-coin universe, equal weight over active coins, exactly as trendsetup.paper_track (start_flat=False) but with three weight sets."""
    G = T.grid(datas)
    names, t_min = G["names"], int(G["t"][0])
    WL, WS = np.full_like(G["W"], np.nan), np.full_like(G["W"], np.nan)
    for a, s in enumerate(names):
        d = datas[s]
        k = calc(d)
        idx = ((d["t"] - t_min) // DAY).astype(int)
        WL[idx, a], WS[idx, a] = k["wL"], -k["wS"]
    sets = dict(L=dict(G, W=WL), S=dict(G, W=WS), LS=dict(G, W=np.where(np.isnan(WL), np.nan, WL + np.nan_to_num(WS))))
    out = {}
    for label, cols in (("all", list(range(len(names)))), ("btc", [names.index("BTCUSDT")])):
        ms = 3 if len(cols) >= 3 else 1
        res = {}
        for per, lo in (("full", None), ("from2023", FROM_2023_MS)):
            row = {}
            hold = None
            for key, Gk in sets.items():
                r, h, e = RB.port(Gk, cols, min_active=ms)
                row[key] = RB.brief(*RB.cut(G["t"], r, lo))
                hold = h
            row["hold"] = RB.brief(*RB.cut(G["t"], hold, lo))
            res[per] = row
        out[label] = dict(coins=len(cols), results=res)
    return out


def verdict(rows, cry):
    elig = [r for r in rows if r.get("status") == "OK" and r["L"].get("years", 0) >= MIN_YEARS]
    v = dict(eligible=len(elig), markets_total=len(rows))
    if len(elig) >= MIN_ELIGIBLE:
        v["s1_share"] = float(np.mean([(r["LS"]["sharpe"] or -9) >= (r["L"]["sharpe"] or -9) for r in elig]))
        v["s2_share"] = float(np.mean([r["S"]["total"] > 0 for r in elig]))
        v["s1_met"], v["s2_met"] = bool(v["s1_share"] >= S_SHARE), bool(v["s2_share"] >= S_SHARE)
    else:
        v["s1_met"] = v["s2_met"] = None
    ok = True
    for per in ("full", "from2023"):
        r = cry["all"]["results"][per]
        ok = ok and (r["S"].get("total") is not None and r["S"]["total"] > 0) and (r["LS"].get("sharpe") or -9) >= (r["L"].get("sharpe") or -9)
    v["s3_met"] = bool(ok)
    flags = [v["s1_met"], v["s2_met"], v["s3_met"]]
    if None in flags:
        v["verdict"] = "INSUFFICIENT_DATA"
    elif all(flags):
        v["verdict"] = "SUPPORTED"
    elif any(flags):
        v["verdict"] = "MIXED"
    else:
        v["verdict"] = "NOT_SUPPORTED"
    return v


def build(datas, notes, code_sha, fetched=None):
    rows, btc = noncrypto(fetched)
    cry = crypto(datas)
    return dict(version="trend-setup-v0-shortside", code_sha256=code_sha, markets=rows, btc_pre2017=btc, crypto=cry, alerts=alert_baskets(datas), verdict=verdict(rows, cry), notes=notes)


def pc(x, d=1):
    return "n/a" if x is None else f"{x * 100:+.{d}f}%"


def sh(x):
    return "n/a" if x.get("sharpe") is None else f"{x['sharpe']:.2f}"


def summary_md(rep):
    L = ["# Trend Setup v0: mirrored short side (pre-registered, descriptive)", "",
         "**Same author; synthetic tests only; funding, borrow and margin not modelled; the crypto sample is in-sample and burned for this rule family. Nothing is evidence of future returns.**", "",
         "## Crypto universe (26 coins, equal weight over active coins)", "", "| basket | period | long-only per yr | short leg per yr | long-short per yr | long-only Sharpe | short leg Sharpe | long-short Sharpe | long-only max DD | long-short max DD | hold per yr |", "|---|---|---|---|---|---|---|---|---|---|---|"]
    for lab, c in rep["crypto"].items():
        for per, r in c["results"].items():
            if r["L"].get("cagr") is None:
                continue
            L.append(f"| {lab} ({c['coins']}) | {per} | {pc(r['L']['cagr'])} | {pc(r['S']['cagr'])} | {pc(r['LS']['cagr'])} | {sh(r['L'])} | {sh(r['S'])} | {sh(r['LS'])} | -{r['L']['maxdd'] * 100:.0f}% | -{r['LS']['maxdd'] * 100:.0f}% | {pc(r['hold']['cagr'])} |")
    L += ["", "## Other markets (each on its own bars)", "", "| market | years | long-only per yr | short leg per yr | long-short per yr | long-only Sharpe | short leg Sharpe | long-short Sharpe | long-short max DD | share of days short |", "|---|---|---|---|---|---|---|---|---|---|"]
    for r in rep["markets"] + ([rep["btc_pre2017"]] if rep.get("btc_pre2017") else []):
        if r.get("status") != "OK":
            L.append(f"| {r.get('name', r['symbol'])} | {r['status']} {r.get('reason', '')} | | | | | | | | |")
            continue
        L.append(f"| {r['name']} | {r['years']:.1f} | {pc(r['L']['cagr'])} | {pc(r['S']['cagr'])} | {pc(r['LS']['cagr'])} | {sh(r['L'])} | {sh(r['S'])} | {sh(r['LS'])} | -{r['LS']['maxdd'] * 100:.0f}% | {r['short_share'] * 100:.0f}% |")
    v = rep["verdict"]
    L += ["", "## Alerts per week (direction changes: enter long, enter short, flip, exit; size changes are not alerts)", "",
          "| first n coins | full: long-short | full: long-only | last 2 yrs: long-short | last 2 yrs: long-only | enter long | enter short | flip | exit |", "|---|---|---|---|---|---|---|---|---|"]
    f2 = lambda x: "n/a" if x is None else f"{x:.2f}"
    for a in rep["alerts"]:
        L.append(f"| {a['n']} | {f2(a['full_LS_per_week'])} | {f2(a['full_L_per_week'])} | {f2(a['last2y_LS_per_week'])} | {f2(a['last2y_L_per_week'])} | {f2(a['full_LS_enter_long_per_week'])} | {f2(a['full_LS_enter_short_per_week'])} | {f2(a['full_LS_flip_per_week'])} | {f2(a['full_LS_exit_per_week'])} |")
    L += ["", "## Pre-registered criteria", f"- eligible markets (>= {MIN_YEARS:.0f} counted years): {v['eligible']} of {v['markets_total']} (a verdict needs at least {MIN_ELIGIBLE})"]
    if v.get("s1_share") is not None:
        L += [f"- S1 long-short Sharpe >= long-only Sharpe in >= {S_SHARE * 100:.0f}% of eligible markets: {v['s1_share'] * 100:.0f}% -> {'MET' if v['s1_met'] else 'NOT MET'}",
              f"- S2 short leg alone has a positive net total return in >= {S_SHARE * 100:.0f}% of eligible markets: {v['s2_share'] * 100:.0f}% -> {'MET' if v['s2_met'] else 'NOT MET'}"]
    L += [f"- S3 crypto universe, full period and from 2023: short leg alone positive and long-short Sharpe >= long-only Sharpe -> {'MET' if v['s3_met'] else 'NOT MET'}", f"- verdict: {v['verdict']}"]
    return "\n".join(L)


def main(argv):
    opts = dict(zip(argv[1::2], argv[2::2]))
    outdir = Path(opts.get("--out", "shortside_out"))
    outdir.mkdir(parents=True, exist_ok=True)
    asof = int(opts.get("--asof-ms", int(time.time() * 1000) // DAY * DAY))
    datas, notes = T.load_universe(asof)
    rep = build(datas, notes, T.code_sha256())
    (outdir / "shortside.json").write_text(json.dumps(rep, separators=(",", ":")), encoding="utf-8")
    print("SHORTSIDE_JSON_BEGIN")
    print(json.dumps(rep, separators=(",", ":")))
    print("SHORTSIDE_JSON_END")
    md = summary_md(rep)
    (outdir / "shortside.md").write_text(md, encoding="utf-8")
    print(md)
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
