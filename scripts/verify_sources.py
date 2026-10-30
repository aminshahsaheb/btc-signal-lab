#!/usr/bin/env python3
"""Verify pinned artifacts and archive integrity.

A pass confirms byte identity and ZIP structure only. It does not validate
research claims, trading performance, live feeds, or TradingView compilation.
"""
from __future__ import annotations
import csv
import hashlib
import sys
import subprocess
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
ROOT_MANIFEST = ROOT / "artifacts" / "SHA256SUMS.txt"
MOVE_ODDS_ROOT = ROOT / "tools" / "move-odds-panel" / "v0.1.2"
MOVE_ODDS_MANIFEST = MOVE_ODDS_ROOT / "SHA256SUMS.txt"


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def check_manifest(manifest: Path, base: Path, label: str) -> tuple[int, list[str]]:
    if not manifest.is_file():
        return 0, [f"{label}: missing manifest: {manifest.relative_to(ROOT)}"]
    checked = 0
    errors: list[str] = []
    for line_no, raw in enumerate(manifest.read_text(encoding="utf-8").splitlines(), 1):
        line = raw.strip()
        if not line or line.startswith("#"):
            continue
        try:
            expected, rel = line.split(None, 1)
            rel = rel.lstrip(" *")
        except ValueError:
            errors.append(f"{label}:{line_no}: malformed manifest line")
            continue
        path = base / rel
        try:
            path.resolve().relative_to(base.resolve())
        except ValueError:
            errors.append(f"{label}:{line_no}: path escapes artifact root: {rel}")
            continue
        if not path.is_file():
            errors.append(f"{label}:{line_no}: missing file: {rel}")
            continue
        actual = sha256(path)
        checked += 1
        if actual.lower() != expected.lower():
            errors.append(f"{label}:{line_no}: SHA-256 mismatch for {rel}: expected {expected}, got {actual}")
    return checked, errors


def check_zip_archives() -> tuple[int, list[str]]:
    errors: list[str] = []
    archives = sorted((ROOT / "artifacts" / "archives").rglob("*.zip"))
    checked = 0
    for path in archives:
        try:
            with zipfile.ZipFile(path) as zf:
                bad = zf.testzip()
                if bad is not None:
                    errors.append(f"zip: corrupt member in {path.relative_to(ROOT)}: {bad}")
                else:
                    checked += 1
        except (OSError, zipfile.BadZipFile) as exc:
            errors.append(f"zip: invalid archive {path.relative_to(ROOT)}: {exc}")
    return checked, errors


def check_extracted_historical_packages() -> tuple[int, list[str]]:
    """Check that browsable historical trees match their preserved original ZIPs."""
    specs = [
        (ROOT / "artifacts/archives/legacy/MoveOdds_Panel_v0_1.zip", "MoveOdds_Panel_v0_1/", ROOT / "tools/move-odds-panel/archive/v0.1.0"),
        (ROOT / "artifacts/archives/legacy/MoveOdds_Panel_v0_1_1.zip", "MoveOdds_Panel_v0_1_1/", ROOT / "tools/move-odds-panel/archive/v0.1.1"),
    ]
    checked = 0
    errors: list[str] = []
    for archive, prefix, target_root in specs:
        try:
            with zipfile.ZipFile(archive) as zf:
                expected = {n[len(prefix):] for n in zf.namelist() if n.startswith(prefix) and not n.endswith("/")}
                actual = {p.relative_to(target_root).as_posix() for p in target_root.rglob("*") if p.is_file()}
                if expected != actual:
                    errors.append(f"historical extraction: file-set mismatch for {archive.name}; missing={sorted(expected-actual)}, extra={sorted(actual-expected)}")
                for name in sorted(expected & actual):
                    with zf.open(prefix + name) as entry:
                        original = entry.read()
                    extracted = (target_root / name).read_bytes()
                    checked += 1
                    if original != extracted:
                        errors.append(f"historical extraction: byte mismatch for {target_root.relative_to(ROOT) / name}")
        except (OSError, zipfile.BadZipFile, KeyError) as exc:
            errors.append(f"historical extraction: cannot verify {archive.relative_to(ROOT)}: {exc}")
    return checked, errors


