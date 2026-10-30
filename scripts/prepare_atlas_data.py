#!/usr/bin/env python3
"""Extract Atlas v1 and place its exact pkg_data.csv input at the expected path."""
import argparse,gzip,hashlib,shutil,zipfile
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
ZIP=ROOT/"artifacts/archives/Atlas_v1_package.zip"
DATA=ROOT/"artifacts/data/BTCUSDT_5m_2021_to_latest_csv.gz"
PREFIX="0bea138cc96dfec0"
p=argparse.ArgumentParser()
p.add_argument("--destination",default=str(ROOT/"workbench/atlas-v1"))
p.add_argument("--force",action="store_true")
a=p.parse_args(); dest=Path(a.destination).expanduser().resolve()
if dest.exists():
    if not a.force: p.error(f"{dest} exists; use --force or another destination")
    shutil.rmtree(dest)
dest.mkdir(parents=True)
with zipfile.ZipFile(ZIP) as z: z.extractall(dest)
atlas=dest/"Atlas_v1"
if not atlas.is_dir(): raise SystemExit("Atlas_v1 folder missing")
raw=dest/"pkg_data.csv"
with gzip.open(DATA,"rb") as src,raw.open("wb") as out: shutil.copyfileobj(src,out)
h=hashlib.sha256(raw.read_bytes()).hexdigest()
if not h.startswith(PREFIX): raw.unlink(missing_ok=True); raise SystemExit(f"hash mismatch: {h}")
print(f"Prepared {atlas} with {raw}; SHA-256={h}")
print("Preparation only; this does not execute or validate the Atlas research.")
