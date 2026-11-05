# Roadmap — 2026-11-05

The source of truth for current decisions is `docs/STATUS.md`. This roadmap does not authorize live data collection or trading.

## Gate 0 — Repository baseline and integrity

- [x] Repository is Public by owner decision as of 2026-11-04; preserve the open licensing and data-rights review.
- [x] Preserve archived packages, historical decisions, and failed research results.
- [x] Verify the current recursive Git tree is not truncated: 167 tree entries, 123 file blobs (current main snapshot after maintenance merges).
- [x] Confirm the full inventory contains 122 rows and excludes itself.
- [x] Correct the Risk-First v0.3.1 table label and inventory row. PR #9 run #66 passed on exact head `db1c03ca6780f0a1cfc638aa0b968a7f92bb091d`; merge `0ae8a0cd9af36d681a88fbd4849303bd7039210a`.
- [x] Reconcile README, STATUS, ROADMAP, remote-sync and execution-plan documents in PR #11; runs #85/#86 passed on exact head `09bad9e582b1962c1f3c35d8fe54422a3cad0c84`; merge `69e716ff4ca4a5cd71b63f4107a746371af08706`.
- [x] Synchronize duplicate Pine sources and regenerate manifests in PR #12; runs #98/#99 passed on exact head `8571a4fffdb6058c82a2ae5df4b0caa5f94db67c`; merge `6379cfd1233a16d29787624ef773d295a5b4c265`.
- [ ] Complete the path-by-path v4-to-main classification and the secrets/data-rights review before any publication decision.

## Current maintenance PR status — 2026-11-05

The owner-approved order is complete through PR #16: PR #25 carried the workflow-only change from conflict-heavy #17, then #18, #19, and #16 merged with current-main synchronization, fresh inventory, and exact-head CI. The corresponding merge commits are `e66eb99`, `46ab8d2`, `58a8442`, and `098309e`. PR #26 added the inventory-regeneration guard found in overlapping PR #21 and is merged at `f6763e6`; PR #21 is closed as superseded. Original PR #17 remains open/draft with stale docs and is not the workflow source.

PR #15 is the final ordered item and remains OPEN / DRAFT at `656cbe5a4804e9a3faffeb3df9e399a8210dfd06`, synchronized with current main. Exact-head run #41944735094 passed 25 synthetic tests, inventory regeneration, SHA-256 verification, and archive screening, including forged-report rejection. It must remain Draft until independent third-party review; SLOT replay parity and grid-boundary policy remain open. PR #23 is an unlocked `r3-reconstruction`, not r3.1. PR #24 is the current documentation reconciliation draft. Public visibility does not imply rights clearance.

## Gate 1 — Move-Odds and Risk-First runtime checks

### Move-Odds v0.1.2
- [ ] Compile the exact Pine source in TradingView.
- [ ] Use a standard time-based 1-hour `BINANCE:BTCUSDT.P` chart.
- [ ] Compare all 12 golden vectors with the rendered values.
- [ ] Save compiler output, chart context, values, and discrepancies.
- [ ] Do not change the algorithm to fit expected values without a dated discrepancy review.

### Risk-First Helper v0.3.1
- [x] Correct the rendered version label and the exact inventory row; source-integrity CI passed on the exact PR head before merge.
- [ ] Compile the exact `pine/risk-first/RiskFirst_Helper_v0_3_1.pine` source in TradingView.
- [ ] Test the supported chart types, invalid inputs, long/short checklist, risk cap, stop/target calculations, and alerts. Preserve raw evidence.
- [ ] Keep this tool described as a manual checklist, not a signal.

## Gate 2 — D-LIQ r3 protocol review

Current disposition: **HOLD — DRAFT / NOT LOCKED**. See Issues #4 and #5.

- [x] Verify r3 package identity and its internal manifest.
- [x] Record the supplied synthetic-test results and their provenance limits.
- [x] Record S10 outcome-dependent missingness failure; do not adopt OPEN-21 from the current synthetic proposal.
- [ ] Pre-register and test more than one outcome-dependent and volatility-dependent missingness mechanism; justify any policy before lock.
- [ ] Independently review the candidate builders in PR #15 and PR #23. PR #23 is r3-reconstruction, not r3.1; test clean, incomplete, tampered, and boundary cases before accepting implementation status.
- [ ] Independently complete the original r3 package four-seed differential run in a clean, sufficiently provisioned environment; keep PR #23's synthetic reconstruction run separate and preserve commands, environment, logs, hashes, and disagreements.
- [ ] Obtain a third-party verifier or independent adversarial review.
- [ ] Resolve OPEN-17, OPEN-18, OPEN-21, N-6 and the remaining protocol values in a dated decision record.
- [ ] Obtain explicit approval and a reachable host for a maximum-20-message format-only Binance dry run. Do not collect price streams or score outcomes in this phase.
- [ ] Select and end-to-end test a real external anchor with timestamp, resolution, and uncertainty bounds.
- [ ] Select and verify the collector host, clock, network, and retention controls.
- [ ] Re-run the final immutable candidate and make a separate lock decision only after every P0 gate passes.

Until then: no collector, T0, market-price scoring, forward directional test, or strategy use.

## Gate 3 — Forward Journal r7

Current disposition: **DRAFT / NOT LOCKED / SPEC ONLY**. See Issue #8.

- [x] Confirm D25 is not satisfied: no independently verified real anchor and no complete two-namespace end-to-end exercise.
- [x] Confirm the D-LIQ r3 package includes the r7 specification but no separate r7 KAT harness/run report.
- [ ] Verify the r7 KAT/harness identity, hashes, and provenance.
- [ ] Re-run all available synthetic KATs in a clean environment and save exact outputs.
- [ ] Map D1-D24 to evidence or an explicit untested status.
- [ ] Independently review the two-namespace target contract and D25 acceptance test.
- [ ] Obtain third-party adversarial review.
- [ ] Keep r7 unlocked until every gate has evidence and a separate lock decision.

## Gate 4 — Strategy validation

- [x] Preserve the rule that discovery/confirmation data are burned and cannot become holdout by renaming.
- [x] Preserve rejected hypotheses and their reasons.
- [ ] For any new candidate, preregister the hypothesis, direction, target, sample, costs, statistic, stopping rules, code hash, and T0 before outcome inspection.
- [ ] Apply the fixed validation chain: bootstrap/significance, fees, train/test, independent-block walk-forward, trade/candle-path Monte Carlo, and multiple-testing/DSR.
- [ ] Do not reopen closed MA/EMA/Ribbon families on the same historical data.
- [ ] Make no edge or profitability claim from synthetic tests or historical discovery data.

## Gate 5 — KCEX execution

- [ ] Start only if a directional hypothesis passes its own frozen test.
- [ ] Preregister entry, stop, target, sizing, and exit rules separately.
- [ ] Measure KCEX fees, spread, slippage, funding, and actual fills.
- [ ] Evaluate net results on independent data and a forward period.
- [ ] Do not infer KCEX profitability from Binance reference returns.

## Closure rules

- PR #3 is closed as superseded; its r2 branch/history is preserved.
- PR #9 is merged after exact-head CI.
- PR #10 is closed without merge; it was a temporary hash-audit PR.
- PR #11 is merged; it reconciles the current documentation and research status.
- PR #12 is merged; it synchronizes duplicate Pine source copies and their manifests.
- PR #1 and #2 were closed without merge; their content was reconciled or preserved in PR #11.
- Issues #4, #5, and #8 remain open while their scientific/operational gates are open.
- Do not close the master issue until every applicable item has evidence, an exact commit, and required checks.