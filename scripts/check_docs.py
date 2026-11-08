#!/usr/bin/env python3
"""Documentation structure guard (links, index coverage, historical banners, stale-visibility claims, README layout).

Rules (each failure names the file):
  R1  every relative link in a tracked *.md file resolves to a tracked file or directory. Covered forms: inline links and images
      (balanced parentheses, <angle> destinations, titles), full and collapsed reference links together with their definitions
      (an undefined label is a failure), and HTML href= / src= attributes. Fenced code blocks (``` and ~~~) and inline code spans
      are ignored; an unclosed fence is a failure (it would hide the rest of the file). NOT covered: shortcut references
      ([label] alone), autolinks, whether a #fragment exists, external URLs (nothing is fetched).
  R2  every top-level file in the repository root and in docs/ (*.md, *.csv, *.txt) has a row in docs/INDEX.md, and every row names an existing path;
  R3  a row classified HISTORICAL must carry a banner containing the word HISTORICAL in the first 12 lines of the file;
  R4  a row classified LIVING must not claim that the repository is private (the repository is Public by owner decision of 2026-11-04);
  R5  the "Repository layout" block of README.md lists every existing top-level directory and no directory that does not exist.
A pass confirms documentation structure only. It does not validate research claims, trading performance, or Pine compilation.
Run from anywhere: python3 scripts/check_docs.py
"""
from __future__ import annotations

import posixpath
import re
import subprocess
import sys
from pathlib import Path
from urllib.parse import unquote

ROOT = Path(__file__).resolve().parents[1]
CLASSES = {"LIVING", "HISTORICAL", "RECORD", "GENERATED"}
FENCE_OPEN = re.compile(r"^ {0,3}(`{3,}|~{3,})")
CODE_SPAN = re.compile(r"(?<!`)(`+)(?!`)(.+?)(?<!`)\1(?!`)", re.S)
REF_DEF = re.compile(r"^ {0,3}\[([^\]\n]+)\]:[ \t]*(<[^>\n]*>|\S+)", re.M)
REF_USE = re.compile(r"\[([^\[\]\n]+)\]\[([^\[\]\n]*)\]")
HTML_ATTR = re.compile(r"""\b(?:href|src)\s*=\s*(?:"([^"]*)"|'([^']*)'|([^\s>"'`]+))""", re.I)
SCHEME = re.compile(r"^(?:[A-Za-z][A-Za-z0-9+.\-]*:|//)")
STALE_PRIVATE = [
    re.compile(r"(?i)visibility\s*:\s*\**\s*private"),
    re.compile(r"(?i)keep the repository private"),
    re.compile(r"(?i)the repository (?:remains|is) private"),
    re.compile(r"(?i)do not make the repository public"),
]


def git_files(root: Path) -> list[str]:
    out = subprocess.run(["git", "-C", str(root), "ls-files"], capture_output=True, text=True, check=True).stdout
    return [line for line in out.splitlines() if line]


def strip_code(text: str) -> tuple[str, bool]:
    """Remove fenced blocks and inline code spans. Returns (text, unclosed_fence)."""
    out: list[str] = []
    fence: tuple[str, int] | None = None
    for line in text.splitlines():
        m = FENCE_OPEN.match(line)
        if fence is None:
            if m:
                fence = (m.group(1)[0], len(m.group(1)))
                out.append("")
            else:
                out.append(line)
        else:
            close = re.match(r"^ {0,3}(" + re.escape(fence[0]) + "{" + str(fence[1]) + r",})\s*$", line)
            if close:
                fence = None
            out.append("")
    return CODE_SPAN.sub(lambda mm: " " * len(mm.group(0)), "\n".join(out)), fence is not None


def inline_destinations(text: str) -> list[str]:
    """Destinations of inline links and images: '](' + destination + optional title + ')'."""
    found: list[str] = []
    i = 0
    while True:
        i = text.find("](", i)
        if i < 0:
            return found
        j = i + 2
        n = len(text)
        while j < n and text[j] in " \t":
            j += 1
        if j < n and text[j] == "<":
            k = text.find(">", j + 1)
            nl = text.find("\n", j + 1)
            if k < 0 or (0 <= nl < k):
                i += 2
                continue
            dest, j = text[j + 1:k], k + 1
        else:
            depth, k = 0, j
            while k < n:
                c = text[k]
                if c == "\\" and k + 1 < n:
                    k += 2
                    continue
                if c in " \t\n":
                    break
                if c == "(":
                    depth += 1
                elif c == ")":
                    if depth == 0:
                        break
                    depth -= 1
                k += 1
            dest, j = text[j:k], k
        while j < n and text[j] in " \t\n":
            j += 1
        if j < n and text[j] in "\"'(":
            close = ")" if text[j] == "(" else text[j]
            e = text.find(close, j + 1)
            if e < 0:
                i += 2
                continue
            j = e + 1
            while j < n and text[j] in " \t\n":
                j += 1
        if j < n and text[j] == ")":
            found.append(dest)
        i += 2


