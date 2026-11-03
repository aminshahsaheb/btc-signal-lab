# BTC Signal Lab — repository-wide execution plan

Audit date: 2026-11-03 (live GitHub reconciliation)  
Main baseline: `da64085fe1c066026a6bee219b600d2b42f280f6`  
Repository: private

## Operating rules

- Work in isolated branches. Never force-push.
- A missing CI result is unknown, not success.
- Mark a task complete only with evidence, exact commit SHA, and required checks on that commit.
- Keep historical failures and rejected hypotheses.
- Do not claim an edge or profitability without independent out-of-sample and forward evidence.
- Do not publish credentials, tokens, private account data, raw private conversations, or restricted data.
- Do not make the repository public before data-rights and licensing review.
- A task on a draft PR is implemented on that branch; it is not merged into main.
- CI verifies only the code and checks it runs. It does not replace independent review or external operational evidence.

## Verified main baseline and merged work

- Main: `da64085fe1c066026a6bee219b600d2b42f280f6`.
- PR #9: exact-head CI passed; merged.
- PR #11: documentation reconciliation; exact-head CI passed; merged.
- PR #12: duplicate Pine source synchronization and manifest refresh; exact-head CI passed; merged.
- PR #14: snapshot correction; exact-head CI passed; merged as current main.
- PR #1/#2/#3/#10: closed without merge for documented superseding or temporary-audit reasons.
- Master ledger: Issue #7 remains open.

## Ordered checklist

### A. Repository and documentation

- [x] Reconcile prior merged work and verify current main SHA.
- [x] Preserve private repository status.
- [x] Re-fetch PR #15/#16, exact heads, review records, and latest PR CI.
- [x] Identify stale main documentation that still described current D-LIQ builder and four-seed rerun as incomplete.
- [ ] Merge the documentation reconciliation PR only after its exact-head CI passes and review is complete.
- [ ] Compare every v4 archive path with the current tree and record path classes.
- [ ] Review archives for secrets, personal data, raw conversation exports, licensing, and data-use rights.

### B. Active pull requests

#### PR #15 — D-LIQ r3 slots builder

- [x] Builder implementation and unit tests added on branch `research/dliq-r3-slots-builder-draft`.
- [x] CI includes Builder tests; 23 tests pass on the current branch head.
- [x] r3.1 archive identity and all 105 manifest entries verified in a clean extraction.
- [x] Four differential seeds 11–14 rerun: 120,336 comparisons, zero disagreements.
- [x] Strict OUTCOME checkpoint-coverage decision recorded and actual-verifier JSON fixtures tested.
- [x] Exact PR workflow #258 passed on head `86adcaffe9f22ff89354123b9b8316d9baabd64a`; push run #257 is recorded PASS in the ledger.
- [ ] Independent third-party/adversarial review.
- [ ] Decide whether production Builder/collector execution must enable optional primary SLOT replay. Do not claim independent SLOT replay parity.
- [ ] Resolve OPEN-17, OPEN-18, OPEN-21, N-6, and remaining protocol decisions.
- [ ] Obtain approved Binance format-only evidence, real anchor evidence, and collector host/clock/network/retention evidence.
- [ ] Final immutable candidate and separate lock decision only after all P0 gates pass.

#### PR #16 — Forward Journal r7 audit

- [x] D1–D25 mapped to evidence or explicit unproven status.
- [x] Confirmed no separate r7 writer, collector, auditor, verifier, metrics implementation, executable KAT harness, or KAT report in the audited tree.
- [x] Identified duplicate spec copies and recorded canonical-path decision as open.
- [x] Documented D25 Stage A and Stage B proof boundary; neither has evidence.
- [x] Exact PR workflow #235 passed on head `0f450809ee0a2318308e6072cdf952b8c10a4e3a`; push run #234 is recorded PASS in the ledger.
- [ ] Independent review of audit and D25 acceptance boundary.
- [ ] Resolve four Stage A/B normative details.
- [ ] Choose canonical r7 spec path before implementation.
- [ ] Implement and run r7 KATs and components.
- [ ] Complete independently verifiable D25 Stage A and Stage B evidence.
- [ ] Separate lock decision only after all gates pass.

Both PRs remain OPEN / DRAFT / NOT MERGED. Neither has a submitted review. Main is unchanged.

### C. TradingView tools

- [x] Move-Odds local static linter: 141 values parsed; zero lint errors and zero mismatches.
- [x] Move-Odds replica: 12 supplied golden rows matched; five 24-hour break-window differences documented as a 5m-versus-1h boundary effect.
- [ ] Move-Odds v0.1.2: compile exact source in TradingView on standard 1h `BINANCE:BTCUSDT.P`; preserve compiler output and compare all 12 vectors.
- [x] Risk-First v0.3.1 title, duplicate source copy, root checksum, and inventory corrected in merged work.
- [x] Risk-First static math review found no obvious arithmetic defect; this is not runtime evidence.
- [ ] Risk-First v0.3.1: compile and test exact source in TradingView; test both sides, inputs, risk cap, stop/target, leverage cap, and alerts.
- [x] Keep Risk-First semantics as a manual checklist, not a direction signal or realised-risk guarantee.

### D. Data, Atlas, and strategy controls

- [x] Preserve rejected experiments and the rule that burned history cannot be renamed into holdout.
- [x] Record Atlas archive/input identity and structural checks; historical reproduction is recorded from the supplied isolated workbench.
- [ ] Compare every v4 path with current main and classify source/archive/generated/obsolete/sensitive content.
- [ ] Complete secrets, personal-data, licensing, and data-rights review.
- [ ] Repeat Atlas from a fresh clean checkout only if exact commands, environment, outputs, and hashes can be preserved.
- [ ] Any future candidate must have a new preregistration, independent data, costs, statistics, stopping rules, code hash, and sample boundaries before outcome inspection.
- [ ] Apply bootstrap/significance, fees, train/test, independent-block walk-forward, trade/candle-path Monte Carlo, and multiple-testing/DSR controls.
- [ ] Measure KCEX fees, spread, slippage, funding, and fills independently, and only after directional evidence passes.

### E. Explicit holds

- [ ] Resolve OPEN-21 outcome-dependent missingness. Synthetic test: with 5% losing outcomes missing, false-PASS rose from 0.050 to 0.177. No fixed allowance is accepted.
- [ ] Resolve OPEN-17, OPEN-18, N-6, and remaining D-LIQ normative decisions.
- [ ] Complete independent D-LIQ review and real-feed/anchor/host qualification.
- [ ] Complete r7 independent review, KAT implementation, and D25 Stage A/B evidence.
- [ ] Obtain TradingView compiler/runtime evidence.
- [ ] Complete licensing/data-rights review before any public release.

## Current holds

- No established profitable or independently validated strategy.
- D-LIQ r3.1 remains draft and unlocked. No collector, T0, market-price scoring, forward directional test, or strategy use is authorized.
- Forward Journal r7 remains SPEC ONLY / NOT LOCKED. No D25 stage is proven.
- No TradingView compilation evidence for Move-Odds v0.1.2 or Risk-First Helper v0.3.1.
- No production external anchor or collector host is verified.
- No authorization to publish the repository or sensitive/private data.

## Completion standard

A task is complete only when its evidence is linked, the exact commit is identified, and required checks pass on that commit. Synthetic tests prove behavior only for their tested fixtures. Independent review, external service qualification, and operational acceptance require their own evidence.
