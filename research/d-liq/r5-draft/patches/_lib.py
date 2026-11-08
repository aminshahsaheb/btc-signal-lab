"""Helpers shared by the r5 patch scripts. Every edit is an exact-text replacement that must match a known number of times; anything else aborts the assembly."""
import hashlib
import os


def sha256_file(path):
    with open(path, "rb") as f:
        return hashlib.sha256(f.read()).hexdigest()


def read(path):
    with open(path, "r", encoding="utf-8", newline="") as f:
        return f.read()


def write(path, text):
    with open(path, "w", encoding="utf-8", newline="") as f:
        f.write(text)


def replace_once(root, rel, old, new, count=1):
    path = os.path.join(root, rel)
    text = read(path)
    found = text.count(old)
    if found != count:
        raise SystemExit("patch target mismatch in %s: expected %d occurrence(s), found %d of: %r" % (rel, count, found, old[:100]))
    write(path, text.replace(old, new))
