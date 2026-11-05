# Status register — 2026-11-05

## Overall

**Research infrastructure: useful. Trading edge: not established.** The repository is **Public** as of 2026-11-04 (owner-selected). No strategy in this repository is proven profitable or independently validated.

Verified snapshot as of 2026-11-05:
- Current `main`: `f6763e66910c67134b927ac5afe4b37666193a75`.
- Recursive Git tree: 167 entries including directories; 123 file blobs. The full inventory contains 122 file rows and excludes itself; the tree response was not truncated.
- Repository visibility is Public by owner decision on 2026-11-04. Public visibility does not resolve licensing, source permissions, or data rights.
- PR #25 merged the workflow-only change extracted from conflict-heavy PR #17 (merge `e66eb9945653db17e003b55d116f390cc61b2528`). The original PR #17 remains OPEN / DRAFT; its stale docs were not merged.
- PR #18 merged the current execution ledger (merge `46ab8d274ca0f1be0a7a0a39aa7cf523ea85c3c1`); PR #19 merged the archive-screening update (merge `58a844216e4b70cd5f0b2143884914dd69c028a9`); PR #16 merged the Forward Journal audit (merge `098309e3ad5baee14efc8696faffb110cf1990c4`). Each was synchronized with then-current main, inventory refreshed, and exact-head CI passed.
- PR #26 restored the unique inventory-regeneration guard found in overlapping PR #21; it merged as `f6763e66910c67134b927ac5afe4b37666193a75` after exact-head CI passed. PR #21 is closed as superseded; no unique change remains unapplied.
- PR #15 is OPEN / DRAFT at `656cbe5a4804e9a3faffeb3df9e399a8210dfd06`, synchronized with current main. Exact-head Actions run #41944735094 passed: 25 Builder/verifier-fixture tests, inventory regeneration, SHA-256 verification, and archive screening. Its branch inventory has 136 file rows. The Builder targets the supplied r3.1 candidate; independent review remains required, so it is not accepted or merged.
- PR #22 is an open Draft recovery reconciliation; PR #23 is an open Draft `r3-reconstruction`, not r3.1; PR #24 is this current-status reconciliation draft. PR #20 is already merged.
- A3 remains 2/6: path classification and pattern-based screening are complete. Public visibility does not meet the private-during-audit condition or imply rights clearance. v4 comparison, full semantic/privacy review, and source-specific rights review remain open.
- These PR states are a snapshot; check current GitHub heads and checks before acting.
## Component status

| Component | Current status | Allowed next action | Not allowed |
|---|---|---|---|
| Move-Odds Panel v0.1.2 | Source and static verification artifacts are present. TradingView compilation is not verified. | Compile the exact source on a standard 1h `BINANCE:BTCUSDT.P` chart; compare all 12 golden vectors; save raw evidence. | Claim compiler/runtime success, direction, or profitability without evidence. |
| Risk-First Helper v0.3.1 | Table label and inventory are corrected. It remains a manual checklist. TradingView compilation/runtime is not verified. | Compile and test the exact `pine/risk-first/RiskFirst_Helper_v0_3_1.pine` source separately. | Treat PASS as a direction signal, automatic risk control, or proof of realised risk. |
| D-LIQ r3 | **DRAFT / NOT LOCKED.** Package review is recorded in Issues #4 and #5. | Resolve statistical and operational blockers; make a new immutable candidate and separate lock decision only after all gates pass. | Collector, T0, price/outcome scoring, forward directional test, or strategy use. |
| D-LIQ r2 | Superseded historical draft. PR #3 is closed without merge. | Preserve its source and tests as history. | Treat r2 as the current protocol. |
| Forward Journal r7 | **DRAFT / NOT LOCKED / SPEC ONLY.** Issue #8 tracks the lock audit. D25 is not satisfied. | Verify KAT provenance, run available tests, map gates, and complete an independent review. | Treat r7 as a locked dependency or start T0. |
| Atlas v1 | Historical package and exact input are preserved. Structural checks and a prior isolated historical reproduction are recorded. | Keep its output as an audit artifact; repeat clean-run reproduction only with exact commands and hashes. | Reclassify used historical data as a virgin holdout or claim a new edge. |
| Strategy research | No active, independently validated candidate. Prior rejected families remain closed under the research rules. | Any new candidate needs a new preregistration and independent data. | Parameter rescue, retuning on burned data, or claims based on synthetic fixtures. |
| KCEX execution | Not started. | Separate measurement of fees, spread, slippage, funding, and fills only after directional evidence passes. | Infer KCEX profitability from Binance reference returns. |

## D-LIQ r3 — open blockers

