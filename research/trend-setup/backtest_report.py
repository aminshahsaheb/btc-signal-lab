#!/usr/bin/env python3
"""Descriptive full-history backtest of the FROZEN Trend Setup v0 rule (imports trendsetup.py unchanged; this file is not hash-frozen).

What it is: how the exact rule of specs/trend-setup/SETUP_TREND_v0.md would have done on public daily history, with the same costs (0.08% per side)
and open-to-open fills, next to simple holding benchmarks. What it is not: evidence. The rule was designed AFTER the authors had seen this history
(and BTC was already burned), so every number except the 'unseen coins 2023+' block is in-sample and optimistic by construction.
Nothing is tuned here; no parameter of the rule is touched.
"""
from __future__ import annotations

import datetime as dt
import json
import math
import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent))
import trendsetup as T  # noqa: E402

DAY = T.DAY_MS
NEW15 = ("SOLUSDT", "DOGEUSDT", "AVAXUSDT", "DOTUSDT", "ATOMUSDT", "UNIUSDT", "AAVEUSDT", "FILUSDT", "ALGOUSDT", "VETUSDT", "NEARUSDT", "XTZUSDT", "ZECUSDT", "DASHUSDT", "HBARUSDT")
SPLIT_MS = 1_672_531_200_000  # 2023-01-01: the Search Lab v1 confirmation window starts here
SERIES_HOST_ROUND = 5


def date_of(ms):
    return dt.datetime.fromtimestamp(int(ms) / 1000, dt.timezone.utc).strftime("%Y-%m-%d")


def equity(r):
    return np.cumprod(1.0 + np.nan_to_num(r))


def stats(t, r):
    """Descriptive statistics of a daily return series (NaN days are ignored)."""
    m = np.isfinite(r)
    x = r[m]
    if len(x) < 3:
        return dict(days=int(len(x)))
    eq = np.cumprod(1.0 + x)
    peak = np.maximum.accumulate(np.r_[1.0, eq])[1:]
    years = len(x) / 365.0
    sd = x.std(ddof=1)
    return dict(days=int(len(x)), first=date_of(t[m][0]), last=date_of(t[m][-1]), total=float(eq[-1] - 1), cagr=float(eq[-1] ** (1 / years) - 1),
                vol=float(sd * math.sqrt(365)), sharpe=float(x.mean() / sd * math.sqrt(365)) if sd > 0 else None, maxdd=float(((peak - eq) / peak).max()),
                worst_day=float(x.min()), best_day=float(x.max()))


def yearly(t, r):
    out = {}
    years = np.array([dt.datetime.fromtimestamp(int(a) / 1000, dt.timezone.utc).year for a in t])
    for y in sorted(set(years.tolist())):
        x = r[(years == y) & np.isfinite(r)]
        if len(x):
            out[str(y)] = dict(ret=float(np.prod(1.0 + x) - 1), days=int(len(x)))
    return out


def window(t, r, lo_ms=None, hi_ms=None):
    m = np.ones(len(t), bool)
    if lo_ms is not None:
        m &= t >= lo_ms
    if hi_ms is not None:
        m &= t < hi_ms
    return t[m], r[m]


def raw_hold_and_exposure(datas):
    """Equal-weight daily-rebalanced holding of the ready coins (no cost, no scaling) and the rule's average gross exposure."""
    G = T.grid(datas)
    O, W, ready = G["O"], np.nan_to_num(G["W"]), G["ready"]
    n_t = len(G["t"])
    raw, expo = np.full(n_t, np.nan), np.full(n_t, np.nan)
    for j in range(2, n_t - 1):
        ro = O[j + 1] / O[j] - 1.0
        act = (ready[j - 1] == 1.0) & np.isfinite(ro)
        n = int(act.sum())
        if n < T.MIN_ACTIVE:
            continue
        raw[j] = float(ro[act].mean())
        expo[j] = float(W[j - 1][act].sum() / n)
    return G["t"], raw, expo


def single_coin(d, c_side=T.C_SIDE):
    """Same rule on one coin: strategy, always-long vol-scaled, always-long raw. Weight = fraction of equity (rest cash)."""
    cc = T.coin_calc(d)
    o = d["o"]
    n = len(o)
    w, ws = cc["w"], np.where(cc["ready"], cc["scale"], 0.0)
    R, Rs, Rr = (np.full(n, np.nan) for _ in range(3))
    for j in range(2, n - 1):
        ro = o[j + 1] / o[j] - 1.0
        if not cc["ready"][j - 1]:
            continue
        R[j] = w[j - 1] * ro - c_side * abs(w[j - 1] - w[j - 2])
        Rs[j] = ws[j - 1] * ro - c_side * abs(ws[j - 1] - ws[j - 2])
        Rr[j] = ro
    return d["t"], R, Rs, Rr, w


def sample(t, r, every=7):
    eq = equity(r)
    idx = list(range(0, len(t), every))
    if idx[-1] != len(t) - 1:
        idx.append(len(t) - 1)
    return [[date_of(t[i]), round(float(eq[i]), SERIES_HOST_ROUND)] for i in idx]


def block(t, r, label):
    return dict(label=label, full=stats(t, r), pre2023=stats(*window(t, r, None, SPLIT_MS)), from2023=stats(*window(t, r, SPLIT_MS, None)), yearly=yearly(t, r))


