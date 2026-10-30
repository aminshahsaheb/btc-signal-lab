# Artifact register

| Artifact | Role | Status / caveat |
|---|---|---|
| `artifacts/data/BTCUSDT_5m_2021_to_latest_csv.gz` | Exact Atlas historical `pkg_data.csv` input | In prepared local v3 bundle; decompressed SHA-256 matches Atlas prefix; burned historical data. Remote binary presence is not yet verified. |
| `docs/BTCUSDT_5M_DATA_AUDIT_2026-10-30.md` | Dataset identity and structural audit | Exact input match and basic validation. |
| `docs/ATLAS_REPRODUCIBILITY_RUN_2026-10-30.md` | Reproduction run record | Atlas pipeline, tests, placebo, tiering and descriptions completed; not new evidence. |
| `scripts/verify_dataset.py` | Dataset identity and structure verifier | Checks decompressed hash prefix, schema, count, cadence and OHLCV validity. |
| `scripts/prepare_atlas_data.py` | Isolated Atlas workbench preparation | Extracts original Atlas ZIP and places exact input at expected relative path. |
| `artifacts/reproduced/Atlas_v1_reproduced_outputs_2026-10-30.zip` | Reproduced Atlas output package | In local v3 bundle; remote binary presence not yet verified. |
| `artifacts/archives/Atlas_v1_package.zip` | Atlas scripts, derived tables/arrays, figures and results | Historical archive; exact external input is recovered separately. |
| `tools/move-odds-panel/v0.1.2/` | Current Move-Odds source package | Static checks only; TradingView compile unverified. |
| `specs/d-liq/` | D-LIQ preregistration drafts | r1 remains draft, not locked; no live data scored. |
| `specs/forward-journal/` | Forward Journal r5/r6/r7 | r7 remains draft, unlocked. |
| `tools/riskfirst/RiskFirst_Helper_v0_3_1.pine` | Manual risk checklist | Not a directional signal; Pine compile unverified. |

Raw conversation export, credentials, tokens, and private account data are deliberately excluded.
