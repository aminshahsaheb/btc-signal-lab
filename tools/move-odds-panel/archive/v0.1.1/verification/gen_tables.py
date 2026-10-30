"""Extract the lookup tables for the Move-Odds Panel from the atlas (single source of truth: atlas_tiers.csv)."""
import pandas as pd, json, sys
A = "../atlas/"
T = pd.read_csv(A + "atlas_tiers.csv")
M = T[T.outcome.str.startswith("MOVE")]
def get(cell):
    out = []
    for k in ("MOVE_L1", "MOVE_L2", "MOVE_L3"):
        r = M[(M.outcome == k) & (M.cell == cell)]
        assert len(r) == 1, (cell, k, len(r))
        r = r.iloc[0]
        tier = r.tier if r.tier in ("A", "B") else ""
        out.append((round(float(r.lift), 2), tier, int(r.n), float(r.z)))
    return out
groups = {
    "R12": [f"ln_range12_b{b}" for b in range(5)],
    "R288": [f"ln_range288_b{b}" for b in range(5)],
    "HOUR": [f"C_H{h:02d}" for h in range(24)],
    "DOW": [f"C_D{d}" for d in range(7)],
    "BRK": ["BREAK_UP_288", "BREAK_DN_288", "BREAK_UP_2016", "BREAK_DN_2016", "BREAK_UP_8640", "BREAK_DN_8640"],
}
tab = {g: [get(c) for c in cells] for g, cells in groups.items()}
json.dump({"groups": groups, "tab": tab}, open("tables.json", "w"), indent=1)
for g, rows in tab.items():
    print(g)
    for c, r in zip(groups[g], rows): print("  ", c, r)
