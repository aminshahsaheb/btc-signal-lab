# Status register — 2026-11-05

## Overall

**Research infrastructure: useful. Trading edge: not established.** The repository is **Public** as of 2026-11-04 (owner-selected). No strategy in this repository is proven profitable or independently validated.

Verified snapshot as of 2026-11-05:
- Current `main`: `37e57307d98591cbcfa769012be3f40445c128bd`.
- Recursive Git tree: 160 entries including directories; 116 file blobs. The full inventory contains 115 file rows and excludes itself.
- Repository visibility is Public by owner decision on 2026-11-04. Public visibility does not resolve licensing, source permissions, or data rights.
- PR #15 (D-LIQ builder), #16 (Forward Journal audit), #17 (status/workflow), and #19 (archive screening) are open Drafts based on older main snapshots; their recorded checks are historical until rerun on current exact heads.
- PR #18 is an open Draft execution-ledger candidate based on this main snapshot; its recorded exact-head checks passed on head `0c4c08244bc94ede1acaf3611b4b706c136f47ed`. PR #21 overlaps and is an older, smaller alternative; do not merge both.
- PR #20 is already merged. PR #22 is an open Draft reconciliation candidate.
- PR #23 is an open Draft for **r3-reconstruction, not r3.1**. Its exact head `25fba639011a95a3128ed406e21864fa529bd8dd` passed the root inventory workflow (#471) and its reconstruction workflow (#4). It remains unmerged and requires independent review.
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
2. `main` still lacks an accepted `slots.csv` builder. Draft PR #15 and reconstruction PR #23 contain candidate code; neither is merged or independently approved.
3. Independently reproduce the original-package four-seed differential run; keep PR #23's synthetic reconstruction results labeled separately.
4. An independent third-party verifier/adversarial review is still required.
5. Real Binance raw-message semantics have not been verified. The fixtures are synthetic.
6. No production external anchor is selected or tested. MockAnchor is insufficient.
7. No collector host or end-to-end run exists.
8. OPEN-17, OPEN-18, OPEN-21, and the entry-candle decision need explicit, dated disposition.

No market data was scored in this review. No live feed, collector, or T0 is active. Do not start them before the blockers close and a separate lock decision is recorded.

## Current repository maintenance queue

Follow the owner-approved merge order only after each branch is based on then-current `main`, stale visibility wording is corrected, inventory is regenerated, exact-head CI passes, and required independent review is complete: **#17 → #18 → #19 → #16 → #15**. If #17 has extensive conflicts, isolate its workflow change. Resolve #21 as superseded only after confirming it has no unique content. Keep #23 Draft until independent review; it is not part of the approved merge sequence for the maintenance PRs.

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