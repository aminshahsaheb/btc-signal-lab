"""Rough static checks for a Pine file (NOT a compiler): ASCII only, no tabs, indentation, bracket balance,
continuation-line indent not a multiple of 4, every namespaced call listed with a 'seen in compiled Helper' flag,
generated lookup arrays parsed back and compared with atlas_tiers.csv."""
import re, sys, json, pandas as pd
src = open(sys.argv[1]).read(); helper = open(sys.argv[2]).read()
lines = src.split("\n"); bad = []
if not src.isascii(): bad.append("non-ASCII characters present")
for i, ln in enumerate(lines, 1):
    if "\t" in ln: bad.append(f"{i}: tab")
    if ln.rstrip() != ln: bad.append(f"{i}: trailing space")
# bracket balance outside strings/comments
def strip(l):
    l = re.sub(r'"(\\.|[^"\\])*"', '""', l); return l.split("//")[0]
depth = 0
for i, ln in enumerate(lines, 1):
    t = strip(ln)
    for ch in t:
        if ch in "([": depth += 1
        elif ch in ")]": depth -= 1
        if depth < 0: bad.append(f"{i}: unbalanced )"); depth = 0
# indentation of statements: multiples of 4 unless the previous logical line is an open paren continuation
d = 0; prev_open = False
for i, ln in enumerate(lines, 1):
    t = strip(ln)
    if t.strip() == "": continue
    ind = len(ln) - len(ln.lstrip(" "))
    if d == 0 and ind % 4 != 0: bad.append(f"{i}: statement indent {ind} not multiple of 4")
    if d > 0 and ind % 4 == 0 and ind != 0: bad.append(f"{i}: continuation indent {ind} is a multiple of 4 (would be read as a block)")
    for ch in t:
        if ch in "([": d += 1
        elif ch in ")]": d -= 1
if depth != 0 or d != 0: bad.append(f"final bracket depth {depth}/{d}")
# namespaced calls
def calls(text):
    out = set()
    for l in text.split("\n"):
        l = strip(l)
        out |= set(re.findall(r"\b((?:ta|math|str|array|table|input|request|barmerge|position|color|size|text|display|chart|syminfo|barstate|timeframe|runtime|format)\.[A-Za-z_0-9]+)", l))
    return out
mine, theirs = calls(src), calls(helper)
print("namespaced identifiers used by the panel:")
for n in sorted(mine): print(("  [in compiled-by-user Helper] " if n in theirs else "  [NOT in Helper -> check by knowledge] ") + n)
# plain functions
for n in ("hour", "dayofweek", "timenow", "na", "int", "float", "plot"): print("  plain:", n, "used" if re.search(r"\b" + n + r"\b", src) else "-")
# parse-back of generated tables
T = pd.read_csv("../atlas/atlas_tiers.csv"); M = T[T.outcome.str.startswith("MOVE")]
G = json.load(open("tables.json"))["groups"]
def arr(name, kind):
    m = re.search(r"var array<%s>\s+%s_%s = array\.from\((.*?)\)\n" % ("float" if kind == "LF" else "int", kind, name), src, re.S)
    return [float(x) for x in m.group(1).replace("\n", " ").split(",")]
nbad = 0; ncell = 0
for g, cells in G.items():
    lf, trr = arr(g, "LF"), arr(g, "TR")
    assert len(lf) == len(cells) * 3 == len(trr), (g, len(lf))
    for s, cell in enumerate(cells):
        for k, o in enumerate(("MOVE_L1", "MOVE_L2", "MOVE_L3")):
            r = M[(M.outcome == o) & (M.cell == cell)].iloc[0]
            tier = {"A": 1, "B": 2}.get(r.tier, 0)
            ncell += 1
            if abs(lf[s * 3 + k] - round(float(r.lift), 2)) > 1e-9 or int(trr[s * 3 + k]) != tier:
                nbad += 1; bad.append(f"table mismatch {cell} {o}")
print(f"parsed-back table entries checked: {ncell}, mismatches: {nbad}")
print("LINT PROBLEMS:", len(bad)); [print("  ", b) for b in bad]
sys.exit(1 if bad else 0)
