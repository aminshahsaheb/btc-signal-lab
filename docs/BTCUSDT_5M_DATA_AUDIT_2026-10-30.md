# BTCUSDT 5m dataset audit — 2026-10-30

## Identity

- Received filename: `BTCUSDT_5m_2021_to_latest_csv (1).gz`
- Repository copy: `artifacts/data/BTCUSDT_5m_2021_to_latest_csv.gz`
- Compression: gzip
- Compressed size: 13,951,593 bytes
- SHA-256 of compressed file: `075d0553026877154dd160ce1f339bd7ad87320691fade8af1f6a4cbd57fb594`
- Decompressed CSV size: 45,203,887 bytes
- SHA-256 of decompressed CSV: `0bea138cc96dfec0da229c6dce0107a99e2875a3ad3d34acca058674995affc3`

## Atlas input identity match

The preserved `Atlas_v1/README.md` states that its external `../pkg_data.csv` input must have SHA-256 prefix `0bea138cc96dfec0`.

The SHA-256 of this uploaded gzip's decompressed CSV matches that prefix exactly. This is a content-level identity match to the expected Atlas input, not a filename-based guess. The full hash is recorded above.

The dataset is therefore the previously missing Atlas `pkg_data.csv` input. Keep the original compressed bytes unchanged. Use `scripts/prepare_atlas_data.py` to prepare a working copy at the relative path expected by the archived Atlas scripts.

## CSV schema and range

- Rows: 602,208 data rows (header excluded)
- Columns, in order: `timestamp,open,high,low,close,volume,taker_buy_base`
- Timestamp type: ISO-8601 UTC timestamps (`+00:00`)
- First timestamp: `2021-01-01 00:00:00+00:00`
- Last timestamp: `2026-09-22 23:55:00+00:00`
- Expected candle interval: 5 minutes

## Structural checks performed

- Timestamp duplicates: 0
- Out-of-order timestamps: 0
- Non-5-minute intervals: 0
- Missing 5-minute intervals inside the observed range: 0
- Null values in all seven columns: 0
- Non-positive OHLC values: 0
- Negative volume or taker-buy-base values: 0
- `high < low`: 0
- `high` below open/close: 0
- `low` above open/close: 0
- `taker_buy_base > volume`: 0

All checks above passed on the received file.

## Limits and interpretation

- The file itself does not contain an exchange field, market-type field, or source URL. Its Atlas hash match establishes it as the exact input expected by that Atlas package, but does not independently establish provenance beyond that package's recorded checksum.
- The file ends on 2026-09-22. It is not current through 2026-10-30. Do not call it "latest" without qualification.
- It is OHLCV plus taker-buy-base data. It is not order-book depth, open interest, funding, basis, or a complete liquidation feed.
- This is historical data already used in Atlas discovery/confirmation/holdout work. It is burned research data, not virgin forward evidence.
- A clean structural check does not validate the Atlas statistical claims or establish a profitable trading strategy.
