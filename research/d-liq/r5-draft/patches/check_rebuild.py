#!/usr/bin/env python3
"""Rebuild checks for r5-draft (GPT audit G-3).

  check_rebuild.py check <assembled dir> <r5-draft dir>      compare an assembled tree with patches/ASSEMBLED_MANIFEST.sha256 and with the committed tree
  check_rebuild.py write-assembled <assembled dir>           (re)write patches/ASSEMBLED_MANIFEST.sha256 from an assembled tree
  check_rebuild.py write-tree <r5-draft dir>                 (re)write MANIFEST.sha256 of the committed tree (every file except itself and __pycache__)

ASSEMBLED_MANIFEST.sha256 lines: "<sha256>  <size>  <path>". MANIFEST.sha256 lines: "<sha256>  ./<path>" (same format as r4-draft).
`check` fails on: a missing or extra assembled file, a hash or size difference, a committed file that is neither an assembled output nor one of {patches/**, logs/**, MANIFEST.sha256}, a committed
output that differs from the assembled one, a committed tree that does not match its MANIFEST.sha256, and any symlink.
"""
import hashlib
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ASSEMBLED = os.path.join(HERE, "ASSEMBLED_MANIFEST.sha256")


def sha(p):
    with open(p, "rb") as f:
        return hashlib.sha256(f.read()).hexdigest()


def listing(root):
    out = []
    for d, dirs, files in os.walk(root, followlinks=False):
        dirs[:] = [x for x in dirs if x != "__pycache__"]
        for x in dirs + files:
            if os.path.islink(os.path.join(d, x)):
                raise SystemExit("symlink: %s" % os.path.join(d, x))
        out += [os.path.relpath(os.path.join(d, f), root).replace(os.sep, "/") for f in files]
    return sorted(out)


def write_assembled(root):
    with open(ASSEMBLED, "w", encoding="utf-8", newline="\n") as f:
        for rel in listing(root):
            f.write("%s  %d  %s\n" % (sha(os.path.join(root, rel)), os.path.getsize(os.path.join(root, rel)), rel))


def write_tree(root):
    with open(os.path.join(root, "MANIFEST.sha256"), "w", encoding="utf-8", newline="\n") as f:
        for rel in listing(root):
            if rel != "MANIFEST.sha256":
                f.write("%s  ./%s\n" % (sha(os.path.join(root, rel)), rel))


def check(assembled, tree):
    errors = []
    expected = {}
    with open(ASSEMBLED, encoding="utf-8") as f:
        for line in f:
            h, size, rel = line.rstrip("\n").split("  ", 2)
            expected[rel] = (h, int(size))
    got = listing(assembled)
    for rel in sorted(set(got) - set(expected)):
        errors.append("assembled file not in ASSEMBLED_MANIFEST: %s" % rel)
    for rel in sorted(set(expected) - set(got)):
        errors.append("ASSEMBLED_MANIFEST file was not assembled: %s" % rel)
    for rel in sorted(set(got) & set(expected)):
        p = os.path.join(assembled, rel)
        if (sha(p), os.path.getsize(p)) != expected[rel]:
            errors.append("assembled file differs from ASSEMBLED_MANIFEST: %s" % rel)
    committed = listing(tree)
    for rel in committed:
        top = rel.split("/", 1)[0]
        if rel in expected:
            if rel in got and sha(os.path.join(tree, rel)) != sha(os.path.join(assembled, rel)):
                errors.append("committed file differs from the rebuilt one: %s" % rel)
        elif not (top in ("patches", "logs") and "/" in rel) and rel != "MANIFEST.sha256":
            errors.append("committed file is neither a rebuilt output nor patches/logs/MANIFEST: %s" % rel)
    for rel in sorted(set(expected) - set(committed)):
        errors.append("rebuilt output is missing from the committed tree: %s" % rel)
    listed = {}
    mpath = os.path.join(tree, "MANIFEST.sha256")
    if not os.path.isfile(mpath):
        return errors + ["MANIFEST.sha256 is missing from the committed tree"]
    with open(mpath, encoding="utf-8") as f:
        for line in f:
            h, _, rel = line.rstrip("\n").partition("  ")
            listed[rel[2:]] = h
    for rel in sorted((set(committed) - {"MANIFEST.sha256"}) ^ set(listed)):
        errors.append("MANIFEST.sha256 and the committed tree disagree about: %s" % rel)
    for rel, h in listed.items():
        if rel in committed and sha(os.path.join(tree, rel)) != h:
            errors.append("MANIFEST.sha256 hash mismatch: %s" % rel)
    return errors


if __name__ == "__main__":
    cmd = sys.argv[1] if len(sys.argv) > 1 else ""
    if cmd == "write-assembled" and len(sys.argv) == 3:
        write_assembled(sys.argv[2])
    elif cmd == "write-tree" and len(sys.argv) == 3:
        write_tree(sys.argv[2])
    elif cmd == "check" and len(sys.argv) == 4:
        errs = check(sys.argv[2], sys.argv[3])
        for e in errs:
            print("FAIL " + e)
        print("REBUILD CHECK: %s (%d problem(s))" % ("PASS" if not errs else "FAIL", len(errs)))
        sys.exit(1 if errs else 0)
    else:
        raise SystemExit(__doc__)
