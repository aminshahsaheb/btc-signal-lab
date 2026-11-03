#!/usr/bin/env python3
"""Read-only archive/content audit for the private BTC Signal Lab repository.

This is a screening tool, not a complete secrets, privacy, provenance, or legal audit.
It reports candidate counts and paths only; it never prints matched values.
"""
from __future__ import annotations

import gzip
import io
import json
import re
import sys
import zipfile
from collections import Counter
from pathlib import Path, PurePosixPath

ROOT = Path(__file__).resolve().parents[1]
TEXT_SUFFIXES = {
    ".md", ".txt", ".py", ".json", ".csv", ".tsv", ".html", ".xml",
    ".yaml", ".yml", ".toml", ".ini", ".pine", ".log", ".sh", ".js",
}
MAX_TEXT_BYTES = 8 * 1024 * 1024
MAX_ENTRY_BYTES = 32 * 1024 * 1024
MAX_TOTAL_EXPANDED = 1024 * 1024 * 1024
MAX_NESTED_DEPTH = 3

PATTERNS = {
    "private_key": re.compile(rb"-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----"),
    "aws_access_key": re.compile(rb"\bAKIA[0-9A-Z]{16}\b"),
    "github_token": re.compile(rb"\b(?:gh[pousr]_[A-Za-z0-9]{20,}|github_pat_[A-Za-z0-9_]{30,})\b"),
    "slack_token": re.compile(rb"\bxox[baprs]-[A-Za-z0-9-]{20,}\b"),
    "credential_assignment": re.compile(
        rb"(?i)\b(?:api[_-]?key|api[_-]?secret|access[_-]?token|password|passwd|secret)"
        rb"\b\s*[:=]\s*['\"][^'\"\r\n]{8,}['\"]"
    ),
    "email_candidate": re.compile(rb"\b[A-Z0-9._%+-]{1,64}@[A-Z0-9.-]{1,190}\.[A-Z]{2,24}\b", re.I),
    "phone_candidate": re.compile(rb"(?:\+\d{1,3}[ -]?)?(?:\(\d{2,4}\)[ -]?)\d{3,4}[ -]?\d{3,4}|\b\d{3}-\d{3}-\d{4}\b"),
}
LICENSE_NAME = re.compile(r"(^|/)(license|licence|copying|notice|third.party.licenses?)(\.|$)", re.I)
COPYRIGHT = re.compile(rb"(?i)(?:\bcopyright\s*(?:\(c\)|©)?\s*(?:19|20)\d{2}|\ball rights reserved\b|\blicensed under\b|\bSPDX-License-Identifier\s*:)")


