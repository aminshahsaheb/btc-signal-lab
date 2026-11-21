#!/usr/bin/env python3
"""Fragility pass on the FROZEN Trend Setup v0 rule (imports trendsetup.py and backtest_report.py unchanged; this file is not hash-frozen).

It changes how the rule is EXECUTED or WHICH coins are held, never a parameter of the rule: one extra day of execution delay, higher costs, smaller
universes, leave-one-coin-out, start-date shifts, rolling one-year windows against holding, spells of all-cash, and a block-bootstrap interval of the
portfolio Sharpe. In-sample description, not evidence (the rule was designed after seeing this history).
"""
from __future__ import annotations

import json
import math
import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent))
import backtest_report as B  # noqa: E402
import trendsetup as T  # noqa: E402

DAY = T.DAY_MS
LARGE8 = ("BTCUSDT", "ETHUSDT", "BNBUSDT", "XRPUSDT", "ADAUSDT", "DOGEUSDT", "SOLUSDT", "TRXUSDT")
OLD11 = ("BTCUSDT",) + tuple(s for s in T.UNIVERSE if s not in B.NEW15 and s != "BTCUSDT")
BOOT_REPS, BOOT_BLOCK, BOOT_SEED = 2000, 30, 20_261_121


def port(G, cols, lag=0, c_side=T.C_SIDE, min_active=T.MIN_ACTIVE):
    """Equal-weight portfolio return of the rule over the coins in cols (indices into G), executed `lag` extra days late, plus the raw hold and exposure.
    lag=0, c_side=0.0008, min_active=3, all coins reproduces trendsetup.paper_track(start_flat=False) exactly (tested)."""
    O, W, ready = G["O"][:, cols], np.nan_to_num(G["W"])[:, cols], G["ready"][:, cols]
    n_t = O.shape[0]
    R, H, E = (np.full(n_t, np.nan) for _ in range(3))
    for j in range(2 + lag, n_t - 1):
        ro = O[j + 1] / O[j] - 1.0
        k = j - 1 - lag
        act = (ready[k] == 1.0) & np.isfinite(ro)
        n = int(act.sum())
        if n < min_active:
            continue
        w1, w2 = W[k], W[k - 1]
        R[j] = float(np.where(act, w1 * np.nan_to_num(ro) - c_side * np.abs(w1 - w2), 0.0).sum() / n)
        H[j] = float(ro[act].mean())
        E[j] = float(W[k][act].sum() / n)
    return R, H, E


def cut(t, r, lo_ms=None):
    m = np.isfinite(r) & (np.ones(len(t), bool) if lo_ms is None else t >= lo_ms)
    return t[m], r[m]


def brief(t, r):
    s = B.stats(t, r)
    return {k: s.get(k) for k in ("days", "first", "total", "cagr", "vol", "sharpe", "maxdd")}


def variant(G, name, desc, cols, **kw):
    t = G["t"]
    R, H, _ = port(G, cols, **kw)
    # hold comparator on the same coins and the same days the rule counts
    Hm = np.where(np.isfinite(R), H, np.nan)
    return dict(name=name, desc=desc, coins=len(cols),
                strategy=dict(full=brief(*cut(t, R)), from2023=brief(*cut(t, R, B.SPLIT_MS))),
                hold=dict(full=brief(*cut(t, Hm)), from2023=brief(*cut(t, Hm, B.SPLIT_MS))))


def rolling(t, R, H, win=365):
    """Compounded return over every window of `win` consecutive counted days, rule vs hold."""
    m = np.isfinite(R) & np.isfinite(H)
    r, h = R[m], H[m]
    if len(r) <= win:
        return None
    cr, ch = np.cumsum(np.log1p(r)), np.cumsum(np.log1p(h))
    a = np.exp(cr[win:] - cr[:-win]) - 1
    b = np.exp(ch[win:] - ch[:-win]) - 1
    return dict(windows=int(len(a)), share_rule_beats_hold=float(np.mean(a > b)), share_rule_positive=float(np.mean(a > 0)), share_hold_positive=float(np.mean(b > 0)),
                rule_median=float(np.median(a)), hold_median=float(np.median(b)), rule_worst=float(a.min()), hold_worst=float(b.min()),
                rule_p10=float(np.percentile(a, 10)), hold_p10=float(np.percentile(b, 10)))


