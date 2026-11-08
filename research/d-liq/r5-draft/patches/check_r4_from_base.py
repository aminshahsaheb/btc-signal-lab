#!/usr/bin/env python3
"""G-3 for r4-draft itself: rebuild research/d-liq/r4-draft from the r3-reconstruction base and compare.

usage: python3 -I check_r4_from_base.py <r3-reconstruction base directory> <r4-draft directory> <scratch output directory (must not exist)>

The base directory is the tree research/d-liq/r3-reconstruction of the (SHA-pinned) commit of PR #23; it is verified completely against the pinned hash of its MANIFEST.sha256
(every file, no extra file, no symlink). r4-draft/patches/assemble.py (which pins PR #15's builder blob by hash) is then run on it and every assembled file must equal the file of r4-draft.
The only r4-draft files that are not assembler output must be exactly: README.md, MANIFEST.sha256, docs/r3_reconstruction_README.md (which must equal the base README.md), logs/**, patches/**.
Limit: the base commit lives on a pull-request branch (PR #23); it is only as durable as that commit stays reachable. Moving the base into `main` is owner decision D-PR-15-23.
"""
import hashlib
import os
import subprocess
import sys

BASE_MANIFEST_SHA256 = "9a7c6848623bfbbcc866ce0e6468c4b7547da2bafdb134d9e05614a6aaa0852a"
BASE_FILE_COUNT = 17          # 16 files listed in the manifest + the manifest itself
R4_ONLY = {"README.md", "MANIFEST.sha256", "docs/r3_reconstruction_README.md"}


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


def main(base, r4, out):
    errors = []
    if sha(os.path.join(base, "MANIFEST.sha256")) != BASE_MANIFEST_SHA256:
        raise SystemExit("FAIL base MANIFEST.sha256 is not the pinned one")
    listed = {}
    with open(os.path.join(base, "MANIFEST.sha256"), encoding="utf-8") as f:
        for line in f:
            h, _, rel = line.rstrip("\n").partition("  ")
            listed[rel[2:] if rel.startswith("./") else rel] = h
    actual = listing(base)
    if len(actual) != BASE_FILE_COUNT or set(actual) - {"MANIFEST.sha256"} != set(listed):
        errors.append("base tree and its manifest disagree: extra=%s missing=%s" % (sorted(set(actual) - {"MANIFEST.sha256"} - set(listed)), sorted(set(listed) - set(actual))))
    for rel, h in listed.items():
        if rel in actual and sha(os.path.join(base, rel)) != h:
            errors.append("base file hash mismatch: %s" % rel)
    if errors:
        raise SystemExit("\n".join("FAIL " + e for e in errors))
    subprocess.run([sys.executable, "-I", "-B", os.path.join(r4, "patches", "assemble.py"), base, out], check=True)
    built = listing(out)
    for rel in built:
        if not os.path.isfile(os.path.join(r4, rel)):
            errors.append("assembled file missing from r4-draft: %s" % rel)
        elif sha(os.path.join(r4, rel)) != sha(os.path.join(out, rel)) and rel not in R4_ONLY:
            errors.append("r4-draft file differs from the rebuilt one: %s" % rel)
    for rel in listing(r4):
        top = rel.split("/", 1)[0]
        if rel in built:
            continue
        if rel in R4_ONLY or (top in ("logs", "patches") and "/" in rel):
            continue
        errors.append("r4-draft file that is not assembler output and not on the allowed list: %s" % rel)
    if sha(os.path.join(r4, "docs/r3_reconstruction_README.md")) != sha(os.path.join(base, "README.md")):
        errors.append("docs/r3_reconstruction_README.md is not the base README.md")
    for e in errors:
        print("FAIL " + e)
    print("R4-FROM-BASE: %s (%d assembled files compared, %d problem(s))" % ("PASS" if not errors else "FAIL", len(built), len(errors)))
    return 1 if errors else 0


if __name__ == "__main__":
    if len(sys.argv) != 4:
        raise SystemExit(__doc__)
    if os.path.exists(sys.argv[3]):
        raise SystemExit("output directory exists")
    raise SystemExit(main(*[os.path.abspath(a) for a in sys.argv[1:4]]))
