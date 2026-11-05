# BTC Signal Lab — Execution Ledger
Date: 2026-11-04
Initial base: main at da64085fe1c066026a6bee219b600d2b42f280f6
Synchronized main parent: 37e57307d98591cbcfa769012be3f40445c128bd
Branch: ops/execution-ledger-2026-11-04

## Counting model

The controlling checklist supplied on 2026-11-03 has:
- 10 ordered top-level execution steps.
- 7 work sections (A–G): 31 numbered work packages in A–F, plus 10 finalization checklist items in G.
- 253 checkbox lines in total: 11 standing operating rules, 12 completed baseline items, and 230 actionable work items across A–G.
- 12 completed baseline items are tracked separately from the A–G actionable checklist.
- After the 2026-11-04 amendment, sections A–G contain 230 actionable items: 25 complete and 205 open.

A checkbox is counted complete only when its own acceptance condition is met and the evidence is recorded. A partial scan, static inspection, CI on a different SHA, or maintainer self-review does not satisfy an independent-review or runtime-evidence gate.

## Current verified counts

| Section | Packages | Checklist items | Completed | Remaining |
|---|---:|---:|---:|---:|
| Baseline | — | 12 | 12 | 0 |
| A — GitHub and documents | 5 | 34 | 5 | 29 |
| B — TradingView runtime | 2 | 18 | 2 | 16 |
| C — D-LIQ r3.1 | 11 | 90 | 18 | 72 |
| D — Forward Journal r7 | 8 | 50 | 0 | 50 |
| E — Direction research | 3 | 17 | 0 | 17 |
| F — KCEX execution | 2 | 11 | 0 | 11 |
| G — Final evidence/maintenance | 10 tasks | 10 | 0 | 10 |
| **Actionable total** | **31 work packages + 10 G items** | **230** | **25** | **205** |

Note: The 11 standing operating rules are invariants, not tasks to complete. The 10 ordered top-level steps are a sequence, not additional checkbox tasks.

## A1 — PR #17 exact-head review: 3/8 complete

Completed:
1. Read the PR diff and verified that the changed paths are exactly the five declared paths:
   - .github/workflows/verify.yml
   - docs/STATUS.md
   - docs/EXECUTION_PLAN_2026-11-03.md
   - artifacts/SHA256SUMS.txt
   - docs/FILE_INVENTORY_SHA256.csv
2. Reviewed workflow trigger scope and permissions: push is limited to main; pull_request lifecycle events cover feature branches; contents:read is retained; SHA verification command is unchanged.
3. Verified exact head 46ac85c6ceab96c1f5b06a5d13461c914c755c70 and PR workflow run #269 SUCCESS, including the manifest verification step. PR body records that the run was triggered by pull_request and no duplicate push run was created for this feature-branch update.

Still open:
4. Independent human review. The only recorded review is the repository maintainer's own COMMENTED review (review id 5758994951); it is explicitly not independent.
5. Mark PR #17 ready for review, only after independent review.
6. Merge PR #17 without rewriting history.
7. Re-fetch merged main, workflow, STATUS, execution plan, and manifest; verify the merge commit and CI on that exact commit.
8. Run the safe trigger-behavior test after merge and retain evidence.

PR #17 remains OPEN / DRAFT / NOT MERGED. Main remains at da64085fe1c066026a6bee219b600d2b42f280f6.

## A3 — security/privacy/data-rights audit: 2/6 accepted

Completed:
- Baseline main tree at `da64085fe1c066026a6bee219b600d2b42f280f6`: 159 entries, 115 file blobs; path-by-path classification is recorded in `docs/A3_FILE_CLASSIFICATION_2026-11-04.csv`.
- Classification: 55 source files, 51 archives, 9 generated outputs; 0 files classified as obsolete or sensitive. This is a role classification, not proof of redistribution rights.
- Repository filename review and content screening are recorded. PR #19 scanner recursively checks ZIP contents (including nested ZIPs), GZIP streams, text-like files, and raw PDF bytes. It found no private-key markers, common AWS/GitHub/Slack token patterns, quoted credential assignments, email candidates, formatted phone candidates, unsafe ZIP paths, encrypted entries, CRC failures, or invalid ZIP/GZIP files.
- Exact PR CI run #358 SUCCESS on head `68fff2450fdbc69ed3645476664956b275e2ceaf`. Scanner output: 118 files seen; 80,780,825 expanded bytes processed; no findings; no license/notice filenames found. Existing integrity checks also tested 5 ZIP archives, compared 34 historical extracted package files to source ZIPs, and passed the dataset identity/structure check.
- GitHub metadata was rechecked on 2026-11-04 and reports `visibility=public`. This records the current state only; it does not satisfy the private-during-audit condition or grant data-rights clearance.

