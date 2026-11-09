"""Automatic mutation check of the independent replay (src/replay_indep.py): every single-site mutation of comparison operators, boolean
operators, `not`, +/-, `if` tests and integer constants is generated from the AST, then
  step 1: the replay's own test suite (src/test_replay_indep.py) must fail  -> TEST_KILLED
  step 2: otherwise the differential harness (tools/diff_replay.py vs the author's replay) must report a disagreement -> DIFF_KILLED
  otherwise SURVIVED (an equivalent mutant or a gap in the checks; every survivor must be reviewed by a human).
Both test files (the clean-room suite and the supplementary suite) must pass for the unmutated module and are both run for every mutant.
tools/mutants_reviewed.txt lists the survivors that were reviewed; the run FAILS (exit 1) for a survivor that is not listed and for a listed entry that no
longer survives, so the list stays exact. Usage: python3 -I -B tools/mutate_indep.py <package-dir> <author-src-dir> [workers]
The package is COPIED; nothing in <package-dir> is modified. Synthetic check only; the mutants are mechanical, not a proof of correctness."""
import ast
import concurrent.futures
import copy
import json
import os
import shutil
import subprocess
import sys
import tempfile

CMP = {ast.Lt: ast.LtE, ast.LtE: ast.Lt, ast.Gt: ast.GtE, ast.GtE: ast.Gt, ast.Eq: ast.NotEq, ast.NotEq: ast.Eq}
DIFF_RUNS = [(31, 400), (32, 400)]


def sites(tree):
    """yield (kind, line, apply(tree_copy_nodes) description) -- implemented by index into ast.walk order"""
    out = []
    for idx, node in enumerate(ast.walk(tree)):
        line = getattr(node, "lineno", 0)
        if isinstance(node, ast.Compare):
            for i, op in enumerate(node.ops):
                if type(op) in CMP:
                    out.append((idx, "cmp", i, line, "%s -> %s" % (type(op).__name__, CMP[type(op)].__name__)))
        elif isinstance(node, ast.BoolOp):
            out.append((idx, "bool", 0, line, "%s -> %s" % (type(node.op).__name__, "Or" if isinstance(node.op, ast.And) else "And")))
        elif isinstance(node, ast.UnaryOp) and isinstance(node.op, ast.Not):
            out.append((idx, "not", 0, line, "drop not"))
        elif isinstance(node, ast.BinOp) and isinstance(node.op, (ast.Add, ast.Sub)):
            out.append((idx, "arith", 0, line, "%s -> %s" % (type(node.op).__name__, "Sub" if isinstance(node.op, ast.Add) else "Add")))
        elif isinstance(node, ast.If):
            out.append((idx, "if", 0, line, "negate if-test"))
        elif isinstance(node, ast.Constant) and type(node.value) is int:
            out.append((idx, "const+", 0, line, "%d -> %d" % (node.value, node.value + 1)))
            out.append((idx, "const-", 0, line, "%d -> %d" % (node.value, node.value - 1)))
    return out


def mutate(src_tree, site):
    idx, kind, sub, _line, _d = site
    t = copy.deepcopy(src_tree)
    node = list(ast.walk(t))[idx]
    if kind == "cmp":
        node.ops[sub] = CMP[type(node.ops[sub])]()
    elif kind == "bool":
        node.op = ast.Or() if isinstance(node.op, ast.And) else ast.And()
    elif kind == "not":
        node.op = ast.UAdd()                       # `not x` -> `+x` would change type; instead replace by identity via double negation below
        node.op = ast.Not()
        node.operand = ast.UnaryOp(op=ast.Not(), operand=node.operand)   # not (not x) == x  => drops the negation
    elif kind == "arith":
        node.op = ast.Sub() if isinstance(node.op, ast.Add) else ast.Add()
    elif kind == "if":
        node.test = ast.UnaryOp(op=ast.Not(), operand=node.test)
    elif kind == "const+":
        node.value += 1
    elif kind == "const-":
        node.value -= 1
    ast.fix_missing_locations(t)
    return ast.unparse(t)


