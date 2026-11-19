#!/usr/bin/env python3
"""Setup Lab v1 engine (see PREREG_SETUPLAB_v1.md, which is the authority; this file only implements it).

What it does: takes daily OHLC bars of several liquid spot pairs, evaluates five pre-registered trade setups with ONE
fixed set of parameters each, and applies a pre-registered verdict rule. Nothing here is tuned, and no parameter is read from data.

Conventions (all frozen by the preregistration):
  * Signal at the CLOSE of bar i; entry at the OPEN of bar i+1 (no look-ahead).
  * Stop distance D = k * ATR14[i]; stop = entry -/+ D; optional target = entry +/- m*D; time exit at the close of bar i+T.
  * Within one bar the stop is checked first. A gap through the stop fills at the open (worse); a target fills at the target price (not better).
  * One position at a time per asset. A signal on the exit bar may be taken (the entry is the next open).
  * Trades that would run past the last bar are dropped.
  * R = (side*(exit-entry) - cost*entry) / D, cost = round-trip fraction of the entry price.
Tests of this file are synthetic and were written by the same author; they show the code does what it is written to do, not that any setup works.
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

import numpy as np
from numpy.lib.stride_tricks import sliding_window_view

VERSION = "setuplab-v1"
DAY_MS = 86_400_000
START_MS = 1_502_928_000_000  # 2017-08-17T00:00:00Z
END_MS = 1_794_873_600_000  # 2026-11-17T00:00:00Z (exclusive: bars opening before this instant)
SPLIT_MS = 1_640_995_200_000  # 2022-01-01T00:00:00Z, boundary of the two time halves
HOSTS = ("data-api.binance.vision", "api.binance.com")
ASSETS = ("ETHUSDT", "BNBUSDT", "XRPUSDT", "ADAUSDT", "LTCUSDT", "TRXUSDT", "LINKUSDT", "XLMUSDT", "ETCUSDT", "NEOUSDT")
REFERENCE = "BTCUSDT"  # burned data: reported descriptively, never part of a verdict
MIN_ASSETS = 7
MAX_MISSING_DAYS = 5
MIN_BARS = 1000

CFG = dict(
    cost=0.0016, cost_low=0.0006, cost_high=0.0030,
    block_days=30, reps=10_000, seed=20_261_118, lo_pct=1.0, hi_pct=99.0,
    min_n=300, min_mean=0.10, half_n=50, asset_n=20, asset_frac=0.60, min_qual_assets=5,
    t0=START_MS, t_end=END_MS, split_ms=SPLIT_MS,
)


# ----------------------------------------------------------------------------- indicators (causal: value at i uses bars <= i)
def roll(x: np.ndarray, n: int, fn) -> np.ndarray:
    out = np.full(len(x), np.nan)
    if len(x) >= n:
        out[n - 1:] = fn(sliding_window_view(x, n), axis=1)
    return out


def sma(x: np.ndarray, n: int) -> np.ndarray:
    return roll(x, n, np.mean)


def shift1(x: np.ndarray) -> np.ndarray:
    out = np.full(len(x), np.nan)
    out[1:] = x[:-1]
    return out


def prev_max(x: np.ndarray, n: int) -> np.ndarray:
    """max of x[i-n .. i-1] (excludes bar i)."""
    return shift1(roll(x, n, np.max))


def prev_min(x: np.ndarray, n: int) -> np.ndarray:
    return shift1(roll(x, n, np.min))


def wilder(x: np.ndarray, n: int, first: int) -> np.ndarray:
    """Wilder smoothing; the seed is the mean of x[first : first+n] placed at index first+n-1."""
    out = np.full(len(x), np.nan)
    s = first + n - 1
    if len(x) <= s:
        return out
    out[s] = float(np.mean(x[first:first + n]))
    for i in range(s + 1, len(x)):
        out[i] = (out[i - 1] * (n - 1) + x[i]) / n
    return out


def atr_wilder(h: np.ndarray, l: np.ndarray, c: np.ndarray, n: int = 14) -> np.ndarray:
    tr = np.empty(len(c))
    tr[0] = h[0] - l[0]
    tr[1:] = np.maximum(h[1:] - l[1:], np.maximum(np.abs(h[1:] - c[:-1]), np.abs(l[1:] - c[:-1])))
    return wilder(tr, n, 0)


def rsi(c: np.ndarray, n: int) -> np.ndarray:
    out = np.full(len(c), np.nan)
    if len(c) <= n:
        return out
    d = np.diff(c)
    up, dn = np.maximum(d, 0.0), np.maximum(-d, 0.0)
    ag, al = wilder(up, n, 0), wilder(dn, n, 0)  # index j of d corresponds to bar j+1
    with np.errstate(divide="ignore", invalid="ignore"):
        r = 100.0 - 100.0 / (1.0 + ag / al)
    r = np.where((al == 0) & (ag > 0), 100.0, r)
    r = np.where((al == 0) & (ag == 0), 50.0, r)
    out[1:] = r
    return out


def pct_rank_prev(x: np.ndarray, n: int) -> np.ndarray:
    """Fraction of x[j-n .. j-1] strictly below x[j]; NaN unless the whole window and x[j] are finite."""
    out = np.full(len(x), np.nan)
    if len(x) <= n:
        return out
    w = sliding_window_view(x, n)[: len(x) - n]
    ok = np.isfinite(w).all(axis=1) & np.isfinite(x[n:])
    r = (w < x[n:, None]).mean(axis=1)
    out[n:] = np.where(ok, r, np.nan)
    return out


# ----------------------------------------------------------------------------- the five frozen setups
def _side(long_: np.ndarray, short_: np.ndarray) -> np.ndarray:
    return (long_ & ~short_).astype(np.int8) - (short_ & ~long_).astype(np.int8)


def sig_s1(o, h, l, c, atr):
    """S1 trend breakout: close beyond the prior 20-bar extreme, in the direction of SMA100."""
    s100 = sma(c, 100)
    return _side((c > prev_max(h, 20)) & (c > s100), (c < prev_min(l, 20)) & (c < s100))


def sig_s2(o, h, l, c, atr):
    """S2 pullback in a trend: RSI5 extreme against the SMA200 trend."""
    r5, s200 = rsi(c, 5), sma(c, 200)
    return _side((r5 < 30) & (c > s200), (r5 > 70) & (c < s200))


def sig_s3(o, h, l, c, atr):
    """S3 overextension: close outside Bollinger(20, 2.5 sd); fade it."""
    mid, sd = sma(c, 20), roll(c, 20, np.std)
    return _side(c < mid - 2.5 * sd, c > mid + 2.5 * sd)


def sig_s4(o, h, l, c, atr):
    """S4 volatility compression then expansion: normalized ATR in the lowest 20% of its previous 120 values (at i-1), then a 10-bar breakout."""
    sq = shift1(pct_rank_prev(atr / c, 120)) <= 0.20
    return _side(sq & (c > prev_max(h, 10)), sq & (c < prev_min(l, 10)))


def sig_s5(o, h, l, c, atr):
    """S5 capitulation / blow-off: one-bar move beyond 2.5 ATR(i-1) with RSI14 extreme; fade it."""
    mv, a1, r14 = c - shift1(c), shift1(atr), rsi(c, 14)
    return _side((mv <= -2.5 * a1) & (r14 < 30), (mv >= 2.5 * a1) & (r14 > 70))


SETUPS = (
    dict(id="S1", name="trend breakout", k=2.0, m=1.5, T=30, fn=sig_s1),
    dict(id="S2", name="pullback in trend", k=1.5, m=2.0, T=24, fn=sig_s2),
    dict(id="S3", name="overextension fade", k=1.5, m=1.0, T=12, fn=sig_s3),
    dict(id="S4", name="compression then expansion", k=3.0, m=None, T=14, fn=sig_s4),
    dict(id="S5", name="capitulation / blow-off fade", k=3.0, m=0.5, T=10, fn=sig_s5),
)


# ----------------------------------------------------------------------------- trade simulation
def simulate_all(o, h, l, c, atr, side: int, k: float, m, T: int):
    """Outcome of entering at the open of EVERY bar i+1 (signal at i), in the given direction. Vectorised over i.
    Returns dict(gross, cu, exit_bar, code): gross R before cost; cu = entry/D (cost in R = cost*cu); code 0 stop, 1 target, 2 time exit."""
    n = len(c)
    gross = np.full(n, np.nan)
    cu = np.full(n, np.nan)
    exit_bar = np.full(n, -1, dtype=np.int64)
    code = np.full(n, -1, dtype=np.int8)
    if n < T + 2:
        return dict(gross=gross, cu=cu, exit_bar=exit_bar, code=code)
    idx = np.arange(n - 1)
    ok = (idx + T <= n - 1) & np.isfinite(atr[: n - 1]) & (atr[: n - 1] > 0)
    i = idx[ok]
    entry = o[i + 1]
    D = k * atr[i]
    stop = entry - side * D
    target = entry + side * m * D if m is not None else None
    done = np.zeros(len(i), dtype=bool)
    px = np.full(len(i), np.nan)
    eb = np.full(len(i), -1, dtype=np.int64)
    cd = np.full(len(i), -1, dtype=np.int8)
    for t in range(1, T + 1):
        j = i + t
        oj, hj, lj, cj = o[j], h[j], l[j], c[j]
        if side == 1:
            stop_hit, stop_px = lj <= stop, np.minimum(oj, stop)
            tgt_hit = (hj >= target) if target is not None else np.zeros(len(i), dtype=bool)
        else:
            stop_hit, stop_px = hj >= stop, np.maximum(oj, stop)
            tgt_hit = (lj <= target) if target is not None else np.zeros(len(i), dtype=bool)
        live = ~done
        hs = live & stop_hit
        ht = live & ~stop_hit & tgt_hit  # stop first when both are touched in one bar
        px = np.where(hs, stop_px, np.where(ht, target if target is not None else px, px))
        eb = np.where(hs | ht, j, eb)
        cd = np.where(hs, 0, np.where(ht, 1, cd)).astype(np.int8)
        done = done | hs | ht
        if t == T:
            to = ~done
            px = np.where(to, cj, px)
            eb = np.where(to, j, eb)
            cd = np.where(to, 2, cd).astype(np.int8)
    gross[i] = side * (px - entry) / D
    cu[i] = entry / D
    exit_bar[i] = eb
    code[i] = cd
    return dict(gross=gross, cu=cu, exit_bar=exit_bar, code=code)


def simulate_one(o, h, l, c, atr, i: int, side: int, k: float, m, T: int, cost: float):
    """Plain scalar reference implementation of one trade (used by tests to cross-check simulate_all). Returns (R_net, exit_bar, code) or None."""
    n = len(c)
    if i + T > n - 1 or not (atr[i] > 0):
        return None
    entry, D = o[i + 1], k * atr[i]
    stop = entry - D if side == 1 else entry + D
    tgt = None if m is None else (entry + m * D if side == 1 else entry - m * D)
    for j in range(i + 1, i + T + 1):
        if side == 1:
            if l[j] <= stop:
                ex, cd = (o[j] if o[j] < stop else stop), 0
                return (ex - entry - cost * entry) / D, j, cd
            if tgt is not None and h[j] >= tgt:
                return (tgt - entry - cost * entry) / D, j, 1
        else:
            if h[j] >= stop:
                ex, cd = (o[j] if o[j] > stop else stop), 0
                return (entry - ex - cost * entry) / D, j, cd
            if tgt is not None and l[j] <= tgt:
                return (entry - tgt - cost * entry) / D, j, 1
    ex = c[i + T]
    return (side * (ex - entry) - cost * entry) / D, i + T, 2


def select_trades(sig: np.ndarray, exit_long: np.ndarray, exit_short: np.ndarray):
    """One position at a time. A signal at bar i is taken if the previous trade has exited at a bar <= i and the trade is simulable."""
    taken, free = [], 0
    for i in np.flatnonzero(sig):
        if i < free:
            continue
        eb = int(exit_long[i] if sig[i] == 1 else exit_short[i])
        if eb < 0:
            continue
        taken.append((int(i), int(sig[i])))
        free = eb
    return taken


# ----------------------------------------------------------------------------- evaluation
def block_bootstrap(block_id: np.ndarray, series: dict, nb: int, reps: int, rng, lo: float, hi: float) -> dict:
    """Resample whole calendar blocks (all assets together) with replacement; empty blocks stay in the pool.
    Returns {name: (lo_percentile, hi_percentile)} of the resampled mean."""
    cnt = np.bincount(block_id, minlength=nb).astype(float)
    idx = rng.integers(0, nb, size=(reps, nb))
    C = cnt[idx].sum(axis=1)
    good = C > 0
    out = {}
    for name, v in series.items():
        S = np.bincount(block_id, weights=v, minlength=nb)[idx].sum(axis=1)
        mm = S[good] / C[good]
        out[name] = (float(np.percentile(mm, lo)), float(np.percentile(mm, hi)))
    return out


def evaluate_setup(setup: dict, assets: dict, cfg: dict, seed_offset: int = 0) -> dict:
    rows = dict(a=[], s=[], i=[], t=[], g=[], cu=[], mg=[], mcu=[], cd=[], hold=[])
    names = list(assets)
    for ai, name in enumerate(names):
        d = assets[name]
        o, h, l, c = d["o"], d["h"], d["l"], d["c"]
        atr = atr_wilder(h, l, c, 14)
        sig = setup["fn"](o, h, l, c, atr)
        sim = {s: simulate_all(o, h, l, c, atr, s, setup["k"], setup["m"], setup["T"]) for s in (1, -1)}
        base = {}
        for s in (1, -1):
            f = np.isfinite(sim[s]["gross"])
            base[s] = (float(np.mean(sim[s]["gross"][f])), float(np.mean(sim[s]["cu"][f]))) if f.any() else (0.0, 0.0)
        for i, s in select_trades(sig, sim[1]["exit_bar"], sim[-1]["exit_bar"]):
            rows["a"].append(ai); rows["s"].append(s); rows["i"].append(i); rows["t"].append(int(d["t"][i + 1]))
            rows["g"].append(float(sim[s]["gross"][i])); rows["cu"].append(float(sim[s]["cu"][i]))
            rows["mg"].append(base[s][0]); rows["mcu"].append(base[s][1])
            rows["cd"].append(int(sim[s]["code"][i])); rows["hold"].append(int(sim[s]["exit_bar"][i]) - i)
    A = {k: np.asarray(v) for k, v in rows.items()}
    n = len(A["g"])
    res = dict(id=setup["id"], name=setup["name"], k=setup["k"], m=setup["m"], T=setup["T"], n=n)
    if n == 0:
        res.update(verdict="INCONCLUSIVE", criteria={"P1_n": False}, failed=["P1_n"])
        return res
    net = lambda cost: A["g"] - cost * A["cu"]
    exc = lambda cost: net(cost) - (A["mg"] - cost * A["mcu"])
    R, X = net(cfg["cost"]), exc(cfg["cost"])
    ndays = int((cfg["t_end"] - cfg["t0"]) // DAY_MS)
    blk = ((A["t"] - cfg["t0"]) // (cfg["block_days"] * DAY_MS)).astype(np.int64)
    nb = int(ndays // cfg["block_days"]) + 1
    rng = np.random.default_rng(cfg["seed"] + seed_offset)
    bs = block_bootstrap(blk, dict(net=R, exc=X), nb, cfg["reps"], rng, cfg["lo_pct"], cfg["hi_pct"])
    per_asset = {}
    for ai, name in enumerate(names):
        mk = A["a"] == ai
        per_asset[name] = dict(n=int(mk.sum()), mean=float(R[mk].mean()) if mk.any() else None)
    qual = [v for v in per_asset.values() if v["n"] >= cfg["asset_n"]]
    pos_frac = (sum(1 for v in qual if v["mean"] > 0) / len(qual)) if qual else 0.0
    h1, h2 = A["t"] < cfg["split_ms"], A["t"] >= cfg["split_ms"]
    halves = {nm: dict(n=int(mk.sum()), mean=float(R[mk].mean()) if mk.any() else None) for nm, mk in (("before_2022", h1), ("from_2022", h2))}
    years = (A["t"].astype("datetime64[ms]").astype("datetime64[Y]").astype(int) + 1970)
    per_year = {int(y): dict(n=int((years == y).sum()), mean=float(R[years == y].mean())) for y in sorted(set(years.tolist()))}
    per_side = {("long" if s == 1 else "short"): dict(n=int((A["s"] == s).sum()), mean=float(R[A["s"] == s].mean()) if (A["s"] == s).any() else None) for s in (1, -1)}
    res.update(
        mean_net=float(R.mean()), sd=float(R.std(ddof=1)) if n > 1 else None,
        net_lo=bs["net"][0], net_hi=bs["net"][1], mean_excess=float(X.mean()), excess_lo=bs["exc"][0], excess_hi=bs["exc"][1],
        mean_net_low_cost=float(net(cfg["cost_low"]).mean()), mean_net_high_cost=float(net(cfg["cost_high"]).mean()),
        mean_gross=float(A["g"].mean()), baseline_net=float((A["mg"] - cfg["cost"] * A["mcu"]).mean()),
        assets_qualifying=len(qual), assets_positive_frac=pos_frac, per_asset=per_asset, halves=halves, per_year=per_year, per_side=per_side,
        outcome_mix=dict(stop=float((A["cd"] == 0).mean()), target=float((A["cd"] == 1).mean()), time_exit=float((A["cd"] == 2).mean())),
        mean_stop_pct=float((100.0 / A["cu"]).mean()), mean_hold_bars=float(A["hold"].mean()),
        trades_per_asset_year=float(n / max(len(names), 1) / (ndays / 365.25)),
    )
    crit = {
        "P1_n>=%d" % cfg["min_n"]: n >= cfg["min_n"],
        "P2_net_lower99>0": res["net_lo"] > 0,
        "P3_excess_lower99>0": res["excess_lo"] > 0,
        "P4_mean_net>=%.2f" % cfg["min_mean"]: res["mean_net"] >= cfg["min_mean"],
        "P5_high_cost_mean>0": res["mean_net_high_cost"] > 0,
        "P6_assets_pos>=%.0f%%" % (100 * cfg["asset_frac"]): res["assets_qualifying"] >= cfg["min_qual_assets"] and pos_frac >= cfg["asset_frac"],
        "P7_both_halves>0": all(v["n"] >= cfg["half_n"] and v["mean"] is not None and v["mean"] > 0 for v in halves.values()),
    }
    res["criteria"] = crit
    res["failed"] = [k for k, v in crit.items() if not v]
    p1 = crit["P1_n>=%d" % cfg["min_n"]]
    if not res["failed"]:
        res["verdict"] = "PASS"
    elif p1 and res["net_hi"] < cfg["min_mean"]:
        res["verdict"] = "FAIL"
    else:
        res["verdict"] = "INCONCLUSIVE"
    return res


# ----------------------------------------------------------------------------- data
class DataError(Exception):
    pass


def default_http_get(url: str, timeout: int = 30) -> str:
    req = urllib.request.Request(url, headers={"User-Agent": "btc-signal-lab-setuplab/1"})
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return r.read().decode("utf-8")


def _page(symbol: str, start_ms: int, end_ms: int, http_get, hosts, retries: int, sleep) -> list:
    last = None
    for host in hosts:
        url = f"https://{host}/api/v3/klines?symbol={symbol}&interval=1d&startTime={start_ms}&endTime={end_ms - 1}&limit=1000"
        for attempt in range(retries):
            try:
                data = json.loads(http_get(url))
                if isinstance(data, list):
                    return data
                last = f"{host}: unexpected payload {str(data)[:80]}"
            except (urllib.error.URLError, OSError, ValueError) as e:  # HTTPError (e.g. 451) is a URLError
                last = f"{host}: {type(e).__name__} {e}"
            sleep(1.0 * (attempt + 1))
    raise DataError(f"{symbol}: all hosts failed ({last})")


def fetch_klines(symbol: str, http_get=default_http_get, start_ms: int = START_MS, end_ms: int = END_MS, hosts=HOSTS,
                 retries: int = 3, sleep=time.sleep) -> dict:
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


def validate_rows(symbol: str, rows: list) -> dict:
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
    missing = int(((dt // DAY_MS) - 1).sum())
    return dict(symbol=symbol, t=t, o=o, h=h, l=l, c=c, missing_days=missing)


def data_hash(d: dict) -> str:
    hh = hashlib.sha256()
    for k in ("t", "o", "h", "l", "c"):
        hh.update(np.ascontiguousarray(d[k]).tobytes())
    return hh.hexdigest()


def load_assets(http_get=default_http_get, symbols=ASSETS + (REFERENCE,), sleep=time.sleep, **kw) -> tuple[dict, list]:
    got, notes = {}, []
    for s in symbols:
        try:
            d = fetch_klines(s, http_get=http_get, sleep=sleep, **kw)
        except DataError as e:
            notes.append(dict(symbol=s, status="EXCLUDED", reason=str(e)))
            continue
        if len(d["c"]) < MIN_BARS or d["missing_days"] > MAX_MISSING_DAYS:
            notes.append(dict(symbol=s, status="EXCLUDED", reason=f"bars={len(d['c'])} missing_days={d['missing_days']}"))
            continue
        got[s] = d
        notes.append(dict(symbol=s, status="OK", bars=len(d["c"]), missing_days=d["missing_days"],
                          first=time.strftime("%Y-%m-%d", time.gmtime(int(d["t"][0]) / 1000)),
                          last=time.strftime("%Y-%m-%d", time.gmtime(int(d["t"][-1]) / 1000)), sha256=data_hash(d)))
    return got, notes


# ----------------------------------------------------------------------------- run + report
def run_all(assets: dict, cfg: dict = CFG) -> dict:
    pool = {k: v for k, v in assets.items() if k != REFERENCE}
    if len(pool) < MIN_ASSETS:
        raise DataError(f"only {len(pool)} usable assets (< {MIN_ASSETS}); this is an infrastructure failure, not a result")
    out = dict(version=VERSION, pooled=[], reference=[])
    for si, s in enumerate(SETUPS):
        out["pooled"].append(evaluate_setup(s, pool, cfg, si))
        if REFERENCE in assets:
            r = evaluate_setup(s, {REFERENCE: assets[REFERENCE]}, cfg, 100 + si)
            r.pop("verdict", None); r.pop("criteria", None); r.pop("failed", None)
            out["reference"].append(r)
    return out


def _f(x, d=3):
    return "n/a" if x is None else f"{x:+.{d}f}"


def render(out: dict, notes: list, code_sha: str, cfg: dict = CFG) -> str:
    L = [f"# Setup Lab v1 results ({out['version']})", "",
         f"code sha256: `{code_sha}`", "Nothing here is self-certified: the tests of this code are synthetic and written by the same author; no independent review exists.", "",
         "## Data", "| symbol | status | bars | missing | first | last | sha256(data) |", "|---|---|---|---|---|---|---|"]
    for n in notes:
        L.append(f"| {n['symbol']} | {n['status']} | {n.get('bars', '')} | {n.get('missing_days', '')} | {n.get('first', '')} | {n.get('last', '')} | {n.get('sha256', n.get('reason', ''))[:16]} |")
    L += ["", f"## Verdicts (cost {cfg['cost']*100:.2f}% round trip; alpha 0.01 one-sided per setup; 5 setups)", "",
          "| setup | k | m | T | n | mean net R | 99% lower | 99% upper | excess vs random entry | excess 99% lower | high-cost mean | verdict | failed criteria |",
          "|---|---|---|---|---|---|---|---|---|---|---|---|---|"]
    for r in out["pooled"]:
        if r["n"] == 0:
            L.append(f"| {r['id']} {r['name']} | | | | 0 | | | | | | | {r['verdict']} | {', '.join(r['failed'])} |")
            continue
        L.append(f"| {r['id']} {r['name']} | {r['k']} | {r['m']} | {r['T']} | {r['n']} | {_f(r['mean_net'])} | {_f(r['net_lo'])} | {_f(r['net_hi'])} | {_f(r['mean_excess'])} | {_f(r['excess_lo'])} | {_f(r['mean_net_high_cost'])} | **{r['verdict']}** | {', '.join(r['failed']) or '-'} |")
    L += ["", "## Detail per setup (descriptive; the verdict above is the only conclusion)"]
    for r in out["pooled"]:
        if r["n"] == 0:
            continue
        L += ["", f"### {r['id']} {r['name']}",
              f"- trades/asset/year {r['trades_per_asset_year']:.1f}; mean stop distance {r['mean_stop_pct']:.2f}% of price; mean holding {r['mean_hold_bars']:.1f} bars; outcomes stop {r['outcome_mix']['stop']:.0%} / target {r['outcome_mix']['target']:.0%} / time {r['outcome_mix']['time_exit']:.0%}",
              f"- mean gross {_f(r['mean_gross'])} R; random-entry baseline (same exits, every bar) {_f(r['baseline_net'])} R; low-cost mean {_f(r['mean_net_low_cost'])}; high-cost mean {_f(r['mean_net_high_cost'])}",
              "- sides: " + "; ".join(f"{k} n={v['n']} mean={_f(v['mean'])}" for k, v in r["per_side"].items()),
              "- halves: " + "; ".join(f"{k} n={v['n']} mean={_f(v['mean'])}" for k, v in r["halves"].items()),
              "- years: " + "; ".join(f"{y}: n={v['n']} {_f(v['mean'], 2)}" for y, v in r["per_year"].items()),
              "- assets: " + "; ".join(f"{k} n={v['n']} {_f(v['mean'], 2)}" for k, v in r["per_asset"].items()),
              "- criteria: " + "; ".join(f"{k}={'yes' if v else 'NO'}" for k, v in r["criteria"].items())]
    if out["reference"]:
        L += ["", f"## {REFERENCE} reference (burned data: descriptive only, never part of a verdict)", "| setup | n | mean net R |", "|---|---|---|"]
        for r in out["reference"]:
            L.append(f"| {r['id']} | {r['n']} | {_f(r.get('mean_net'))} |")
    return "\n".join(L) + "\n"


def code_sha256() -> str:
    return hashlib.sha256(Path(__file__).read_bytes()).hexdigest()


def main(argv: list) -> int:
    outdir = Path(argv[1]) if len(argv) > 1 else Path("setuplab_out")
    outdir.mkdir(parents=True, exist_ok=True)
    assets, notes = load_assets()
    for n in notes:
        print(n, flush=True)
    out = run_all(assets)
    report = render(out, notes, code_sha256())
    (outdir / "report.md").write_text(report, encoding="utf-8")
    (outdir / "results.json").write_text(json.dumps(dict(out, data=notes, code_sha256=code_sha256()), indent=1, default=float), encoding="utf-8")
    print(report)
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