def norm_label(label: str) -> str:
    return " ".join(label.lower().split())


def link_problems(rel: str, text: str, fileset: set[str]) -> tuple[list[str], int]:
    """Return (error messages, number of relative links checked) for one Markdown file."""
    errors: list[str] = []
    body, unclosed = strip_code(text)
    if unclosed:
        errors.append(f"R1 unclosed code fence in {rel} (links after it are not checked)")
    dests = inline_destinations(body)
    defs = {norm_label(m.group(1)): m.group(2).strip("<>") for m in REF_DEF.finditer(body) if not m.group(1).startswith("^")}
    dests += list(defs.values())
    body_wo_defs = REF_DEF.sub("", body)
    for m in REF_USE.finditer(body_wo_defs):
        label = norm_label(m.group(2) or m.group(1))
        if label not in defs:
            errors.append(f"R1 undefined link reference [{label}] in {rel}")
    for m in HTML_ATTR.finditer(body):
        dests.append(next(g for g in m.groups() if g is not None))
    checked = 0
    for url in dests:
        url = url.strip()
        if not url or url.startswith("#") or SCHEME.match(url):
            continue
        target = unquote(re.split(r"[#?]", url, maxsplit=1)[0])
        if not target:
            continue
        checked += 1
        joined = target.lstrip("/") if target.startswith("/") else posixpath.join(posixpath.dirname(rel), target)
        clean = posixpath.normpath(joined)
        if clean == ".":
            continue  # the repository root itself
        if clean == ".." or clean.startswith("../"):
            errors.append(f"R1 link escapes the repository in {rel}: {url}")
            continue
        if clean not in fileset and not any(x.startswith(clean.rstrip("/") + "/") for x in fileset):
            errors.append(f"R1 broken link in {rel}: {url}")
    return errors, checked


def parse_index(root: Path) -> tuple[dict[str, str], list[str]]:
    rows: dict[str, str] = {}
    errors: list[str] = []
    index = root / "docs" / "INDEX.md"
    if not index.is_file():
        return rows, ["missing docs/INDEX.md"]
    for line in index.read_text(encoding="utf-8").splitlines():
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


def run(root: Path, files: list[str] | None = None) -> tuple[list[str], dict[str, int]]:
    """Run every rule on `root`. `files` is the tracked-file list (default: git ls-files)."""
    errors: list[str] = []
    files = git_files(root) if files is None else files
    fileset = set(files)
    md_files = [f for f in files if f.endswith(".md")]

    def read(rel: str) -> str:
        return (root / rel).read_text(encoding="utf-8", errors="replace")

    links = 0
    for f in md_files:
        errs, n = link_problems(f, read(f), fileset)
        errors += errs
        links += n

    rows, idx_errors = parse_index(root)
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

    if "README.md" not in fileset:
        errors.append("R5 README.md is not tracked")
    else:
        m = re.search(r"## Repository layout\s+```[a-z]*\n(.*?)```", read("README.md"), re.S)
        if not m:
            errors.append("R5 README.md has no 'Repository layout' code block")
        else:
            listed = {d for d in re.findall(r"^[├└]── ([A-Za-z0-9_.\-]+)/", m.group(1), re.M) if not d.startswith(".")}
            actual = {f.split("/", 1)[0] for f in files if "/" in f and not f.startswith(".")}
            for d in sorted(actual - listed):
                errors.append(f"R5 README layout does not list the top-level directory: {d}/")
            for d in sorted(listed - actual):
                errors.append(f"R5 README layout lists a directory that does not exist: {d}/")
    return errors, {"markdown": len(md_files), "links": links, "index_rows": len(rows)}


def main() -> int:
    errors, stats = run(ROOT)
    print(f"markdown files: {stats['markdown']}; relative links checked: {stats['links']}; index rows: {stats['index_rows']}")
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