Still open:
- Exact v4 ZIP bytes are not present in the user's Library ZIP listing or the repository. Only the previously recorded SHA-256 `b82694723aa3b1efbefdfff9df5f77aa15acf7c2bfc50e8b48d372e0beb1db61` is known. A hash alone cannot establish its path list or content, so v4-to-main comparison is blocked.
- Personal-data review is not fully closed. Pattern screening does not detect every identifier or encoding. The PDF received a raw-byte scan only; no OCR or full semantic review was performed.
- Data rights and third-party terms remain unresolved. No root LICENSE or recognizable license/notice file was found, but absence of a notice is not permission to redistribute.
- The current public visibility means the prior private-during-audit condition is not satisfied. Do not change visibility without an owner decision; no public-release or redistribution clearance is implied.
- The report and scanner limitations are recorded in [the A3 report on PR #19](https://github.com/aminshahsaheb/btc-signal-lab/blob/audit/a3-archive-content-review/docs/reviews/2026-11-04-a3-archive-content-screening.md). No public-release clearance is granted.

A3 = 2/6: path classification and pattern-based content screening are complete. The repository is currently public; the private-during-audit condition is not satisfied. v4 comparison, complete semantic personal-data review, and source-specific rights review remain open. No public-release clearance is implied.

## B1/B2 — source identity and SHA-256 registration: 2 checklist lines complete

- B1 item 1 complete: Move-Odds v0.1.2 exact Pine source is `tools/move-odds-panel/v0.1.2/MoveOdds_Panel_v0_1_2.pine`, 16,009 bytes, SHA-256 `d07865ebf10a7f5908aca69a90f792c90af601ef36bb5c4ef76b0ae1c192a84d`. The package SHA manifest and full repository inventory record the same identity.
- B2 item 1 complete: Risk-First Helper v0.3.1 exact Pine source is `tools/riskfirst/RiskFirst_Helper_v0_3_1.pine`, 18,364 bytes, SHA-256 `43e41fcbf8b8590b3267400b0c7f5744473893a67c675a10b291725853480257`. The full repository inventory records this identity.
- These hashes were read from the main-branch SHA-256 records. They identify the source files only. They do not prove TradingView compilation or runtime behavior.

Still open: both TradingView chart setup, compilation, golden-vector/runtime checks, and the remaining chart/configuration validation items.

## C3 — NONE-slot and OUTCOME checkpoint policy: 5/6 complete

Completed:
- The exact candidate archive and protocol hashes were verified; package manifest passed.
- A synthetic journal with anchored `SLOT(status=NONE)` followed by `OUTCOME(status=NO_PRICE)` was tested directly. Writer normal append refused it with `JournalError`; Primary Verifier and active r3.1 Independent Verifier both returned FAIL with hard `OUTCOME_FOR_NONE_SLOT`.
- The preserved `verify_indep_as_delivered.py` baseline returned PASS with no hard finding. This is expected provenance evidence: it is the original delivered version and did not yet contain the r3.1 rule. The active corrected verifier is `verify_indep.py`; do not confuse the preserved baseline with the active verifier.
- Writer/primary suite: 199 checks, 0 failed. Active independent suite: 93 tests, all passed. r3 consistency: 16 checks, 0 failed.
- Differential verification: seed 11 was first checked in this pass with 3,000 random mutations plus 84 hand-built baseline/time checks (3,084 comparisons, 0 disagreements; `OUTCOME_FOR_NONE_SLOT` appeared in 64 mutated journals). A later exact-branch update reran all four seeds independently: 30,084 journals per seed, 120,336 total comparisons, 0 disagreements, as recorded in the current PR #15 body and its exact-head verification record.
- The monolithic `REPRODUCE.sh` invocation still exceeded the execution time limit during its bundled four-seed phase. This timeout is distinct from the later successful per-seed reruns; do not describe the four-seed evidence as unverified.
- The project-level requirement that the OUTCOME itself be covered by a later valid CHECKPOINT remains a stricter Builder acceptance rule, not an amendment to immutable r3.1 A.6.

Still open:
- Item 6 is conditional. No protocol amendment is being made. If the protocol owner later chooses to amend r3.1, it requires a separately versioned protocol, hash, manifest, tests, and owner decision.

Evidence note: [C3 direct verification on PR #15](https://github.com/aminshahsaheb/btc-signal-lab/blob/research/dliq-r3-slots-builder-draft/docs/reviews/2026-11-04-c3-none-slot-verification.md). C3 = 5/6; item 6 is currently N/A. Protocol remains DRAFT / NOT LOCKED.

## C1 — r3.1 package identity and storage: 5/5 complete

- Exact candidate archive `dliq_r3_1_candidate.zip`: 2,455,000 bytes, SHA-256 `4d3faaae13e0263ac1f422a3b6d88904d70057b4bb5271029c1ce5cc9d194ec2`. The bytes were retrieved from the user's private Library and the computed hash matches the value recorded in Issue #4.
- Candidate r3.1 protocol SHA-256: `5c05a15de7addd55cade7617fcdcaea570aad82b61c0b16c95d14024fc649948`.
- Original r3 protocol SHA-256: `449753f9c74bc3d5b41313664f062b50948104906042197f1ed61bacb886df8d`; the original is preserved separately under `protocol/superseded/`. The candidate and original hashes were recomputed and match the manifest.
- Storage decision: retain the binary ZIP in the user's private Library as the controlled archive; do not add a duplicate binary blob to GitHub while data rights remain unresolved. Limitation: collaborators without Library access cannot retrieve it from GitHub alone.
- Candidate protocol, Writer, primary verifier, active independent verifier, preserved as-delivered verifier, tests, and manifest are all retrievable from the exact hash-verified archive. `sha256sum -c MANIFEST.sha256` passed.

Evidence note: [C1 package identity on PR #15](https://github.com/aminshahsaheb/btc-signal-lab/blob/research/dliq-r3-slots-builder-draft/docs/reviews/2026-11-04-c1-package-identity.md). C1 acceptance is complete; this does not lock the protocol.

## C2 — PR #15 Builder review: 8/9 complete

The following eight checklist items are supported by the Builder review and exact PR #15 head `4ee63228e0b9fcfe1330f8dc6e5be94997204db9` (the Builder source/tests remain unchanged from the earlier tested code head):
1. Complete PR diff and Builder/test source reviewed; changed paths enumerated.
2. Builder checks canonical journal JSONL, contiguous sequence, journal-head/event-count binding, verifier report shape, slot-map and missing-grid agreement, hard findings, checkpoint monotonicity/coverage, and output eligibility.
3. Two integration cases are present in `test_actual_verifier_reports.py`; fixture provenance records the exact r3.1 archive, protocol, writer, and both verifier hashes. The fixture uses a local MockAnchor.
4. The anchored OUTCOME integration test expects EVAL.
5. Tests cover pending/unanchored outcome, hard findings, verifier disagreement, NONE-slot, missing grid, bad checkpoint coverage, and malformed report cases.
6. Stale output cleanup is implemented and covered by positive/negative CLI tests.
7. Prior-sign, NO_PRICE, NONE, N_unanch, and missing-prior-candle cases have explicit tests.
8. Exact-head CI run #365 SUCCESS on PR #15 head `4ee63228e0b9fcfe1330f8dc6e5be94997204db9`; it ran all 23 Builder tests, verified inventory regeneration, and passed full SHA-256 manifest verification. Earlier exact Builder-code head run #258 also passed.

Still open:
9. Independent third-party review. The existing maintainer review (id 5759011832) is not independent.

This completes eight checklist lines only. It does not complete the C2 package acceptance gate, merge PR #15, resolve OPEN-17/18/21 or N-6, qualify SLOT replay parity, validate live feed/anchor, authorize LOCK, or authorize a collector/T0.

## Other current gate state (no new completion claimed)

- PR #15: OPEN / DRAFT / NOT MERGED. Exact head `4ee63228e0b9fcfe1330f8dc6e5be94997204db9`; CI run #365 succeeded. C1 = 5/5; C2 = 8/9; C3 = 5/6. Maintainer review id 5759011832 is not independent. OPEN-17/18/21, N-6, SLOT replay parity, external review, real feed, real anchor, and collector qualification remain open.
- PR #19: OPEN / DRAFT / NOT MERGED. A3 screening code and report are on head `68fff2450fdbc69ed3645476664956b275e2ceaf`; CI run #358 SUCCESS. A3 = 3/6, with v4 bytes, semantic privacy review, and data rights still open.
- PR #16: OPEN / DRAFT / NOT MERGED. Exact head 0f450809ee0a2318308e6072cdf952b8c10a4e3a; CI run #235 succeeded. Maintainer review id 5759012211 is not independent. Canonical spec path, four Stage A/B owner decisions, implementation, executable KATs, independent review, and D25 evidence remain open.
- Move-Odds v0.1.2 and Risk-First v0.3.1 source hashes are now recorded in the ledger; TradingView compile/runtime evidence is still not present.
- No Collector, T0, outcome scoring, LOCK, or live trading is authorized by this ledger.

## Next execution order

1. Obtain an independent reviewer for PR #17; do not merge it on self-review alone.
2. Obtain the exact v4 archive bytes, complete the PDF/semantic privacy review, and resolve source-specific data rights. Do not clear public release before these gates close.
3. After PR #17 merge, complete A2 and post-merge checks.
4. Run B1/B2 in TradingView with exact source hashes and preserve runtime evidence.
5. Continue offline C and D work; obtain an independent third-party review for PR #15 and close the remaining protocol-owner decisions. Do not cross any real-feed, Anchor, LOCK, T0, or Collector gate without its own evidence and authorization.

## Evidence references

- PR #17: https://github.com/aminshahsaheb/btc-signal-lab/pull/17
- PR #15: https://github.com/aminshahsaheb/btc-signal-lab/pull/15
- PR #16: https://github.com/aminshahsaheb/btc-signal-lab/pull/16
- PR #19: https://github.com/aminshahsaheb/btc-signal-lab/pull/19
- Master tracker: https://github.com/aminshahsaheb/btc-signal-lab/issues/7


## A3 follow-up — v4 archive and Atlas PDF checks (2026-11-04)

The user approved leaving the public handle `@aminproje` visible in the Atlas PDF.

The exact v4 archive was located on the user's Mac at `/Users/Amin/Downloads/btc-signal-lab-complete-v4.zip`. Its SHA-256 was checked in the user's terminal and matched the expected value `b82694723aa3b1efbefdfff9df5f77aa15acf7c2bfc50e8b48d372e0beb1db61`.

Reported checks: outer ZIP integrity passed (128 entries; 51,823,644 uncompressed bytes); six nested ZIPs were enumerated and extracted without reported listing errors; the BTCUSDT 5-minute GZIP passed `gzip -t`. The dataset inspection reported 602,208 rows, seven expected columns, timestamps from 2021-01-01 00:00 UTC through 2026-09-22 23:55 UTC, and zero duplicates, out-of-order timestamps, gaps over five minutes, invalid numeric/value rows, or OHLC/volume consistency failures.

Atlas PDF text extraction succeeded (17 pages, 791 lines, 3,143 words). The extracted-text pattern scan found only the approved handle `@aminproje`; it found no email address, common API-key/secret/token/password pattern, or local filesystem path. The reported `mdls` metadata grep returned no matching output. This is not full OCR, embedded-object, or exhaustive metadata review.

These user-run checks establish archive integrity and internal dataset structure only. They do not establish source authenticity, data licensing, redistribution rights, or complete semantic/privacy clearance. A3 remains 3/6 pending exact v4-to-repository comparison and source-specific third-party/data redistribution rights. No public-release clearance is implied.

## Historical GitHub verification before Grok amendment (2026-11-04)

- Repository `aminshahsaheb/btc-signal-lab` is currently **public** (`visibility=public`), confirmed by repository metadata. This is not a rights or public-release clearance.
- Main is the base SHA `da64085fe1c066026a6bee219b600d2b42f280f6` for the five open Draft PRs verified in this pass; no PR merge was observed.
- Historical snapshot (superseded): PR #18 was OPEN / DRAFT / NOT MERGED on branch `ops/execution-ledger-2026-11-04`, exact head `736bb56c623ba1ab55808cbd6eb3d628a933f8b4`; pull-request workflow run #380 completed SUCCESS on that exact head.
- PR #15 remains OPEN / DRAFT at `4ee63228e0b9fcfe1330f8dc6e5be94997204db9`; PR #16 at `0f450809ee0a2318308e6072cdf952b8c10a4e3a`; PR #17 at `46ac85c6ceab96c1f5b06a5d13461c914c755c70`; PR #19 at `68fff2450fdbc69ed3645476664956b275e2ceaf`. All remain unmerged. Their review and release gates remain open as documented above.
- The earlier ledger snapshot naming PR #18 head `1044fa...` and runs #377/#376 is stale and is superseded by this readback.
- No PR was merged, no repository visibility change was made in this pass, and no LOCK, T0, Collector, scoring, or live trading is authorized.


## Amendment — Grok review additions (2026-11-04)

Five open checklist items are added to existing sections. These are additions, not completion evidence:

- **B (+2):** preserve raw TradingView compile/runtime evidence for Move-Odds v0.1.2 and Risk-First v0.3.1, including source SHA, chart/symbol/timeframe, settings, and test context; separately execute and record all 12 Move-Odds golden vectors with expected-versus-observed values.
- **C (+1):** run a bounded D-LIQ dry-run of no more than 20 messages for format and data-quality checks only. Do not attach prices, score outcomes, or perform outcome analysis. This remains subject to protocol prerequisites and does not authorize an Anchor, Collector, T0, LOCK, or live feed.
- **G (+2):** record whether the parallel utility track is a personal-use tool or a public product; define utility acceptance criteria separately from strategy profitability (for example alert integrity/timeliness, journal completeness, and risk-check workflow). Do not expand implementation scope before the owner decision.

Updated count arithmetic:
- A: 34 items, 5 complete, 29 open.
- B: 18 items, 2 complete, 16 open.
- C: 90 items, 18 complete, 72 open.
- D: 50 items, 0 complete, 50 open.
- E: 17 items, 0 complete, 17 open.
- F: 11 items, 0 complete, 11 open.
- G: 10 items, 0 complete, 10 open.
- **A–G: 230 actionable items = 25 complete + 205 open.**
- **Including the 12 completed baseline items: 242 checklist items = 37 complete + 205 open.**
- The 11 standing operating rules remain invariants, not tasks. Including them, the document contains 253 checkbox lines.


## Amendment verification checkpoint (2026-11-04)

- The five Grok-derived checklist additions and visibility/count corrections were committed to PR #18.
- Candidate head `0b704bb4f4c6e3680d08d67048add1e903dc7c09` passed workflow run **#398** (`verify-source-artifacts`, push event, SUCCESS).
- The run completed both required steps: inventory regeneration produced no diff, and SHA-256 manifest verification passed.
- This is the pre-final-ledger-refresh verification checkpoint. The final head and its exact-head CI result are recorded in the live PR #18 body; do not substitute this checkpoint SHA for the final head.


## 2026-11-04 GitHub recheck — superseding status record

This section supersedes older status statements above where they conflict with the live GitHub state. It does not rewrite historical evidence or mark research tasks complete.

### Main and repository state
- Repository visibility: **PUBLIC** (GitHub repository metadata checked 2026-11-04). Public visibility is not a reuse license, redistribution approval, or release clearance.
- Current `main`: `37e57307d98591cbcfa769012be3f40445c128bd` (commit message: `docs: correct public visibility and safeguards`). It is a child of the former main `da64085fe1c066026a6bee219b600d2b42f280f6`.
- Exact-main GitHub Actions run **#392** completed **SUCCESS** on `37e5730...` (push event). This verifies the workflow checks on that SHA only.
- Main's visibility correction updates `docs/PUBLISHING.md`, `docs/STATUS.md`, and adds `docs/VISIBILITY_CORRECTION_2026-11-04.md`; it does not resolve data rights or research gates.

### Pull request reconciliation
- PR #15: OPEN / DRAFT / NOT MERGED; head `4faa7393f4293417b7d4e1bd8e334a57bb088334`; base remains old main `da64085...`. No workflow run was found for this exact head. The previous run #365 belongs to the older head `4ee63228e0b9fcfe1330f8dc6e5be94997204db9` and must not be attributed to `4faa739...`.
- PR #16: OPEN / DRAFT / NOT MERGED; head `0f450809ee0a2318308e6072cdf952b8c10a4e3a`; base `da64085...`. Its prior CI evidence remains scoped to its recorded head only.
- PR #17: OPEN / DRAFT / NOT MERGED; head `46ac85c6ceab96c1f5b06a5d13461c914c755c70`; base `da64085...`. Exact-head run #269 was successful; independent review and merge/post-merge gates remain open.
- Historical checkpoint (superseded): PR #18 was OPEN / DRAFT / NOT MERGED at head `cf2d6ba419437a29251586d7338cbc4fd67ba2f7`, based on `da64085...`; exact-head run #400 succeeded. The branch was later advanced through the documented inventory corrections and synchronized with current main.
- PR #19: OPEN / DRAFT / NOT MERGED; head `68fff2450fdbc69ed3645476664956b275e2ceaf`; base `da64085...`. Exact-head run #358 succeeded; A3 limitations and data-rights gates remain open.
- PR #21: OPEN / READY FOR REVIEW / NOT MERGED; head `736bb56c623ba1ab55808cbd6eb3d628a933f8b4`; base is current main `37e5730...`. Compare reports 28 commits ahead and 1 behind, with merge base `da64085...`. Exact-head run #393 succeeded on a push event. Its five changed paths are the same five paths changed by PR #18, but its ledger still has the earlier 225-item / 8-item-G accounting and its PR body is still the empty template. PR #18 has the later reconciled 230-item / 10-item-G accounting and is the preferred current ledger candidate. Do not merge both parallel documentation branches. Resolve PR #21 as superseded by PR #18, or explicitly reconcile its unique content before any merge.
- PRs #15–#17 and #19 still target the previous main SHA. PR #18 has since been synchronized with current main `37e57307d98591cbcfa769012be3f40445c128bd` through merge commit `bd52cbcfa108c27795219066785c209d68ec6416`. Historical checks for the other PRs do not establish that they are current with main; update/rebase and resolve overlapping workflow/documentation changes before merge.

### PR #15 Builder source review — additional open gaps
- Reviewed the current Builder and its synthetic unit tests at PR #15 head `4faa739...`. The current code builds the grid from the first and last observed SLOT. It cannot detect expected leading or trailing slots outside that observed range. The collection-window / boundary policy must be explicit before this is accepted.
- No Builder test explicitly exercises `SLOT_MISMATCH`. The independent verifier does not implement the optional SLOT replay layer, and the 120,336-comparison four-seed differential evidence does not cover `SLOT_MISMATCH`. Primary-verifier replay tests are not independent replay parity.
- `first_candles()` keeps the first CANDLE for each open time. It does not itself compare duplicate CANDLE values. The builder depends on verifier findings such as `CANDLE_CONFLICT`; add a direct negative test for conflicting duplicates and confirm both verifier reports propagate the hard finding.
- The builder validates report shape, journal head, event count, slot map agreement, and missing-grid agreement. It does not execute the verifier binaries itself or cryptographically prove that supplied reports came from the expected immutable verifier builds. Report provenance remains an integration/review gate.
- The existing tests cover the strict later-CHECKPOINT OUTCOME rule, but they are synthetic or fixture-based. They do not replace independent third-party review, real anchor qualification, or live-feed evidence.
- Exact-head CI on `4faa739...` remains unverified. Keep PR #15 DRAFT. Do not mark C2 complete or merge it until the exact head passes CI, independent replay/edge cases are resolved or formally scoped, and an independent third-party reviewer signs off.

### Tracking and non-authorization
- Issue #7's existing body is stale: it still describes the repository as private and main as `da64085...`. A superseding comment must record current main `37e5730...`, public visibility, and the PR reconciliation above.
- Checklist counts remain **230 actionable / 25 complete / 205 open**, plus 12 completed baseline items tracked separately. No checklist completion is claimed by this recheck.
- D-LIQ r3.1 remains DRAFT / NOT LOCKED. Forward Journal r7 remains DRAFT / NOT LOCKED / SPEC ONLY. No collector, T0, live feed, outcome scoring, directional test, or live trading is authorized. No strategy is proven profitable or independently validated.


### CI correction record — run #402

- Run #402 executed on commit `8a061bb8cb206235880ba9fe42b9706656598c5e` and failed at **Verify inventory regeneration is clean**. The SHA-256 value entered for the updated execution ledger did not match the repository generator's measured value.
- The failure occurred before `Verify SHA-256 manifests`; that step was skipped. It is an inventory mismatch, not a Builder test result and not evidence of a research failure.
- The mismatch is being corrected from the repository's own generator output. The next exact-head run must pass both inventory regeneration and full SHA-256 manifest verification before this documentation update is accepted.


### Final exact-head verification — 2026-11-04

- Candidate head before this ledger addendum: `8165801941adc8d1047c91c92650628197315c13`.
- Exact-head GitHub Actions run **#405** completed **SUCCESS** on that SHA.
- Both required checks passed: `Verify inventory regeneration is clean` and `Verify SHA-256 manifests`.
- This supersedes the earlier pending status for head `8165801...`. The ledger addendum itself changes the ledger bytes, so the resulting commit must receive a new inventory refresh and a separate exact-head CI run before this final record is considered fully verified.
- This was a documentation/integrity check. It did not run TradingView, D-LIQ market analysis, a live collector, an external anchor, T0, or a strategy profitability test.


## Exact-head verification after main synchronization

- Synchronization merge commit: `bd52cbcfa108c27795219066785c209d68ec6416`.
- Parent 1 preserves the prior PR history at `2352d0d5a717de959f10315d14d1a2ea1434f795`; parent 2 incorporates current main `37e57307d98591cbcfa769012be3f40445c128bd`.
- The branch now compares to main as **43 commits ahead / 0 behind**. The merge base is the current main SHA above.
- Exact-head GitHub Actions run **#408** (push) completed **SUCCESS** on `bd52cbcfa108c27795219066785c209d68ec6416`.
- Exact-head GitHub Actions run **#409** (pull_request) also completed **SUCCESS** on the same SHA.
- Both runs passed `Verify inventory regeneration is clean` and `Verify SHA-256 manifests`.
- These checks cover documentation inventory and source-manifest integrity only. They do not run Builder tests, TradingView, D-LIQ market analysis, live collection, external anchoring, T0, or profitability tests.
- PR #18 remains OPEN / DRAFT / NOT MERGED. PR #21 still overlaps on the same five changed paths. Do not merge both. No checklist item is completed by this synchronization.


## Historical checkpoint — PR #18 state after inventory correction 1 — 2026-11-04

- Current PR head: `94173f3a07b3ef1f8a411b93a132010f20be0256`; base main: `37e57307d98591cbcfa769012be3f40445c128bd`.
- Compare state at this checkpoint: **45 commits ahead / 0 behind**. The merge base is current main.
- Exact-head GitHub Actions run **#412** (push) and run **#413** (pull_request) both completed **SUCCESS** on `94173f3a07b3ef1f8a411b93a132010f20be0256`.
- Both runs passed `Verify inventory regeneration is clean` and `Verify SHA-256 manifests`.
- Runs #410 and #411 failed on the preceding ledger-only head because the ledger SHA-256 inventory row had not yet been refreshed. The CI log supplied the exact measured size and digest; the inventory was corrected, and #412/#413 then passed. Preserve this correction history.
- PR #18 remains OPEN / DRAFT / NOT MERGED. It is synchronized with main, but PR #21 still overlaps on the same five paths. Do not merge both. Independent review and merge approval remain separate gates.
- No checklist item was completed by this synchronization or inventory correction.


## Latest branch state after ledger-history reconciliation — 2026-11-04

- Current PR #18 head at this checkpoint: `241a79918f161959d2d9c04c589844a4a90f8298`; base main: `37e57307d98591cbcfa769012be3f40445c128bd`.
- Compare state: **47 commits ahead / 0 behind**. The merge base is current main.
- Exact-head GitHub Actions run **#416** (push) and run **#417** (pull_request) both completed **SUCCESS** on `241a79918f161959d2d9c04c589844a4a90f8298`.
- Both runs passed `Verify inventory regeneration is clean` and `Verify SHA-256 manifests`.
- Runs #414 and #415 failed on the preceding ledger-update head because the inventory digest had not yet been refreshed. The CI log supplied the exact measured ledger size and SHA-256; the inventory was corrected, and #416/#417 then passed.
- PR #18 remains OPEN / DRAFT / NOT MERGED. It is synchronized with main. PR #21 still overlaps on the same five changed paths; do not merge both. Independent review and merge approval remain separate gates.
- Checklist accounting remains 230 actionable / 25 complete / 205 open, plus 12 completed baseline items. No checklist item was completed by these documentation corrections.


## Current reconciliation after PR #25 — 2026-11-05

- Main is now `e66eb9945653db17e003b55d116f390cc61b2528`. PR #25 merged the workflow-only change extracted from conflict-heavy PR #17. The repository is Public by owner choice.
- PR #17 itself remains OPEN / DRAFT / NOT MERGED. Its stale documentation and inventory changes were not merged; PR #24 is the separate documentation reconciliation candidate.
- Owner's ordered sequence is #17 (workflow-only replacement #25), #18, #19, #16, then #15. Before each merge, sync the current main parent, correct any stale visibility claims, refresh the full inventory, and require exact-head CI.
- This PR #18 branch is being synced to the new main and will receive fresh exact-head CI. PR #19 and #16 were synced to the prior main `37e5730...`; they must be synced again after this merge and rechecked in sequence.
- PR #15 is now at `0670acc4eb36f95606ee1b6413477e4e4872937d`; exact-head checks #41941410425/#41941416236 and 25 Builder/verifier-fixture tests pass. Verifier reports are recomputed with SHA-pinned implementations and compared to supplied reports. PR #15 remains DRAFT pending independent review; replay parity, boundary policy, and live-evidence gates remain open.
- PR #23 is an unlocked `r3-reconstruction`, not r3.1. PR #24 is the status/roadmap reconciliation draft. No r4 delivery, live anchor, collector, T0, or outcome scoring is claimed.
- Public visibility is current state, not rights clearance. The prior private-during-audit condition is unavailable while the repository is Public; v4 comparison, full semantic/privacy review, and source-specific rights review remain open.


## Current maintenance sequence status — 2026-11-05

- Current main: `f6763e66910c67134b927ac5afe4b37666193a75`; recursive tree 167 entries, 123 file blobs, 122 inventory rows; tree not truncated.
- Owner sequence completed through #16: PR #25 (workflow-only replacement extracted from #17) merged as `e66eb9945653db17e003b55d116f390cc61b2528`; PR #18 as `46ab8d274ca0f1be0a7a0a39aa7cf523ea85c3c1`; PR #19 as `58a844216e4b70cd5f0b2143884914dd69c028a9`; PR #16 as `098309e3ad5baee14efc8696faffb110cf1990c4`. Each had current-main sync, corrected visibility wording where applicable, regenerated inventory, and exact-head CI success.
- PR #21's unique inventory-regeneration workflow guard was preserved in PR #26, merged as `f6763e66910c67134b927ac5afe4b37666193a75` after exact-head CI. PR #21 was then closed as superseded. Original PR #17 remains open/draft; only its isolated workflow change was used.
- PR #15 is OPEN / DRAFT at `0670acc4eb36f95606ee1b6413477e4e4872937d`. Exact-head checks #41941410425 and #41941416236 succeeded, with 25 Builder/verifier-fixture tests. The Builder recomputes primary and independent reports through SHA-pinned verifier sources against a separate anchor snapshot, then compares canonical report content. Matching forged reports with the same journal head and event count are rejected.
- PR #15 remains unmerged pending independent third-party review. SLOT replay parity, grid-boundary policy, real external anchor/feed, collector, T0, protocol lock, and outcome scoring remain open or unauthorized. PR #23 remains synthetic `r3-reconstruction`, not r3.1.
