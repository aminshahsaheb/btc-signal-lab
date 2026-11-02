# Remote synchronization audit — 2026-11-03

## Verified remote state

- Repository: `aminshahsaheb/btc-signal-lab`
- Visibility: **Private**
- Branch: `main`
- Verified head: `0ae8a0cd9af36d681a88fbd4849303bd7039210a`
- Recursive Git tree: **157 entries**, including tree objects; **113 file blobs**. API response: `truncated=false`.
- Full SHA-256 inventory: **112 file rows**, excluding the inventory file itself.
- Risk-First v0.3.1 source row: 18,364 bytes; SHA-256 `43e41fcbf8b8590b3267400b0c7f5744473893a67c675a10b291725853480257`.
- The repository remains private.

## Latest repository CI evidence

PR #9 changed only the Risk-First table label and its inventory row. The exact PR head was `db1c03ca6780f0a1cfc638aa0b968a7f92bb091d`. GitHub Actions run #66 completed successfully on that exact head. PR #9 was squash-merged as `0ae8a0cd9af36d681a88fbd4849303bd7039210a`.

This validates source integrity for the configured checks. It is not a TradingView compiler result, a trading hypothesis result, a live-feed test, or a KCEX execution result.

## Pull-request disposition

- PR #1: still open; documentation branch uses an older base and includes old synchronization language. It must not be merged without a fresh reconciliation and exact-head CI.
- PR #2: still open; strategy-program draft has valuable historical synthesis, but its D-LIQ/Ribbon status needs a dated supersession note before acceptance.
- PR #3: closed without merge as superseded. Preserve its r2 source/tests and branch history.
- PR #9: merged after exact-head CI.
- PR #10: closed without merge. It was a temporary audit PR used to calculate the exact Risk-First source hash and size.

## Data and artifact checks

- The v4 ZIP is internally consistent according to its included inventory, but it is **not** a current mirror of `main`. Its upload and synchronization notes describe an earlier 27-file state.
- The Atlas package/input structural checks and the 602,208-row BTCUSDT dataset checks are recorded in the dated audit documents. This dataset ends on 2026-09-22 and is burned historical research data.
- The remote inventory confirms paths and hashes. It does not establish data-rights approval or independent source provenance.

## Verification limits and next steps

1. Complete a path-by-path comparison of v4 against the current remote tree. Classify each path as identical, changed, local-only, remote-only, or unsafe to publish.
2. Review all archives for credentials, private data, raw conversations, and data-use restrictions. Keep the repository private.
3. Reconcile the README, STATUS, ROADMAP, and execution plan on one isolated branch. Regenerate both inventories affected by content changes and run CI on the exact final PR head.
4. Obtain TradingView compiler evidence for Move-Odds v0.1.2 and Risk-First v0.3.1.
5. Keep D-LIQ r3 and Forward Journal r7 unlocked until their separate scientific and operational gates pass.

## Exclusions

Do not commit credentials, API keys, access tokens, private account details, raw private conversation exports, or unapproved live capture. Do not make the repository public before data-rights and licensing review.