#!/usr/bin/env python3
"""Search Lab v1 engine (see specs/search-lab/PREREG_SEARCHLAB_v1.md, which is the authority; this file only implements it).

Design: a fixed, declared set of 97 rule variants (11 families) is evaluated on a DISCOVERY panel (10 coins, daily bars, evaluation window
2018-06-01 .. 2022-12-31). The best variant of each of the 3 best families (by discovery Sharpe, mechanically) is frozen and then evaluated ONCE
on a CONFIRMATION panel it has never seen: 15 other coins and the later period 2023-01-01 .. 2026-11-16 (the first 10 coins are reported as a replication).
No human choice sits between the two stages. The discovery stage physically cannot see data after 2022-12-31.

Conventions: a position is decided at the CLOSE of bar i from data <= i, entered at the OPEN of bar i+1; a bar's return is open-to-open.
Position size = direction x min(1, 0.5 / 30-day annualised volatility). Cost = 0.08% of the traded notional per side (0.16% round trip).
Portfolio = equal weight over coins that are active (listed for >= 260 bars); days with < 3 active coins are dropped.
Tests of this file are synthetic and written by the same author; they show the code does what it says, not that any rule works.
"""
from __future__ import annotations

import hashlib
import json
import math
import sys
import time
import urllib.error
import urllib.request
from pathlib import Path
from statistics import NormalDist

import numpy as np
from numpy.lib.stride_tricks import sliding_window_view

VERSION = "searchlab-v1"
DAY_MS = 86_400_000
START_MS = 1_502_928_000_000  # 2017-08-17T00:00:00Z
DISC_START_MS = 1_527_811_200_000  # 2018-06-01: first evaluation day of the discovery stage
SPLIT_MS = 1_672_531_200_000  # 2023-01-01: discovery data end (exclusive) / confirmation start
WARMUP_END_MS = 1_651_276_800_000  # 2022-04-30: a confirmation coin must have bars on or before this day
END_MS = 1_794_873_600_000  # 2026-11-17 (exclusive)
HOSTS = ("data-api.binance.vision", "api.binance.com")
OLD = ("ETHUSDT", "BNBUSDT", "XRPUSDT", "ADAUSDT", "LTCUSDT", "TRXUSDT", "LINKUSDT", "XLMUSDT", "ETCUSDT", "NEOUSDT")
NEW = ("SOLUSDT", "DOGEUSDT", "AVAXUSDT", "DOTUSDT", "ATOMUSDT", "UNIUSDT", "AAVEUSDT", "FILUSDT", "ALGOUSDT", "VETUSDT",
       "NEARUSDT", "XTZUSDT", "ZECUSDT", "DASHUSDT", "HBARUSDT")
MIN_OLD, MIN_NEW, MAX_MISSING_DAYS = 7, 8, 5

CFG = dict(
    target_vol=0.50, vol_window=30, warmup_bars=260, min_active=3, c_side=0.0008, c_side_high=0.0015,
    block_days=30, reps=5000, seed=20_261_120, lo_pct=1.25, hi_pct=98.75, k_select=3, ref_id="ENSEMBLE:DONCH5LF",
    min_days=700, min_sharpe=0.5, ann=365.0,
    disc_lo_ms=DISC_START_MS, split_ms=SPLIT_MS, t0=START_MS,
)


# ----------------------------------------------------------------------------- indicators (causal: value at i uses bars <= i)
def roll(x, n, fn):
    out = np.full(len(x), np.nan)
    if len(x) >= n:
        out[n - 1:] = fn(sliding_window_view(x, n), axis=1)
    return out


def sma(x, n):
    return roll(x, n, np.mean)


def shift1(x):
    out = np.full(len(x), np.nan)
    out[1:] = x[:-1]
    return out


def prev_max(x, n):
    return shift1(roll(x, n, np.max))


def prev_min(x, n):
    return shift1(roll(x, n, np.min))


def wilder(x, n, first):
    """Wilder smoothing; a missing (NaN) input carries the previous value forward instead of poisoning the rest of the series."""
    out = np.full(len(x), np.nan)
    s = first + n - 1
    if len(x) <= s:
        return out
    seed = x[first:first + n]
    out[s] = float(np.nanmean(seed)) if np.isfinite(seed).any() else np.nan
    for i in range(s + 1, len(x)):
        out[i] = (out[i - 1] * (n - 1) + x[i]) / n if np.isfinite(x[i]) else out[i - 1]
    return out


def atr_wilder(h, l, c, n=14):
    tr = np.empty(len(c))
    tr[0] = h[0] - l[0]
    tr[1:] = np.maximum(h[1:] - l[1:], np.maximum(np.abs(h[1:] - c[:-1]), np.abs(l[1:] - c[:-1])))
    return wilder(tr, n, 0)


