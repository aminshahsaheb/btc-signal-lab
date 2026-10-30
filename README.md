# BTC Signal Lab

Evidence-first research workspace for Bitcoin movement timing, directional hypothesis testing, risk controls, and forward validation.

> **Status (2026-10-30):** No profitable strategy is established. D-LIQ r1 remains an unlocked draft. No live collector or T0 exists. Pine compilation in TradingView is not verified.

## Components

- **Move-Odds:** movement timing/odds, not Long/Short direction.
- **D-LIQ:** a draft directional-continuation hypothesis using delivered liquidation snapshots.
- **Risk-First:** manual trade-plan risk checklist, not a signal.
- **Forward Journal:** evidence capture and verification protocol; r7 is draft/unlocked.

Keep these claims separate. Do not combine components without independent gates and a new preregistration.

## Recovered Atlas input

The uploaded BTCUSDT five-minute gzip dataset has been identified as the exact historical `pkg_data.csv` input expected by Atlas v1: the decompressed SHA-256 matches the prefix recorded in the Atlas README. Structural checks pass for 602,208 UTC bars from 2021-01-01 through 2026-09-22.

The Atlas pipeline was rerun in an isolated workbench: build, engine tests, stats tests, main analysis, 300-draw placebo, tiering, and descriptive modules completed. See [dataset audit](docs/BTCUSDT_5M_DATA_AUDIT_2026-10-30.md) and [Atlas reproduction report](docs/ATLAS_REPRODUCIBILITY_RUN_2026-10-30.md).

**Important:** the recovered history is already burned by prior research. Reproduction is not fresh evidence, a tradable edge, or proof of profitability after costs. The binary dataset and reproduced-output archive are present in the prepared v3 bundle; verify their presence on GitHub separately before assuming remote storage.

## Start here

- [Current status](docs/STATUS.md)
- [Project map](docs/PROJECT_MAP.md)
- [Research rules](docs/RESEARCH_RULES.md)
- [Upload manifest](docs/UPLOAD_MANIFEST.md)
- [Artifact register](docs/ARTIFACT_REGISTER.md)
