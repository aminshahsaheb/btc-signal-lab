# BTC Signal Lab — repository-wide execution plan

Audit date: 2026-11-03  
Baseline: `main` at `1886f9e6b5e424bd6e421b28eded3b068ff25398`  
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

- Four branches: `main`, `audit/post-publication-sync-corrections`, `research/dliq-r2-spec`, `research/strategy-program-v1`.
- PR #1 is a documentation reconciliation branch, seven commits ahead of main, six files changed. It needs exact PR-head verification before merge.
- PR #2 is the strategy-program draft. It needs independent review against the frozen research rules and prior negative results.
- PR #3 is the D-LIQ r2 draft. Preserve its history; do not merge it as the current protocol.
- D-LIQ r3 has separate intake findings in issues #4 and #5. It remains unlocked.
- The v4 ZIP is not a current mirror of main. Its embedded upload manifest and remote-sync checklist still describe an older 27-file state. Do not bulk-copy it over the repository.

## Ordered checklist

### A. Baseline and source reconciliation
- [ ] Re-fetch main head, recursive remote tree, branch heads, PRs, issues, and workflow runs.
- [ ] Record exact SHA-256 hashes for v2/v3/v4 and the r3 package.
- [ ] Compare v4 inventory against the current remote tree. Classify each path: identical, changed, local-only, remote-only, or unsafe to publish.
- [ ] Reconcile ZIP entries, actual files, remote blobs, and manifest rows as separate counts.
- [ ] Audit secrets, personal data, raw conversation exports, and data-use rights.
- [ ] Keep the repository private.

### B. Existing pull requests
- [ ] PR #1: inspect all changed files, inventory/hash consistency, and workflow on the exact PR head. Merge only after review and successful checks on that head.
- [ ] PR #2: review the full strategy-program diff against prior experiment records, holdout discipline, fees, walk-forward, Monte Carlo, and multiple-testing controls.
- [ ] PR #3: preserve r2 as history. Do not treat it as current protocol. Create a separate r3 PR only after r3 blockers close.

### C. Tool packages
- [ ] Move-Odds v0.1.2: compile in TradingView; verify all 12 golden vectors on the declared chart; preserve raw evidence and discrepancies.
- [ ] Risk-First Helper v0.3.1: compile and test separately; keep its manual-checklist status.
- [ ] Atlas v1: verify archive/input hashes and reproduce from a clean environment. Historical data remains previously used discovery evidence.
- [ ] Run all scripts from a clean checkout.

### D. D-LIQ r3 and Forward Journal
- [ ] Resolve outcome-dependent missingness failure from synthetic calibration S10. Do not adopt OPEN-21 or a threshold without independent rationale and preregistration.
- [ ] Implement and test the `slots.csv` builder.
- [ ] Complete all four differential-verifier seeds. Preserve logs, environment, hashes, and disagreements.
- [ ] Obtain independent adversarial review of the verifier and contract.
- [ ] Verify Binance raw-message semantics in an authorized format-only probe. No market-price stream or outcome analysis during this probe.
- [ ] Select and end-to-end test a real external anchor. `MockAnchor` is insufficient.
- [ ] Select and verify collector host, clock, network, and retention controls.
- [ ] Resolve entry-candle capture and all OPEN protocol parameters before lock.
- [ ] Review Forward Journal r7 independently. Do not treat a draft as a locked dependency.
- [ ] Only after all gates pass, make a separate lock decision. No collector, T0, directional scoring, or market outcome analysis before that decision.

### E. Strategy and venue validation
- [ ] Preserve all rejected experiments and exact reasons.
- [ ] Freeze the hypothesis, target, sample, costs, and evaluation plan before confirmation/holdout inspection.
- [ ] Apply the fixed chain: hypothesis, bootstrap/significance, fees, train/test, independent-block walk-forward, trade/candle-path Monte Carlo, and multiple-testing/DSR controls.
- [ ] If direction passes, create a separate strategy preregistration.
- [ ] Measure KCEX fees, spread, slippage, funding, and fills independently. Binance returns do not prove KCEX profitability.

## Current holds

- No established profitable or independently validated strategy.
- No D-LIQ collector, T0, or forward directional test.
- No TradingView compilation evidence for Move-Odds v0.1.2 or Risk-First Helper v0.3.1.
- No production anchor or collector host verified for D-LIQ r3.
- No authorization to publish the repository or sensitive/private data.

## Completion standard

A task is complete only when evidence is linked, the exact commit is identified, and required checks pass on that commit. Synthetic tests prove behavior only for their tested fixtures.