def rsi(c, n):
    out = np.full(len(c), np.nan)
    if len(c) <= n:
        return out
    d = np.diff(c)
    ag, al = wilder(np.maximum(d, 0.0), n, 0), wilder(np.maximum(-d, 0.0), n, 0)
    with np.errstate(divide="ignore", invalid="ignore"):
        r = 100.0 - 100.0 / (1.0 + ag / al)
    r = np.where((al == 0) & (ag > 0), 100.0, r)
    r = np.where((al == 0) & (ag == 0), 50.0, r)
    out[1:] = r
    return out


def pct_rank_prev(x, n):
    out = np.full(len(x), np.nan)
    if len(x) <= n:
        return out
    w = sliding_window_view(x, n)[: len(x) - n]
    ok = np.isfinite(w).all(axis=1) & np.isfinite(x[n:])
    out[n:] = np.where(ok, (w < x[n:, None]).mean(axis=1), np.nan)
    return out


def colwise(fn, X):
    """Apply fn to each column starting at its first finite value (late-listed coins have leading NaN)."""
    out = np.full(X.shape, np.nan)
    for a in range(X.shape[1]):
        fin = np.flatnonzero(np.isfinite(X[:, a]))
        if len(fin):
            f = fin[0]
            out[f:, a] = fn(X[f:, a])
    return out


def atr_panel(H, L, C):
    out = np.full(C.shape, np.nan)
    for a in range(C.shape[1]):
        fin = np.flatnonzero(np.isfinite(C[:, a]))
        if len(fin) > 20:
            f = fin[0]
            out[f:, a] = atr_wilder(H[f:, a], L[f:, a], C[f:, a])
    return out