def cash_spells(t, E):
    m = np.isfinite(E)
    e, tt = E[m], t[m]
    zero = e < 1e-9
    best, cur, best_end = 0, 0, -1
    for i, z in enumerate(zero):
        cur = cur + 1 if z else 0
        if cur > best:
            best, best_end = cur, i
    now = 0
    for z in zero[::-1]:
        if not z:
            break
        now += 1
    return dict(share_zero=float(zero.mean()), share_below_10pct=float((e < 0.10).mean()), longest_days=int(best), longest_end=B.date_of(tt[best_end]) if best_end >= 0 else None, current_days=int(now))


def sharpe(x):
    sd = x.std(ddof=1)
    return float(x.mean() / sd * math.sqrt(365)) if sd > 0 else float("nan")


def bootstrap(R, H, reps=BOOT_REPS, block=BOOT_BLOCK, seed=BOOT_SEED):
    m = np.isfinite(R) & np.isfinite(H)
    r, h = R[m], H[m]
    n = len(r)
    rng = np.random.default_rng(seed)
    nb = int(math.ceil(n / block))
    sa, sb = np.empty(reps), np.empty(reps)
    for k in range(reps):
        st = rng.integers(0, n - block + 1, nb)
        idx = (st[:, None] + np.arange(block)[None, :]).ravel()[:n]
        sa[k], sb[k] = sharpe(r[idx]), sharpe(h[idx])
    return dict(reps=reps, block_days=block, rule_sharpe_p5=float(np.percentile(sa, 5)), rule_sharpe_p50=float(np.percentile(sa, 50)), rule_sharpe_p95=float(np.percentile(sa, 95)),
                hold_sharpe_p5=float(np.percentile(sb, 5)), hold_sharpe_p50=float(np.percentile(sb, 50)), hold_sharpe_p95=float(np.percentile(sb, 95)),
                share_rule_sharpe_above_hold=float(np.mean(sa > sb)))


def build(datas, notes=None, code_sha=None):
    G = T.grid(datas)
    names = G["names"]
    col = {s: i for i, s in enumerate(names)}
    allc = list(range(len(names)))
    sel = lambda syms: [col[s] for s in syms if s in col]
    out = dict(version="trend-setup-v0-robustness", code_sha256=code_sha, coins=len(names), notes=notes, variants=[])
    V = out["variants"]
    V.append(variant(G, "baseline", "As specified: next-open fills, 0.08% per side, all coins", allc))
    V.append(variant(G, "lag1", "Executed one extra day late (decided at close i, filled at open i+2)", allc, lag=1))
    V.append(variant(G, "cost15", "Cost 0.15% per side (0.30% round trip)", allc, c_side=0.0015))
    V.append(variant(G, "cost30", "Cost 0.30% per side (0.60% round trip)", allc, c_side=0.0030))
    V.append(variant(G, "lag1_cost15", "One extra day late and 0.15% per side", allc, lag=1, c_side=0.0015))
    V.append(variant(G, "btc_eth", "BTC and ETH only (2 coins)", sel(("BTCUSDT", "ETHUSDT")), min_active=2))
    V.append(variant(G, "large8", "8 large coins: BTC ETH BNB XRP ADA DOGE SOL TRX", sel(LARGE8)))
    V.append(variant(G, "old11", "The 11 coins listed since 2017 (BTC + 10 old)", sel(OLD11)))
    V.append(variant(G, "new15", "The 15 coins listed later", sel(B.NEW15)))
    loo = []
    for s in names:
        cols = [c for c in allc if names[c] != s]
        R, H, _ = port(G, cols)
        st = B.stats(*cut(G["t"], R))
        loo.append(dict(dropped=s, cagr=st["cagr"], sharpe=st["sharpe"], maxdd=st["maxdd"]))
    out["leave_one_out"] = dict(rows=loo, worst_sharpe=min(loo, key=lambda r: r["sharpe"]), best_sharpe=max(loo, key=lambda r: r["sharpe"]),
                                worst_maxdd=max(loo, key=lambda r: r["maxdd"]))
    t = G["t"]
    R, H, E = port(G, allc)
    starts = []
    for label, ms in (("2018-07", None), ("2019-01", 1_546_300_800_000), ("2020-01", 1_577_836_800_000), ("2021-01", 1_609_459_200_000), ("2022-01", 1_640_995_200_000), ("2023-01", B.SPLIT_MS)):
        Hm = np.where(np.isfinite(R), H, np.nan)
        starts.append(dict(start=label, rule=brief(*cut(t, R, ms)), hold=brief(*cut(t, Hm, ms))))
    out["start_dates"] = starts
    out["rolling_365"] = rolling(t, R, H, 365)
    out["rolling_730"] = rolling(t, R, H, 730)
    out["cash"] = cash_spells(t, E)
    out["bootstrap"] = bootstrap(R, H)
    return out


