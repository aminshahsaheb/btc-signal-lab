#!/usr/bin/env python3
"""How often does the FROZEN Trend Setup v0 rule ask for a trade, and what happens if a person only acts when the signal changes?
Descriptive only (not an edge test, nothing is tuned). Imports trendsetup.py unchanged.

A. Signal events per coin: the signal is the mean of five Donchian states (0, 0.2, ... 1). An event is a bar on which it changes.
   entries = 0 -> above 0, exits = above 0 -> 0, steps = changes between two non-zero levels. Baskets: the first 1, 2, 5, 10, 26 coins of the fixed universe.
B. One pre-stated manual variant, V1: trade only on the bar a signal event happens (size = signal x vol scale of that bar), then hold that size until the next event
   (no daily re-sizing for volatility). Compared with the frozen daily-resized rule on the same days, coins and costs (0.08% per side).
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent))
import robustness_report as RB  # noqa: E402
import trendsetup as T  # noqa: E402

BASKETS = (1, 2, 5, 10, 26)
DAY = T.DAY_MS


def signal_events(sig, ready):
    """Counts of signal-change bars among ready bars: entries, exits, steps."""
    ent = ext = stp = 0
    for i in range(1, len(sig)):
        if not ready[i] or not ready[i - 1] or sig[i] == sig[i - 1]:
            continue
        if sig[i - 1] == 0:
            ent += 1
        elif sig[i] == 0:
            ext += 1
        else:
            stp += 1
    return ent, ext, stp


def carry_weights(sig, w, ready):
    """V1: the weight is re-set only on a bar where the signal changed (and on the first ready bar), otherwise carried unchanged."""
    out = np.zeros(len(w))
    cur, first = 0.0, True
    for i in range(len(w)):
        if not ready[i]:
            continue
        if first or sig[i] != sig[i - 1]:
            cur, first = w[i], False
        out[i] = cur
    return out


def per_coin(d):
    cc = T.coin_calc(d)
    ent, ext, stp = signal_events(cc["sig"], cc["ready"])
    nready = int(cc["ready"].sum())
    years = nready / 365.0
    w0, w1 = cc["w"], carry_weights(cc["sig"], cc["w"], cc["ready"])
    # days on which a trade is needed: V0 = any change of the weight, V1 = only event days (weight changes by construction)
    t0 = int((np.abs(np.diff(w0)) > 1e-9).sum())
    t1 = int((np.abs(np.diff(w1)) > 1e-9).sum())
    return dict(ready_bars=nready, years=years, entries=ent, exits=ext, steps=stp, events=ent + ext + stp, events_per_year=(ent + ext + stp) / years if years > 0 else None,
                weight_change_days_v0=t0, weight_change_days_v1=t1, turnover_per_year_v0=float(np.abs(np.diff(w0)).sum() / years) if years > 0 else None,
                turnover_per_year_v1=float(np.abs(np.diff(w1)).sum() / years) if years > 0 else None), w1


def build(datas, notes, code_sha):
    G = T.grid(datas)
    names = G["names"]
    coin, W1 = {}, np.full_like(G["W"], np.nan)
    t_min = int(G["t"][0])
    for a, s in enumerate(names):
        d = datas[s]
        row, w1 = per_coin(d)
        coin[s] = row
        idx = ((d["t"] - t_min) // DAY).astype(int)
        W1[idx, a] = w1
    order = [s for s in T.UNIVERSE if s in coin]
    baskets = []
    for n in BASKETS:
        members = order[:n]
        ev = sum(coin[s]["events"] for s in members)
        yrs = np.mean([coin[s]["years"] for s in members])
        baskets.append(dict(n=len(members), members=members, events_per_week=float(ev / (yrs * 52.0)) if yrs > 0 else None,
                            entries_per_year=float(sum(coin[s]["entries"] for s in members) / yrs), exits_per_year=float(sum(coin[s]["exits"] for s in members) / yrs)))
    # B: V1 vs frozen rule, same coins/days/costs
    G1 = dict(G, W=W1)
    cols_all = list(range(len(names)))
    variants = {}
    for label, cols in (("all", cols_all), ("btc", [names.index("BTCUSDT")]), ("top5", [names.index(s) for s in order[:5] if s in names]), ("top10", [names.index(s) for s in order[:10] if s in names])):
        ms = 3 if len(cols) >= 3 else 1
        r0, h, e0 = RB.port(G, cols, min_active=ms)
        r1, _, e1 = RB.port(G1, cols, min_active=ms)
        out = {}
        for per, lo in (("full", None), ("from2023", int(__import__("calendar").timegm((2023, 1, 1, 0, 0, 0)) * 1000))):
            t0_, x0 = RB.cut(G["t"], r0, lo)
            t1_, x1 = RB.cut(G["t"], r1, lo)
            th_, xh = RB.cut(G["t"], h, lo)
            out[per] = dict(v0=RB.brief(t0_, x0), v1=RB.brief(t1_, x1), hold=RB.brief(th_, xh))
        variants[label] = dict(coins=len(cols), results=out)
    return dict(version="trend-setup-v0-frequency", code_sha256=code_sha, coin=coin, baskets=baskets, variants=variants, notes=notes)


def pc(x, d=1):
    return "n/a" if x is None else f"{x * 100:+.{d}f}%"


def summary_md(rep):
    L = ["# Trend Setup v0: trade frequency and a manual 'act only on signal change' variant", "",
         "**Descriptive, in-sample, same author; the variant V1 was stated before the run and is not tuned. Nothing here is evidence of an edge.**", "",
         "## Signal events (the frozen rule asks for a size change only when the signal changes)", "", "| basket | coins | entries/yr | exits/yr | signal events per week |", "|---|---|---|---|---|"]
    for b in rep["baskets"]:
        L.append(f"| first {b['n']} | {b['n']} | {b['entries_per_year']:.1f} | {b['exits_per_year']:.1f} | {b['events_per_week']:.2f} |")
    BTC = rep["coin"].get("BTCUSDT")
    if BTC:
        L += ["", f"BTC alone: {BTC['entries']} entries, {BTC['exits']} exits, {BTC['steps']} steps over {BTC['years']:.1f} years; weight-change days per year: frozen rule (daily re-sizing) {BTC['weight_change_days_v0'] / BTC['years']:.0f}, V1 {BTC['weight_change_days_v1'] / BTC['years']:.1f}."]
    L += ["", "## V1 (trade only on signal-change bars) against the frozen rule, same days, coins and costs", "",
          "| basket | period | frozen rule per year | V1 per year | frozen Sharpe | V1 Sharpe | frozen max DD | V1 max DD | hold per year | hold max DD |", "|---|---|---|---|---|---|---|---|---|---|"]
    for lab, v in rep["variants"].items():
        for per, r in v["results"].items():
            a, b, h = r["v0"], r["v1"], r["hold"]
            if a.get("cagr") is None or b.get("cagr") is None or h.get("cagr") is None:
                continue
            sh = lambda x: "n/a" if x.get("sharpe") is None else f"{x['sharpe']:.2f}"
            L.append(f"| {lab} ({v['coins']}) | {per} | {pc(a['cagr'])} | {pc(b['cagr'])} | {sh(a)} | {sh(b)} | -{a['maxdd'] * 100:.0f}% | -{b['maxdd'] * 100:.0f}% | {pc(h['cagr'])} | -{h['maxdd'] * 100:.0f}% |")
    return "\n".join(L)


def main(argv):
    opts = dict(zip(argv[1::2], argv[2::2]))
    outdir = Path(opts.get("--out", "frequency_out"))
    outdir.mkdir(parents=True, exist_ok=True)
    asof = int(opts.get("--asof-ms", int(__import__("time").time() * 1000) // DAY * DAY))
    datas, notes = T.load_universe(asof)
    rep = build(datas, notes, T.code_sha256())
    (outdir / "frequency.json").write_text(json.dumps(rep, separators=(",", ":")), encoding="utf-8")
    print("FREQUENCY_JSON_BEGIN")
    print(json.dumps(rep, separators=(",", ":")))
    print("FREQUENCY_JSON_END")
    md = summary_md(rep)
    (outdir / "frequency.md").write_text(md, encoding="utf-8")
    print(md)
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
