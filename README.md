# BTC Signal Lab

**A private, evidence-first research workspace for Bitcoin market-movement timing, directional hypotheses, risk controls, and forward validation.**

> **Research status — 2026-10-30:** No trading strategy in this repository is established as profitable or independently validated. D-LIQ r1 is a draft and is **not locked**. No live collector is running, no D-LIQ market data has been scored, and no T0 has been set. Move-Odds Panel v0.1.2 and Risk-First Helper v0.3.1 have **not** been compiled in TradingView in this workspace.

## Why this repository exists

The research now has distinct components that need separate versioning, reproducibility checks, and evidence gates. Keeping them in a dedicated repository prevents them from being mixed with the unrelated Fanus projects or mistaken for one combined, validated strategy.

| Component | Question | Current status | What it does **not** prove |
|---|---|---|---|
| **Move-Odds** | When is a large BTC move more likely? | Historical research artifact; Pine v0.1.2 package included | Direction, profitability, or live correctness |
| **D-LIQ snapshot hypothesis** | Does the direction of delivered liquidation snapshots predict continuation over the next four hours? | Draft preregistration r1; not locked | A valid Long/Short edge |
| **Risk-First Helper** | Does a proposed trade plan respect configured risk checks? | Manual Pine checklist; v0.3.1 source included | Directional edge, automatic execution, or realised risk |
| **Execution validation** | Does a research signal survive actual fees, spread, slippage, funding, and venue differences? | Not started | KCEX profitability |

These components are not combined. A timing feature, a direction hypothesis, a risk checklist, and execution evidence answer different questions. No composite signal is permitted unless each component passes its own pre-defined gate and a new combination is preregistered independently.

## Start here

1. Read [`docs/STATUS.md`](docs/STATUS.md) for current decisions and blockers.
2. Read [`docs/PROJECT_MAP.md`](docs/PROJECT_MAP.md) for the layers and the research path.
3. Read [`docs/RESEARCH_RULES.md`](docs/RESEARCH_RULES.md) before changing any specification or looking at evaluation data.
4. Read the latest D-LIQ review: [`docs/reviews/2026-10-30-dliq-r1-move-odds-review.md`](docs/reviews/2026-10-30-dliq-r1-move-odds-review.md).
5. Run the integrity checks:

   ```bash
   python3 scripts/verify_sources.py
   ```

   The full file inventory is in `docs/FILE_INVENTORY_SHA256.csv`. After an intentional source change, regenerate it with `python3 scripts/generate_inventory.py`, then run the verifier. Review the diff before committing.

6. For Move-Odds, read [`tools/move-odds-panel/v0.1.2/README_FA.md`](tools/move-odds-panel/v0.1.2/README_FA.md). Its instructions include the twelve golden vectors. A static verification report is not a Pine compiler result; compile and compare in TradingView before treating the panel as runtime-verified.

## Source completeness and audit trail

The curated source audit is [`docs/PROJECT_AUDIT_2026-10-30.md`](docs/PROJECT_AUDIT_2026-10-30.md). It catalogs the research, archived releases, PDF report, journal revisions, privacy exclusions, and recovered source data. Older Move-Odds versions and Forward Journal r5/r6 are preserved instead of overwritten. The raw conversation export is deliberately not committed.

**Atlas input recovered:** the exact `pkg_data.csv` input has been supplied as a gzip file under `artifacts/data/`. Its decompressed SHA-256 matches the hash prefix in the Atlas README. The historical pipeline was rerun; see `docs/ATLAS_REPRODUCIBILITY_RUN_2026-10-30.md`.

## Current evidence and restrictions

- Historical BTC data from **2021-01-01 through 2026-09-22** has already been used for prior exploration and model selection. It is not a clean holdout for a new directional claim.
- The archived Atlas package is retained as a historical research artifact for provenance and inspection. Do not use it to rescue a failed hypothesis, tune thresholds, or claim forward evidence.
- D-LIQ r1 explicitly remains a draft. Its statistical method, message-validity rules, deduplication contract, sample accounting, and anchoring/journal design still need to be closed before lock.
- A pre-T0 data-quality probe, if eventually authorised by the locked protocol, must remain separate from the forward evaluation and must not examine returns or relationships with price.
- There is no exchange API key, credential, raw live capture, full OHLC dataset, or personal conversation export in this repository.

