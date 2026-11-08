#!/usr/bin/env python3
"""Assemble the r5-draft source tree from the r4-draft tree on `main` plus the patch scripts in this directory.

usage: python3 -I assemble_r5.py <r4-draft directory> <output directory (must not exist)>

1. The r4-draft directory is verified COMPLETELY: its MANIFEST.sha256 must itself have the pinned hash, every listed file must have the listed hash, there must be no file that is not
   listed (other than __pycache__) and no listed file may be missing, and there must be no symlink anywhere.
2. Everything except logs/, patches/, MANIFEST.sha256 and README.md is copied; the patch scripts p01..p05 are run in order; the three verifier copies under builder/verifiers/ are refreshed
   from the patched sources and the builder pins are updated; README.md is taken from patches/files/README.md.
3. Nothing else is written. patches/check_rebuild.py then compares the output with ASSEMBLED_MANIFEST.sha256 and with the committed r5-draft tree.
"""
import hashlib
import os
import shutil
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from _lib import replace_once, sha256_file  # noqa: E402

R4_MANIFEST_SHA256 = "abbc40f6e34eb8988f3bf37e8a213e479ad540f6ba26a816c0a02cb77e886734"   # MANIFEST.sha256 of research/d-liq/r4-draft on main (merge commit 1336d77)
R4_FILE_COUNT = 49                                                                       # files listed in that manifest (the manifest does not list itself)
EXCLUDE_TOP = {"logs", "patches", "MANIFEST.sha256", "README.md"}
PATCHES = ("p01_contract.py", "p02_primary.py", "p03_independent.py", "p04_builder.py", "p05_tests.py")
# builder pins as they are in r4-draft; replaced by the hashes of the patched files
R4_PINS = {
    "PRIMARY_VERIFIER_SHA256": "2eedfbe9d56a31297bab3956d165b93e21cd0e72779d19de607883f85ca006be",
    "INDEPENDENT_VERIFIER_SHA256": "8409e5845ffb91f9e7df02ecb3de87a171f1d71e28364dbbe5ee1a2c34bb5cc1",
    "MSG_CONTRACT_SHA256": "e41678d794fb24480c148d7a3507c5d1d3346dabe53c29796b3bb2b271aee7dc",
}


def listing(root):
    files = []
    for dirpath, dirnames, filenames in os.walk(root, followlinks=False):
        dirnames[:] = [d for d in dirnames if d != "__pycache__"]
        for d in dirnames:
            if os.path.islink(os.path.join(dirpath, d)):
                raise SystemExit("symlink in the base tree: %s" % os.path.join(dirpath, d))
        for f in filenames:
            p = os.path.join(dirpath, f)
            if os.path.islink(p):
                raise SystemExit("symlink in the base tree: %s" % p)
            files.append(os.path.relpath(p, root).replace(os.sep, "/"))
    return sorted(files)


def verify_base(base):
    mpath = os.path.join(base, "MANIFEST.sha256")
    if sha256_file(mpath) != R4_MANIFEST_SHA256:
        raise SystemExit("base MANIFEST.sha256 is not the pinned r4-draft manifest")
    listed = {}
    with open(mpath, encoding="utf-8") as f:
        for line in f:
            line = line.rstrip("\n")
            if not line:
                continue
            h, _, rel = line.partition("  ")
            if not rel.startswith("./") or len(h) != 64:
                raise SystemExit("bad manifest line: %r" % line)
            if rel[2:] in listed:
                raise SystemExit("duplicate manifest entry: %s" % rel)
            listed[rel[2:]] = h
    if len(listed) != R4_FILE_COUNT:
        raise SystemExit("base manifest lists %d files, expected %d" % (len(listed), R4_FILE_COUNT))
    actual = set(listing(base)) - {"MANIFEST.sha256"}
    if actual != set(listed):
        raise SystemExit("base tree differs from its manifest: extra=%s missing=%s" % (sorted(actual - set(listed)), sorted(set(listed) - actual)))
    for rel, h in listed.items():
        if sha256_file(os.path.join(base, rel)) != h:
            raise SystemExit("base file hash mismatch: %s" % rel)
    return len(listed)


def main():
    if len(sys.argv) != 3:
        raise SystemExit(__doc__)
    base, out = os.path.abspath(sys.argv[1]), os.path.abspath(sys.argv[2])
    if os.path.exists(out):
        raise SystemExit("output directory already exists: %s" % out)
    n = verify_base(base)
    print("base verified: %d files, manifest %s" % (n, R4_MANIFEST_SHA256[:12]))
    for rel in listing(base):
        if rel.split("/", 1)[0] in EXCLUDE_TOP:
            continue
        dst = os.path.join(out, rel)
        os.makedirs(os.path.dirname(dst), exist_ok=True)
        shutil.copy2(os.path.join(base, rel), dst)
    for name in PATCHES:
        subprocess.run([sys.executable, "-I", os.path.join(HERE, name), out], check=True)
    # refresh the verifier copies shipped with the builder, then pin them
    copies = (("src/dliq_journal_verify_v2.py", "builder/verifiers/primary/dliq_journal_verify_v2.py", "PRIMARY_VERIFIER_SHA256"),
              ("src/dliq_msg_contract_v1.py", "builder/verifiers/primary/dliq_msg_contract_v1.py", "MSG_CONTRACT_SHA256"),
              ("indep_verifier/verify_indep.py", "builder/verifiers/independent/verify_indep.py", "INDEPENDENT_VERIFIER_SHA256"))
    for src, dst, pin in copies:
        if not os.path.isfile(os.path.join(out, dst)):
            raise SystemExit("expected shipped verifier copy is missing: %s" % dst)
        shutil.copy2(os.path.join(out, src), os.path.join(out, dst))
        new = sha256_file(os.path.join(out, dst))
        if new != R4_PINS[pin]:
            replace_once(out, "builder/build_slots_v2.py", '%s = "%s"' % (pin, R4_PINS[pin]), '%s = "%s"' % (pin, new))
    shutil.copy2(os.path.join(HERE, "files", "README.md"), os.path.join(out, "README.md"))
    print("assembled %d files into %s" % (len(listing(out)), out))


if __name__ == "__main__":
    main()
