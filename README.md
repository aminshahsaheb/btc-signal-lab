# BTC Signal Lab

**Private, evidence-first research workspace for Bitcoin market-movement timing, directional hypotheses, risk controls, and forward validation.**

> **Status (2026-10-30):** This repository is being populated. No strategy is established as profitable or independently validated. D-LIQ r1 remains a draft and is not locked. No live collector is running, no D-LIQ market data has been scored, and no T0 has been set. Move-Odds v0.1.2 and Risk-First Helper v0.3.1 have not been compiled in TradingView in this workspace.

## Research components

| Component | Purpose | Status |
|---|---|---|
| Move-Odds | Timing/odds of a large BTC move; not directional | Historical research artifact; v0.1.2 source prepared, TradingView compile pending |
| D-LIQ | Directional continuation hypothesis from delivered liquidation snapshots | r1 draft; not locked |
| Risk-First | Manual trade-plan risk checklist | Helper source; not proof of an edge |
| Forward Journal | Immutable evidence and forward-validation record | r7 draft; not locked |

These components must remain separate. No composite signal is permitted unless each component passes its own pre-defined gate and the combination is preregistered independently.

## Research rules

1. Do not treat historical data already used for discovery or model selection as a clean holdout.
2. Do not tune a failed hypothesis using the same evaluation data.
3. Keep timing, direction, risk controls, and execution validation as separate claims.
4. Preserve failed branches and prior specifications. Do not overwrite history.
5. Do not start a collector or set T0 before the protocol, statistical method, data-validity rules, deduplication, sample accounting, and evidence anchoring are locked.
6. Never describe static lint or hash verification as TradingView compilation or market validation.

## Start here

- [Repository status](docs/STATUS.md)
- [Project map](docs/PROJECT_MAP.md)
- [Research rules](docs/RESEARCH_RULES.md)
- [Artifact and upload manifest](docs/UPLOAD_MANIFEST.md)

## Data completeness warning

The Atlas archive references a separate `pkg_data.csv` input that was not present in the supplied working set. Therefore, the archive is retained for provenance and inspection; this repository must not claim a fully self-contained historical rerun until that input is recovered and independently verified.

The raw conversation export and personal information are intentionally excluded. No exchange API keys, credentials, or private account data belong here.
