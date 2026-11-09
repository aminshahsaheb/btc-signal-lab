#!/usr/bin/env python3
"""Guard the duplicated (mirrored) files.

The repository still carries two copies of some documents and Pine sources: the canonical copy (first column below) and a legacy mirror
from the original upload (second column). This check does not decide which tree should survive; it only makes sure the copies cannot drift
apart silently, and that nobody adds a NEW file to a legacy mirror tree without registering it here.

Equality is byte equality after removing trailing whitespace at the end of a file (several mirrors differ only by a final newline).
A pass confirms copy equality only. It does not validate research claims, trading performance, or Pine compilation.
Run from anywhere: python3 scripts/check_mirrors.py
"""
from __future__ import annotations

import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

# (canonical, mirror)
PAIRS = [
    ("specs/d-liq/PREREG_D-LIQ-SNAPSHOT-CONT4H-v1_r1_DRAFT.md", "research/d-liq/PREREG_D-LIQ-SNAPSHOT-CONT4H-v1_r1_DRAFT.md"),
    ("specs/d-liq/archive/PREREG_D-LIQ-SNAPSHOT-CONT4H-v1_r0_DRAFT.md", "research/d-liq/archive/PREREG_D-LIQ-SNAPSHOT-CONT4H-v1_r0_DRAFT.md"),
    ("specs/forward-journal/FORWARD_JOURNAL_SPEC_v1_r7_DRAFT.md", "research/forward-journal/FORWARD_JOURNAL_SPEC_v1_r7_DRAFT.md"),
    ("specs/forward-journal/archive/FORWARD_JOURNAL_SPEC_v1_r5_DRAFT.md", "research/forward-journal/archive/FORWARD_JOURNAL_SPEC_v1_r5_DRAFT.md"),
    ("specs/forward-journal/archive/FORWARD_JOURNAL_SPEC_v1_r6_DRAFT.md", "research/forward-journal/archive/FORWARD_JOURNAL_SPEC_v1_r6_DRAFT.md"),
    ("docs/archive/BTC_Trading_Tool_Research_Global_2026-10-24_v2.md", "research/archive/BTC_Trading_Tool_Research_Global_2026-10-24_v2.md"),
    ("docs/decisions/2026-10-29-btc-direction-path.md", "research/decisions/BTC_DIRECTION_PATH_DECISION_2026-10-29.md"),
    ("docs/reviews/2026-10-29-dliq-r0-move-odds-review.md", "research/reviews/2026-10-29-dliq-r0-move-odds-review.md"),
    ("docs/reviews/2026-10-30-dliq-r1-move-odds-review.md", "research/reviews/GPT_REVIEW_DLIQ_r1_MoveOdds_v0_1_2_2026-10-30.md"),
    ("tools/move-odds-panel/v0.1.2/MoveOdds_Panel_v0_1_2.pine", "pine/move-odds/v0.1.2/MoveOdds_Panel_v0_1_2.pine"),
    ("tools/move-odds-panel/archive/v0.1.1/MoveOdds_Panel_v0_1_1.pine", "pine/move-odds/archive/v0.1.1/MoveOdds_Panel_v0_1_1.pine"),
    ("tools/riskfirst/RiskFirst_Helper_v0_3_1.pine", "pine/risk-first/RiskFirst_Helper_v0_3_1.pine"),
    # the short original README lives under pine/ and is archived (unchanged) under tools/; the long README under tools/v0.1.2 is the current one
    ("tools/move-odds-panel/archive/v0.1.2/README_FA_short_original.md", "pine/move-odds/v0.1.2/README_FA.md"),
]

# legacy mirror trees: every tracked file under these prefixes must be registered above, EXCEPT files inside a D-LIQ work package.
# A work package is exactly a directory research/d-liq/r<number>-draft/ (e.g. r4-draft) or research/d-liq/g<number>-<word>-draft/ (e.g. the
# G-1 package g1-candle-draft). A file or directory that merely starts with "r" or "g" (research/d-liq/rogue-file.md, research/d-liq/r4x/...) is NOT exempt.
MIRROR_PREFIXES = ("pine/", "research/archive/", "research/decisions/", "research/reviews/", "research/forward-journal/", "research/d-liq/")
WORK_PACKAGE = re.compile(r"^research/d-liq/(?:r[0-9]+|g[0-9]+-[a-z]+)-draft/.+")


def git_files(root: Path) -> list[str]:
    out = subprocess.run(["git", "-C", str(root), "ls-files"], capture_output=True, text=True, check=True).stdout
    return [line for line in out.splitlines() if line]


def norm(data: bytes) -> bytes:
    return data.rstrip(b" \t\r\n")


def run(root: Path, files: list[str] | None = None, pairs: list[tuple[str, str]] | None = None) -> tuple[list[str], int, int]:
    """Return (errors, byte-identical pair count, equal-apart-from-final-newline pair count)."""
    errors: list[str] = []
    exact = trailing = 0
    pairs = PAIRS if pairs is None else pairs
    files = git_files(root) if files is None else files
    for canonical, mirror in pairs:
        a, b = root / canonical, root / mirror
        if not a.is_file():
            errors.append(f"missing canonical copy: {canonical}")
            continue
        if not b.is_file():
            errors.append(f"missing mirror copy: {mirror}")
            continue
        da, db = a.read_bytes(), b.read_bytes()
        if da == db:
            exact += 1
        elif norm(da) == norm(db):
            trailing += 1
        else:
            errors.append(f"mirror drift: {canonical} != {mirror} ({len(da)} vs {len(db)} bytes)")
    registered = {m for _, m in pairs}
    for path in files:
        if not path.startswith(MIRROR_PREFIXES) or WORK_PACKAGE.match(path):
            continue
        if path not in registered:
            errors.append(f"file in a legacy mirror tree is not registered in scripts/check_mirrors.py: {path}")
    return errors, exact, trailing


def main() -> int:
    errors, exact, trailing = run(ROOT)
    print(f"mirror pairs checked: {len(PAIRS)} (byte-identical: {exact}; equal apart from the final newline: {trailing})")
    if errors:
        print("MIRROR CHECK: FAIL", file=sys.stderr)
        for e in errors:
            print(f"- {e}", file=sys.stderr)
        return 1
    print("MIRROR CHECK: PASS")
    print("Scope: copy equality only; not research validity, trading performance, or Pine compilation.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
