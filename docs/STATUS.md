# Status register — 2026-11-07

> Newest entries first: "Update 2026-11-07", then "Update 2026-11-06". The figures under "Overall" and "Live PR synchronization" are dated snapshots of 2026-11-05 and are **not** the current `main`. The ordered plan is `ROADMAP.md`; this file is the single source of truth for current state.

## Update 2026-11-07 — maintenance merged without independent review; second audit; gates still open

- **Merged by the owner on 2026-11-07 at 13:48Z, merge commit `1336d77`:** PR #30 (documentation architecture: `docs/INDEX.md`, HISTORICAL banners, `ROADMAP.md` as the master checklist, drift guards, CI hardening, the audit record `reviews/2026-11-07-repository-audit.md`) and PR #29 (the 2026-11-06 note below). **Neither had an independent review** (0 reviews on both). CI on that commit succeeded: `verify-source-artifacts` run 42378627637 and `D-LIQ r4-draft synthetic verification` run 42378627650 (read through the GitHub API).
- **Ruleset "Protect Main" is unchanged** when read through the API on 2026-11-07 (required approvals 0, required status checks empty, no bypass actors). It is the same condition that allowed PR #28 and PR #30 to reach `main` unreviewed. Open: D-RULESET-1.
- **PR #15 and PR #23 are no longer Draft.** The owner marked them ready for review on 2026-11-07 (14:00Z and 14:02Z). GitHub reports both as not mergeable (conflicts with `main`). Their code is superseded by `r4-draft`; do not merge either without an independent review and an owner decision.
- **Second GPT audit (2026-11-07, after the merge):** CANDLE provenance (G-1), the `replay_slots=False` default (G-2), the incomplete rebuild pinning (G-3) and the missing independent SLOT replay stay open (see `ROADMAP.md`). It also found defects in the new guards and stale roadmap lines; Claude reproduced each of them. They are fixed in the follow-up pull request `maintenance/guard-fixes-2026-11-07`: `check_docs.py` now parses reference-style and HTML links, `check_mirrors.py` exempts only `research/d-liq/r<number>-draft/`, `check_all.sh` and the r4 workflow no longer ignore a crashing mutation or differential run (they use `scripts/check_dliq_strict.sh`), and `scripts/test_guards.py` makes every guard prove that it fails on known-bad input.
- **2026-11-09 (evening): free format-only dry-run tool drafted** (`research/d-liq/g1-dryrun-draft`, PR to `main` as Draft): stdlib-only, own minimal websocket client, hard caps (<= 20 `forceOrder` and <= 10 `kline_1m` frames), TLS verification always on, writes only a new directory, does nothing without the approval flag; 87 tests against a loopback fake server (the tests and every mutant are blocked from reaching a real host) and 107 deliberate-bug mutants, all killed (version 4). **Real runs by the owner (2026-11-09 22:24Z to 23:12Z, through a VPN): the routed `/market` paths accepted the connections; 18 kline frames (RAW and COMBINED) were all accepted unchanged by the G-1 parser; 8 all-market `forceOrder` frames matched the message contract's grammar (checked with the symbol relabelled in a copy; the real symbols are not BTCUSDT) but carry two extra fields `ps` and `st` inside `o`, while the contract's `st` rule reads the top level (GPT decided on 2026-11-10 to remove that rule; recorded as a working basis in docs PR #38); **on 2026-11-10 (run 9, version 4 watch mode) ONE genuine BTCUSDT `forceOrder` frame was captured: `ps` and `st` sit INSIDE `o` on the single-symbol stream too, which contradicts the assumption behind GPT's 2026-11-10 `st`/`ps` decision (open for GPT; one frame only; not committed);** his laptop clock was about 4.2 s behind the exchange; the VPN path hung up connections after 51-53 s (one after 103 s).** Versions 2 and 3 of the tool added retries and a corrected stop rule; version 4 adds a bounded watch mode (reconnects after every hang-up) to capture the one genuine BTCUSDT `forceOrder` frame GPT requires before any lock. The tests show only that the code follows the protocol as its author understood it. The owner runs it from his own computer through a VPN with an exit outside the USA and sends back `capture.jsonl` and `summary.json`; those must not be committed without an owner decision. It records the endpoint-routing and ping-health concerns as `[VERIFY]` in its README and in ROADMAP 2F. Nothing is self-certified; step 8 stays BLOCKED.
- **2026-11-09: candidate independent SLOT replay** (`research/d-liq/g2-replay-draft`, PR to `main`): a spec-only second implementation of the SLOT replay (188 own tests + 3 supplementary), a differential harness (4 x 4000 synthetic journals vs the r5 verifier and 1 vs r4: 0 disagreements, harness bugs found and fixed on the way) and an automatic mutation check (279 mutants, 245 killed, 34 survivors reviewed by me alone as equivalent/unobservable/immaterial). Not reviewed, not adopted; the builder policy `REQUIRE_INDEPENDENT_REPLAY` is unchanged and nothing becomes `analysis_eligible`. Three of its five specification inputs are not in the repository (owner decision D-SPEC-1). The #33 conflict (inventory CSV) was resolved by regenerating the file.
- **2026-11-08 (later): PR #32 (r5-draft, G-2 and the start of G-3) was merged by the owner into `main` at 18:38Z (merge `f8198a2`), without an independent review. G-1 draft package opened** (`research/d-liq/g1-candle-draft`; PR #34 was stacked on PR #32 and was merged on 2026-11-08 18:40Z into the r5 BRANCH after #32 had already merged into `main`, so the content did not reach `main` and is re-submitted as a new PR to `main`; lesson: no stacked PRs): contract amendment proposal, shared kline parser, reference CANDLE checker with synthetic tests and deliberate-bug checks, and a reproducible demonstration that kline frames recorded as MSG break the current SLOT replay (a `feed` marker per connection is needed; decision for GPT). Nothing is integrated into the verifiers or the builder, the receipt-lag bound `L` has no value, exchange field names are `[VERIFY]` (no real capture), and nothing was independently reviewed. Also opened: PR #33 (Draft), GPT's OPEN-21 / LIQ_INCREMENTAL wording recorded as an unadopted proposal.
- **PR #31 (the guard fixes above) was merged by the owner on 2026-11-08 at 00:38Z, merge commit `c1242c1`, again with no review** (CI green on its head). The ruleset was still unchanged afterwards. A CodeRabbit GitHub App is installed on the repository; on this repository it only posted an invitation to trigger a review (no review was produced) and it is not an independent human review.
- Unchanged: all D-LIQ tests are synthetic; the counts (219 / 102 / 59 / 2 / 17 checks, 15 of 15 mutants killed, four differential seeds with 0 disagreements) are the author's own plus GPT's reading of the raw CI logs, not an independent execution; the verifier written as "independent" shares its model family with the primary one and has no SLOT replay. Step 8 (a real Binance message, a real anchor, a collector host) is BLOCKED. No collector, T0, probe, live feed, scoring or trading action is authorized. No trading edge is established.

## Overall (snapshot of 2026-11-05)

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
## Update 2026-11-06 — D-LIQ r4-draft is on `main`, unreviewed

- PR #28 was merged into `main` as `4a338f4` (owner action, 2026-11-06 07:02 +0330) **before any independent review**. It adds only new files under `research/d-liq/r4-draft/` (53 files, 0 deletions); the `main` tree equals the PR head `ccd76c3`. Nothing outside that directory changed.
- Status of that content: **Draft source. Not r3.1, not a protocol lock, not a lock candidate, not evidence of any trading edge.** All tests are synthetic. The test counts in `docs/reviews/2026-11-05-dliq-r4-increment.md` come from the author's own session and are not independently recounted.
- Still open for r4: independent review (recount, builder-vs-PR #15 diff, hash equality, break attempts); an independent SLOT-replay implementation (GPT P0-3 is PARTIAL); protocol text for OPEN-21 (sensitivity analysis only, not approved) and for the `LIQ_INCREMENTAL` wording (positive conditional estimate under the limited prior-sign control, not a causal or tradable edge); OPEN-17/18/23, the entry-candle decision and the anchor choice.
- BLOCKED (unchanged): real Binance raw-message dry-run (the `forceOrder` endpoint path is unverified), a real external anchor test, a collector host, and an end-to-end run. No "ready for lock" statement may be made before these exist.
- PR #15 (Builder) and PR #23 (r3-reconstruction) remain Draft and now lag `main`; each needs a sync with `main` and an inventory regeneration before any further action. Do not merge either without independent review and an owner decision.
- No collector, T0, probe, live feed, scoring or trading action is authorized.

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

The ordered, tickable plan with evidence and owner decisions is **`ROADMAP.md`** (Gates 0-5). In short: stabilize the repository and its guards; then data provenance and verifier correctness (G-1 to G-4, independent SLOT replay); then close the D-LIQ protocol text; then Forward Journal r7; then a limited real-format Binance test; then, only after explicit protocol lock, any forward test; trading conversion and KCEX economics last and separately.

A task is complete only when its evidence, exact commit, and required checks are recorded.

## Live PR synchronization — 2026-11-05 (HISTORICAL snapshot; superseded by the entries above)

Verified against main `919afab5b9dd43430c6abeb1d39e1ff361d41c4b` (168 tree entries, 124 file blobs; inventory 123 rows, excluding itself):

- PR #24 status/documentation reconciliation and PR #22 recovery reconciliation are merged. PR #17 is closed without merge; its workflow change was preserved in #25 and stale docs were superseded.
- PR #15 is OPEN / DRAFT at `be5eefc4e061d23a0f56d046c7b1fc8efc7bd285`, based on this main. Exact-head run #41993274436 passed 25 Builder tests, inventory regeneration (137 rows), SHA-256 verification, and archive screening. Independent third-party review remains required before merge; replay parity and protocol/operational gates remain open.
- PR #23 is OPEN / DRAFT at `62e40670d76215bfb3b907f30da18cfece96c38f`, based on this main. Exact-head source/inventory run #41992708428 and reconstruction synthetic run #41992708462 passed. It remains explicitly r3-reconstruction, not r3.1, and needs independent review.
- Main push check #41992622485 passed. Public visibility remains an owner decision and does not clear rights review.
- No collector, T0, live anchor, scoring, or trading action is authorized.
