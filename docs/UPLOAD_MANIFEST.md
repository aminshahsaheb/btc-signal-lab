# Upload manifest and source gaps

Updated: 2026-10-30

This manifest distinguishes files verified on GitHub from files still pending. A local archive is not proof of remote upload.

## Verified on GitHub

- `README.md`
- `docs/STATUS.md`
- `docs/PROJECT_MAP.md`
- `docs/RESEARCH_RULES.md`
- `research/forward-journal/FORWARD_JOURNAL_SPEC_v1_r7_DRAFT.md` — uploaded in three complete line ranges (1–1119); GitHub copy re-read and verified at 178,034 characters.
- `research/d-liq/PREREG_D-LIQ-SNAPSHOT-CONT4H-v1_r1_DRAFT.md`
- `research/decisions/BTC_DIRECTION_PATH_DECISION_2026-10-29.md`
- `research/reviews/GPT_REVIEW_DLIQ_r1_MoveOdds_v0_1_2_2026-10-30.md`
- `pine/risk-first/RiskFirst_Helper_v0_3_1.pine`
- `pine/move-odds/v0.1.2/MoveOdds_Panel_v0_1_2.pine`
- `pine/move-odds/v0.1.2/README_FA.md`
- `research/d-liq/archive/PREREG_D-LIQ-SNAPSHOT-CONT4H-v1_r0_DRAFT.md`
- `research/reviews/2026-10-29-dliq-r0-move-odds-review.md`
- `research/archive/BTC_Trading_Tool_Research_Global_2026-10-24_v2.md`
- `scripts/data/download_btcusdt_5m.py` — source downloader script; this is code, not the dataset itself.
- `pine/move-odds/archive/v0.1.1/MoveOdds_Panel_v0_1_1.pine`
- `research/forward-journal/archive/FORWARD_JOURNAL_SPEC_v1_r5_DRAFT.md`
- `research/forward-journal/archive/FORWARD_JOURNAL_SPEC_v1_r6_DRAFT.md` — uploaded in three complete line ranges (1–1058) and reassembled.

## Not yet uploaded

- Atlas archive ZIP and Persian PDF report.
- Move-Odds v0.1.0/v0.1.1 packages, historical ZIPs, verification scripts and data tables.
- Remaining Forward Journal source artifacts, if any, beyond the verified r5/r6/r7 copies.
- Project state snapshot.
- Inventory, full local SHA-256 manifest, and remaining project documentation/scripts.
- Full r7 source integrity verification (the uploaded copy was produced from a bounded text read).

## Data availability

The file `BTCUSDT_5m_2021_to_latest_csv (1)` is **not visible among the files attached to this conversation or mounted in the working directory at this time**. Do not infer its presence from its filename.

The Atlas archive references a separate `pkg_data.csv` input that was not found in the supplied working set. The BTCUSDT five-minute OHLC file, if supplied, must be inspected for schema, timestamp timezone, duplicate/missing bars, gaps, OHLC validity, and end date before deciding whether it can replace or reproduce that input. Matching symbol and timeframe alone is insufficient.

## Exclusions and handling

- Raw conversation export excluded for privacy and relevance.
- No credentials, API keys, or private account data should be committed.
- Large binary archives and datasets require an appropriate Git LFS/release strategy or separate storage; do not force oversized binaries into ordinary Git blobs.
- Keep old versions and drafts. Do not overwrite them with later drafts.