def check_full_inventory() -> tuple[int, list[str]]:
    """Check the SHA-256 inventory for every repository file except itself."""
    inv = ROOT / "docs" / "FILE_INVENTORY_SHA256.csv"
    if not inv.is_file():
        return 0, ["inventory: missing docs/FILE_INVENTORY_SHA256.csv"]
    try:
        with inv.open("r", encoding="utf-8", newline="") as f:
            rows = list(csv.DictReader(f))
    except (OSError, csv.Error) as exc:
        return 0, [f"inventory: cannot read CSV: {exc}"]
    expected = {row.get("path", ""): row for row in rows}
    errors: list[str] = []
    if len(expected) != len(rows):
        errors.append("inventory: duplicate path entries")
    actual_paths = {
        p.relative_to(ROOT).as_posix()
        for p in ROOT.rglob("*")
        if p.is_file()
        and p != inv
        and not any(part in {".git", "__pycache__", ".pytest_cache", ".venv", "venv"} for part in p.relative_to(ROOT).parts)
        and p.suffix != ".pyc"
        and p.name != ".DS_Store"
    }
    if actual_paths != set(expected):
        errors.append(f"inventory: file-set mismatch; missing entries={sorted(actual_paths-set(expected))}; stale entries={sorted(set(expected)-actual_paths)}")
    checked = 0
    for rel, row in expected.items():
        if rel not in actual_paths:
            continue
        path = ROOT / rel
        try:
            path.resolve().relative_to(ROOT.resolve())
        except ValueError:
            errors.append(f"inventory: path escapes repository: {rel}")
            continue
        try:
            recorded_size = int(row.get("bytes", ""))
        except ValueError:
            errors.append(f"inventory: invalid byte size: {rel}")
            continue
        recorded_hash = row.get("sha256", "").lower()
        checked += 1
        if path.stat().st_size != recorded_size:
            errors.append(f"inventory: byte-size mismatch for {rel}")
        if sha256(path) != recorded_hash:
            errors.append(f"inventory: SHA-256 mismatch for {rel}")
    return checked, errors


def main() -> int:
    checked_root, root_errors = check_manifest(ROOT_MANIFEST, ROOT, "root")
    checked_mo, mo_errors = check_manifest(MOVE_ODDS_MANIFEST, MOVE_ODDS_ROOT, "move-odds-v0.1.2")
    checked_zips, zip_errors = check_zip_archives()
    checked_old, old_errors = check_extracted_historical_packages()
    checked_inventory, inventory_errors = check_full_inventory()
    dataset_result = subprocess.run([sys.executable, str(ROOT / "scripts" / "verify_dataset.py")], capture_output=True, text=True)
    dataset_errors = [] if dataset_result.returncode == 0 else [dataset_result.stderr.strip() or dataset_result.stdout.strip() or "dataset verification failed"]
    errors = root_errors + mo_errors + zip_errors + old_errors + inventory_errors + dataset_errors
    print(f"Root source artifacts checked: {checked_root}")
    print(f"Move-Odds v0.1.2 package files checked: {checked_mo}")
    print(f"ZIP archives structurally tested: {checked_zips}")
    print(f"Historical extracted package files compared to source ZIPs: {checked_old}")
    print(f"Full repository inventory files checked: {checked_inventory}")
    print(f"Dataset identity/structure check: {'PASS' if dataset_result.returncode == 0 else 'FAIL'}")
    if errors:
        print("INTEGRITY CHECK: FAIL", file=sys.stderr)
        for err in errors:
            print(f"- {err}", file=sys.stderr)
        return 1
    print("INTEGRITY CHECK: PASS")
    print("Scope: byte identity, ZIP structure, and historical extraction equality only; not research validity, trading performance, live feed correctness, or Pine compilation.")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
