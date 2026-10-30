"""Generate MoveOdds_Panel_v0_1.pine from tables.json (atlas) + edges.json so the numbers have one source of truth."""
import json
T = json.load(open("tables.json")); tab = T["tab"]
E = json.load(open("../atlas/edges.json"))
def fl(rows):   # flat float list: index = state*3 + outcome(L1,L2,L3)
    return ", ".join(f"{r[k][0]:.2f}" for r in rows for k in range(3))
def tr(rows):   # 0 none, 1 = tier A, 2 = tier B
    return ", ".join(str({"": 0, "A": 1, "B": 2}[r[k][1]]) for r in rows for k in range(3))
def wrap(s, n=12):  # keep Pine lines moderate
    items = s.split(", "); out = []
    for i in range(0, len(items), n): out.append(", ".join(items[i:i + n]))
    return (",\n     ").join(out)
def arrs(name, rows):
    return (f"var array<float> LF_{name} = array.from(\n     {wrap(fl(rows))})\n"
            f"var array<int>   TR_{name} = array.from(\n     {wrap(tr(rows))})\n")
e12 = [repr(v) for v in E["ln_range12"]]; e288 = [repr(v) for v in E["ln_range288"]]
tables = "".join(arrs(n, tab[n]) for n in ("R12", "R288", "HOUR", "DOW", "BRK"))
pine = open("template.pine").read()
pine = pine.replace("%%EDGES%%", (
    f"float E12_0 = {e12[0]}\nfloat E12_1 = {e12[1]}\nfloat E12_2 = {e12[2]}\nfloat E12_3 = {e12[3]}\n"
    f"float E288_0 = {e288[0]}\nfloat E288_1 = {e288[1]}\nfloat E288_2 = {e288[2]}\nfloat E288_3 = {e288[3]}\n"))
pine = pine.replace("%%TABLES%%", tables)
open("MoveOdds_Panel_v0_1.pine", "w").write(pine)
print("written", len(pine.splitlines()), "lines")
