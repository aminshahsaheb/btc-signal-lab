# BTCUSDT 5m dataset audit — 2026-10-30

## Identity and Atlas match

Received: `BTCUSDT_5m_2021_to_latest_csv (1).gz`
Compressed SHA-256: `075d0553026877154dd160ce1f339bd7ad87320691fade8af1f6a4cbd57fb594`
Compressed bytes: 13,951,593
Decompressed CSV bytes: 45,203,887
Decompressed SHA-256: `0bea138cc96dfec0da229c6dce0107a99e2875a3ad3d34acca058674995affc3`

The Atlas v1 README specifies that its external `../pkg_data.csv` must begin with SHA-256 prefix `0bea138cc96dfec0`. The decompressed upload matches this exact prefix. This is a content-level identity match to the expected Atlas input, not a filename-based guess.

## Schema and coverage

- Rows: 602,208 (header excluded)
- Columns: `timestamp,open,high,low,close,volume,taker_buy_base`
- UTC range: 2021-01-01 00:00:00 through 2026-09-22 23:55:00
- Cadence: every adjacent pair is exactly 5 minutes

## Structural checks

Passed: no duplicate timestamps; no out-of-order timestamps; no missing or unexpected 5-minute intervals; no nulls; no non-positive OHLC; no negative volume fields; no `high < low`; no high/low violating open/close; no `taker_buy_base > volume`.

## Interpretation and limitations

- The exact Atlas input is recovered. Keep the received gzip bytes unchanged.
- The file ends 2026-09-22; it is not current through 2026-10-30.
- CSV contains OHLCV plus taker-buy-base only, not order-book depth, OI, funding, basis, or a complete liquidation feed.
- Historical data are burned from prior Atlas research. They are not virgin forward evidence.
- Hash match and structural validity do not validate a profitable edge or the statistical conclusions.
- Full Atlas build and core tests were run locally: `build.py`, `test_engine.py`, `test_stats.py`, and `run_main.py` completed; `test_engine.py` reported ALL PASS and `test_stats.py` reported PASS. The 300-shift placebo run did not complete within the available execution window, so no fresh placebo result is claimed.