# ----------------------------------------------------------------------------- panel
def build_panel(datas: dict, t0: int, t_end: int, cfg=CFG) -> dict:
    """datas: {symbol: dict(t,o,h,l,c)} -> aligned (T x A) panel on the daily UTC grid [t0, t_end)."""
    names = sorted(datas)
    T = int((t_end - t0) // DAY_MS)
    O, H, L, C = (np.full((T, len(names)), np.nan) for _ in range(4))
    for a, s in enumerate(names):
        d = datas[s]
        idx = ((d["t"] - t0) // DAY_MS).astype(int)
        ok = (idx >= 0) & (idx < T)
        for M, k in ((O, "o"), (H, "h"), (L, "l"), (C, "c")):
            M[idx[ok], a] = d[k][ok]
    t = t0 + DAY_MS * np.arange(T, dtype=np.int64)
    return prep(dict(names=names, t=t, O=O, H=H, L=L, C=C), cfg)


def prep(P: dict, cfg=CFG) -> dict:
    O, C = P["O"], P["C"]
    T, A = C.shape
    ret1 = np.full((T, A), np.nan)
    ret1[1:] = C[1:] / C[:-1] - 1.0
    vol = colwise(lambda x: roll(x, cfg["vol_window"], np.std), ret1) * math.sqrt(cfg["ann"])
    with np.errstate(divide="ignore", invalid="ignore"):
        scale = np.where(np.isfinite(vol) & (vol > 0), np.minimum(1.0, cfg["target_vol"] / vol), 0.0)
    ropen = np.full((T, A), np.nan)
    ropen[:-1] = O[1:] / O[:-1] - 1.0
    ready = np.zeros((T, A), dtype=bool)
    for a in range(A):
        fin = np.flatnonzero(np.isfinite(C[:, a]))
        if len(fin):
            ready[fin[0] + cfg["warmup_bars"]:, a] = True
    P.update(ret1=ret1, scale=scale, ropen=ropen, ready=ready, memo={})
    return P


def memo(P, key, fn):
    if key not in P["memo"]:
        P["memo"][key] = fn()
    return P["memo"][key]


# ----------------------------------------------------------------------------- the 97 variants: each returns a (T x A) target position in [-1, 1]
def _sign_pos(cond_long, cond_short, ls):
    pos = np.where(cond_long, 1.0, 0.0)
    if ls:
        pos = np.where(cond_short, -1.0, pos)
    return pos


def f_tsmom(P, Lb, ls):
    C = P["C"]
    r = np.full(C.shape, np.nan)
    r[Lb:] = C[Lb:] / C[:-Lb] - 1.0
    with np.errstate(invalid="ignore"):
        return _sign_pos(r > 0, r < 0, ls)


def f_donch(P, N, M, ls):
    H, L, C = P["H"], P["L"], P["C"]
    hh = memo(P, ("pmax", N), lambda: colwise(lambda x: prev_max(x, N), H))
    ll = memo(P, ("pmin", N), lambda: colwise(lambda x: prev_min(x, N), L))
    xh = memo(P, ("pmax", M), lambda: colwise(lambda x: prev_max(x, M), H))
    xl = memo(P, ("pmin", M), lambda: colwise(lambda x: prev_min(x, M), L))
    pos = np.zeros(C.shape)
    st = np.zeros(C.shape[1])
    with np.errstate(invalid="ignore"):
        for i in range(C.shape[0]):
            c = C[i]
            st = np.where(st == 1, np.where(c < xl[i], 0.0, 1.0), st)
            st = np.where(st == -1, np.where(c > xh[i], 0.0, -1.0), st)
            nl = (st == 0) & (c > hh[i])
            ns = (st == 0) & (c < ll[i]) if ls else np.zeros(len(c), dtype=bool)
            st = np.where(nl, 1.0, np.where(ns, -1.0, st))
            pos[i] = st
    return pos


def f_macross(P, fast, slow, ls):
    C = P["C"]
    a = memo(P, ("sma", fast), lambda: colwise(lambda x: sma(x, fast), C))
    b = memo(P, ("sma", slow), lambda: colwise(lambda x: sma(x, slow), C))
    with np.errstate(invalid="ignore"):
        return _sign_pos(a > b, a < b, ls)


def f_pricesma(P, Lb, ls):
    C = P["C"]
    a = memo(P, ("sma", Lb), lambda: colwise(lambda x: sma(x, Lb), C))
    with np.errstate(invalid="ignore"):
        return _sign_pos(C > a, C < a, ls)


ENS_N = (10, 20, 30, 55, 100)


def f_ensemble(P, ls):
    return np.mean([f_donch(P, N, N // 2, ls) for N in ENS_N], axis=0)


def f_bbrev(P, Lb, k, ls):
    C = P["C"]
    mid = memo(P, ("sma", Lb), lambda: colwise(lambda x: sma(x, Lb), C))
    sd = memo(P, ("std", Lb), lambda: colwise(lambda x: roll(x, Lb, np.std), C))
    with np.errstate(invalid="ignore", divide="ignore"):
        z = (C - mid) / sd
    pos = np.zeros(C.shape)
    st = np.zeros(C.shape[1])
    with np.errstate(invalid="ignore"):
        for i in range(C.shape[0]):
            zi = z[i]
            st = np.where((st == 1) & (zi > 0), 0.0, st)
            st = np.where((st == -1) & (zi < 0), 0.0, st)
            st = np.where((st == 0) & (zi < -k), 1.0, np.where((st == 0) & (zi > k) & ls, -1.0, st))
            pos[i] = st
    return pos


def f_rsi(P, p, thr, flt):
    C = P["C"]
    r = memo(P, ("rsi", p), lambda: colwise(lambda x: rsi(x, p), C))
    trend = memo(P, ("sma", 200), lambda: colwise(lambda x: sma(x, 200), C))
    pos = np.zeros(C.shape)
    st = np.zeros(C.shape[1])
    with np.errstate(invalid="ignore"):
        for i in range(C.shape[0]):
            st = np.where((st == 1) & (r[i] > 50), 0.0, st)
            enter = (st == 0) & (r[i] < thr)
            if flt:
                enter &= C[i] > trend[i]
            st = np.where(enter, 1.0, st)
            pos[i] = st
    return pos


def f_volbo(P, hold, ls):
    H, L, C = P["H"], P["L"], P["C"]
    atr = memo(P, ("atr",), lambda: atr_panel(H, L, C))
    with np.errstate(invalid="ignore", divide="ignore"):
        nat = atr / C
    rk = memo(P, ("rank",), lambda: colwise(lambda x: pct_rank_prev(x, 120), nat))
    sq = np.vstack([np.full((1, C.shape[1]), np.nan), rk[:-1]]) <= 0.20
    hh = memo(P, ("pmax", 10), lambda: colwise(lambda x: prev_max(x, 10), H))
    ll = memo(P, ("pmin", 10), lambda: colwise(lambda x: prev_min(x, 10), L))
    pos = np.zeros(C.shape)
    st = np.zeros(C.shape[1])
    left = np.zeros(C.shape[1])
    with np.errstate(invalid="ignore"):
        for i in range(C.shape[0]):
            left = np.where(st != 0, left - 1, left)
            st = np.where((st != 0) & (left <= 0), 0.0, st)
            nl = (st == 0) & sq[i] & (C[i] > hh[i])
            ns = (st == 0) & sq[i] & (C[i] < ll[i]) & ls
            st = np.where(nl, 1.0, np.where(ns, -1.0, st))
            left = np.where(nl | ns, float(hold), left)
            pos[i] = st
    return pos


def _cs_pos(P, Lb, ls, reverse, every):
    C, ready = P["C"], P["ready"]
    T, A = C.shape
    pos = np.zeros((T, A))
    cur = np.zeros(A)
    for i in range(T):
        if i >= Lb and i % every == 0:
            r = C[i] / C[i - Lb] - 1.0
            ok = ready[i] & np.isfinite(r)
            cur = np.zeros(A)
            n = int(ok.sum())
            if n >= 6:
                k = max(1, n // 3)
                idx = np.flatnonzero(ok)
                order = idx[np.argsort(r[idx], kind="stable")]
                lo_, hi_ = order[:k], order[-k:]
                if reverse:
                    cur[lo_] = 1.0
                    if ls:
                        cur[hi_] = -1.0
                else:
                    cur[hi_] = 1.0
                    if ls:
                        cur[lo_] = -1.0
        pos[i] = cur
    return pos


def f_csmom(P, Lb, ls):
    return _cs_pos(P, Lb, ls, False, 7)


def f_csrev(P, Lb):
    return _cs_pos(P, Lb, True, True, 1)


def f_dow(P, d):
    T, A = P["C"].shape
    wd = ((P["t"] // DAY_MS + 3) % 7).astype(int)  # Monday = 0 for the bar's own open time
    nxt = np.roll(wd, -1)  # weekday of the bar in which the position is held (bar i+1)
    on = (nxt < 5) if d == "WK" else (nxt == d)
    return np.repeat(on[:, None].astype(float), A, axis=1)


def build_variants():
    V = []

    def add(fam, name, fn):
        V.append(dict(id=f"{fam}:{name}", family=fam, fn=fn))
    for Lb in (10, 20, 30, 60, 90, 120, 180, 250):
        for ls in (False, True):
            add("TSMOM", f"L{Lb}{'LS' if ls else 'LF'}", lambda P, Lb=Lb, ls=ls: f_tsmom(P, Lb, ls))
    for N in (10, 20, 30, 55, 100):
        for ls in (False, True):
            add("DONCH", f"N{N}{'LS' if ls else 'LF'}", lambda P, N=N, ls=ls: f_donch(P, N, N // 2, ls))
    for fa, sl in ((5, 20), (10, 50), (20, 50), (20, 100), (50, 200), (30, 150)):
        for ls in (False, True):
            add("MACROSS", f"{fa}_{sl}{'LS' if ls else 'LF'}", lambda P, fa=fa, sl=sl, ls=ls: f_macross(P, fa, sl, ls))
    for Lb in (20, 50, 100, 150, 200):
        for ls in (False, True):
            add("PRICESMA", f"L{Lb}{'LS' if ls else 'LF'}", lambda P, Lb=Lb, ls=ls: f_pricesma(P, Lb, ls))
    for ls in (False, True):
        add("ENSEMBLE", f"DONCH5{'LS' if ls else 'LF'}", lambda P, ls=ls: f_ensemble(P, ls))
    for Lb in (10, 20):
        for k in (1.5, 2.0, 2.5):
            for ls in (False, True):
                add("BBREV", f"L{Lb}k{k}{'LS' if ls else 'LF'}", lambda P, Lb=Lb, k=k, ls=ls: f_bbrev(P, Lb, k, ls))
    for p in (2, 5):
        for thr in (10, 20, 30):
            for flt in (False, True):
                add("RSIREV", f"p{p}t{thr}{'F' if flt else 'N'}", lambda P, p=p, thr=thr, flt=flt: f_rsi(P, p, thr, flt))
    for hold in (7, 14):
        for ls in (False, True):
            add("VOLBO", f"H{hold}{'LS' if ls else 'LF'}", lambda P, hold=hold, ls=ls: f_volbo(P, hold, ls))
    for Lb in (7, 14, 28, 56):
        for ls in (False, True):
            add("CSMOM", f"L{Lb}{'LS' if ls else 'LF'}", lambda P, Lb=Lb, ls=ls: f_csmom(P, Lb, ls))
    for Lb in (1, 3, 7):
        add("CSREV", f"L{Lb}LS", lambda P, Lb=Lb: f_csrev(P, Lb))
    for d in range(7):
        add("DOW", f"D{d}", lambda P, d=d: f_dow(P, d))
    add("DOW", "WK", lambda P: f_dow(P, "WK"))
    return V


VARIANTS = build_variants()


# ----------------------------------------------------------------------------- engine
def portfolio_returns(P: dict, pos: np.ndarray, c_side: float, cfg=CFG) -> np.ndarray:
    """Daily equal-weight portfolio return (open-to-open) of the target positions; NaN where fewer than min_active coins are active."""
    w = np.where(P["ready"], pos * P["scale"], 0.0)
    w1 = np.zeros_like(w); w1[1:] = w[:-1]  # weight held in bar j (decided at close j-1)
    w2 = np.zeros_like(w); w2[2:] = w[:-2]
    ret = w1 * P["ropen"] - c_side * np.abs(w1 - w2)
    ready_prev = np.zeros_like(P["ready"]); ready_prev[1:] = P["ready"][:-1]
    active = ready_prev & np.isfinite(P["ropen"])
    n = active.sum(axis=1)
    tot = np.where(active, ret, 0.0).sum(axis=1)
    with np.errstate(invalid="ignore", divide="ignore"):
        R = np.where(n >= cfg["min_active"], tot / n, np.nan)
    return R


def window_mask(P, lo_ms, hi_ms):
    return (P["t"] >= lo_ms) & (P["t"] < hi_ms)


def sharpe(x, ann=365.0):
    x = x[np.isfinite(x)]
    if len(x) < 2 or np.std(x, ddof=1) == 0:
        return float("nan")
    return float(np.mean(x) / np.std(x, ddof=1) * math.sqrt(ann))


def max_drawdown(x):
    x = x[np.isfinite(x)]
    eq = np.cumprod(1.0 + x)
    return float(np.max(1.0 - eq / np.maximum.accumulate(eq))) if len(eq) else float("nan")


def block_sharpe_bounds(x, block, reps, rng, lo, hi, ann=365.0):
    """Percentile bounds of the annualised Sharpe under resampling of whole `block`-day blocks."""
    x = np.asarray(x, dtype=float)
    nb = int(math.ceil(len(x) / block))
    bid = np.arange(len(x)) // block
    s1 = np.bincount(bid, weights=x, minlength=nb)
    s2 = np.bincount(bid, weights=x * x, minlength=nb)
    cn = np.bincount(bid, minlength=nb).astype(float)
    idx = rng.integers(0, nb, size=(reps, nb))
    C, S1, S2 = cn[idx].sum(1), s1[idx].sum(1), s2[idx].sum(1)
    m = S1 / C
    v = np.maximum(S2 / C - m * m, 1e-18)
    sh = m / np.sqrt(v) * math.sqrt(ann)
    return float(np.percentile(sh, lo)), float(np.percentile(sh, hi))


def alpha_beta(r, b, ann=365.0):
    mr, mb = float(np.mean(r)), float(np.mean(b))
    var = float(np.mean(b * b) - mb * mb)
    beta = (float(np.mean(r * b)) - mr * mb) / var if var > 1e-18 else float("nan")
    return (mr - beta * mb) * ann, beta


def block_alpha_bounds(r, b, block, reps, rng, lo, hi, ann=365.0):
    """Percentile bounds of the annualised regression alpha of r on the long-only benchmark b under block resampling."""
    r, b = np.asarray(r, dtype=float), np.asarray(b, dtype=float)
    nb = int(math.ceil(len(r) / block))
    bid = np.arange(len(r)) // block
    sr, sb = np.bincount(bid, weights=r, minlength=nb), np.bincount(bid, weights=b, minlength=nb)
    srb, sbb = np.bincount(bid, weights=r * b, minlength=nb), np.bincount(bid, weights=b * b, minlength=nb)
    cn = np.bincount(bid, minlength=nb).astype(float)
    idx = rng.integers(0, nb, size=(reps, nb))
    C = cn[idx].sum(1)
    mr, mb = sr[idx].sum(1) / C, sb[idx].sum(1) / C
    cov, var = srb[idx].sum(1) / C - mr * mb, np.maximum(sbb[idx].sum(1) / C - mb * mb, 1e-18)
    al = (mr - cov / var * mb) * ann
    return float(np.percentile(al, lo)), float(np.percentile(al, hi))


def deflated_sharpe(sr_daily, T, skew, kurt, trial_srs):
    """Probability that the true Sharpe exceeds the expected maximum of N independent trials (Bailey & Lopez de Prado, as implemented here;
    descriptive only and not part of any verdict)."""
    N = len(trial_srs)
    if N < 2 or T < 3:
        return float("nan")
    nd, g = NormalDist(), 0.5772156649
    sr0 = float(np.std(trial_srs, ddof=1)) * ((1 - g) * nd.inv_cdf(1 - 1.0 / N) + g * nd.inv_cdf(1 - 1.0 / (N * math.e)))
    den = math.sqrt(max(1e-12, 1 - skew * sr_daily + (kurt - 1) / 4.0 * sr_daily ** 2))
    return float(nd.cdf((sr_daily - sr0) * math.sqrt(T - 1) / den))


def moments(x):
    x = x[np.isfinite(x)]
    m, s = x.mean(), x.std()
    z = (x - m) / s if s > 0 else x * 0
    return float((z ** 3).mean()), float((z ** 4).mean())


def discover(P: dict, cfg=CFG, variants=None) -> dict:
    """Evaluate every variant on the discovery panel; mechanical selection of the best variant of each of the best k_select families."""
    variants = VARIANTS if variants is None else variants
    mk = window_mask(P, cfg["disc_lo_ms"], cfg["split_ms"])
    rows = []
    for v in variants:
        R = portfolio_returns(P, v["fn"](P), cfg["c_side"], cfg)[mk]
        ok = R[np.isfinite(R)]
        sk, ku = moments(ok) if len(ok) > 3 else (0.0, 3.0)
        rows.append(dict(id=v["id"], family=v["family"], n=int(len(ok)), sharpe=sharpe(R, cfg["ann"]), ann_ret=float(ok.mean() * cfg["ann"]) if len(ok) else float("nan"),
                         maxdd=max_drawdown(R), skew=sk, kurt=ku, sr_daily=float(ok.mean() / ok.std(ddof=1)) if len(ok) > 2 and ok.std() > 0 else float("nan")))
    trial = np.array([r["sr_daily"] for r in rows if np.isfinite(r["sr_daily"])])
    for r in rows:
        r["dsr"] = deflated_sharpe(r["sr_daily"], r["n"], r["skew"], r["kurt"], trial) if np.isfinite(r["sr_daily"]) else float("nan")
    bench = portfolio_returns(P, np.ones_like(P["C"]), cfg["c_side"], cfg)[mk]
    ranked = sorted(rows, key=lambda r: (-(r["sharpe"] if np.isfinite(r["sharpe"]) else -1e9), r["id"]))
    best_by_fam = {}
    for r in ranked:
        best_by_fam.setdefault(r["family"], r)
    selected = sorted(best_by_fam.values(), key=lambda r: (-(r["sharpe"] if np.isfinite(r["sharpe"]) else -1e9), r["id"]))[: cfg["k_select"]]
    sel_ids = [s["id"] for s in selected]
    ref = cfg.get("ref_id")
    cands = sel_ids + ([ref] if ref and ref not in sel_ids and any(v["id"] == ref for v in variants) else [])
    return dict(rows=ranked, selected=sel_ids, candidates=cands, reference=ref, n_variants=len(rows), benchmark_sharpe=sharpe(bench, cfg["ann"]),
                benchmark_ann_ret=float(np.nanmean(bench) * cfg["ann"]))


def confirm(selected_ids, P_new: dict, P_old: dict, cfg=CFG, variants=None, seed_offset=0) -> list:
    """One frozen evaluation per selected variant on the confirmation panel (new coins, 2023-01-01 on) + replication on the old coins."""
    variants = VARIANTS if variants is None else variants
    byid = {v["id"]: v for v in variants}
    out = []
    mk_new, mk_old = window_mask(P_new, cfg["split_ms"], 10 ** 18), window_mask(P_old, cfg["split_ms"], 10 ** 18)
    bench_new = portfolio_returns(P_new, np.ones_like(P_new["C"]), cfg["c_side"], cfg)
    for si, vid in enumerate(selected_ids):
        v = byid[vid]
        pos_new, pos_old = v["fn"](P_new), v["fn"](P_old)
        R = portfolio_returns(P_new, pos_new, cfg["c_side"], cfg)
        Rh = portfolio_returns(P_new, pos_new, cfg["c_side_high"], cfg)
        Ro = portfolio_returns(P_old, pos_old, cfg["c_side"], cfg)
        sel = mk_new & np.isfinite(R) & np.isfinite(bench_new)
        r, rh = R[sel], Rh[sel]
        ro = Ro[mk_old & np.isfinite(Ro)]
        rng = np.random.default_rng(cfg["seed"] + seed_offset + si)
        lo_r, hi_r = block_sharpe_bounds(r, cfg["block_days"], cfg["reps"], rng, cfg["lo_pct"], cfg["hi_pct"], cfg["ann"])
        bb = bench_new[sel]
        lo_a, hi_a = block_alpha_bounds(r, bb, cfg["block_days"], cfg["reps"], rng, cfg["lo_pct"], cfg["hi_pct"], cfg["ann"])
        alpha, beta = alpha_beta(r, bb, cfg["ann"])
        res = dict(id=vid, family=v["family"], role=("discovery" if vid in selected_ids[: cfg["k_select"]] else "reference"), days=int(len(r)), sharpe=sharpe(r, cfg["ann"]), sharpe_lo=lo_r, sharpe_hi=hi_r,
                   alpha_ann=alpha, beta=beta, alpha_lo=lo_a, alpha_hi=hi_a, sharpe_high_cost=sharpe(rh, cfg["ann"]),
                   sharpe_old_coins=sharpe(ro, cfg["ann"]), old_days=int(len(ro)), ann_ret=float(r.mean() * cfg["ann"]) if len(r) else float("nan"),
                   maxdd=max_drawdown(r), benchmark_sharpe=sharpe(bench_new[sel], cfg["ann"]),
                   turnover=float(np.nanmean(np.abs(np.diff(np.where(P_new["ready"], pos_new * P_new["scale"], 0.0), axis=0)))) if len(pos_new) > 1 else float("nan"))
        crit = {
            "Q1_days>=%d" % cfg["min_days"]: res["days"] >= cfg["min_days"],
            "Q2_sharpe_lower>0": res["sharpe_lo"] > 0,
            "Q3_alpha_vs_longonly_lower>0": res["alpha_lo"] > 0,
            "Q4_sharpe>=%.1f" % cfg["min_sharpe"]: res["sharpe"] >= cfg["min_sharpe"],
            "Q5_high_cost_sharpe>0": res["sharpe_high_cost"] > 0,
            "Q6_old_coins_2023+_sharpe>0": res["sharpe_old_coins"] > 0,
        }
        res["criteria"], res["failed"] = crit, [k for k, ok in crit.items() if not ok]
        q1 = crit["Q1_days>=%d" % cfg["min_days"]]
        res["verdict"] = "PASS" if not res["failed"] else ("FAIL" if q1 and res["sharpe_hi"] < cfg["min_sharpe"] else "INCONCLUSIVE")
        out.append(res)
    return out


# ----------------------------------------------------------------------------- data (same rules as Setup Lab v1)
class DataError(Exception):
    pass


def default_http_get(url, timeout=30):
    req = urllib.request.Request(url, headers={"User-Agent": "btc-signal-lab-searchlab/1"})
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return r.read().decode("utf-8")


def _page(symbol, start_ms, end_ms, http_get, hosts, retries, sleep):
    last = None
    for host in hosts:
        url = f"https://{host}/api/v3/klines?symbol={symbol}&interval=1d&startTime={start_ms}&endTime={end_ms - 1}&limit=1000"
        for attempt in range(retries):
            try:
                data = json.loads(http_get(url))
                if isinstance(data, list):
                    return data
                last = f"{host}: unexpected payload {str(data)[:80]}"
            except (urllib.error.URLError, OSError, ValueError) as e:
                last = f"{host}: {type(e).__name__} {e}"
            sleep(1.0 * (attempt + 1))
    raise DataError(f"{symbol}: all hosts failed ({last})")


def validate_rows(symbol, rows):
    if not rows:
        raise DataError(f"{symbol}: no rows")
    try:
        t = np.array([int(r[0]) for r in rows], dtype=np.int64)
        o, h, l, c = (np.array([float(r[k]) for r in rows]) for k in (1, 2, 3, 4))
    except (TypeError, ValueError, IndexError) as e:
        raise DataError(f"{symbol}: malformed row ({e})")
    if not np.all(np.isfinite([o, h, l, c])) or (np.minimum.reduce([o, h, l, c]) <= 0).any():
        raise DataError(f"{symbol}: non-positive or non-finite price")
    if (h < np.maximum(o, c)).any() or (l > np.minimum(o, c)).any() or (h < l).any():
        raise DataError(f"{symbol}: inconsistent OHLC bar")
    dt = np.diff(t)
    if (dt < DAY_MS).any() or (t % DAY_MS != 0).any():
        raise DataError(f"{symbol}: duplicate, unordered or non-daily timestamps")
    return dict(symbol=symbol, t=t, o=o, h=h, l=l, c=c, missing_days=int(((dt // DAY_MS) - 1).sum()))


def fetch_klines(symbol, http_get=default_http_get, start_ms=START_MS, end_ms=END_MS, hosts=HOSTS, retries=3, sleep=time.sleep):
    rows, cur = [], start_ms
    while cur < end_ms:
        page = _page(symbol, cur, end_ms, http_get, hosts, retries, sleep)
        if not page:
            break
        rows += [r for r in page if start_ms <= int(r[0]) < end_ms]
        last_open = int(page[-1][0])
        if len(page) < 1000 or last_open < cur:
            break
        cur = last_open + DAY_MS
        sleep(0.15)
    return validate_rows(symbol, rows)


def data_hash(d):
    hh = hashlib.sha256()
    for k in ("t", "o", "h", "l", "c"):
        hh.update(np.ascontiguousarray(d[k]).tobytes())
    return hh.hexdigest()


def load_assets(symbols, end_ms, http_get=default_http_get, sleep=time.sleep, min_bars=300, need_by_ms=None):
    """Fetch and validate. need_by_ms: the coin must have a bar on or before that instant (confirmation coins need a warm-up history)."""
    got, notes = {}, []
    for s in symbols:
        try:
            d = fetch_klines(s, http_get=http_get, sleep=sleep, end_ms=end_ms)
        except DataError as e:
            notes.append(dict(symbol=s, status="EXCLUDED", reason=str(e)))
            continue
        why = None
        if len(d["c"]) < min_bars or d["missing_days"] > MAX_MISSING_DAYS:
            why = f"bars={len(d['c'])} missing_days={d['missing_days']}"
        elif need_by_ms is not None and int(d["t"][0]) > need_by_ms:
            why = "history starts too late for the warm-up"
        if why:
            notes.append(dict(symbol=s, status="EXCLUDED", reason=why))
            continue
        got[s] = d
        notes.append(dict(symbol=s, status="OK", bars=len(d["c"]), missing_days=d["missing_days"], first=time.strftime("%Y-%m-%d", time.gmtime(int(d["t"][0]) / 1000)),
                          last=time.strftime("%Y-%m-%d", time.gmtime(int(d["t"][-1]) / 1000)), sha256=data_hash(d)))
    return got, notes


# ----------------------------------------------------------------------------- run + report
def _f(x, d=2):
    return "n/a" if x is None or (isinstance(x, float) and not np.isfinite(x)) else f"{x:+.{d}f}"


def render(disc, conf, notes_disc, notes_conf, code_sha, cfg=CFG):
    L = [f"# Search Lab v1 results ({VERSION})", "", f"code sha256: `{code_sha}`",
         "Nothing here is self-certified: tests are synthetic and by the same author; no independent review exists.", "",
         f"## Stage 1: discovery ({disc['n_variants']} declared variants, 10 coins, 2018-06-01 .. 2022-12-31, cost 0.16% round trip)", "",
         f"Always-long vol-scaled benchmark: Sharpe {_f(disc['benchmark_sharpe'])}, annualised return {_f(disc['benchmark_ann_ret'])}.", "",
         "| rank | variant | Sharpe | ann. return | max DD | deflated-Sharpe prob. (descriptive) |", "|---|---|---|---|---|---|"]
    for i, r in enumerate(disc["rows"][:15], 1):
        L.append(f"| {i} | {r['id']} | {_f(r['sharpe'])} | {_f(r['ann_ret'])} | {r['maxdd']:.2f} | {r['dsr']:.2f} |")
    L += ["", f"Mechanically selected (best variant of each of the best {cfg['k_select']} families): **{', '.join(disc['selected'])}**; literature-prior reference candidate (always confirmed): **{disc.get('reference')}**; Bonferroni K = {cfg['k_select'] + 1}", "",
          "## Stage 2: confirmation (15 new coins, 2023-01-01 .. 2026-11-16; frozen rules; one run)", "",
          "| variant | role | days | Sharpe | 98.75% interval | alpha vs long-only (ann.) | beta | alpha 98.75% lower | high-cost Sharpe | old coins 2023+ Sharpe | verdict | failed |", "|---|---|---|---|---|---|---|---|---|---|---|---|"]
    for r in conf:
        L.append(f"| {r['id']} | {r['role']} | {r['days']} | {_f(r['sharpe'])} | [{_f(r['sharpe_lo'])}, {_f(r['sharpe_hi'])}] | {_f(r['alpha_ann'])} | {_f(r['beta'])} | {_f(r['alpha_lo'])} | {_f(r['sharpe_high_cost'])} | {_f(r['sharpe_old_coins'])} | **{r['verdict']}** | {', '.join(r['failed']) or '-'} |")
    for r in conf:
        L += ["", f"### {r['id']}", f"- annualised return {_f(r['ann_ret'])}, max DD {r['maxdd']:.2f}, mean daily turnover {r['turnover']:.3f}; always-long benchmark Sharpe on the same coins and days {_f(r['benchmark_sharpe'])}",
              "- criteria: " + "; ".join(f"{k}={'yes' if v else 'NO'}" for k, v in r["criteria"].items())]
    L += ["", "## Data", "| symbol | status | bars | missing | first | last | sha256(data) |", "|---|---|---|---|---|---|---|"]
    for n in list(notes_disc) + [dict(x, symbol=x["symbol"] + " (full)") for x in notes_conf]:
        L.append(f"| {n['symbol']} | {n['status']} | {n.get('bars', '')} | {n.get('missing_days', '')} | {n.get('first', '')} | {n.get('last', '')} | {n.get('sha256', n.get('reason', ''))[:16]} |")
    return "\n".join(L) + "\n"


def code_sha256():
    return hashlib.sha256(Path(__file__).read_bytes()).hexdigest()


def main(argv):
    outdir = Path(argv[1]) if len(argv) > 1 else Path("searchlab_out")
    outdir.mkdir(parents=True, exist_ok=True)
    # Stage 1 sees ONLY bars before 2023-01-01 (the fetch itself is cut at the split).
    old_pre, notes_pre = load_assets(OLD, SPLIT_MS)
    if len(old_pre) < MIN_OLD:
        raise DataError(f"only {len(old_pre)} discovery coins (< {MIN_OLD}); infrastructure failure, not a result")
    P_pre = build_panel(old_pre, START_MS, SPLIT_MS)
    disc = discover(P_pre)
    print("DISCOVERY SELECTED:", disc["selected"], flush=True)
    # Stage 2 data are fetched only after the selection exists.
    old_full, notes_old = load_assets(OLD, END_MS)
    new_full, notes_new = load_assets(NEW, END_MS, need_by_ms=WARMUP_END_MS)
    if len(old_full) < MIN_OLD or len(new_full) < MIN_NEW:
        raise DataError(f"too few confirmation coins (old {len(old_full)}, new {len(new_full)}); infrastructure failure, not a result")
    conf = confirm(disc["candidates"], build_panel(new_full, START_MS, END_MS), build_panel(old_full, START_MS, END_MS))
    report = render(disc, conf, notes_pre, notes_old + notes_new, code_sha256())
    (outdir / "report.md").write_text(report, encoding="utf-8")
    (outdir / "results.json").write_text(json.dumps(dict(discovery=disc, confirmation=conf, code_sha256=code_sha256()), indent=1, default=float), encoding="utf-8")
    print(report)
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
