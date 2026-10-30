# Source and repository audit — 2026-10-30

## Purpose and scope

This audit establishes what source material was available in the working files and how it is represented in this repository. It is not a new market-data test and does not validate a trading edge.

## Source inventory and disposition

| Source family | Available source(s) | Repository location | Decision / caveat |
|---|---|---|---|
| Project state / prior branch results | `PROJECT_STATE_v2`, global research inventory dated 2026-10-24 | `docs/archive/` | Preserve for history; current status and decisions take precedence. |
| Direction-path decision | `BTC_DIRECTION_PATH_DECISION_2026-10-29.md` | `docs/decisions/` | Active research governance decision; not evidence of an edge. |
| Move-Onset Atlas | Atlas v1 ZIP and Persian 17-page summary PDF dated 2026-10-27 | `artifacts/archives/Atlas_v1_package.zip`; `docs/archive/reports/` | Historical/descriptive only. Archive says input history is burned; do not rescore as virgin evidence. |
| Move-Odds Panel | v0.1, v0.1.1, v0.1.2, patch bundle, golden vectors, lookup data, static lint/replica outputs | `tools/move-odds-panel/` and `artifacts/archives/` | Preserve versions. Static checks are not a TradingView compile or runtime validation. |
| D-LIQ | r0 and r1 preregistration drafts; GPT reviews of each stage | `specs/d-liq/`, `docs/reviews/` | r0 superseded but never locked; r1 remains `DRAFT — NOT LOCKED`. No live collection or T0. |
| Forward Journal | r5, r6, r7 draft files | `specs/forward-journal/` | Historical versions are immutable archival inputs; r7 is not locked. |
| Risk-First Helper | `RiskFirst_Helper_v0_3_1.pine` | `tools/riskfirst/` | Manual risk checklist, not a signal; Pine compilation is not verified here. |
| Full conversation export | `chat-share (12).txt` (raw conversation history, around 2 MB) | **Not committed** | Deliberately excluded. It is not a clean source artifact and can contain unrelated personal or sensitive context. Project decisions already needed for reproducibility are captured in curated, dated research documents. |
| Raw market history | Uploaded gzip `BTCUSDT_5m_2021_to_latest_csv (1).gz`; decompressed SHA-256 exactly matches the Atlas README's expected `pkg_data.csv` hash prefix. 602,208 UTC 5m rows, 2021-01-01 through 2026-09-22. | `artifacts/data/BTCUSDT_5m_2021_to_latest_csv.gz` | Exact Atlas input identity confirmed by hash prefix; structural checks pass. Historical/burned data, not forward evidence. |
| Secrets / live capture | No legitimate requirement to store credentials or raw live logs in Git | **Excluded** | Never commit API keys, tokens, private account details, or live capture logs. |
| Unrelated Fanus work | Separate projects/repositories | **Excluded** | Keep research boundaries clean; do not merge Fanus files into this BTC repository. |

## Integrity verification performed

- The uploaded gzip dataset was decompressed in a streaming pass. Its decompressed SHA-256 is `0bea138cc96dfec0da229c6dce0107a99e2875a3ad3d34acca058674995affc3`, matching the exact `0bea138cc96dfec0` prefix required by the Atlas README for `pkg_data.csv`.
- CSV structural audit: 602,208 rows; expected seven columns; no duplicate or out-of-order timestamps; every interval is exactly five minutes; no nulls, invalid OHLC ranges, negative volume values, or taker-buy-base values exceeding volume.

- The source manifest in the original Atlas ZIP was inspected. It describes a BTCUSDT 5-minute descriptive atlas from 2021-01-01 through 2026-09-22, with 602,208 candles and 984 single-feature tests. The package's own README explicitly says these data are burned and no atlas cell is a validated edge.
- The accompanying PDF was checked for metadata, text, and rendered appearance across all 17 pages. It is an explanatory report, not a separate raw dataset.
- v0.1/v0.1.1/v0.1.2 and the v0.1.2 patch ZIPs were inspected for file listings and SHA-256 values. Archived ZIPs are retained as received; extracted historical source folders are for browsing.
- The root source manifest pins selected artifacts and ZIPs. The Move-Odds v0.1.2 manifest pins its 16 internal files.
- `scripts/verify_sources.py` validates file hashes and archive structure only. A passing result does not validate statistical claims, TradingView compilation, a live Binance feed, or KCEX execution.

## What is missing / unresolved

1. The exact Atlas `pkg_data.csv` input has now been recovered and hash-prefix matched. `scripts/prepare_atlas_data.py` prepares the Atlas workbench with the expected relative input path. The Atlas pipeline has now been rerun in an isolated workbench. Build, internal engine tests, statistics tests, main analysis, 300-draw placebo, tiering, and descriptive modules completed. See the dated reproducibility report.
2. The Pine scripts have not been compiled in TradingView in this workspace.
3. D-LIQ r1 has not been locked; the blocking statistical, message validity, deduplication, sample-accounting, and evidence-journal items documented in its review remain open.
4. No live collector, data-quality probe, T0, or forward evaluation has been started.

## Rule for updates

Add new versions side-by-side. Do not overwrite archived specifications or packages. Every change to pinned bytes must update the SHA manifest and this audit record in the same commit. No new feature, parameter, sample extension, or strategy combination may be introduced silently.


## Dataset recovery update — 2026-10-30

The uploaded gzip file was verified against the exact hash prefix recorded by Atlas v1. Structural validation passed. The Atlas pipeline was rerun using the recovered input; internal engine and statistics tests passed. The compressed dataset and complete reproducibility report are included in the prepared local package. The prepared local source package includes the compressed dataset and report. The remote GitHub copy still needs explicit binary-file verification; do not assume a local artifact is present remotely.
