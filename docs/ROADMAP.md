# Roadmap — 2026-11-03

The source of truth for current decisions is `docs/STATUS.md`. This roadmap does not authorize live data collection or trading.

## Gate 0 — Repository baseline and integrity

- [x] Keep the repository private.
- [x] Preserve archived packages, historical decisions, and failed research results.
- [x] Verify the current recursive Git tree is not truncated: 157 tree entries, 113 file blobs.
- [x] Confirm the full inventory contains 112 rows and excludes itself.
- [x] Correct the Risk-First v0.3.1 table label and inventory row. PR #9 passed CI on exact head `db1c03ca6780f0a1cfc638aa0b968a7f92bb091d` (run #66) and merged as `0ae8a0cd9af36d681a88fbd4849303bd7039210a`.
- [ ] Reconcile the remaining README, STATUS, ROADMAP, remote-sync and execution-plan records; regenerate inventory; require CI on the exact documentation PR head.
- [ ] Complete the path-by-path v4-to-main classification and the secrets/data-rights review before any publication decision.

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
- [ ] Implement the deterministic `slots.csv` builder and test clean, incomplete, tampered, and boundary cases.
- [ ] Complete all four differential seeds in a clean, sufficiently provisioned environment; preserve commands, environment, logs, hashes, and disagreements.
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
- PR #10 is closed; it was a temporary audit-only PR.
- PR #1 and PR #2 remain open until replaced or updated and reviewed on current `main`.
- Issues #4, #5, and #8 remain open while their scientific/operational gates are open.
- Do not close the master issue until every applicable item has evidence, an exact commit, and required checks.