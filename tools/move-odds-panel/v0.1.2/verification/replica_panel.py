"""Python replica of the Move-Odds panel as it is implemented in the Pine file (one request.security on 60m,
evaluated on the developing hourly candle j+1 using only completed candles via [1]/[2] offsets).
Everything is written with Pine-style primitives (ta.highest/ta.lowest with na until the window is full, [n] offsets,
comparison-count binning, Pine dayofweek mapping) and validated against the atlas cell membership (cellmat.npz,
cells_meta.csv), which was built from the 5m series.  Run from this folder: python3 replica_panel.py"""
import json, sys, numpy as np, pandas as pd, scipy.sparse as sp
A = "../atlas/"
sys.path.insert(0, A)
import common

E = json.load(open(A + "edges.json"))
EDGE12 = [float(repr(v)) for v in E["ln_range12"]]      # full double precision, as carried by the Pine file
EDGE288 = [float(repr(v)) for v in E["ln_range288"]]

def highest(x, n): return pd.Series(x).rolling(n, min_periods=n).max().to_numpy()
def lowest(x, n):  return pd.Series(x).rolling(n, min_periods=n).min().to_numpy()
def sh(x, k):      return np.r_[np.full(k, np.nan), x[:-k]]          # Pine x[k]
def bin5(x, e):
    b = sum((x >= ek).astype(float) for ek in e)
    return np.where(np.isfinite(x), b, np.nan)
def pine_dow(ts):
    d = ((ts.dayofweek.to_numpy() + 1) % 7) + 1      # Pine numbering Sunday=1..Saturday=7
    return (d + 5) % 7                                # -> atlas Monday=0 .. Sunday=6

def hourly(df):
    g = df.groupby(df.index.floor("h"))
    H = pd.DataFrame({"open": g.open.first(), "high": g.high.max(), "low": g.low.min(), "close": g.close.last(), "n": g.close.count()})
    return H

def panel_states(H):
    """Row j (hourly index) = state seen on the developing candle j+1, i.e. decision time = open(j) + 1h."""
    h = H.high.to_numpy(float); l = H.low.to_numpy(float); c = H.close.to_numpy(float)
    out = {}
    with np.errstate(all="ignore"):
        out["r12"] = np.log((h - l) / c)                                  # candle j
        out["r288"] = np.log((highest(h, 24) - lowest(l, 24)) / c)        # last 24 candles ending at j
    out["b12"], out["b288"] = bin5(out["r12"], EDGE12), bin5(out["r288"], EDGE288)
    dt = H.index + pd.Timedelta("1h")
    out["hour"] = dt.hour.to_numpy().astype(float); out["dow"] = pine_dow(dt).astype(float)
    for N, w in ((288, 23), (2016, 167), (8640, 719)):
        pmax = sh(highest(h, w), 1); pmin = sh(lowest(l, w), 1)           # candles j-w..j-1 (excludes the decision hour)
        ok = np.isfinite(pmax)
        out[f"up{N}"] = np.where(ok, (c > pmax).astype(float), np.nan)
        out[f"dn{N}"] = np.where(ok, (c < pmin).astype(float), np.nan)
    out["close"] = c
    out["dec"] = dt
    return out

if __name__ == "__main__":
    df = common.load()
    H = hourly(df)
    S = panel_states(H)
    # map atlas D-points (bar idx with minute==55 -> decision = open+5min) to hourly rows
    idx = np.where(df.index.minute.to_numpy() == 55)[0]
    dts = df.index[idx] + pd.Timedelta("5min")
    pos = H.index.get_indexer(dts - pd.Timedelta("1h"))
    assert (pos >= 0).all()
    M = sp.load_npz(A + "cellmat.npz").tocsc()
    meta = pd.read_csv(A + "cells_meta.csv"); col = {c: i for i, c in enumerate(meta.cell)}
    def mem(cell): return M[:, col[cell]].toarray().ravel().astype(bool)
    tot = 0
    def check(name, got, cell):
        global tot
        exp = mem(cell); fp = int((got & ~exp).sum()); fn = int((~got & exp).sum()); tot += fp + fn
        flag = "" if fp + fn == 0 else "   <-- differs"
        print(f"{name:12s} vs {cell:18s} atlas n={int(exp.sum()):6d} replica n={int(got.sum()):6d}  extra={fp:3d} missing={fn:3d}{flag}")
    exact_bad = 0
    for k in range(5): check(f"b12=={k}", S["b12"][pos] == k, f"ln_range12_b{k}")
    for k in range(5): check(f"b288=={k}", S["b288"][pos] == k, f"ln_range288_b{k}")
    for hh in range(24): check(f"hour=={hh}", S["hour"][pos] == hh, f"C_H{hh:02d}")
    for d in range(7): check(f"dow=={d}", S["dow"][pos] == d, f"C_D{d}")
    exact = tot; print("---- exact-by-construction groups (R12,R288,hour,dow): total differences =", exact)
    tot = 0
    for N in (288, 2016, 8640):
        check(f"up{N}", np.nan_to_num(S[f"up{N}"][pos]) == 1, f"BREAK_UP_{N}")
        check(f"dn{N}", np.nan_to_num(S[f"dn{N}"][pos]) == 1, f"BREAK_DN_{N}")
    print("---- break groups (hourly-candle windows, differ from 5m windows by one old 5m bar): total differences =", tot)
    json.dump({"exact_groups_diff": int(exact), "break_groups_diff": int(tot)}, open("replica_check.json", "w"))
    # golden vectors: chart-bar open time = decision time (state shown on the 5m/15m/1h chart bar that opens at HH:00 and until HH:55)
    tab = json.load(open("tables.json"))["tab"]
    rows = []
    pick = [pd.Timestamp(x, tz="UTC") for x in (
        "2021-03-10 14:00", "2022-06-14 13:00", "2023-03-15 14:00", "2024-03-05 00:00", "2024-08-05 03:00",
        "2025-04-07 14:00", "2025-10-10 21:00", "2026-01-20 12:00", "2026-05-29 15:00", "2026-08-15 10:00",
        "2026-09-01 14:00", "2026-09-21 23:00")]
    for t in pick:
        j = H.index.get_loc(t - pd.Timedelta("1h"))
        r = dict(decision_utc=str(t)[:16], close_of_hour=float(S["close"][j]),
                 range1h_pct=round(100 * float(np.exp(S["r12"][j])), 3), b12=int(S["b12"][j]),
                 range24h_pct=round(100 * float(np.exp(S["r288"][j])), 3), b288=int(S["b288"][j]),
                 hour=int(S["hour"][j]), dow=int(S["dow"][j]))
        for N in (288, 2016, 8640):
            u, d_ = S[f"up{N}"][j], S[f"dn{N}"][j]
            r[f"brk{N}"] = "na" if np.isnan(u) else ("UP" if u == 1 else ("DN" if d_ == 1 else "-"))
        r["L1_r12"], r["L2_r12"], r["L3_r12"] = [x[0] for x in tab["R12"][r["b12"]]]
        r["L2_r288"] = tab["R288"][r["b288"]][1][0]
        r["L1_hour"] = tab["HOUR"][r["hour"]][0][0]
        rows.append(r)
    G = pd.DataFrame(rows); G.to_csv("golden_vectors.csv", index=False)
    print(G.to_string())
    sys.exit(0 if exact == 0 else 1)
