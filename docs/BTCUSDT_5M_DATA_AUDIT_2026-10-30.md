# BTCUSDT 5m dataset audit — 2026-10-30

Received filename: `BTCUSDT_5m_2021_to_latest_csv (1).gz`

Compressed SHA-256: `075d0553026877154dd160ce1f339bd7ad87320691fade8af1f6a4cbd57fb594`

Decompressed CSV size: 45,203,887 bytes.

Decompressed SHA-256: `0bea138cc96dfec0da229c6dce0107a99e2875a3ad3d34acca058674995affc3`.

The Atlas v1 README requires its external `pkg_data.csv` to begin with SHA-256 prefix `0bea138cc96dfec0`. The uploaded file's decompressed content matches that exact prefix. This is a content-level identity match, not a filename guess.

- Rows: 602,208
- Columns: timestamp, open, high, low, close, volume, taker_buy_base
- UTC range: 2021-01-01 00:00 through 2026-09-22 23:55
- Every adjacent timestamp is exactly 5 minutes apart.
- No duplicate or out-of-order timestamps, gaps, nulls, invalid OHLC ranges, negative volume values, or taker-buy-base greater than volume were found.

Limitations: no source URL/exchange field is embedded in the CSV; the file ends 2026-09-22; it is OHLCV plus taker-buy-base only; and it is burned historical research data, not virgin forward evidence. Hash match and structural checks do not establish a profitable edge.
