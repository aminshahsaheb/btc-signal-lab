# Artifact register

| Artifact | Role | Status / caveat |
|---|---|---|
| `artifacts/data/BTCUSDT_5m_2021_to_latest_csv.gz` | Exact Atlas historical `pkg_data.csv` input | Local package copy; decompressed SHA-256 matches Atlas prefix; structural checks pass; burned historical data. |
| `docs/BTCUSDT_5M_DATA_AUDIT_2026-10-30.md` | Dataset identity and structural audit | Exact input match and basic validation; see limits in report. |
| `docs/ATLAS_REPRODUCIBILITY_RUN_2026-10-30.md` | Reproduction run record | Atlas pipeline, tests, placebo, tiering and descriptions completed; not new evidence or profitability validation. |
| `scripts/verify_dataset.py` | Dataset identity and structure verifier | Checks decompressed hash prefix, schema, count, cadence and OHLCV validity. |
| `scripts/prepare_atlas_data.py` | Isolated Atlas workbench preparation | Extracts original Atlas ZIP and places exact input at expected relative path. |
| `docs/PROJECT_AUDIT_2026-10-30.md` | Source inventory and audit | Updated after recovery; remote binary upload remains separate. |
| `docs/archive/PROJECT_STATE_v2_2026-10-07.md` | Earlier frozen project state | Historical snapshot; superseded by newer decisions. |
| `docs/archive/BTC_Trading_Tool_Research_Global_2026-10-24_v2.md` | Cross-branch research inventory | Historical inventory; do not treat as a new score. |
| `docs/archive/reports/Atlas_Starting_Bitcoin_Moves_2026-10-27.pdf` | Persian human-readable Atlas report | 17 pages; descriptive report, based on burned historical data. |
| `artifacts/archives/Atlas_v1_package.zip` | Atlas scripts, derived tables/arrays, figures and results | Historical archive; exact external input is now recovered separately. |
| `tools/move-odds-panel/v0.1.2/` | Current navigable Move-Odds source package | Static checks only; not compiled in TradingView. |
| `artifacts/archives/MoveOdds_Panel_v0_1_2_source.zip` | Original v0.1.2 package archive | Preserved as received. |
| `artifacts/archives/legacy/MoveOdds_Panel_v0_1.zip` | Initial Move-Odds package | Historical version. |
| `artifacts/archives/legacy/MoveOdds_Panel_v0_1_1.zip` | Move-Odds v0.1.1 package | Historical version. |
| `artifacts/archives/legacy/MoveOdds_Panel_v0_1_2_patch.zip` | v0.1.2 patch bundle | Preserved separately. |
| `specs/d-liq/PREREG_D-LIQ-SNAPSHOT-CONT4H-v1_r1_DRAFT.md` | Current candidate preregistration | Draft, not locked; no live data scored. |
| `specs/d-liq/archive/PREREG_D-LIQ-SNAPSHOT-CONT4H-v1_r0_DRAFT.md` | Superseded D-LIQ draft | Preserved for audit trail. |
| `specs/forward-journal/` | Forward Journal r5/r6/r7 | r7 remains draft and unlocked. |
| `tools/riskfirst/RiskFirst_Helper_v0_3_1.pine` | Manual risk checklist | Not a directional signal; Pine compilation not verified. |
| `docs/decisions/` and `docs/reviews/` | Research decisions and reviews | Governance/review material, not independent market performance proof. |

The inventory and SHA-256 manifests identify exact bytes. Integrity checks do not validate strategy performance, live feeds, or TradingView compilation.