def build_report(datas, notes=None, code_sha=None):
    tr = T.paper_track(datas, t0_ms=0, start_flat=False)
    t, R, Rb = tr["t"], tr["R"], tr["Rb"]
    t2, raw, expo = raw_hold_and_exposure(datas)
    first = int(np.argmax(np.isfinite(R)))
    last = len(t) - 2
    sl = slice(first, last + 1)
    rep = dict(version="trend-setup-v0-backtest", code_sha256=code_sha, coins=len(datas), notes=notes,
               portfolio=dict(strategy=block(t[sl], R[sl], "Rule: signal x vol scale, equal weight over active coins, cost 0.08% per side"),
                              scaled_hold=block(t[sl], Rb[sl], "Always long, same vol scale, same coins and costs"),
                              raw_hold=block(t[sl], raw[sl], "Equal-weight holding (daily rebalanced), no scaling, no cost"),
                              avg_gross_exposure=float(np.nanmean(expo[sl])),
                              avg_gross_exposure_2023=(float(np.nanmean(expo[sl][t[sl] >= SPLIT_MS])) if np.isfinite(expo[sl][t[sl] >= SPLIT_MS]).any() else None),
                              series=dict(strategy=sample(t[sl], R[sl]), scaled_hold=sample(t[sl], Rb[sl]), raw_hold=sample(t[sl], raw[sl]))))
    new = {k: v for k, v in datas.items() if k in NEW15}
    if len(new) >= 8:
        tn = T.paper_track(new, t0_ms=SPLIT_MS, start_flat=False)
        _, rawn, _ = raw_hold_and_exposure(new)
        m = tn["t"] >= SPLIT_MS
        rep["unseen_coins_2023"] = dict(coins=len(new), strategy=stats(tn["t"][m], tn["R"][m]), scaled_hold=stats(tn["t"][m], tn["Rb"][m]), raw_hold=stats(tn["t"][m], rawn[m]),
                                        series=dict(strategy=sample(tn["t"][m][np.isfinite(tn["R"][m])], tn["R"][m][np.isfinite(tn["R"][m])]),
                                                    raw_hold=sample(tn["t"][m][np.isfinite(rawn[m])], rawn[m][np.isfinite(rawn[m])])))
    if "BTCUSDT" in datas:
        tb, Rbtc, Rsc, Rrw, w = single_coin(datas["BTCUSDT"])
        f = int(np.argmax(np.isfinite(Rbtc)))
        s = slice(f, len(tb) - 1)
        rep["btc_only"] = dict(strategy=block(tb[s], Rbtc[s], "Same rule on BTC alone (weight = fraction of equity, rest cash)"), scaled_hold=block(tb[s], Rsc[s], "BTC always long, vol scaled"),
                               raw_hold=block(tb[s], Rrw[s], "BTC buy and hold, no cost"), share_of_days_long=float(np.mean(w[260:] > 0)),
                               series=dict(strategy=sample(tb[s], Rbtc[s]), raw_hold=sample(tb[s], Rrw[s])))
    return rep


def summary_md(rep):
    f = lambda x: "n/a" if x is None else f"{x * 100:+.1f}%"
    g = lambda x: "n/a" if x is None else f"{x:.2f}"
    L = ["# Trend Setup v0: descriptive full-history backtest", "",
         "**In-sample description, not evidence.** The rule was designed after seeing this history; BTC was already burned. Only the 'unseen coins 2023+' block is out-of-sample for the rule family (Search Lab v1), and even it is weak (see the specification).", ""]
    def row(name, s):
        return f"| {name} | {s.get('first','')} | {f(s.get('total'))} | {f(s.get('cagr'))} | {f(s.get('vol'))} | {g(s.get('sharpe'))} | {f(-s['maxdd']) if s.get('maxdd') is not None else 'n/a'} |"
    hdr = ["| series | first day | total | per year (CAGR) | vol | Sharpe | max drawdown |", "|---|---|---|---|---|---|---|"]
    for key, title in (("portfolio", "Portfolio of all coins"), ("btc_only", "BTC alone")):
        if key not in rep:
            continue
        L += [f"## {title}", ""] + hdr
        for part in ("strategy", "scaled_hold", "raw_hold"):
            for per, lab in (("full", "full"), ("pre2023", "2018-2022"), ("from2023", "2023-now")):
                L.append(row(f"{part} ({lab})", rep[key][part][per]))
        L.append("")
    if "unseen_coins_2023" in rep:
        u = rep["unseen_coins_2023"]
        L += ["## 15 coins the discovery never saw, 2023-now", ""] + hdr + [row("strategy", u["strategy"]), row("scaled_hold", u["scaled_hold"]), row("raw_hold", u["raw_hold"]), ""]
    return "\n".join(L) + "\n"


def main(argv):
    opts = dict(zip(argv[1::2], argv[2::2]))
    outdir = Path(opts.get("--out", "backtest_out"))
    outdir.mkdir(parents=True, exist_ok=True)
    asof = int(opts.get("--asof-ms", int(__import__("time").time() * 1000) // DAY * DAY))
    datas, notes = T.load_universe(asof)
    rep = build_report(datas, notes, T.code_sha256())
    md = summary_md(rep)
    (outdir / "backtest.json").write_text(json.dumps(rep, separators=(",", ":")), encoding="utf-8")
    (outdir / "backtest.md").write_text(md, encoding="utf-8")
    print(md)
    print("BACKTEST_JSON_BEGIN")
    print(json.dumps(rep, separators=(",", ":")))
    print("BACKTEST_JSON_END")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
