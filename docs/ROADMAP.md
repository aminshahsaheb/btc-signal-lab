# Roadmap and completion gates

## Gate 0 — Repository and provenance

- [x] Separate BTC research from unrelated projects.
- [x] Preserve source packages and dated decision/review documents in the local v3 package.
- [x] Recover the exact Atlas input by decompressed SHA-256 prefix.
- [x] Validate 602,208 five-minute rows and rerun Atlas pipeline/tests locally.
- [x] Verify current remote GitHub tree; 24 files confirmed.
- [ ] Transfer the remaining approved source artifacts and binaries to GitHub (large files require Git LFS or release assets; connector currently cannot verify those uploads).
- [ ] Reconcile the complete local v3 package with remote main tree.

## Gate 1 — Move-Odds runtime verification

- [ ] Compile v0.1.2 in TradingView on a standard time-based 1h `BINANCE:BTCUSDT.P` chart.
- [ ] Compare all 12 golden vectors and record exact compiler/output evidence.
- [ ] Do not tune the algorithm to fit expected values without a documented discrepancy review.

## Gate 2 — D-LIQ r2 closure

- [ ] Resolve every blocking issue in the r1 review.
- [ ] Freeze statistical method, sample accounting, valid/malformed statuses, duplicate handling, missing-price treatment and PASS/FAIL/INCONCLUSIVE rules.
- [ ] Freeze the standalone journal/anchoring contract, verifier and analysis-code hashes.
- [ ] Recalculate power under declared dependence assumptions.
- [ ] Preserve one-sided continuation; no reversal rescue.

## Gate 3 — Quality probe

- [ ] Only after protocol lock, run a short feed-quality-only probe.
- [ ] Do not collect price streams or score outcomes during the probe.
- [ ] Record uptime, gaps, timestamps, duplicate behavior and coverage.
- [ ] Exclude the probe permanently from forward hypothesis evaluation.

## Gate 4 — Forward directional test

- [ ] Lock specification, code, journal and anchoring.
- [ ] Declare T0 on the frozen grid.
- [ ] Capture every scheduled slot, including NONE and missing-price cases.
- [ ] Run only the preregistered analysis on eligible post-T0 observations.
- [ ] Close under frozen failure/inconclusive rules.

## Gate 5 — Strategy and venue validation

- [ ] Only after directional PASS, preregister entry/stop/target/exit rules separately.
- [ ] Use independent data.
- [ ] Measure actual KCEX fees, spread, slippage, funding and fills.
- [ ] Make no profitability claim without net out-of-sample forward evidence.
