#!/usr/bin/env python3
"""Verify the received compressed Atlas input dataset against its recorded identity."""
from __future__ import annotations
import csv
import gzip
import hashlib
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "artifacts/data/BTCUSDT_5m_2021_to_latest_csv.gz"
EXPECTED_PREFIX = "0bea138cc96dfec0"
EXPECTED_HEADER = ["timestamp", "open", "high", "low", "close", "volume", "taker_buy_base"]
EXPECTED_ROWS = 602_208

def digest_stream(stream) -> tuple[str, int]:
    h = hashlib.sha256()
    size = 0
    for chunk in iter(lambda: stream.read(1024 * 1024), b""):
        h.update(chunk)
        size += len(chunk)
    return h.hexdigest(), size

def main() -> int:
    if not DATA.is_file():
        print(f"Missing dataset: {DATA.relative_to(ROOT)}", file=sys.stderr)
        return 1
    compressed_hash = hashlib.sha256(DATA.read_bytes()).hexdigest()
    try:
        with gzip.open(DATA, "rb") as raw:
            raw_hash, raw_size = digest_stream(raw)
        with gzip.open(DATA, "rt", encoding="utf-8", newline="") as text:
            reader = csv.DictReader(text)
            if reader.fieldnames != EXPECTED_HEADER:
                raise ValueError(f"Unexpected columns: {reader.fieldnames}")
            rows = 0
            previous = None
            first = last = None
            nulls = 0
            bad = 0
            for row in reader:
                rows += 1
                stamp = datetime.fromisoformat(row["timestamp"].replace("Z", "+00:00"))
                if stamp.tzinfo is None:
                    bad += 1
                if previous is not None and (stamp - previous).total_seconds() != 300:
                    bad += 1
                previous = stamp
                first = first or stamp
                last = stamp
                if any(v is None or v == "" for v in row.values()):
                    nulls += 1
                try:
                    o, h, l, c, v, tb = (float(row[k]) for k in EXPECTED_HEADER[1:])
                    if min(o, h, l, c) <= 0 or v < 0 or tb < 0 or h < max(o, c, l) or l > min(o, c, h) or tb > v + 1e-9:
                        bad += 1
                except (TypeError, ValueError):
                    bad += 1
    except Exception as exc:
        print(f"DATASET CHECK: FAIL — {exc}", file=sys.stderr)
        return 1
    print(f"Rows: {rows}")
    print(f"Compressed SHA-256: {compressed_hash}")
    print(f"Decompressed SHA-256: {raw_hash}")
    print(f"Decompressed bytes: {raw_size}")
    print(f"Range: {first} .. {last}")
    if not raw_hash.startswith(EXPECTED_PREFIX):
        print(f"DATASET CHECK: FAIL — hash does not match Atlas prefix {EXPECTED_PREFIX}", file=sys.stderr)
        return 1
    if rows != EXPECTED_ROWS or nulls or bad:
        print(f"DATASET CHECK: FAIL — rows={rows}, nulls={nulls}, invalid={bad}", file=sys.stderr)
        return 1
    print("DATASET CHECK: PASS")
    print("Scope: gzip readability, recorded Atlas hash-prefix identity, CSV schema, row count, UTC cadence and basic OHLCV validity; not provenance beyond the recorded hash, strategy performance, or statistical validity.")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
