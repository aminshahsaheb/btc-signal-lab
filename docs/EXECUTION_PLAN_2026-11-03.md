# BTC Signal Lab — repository-wide execution plan

Audit date: 2026-11-03  
Baseline: `main` at `0ae8a0cd9af36d681a88fbd4849303bd7039210a`  
Repository: private

## Operating rules

- Work in isolated branches. Never force-push.
- A missing CI result is unknown, not success.
- Mark a task complete only with evidence, exact commit SHA, and required checks on that commit.
- Keep historical failures and rejected hypotheses.
- Do not claim an edge or profitability without independent out-of-sample and forward evidence.
- Do not publish credentials, tokens, private account data, raw private conversations, or restricted data.
- Do not make the repository public before data-rights and licensing review.

## Verified baseline

- `main` is `0ae8a0cd9af36d681a88fbd4849303bd7039210a`.
- Recursive Git tree: 157 entries, 113 file blobs; response not truncated.
- Full file inventory: 112 rows; it excludes itself.
- PR #9: exact source inventory corrected; run #66 passed on head `db1c03ca6780f0a1cfc638aa0b968a7f92bb091d`; squash merge commit is the current main head.
- PR #3: closed as superseded, not merged; retain the r2 branch and test history.
- PR #10: closed as temporary audit-only PR.
- PR #1 and #2: still open, with stale bases and historical CI only. Do not merge them as-is.
- D-LIQ r3 package review is recorded in Issues #4 and #5; r3 remains draft/unlocked.
- Forward Journal r7 is draft/unlocked; D25 is not satisfied.
- v4 ZIP is internally consistent but not a current mirror of main.

## Ordered checklist

### A. Baseline and source reconciliation
- [x] Re-fetch current main head, recursive tree, PRs, issues, and workflow evidence after PR #9.
- [x] Confirm main is private; tree has 113 file blobs and inventory has 112 rows.
- [ ] Reconcile README, STATUS, ROADMAP, remote-sync and execution-plan documents on an isolated branch; regenerate inventory and require exact-head CI.
- [ ] Compare every v4 path with the current main tree and record path classes.
- [ ] Review archived files for secrets, personal data, raw conversation exports, and data-use rights.
- [ ] Keep the repository private.

### B. Existing pull requests
- [ ] PR #1: replace stale synchronization statements; inspect all changes; regenerate manifests; pass CI on exact new head; merge only after review.
- [ ] PR #2: retain the strategy-program research only with a dated status amendment; reconcile old D-LIQ r1/Ribbon statements with current Issues #4/#5 and frozen research decisions; pass CI on exact new head.
- [x] PR #3: close as superseded without merge; preserve branch/history.
- [x] PR #9: correct label and inventory; exact-head CI passed; merged as current main.
- [x] PR #10: close temporary hash-audit PR after recording the exact hash and size.

### C. Tool packages
- [ ] Move-Odds v0.1.2: compile in TradingView; verify all 12 golden vectors on the declared chart; preserve raw evidence and discrepancies.
- [x] Risk-First v0.3.1: correct user-facing version label and exact inventory row; CI passed on exact PR head before merge.
- [ ] Risk-First v0.3.1: compile and test separately in TradingView. It remains a manual checklist.
- [x] Atlas v1: archive/input identity and structural checks are recorded; historical pipeline reproduction was completed in an isolated workbench.
- [ ] Repeat Atlas pipeline from a fresh clean checkout only if the exact environment and commands can be preserved; historical input remains burned.
- [ ] Run all scripts from a clean checkout and record outputs/hashes.

### D. D-LIQ r3 and Forward Journal
- [x] Verify r3 package ZIP identity and internal manifest.
- [x] Record supplied synthetic test evidence and the local differential-run timeout limitation.
- [x] Record the S10 outcome-dependent missingness failure; OPEN-21 proposal is not adopted.
- [ ] Resolve missingness failure with preregistered policy and wider sensitivity tests.
- [ ] Implement and test the `slots.csv` builder.
- [ ] Complete all four differential seeds in a clean environment.
- [ ] Obtain independent adversarial review / third-party verifier.
- [ ] Resolve OPEN-17, OPEN-18, OPEN-21, N-6 and remaining normative values.
- [ ] Verify Binance raw-message semantics in an approved format-only probe.
- [ ] Select and end-to-end test a real external anchor.
- [ ] Select and verify collector host, clock, network, and retention controls.
- [ ] Review Forward Journal r7 KAT provenance, D1-D24 evidence, two-namespace contract, and D25.
- [ ] Only after all gates pass, make a separate lock decision. No collector, T0, directional scoring, or market outcome analysis before that decision.

### E. Strategy and venue validation
- [x] Preserve rejected experiments and the rule that burned history cannot be renamed into holdout.
- [ ] Freeze every future hypothesis, target, sample, costs, statistic, code hash, stopping rule, and T0 before outcome inspection.
- [ ] Apply the fixed chain: hypothesis, bootstrap/significance, fees, train/test, independent-block walk-forward, trade/candle-path Monte Carlo, and multiple-testing/DSR controls.
- [ ] If direction passes, create a separate strategy preregistration.
- [ ] Measure KCEX fees, spread, slippage, funding, and fills independently. Binance returns do not prove KCEX profitability.

## Current holds

- No established profitable or independently validated strategy.
- No D-LIQ r3 lock, collector, T0, or forward directional test.
- No TradingView compilation evidence for Move-Odds v0.1.2 or Risk-First Helper v0.3.1.
- No production anchor or collector host verified for D-LIQ r3.
- Forward Journal r7 remains unlocked.
- No authorization to publish the repository or sensitive/private data.

## Completion standard

A task is complete only when evidence is linked, the exact commit is identified, and required checks pass on that commit. Synthetic tests prove behavior only for their tested fixtures.