# Remote synchronization audit — 2026-11-03

> **HISTORICAL RECORD — superseded for current state.** This document describes the repository as of 2026-11-03; it states that the repository is Private; the repository has been Public since 2026-11-04. The repository is **Public** by owner decision of 2026-11-04. Current state: [`STATUS.md`](STATUS.md). Master checklist: [`ROADMAP.md`](ROADMAP.md). The text below is preserved unchanged.


## Verified snapshot

- Repository: `aminshahsaheb/btc-signal-lab`
- Visibility: **Private**
- Baseline commit immediately before this documentation refresh: `6379cfd1233a16d29787624ef773d295a5b4c265`
- Recursive Git tree: **159 entries**, including tree objects; **115 file blobs**. API response: `truncated=false`.
- Full SHA-256 inventory: **114 file rows**, excluding the inventory file itself.
- Risk-First source copies: 18,364 bytes; SHA-256 `43e41fcbf8b8590b3267400b0c7f5744473893a67c675a10b291725853480257`.
- Move-Odds v0.1.2 source copies: 16,009 bytes; SHA-256 `d07865ebf10a7f5908aca69a90f792c90af601ef36bb5c4ef76b0ae1c192a84d`.
- The repository remains private.

## Verified PR and CI history

- PR #9: Risk-First v0.3.1 table label and inventory correction. Run #66 passed on exact head `db1c03ca6780f0a1cfc638aa0b968a7f92bb091d`; merge `0ae8a0cd9af36d681a88fbd4849303bd7039210a`.
- PR #11: README, STATUS, ROADMAP, remote-sync and execution-plan reconciliation. Runs #85 and #86 passed on exact head `09bad9e582b1962c1f3c35d8fe54422a3cad0c84`; merge `69e716ff4ca4a5cd71b63f4107a746371af08706`.
- PR #12: duplicate Pine source synchronization and manifest repair. Runs #98 and #99 passed on exact head `8571a4fffdb6058c82a2ae5df4b0caa5f94db67c`; merge `6379cfd1233a16d29787624ef773d295a5b4c265`.
- PR #1 and #2: closed without merge; superseded by PR #11. Their branches remain available.
- PR #3: closed without merge as superseded D-LIQ r2; branch/history remains available.
- PR #10: closed without merge; temporary audit-only PR.
- PR #6: merged; added the original repository-wide execution plan.

The source-integrity workflow passed on the exact final heads for PR #9, #11 and #12. These checks do not prove Pine compilation, strategy validity, live-feed quality, or KCEX profitability.

## Data and artifact checks

- The v4 ZIP is internally consistent according to its included inventory, but it is **not** a current mirror of `main`. Its embedded upload/sync notes describe an older 27-file state.
- Atlas archive and input structural checks are recorded in the dated audit documents. The BTCUSDT dataset has 602,208 rows and ends on 2026-09-22. It is burned historical research data.
- The remote inventory confirms repository file identity. It does not establish independent market-data provenance or data-rights approval.

## Remaining verification

1. Complete path-by-path v4-to-main classification: identical, changed, local-only, remote-only, or unsafe to publish.
2. Complete secrets, personal-data, licensing and data-rights review. Keep the repository private.
3. Obtain TradingView compiler/runtime evidence for Move-Odds v0.1.2 and Risk-First v0.3.1.
4. Keep D-LIQ r3 and Forward Journal r7 unlocked until their separate scientific and operational gates pass.
5. Measure KCEX fees, spread, slippage, funding, and fills only after independent directional evidence passes.

## Exclusions

Do not commit credentials, API keys, access tokens, private account details, raw private conversation exports, or unapproved live capture. Do not make the repository public before data-rights and licensing review.