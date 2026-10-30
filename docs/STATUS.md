# Status register — 2026-10-30

## Overall

**Research infrastructure: useful. Trading edge: not established.** This repository separates assets and decisions; creating the repository does not validate the hypotheses.

The source inventory includes the Atlas PDF, prior Move-Odds packages, Forward Journal r5/r6, and the exact Atlas `pkg_data.csv` input compressed at `artifacts/data/BTCUSDT_5m_2021_to_latest_csv.gz`. The decompressed SHA-256 begins with the exact prefix recorded by the Atlas README. Structural checks pass. The full archived Atlas pipeline and internal tests were rerun successfully in an isolated workbench; see the dated reproducibility report. The raw conversation export remains intentionally excluded.

| Item | Status | Allowed next action | Not allowed yet |
|---|---|---|---|
| Move-Odds Panel v0.1.2 | Source package and static verification artifacts preserved; Pine compilation not verified | Compile in TradingView; compare the 12 golden vectors on a standard 1h `BINANCE:BTCUSDT.P` chart | Claim compile/runtime success or direction prediction |
| D-LIQ r1 | `DRAFT — NOT LOCKED` | Resolve P0/P1 issues from the 2026-10-30 review in a new r2; freeze exact statistical code and journal contract | Market data scoring, permanent collector, T0, or parameter rescue |
| Forward Journal r7 | `DRAFT — NOT LOCKED`; exact source hash pinned | Use as a reference and close its open requirements separately | Treat it as a locked dependency for D-LIQ |
| Risk-First Helper v0.3.1 | Source preserved; Pine compilation not verified; manual checklist only | Review or compile as a separate tool | Call PASS a prediction or validated trade edge |
| Atlas v1 package + exact input | Archive and matching `pkg_data.csv` input preserved; input hash prefix and structural checks pass | Historical pipeline rerun completed; retain outputs for audit only | Treat the historical data as virgin evidence or claim a new edge |
| Live capture / T0 | Not started | Only after the relevant protocol and evidence journal are locked | Connect an ongoing collector or declare forward validation started |
| KCEX execution validation | Not started | Separate pre-registration after direction and strategy gates pass | Infer KCEX profitability from Binance reference returns |

## Current order of work

1. Keep the repository private and preserve the source-controlled baseline, including the exact Atlas input dataset.
2. Compile and manually verify Move-Odds v0.1.2 in TradingView; report the actual compiler output.
3. Draft D-LIQ r2 to close the blocking items in [`reviews/2026-10-30-dliq-r1-move-odds-review.md`](reviews/2026-10-30-dliq-r1-move-odds-review.md).
4. Freeze a stand-alone journal/anchoring contract, analysis code, and hashes before T0.
5. Only then consider a narrowly scoped quality probe with no price/outcome analysis.
6. Start the forward test only after lock, integrity checks, and explicit T0 declaration.
7. If direction passes, preregister the trading rules on independent data, then measure KCEX execution costs separately.
