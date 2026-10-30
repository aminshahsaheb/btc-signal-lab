# Status register — 2026-10-30

## Overall

Research infrastructure and historical reproduction: useful. Trading edge: not established.

The exact Atlas `pkg_data.csv` input was recovered from the user-uploaded gzip. Its decompressed SHA-256 matches the prefix in the Atlas README. Structural checks pass. Atlas build, internal engine tests, stats tests, main analysis, 300-draw placebo, tiering and descriptive modules completed in an isolated workbench. See `docs/ATLAS_REPRODUCIBILITY_RUN_2026-10-30.md`.

| Item | Status | Allowed next action | Not allowed |
|---|---|---|---|
| Atlas v1 + input | Historical pipeline rerun completed; tests pass | Preserve exact input and outputs; audit reproducibility | Treat burned history as virgin evidence |
| Move-Odds v0.1.2 | Source and static checks preserved; TradingView compile unverified | Compile and compare golden vectors in TradingView | Claim runtime/compile success or direction prediction |
| D-LIQ r1 | DRAFT — NOT LOCKED | Resolve review issues in r2 and freeze protocol | Market-data scoring, permanent collector, T0 |
| Forward Journal r7 | DRAFT — NOT LOCKED | Close open requirements and independent tests | Treat as locked dependency |
| Risk-First v0.3.1 | Manual helper; Pine compile unverified | Review/compile separately | Call PASS a validated edge |
| Live capture / T0 | Not started | Only after protocol and journal lock | Declare forward validation started |
| KCEX execution | Not started | Separate preregistration after research gates | Infer execution profitability from Binance data |

Historical Atlas input ends 2026-09-22 and is not fresh forward evidence.
