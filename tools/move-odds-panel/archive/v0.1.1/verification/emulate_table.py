"""Emulate the text the Pine table shows for given decision times, reading the lookup arrays BACK from the .pine file
(so a generator/ordering mistake in the file would show up here), and states from replica_panel.py."""
import re, sys, numpy as np, pandas as pd
sys.path.insert(0, "../atlas"); import common, replica_panel as rp
src = open("MoveOdds_Panel_v0_1_1.pine").read()
def arr(name, kind):
    m = re.search(r"var array<%s>\s+%s_%s = array\.from\((.*?)\)\n" % ("float" if kind == "LF" else "int", kind, name), src, re.S)
    return [float(x) for x in m.group(1).replace("\n", " ").split(",")]
LF = {n: arr(n, "LF") for n in ("R12", "R288", "HOUR", "DOW", "BRK")}; TR = {n: arr(n, "TR") for n in LF}
B = (17.1, 20.1, 30.5)
DAY = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]
def cell(name, k, j):
    if k < 0: return "-"
    lift = LF[name][k * 3 + j]; t = int(TR[name][k * 3 + j])
    return f"{lift:.2f}x" + (" A" if t == 1 else " B" if t == 2 else "")
def row(label, state, name, k):
    return f"{label:17s}{state:18s}" + "".join(f"{cell(name, k, j):>10s}" for j in range(3))
def brk(v, pair):
    if np.isnan(v): return "n/a", -1
    if v == 0: return "none", -1
    return ("UP" if v > 0 else "DOWN"), pair * 2 + (0 if v > 0 else 1)
if __name__ == "__main__":
    df = common.load(); H = rp.hourly(df); S = rp.panel_states(H)
    G = pd.read_csv("golden_vectors.csv")
    out = []
    for t in G.decision_utc:
        ts = pd.Timestamp(t, tz="UTC"); j = H.index.get_loc(ts - pd.Timedelta("1h"))
        tehran = (ts + pd.Timedelta("3h30min")).strftime("%Y-%m-%d %H:%M")
        out.append(f"=== decision {t} UTC  (Tehran {tehran}) -> the 5m/15m/1h chart bar that OPENS at this time ===")
        out.append(f"{'Factor':17s}{'State now':18s}{'+-1%/2h':>10s}{'+-2%/8h':>10s}{'+-3%/24h':>10s}")
        b12, b288 = int(S["b12"][j]), int(S["b288"][j])
        out.append(row("1h range", f"Q{b12 + 1}  {100 * np.exp(S['r12'][j]):.2f}%", "R12", b12))
        out.append(row("24h range", f"Q{b288 + 1}  {100 * np.exp(S['r288'][j]):.2f}%", "R288", b288))
        hr, dw = int(S["hour"][j]), int(S["dow"][j])
        out.append(row("Hour of day", f"{hr:02d}:00 UTC", "HOUR", hr))
        out.append(row("Weekday", DAY[dw], "DOW", dw))
        for lab, N, pair in (("24h-range break", 288, 0), ("7d-range break", 2016, 1), ("30d-range break", 8640, 2)):
            v = S[f"up{N}"][j]; d = S[f"dn{N}"][j]
            val = np.nan if np.isnan(v) else (1.0 if v == 1 else (-1.0 if d == 1 else 0.0))
            st, k = brk(val, pair); out.append(row(lab, st, "BRK", k))
        out.append("")
    open("golden_expected_panel.txt", "w").write("\n".join(out))
    print("\n".join(out[:30]))
