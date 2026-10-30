#!/usr/bin/env python3
"""
Download BTCUSDT Binance USD-M Futures 5m data for the direction test.

Source order:
1) Binance official public archive.
2) Hugging Face mirror: linxy/USDT-M_Perpetual_Futures.
3) Hugging Face raw mirror: ibrahimdaud/binance-btcusdt.

Output columns:
    timestamp, open, high, low, close, volume, taker_buy_base

The script validates:
- monotonic UTC timestamps
- duplicate timestamps
- 5-minute continuity
- OHLC validity
- required taker-buy data

Default end date: yesterday UTC.
Current month uses Binance daily archives. Older months use monthly archives.
If official download is not usable, the script falls back to a mirror.
"""

from __future__ import annotations

import argparse
import io
import os
import shutil
import subprocess
import sys
import tempfile
import zipfile
from datetime import date, datetime, timedelta, timezone
from pathlib import Path

import pandas as pd

BINANCE_MONTHLY = (
    "https://data.binance.vision/data/futures/um/monthly/klines/"
    "BTCUSDT/5m/BTCUSDT-5m-{ym}.zip"
)
BINANCE_DAILY = (
    "https://data.binance.vision/data/futures/um/daily/klines/"
    "BTCUSDT/5m/BTCUSDT-5m-{ymd}.zip"
)

HF_PRIMARY_REPO = "linxy/USDT-M_Perpetual_Futures"
HF_PRIMARY_FILE = "BTCUSDT/BTCUSDT_5m.parquet"
HF_SECONDARY_REPO = "ibrahimdaud/binance-btcusdt"
HF_SECONDARY_PREFIX = "raw/klines_5m/BTCUSDT"

RAW_COLS = [
    "open_time", "open", "high", "low", "close", "volume",
    "close_time", "quote_volume", "count", "taker_buy_volume",
    "taker_buy_quote_volume", "ignore",
]
OUT_COLS = ["timestamp", "open", "high", "low", "close", "volume", "taker_buy_base"]


def run(cmd: list[str]) -> None:
    print("$", " ".join(cmd), flush=True)
    subprocess.run(cmd, check=True)


def download_url(url: str, out: Path) -> bool:
    out.parent.mkdir(parents=True, exist_ok=True)
    curl = shutil.which("curl")
    if curl:
        cmd = [
            curl, "-fL", "--retry", "3", "--retry-delay", "2",
            "--connect-timeout", "20", "--max-time", "300",
            "-o", str(out), url,
        ]
        try:
            subprocess.run(cmd, check=True, stdout=subprocess.DEVNULL)
            return out.exists() and out.stat().st_size > 1024
        except subprocess.CalledProcessError:
            return False
    wget = shutil.which("wget")
    if wget:
        cmd = [wget, "-q", "-O", str(out), url]
        try:
            subprocess.run(cmd, check=True)
            return out.exists() and out.stat().st_size > 1024
        except subprocess.CalledProcessError:
            return False
    raise RuntimeError("curl or wget is required")


def iter_months(start: date, end: date):
    cur = date(start.year, start.month, 1)
    stop = date(end.year, end.month, 1)
    while cur <= stop:
        yield cur
        cur = date(cur.year + (cur.month == 12), 1 if cur.month == 12 else cur.month + 1, 1)


def read_binance_zip(path: Path) -> pd.DataFrame:
    with zipfile.ZipFile(path) as zf:
        csv_names = [n for n in zf.namelist() if n.lower().endswith(".csv")]
        if not csv_names:
            raise ValueError(f"No CSV inside {path}")
        with zf.open(csv_names[0]) as fh:
            raw = fh.read()
    df = pd.read_csv(io.BytesIO(raw), header=None)
    if len(df.columns) < 12:
        raise ValueError(f"Unexpected Binance kline width: {df.shape}")
    df = df.iloc[:, :12]
    df.columns = RAW_COLS
    return df