The original r3 package audit is recorded in Issues #4 and #5. The supplied candidate archive is distinct from r3; PR #23 is explicitly an unlocked r3 reconstruction, not r3.1. Its four-seed synthetic differential suite passed on its recorded PR head, but that does not complete an independent four-seed reproduction of the original r3 package or establish r3.1 equivalence.

Blocking items:
1. Synthetic S10 shows an outcome-dependent missingness failure: false-PASS rose from 0.050 to 0.177 when 5% of losing outcomes were missing. The proposed OPEN-21 allowance was not adopted.
2. `main` still lacks an accepted `slots.csv` builder. PR #15 and PR #23 contain candidates; PR #15 remains Draft pending independent review, and PR #23 is an unlocked reconstruction rather than r3.1.
3. Independently reproduce the original-package four-seed differential run; keep PR #23's synthetic reconstruction results labeled separately.
4. An independent third-party verifier/adversarial review is still required.
5. Real Binance raw-message semantics have not been verified. The fixtures are synthetic.
6. No production external anchor is selected or tested. MockAnchor is insufficient.
7. No collector host or end-to-end run exists.
8. OPEN-17, OPEN-18, OPEN-21, and the entry-candle decision need explicit, dated disposition.

No market data was scored in this review. No live feed, collector, or T0 is active. Do not start them before the blockers close and a separate lock decision is recorded.

## Current repository maintenance queue

The owner-approved maintenance sequence has been completed through its first four items: PR #25 carried the workflow-only part of conflict-heavy #17, followed by #18, #19, and #16. Original PR #17 remains OPEN / DRAFT with stale documentation; PR #24 is the current status reconciliation. PR #15 is the final item and remains Draft until independent review and its remaining replay/boundary gates are resolved. PR #21 was superseded after its unique inventory CI guard moved to merged PR #26. Keep PR #23 Draft; it is r3-reconstruction, not r3.1.

## Forward Journal r7 — open blockers

- D25 is not satisfied: no real external anchoring target has been selected and independently verified, and the two-namespace end-to-end exercise is incomplete.
- The supplied D-LIQ package contains the r7 specification but no separate r7 KAT harness/run report.
- D1-D24 are gates in the specification, not proof that those gates passed.
- No live connection or T0 exists.

Keep r7 unlocked. See Issue #8.

## Data and integrity limits

- The BTCUSDT 5-minute dataset has 602,208 rows and ends on 2026-09-22. It is historical discovery/confirmation data and is burned for new holdout claims.
- The dataset's recorded compressed/decompressed hashes and structural checks establish file identity and structure only. They do not prove an independent market-data source or a trading edge.
- The v4 ZIP is internally consistent, but its embedded upload/sync notes describe an older 27-file state. It is not a current mirror of `main`.
- Repository visibility is **Public** as of 2026-11-04. Public visibility does not grant a reuse license or resolve data rights. Do not add credentials, private account details, raw conversation exports, or unreviewed live capture.

## Current order of work

1. Reconcile repository visibility documentation and regenerate both SHA-256 manifests on a branch from current `main`; require exact-head CI.
2. Review/close the stale PR #1 and PR #2 only after their content has a current replacement or an explicit superseding decision.
3. Complete static, local Move-Odds and Risk-First checks. Then obtain actual TradingView compile and golden-vector evidence.
4. Resolve D-LIQ r3 missingness, builder, differential, independent-review, real-feed, anchor, and host gates.
5. Complete the Forward Journal r7 KAT and D25 review. Do not lock by default.
6. Only after explicit protocol lock, consider a bounded format-quality probe. No price/outcome analysis in that probe.
7. Only after all directional gates pass, preregister strategy execution and measure KCEX economics separately.

A task is complete only when its evidence, exact commit, and required checks are recorded.

## Live PR synchronization — 2026-11-05

Verified against main `919afab5b9dd43430c6abeb1d39e1ff361d41c4b` (168 tree entries, 124 file blobs; inventory 123 rows, excluding itself):

- PR #24 status/documentation reconciliation and PR #22 recovery reconciliation are merged. PR #17 is closed without merge; its workflow change was preserved in #25 and stale docs were superseded.
- PR #15 is OPEN / DRAFT at `be5eefc4e061d23a0f56d046c7b1fc8efc7bd285`, based on this main. Exact-head run #41993274436 passed 25 Builder tests, inventory regeneration (137 rows), SHA-256 verification, and archive screening. Independent third-party review remains required before merge; replay parity and protocol/operational gates remain open.
- PR #23 is OPEN / DRAFT at `62e40670d76215bfb3b907f30da18cfece96c38f`, based on this main. Exact-head source/inventory run #41992708428 and reconstruction synthetic run #41992708462 passed. It remains explicitly r3-reconstruction, not r3.1, and needs independent review.
- Main push check #41992622485 passed. Public visibility remains an owner decision and does not clear rights review.
- No collector, T0, live anchor, scoring, or trading action is authorized.
