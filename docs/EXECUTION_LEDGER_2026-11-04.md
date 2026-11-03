# BTC Signal Lab — Execution Ledger
Date: 2026-11-04
Base: main at da64085fe1c066026a6bee219b600d2b42f280f6
Branch: ops/execution-ledger-2026-11-04

## Counting model

The controlling checklist supplied on 2026-11-03 has:
- 10 ordered top-level execution steps.
- 7 work sections (A–G): 31 numbered work packages in A–F, plus 8 finalization checklist items in G.
- 248 checkbox lines in total: 11 standing operating rules, 12 completed baseline items, and 225 actionable work items across A–G.
- 12 actionable items were already checked in the baseline section.
- 225 actionable work items were open in sections A–G at the start of this execution pass.

A checkbox is counted complete only when its own acceptance condition is met and the evidence is recorded. A partial scan, static inspection, CI on a different SHA, or maintainer self-review does not satisfy an independent-review or runtime-evidence gate.

## Current verified counts

| Section | Packages | Checklist items | Completed | Remaining |
|---|---:|---:|---:|---:|
| Baseline | — | 12 | 12 | 0 |
| A — GitHub and documents | 5 | 34 | 6 | 28 |
| B — TradingView runtime | 2 | 16 | 2 | 14 |
| C — D-LIQ r3.1 | 11 | 89 | 18 | 71 |
| D — Forward Journal r7 | 8 | 50 | 0 | 50 |
| E — Direction research | 3 | 17 | 0 | 17 |
| F — KCEX execution | 2 | 11 | 0 | 11 |
| G — Final evidence/maintenance | 8 tasks | 8 | 0 | 8 |
| **Actionable total** | **31 work packages + 8 G items** | **237** | **38** | **199** |

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

## A3 — security/privacy/data-rights audit: 3/6 accepted

Completed:
- Baseline main tree at `da64085fe1c066026a6bee219b600d2b42f280f6`: 159 entries, 115 file blobs; path-by-path classification is recorded in `docs/A3_FILE_CLASSIFICATION_2026-11-04.csv`.
- Classification: 55 source files, 51 archives, 9 generated outputs; 0 files classified as obsolete or sensitive. This is a role classification, not proof of redistribution rights.
- Repository filename review and content screening are recorded. PR #19 scanner recursively checks ZIP contents (including nested ZIPs), GZIP streams, text-like files, and raw PDF bytes. It found no private-key markers, common AWS/GitHub/Slack token patterns, quoted credential assignments, email candidates, formatted phone candidates, unsafe ZIP paths, encrypted entries, CRC failures, or invalid ZIP/GZIP files.
- Exact PR CI run #358 SUCCESS on head `68fff2450fdbc69ed3645476664956b275e2ceaf`. Scanner output: 118 files seen; 80,780,825 expanded bytes processed; no findings; no license/notice filenames found. Existing integrity checks also tested 5 ZIP archives, compared 34 historical extracted package files to source ZIPs, and passed the dataset identity/structure check.
- Repository metadata confirms `private=true`. This satisfies the requirement to keep the repository private during the audit.

Still open:
- Exact v4 ZIP bytes are not present in the user's Library ZIP listing or the repository. Only the previously recorded SHA-256 `b82694723aa3b1efbefdfff9df5f77aa15acf7c2bfc50e8b48d372e0beb1db61` is known. A hash alone cannot establish its path list or content, so v4-to-main comparison is blocked.
- Personal-data review is not fully closed. Pattern screening does not detect every identifier or encoding. The PDF received a raw-byte scan only; no OCR or full semantic review was performed.
- Data rights and third-party terms remain unresolved. No root LICENSE or recognizable license/notice file was found, but absence of a notice is not permission to redistribute.
- The report and scanner limitations are recorded in [the A3 report on PR #19](https://github.com/aminshahsaheb/btc-signal-lab/blob/audit/a3-archive-content-review/docs/reviews/2026-11-04-a3-archive-content-screening.md). No public-release clearance is granted.

A3 = 3/6: path classification, pattern-based content screening, and private-repository requirement are complete. v4 comparison, complete semantic personal-data review, and source-specific rights review remain open.

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
- Differential test, seed 11: 3,000 random mutations plus 84 hand-built baseline/time checks; 3,084 journal comparisons, 0 disagreements. `OUTCOME_FOR_NONE_SLOT` appeared in 64 mutated journals. A base-corpus-only run compared 84 journals with 0 disagreements.
- The full `REPRODUCE.sh` run passed package integrity and all suites through the 93-test independent verifier, then exceeded the execution time limit during the full four-seed differential phase. The package-reported 120,336-journal result is not claimed as a full rerun in this pass.
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
