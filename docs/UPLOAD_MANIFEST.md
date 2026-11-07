# GitHub upload manifest — 2026-10-30

> **HISTORICAL RECORD — superseded for current state.** This document describes the repository as of 2026-10-30 (a 27-file state); it is not a description of the current tree. The repository is **Public** by owner decision of 2026-11-04. Current state: [`STATUS.md`](STATUS.md). Master checklist: [`ROADMAP.md`](ROADMAP.md). The text below is preserved unchanged.


This manifest separates files verified on the remote GitHub branch from files present only in the prepared local v4 bundle. A local ZIP is not proof of remote upload.

## Confirmed in GitHub main tree (27 files; tree re-read after latest commit)

- README.md
- docs/ARTIFACT_REGISTER.md
- docs/ATLAS_REPRODUCIBILITY_RUN_2026-10-30.md
- docs/BTCUSDT_5M_DATA_AUDIT_2026-10-30.md
- docs/DATA_POLICY.md
- docs/PROJECT_MAP.md
- docs/REMOTE_SYNC_CHECKLIST.md
- docs/RESEARCH_RULES.md
- docs/ROADMAP.md
- docs/STATUS.md
- docs/UPLOAD_MANIFEST.md
- pine/move-odds/archive/v0.1.1/MoveOdds_Panel_v0_1_1.pine
- pine/move-odds/v0.1.2/MoveOdds_Panel_v0_1_2.pine
- pine/move-odds/v0.1.2/README_FA.md
- pine/risk-first/RiskFirst_Helper_v0_3_1.pine
- research/archive/BTC_Trading_Tool_Research_Global_2026-10-24_v2.md
- research/d-liq/PREREG_D-LIQ-SNAPSHOT-CONT4H-v1_r1_DRAFT.md
- research/d-liq/archive/PREREG_D-LIQ-SNAPSHOT-CONT4H-v1_r0_DRAFT.md
- research/decisions/BTC_DIRECTION_PATH_DECISION_2026-10-29.md
- research/forward-journal/FORWARD_JOURNAL_SPEC_v1_r7_DRAFT.md
- research/forward-journal/archive/FORWARD_JOURNAL_SPEC_v1_r5_DRAFT.md
- research/forward-journal/archive/FORWARD_JOURNAL_SPEC_v1_r6_DRAFT.md
- research/reviews/2026-10-29-dliq-r0-move-odds-review.md
- research/reviews/GPT_REVIEW_DLIQ_r1_MoveOdds_v0_1_2_2026-10-30.md
- scripts/data/download_btcusdt_5m.py
- scripts/prepare_atlas_data.py
- scripts/verify_dataset.py

## Present in the local v4 bundle; not confirmed on GitHub

- artifacts/data/BTCUSDT_5m_2021_to_latest_csv.gz
- artifacts/reproduced/Atlas_v1_reproduced_outputs_2026-10-30.zip
- artifacts/archives/Atlas_v1_package.zip and historical Move-Odds ZIPs
- docs/archive/reports/Atlas_Starting_Bitcoin_Moves_2026-10-27.pdf
- Complete Move-Odds v0.1.0/v0.1.1/v0.1.2 source trees, golden vectors, lookup tables and verification files
- Remaining source manifests, audit records, scripts, policies and repository configuration files

Do not claim these files are remotely stored until their exact paths, sizes and hashes are checked in the remote tree. The GitHub connector can write UTF-8 text but does not provide a binary upload path for these archives in this workflow. Use the supplied local bundle to sync them through Git or an approved large-file/release workflow.

## Deliberate exclusions

- Raw conversation export and unrelated personal content.
- Credentials, API keys, tokens, private account details, and live account exports.
- No strategy is claimed profitable. Atlas history is burned and is not forward evidence.
