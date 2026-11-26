"""Zero-Pip Lab v1: which entry hours of BTCUSDT 1h history were "0-pip" entries (price barely moved against the entry before the
take-profit), what could be observed at the decision time before them, and does any declared pattern survive costs, later years
and other coins.

Preregistration: specs/zero-pip-lab/PREREG_ZEROPIP_v1.md (frozen with this file's SHA-256 before any real-data output).
Nothing here is self-certified: the tests are synthetic and were written by the author of this code, and no independent review exists.
All BTC history is burned (docs/RESEARCH_RULES.md rule 2): a PASS can only mean "worth a forward paper test", never "proven".

Run: python -I -B research/zero-pip-lab/zeropip.py OUTDIR [--end-ms MS]
"""
from __future__ import annotations

import base64
import gzip
import hashlib
import json
import sys
import time
import urllib.error
import urllib.request
from pathlib import Path

import numpy as np

VERSION = "zeropip-v1"
HOUR_MS = 3_600_000
DAY_MS = 24 * HOUR_MS
WEEK_MS = 7 * DAY_MS
START_MS = 1_502_928_000_000  # 2017-08-17T00:00:00Z
SPLIT_MS = 1_672_531_200_000  # 2023-01-01T00:00:00Z: discovery data end / holdout start
END_MS = 1_795_392_000_000  # 2026-11-23T00:00:00Z (exclusive)
HOSTS = ("data-api.binance.vision", "api.binance.com")
BTC = "BTCUSDT"
OTHERS = ("ETHUSDT", "BNBUSDT", "XRPUSDT", "ADAUSDT", "LTCUSDT", "TRXUSDT")
CFG = dict(
    atr_n=14, atr_long_n=168, warmup=480,
    a_primary=1.0, k_primary=3.0, h_primary=24, cost_primary=0.0010,
    a_grid=(0.5, 1.0, 2.0), k_grid=(2.0, 3.0), h_grid=(12, 24), cost_grid=(0.0004, 0.0010, 0.0016),
    clean_m=0.25,
    q_lo=0.20, q_hi=0.80,
    n_min=300, min_weeks=30, top_n=3,
    boot_b=2000, boot_seed=20261124,
    min_effect_r=0.10, min_trades_btc=80, min_trades_others=150, years_needed=3, min_year_trades=10,
    holdout_years=(2023, 2024, 2025, 2026),
    max_missing_frac=0.01,
)
CONT = ("dlow24", "dlow168", "dlow480", "ret6", "ret24", "lowwick", "body", "range", "downrun",
        "atrratio", "volratio", "tbr", "tbr24", "rounddist")
BOOLS = ("sweep24", "sweep168", "s_asia", "s_eu", "s_us", "wkend")


# ----------------------------------------------------------------------------- data
class DataError(Exception):
    pass


def default_http_get(url, timeout=30):
    req = urllib.request.Request(url, headers={"User-Agent": "btc-signal-lab-zeropip/1"})
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return r.read()


def _page(symbol, start_ms, end_ms, http_get, hosts, retries, sleep):
    last = None
    for attempt in range(retries):
        for host in hosts:
            url = (f"https://{host}/api/v3/klines?symbol={symbol}&interval=1h&startTime={start_ms}"
                   f"&endTime={end_ms - 1}&limit=1000")
            try:
                data = json.loads(http_get(url))
                if isinstance(data, list):
                    return data
                last = DataError(f"unexpected response {str(data)[:80]}")
            except (urllib.error.URLError, OSError, ValueError) as e:
                last = e
        sleep(1.5 * (attempt + 1))
    raise DataError(f"{symbol}: fetch failed ({last})")


def fetch_klines(symbol, http_get=default_http_get, start_ms=START_MS, end_ms=END_MS, hosts=HOSTS, retries=3, sleep=time.sleep):
    rows, cur = [], start_ms
    while cur < end_ms:
        page = _page(symbol, cur, end_ms, http_get, hosts, retries, sleep)
        if not page:
            break
        rows.extend(page)
        nxt = int(page[-1][0]) + HOUR_MS
        if nxt <= cur:
            raise DataError(f"{symbol}: pagination did not advance")
        cur = nxt
    if not rows:
        raise DataError(f"{symbol}: no data")
    return rows


def parse_rows(symbol, rows, end_ms=END_MS):
    out, prev = [], None
    for r in rows:
        t = int(r[0])
        o, h, l, c, v = (float(r[i]) for i in (1, 2, 3, 4, 5))
        tb = float(r[9])
        if t % HOUR_MS:
            raise DataError(f"{symbol}: open time {t} is not on the hour")
        if prev is not None and t <= prev:
            raise DataError(f"{symbol}: open times not strictly increasing at {t}")
        if int(r[6]) != t + HOUR_MS - 1:
            raise DataError(f"{symbol}: unexpected close time at {t}")
        if not (l > 0 and l <= min(o, c) and h >= max(o, c) and v >= 0 and 0 <= tb <= v * (1 + 1e-9) + 1e-12):
            raise DataError(f"{symbol}: malformed bar at {t}")
        if t + HOUR_MS > end_ms:
            raise DataError(f"{symbol}: bar {t} extends past the data end")
        prev = t
        out.append((t, o, h, l, c, v, tb))
    if not out:
        raise DataError(f"{symbol}: no bars")
    return out


