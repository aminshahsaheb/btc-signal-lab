#!/usr/bin/env python3
"""Verify compressed Atlas pkg_data.csv identity and basic CSV structure."""
import csv, gzip, hashlib, sys
from datetime import datetime
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
DATA=ROOT/"artifacts/data/BTCUSDT_5m_2021_to_latest_csv.gz"
PREFIX="0bea138cc96dfec0"
HEADER=["timestamp","open","high","low","close","volume","taker_buy_base"]
h=hashlib.sha256(); size=0
try:
    with gzip.open(DATA,"rb") as f:
        for chunk in iter(lambda:f.read(1024*1024),b""):
            h.update(chunk); size+=len(chunk)
    digest=h.hexdigest()
    rows=0; prev=None; first=last=None; errors=0
    with gzip.open(DATA,"rt",encoding="utf-8",newline="") as f:
        reader=csv.DictReader(f)
        if reader.fieldnames!=HEADER: raise ValueError(f"Unexpected header: {reader.fieldnames}")
        for r in reader:
            rows+=1
            t=datetime.fromisoformat(r["timestamp"].replace("Z","+00:00"))
            if t.tzinfo is None or (prev is not None and (t-prev).total_seconds()!=300): errors+=1
            prev=t; first=first or t; last=t
            try:
                o,hi,lo,c,v,tb=(float(r[k]) for k in HEADER[1:])
                if min(o,hi,lo,c)<=0 or v<0 or tb<0 or hi<max(o,c,lo) or lo>min(o,c,hi) or tb>v+1e-9: errors+=1
            except Exception: errors+=1
    print(f"rows={rows}; decompressed_bytes={size}; sha256={digest}; range={first}..{last}; invalid={errors}")
    if not digest.startswith(PREFIX) or rows!=602208 or errors: raise SystemExit("DATASET CHECK: FAIL")
    print("DATASET CHECK: PASS — exact Atlas hash-prefix identity and basic structure")
except Exception as e:
    print(f"DATASET CHECK: FAIL — {e}",file=sys.stderr); raise SystemExit(1)
