#!/usr/bin/env python3
"""Regenerate the full file inventory after an intentional repository change.

The inventory does not hash itself, to avoid a recursive checksum problem.
Run from any working directory: python3 scripts/generate_inventory.py
"""
from __future__ import annotations
import csv
import hashlib
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "docs" / "FILE_INVENTORY_SHA256.csv"

def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()

rows = []
for path in sorted(ROOT.rglob("*")):
    if not path.is_file() or path == OUT:
        continue
    parts = path.relative_to(ROOT).parts
    if any(part in {".git", "__pycache__", ".pytest_cache", ".venv", "venv"} for part in parts):
        continue
    if path.suffix == ".pyc" or path.name == ".DS_Store":
        continue
    rel = path.relative_to(ROOT).as_posix()
    rows.append((rel, path.stat().st_size, sha256(path)))
OUT.parent.mkdir(parents=True, exist_ok=True)
with OUT.open("w", encoding="utf-8", newline="") as f:
    writer = csv.writer(f, lineterminator="\n")
    writer.writerow(["path", "bytes", "sha256"])
    writer.writerows(rows)
print(f"Wrote {OUT.relative_to(ROOT)} with {len(rows)} pinned files (inventory excludes itself).")