def official_download(start: date, end: date, work: Path) -> pd.DataFrame | None:
    print("\n[1/3] Trying Binance official archive...", flush=True)
    frames: list[pd.DataFrame] = []
    failed_months: list[str] = []

    for month in iter_months(start, end):
        month_start = max(start, month)
        next_month = date(month.year + (month.month == 12), 1 if month.month == 12 else month.month + 1, 1)
        month_end = min(end, next_month - timedelta(days=1))
        ym = month.strftime("%Y-%m")
        zip_path = work / f"BTCUSDT-5m-{ym}.zip"
        ok = download_url(BINANCE_MONTHLY.format(ym=ym), zip_path)

        if ok:
            try:
                df = read_binance_zip(zip_path)
                frames.append(df)
                print(f"  OK monthly {ym}: {len(df):,} rows", flush=True)
                continue
            except Exception as exc:
                print(f"  monthly parse failed {ym}: {exc}", flush=True)

        # Fallback for this month: daily archives.
        print(f"  monthly unavailable for {ym}; trying daily files", flush=True)
        daily_ok = True
        cur = month_start
        while cur <= month_end:
            ymd = cur.strftime("%Y-%m-%d")
            dpath = work / f"BTCUSDT-5m-{ymd}.zip"
            if not download_url(BINANCE_DAILY.format(ymd=ymd), dpath):
                daily_ok = False
                print(f"    FAIL {ymd}", flush=True)
                break
            try:
                frames.append(read_binance_zip(dpath))
            except Exception as exc:
                daily_ok = False
                print(f"    FAIL parse {ymd}: {exc}", flush=True)
                break
            cur += timedelta(days=1)
        if not daily_ok:
            failed_months.append(ym)
        else:
            print(f"  OK daily fallback {ym}", flush=True)

    if failed_months:
        print("Official archive incomplete for:", ", ".join(failed_months), flush=True)
        return None
    if not frames:
        return None
    return normalize(pd.concat(frames, ignore_index=True), start, end)


def hf_primary_download(start: date, end: date, out_dir: Path) -> pd.DataFrame | None:
    print("\n[2/3] Trying Hugging Face mirror (linxy)...", flush=True)
    try:
        from huggingface_hub import hf_hub_download
    except Exception:
        print("  huggingface_hub is not installed", flush=True)
        return None
    try:
        local = hf_hub_download(
            repo_id=HF_PRIMARY_REPO,
            repo_type="dataset",
            filename=HF_PRIMARY_FILE,
            local_dir=str(out_dir),
        )
        df = pd.read_parquet(local)
        if "open_time" not in df.columns or "taker_buy_volume" not in df.columns:
            raise ValueError(f"Unexpected mirror columns: {list(df.columns)}")
        return normalize(df, start, end)
    except Exception as exc:
        print(f"  primary mirror failed: {exc}", flush=True)
        return None


def hf_secondary_download(start: date, end: date, out_dir: Path) -> pd.DataFrame | None:
    print("\n[3/3] Trying Hugging Face raw mirror (ibrahimdaud)...", flush=True)
    try:
        from huggingface_hub import list_repo_files, hf_hub_download
    except Exception:
        print("  huggingface_hub is not installed", flush=True)
        return None
    try:
        files = [
            f for f in list_repo_files(HF_SECONDARY_REPO, repo_type="dataset")
            if f.startswith(HF_SECONDARY_PREFIX + "/") and f.endswith(".parquet")
        ]
        wanted = []
        for f in files:
            name = Path(f).stem
            try:
                d = datetime.strptime(name, "%Y-%m-%d").date()
            except ValueError:
                continue
            if start <= d <= end:
                wanted.append((d, f))
        wanted.sort()
        if not wanted:
            raise RuntimeError("No matching daily parquet files found")
        frames = []
        for d, f in wanted:
            local = hf_hub_download(
                repo_id=HF_SECONDARY_REPO,
                repo_type="dataset",
                filename=f,
                local_dir=str(out_dir / "ibrahim"),
            )
            frames.append(pd.read_parquet(local))
        return normalize(pd.concat(frames, ignore_index=True), start, end)
    except Exception as exc:
        print(f"  secondary mirror failed: {exc}", flush=True)
        return None


