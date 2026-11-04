# BTC Signal Lab — repository-wide execution plan

Audit date: 2026-11-04  
Baseline snapshot immediately before this documentation refresh: `6379cfd1233a16d29787624ef773d295a5b4c265`  
Repository visibility at this audit: public (confirmed by GitHub metadata on 2026-11-04); this is a status fact, not rights clearance.

## Operating rules

- Work in isolated branches. Never force-push.
- A missing CI result is unknown, not success.
- Mark a task complete only with evidence, exact commit SHA, and required checks on that commit.
- Keep historical failures and rejected hypotheses.
- Do not claim an edge or profitability without independent out-of-sample and forward evidence.
- Do not publish credentials, tokens, private account data, raw private conversations, or restricted data.
- The repository is currently public. Do not treat visibility as data-rights or licensing clearance; do not expand redistribution before source-specific review.

## Verified baseline

- Baseline snapshot: `6379cfd1233a16d29787624ef773d295a5b4c265`.
- Recursive Git tree: 159 entries, 115 file blobs; response not truncated.
- Full file inventory: 114 rows; it excludes itself.
- PR #9: exact inventory fix; run #66 passed on head `db1c03ca6780f0a1cfc638aa0b968a7f92bb091d`; merge `0ae8a0cd9af36d681a88fbd4849303bd7039210a`.
- PR #11: docs reconciliation; runs #85/#86 passed on exact head `09bad9e582b1962c1f3c35d8fe54422a3cad0c84`; merge `69e716ff4ca4a5cd71b63f4107a746371af08706`.
- PR #12: duplicate Pine source copies and manifests synchronized; runs #98/#99 passed on exact head `8571a4fffdb6058c82a2ae5df4b0caa5f94db67c`; merge `6379cfd1233a16d29787624ef773d295a5b4c265`.
- PR #1/#2: closed without merge; changes reconciled or preserved by PR #11.
- PR #3: closed without merge as superseded D-LIQ r2; retain history.
- PR #10: closed without merge after temporary hash audit.
- D-LIQ r3 review is recorded in Issues #4/#5; it remains unlocked.
- Forward Journal r7 remains unlocked; D25 is not satisfied.
- v4 ZIP is internally consistent but is not a current mirror of main.

## Ordered checklist

### A. Baseline and source reconciliation
- [x] Re-fetch main head, recursive tree, PRs, issues, and workflow evidence after PR #12.
- [x] Confirm the baseline tree has 115 file blobs and inventory has 114 rows; historical privacy state is not evidence of current visibility.
- [x] Reconcile README, STATUS, ROADMAP, remote-sync and execution plan in PR #11; exact-head CI passed.
- [x] Synchronize duplicate Pine source copies and regenerate manifests in PR #12; exact-head CI passed.
- [ ] Compare every v4 path with the current remote tree and record path classes.
- [ ] Review archives for secrets, personal data, raw conversation exports, and data-use rights.
- [ ] Resolve the current public-visibility and release policy after source-specific data-rights and licensing review; do not infer clearance from the existing public state.

### B. Pull requests
- [x] PR #1/#2: closed without merge; replaced or superseded by PR #11.
- [x] PR #3: closed as superseded; keep r2 history.
- [x] PR #9: label and inventory corrected; exact-head CI passed; merged.
- [x] PR #11: docs reconciled; exact-head CI passed; merged.
- [x] PR #12: duplicated Pine sources synchronized; exact-head CI passed; merged.
- [x] PR #10: temporary audit-only PR closed without merge.

### C. Tool packages
- [x] Move-Odds local static linter: 141 values parsed; zero lint errors and zero value mismatches.
- [x] Move-Odds replica: all 12 golden vector rows matched; hour/day/range groups matched; five 24-hour break-window differences were identified as a 5m-versus-1h window-boundary effect.
- [ ] Move-Odds v0.1.2: compile in TradingView on a standard 1h `BINANCE:BTCUSDT.P` chart.
- [ ] Execute and record all 12 golden vectors with expected-versus-observed values.
- [ ] Preserve raw compile/runtime evidence for Move-Odds and Risk-First, including exact source SHA, chart/symbol/timeframe, settings, and test context.
- [x] Risk-First v0.3.1 label, duplicate source copy, root checksum, and full inventory corrected; exact-head CI passed.
- [ ] Risk-First v0.3.1: compile and test in TradingView; keep it a manual checklist.
- [x] Atlas archive/input identity and structural checks are recorded; historical reproduction was completed in the supplied isolated workbench.
- [ ] Repeat Atlas pipeline from a fresh clean checkout with exact environment and commands if needed. Historical input remains burned.
- [ ] Run every script from a clean checkout and record outputs/hashes.

### D. D-LIQ r3 and Forward Journal
- [x] Verify r3 package ZIP identity and internal manifest.
- [x] Record supplied synthetic test evidence and local differential-run timeout limitation.
- [x] Record S10 outcome-dependent missingness failure; OPEN-21 proposal is not adopted.
- [ ] Resolve missingness failure with preregistered policy and wider sensitivity tests.
- [ ] Implement and test the `slots.csv` builder.
- [ ] Complete all four differential seeds in a clean environment.
- [ ] Obtain independent adversarial review / third-party verifier.
- [ ] Resolve OPEN-17, OPEN-18, OPEN-21, N-6 and remaining normative values.
- [ ] Verify Binance raw-message semantics in an approved format-only probe.
- [ ] Select and end-to-end test a real external anchor.
- [ ] Select and verify collector host, clock, network, and retention controls.
- [ ] After protocol prerequisites, run a dry-run of at most 20 D-LIQ messages for format/data-quality only; no price attachment, scoring, or outcome analysis.
- [ ] Review Forward Journal r7 KAT provenance, D1-D24 evidence, two-namespace contract, and D25.
- [ ] Only after all gates pass, make a separate lock decision. No collector, T0, directional scoring, or market outcome analysis before that decision.

### E. Strategy and venue validation
- [x] Preserve rejected experiments and the rule that burned history cannot be renamed into holdout.
- [ ] Freeze every future hypothesis, target, sample, costs, statistic, code hash, stopping rule, and T0 before outcome inspection.
- [ ] Apply bootstrap/significance, fees, train/test, independent-block walk-forward, trade/candle-path Monte Carlo, and multiple-testing/DSR controls.
- [ ] If direction passes, create a separate strategy preregistration.
- [ ] Measure KCEX fees, spread, slippage, funding, and fills independently.

## G. Parallel utility track (scope decision required)

- [ ] Record whether the utility track is a personal-use tool or a public product.
- [ ] Define utility acceptance criteria separately from strategy profitability (alert integrity/timeliness, journal completeness, and risk-check workflow). Do not expand implementation scope before the owner decision.

## Current holds

- No established profitable or independently validated strategy.
- No D-LIQ r3 lock, collector, T0, or forward directional test.
- No TradingView compilation evidence for Move-Odds v0.1.2 or Risk-First Helper v0.3.1.
- No production anchor or collector host verified for D-LIQ r3.
- Forward Journal r7 remains unlocked.
- The repository is currently public; no public-release, licensing, or redistribution clearance is implied. Do not publish sensitive/private data.

## Completion standard

A task is complete only when evidence is linked, the exact commit is identified, and required checks pass on that commit. Synthetic tests prove behavior only for their tested fixtures.