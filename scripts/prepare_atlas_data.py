#!/usr/bin/env python3
"""Prepare an isolated Atlas workbench with the exact pkg_data.csv input."""
from __future__ import annotations
import argparse
import gzip
import hashlib
import shutil
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
ARCHIVE = ROOT / "artifacts/archives/Atlas_v1_package.zip"
DATA = ROOT / "artifacts/data/BTCUSDT_5m_2021_to_latest_csv.gz"
EXPECTED_PREFIX = "0bea138cc96dfec0"

def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()

def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--destination", default=str(ROOT / "workbench" / "atlas-v1"))
    parser.add_argument("--force", action="store_true", help="replace the destination directory")
    args = parser.parse_args()
    dest = Path(args.destination).expanduser().resolve()
    if dest.exists():
        if not args.force:
            parser.error(f"{dest} already exists; choose another path or pass --force")
        shutil.rmtree(dest)
    dest.mkdir(parents=True)
    if not ARCHIVE.is_file() or not DATA.is_file():
        raise SystemExit("Required Atlas ZIP or compressed dataset is missing")
    with zipfile.ZipFile(ARCHIVE) as zf:
        zf.extractall(dest)
    atlas = dest / "Atlas_v1"
    if not atlas.is_dir():
        raise SystemExit("Atlas_v1 directory not found after extraction")
    raw = dest / "pkg_data.csv"
    with gzip.open(DATA, "rb") as src, raw.open("wb") as out:
        shutil.copyfileobj(src, out)
    actual = sha256(raw)
    if not actual.startswith(EXPECTED_PREFIX):
        raw.unlink(missing_ok=True)
        raise SystemExit(f"Dataset hash mismatch: {actual}")
    print(f"Workbench: {dest}")
    print(f"Atlas package: {atlas}")
    print(f"Input: {raw}")
    print(f"pkg_data.csv SHA-256: {actual}")
    print("The archived Atlas README's relative ../pkg_data.csv dependency is now satisfied.")
    print("This only prepares the input/package; it does not execute Atlas or validate its findings.")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