def normalize(df: pd.DataFrame, start: date, end: date) -> pd.DataFrame:
    df = df.copy()
    rename = {
        "open_time": "timestamp",
        "bar_time_ms": "timestamp",
        "taker_buy_volume": "taker_buy_base",
        "taker_buy_base": "taker_buy_base",
    }
    for src, dst in rename.items():
        if src in df.columns and dst not in df.columns:
            df[dst] = df[src]
    required = ["timestamp", "open", "high", "low", "close", "volume", "taker_buy_base"]
    missing = [c for c in required if c not in df.columns]
    if missing:
        raise ValueError(f"Missing columns: {missing}")
    if pd.api.types.is_numeric_dtype(df["timestamp"]):
        ts = pd.to_datetime(df["timestamp"], unit="ms", utc=True, errors="coerce")
    else:
        ts = pd.to_datetime(df["timestamp"], utc=True, errors="coerce")
    df["timestamp"] = ts
    for c in required[1:]:
        df[c] = pd.to_numeric(df[c], errors="coerce")
    start_ts = pd.Timestamp(start, tz="UTC")
    end_excl = pd.Timestamp(end + timedelta(days=1), tz="UTC")
    df = df[(df.timestamp >= start_ts) & (df.timestamp < end_excl)]
    df = df[required].dropna()
    df = df.sort_values("timestamp").drop_duplicates("timestamp", keep="last")
    return df.reset_index(drop=True)


def validate(df: pd.DataFrame) -> dict[str, object]:
    if df.empty:
        raise ValueError("No rows in output")
    diffs = df.timestamp.diff().dropna().dt.total_seconds().astype("int64")
    bad_steps = int((diffs != 300).sum())
    first = df.timestamp.iloc[0]
    last = df.timestamp.iloc[-1]
    bad_ohlc = int(((df.high < df.low) | (df.high < df.open) | (df.high < df.close) |
                    (df.low > df.open) | (df.low > df.close)).sum())
    bad_taker = int(((df.taker_buy_base < 0) | (df.taker_buy_base > df.volume + 1e-9)).sum())
    dup = int(df.timestamp.duplicated().sum())
    return {
        "rows": len(df),
        "first": first.isoformat(),
        "last": last.isoformat(),
        "duplicates": dup,
        "bad_5m_steps": bad_steps,
        "bad_ohlc": bad_ohlc,
        "bad_taker_buy": bad_taker,
    }


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--start", default="2021-01-01")
    ap.add_argument("--end", default=(datetime.now(timezone.utc).date() - timedelta(days=1)).isoformat())
    ap.add_argument("--out", default="BTCUSDT_5m_2021_to_latest.csv.gz")
    ap.add_argument("--work", default="./binance_download_work")
    args = ap.parse_args()

    start = date.fromisoformat(args.start)
    end = date.fromisoformat(args.end)
    if end < start:
        raise SystemExit("end < start")

    work = Path(args.work).resolve()
    work.mkdir(parents=True, exist_ok=True)

    df = official_download(start, end, work)
    source = "Binance official"
    if df is None:
        df = hf_primary_download(start, end, work / "hf_primary")
        source = "Hugging Face linxy"
    if df is None:
        df = hf_secondary_download(start, end, work / "hf_secondary")
        source = "Hugging Face ibrahimdaud"
    if df is None:
        raise SystemExit("All sources failed. No dataset was produced.")

    report = validate(df)
    out = Path(args.out).resolve()
    out.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(out, index=False, compression="gzip")

    report_path = out.with_suffix("").with_suffix(".validation.txt")
    with report_path.open("w", encoding="utf-8") as f:
        f.write(f"source={source}\n")
        for k, v in report.items():
            f.write(f"{k}={v}\n")

    print("\nDONE")
    print(f"source: {source}")
    print(f"output: {out}")
    print(f"validation: {report_path}")
    for k, v in report.items():
        print(f"{k}: {v}")

    if report["duplicates"] or report["bad_ohlc"] or report["bad_taker_buy"]:
        print("WARNING: structural errors found")
        return 2
    if report["bad_5m_steps"]:
        print("WARNING: missing/non-5m timestamps found. Keep the gaps visible. Do not fill them.")
        return 3
    return 0


if __name__ == "__main__":
    raise SystemExit(main())