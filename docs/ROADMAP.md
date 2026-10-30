# Roadmap

## Gate 0 — Repository baseline

- [x] Keep the BTC research separate from Fanus repositories.
- [x] Preserve source package hashes and archived decision/review documents.
- [x] Keep locked/draft status explicit.
- [x] Create the GitHub repository as **private** and push the complete audited bundle. Remote head `1886f9e`; 112 file blobs verified; GitHub Actions source-integrity workflow passed.

## Gate 1 — Move-Odds runtime verification

- [ ] Paste the v0.1.2 Pine source into TradingView.
- [ ] Compile on a standard, time-based, 1-hour `BINANCE:BTCUSDT.P` chart.
- [ ] Compare all 12 golden vectors and save the exact result / errors.
- [ ] Do not modify the algorithm to fit the values without a documented discrepancy analysis.

## Gate 2 — D-LIQ r2 specification closure

- [ ] Freeze the statistical method and exact analysis-code hash.
- [ ] Specify valid message statuses and malformed-message window attribution.
- [ ] Define duplicate handling, including overlap behavior and the limits of identifying a unique event.
- [ ] Define primary sample counts, missing-price treatment, and `PASS` / `FAIL` / `INCONCLUSIVE` precisely.
- [ ] Complete the standalone journal/anchoring contract and independent verifier requirements.
- [ ] Recalculate power with the declared split and dependence assumptions.
- [ ] Keep the one-sided continuation hypothesis fixed; do not rescue with reversal.

## Gate 3 — Quality probe (only after the protocol authorizes it)

- [ ] Freeze the probe code/hash and allowed outputs.
- [ ] Collect feed quality only; do not collect market-price streams or analyze returns in this phase.
- [ ] Record uptime, gaps, timing, duplicate behavior, and coverage.
- [ ] Keep the probe permanently out of the forward hypothesis evaluation.

## Gate 4 — Forward directional test

- [ ] Lock specification, code, journal and anchoring.
- [ ] Declare T0 on the predefined time grid.
- [ ] Capture every scheduled slot, including `NONE` and missing price cases.
- [ ] Run only the preregistered analysis, using only eligible post-T0 observations.
- [ ] Close the branch under the frozen `FAIL` / `INCONCLUSIVE` rule.

## Gate 5 — Strategy and venue validation

- [ ] If and only if direction passes, write a separate strategy preregistration for entry/stop/target/exit.
- [ ] Evaluate the strategy on a period independent of the directional discovery.
- [ ] Measure real KCEX fees, spread, slippage, funding and fills.
- [ ] Make no profit claims without net, out-of-sample, forward evidence.