def run_one(args):
    pkg, author, site, code = args
    work = tempfile.mkdtemp(prefix="mut_")
    try:
        shutil.copytree(os.path.join(pkg, "src"), os.path.join(work, "src"), ignore=shutil.ignore_patterns("__pycache__"))
        shutil.copytree(os.path.join(pkg, "spec"), os.path.join(work, "spec"))
        shutil.copytree(os.path.join(pkg, "tools"), os.path.join(work, "tools"), ignore=shutil.ignore_patterns("__pycache__"))
        with open(os.path.join(work, "src", "replay_indep.py"), "w", encoding="utf-8") as fh:
            fh.write(code)
        try:
            for suite in ("src/test_replay_indep.py", "src/test_replay_indep_supplement.py"):
                r = subprocess.run([sys.executable, "-I", "-B", suite], cwd=work, capture_output=True, text=True, timeout=120)
                if r.returncode != 0:
                    return site, "TEST_KILLED"
        except subprocess.TimeoutExpired:
            return site, "TEST_KILLED"                 # a mutant that hangs is observable
        for seed, n in DIFF_RUNS:
            try:
                r = subprocess.run([sys.executable, "-I", "-B", "tools/diff_replay.py", author, "src", str(seed), str(n)], cwd=work, capture_output=True, text=True, timeout=300)
            except subprocess.TimeoutExpired:
                return site, "DIFF_KILLED"
            if r.returncode == 1:
                return site, "DIFF_KILLED"
        return site, "SURVIVED"
    finally:
        shutil.rmtree(work, ignore_errors=True)


def main():
    if len(sys.argv) not in (3, 4):
        print("usage: mutate_indep.py <package-dir> <author-src-dir> [workers]", file=sys.stderr)
        return 2
    pkg, author = os.path.abspath(sys.argv[1]), os.path.abspath(sys.argv[2])
    workers = int(sys.argv[3]) if len(sys.argv) == 4 else 4
    src = open(os.path.join(pkg, "src", "replay_indep.py"), encoding="utf-8").read()
    tree = ast.parse(src)
    # sanity: the unmutated (unparsed) module must pass its own tests, otherwise every mutant would count as killed
    base_code = ast.unparse(tree)
    s0, st0 = run_one((pkg, author, (0, "base", 0, 0, "unmutated"), base_code))
    if st0 != "SURVIVED":
        print("FAIL: the unparsed, unmutated module is not accepted by the checks (%s)" % st0)
        return 1
    all_sites = sites(tree)
    jobs = []
    for s in all_sites:
        try:
            jobs.append((pkg, author, s, mutate(tree, s)))
        except Exception as e:                       # a site that cannot be mutated is reported, never skipped silently
            print("UNMUTABLE line %d %s: %s" % (s[3], s[4], e))
    res = {"TEST_KILLED": 0, "DIFF_KILLED": 0, "SURVIVED": 0}
    survivors = []
    with concurrent.futures.ThreadPoolExecutor(max_workers=workers) as ex:
        for site, status in ex.map(run_one, jobs):
            res[status] += 1
            if status != "TEST_KILLED":
                print("%-11s line %4d  %-6s %s" % (status, site[3], site[1], site[4]))
            if status == "SURVIVED":
                survivors.append(site)
    reviewed = {}
    for ln in open(os.path.join(pkg, "tools", "mutants_reviewed.txt"), encoding="utf-8"):
        if ln.strip() and not ln.startswith("#"):
            key, _, why = ln.rstrip("\n").partition("\t")
            reviewed[key] = why
    got = {"%d %s %s" % (s[3], s[1], s[4]) for s in survivors}
    unreviewed = sorted(got - set(reviewed))
    stale = sorted(set(reviewed) - got)
    for k in unreviewed:
        print("UNREVIEWED SURVIVOR: " + k)
    for k in stale:
        print("STALE REVIEW ENTRY (no longer survives): " + k)
    print(json.dumps({"mutants": len(jobs), **res, "unreviewed": len(unreviewed), "stale": len(stale)}))
    return 1 if (unreviewed or stale) else 0


if __name__ == "__main__":
    raise SystemExit(main())
