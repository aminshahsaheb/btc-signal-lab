#!/usr/bin/env python3
"""Documentation structure guard (links, index coverage, historical banners, stale-visibility claims, README layout).

Rules (each failure names the file):
  R1  every relative Markdown link in a tracked *.md file resolves to a tracked file or directory;
  R2  every top-level file in the repository root and in docs/ (*.md, *.csv, *.txt) has a row in docs/INDEX.md, and every row names an existing path;
  R3  a row classified HISTORICAL must carry a banner containing the word HISTORICAL in the first 12 lines of the file;
  R4  a row classified LIVING must not claim that the repository is private (the repository is Public by owner decision of 2026-11-04);
  R5  the "Repository layout" block of README.md lists every existing top-level directory and no directory that does not exist.
A pass confirms documentation structure only. It does not validate research claims, trading performance, or Pine compilation.
Run from anywhere: python3 scripts/check_docs.py
"""
from __future__ import annotations

import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
INDEX = ROOT / "docs" / "INDEX.md"
CLASSES = {"LIVING", "HISTORICAL", "RECORD", "GENERATED"}
LINK = re.compile(r"\[[^\]\n]*\]\(([^)\s]+)(?:\s+\"[^\"]*\")?\)")
FENCE = re.compile(r"```.*?```", re.S)
STALE_PRIVATE = [
    re.compile(r"(?i)visibility\s*:\s*\**\s*private"),
    re.compile(r"(?i)keep the repository private"),
    re.compile(r"(?i)the repository (?:remains|is) private"),
    re.compile(r"(?i)do not make the repository public"),
]


def tracked() -> list[str]:
    out = subprocess.run(["git", "-C", str(ROOT), "ls-files"], capture_output=True, text=True, check=True).stdout
    return [line for line in out.splitlines() if line]


def read(rel: str) -> str:
    return (ROOT / rel).read_text(encoding="utf-8", errors="replace")


def parse_index() -> tuple[dict[str, str], list[str]]:
    rows: dict[str, str] = {}
    errors: list[str] = []
    if not INDEX.is_file():
        return rows, ["missing docs/INDEX.md"]
    for line in INDEX.read_text(encoding="utf-8").splitlines():
        m = re.match(r"^\|\s*`([^`]+)`\s*\|\s*([A-Z]+)\s*\|", line)
        if not m:
            continue
        path, cls = m.group(1), m.group(2)
        if cls not in CLASSES:
            errors.append(f"docs/INDEX.md: unknown class {cls!r} for {path}")
        if path in rows:
            errors.append(f"docs/INDEX.md: duplicate row for {path}")
        rows[path] = cls
    return rows, errors


def main() -> int:
    errors: list[str] = []
    files = tracked()
    fileset = set(files)
    md_files = [f for f in files if f.endswith(".md")]

    # R1 links
    links = 0
    for f in md_files:
        text = FENCE.sub("", read(f))
        for m in LINK.finditer(text):
            url = m.group(1)
            if re.match(r"^(https?:|mailto:|#)", url):
                continue
            target = url.split("#", 1)[0]
            if not target:
                continue
            links += 1
            resolved = (Path(f).parent / target)
            norm = Path(*[p for p in resolved.parts if p != "."]).as_posix()
            parts: list[str] = []
            for p in norm.split("/"):
                if p == "..":
                    if parts:
                        parts.pop()
                else:
                    parts.append(p)
            clean = "/".join(parts)
            if clean not in fileset and not any(x.startswith(clean.rstrip("/") + "/") for x in fileset):
                errors.append(f"R1 broken link in {f}: {url}")

    # R2 index coverage
    rows, idx_errors = parse_index()
    errors += idx_errors
    top = [f for f in files if "/" not in f or (f.startswith("docs/") and f.count("/") == 1)]
    top = [f for f in top if f.endswith((".md", ".csv", ".txt")) and f != "docs/INDEX.md"]
    for f in top:
        if f not in rows and not any(g.endswith("*") and f.startswith(g[:-1]) for g in rows):
            errors.append(f"R2 not listed in docs/INDEX.md: {f}")
    for p in rows:
        if p.endswith("*"):
            if not any(x.startswith(p[:-1]) for x in files):
                errors.append(f"R2 docs/INDEX.md glob matches nothing: {p}")
        elif p not in fileset:
            errors.append(f"R2 docs/INDEX.md names a path that does not exist: {p}")

    # R3 banners, R4 stale visibility claims
    for p, cls in rows.items():
        if p.endswith("*") or p not in fileset:
            continue
        text = read(p)
        if cls == "HISTORICAL":
            head = "\n".join(text.splitlines()[:12])
            if "HISTORICAL" not in head:
                errors.append(f"R3 HISTORICAL document without a banner in its first 12 lines: {p}")
        if cls == "LIVING" and p.endswith(".md"):
            for pat in STALE_PRIVATE:
                if pat.search(text):
                    errors.append(f"R4 LIVING document claims the repository is private: {p} ({pat.pattern})")

    # R5 README layout
    readme = read("README.md")
    m = re.search(r"## Repository layout\s+```[a-z]*\n(.*?)```", readme, re.S)
    if not m:
        errors.append("R5 README.md has no 'Repository layout' code block")
    else:
        listed = {d for d in re.findall(r"^[├└]── ([A-Za-z0-9_.\-]+)/", m.group(1), re.M) if not d.startswith(".")}
        actual = {f.split("/", 1)[0] for f in files if "/" in f and not f.startswith(".")}
        for d in sorted(actual - listed):
            errors.append(f"R5 README layout does not list the top-level directory: {d}/")
        for d in sorted(listed - actual):
            errors.append(f"R5 README layout lists a directory that does not exist: {d}/")

    print(f"markdown files: {len(md_files)}; relative links checked: {links}; index rows: {len(rows)}")
    if errors:
        print("DOCS CHECK: FAIL", file=sys.stderr)
        for e in errors:
            print(f"- {e}", file=sys.stderr)
        return 1
    print("DOCS CHECK: PASS")
    print("Scope: documentation structure only; not research validity, trading performance, or Pine compilation.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