def build_series(symbol, rows, end_ms=END_MS):
    parsed = parse_rows(symbol, rows, end_ms)
    t0 = parsed[0][0]
    n = int((end_ms - t0) // HOUR_MS)
    arr = {k: np.full(n, np.nan) for k in ("o", "h", "l", "c", "v", "tb")}
    for t, o, h, l, c, v, tb in parsed:
        i = (t - t0) // HOUR_MS
        arr["o"][i], arr["h"][i], arr["l"][i], arr["c"][i], arr["v"][i], arr["tb"][i] = o, h, l, c, v, tb
    missing = int(np.isnan(arr["c"]).sum())
    S = dict(symbol=symbol, t=t0 + HOUR_MS * np.arange(n, dtype=np.int64), ref_o=arr["o"].copy(), ref_c=arr["c"].copy(),
             bars=len(parsed), missing=missing, mirrored=False, **arr)
    return S


def mirror(S):
    """The SHORT view: a short on S is a long on the sign-flipped series (high and low swap, taker buy becomes taker sell)."""
    M = dict(S)
    M.update(o=-S["o"], h=-S["l"], l=-S["h"], c=-S["c"], tb=S["v"] - S["tb"], mirrored=True)
    return M


def data_hash(S):
    hh = hashlib.sha256()
    for k in ("t", "o", "h", "l", "c", "v", "tb"):
        hh.update(np.ascontiguousarray(S[k]).tobytes())
    return hh.hexdigest()


def load_all(symbols, http_get=default_http_get, end_ms=END_MS, sleep=time.sleep, cfg=CFG):
    out, notes = {}, []
    for s in symbols:
        try:
            S = build_series(s, fetch_klines(s, http_get=http_get, end_ms=end_ms, sleep=sleep), end_ms)
        except DataError as e:
            notes.append(dict(symbol=s, status="EXCLUDED", reason=str(e)))
            continue
        frac = S["missing"] / len(S["c"])
        if frac > cfg["max_missing_frac"]:
            notes.append(dict(symbol=s, status="EXCLUDED", reason=f"missing_frac={frac:.4f}"))
            continue
        out[s] = S
        notes.append(dict(symbol=s, status="OK", bars=S["bars"], missing_hours=S["missing"], first=int(S["t"][0]),
                          last=int(S["t"][-1]), sha256=data_hash(S)[:16]))
    return out, notes


# ----------------------------------------------------------------------------- building blocks (trailing windows only)
def roll_apply(x, n, fn):
    """fn over x[i-n+1..i]; NaN until a full window exists; NaN propagates (a gap poisons every window that contains it)."""
    out = np.full(len(x), np.nan)
    if len(x) >= n:
        out[n - 1:] = fn(np.lib.stride_tricks.sliding_window_view(x, n), axis=1)
    return out


def shift(x, k):
    """value k bars earlier"""
    out = np.full(len(x), np.nan)
    if k < len(x):
        out[k:] = x[:len(x) - k]
    return out


def prev_apply(x, n, fn):
    """fn over x[i-n..i-1] (the current bar is excluded)"""
    return shift(roll_apply(x, n, fn), 1)


def true_range(S):
    h, l, c = S["h"], S["l"], S["c"]
    pc = shift(c, 1)
    return np.maximum(np.maximum(h - l, np.abs(h - pc)), np.abs(l - pc))


def atr(S, n=14):
    return roll_apply(true_range(S), n, np.mean)


def features(S, cfg=CFG, a=None):
    """All features at decision index i use bars <= i only (bar i has just closed; the entry is the open of bar i+1)."""
    o, h, l, c, v, tb = (S[k] for k in ("o", "h", "l", "c", "v", "tb"))
    n = len(c)
    with np.errstate(invalid="ignore", divide="ignore"):
        a = atr(S, cfg["atr_n"]) if a is None else a
        sa = np.where(a > 0, a, np.nan)
        tr = true_range(S)
        atr_long = roll_apply(tr, cfg["atr_long_n"], np.mean)
        F = {}
        for name, w in (("dlow24", 24), ("dlow168", 168), ("dlow480", 480)):
            F[name] = (c - roll_apply(l, w, np.min)) / sa
        F["ret6"] = (c - shift(c, 6)) / sa
        F["ret24"] = (c - shift(c, 24)) / sa
        rng = h - l
        F["lowwick"] = (np.minimum(o, c) - l) / np.where(rng > 0, rng, np.nan)
        F["body"] = (c - o) / sa
        F["range"] = rng / sa
        down = np.where(np.isnan(c) | np.isnan(o), np.nan, (c < o).astype(float))
        run = np.full(n, np.nan)
        cnt = 0.0
        for i in range(n):
            d = down[i]
            if d != d:
                cnt = 0.0
            else:
                cnt = cnt + 1.0 if d == 1.0 else 0.0
                run[i] = min(cnt, 8.0)
        F["downrun"] = run
        F["atrratio"] = a / np.where(atr_long > 0, atr_long, np.nan)
        vmean = prev_apply(v, 24, np.mean)
        F["volratio"] = v / np.where(vmean > 0, vmean, np.nan)
        F["tbr"] = tb / np.where(v > 0, v, np.nan)
        sv, st = roll_apply(v, 24, np.sum), roll_apply(tb, 24, np.sum)
        F["tbr24"] = st / np.where(sv > 0, sv, np.nan)
        p = S["ref_c"]
        lvl = 10.0 ** (np.floor(np.log10(p)) - 1.0)
        F["rounddist"] = np.abs(p - np.round(p / lvl) * lvl) / sa
        for name, w in (("sweep24", 24), ("sweep168", 168)):
            pm = prev_apply(l, w, np.min)
            ok = ~(np.isnan(pm) | np.isnan(l) | np.isnan(c))
            F[name] = np.where(ok, ((l < pm) & (c > pm)).astype(float), np.nan)
        t_next = S["t"] + HOUR_MS
        hour = (t_next // HOUR_MS) % 24
        wd = ((t_next // DAY_MS) + 3) % 7  # Monday = 0 (1970-01-01 was a Thursday)
        F["s_asia"] = (hour < 8).astype(float)
        F["s_eu"] = ((hour >= 8) & (hour < 16)).astype(float)
        F["s_us"] = (hour >= 16).astype(float)
        F["wkend"] = (wd >= 5).astype(float)
    return F


def outcomes(S, a_mult, k, h, cost, cfg=CFG, a=None):
    """Bracket outcome of a LONG entered at the open of bar i+1 (decision at the close of bar i):
    stop = entry - a_mult*ATR14(i), take profit = entry + k*stop distance, horizon h bars.
    Within one bar the stop is assumed to hit first. Timeout exits at the close of the last bar. Cost is a round-trip fraction of the
    original (unmirrored) price, converted to R by the stop distance. mae is the worst excursion against the entry in stop units
    (the take-profit bar's own low counts, which is conservative)."""
    n = len(S["c"])
    a = atr(S, cfg["atr_n"]) if a is None else a
    o, hi, lo, c = S["o"], S["h"], S["l"], S["c"]
    entry = np.full(n, np.nan)
    entry[:-1] = o[1:]
    ref_entry = np.full(n, np.nan)
    ref_entry[:-1] = S["ref_o"][1:]
    with np.errstate(invalid="ignore", divide="ignore"):
        sd = a_mult * a
        sd = np.where(sd > 0, sd, np.nan)
        stop = entry - sd
        tp = entry + k * sd
        win_ok = ~(np.isnan(entry) | np.isnan(sd))
        alive = win_ok.copy()
        res = np.zeros(n, dtype=np.int8)  # 0 invalid, 1 take profit, 2 stop, 3 timeout
        mae = np.zeros(n)
        exit_bar = np.full(n, -1, dtype=np.int64)
        gross = np.full(n, np.nan)
        idx = np.arange(n)
        for d in range(h):
            b = idx + 1 + d
            inside = b < n
            lo_d = np.full(n, np.nan)
            hi_d = np.full(n, np.nan)
            lo_d[inside] = lo[b[inside]]
            hi_d[inside] = hi[b[inside]]
            win_ok &= ~(np.isnan(lo_d) | np.isnan(hi_d))  # validity needs the WHOLE window, whatever the outcome (no censoring bias)
            hit_stop = alive & (lo_d <= stop)
            hit_tp = alive & ~hit_stop & (hi_d >= tp)
            mae = np.where(alive, np.maximum(mae, (entry - lo_d) / sd), mae)
            res[hit_stop] = 2
            res[hit_tp] = 1
            gross[hit_stop] = -1.0
            gross[hit_tp] = k
            done = hit_stop | hit_tp
            exit_bar[done] = b[done]
            alive = alive & ~done
        to = alive & win_ok
        res[to] = 3
        exit_bar[to] = idx[to] + h
        gross[to] = (c[exit_bar[to]] - entry[to]) / sd[to]
        bad = ~win_ok
        res[bad] = 0
        gross[bad] = np.nan
        exit_bar[bad] = -1
        cost_r = cost * ref_entry / sd
        net = gross - cost_r
        mae = np.where(res > 0, mae, np.nan)
    clean = (res == 1) & (mae <= cfg["clean_m"])
    return dict(res=res, gross=gross, net=net, mae=mae, exit_bar=exit_bar, sd=sd, entry=entry, ref_entry=ref_entry, clean=clean,
                a_mult=a_mult, k=k, h=h, cost=cost)


def with_cost(out, cost):
    o = dict(out)
    o["net"] = out["gross"] - cost * out["ref_entry"] / out["sd"]
    o["cost"] = cost
    return o


def year_of(t_ms):
    return np.asarray(t_ms, dtype="int64").astype("datetime64[ms]").astype("datetime64[Y]").astype(int) + 1970


def week_ids(S):
    """calendar-week cluster id of the ENTRY bar (open of bar i+1), common to every coin"""
    return (S["t"] + HOUR_MS - START_MS) // WEEK_MS


def masks_for(S, out, cfg=CFG):
    n = len(S["t"])
    idx = np.arange(n)
    split_idx = int(np.searchsorted(S["t"], SPLIT_MS))
    base = (idx >= cfg["warmup"]) & (out["res"] > 0)
    disc = base & (idx + out["h"] < split_idx)  # even the latest possible exit (bar i+h) is before 2023-01-01; same for both directions
    hold = base & (idx + 1 >= split_idx)  # the entry bar opens on or after 2023-01-01
    return dict(disc=disc, hold=hold, base=base, split_idx=split_idx)


# ----------------------------------------------------------------------------- rules
def single_rules():
    rules = []
    for f in CONT:
        rules.append((f + "<=q20", f, "lo"))
        rules.append((f + ">=q80", f, "hi"))
    for b in BOOLS:
        rules.append((b + "==1", b, "bool"))
    return rules


def thresholds(F, S, cfg=CFG):
    """tail thresholds from decisions whose information was complete before 2023-01-01 (nothing from the holdout)"""
    avail = (S["t"] + HOUR_MS <= SPLIT_MS) & (np.arange(len(S["t"])) >= cfg["warmup"])
    thr = {}
    for f in CONT:
        x = F[f][avail]
        x = x[~np.isnan(x)]
        if len(x) < 100:
            raise DataError(f"too little discovery data for {f}")
        thr[f] = (float(np.quantile(x, cfg["q_lo"])), float(np.quantile(x, cfg["q_hi"])))
    return thr


def single_masks(F, thr):
    m = {}
    for name, f, kind in single_rules():
        x = F[f]
        with np.errstate(invalid="ignore"):
            m[name] = (x <= thr[f][0]) if kind == "lo" else (x >= thr[f][1]) if kind == "hi" else (x == 1.0)
    return m


def base_feature(rule_name):
    return rule_name.split("<=")[0].split(">=")[0].split("==")[0]


def rule_list():
    """declared family: every single rule and every pair of single rules on two different features"""
    singles = [r[0] for r in single_rules()]
    pairs = []
    for i in range(len(singles)):
        for j in range(i + 1, len(singles)):
            if base_feature(singles[i]) != base_feature(singles[j]):
                pairs.append(singles[i] + " & " + singles[j])
    return singles, pairs


def rule_mask(name, masks):
    parts = name.split(" & ")
    m = masks[parts[0]]
    for p in parts[1:]:
        m = m & masks[p]
    return m


# ----------------------------------------------------------------------------- statistics
def sequential_trades(sig, out):
    """one position at a time: the first signal while flat, flat again when the trade resolved (a new decision may use the close of the
    resolving bar)"""
    cand = np.flatnonzero(sig & (out["res"] > 0))
    taken, free = [], -1
    xb = out["exit_bar"]
    for i in cand:
        if i < free:
            continue
        taken.append(int(i))
        free = int(xb[i])
    return np.array(taken, dtype=np.int64)


def trade_stats(idx, out):
    n = len(idx)
    if n == 0:
        return dict(n=0, win=None, clean=None, stop=None, timeout=None, mean=None, sd=None, sum=0.0)
    r = out["net"][idx]
    res = out["res"][idx]
    return dict(n=int(n), win=float((res == 1).mean()), clean=float(out["clean"][idx].mean()), stop=float((res == 2).mean()),
                timeout=float((res == 3).mean()), mean=float(r.mean()), sd=float(r.std(ddof=1)) if n > 1 else None, sum=float(r.sum()))


def boot_ci(parts, cfg=CFG, seed_off=0):
    """cluster bootstrap by calendar week; parts = list of (net values, week ids); returns the 90% interval of the pooled mean"""
    if not parts:
        return (None, None)
    net = np.concatenate([np.asarray(p[0], dtype=float) for p in parts])
    wk = np.concatenate([np.asarray(p[1], dtype=np.int64) for p in parts])
    if len(net) == 0:
        return (None, None)
    ww = wk - wk.min()
    W = int(ww.max()) + 1
    sR = np.bincount(ww, weights=net, minlength=W)
    nW = np.bincount(ww, minlength=W).astype(float)
    rng = np.random.default_rng(cfg["boot_seed"] + seed_off)
    pick = rng.integers(0, W, size=(cfg["boot_b"], W))
    num, den = sR[pick].sum(axis=1), nW[pick].sum(axis=1)
    m = num / np.where(den > 0, den, np.nan)
    return (float(np.nanpercentile(m, 5)), float(np.nanpercentile(m, 95)))


def eval_rule(sig, S, out, mask, cfg=CFG, seed_off=0):
    """sequential-policy statistics of a rule inside a period mask, with a week-cluster bootstrap interval"""
    idx = sequential_trades(sig & mask, out)
    st = trade_stats(idx, out)
    st["ci90"] = boot_ci([(out["net"][idx], week_ids(S)[idx])], cfg, seed_off) if len(idx) else (None, None)
    return st, idx


def by_year(idx, S, out, years):
    if len(idx) == 0:
        return {int(y): dict(n=0, mean=None) for y in years}
    yr = year_of(S["t"][idx + 1])
    res = {}
    for y in years:
        sel = idx[yr == y]
        res[int(y)] = dict(n=int(len(sel)), mean=float(out["net"][sel].mean()) if len(sel) else None)
    return res


def month_ids(S, idx):
    """calendar-month id of the ENTRY bar (the open of bar i+1) for decision indices idx"""
    return np.asarray(S["t"][idx + 1], dtype="int64").astype("datetime64[ms]").astype("datetime64[M]").astype(np.int64)


def demean_by_month(x, mon):
    """subtract the mean of the calendar month (over the valid discovery hours of that month). The ranking statistic then asks for timing
    information INSIDE a month; a rule that merely picks bull months (or bear months) gets no credit."""
    _, inv = np.unique(mon, return_inverse=True)
    inv = inv.reshape(-1)
    s = np.bincount(inv, weights=x)
    c = np.bincount(inv).astype(float)
    return x - (s / c)[inv]


def cluster_t(M, x, wk, chunk=64):
    """Week-clustered t statistic of the mean of x over the hours of each rule.
    M: (rules, n) 0/1 matrix; x: (n,) outcome (already centred); wk: (n,) non-decreasing calendar-week ids.
    theta = sum(M x) / sum(M); se^2 = G/(G-1) * sum_w (a_w - theta*n_w)^2 / N^2, where a_w is the sum of x over the rule's hours of week w,
    n_w their number and G the number of weeks containing at least one rule hour. Brackets of neighbouring hours overlap (so their outcomes
    are dependent); the calendar week is the independent unit. Returns (theta, t, N, G)."""
    starts = np.flatnonzero(np.r_[True, np.diff(wk) != 0])
    th, tt, nn, gg = [], [], [], []
    for a in range(0, M.shape[0], chunk):
        Mc = M[a:a + chunk].astype(np.float64)
        aw = np.add.reduceat(Mc * x[None, :], starts, axis=1)
        nw = np.add.reduceat(Mc, starts, axis=1)
        N = nw.sum(axis=1)
        theta = aw.sum(axis=1) / N
        G = (nw > 0).sum(axis=1).astype(float)
        with np.errstate(divide="ignore", invalid="ignore"):
            se = np.sqrt(G / (G - 1.0) * ((aw - theta[:, None] * nw) ** 2).sum(axis=1)) / N
            t = np.where(se > 0, theta / se, np.nan)
        th.append(theta)
        tt.append(t)
        nn.append(N)
        gg.append(G)
    return np.concatenate(th), np.concatenate(tt), np.concatenate(nn), np.concatenate(gg)


def discover(P, cfg=CFG):
    """P = prepare(BTC series). For each direction every eligible rule of the declared family (>= n_min discovery hours in >= min_weeks
    weeks) is ranked by the week-clustered t of its mean GROSS R after subtracting the calendar-month mean. Discovery hours only.
    No p-value is produced: the ranking only decides WHICH rules are evaluated; the decision comes from the untouched holdout and the
    other coins. (An earlier draft computed a family-wise permutation p-value here; at real size its null was mis-calibrated and it was
    dropped before any real-data output.)"""
    singles, pairs = rule_list()
    names_all = singles + pairs
    pm = masks_for(P["long"]["S"], P["long"]["out"], cfg)
    disc = pm["disc"]
    if int(disc.sum()) < 5000:
        raise DataError("discovery sample too small")
    idx = np.flatnonzero(disc)
    tabs = {}
    for d in ("long", "short"):
        Pd = P[d]
        S, out = Pd["S"], Pd["out"]
        if not np.array_equal(masks_for(S, out, cfg)["disc"], disc):
            raise DataError("the two directions disagree on the discovery sample")
        thr = thresholds(Pd["F"], S, cfg)
        sm = single_masks(Pd["F"], thr)
        gross, net = out["gross"][idx], out["net"][idx]
        win, cln = (out["res"][idx] == 1), out["clean"][idx]
        wk, mon = week_ids(S)[idx], month_ids(S, idx)
        x = demean_by_month(gross, mon)
        rows, mats = [], []
        for nm in names_all:
            m = rule_mask(nm, sm)[idx]
            if int(m.sum()) >= cfg["n_min"]:
                rows.append(nm)
                mats.append(m)
        M = np.stack(mats, axis=0).astype(np.float32)
        theta, t, N, G = cluster_t(M, x, wk)
        keep = np.isfinite(t) & (G >= cfg["min_weeks"])
        Mk = M[keep].astype(np.float64)
        Nk = Mk.sum(axis=1)
        tabs[d] = dict(names=[r for r, k in zip(rows, keep) if k], n=Nk, weeks=G[keep], t=t[keep], theta=theta[keep],
                       mean_gross=(Mk @ gross) / Nk, mean_net=(Mk @ net) / Nk,
                       win=(Mk @ win.astype(np.float64)) / Nk, clean=(Mk @ cln.astype(np.float64)) / Nk,
                       base_gross=float(gross.mean()), base_net=float(net.mean()), base_win=float(win.mean()), base_clean=float(cln.mean()),
                       thr=thr, eligible_before_week_filter=len(rows), dropped_by_week_filter=int((~keep).sum()))
    return tabs, pm


def pick_top(tab, cfg=CFG):
    """the top_n rules by clustered t (ties: declared order)"""
    order = np.argsort(-tab["t"], kind="stable")
    return [int(i) for i in order[: cfg["top_n"]]]


def clean_profile(P_dir, disc, cfg=CFG):
    """median of every continuous feature at CLEAN entries versus all valid discovery entries, and the percentile of the CLEAN median"""
    F, out = P_dir["F"], P_dir["out"]
    cl = disc & out["clean"]
    prof = {}
    for f in CONT:
        x_all = F[f][disc]
        x_all = x_all[~np.isnan(x_all)]
        x_cl = F[f][cl]
        x_cl = x_cl[~np.isnan(x_cl)]
        if len(x_cl) < 20 or len(x_all) < 100:
            continue
        med = float(np.median(x_cl))
        prof[f] = dict(clean_median=med, all_median=float(np.median(x_all)), clean_pctile=float((x_all <= med).mean()), n_clean=int(len(x_cl)))
    return prof


# ----------------------------------------------------------------------------- study
def prepare(S, cfg=CFG):
    P = {}
    for d, Sd in (("long", S), ("short", mirror(S))):
        a = atr(Sd, cfg["atr_n"])
        P[d] = dict(S=Sd, a=a, F=features(Sd, cfg, a=a),
                    out=outcomes(Sd, cfg["a_primary"], cfg["k_primary"], cfg["h_primary"], cfg["cost_primary"], cfg, a=a))
    return P


def oracle_tables(P, cfg=CFG):
    """descriptive base rates for BTC: how often a bracket wins, how often it wins 'clean', and what entering at every free hour earns"""
    rows = []
    for d in ("long", "short"):
        Sd, a = P[d]["S"], P[d]["a"]
        for am in cfg["a_grid"]:
            for k in cfg["k_grid"]:
                for h in cfg["h_grid"]:
                    out = outcomes(Sd, am, k, h, cfg["cost_primary"], cfg, a=a)
                    pm = masks_for(Sd, out, cfg)
                    for per, m in (("discovery", pm["disc"]), ("holdout", pm["hold"])):
                        nv = int(m.sum())
                        if nv == 0:
                            continue
                        win = (out["res"][m] == 1)
                        rec = dict(dir=d, a=am, k=k, h=h, period=per, hours=nv, p_win=float(win.mean()), p_clean=float(out["clean"][m].mean()),
                                   clean_share_of_wins=float(out["clean"][m].sum() / max(1, win.sum())),
                                   mean_gross_r=float(np.nanmean(out["gross"][m])),
                                   stop_pct_of_price=float(np.nanmedian((out["sd"][m] / out["ref_entry"][m]) * 100.0)))
                        for c in cfg["cost_grid"]:
                            oc = with_cost(out, c)
                            rec[f"mean_net_r_cost_{int(round(c * 1e4))}bp"] = float(np.nanmean(oc["net"][m]))
                        idx_all = sequential_trades(m, out)
                        idx_cl = sequential_trades(m & out["clean"], out)
                        yrs = max(1e-9, (Sd["t"][np.flatnonzero(m)[-1]] - Sd["t"][np.flatnonzero(m)[0]]) / (365.25 * DAY_MS))
                        rec["flat_entry_trades_per_week"] = float(len(idx_all) / (yrs * 52.18))
                        rec["oracle_clean_points_per_week"] = float(len(idx_cl) / (yrs * 52.18))
                        rec["flat_entry_mean_net_r"] = float(out["net"][idx_all].mean()) if len(idx_all) else None
                        rows.append(rec)
    return rows


def boot_diff_ci(parts_a, parts_b, cfg=CFG, seed_off=0):
    """week-cluster bootstrap of mean(a) - mean(b); a and b are lists of (net values, week ids) and both means are recomputed on the SAME
    resampled weeks. Returns (lower 5%, upper 95%, point estimate), or (None, None, None) when either side is empty."""
    def pack(parts):
        if not parts:
            return np.array([]), np.array([], dtype=np.int64)
        return (np.concatenate([np.asarray(p[0], dtype=float) for p in parts]),
                np.concatenate([np.asarray(p[1], dtype=np.int64) for p in parts]))
    na, wa = pack(parts_a)
    nb, wb = pack(parts_b)
    if len(na) == 0 or len(nb) == 0:
        return (None, None, None)
    w0 = int(min(wa.min(), wb.min()))
    W = int(max(wa.max(), wb.max())) - w0 + 1
    sa, ca = np.bincount(wa - w0, weights=na, minlength=W), np.bincount(wa - w0, minlength=W).astype(float)
    sb, cb = np.bincount(wb - w0, weights=nb, minlength=W), np.bincount(wb - w0, minlength=W).astype(float)
    rng = np.random.default_rng(cfg["boot_seed"] + seed_off)
    pick = rng.integers(0, W, size=(cfg["boot_b"], W))
    da, db = ca[pick].sum(axis=1), cb[pick].sum(axis=1)
    with np.errstate(invalid="ignore", divide="ignore"):
        m = sa[pick].sum(axis=1) / np.where(da > 0, da, np.nan) - sb[pick].sum(axis=1) / np.where(db > 0, db, np.nan)
    return (float(np.nanpercentile(m, 5)), float(np.nanpercentile(m, 95)), float(na.mean() - nb.mean()))


def evaluate_selected(P_btc, tabs, picks, others_P, cfg=CFG):
    """picks: {direction: [row indices]}; every rule is evaluated unchanged on BTC (discovery and holdout) and on the other coins.
    Besides its absolute mean net R, a rule must beat the SAME one-position-at-a-time policy applied to every free hour of the same
    period and coin (the 'lift'), so a rising (or falling) market by itself cannot approve a rule."""
    evals = []
    for d, ids in picks.items():
        tab = tabs[d]
        Pd = P_btc[d]
        sm = single_masks(Pd["F"], tab["thr"])
        pm = masks_for(Pd["S"], Pd["out"], cfg)
        wkb = week_ids(Pd["S"])
        idx_base = sequential_trades(pm["hold"], Pd["out"])
        base_h = trade_stats(idx_base, Pd["out"])
        others_base = {}
        for sym, Po in others_P.items():
            pmo = masks_for(Po[d]["S"], Po[d]["out"], cfg)
            others_base[sym] = sequential_trades(pmo["hold"], Po[d]["out"])
        for rank, r in enumerate(ids, start=1):
            nm = tab["names"][r]
            sig = rule_mask(nm, sm)
            ev = dict(direction=d, rule=nm, rank=rank, t=float(tab["t"][r]), hours=int(tab["n"][r]), weeks=int(tab["weeks"][r]),
                      disc_theta=float(tab["theta"][r]), disc_mean_gross=float(tab["mean_gross"][r]), disc_mean_net=float(tab["mean_net"][r]),
                      disc_win=float(tab["win"][r]), disc_clean=float(tab["clean"][r]), base_gross=tab["base_gross"],
                      base_net=tab["base_net"], base_win=tab["base_win"], base_clean=tab["base_clean"])
            st_d, _ = eval_rule(sig, Pd["S"], Pd["out"], pm["disc"], cfg, 1)
            st_h, idx_h = eval_rule(sig, Pd["S"], Pd["out"], pm["hold"], cfg, 2)
            ev["btc_discovery"] = st_d
            ev["btc_holdout"] = st_h
            ev["btc_holdout_baseline"] = base_h
            lo, hi, pt = boot_diff_ci([(Pd["out"]["net"][idx_h], wkb[idx_h])], [(Pd["out"]["net"][idx_base], wkb[idx_base])], cfg, 4)
            ev["btc_holdout_lift"] = dict(point=pt, ci90=(lo, hi))
            ev["btc_holdout_years"] = by_year(idx_h, Pd["S"], Pd["out"], cfg["holdout_years"])
            sens = {}
            for c in cfg["cost_grid"]:
                oc = with_cost(Pd["out"], c)
                idx = sequential_trades(sig & pm["hold"], oc)
                sens[f"cost_{int(round(c * 1e4))}bp"] = trade_stats(idx, oc)["mean"]
            ev["btc_holdout_cost_sensitivity"] = sens
            parts_h, parts_a, parts_b, per_coin = [], [], [], {}
            net_h, net_a = [], []
            for sym, Po in others_P.items():
                Po_d = Po[d]
                smo = single_masks(Po_d["F"], tab["thr"])
                sigo = rule_mask(nm, smo)
                pmo = masks_for(Po_d["S"], Po_d["out"], cfg)
                idx_hc = sequential_trades(sigo & pmo["hold"], Po_d["out"])
                idx_ac = sequential_trades(sigo & pmo["base"], Po_d["out"])
                idx_bc = others_base[sym]
                w = week_ids(Po_d["S"])
                parts_h.append((Po_d["out"]["net"][idx_hc], w[idx_hc]))
                parts_a.append((Po_d["out"]["net"][idx_ac], w[idx_ac]))
                parts_b.append((Po_d["out"]["net"][idx_bc], w[idx_bc]))
                net_h.append(Po_d["out"]["net"][idx_hc])
                net_a.append(Po_d["out"]["net"][idx_ac])
                per_coin[sym] = dict(holdout=trade_stats(idx_hc, Po_d["out"]), holdout_baseline=trade_stats(idx_bc, Po_d["out"]),
                                     all_period=trade_stats(idx_ac, Po_d["out"]))
            for key, parts, nets in (("others_holdout", parts_h, net_h), ("others_all_period", parts_a, net_a)):
                allnet = np.concatenate(nets) if nets else np.array([])
                ev[key] = dict(n=int(len(allnet)), mean=float(allnet.mean()) if len(allnet) else None,
                               ci90=boot_ci(parts, cfg, 3) if len(allnet) else (None, None))
            lo, hi, pt = boot_diff_ci(parts_h, parts_b, cfg, 5)
            ev["others_holdout_lift"] = dict(point=pt, ci90=(lo, hi))
            ev["per_coin"] = per_coin
            ev["verdict"] = verdict(ev, cfg)
            evals.append(ev)
    return evals


def verdict(ev, cfg=CFG):
    """H1 BTC holdout: enough trades, mean net R >= min_effect_r with a positive 90% lower bound, AND a positive lower bound of the lift over
    the all-free-hours policy. H2 other coins (pooled holdout): enough trades, mean > 0 with a positive lower bound AND a positive lift lower
    bound. H3 at least years_needed of the holdout years positive (each with at least min_year_trades trades)."""
    h, o = ev["btc_holdout"], ev["others_holdout"]
    lh, lo_ = ev["btc_holdout_lift"], ev["others_holdout_lift"]
    yrs = ev["btc_holdout_years"]
    pos_years = sum(1 for y in yrs.values() if y["n"] >= cfg["min_year_trades"] and y["mean"] is not None and y["mean"] > 0)

    def pos(ci):
        return ci[0] is not None and ci[0] > 0
    h1_n = h["n"] >= cfg["min_trades_btc"]
    h2_n = o["n"] >= cfg["min_trades_others"]
    h1 = bool(h1_n and h["mean"] is not None and h["mean"] >= cfg["min_effect_r"] and pos(h["ci90"]) and pos(lh["ci90"]))
    h2 = bool(h2_n and o["mean"] is not None and o["mean"] > 0 and pos(o["ci90"]) and pos(lo_["ci90"]))
    h3 = pos_years >= cfg["years_needed"]
    crit = dict(H1_btc_holdout=h1, H2_other_coins_holdout=h2, H3_years=h3, enough_n_btc=h1_n, enough_n_others=h2_n, positive_years=pos_years)
    if h1 and h2 and h3:
        v = "PASS"
    elif not (h1_n and h2_n):
        v = "INCONCLUSIVE"
    else:
        v = "FAIL"
    return dict(label=v, criteria=crit)


def run_study(series, cfg=CFG):
    """series: {symbol: series dict}; BTC is mandatory. Returns the full result dictionary."""
    if BTC not in series:
        raise DataError("BTCUSDT is required")
    P_btc = prepare(series[BTC], cfg)
    others_P = {s: prepare(S, cfg) for s, S in series.items() if s != BTC}
    tabs, pm = discover(P_btc, cfg)
    picks = {d: pick_top(tabs[d], cfg) for d in tabs}
    evals = evaluate_selected(P_btc, tabs, picks, others_P, cfg)
    res = dict(version=VERSION, config={k: (list(v) if isinstance(v, tuple) else v) for k, v in cfg.items()},
               oracle=oracle_tables(P_btc, cfg), evaluations=evals,
               family=dict(singles=len(rule_list()[0]), pairs=len(rule_list()[1]),
                           eligible={d: len(tabs[d]["names"]) for d in tabs},
                           eligible_before_week_filter={d: tabs[d]["eligible_before_week_filter"] for d in tabs}),
               discovery_hours=int(pm["disc"].sum()))
    top = {}
    for d in tabs:
        order = np.argsort(-tabs[d]["t"], kind="stable")[:12]
        top[d] = [dict(rule=tabs[d]["names"][i], hours=int(tabs[d]["n"][i]), weeks=int(tabs[d]["weeks"][i]), t=float(tabs[d]["t"][i]),
                       theta=float(tabs[d]["theta"][i]), mean_gross=float(tabs[d]["mean_gross"][i]), mean_net=float(tabs[d]["mean_net"][i]),
                       p_win=float(tabs[d]["win"][i]), p_clean=float(tabs[d]["clean"][i])) for i in order]
        top[d + "_base"] = dict(p_win=tabs[d]["base_win"], p_clean=tabs[d]["base_clean"], mean_gross=tabs[d]["base_gross"],
                                mean_net=tabs[d]["base_net"])
    res["top_rules"] = top
    topc = {}
    for d in tabs:  # exploratory only: the rules whose discovery hours most often end CLEAN (not used for selection, never evaluated)
        order = np.argsort(-tabs[d]["clean"], kind="stable")[:12]
        topc[d] = [dict(rule=tabs[d]["names"][i], hours=int(tabs[d]["n"][i]), weeks=int(tabs[d]["weeks"][i]), t=float(tabs[d]["t"][i]),
                        mean_gross=float(tabs[d]["mean_gross"][i]), mean_net=float(tabs[d]["mean_net"][i]),
                        p_win=float(tabs[d]["win"][i]), p_clean=float(tabs[d]["clean"][i])) for i in order]
    res["top_clean_rules"] = topc
    res["clean_profile"] = {d: clean_profile(P_btc[d], pm["disc"], cfg) for d in ("long", "short")}
    sel = [e for e in evals if e["verdict"]["label"] == "PASS"]
    res["overall"] = ("CANDIDATE_FOR_FORWARD_TEST" if sel else "NO_CANDIDATE")
    return res


# ----------------------------------------------------------------------------- output
def encode_chunks(obj, width=3000):
    raw = json.dumps(obj, sort_keys=True, separators=(",", ":"), default=_json_default).encode()
    b = base64.b64encode(gzip.compress(raw, 9, mtime=0)).decode()
    return [b[i:i + width] for i in range(0, len(b), width)]


def decode_chunks(chunks):
    return json.loads(gzip.decompress(base64.b64decode("".join(chunks))))


def _json_default(o):
    if isinstance(o, (np.integer,)):
        return int(o)
    if isinstance(o, (np.floating,)):
        return float(o)
    if isinstance(o, np.ndarray):
        return o.tolist()
    raise TypeError(type(o))


def _f(x, d=3):
    return "n/a" if x is None else f"{x:.{d}f}"


def render(res, notes, code_sha):
    L = [f"# Zero-Pip Lab v1 report ({VERSION})", "",
         "Descriptive and exploratory. All BTC history is burned (RESEARCH_RULES rule 2). Tests are synthetic and by the same author; no independent review.",
         f"Code SHA-256: `{code_sha}`", "", "## Data", "", "| coin | status | bars | missing hours | sha256 (prefix) |", "|---|---|---|---|---|"]
    for n in notes:
        L.append(f"| {n['symbol']} | {n['status']} | {n.get('bars', '')} | {n.get('missing_hours', n.get('reason', ''))} | {n.get('sha256', '')} |")
    L += ["", f"Overall: **{res['overall']}**", "", "## Base rates (BTC, entering at a free hour; cost 0.10% round trip unless stated)", "",
          "| dir | stop (xATR) | TP (xstop) | h | period | hours | P(win) | P(clean) | clean share of wins | stop % price | mean net R @0.04% | @0.10% | @0.16% | oracle clean pts/week |",
          "|---|---|---|---|---|---|---|---|---|---|---|---|---|---|"]
    for r in res["oracle"]:
        L.append(f"| {r['dir']} | {r['a']} | {r['k']} | {r['h']} | {r['period']} | {r['hours']} | {_f(r['p_win'])} | {_f(r['p_clean'])} | "
                 f"{_f(r['clean_share_of_wins'])} | {_f(r['stop_pct_of_price'], 2)} | {_f(r['mean_net_r_cost_4bp'])} | {_f(r['mean_net_r_cost_10bp'])} | "
                 f"{_f(r['mean_net_r_cost_16bp'])} | {_f(r['oracle_clean_points_per_week'], 2)} |")
    L += ["", "## Declared family", "", f"{res['family']}", ""]
    for d in ("long", "short"):
        b = res["top_rules"][d + "_base"]
        L += [f"### Top discovery rules, {d} (ranked by week-clustered t of month-demeaned gross R; all discovery hours: P(win) {_f(b['p_win'])}, "
              f"P(clean) {_f(b['p_clean'])}, mean gross R {_f(b['mean_gross'])}, mean net R {_f(b['mean_net'])})", "",
              "| rule | hours | weeks | t | month-demeaned gross R | mean gross R | mean net R | P(win) | P(clean) |", "|---|---|---|---|---|---|---|---|---|"]
        for t in res["top_rules"][d]:
            L.append(f"| {t['rule']} | {t['hours']} | {t['weeks']} | {_f(t['t'], 2)} | {_f(t['theta'])} | {_f(t['mean_gross'])} | {_f(t['mean_net'])} | "
                     f"{_f(t['p_win'])} | {_f(t['p_clean'])} |")
        L.append("")
        b = res["top_rules"][d + "_base"]
        L += [f"### Exploratory, {d}: rules with the highest P(clean) in discovery (best of the family by one column; not used for selection; base P(clean) {_f(b['p_clean'])})", "",
              "| rule | hours | weeks | P(clean) | P(win) | mean gross R | mean net R | t of month-demeaned gross R |", "|---|---|---|---|---|---|---|---|"]
        for t in res["top_clean_rules"][d]:
            L.append(f"| {t['rule']} | {t['hours']} | {t['weeks']} | {_f(t['p_clean'])} | {_f(t['p_win'])} | {_f(t['mean_gross'])} | {_f(t['mean_net'])} | {_f(t['t'], 2)} |")
        L.append("")
        L += [f"### CLEAN-entry feature medians, {d} (discovery)", "", "| feature | median at CLEAN | median overall | percentile of CLEAN median |", "|---|---|---|---|"]
        for f, v in res["clean_profile"][d].items():
            L.append(f"| {f} | {_f(v['clean_median'])} | {_f(v['all_median'])} | {_f(v['clean_pctile'], 2)} |")
        L.append("")
    L += ["## Evaluated rules (top rules of the discovery ranking, unchanged on the holdout and on the other coins)", "",
          "| dir | rank | rule | verdict | disc trades | BTC holdout n | mean net R | 90% CI | lift vs all free hours | 90% CI | years>0 | other coins n | mean net R | 90% CI | lift | 90% CI |",
          "|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|"]
    for e in res["evaluations"]:
        h, o = e["btc_holdout"], e["others_holdout"]
        lh, lo_ = e["btc_holdout_lift"], e["others_holdout_lift"]
        L.append(f"| {e['direction']} | {e['rank']} | {e['rule']} | {e['verdict']['label']} | {e['btc_discovery']['n']} | {h['n']} | {_f(h['mean'])} | "
                 f"{_f(h['ci90'][0])}..{_f(h['ci90'][1])} | {_f(lh['point'])} | {_f(lh['ci90'][0])}..{_f(lh['ci90'][1])} | "
                 f"{e['verdict']['criteria']['positive_years']} | {o['n']} | {_f(o['mean'])} | {_f(o['ci90'][0])}..{_f(o['ci90'][1])} | "
                 f"{_f(lo_['point'])} | {_f(lo_['ci90'][0])}..{_f(lo_['ci90'][1])} |")
    return "\n".join(L) + "\n"


def code_sha256():
    return hashlib.sha256(Path(__file__).read_bytes()).hexdigest()


def main(argv):
    outdir = Path(argv[1] if len(argv) > 1 and not argv[1].startswith("--") else "zeropip_out")
    end_ms = END_MS
    if "--end-ms" in argv:
        end_ms = int(argv[argv.index("--end-ms") + 1])
    outdir.mkdir(parents=True, exist_ok=True)
    series, notes = load_all((BTC,) + OTHERS, end_ms=end_ms)
    if BTC not in series:
        raise SystemExit("BTCUSDT unavailable: infrastructure failure, not a result")
    res = run_study(series)
    sha = code_sha256()
    res["code_sha256"] = sha
    res["data_notes"] = notes
    txt = render(res, notes, sha)
    (outdir / "report.md").write_text(txt, encoding="utf-8")
    (outdir / "results.json").write_text(json.dumps(res, sort_keys=True, default=_json_default), encoding="utf-8")
    chunks = encode_chunks(res)
    print(txt)
    print(f"ZP_JSON_BEGIN lines={len(chunks)}")
    for i, ch in enumerate(chunks):
        print(f"ZP|{i}|{ch}")
    print("ZP_JSON_END")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