## Repository layout

```text
.
├── docs/
│   ├── decisions/       # Dated path decisions
│   ├── reviews/         # Independent reviews and blockers
│   ├── archive/         # Historical context/reports; not the active source of truth
│   ├── PROJECT_MAP.md
│   ├── RESEARCH_RULES.md
│   ├── ROADMAP.md
│   └── STATUS.md
├── specs/
│   ├── d-liq/           # Current and superseded preregistration drafts
│   └── forward-journal/ # Related but currently unlocked journal draft
├── tools/
│   ├── move-odds-panel/v0.1.2/  # Pine source, golden vectors, verifier and lookup artifact
│   └── riskfirst/              # Manual risk checklist, not a signal
├── artifacts/archives/  # Immutable input packages, historical releases, and Atlas package
├── scripts/             # Reproducibility/integrity utilities
└── .github/workflows/   # Lightweight integrity check in CI
```

## Verify source artifacts

The root manifest [`artifacts/SHA256SUMS.txt`](artifacts/SHA256SUMS.txt) pins selected source files and archival ZIPs. The full inventory [`docs/FILE_INVENTORY_SHA256.csv`](docs/FILE_INVENTORY_SHA256.csv) hashes every repository file except itself, and the Move-Odds v0.1.2 package retains its internal manifest. The verifier checks all three, tests ZIP structure, and compares the browsable v0.1/v0.1.1 source trees byte-for-byte with their original ZIPs. A passing checksum test confirms file identity only; it does **not** confirm the trading hypothesis, a TradingView compile, the live Binance feed, or KCEX execution. Also read [`docs/reviews/2026-10-30-move-odds-package-portability.md`](docs/reviews/2026-10-30-move-odds-package-portability.md): some historical verification scripts rely on an external `../atlas/` folder and one retains a v0.1.1 filename, so their logged outputs are preserved but the harness is not yet standalone from a clean clone.

## Safety and publication policy

This repository should start **private**. There is no license file because the intended reuse and publication terms have not been decided. Do not switch it to public until the archived artifact contents, data rights, and intended disclosures have been reviewed. Do not commit API keys, access tokens, raw live logs, or exchange account information.

This is a research record, not financial advice and not a promise of returns. It is designed to make a failed hypothesis easier to close than to rescue by tuning.

## Primary references

- [Binance USD-M liquidation snapshot stream](https://developers.binance.com/docs/derivatives/usds-margined-futures/websocket-market-streams/All-Market-Liquidation-Order-Streams)
- [Binance Derivatives API changelog](https://developers.binance.com/docs/derivatives/change-log)
- [TradingView Pine FAQ: other data and timeframes](https://www.tradingview.com/pine-script-docs/faq/other-data-and-timeframes/)
- [KCEX futures fee explanation](https://www.kcex.com/support/articles/24022325982105)


## Remote synchronization state

The current GitHub `main` tree has 27 verified files. The complete local v4 package has 98 files (including the inventory); several binary archives, dataset files, PDFs, and verification trees remain local-only until the bundle is synced. See `docs/REMOTE_SYNC_CHECKLIST.md`.

## Recovered Atlas input dataset

The exact historical `pkg_data.csv` input required by Atlas v1 is now preserved as `artifacts/data/BTCUSDT_5m_2021_to_latest_csv.gz`. Its decompressed SHA-256 matches the prefix recorded in the Atlas package README. Run `python3 scripts/verify_dataset.py` to verify identity and basic structure, then `python3 scripts/prepare_atlas_data.py` to prepare an isolated Atlas workbench. This dataset ends on 2026-09-22 and is burned historical research data, not fresh forward evidence.