def summary_md(rep):
    f = lambda x: "n/a" if x is None else f"{x * 100:+.1f}%"
    g = lambda x: "n/a" if x is None else f"{x:.2f}"
    L = ["# Trend Setup v0: fragility pass (frozen rule; only execution and universe change)", "", "**In-sample description, not evidence.**", "",
         "| variant | coins | rule per year | rule Sharpe | rule max DD | hold per year | hold max DD | rule Sharpe 2023+ |", "|---|---|---|---|---|---|---|---|"]
    for v in rep["variants"]:
        s, h, s3 = v["strategy"]["full"], v["hold"]["full"], v["strategy"]["from2023"]
        L.append(f"| {v['name']} | {v['coins']} | {f(s.get('cagr'))} | {g(s.get('sharpe'))} | {f(-s['maxdd']) if s.get('maxdd') is not None else 'n/a'} | {f(h.get('cagr'))} | {f(-h['maxdd']) if h.get('maxdd') is not None else 'n/a'} | {g(s3.get('sharpe'))} |")
    lo = rep["leave_one_out"]
    L += ["", f"Leave-one-coin-out (26 runs): Sharpe from {g(lo['worst_sharpe']['sharpe'])} (drop {lo['worst_sharpe']['dropped']}) to {g(lo['best_sharpe']['sharpe'])} (drop {lo['best_sharpe']['dropped']}); worst max drawdown {f(-lo['worst_maxdd']['maxdd'])} (drop {lo['worst_maxdd']['dropped']}).", "",
          "| start | rule total | rule per year | rule max DD | hold total | hold per year | hold max DD |", "|---|---|---|---|---|---|---|"]
    for s in rep["start_dates"]:
        a, b = s["rule"], s["hold"]
        L.append(f"| {s['start']} | {f(a.get('total'))} | {f(a.get('cagr'))} | {f(-a['maxdd']) if a.get('maxdd') is not None else 'n/a'} | {f(b.get('total'))} | {f(b.get('cagr'))} | {f(-b['maxdd']) if b.get('maxdd') is not None else 'n/a'} |")
    for k in ("rolling_365", "rolling_730"):
        r = rep[k]
        if r:
            L += ["", f"{k}: {r['windows']} windows; rule beat holding in {r['share_rule_beats_hold'] * 100:.0f}%; rule positive {r['share_rule_positive'] * 100:.0f}% vs hold {r['share_hold_positive'] * 100:.0f}%; median {f(r['rule_median'])} vs {f(r['hold_median'])}; worst {f(r['rule_worst'])} vs {f(r['hold_worst'])}."]
    c, b = rep["cash"], rep["bootstrap"]
    L += ["", f"All-cash days: {c['share_zero'] * 100:.0f}% of days; below 10% invested: {c['share_below_10pct'] * 100:.0f}%; longest all-cash spell {c['longest_days']} days (ended {c['longest_end']}); current spell {c['current_days']} days.", "",
          f"Block bootstrap ({b['reps']} resamples, {b['block_days']}-day blocks): rule Sharpe {g(b['rule_sharpe_p5'])} / {g(b['rule_sharpe_p50'])} / {g(b['rule_sharpe_p95'])} (5% / median / 95%); hold {g(b['hold_sharpe_p5'])} / {g(b['hold_sharpe_p50'])} / {g(b['hold_sharpe_p95'])}; rule Sharpe above hold in {b['share_rule_sharpe_above_hold'] * 100:.0f}% of resamples."]
    return "\n".join(L) + "\n"


def main(argv):
    opts = dict(zip(argv[1::2], argv[2::2]))
    outdir = Path(opts.get("--out", "robustness_out"))
    outdir.mkdir(parents=True, exist_ok=True)
    asof = int(opts.get("--asof-ms", int(__import__("time").time() * 1000) // DAY * DAY))
    datas, notes = T.load_universe(asof)
    rep = build(datas, notes, T.code_sha256())
    md = summary_md(rep)
    (outdir / "robustness.json").write_text(json.dumps(rep, separators=(",", ":")), encoding="utf-8")
    (outdir / "robustness.md").write_text(md, encoding="utf-8")
    print(md)
    print("ROBUSTNESS_JSON_BEGIN")
    print(json.dumps(rep, separators=(",", ":")))
    print("ROBUSTNESS_JSON_END")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
