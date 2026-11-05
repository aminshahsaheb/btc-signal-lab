# BTC Signal Lab — repository-wide execution plan

Audit date: 2026-11-05  
Current verified `main` baseline: `f6763e66910c67134b927ac5afe4b37666193a75`  
Repository: **Public** (owner-selected; checked 2026-11-04)

## Operating rules

- Work in isolated branches. Never force-push.
- A missing CI result is unknown, not success.
- Mark a task complete only with evidence, exact commit SHA, and required checks on that commit.
- Keep historical failures and rejected hypotheses.
- Do not claim an edge or profitability without independent out-of-sample and forward evidence.
- Do not publish credentials, tokens, private account data, raw private conversations, or restricted data.
- Repository is Public by owner decision on 2026-11-04. This does not grant a license or close data-rights and licensing review.

## Verified baseline

- Current baseline: `f6763e66910c67134b927ac5afe4b37666193a75` (2026-11-05).
- Recursive Git tree: 167 entries, 123 file blobs; response not truncated.
- Full file inventory: 122 rows; it excludes itself.
- PR #9: exact inventory fix; run #66 passed on head `db1c03ca6780f0a1cfc638aa0b968a7f92bb091d`; merge `0ae8a0cd9af36d681a88fbd4849303bd7039210a`.
- PR #11: docs reconciliation; runs #85/#86 passed on exact head `09bad9e582b1962c1f3c35d8fe54422a3cad0c84`; merge `69e716ff4ca4a5cd71b63f4107a746371af08706`.
- PR #12: duplicate Pine source copies and manifests synchronized; runs #98/#99 passed on exact head `8571a4fffdb6058c82a2ae5df4b0caa5f94db67c`; merge `6379cfd1233a16d29787624ef773d295a5b4c265`.
- PR #1/#2: closed without merge; changes reconciled or preserved by PR #11.
- PR #3: closed without merge as superseded D-LIQ r2; retain history.
- PR #10: closed without merge after temporary hash audit.
- D-LIQ r3 review is recorded in Issues #4/#5; it remains unlocked.
- Forward Journal r7 remains unlocked; D25 is not satisfied.
- v4 ZIP is internally consistent but is not a current mirror of main.

## Current PR queue (verified 2026-11-05)

- #17, #16, and #19 have stale bases; historical successful checks do not qualify as current-head checks.
- #18 is the current ledger candidate; #21 overlaps and appears older. Compare unique content before superseding #21.
- #22 is a Draft reconciliation document that needs refresh against this status.
- #23 is a Draft r3 reconstruction, explicitly not r3.1; it passed its recorded synthetic CI but still needs independent review.
- Ordered maintenance work completed through the first four items: PR #25 carried the workflow-only portion of conflict-heavy #17, followed by #18, #19, and #16. Original PR #17 remains open/draft; PR #15 is the final item and stays Draft pending independent review. PR #21 was superseded after its unique inventory guard was preserved in PR #26. #20 is already merged.

## Ordered checklist

### A. Baseline and source reconciliation
- [x] Re-fetch main head, recursive tree, PRs, issues, and workflow evidence after PR #12.
- [x] Confirm main is Public by owner decision (2026-11-04); tree has 116 file blobs and inventory has 115 rows. This does not resolve data rights or licensing.
- [x] Reconcile README, STATUS, ROADMAP, remote-sync and execution plan in PR #11; exact-head CI passed.
- [x] Synchronize duplicate Pine source copies and regenerate manifests in PR #12; exact-head CI passed.
- [ ] Compare every v4 path with the current remote tree and record path classes.
- [ ] Review archives for secrets, personal data, raw conversation exports, and data-use rights.
- [x] Owner changed repository visibility to Public on 2026-11-04; data-rights and license review remain open.

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
- [ ] Move-Odds v0.1.2: compile in TradingView on a standard 1h `BINANCE:BTCUSDT.P` chart; compare all 12 rendered vectors; preserve raw evidence.
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
- [ ] Independently review the candidate builders in PR #15 and the explicitly labeled r3-reconstruction in PR #23; do not treat either as accepted r3.1 implementation until the applicable protocol and independent review gates pass.
- [ ] Complete an independent four-seed reproduction of the original r3 package in a clean environment. Keep PR #23's completed synthetic reconstruction seeds as separate evidence.
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
- [ ] Apply bootstrap/significance, fees, train/test, independent-block walk-forward, trade/candle-path Monte Carlo, and multiple-testing/DSR controls.
- [ ] If direction passes, create a separate strategy preregistration.
- [ ] Measure KCEX fees, spread, slippage, funding, and fills independently.



## Current maintenance PR results — 2026-11-05

Main is `f6763e66910c67134b927ac5afe4b37666193a75`; its recursive tree has 167 entries, 123 file blobs, and 122 inventory rows. Exact-head PR CI passed before the merges: #25 run #41938187349, #18 #41942204471, #19 #41942554982, #16 #41942791983, and #26 #41943313931. The main push check #41943405649 also passed on this exact main SHA. PR #15 remains the final ordered item, Draft at `656cbe5a4804e9a3faffeb3df9e399a8210dfd06`, synchronized with current main. Exact-head run #41944735094 passed 25 Builder/verifier-fixture tests, inventory regeneration, SHA-256 verification, and archive screening. Independent third-party review is still outstanding. PR #17's conflicting docs were not merged. PR #21 was closed after its workflow guard was preserved and merged in #26.

## Current holds

- No established profitable or independently validated strategy.
- No D-LIQ r3 lock, collector, T0, or forward directional test.
- No TradingView compilation evidence for Move-Odds v0.1.2 or Risk-First Helper v0.3.1.
- No production anchor or collector host verified for D-LIQ r3.
- Forward Journal r7 remains unlocked.
- Repository visibility is Public by owner choice; source licensing, data rights, and archive review remain open. Do not publish sensitive/private data.

## Completion standard

A task is complete only when evidence is linked, the exact commit is identified, and required checks pass on that commit. Synthetic tests prove behavior only for their tested fixtures.

## Live PR synchronization — 2026-11-05

Verified against main `919afab5b9dd43430c6abeb1d39e1ff361d41c4b` (168 tree entries, 124 file blobs; inventory 123 rows, excluding itself):

- PR #24 status/documentation reconciliation and PR #22 recovery reconciliation are merged. PR #17 is closed without merge; its workflow change was preserved in #25 and stale docs were superseded.
- PR #15 is OPEN / DRAFT at `be5eefc4e061d23a0f56d046c7b1fc8efc7bd285`, based on this main. Exact-head run #41993274436 passed 25 Builder tests, inventory regeneration (137 rows), SHA-256 verification, and archive screening. Independent third-party review remains required before merge; replay parity and protocol/operational gates remain open.
- PR #23 is OPEN / DRAFT at `62e40670d76215bfb3b907f30da18cfece96c38f`, based on this main. Exact-head source/inventory run #41992708428 and reconstruction synthetic run #41992708462 passed. It remains explicitly r3-reconstruction, not r3.1, and needs independent review.
- Main push check #41992622485 passed. Public visibility remains an owner decision and does not clear rights review.
- No collector, T0, live anchor, scoring, or trading action is authorized.