class Audit:
    def __init__(self) -> None:
        self.counts: Counter[str] = Counter()
        self.findings: list[dict[str, str | int]] = []
        self.license_paths: set[str] = set()
        self.expanded = 0
        self.seen_archives: set[str] = set()

    def finding(self, category: str, path: str, count: int = 1) -> None:
        self.counts[category] += count
        self.findings.append({"category": category, "path": path, "count": count})

    def scan_bytes(self, data: bytes, path: str, *, text_mode: bool = False) -> None:
        if len(data) > MAX_TEXT_BYTES and text_mode:
            self.finding("text_scan_size_limit", path)
            return
        for category, pattern in PATTERNS.items():
            n = sum(1 for _ in pattern.finditer(data))
            if n:
                self.finding(category, path, n)
        if COPYRIGHT.search(data):
            self.finding("copyright_or_license_notice", path)
        if LICENSE_NAME.search(path):
            self.license_paths.add(path)

    def scan_zip(self, payload: bytes, label: str, depth: int = 0) -> None:
        if depth > MAX_NESTED_DEPTH:
            self.finding("nested_archive_depth_limit", label)
            return
        try:
            zf = zipfile.ZipFile(io.BytesIO(payload))
            bad = zf.testzip()
            if bad:
                self.finding("zip_crc_failure", f"{label}!/{bad}")
            names: set[str] = set()
            for info in zf.infolist():
                name = info.filename
                path = PurePosixPath(name)
                if name in names:
                    self.finding("duplicate_zip_path", f"{label}!/{name}")
                names.add(name)
                if path.is_absolute() or ".." in path.parts or "\\" in name:
                    self.finding("unsafe_zip_path", f"{label}!/{name}")
                if info.flag_bits & 0x1:
                    self.finding("encrypted_zip_entry", f"{label}!/{name}")
                if info.file_size > MAX_ENTRY_BYTES:
                    self.finding("zip_entry_size_limit", f"{label}!/{name}")
                    continue
                if info.is_dir():
                    continue
                self.expanded += info.file_size
                if self.expanded > MAX_TOTAL_EXPANDED:
                    self.finding("total_expansion_limit", label)
                    return
                if LICENSE_NAME.search(name):
                    self.license_paths.add(f"{label}!/{name}")
                suffix = Path(name).suffix.lower()
                if suffix in TEXT_SUFFIXES or suffix in {".pdf", ".zip", ".gz"}:
                    try:
                        content = zf.read(info)
                    except Exception:
                        self.finding("zip_entry_read_error", f"{label}!/{name}")
                        continue
                    self.scan_bytes(content, f"{label}!/{name}", text_mode=suffix in TEXT_SUFFIXES)
                    if suffix == ".zip":
                        self.scan_zip(content, f"{label}!/{name}", depth + 1)
                    elif suffix == ".gz":
                        self.scan_gzip(content, f"{label}!/{name}")
        except zipfile.BadZipFile:
            self.finding("invalid_zip", label)

    def scan_gzip(self, payload: bytes, label: str) -> None:
        try:
            with gzip.GzipFile(fileobj=io.BytesIO(payload)) as stream:
                while True:
                    chunk = stream.read(1024 * 1024)
                    if not chunk:
                        break
                    self.expanded += len(chunk)
                    if self.expanded > MAX_TOTAL_EXPANDED:
                        self.finding("total_expansion_limit", label)
                        return
                    self.scan_bytes(chunk, label)
        except (OSError, EOFError):
            self.finding("invalid_gzip", label)


def main() -> int:
    audit = Audit()
    tracked = [p for p in ROOT.rglob("*") if p.is_file() and ".git" not in p.parts]
    for path in tracked:
        rel = path.relative_to(ROOT).as_posix()
        suffix = path.suffix.lower()
        if LICENSE_NAME.search(rel):
            audit.license_paths.add(rel)
        if rel == "scripts/audit_archive_contents.py":
            continue  # avoid the scanner matching its own pattern definitions
        if suffix == ".zip":
            audit.scan_zip(path.read_bytes(), rel)
        elif suffix == ".gz":
            audit.scan_gzip(path.read_bytes(), rel)
        elif suffix in TEXT_SUFFIXES:
            audit.scan_bytes(path.read_bytes(), rel, text_mode=True)
        elif suffix == ".pdf":
            audit.scan_bytes(path.read_bytes(), rel)

    report = {
        "scope": "tracked working-tree files; ZIP contents recursively; GZIP streams; text-like files; raw PDF byte scan",
        "files_seen": len(tracked),
        "expanded_bytes_scanned": audit.expanded,
        "license_or_notice_paths": sorted(audit.license_paths),
        "finding_counts": dict(sorted(audit.counts.items())),
        "findings": audit.findings,
        "limitations": [
            "Pattern screening does not prove absence of secrets or personal data.",
            "PDF scan is byte-level only; no OCR or full semantic review.",
            "No legal conclusion about ownership, licenses, redistribution, or third-party terms is made.",
            "No v4 archive comparison is possible unless the exact v4 archive bytes are supplied.",
        ],
    }
    print(json.dumps(report, ensure_ascii=False, indent=2))
    hard = {"zip_crc_failure", "unsafe_zip_path", "encrypted_zip_entry", "invalid_zip", "invalid_gzip"}
    return 1 if any(item["category"] in hard for item in audit.findings) else 0


if __name__ == "__main__":
    sys.exit(main())
