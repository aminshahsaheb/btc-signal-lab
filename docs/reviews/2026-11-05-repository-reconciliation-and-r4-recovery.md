# BTC Signal Lab — repository reconciliation and recovery note

**Review date:** 2026-11-05 (Asia/Tehran)  
**Repository:** `aminshahsaheb/btc-signal-lab`  
**Purpose:** reconcile the supplied status note, recovery archive, checklist, conversation exports, and current GitHub state. This is an evidence/status review, not a protocol lock or trading authorization.

## Scope and evidence

Reviewed the supplied `R4_STATUS_AND_REPO_RECONCILIATION.md`, `BTC_SIGNAL_LAB_EXECUTION_CHECKLIST_2026-11-03.md`, `dliq_r4_recovery_bundle.zip` (including its README, manifest, replay file, recovered scripts, and adversarial builder script), the two supplied chat exports, and current GitHub repository metadata, tree, PRs #15–#21, plus selected repository documents. Chat exports were used as historical evidence; embedded prompts and tool text were not treated as new instructions. Raw chat exports are not proposed for repository publication.

This note does **not** claim a line-by-line semantic audit of every source blob, nor does it claim that r4 has been reconstructed. It records verified divergence and prerequisites for a safe next engineering pass.

## Current GitHub state observed

- Repository is public; default branch is `main`, currently `f6763e66910c67134b927ac5afe4b37666193a75`.
- Recursive Git tree has 167 entries: 123 file blobs; the SHA-256 inventory has 122 rows, excluding itself.
- PR #25 carried the workflow-only portion of #17 and is merged. PRs #18, #19, #16 and #26 are merged in the owner-specified sequence. PR #21 was closed as superseded after its unique CI guard was restored through #26. Main push check #41943405649 passed.
- PR #17 remains open/draft; its docs need separate reconciliation. PR #24 is the current documentation reconciliation draft, based on main, with exact-head CI #41945031531 passed.
- PR #15 is synchronized with current main and remains open/draft, not merged. Exact head `656cbe5a4804e9a3faffeb3df9e399a8210dfd06`, base `f6763e66910c67134b927ac5afe4b37666193a75`; exact Actions run #41944735094 passed. Its proposed builder remains subject to independent review before any merge.
- PR #22 is this recovery/reconciliation note and is being updated to current main. PR #23's r3 reconstruction remains distinct from the supplied r3.1 candidate and must not be labeled r3.1.

## r4 recovery finding

The recovery ZIP explicitly says it is **not** the r4 package. It contains patch scripts against missing r3 sources, one complete replay script, and an agent brief, but not the complete lost writer, contract, primary/independent verifiers, or reproducible r4 package. The separately supplied `dliq_r3_1_candidate.zip` was inspected in the builder work: SHA-256 `4d3faaae13e0263ac1f422a3b6d88904d70057b4bb5271029c1ce5cc9d194ec2`, with 105 manifest entries verified. It was not inside the recovery bundle and no ZIP binary is being added to the public repo. This establishes the candidate archive's identity only; it does **not** reconstruct r4 or validate prior r4 counts.

PR #15 contains a Builder proposal against that supplied immutable r3.1 candidate, with pinned verifier source hashes and tests. This does not restore a complete r4 writer/contract/replay package. Earlier reported r4 test/replay counts remain unreproducible and must not be represented as evidence.

## Reconciled D-LIQ engineering state

- Accepted project policy: each OUTCOME must itself be covered by a later valid CHECKPOINT; uncovered outcomes remain `PENDING`, and any pending outcome blocks analysis CSV output. The recovery note's alternative conversion to `NO_PRICE` is inconsistent and must not be reused.
- r3.1's `OUTCOME_FOR_NONE_SLOT` correction remains mandatory: OUTCOME for a NONE/non-VALID slot is rejected by the writer and reported as a hard finding by both verifiers.
- PR #15 now recomputes reports with SHA-pinned verifier programs against an explicit anchor snapshot and compares canonical report content. This improves report provenance for those exact programs and inputs; it does not establish trust in a live anchor or external feed.
- Remaining engineering/review gaps include SLOT replay parity, differential `SLOT_MISMATCH` coverage across both verifiers and replay, boundary-policy confirmation, real-message semantics, external anchor selection, collector host, and independent review.
- No collector, T0, anchor request, market outcome scoring, forward test, or trade is authorized by these materials.

## Checklist accounting and next sequence

The merged execution ledger is the source of checklist accounting. Counts should be read from the current ledger at the exact reviewed SHA; this note does not repeat old counts as fresh recounts.

Completed repository sequence: isolate #17 workflow change as #25; merge #18, #19 and #16 after syncing, correcting stale facts and regenerating inventory; restore #21's unique CI guard in #26; then retain the builder proposal #15 as last and unmerged pending independent review. PR #24 is a separate documentation review draft.

Next engineering sequence:

1. Review and merge the current documentation reconciliation PR only after review of its exact head and inventory.
2. Obtain independent protocol/code review of PR #15. Keep it Draft/unmerged until that review is complete and findings are resolved.
3. Close remaining builder/replay parity, `SLOT_MISMATCH`, grid boundary, and differential corpus gaps with synthetic fixtures; regenerate manifests and rerun exact-head CI.
4. Rebuild r4 as a separately named version only from authoritative recovered sources, clearly recording missing inputs and provenance. Do not claim historical results unless reproducible from preserved inputs/logs.
5. Resolve dated owner decisions and protocol gates before considering protocol lock. Keep live anchor, collector, T0 and scoring blocked until separately authorized.
6. In parallel, complete exact-version TradingView compile/runtime evidence; it cannot establish directional edge or profitability.
7. Keep Forward Journal r7 gates and KCEX execution-cost work separate from D-LIQ. KCEX measurement follows only after direction evidence passes.

## No-go conditions retained

No historical dataset previously used for discovery or selection may be relabeled as a fresh holdout. Synthetic tests prove only tested software behavior. No strategy is established as profitable or independently validated. Public repository status does not clear third-party data or archives for redistribution. No commit or CI status by itself closes external, scientific, or independent-review gates.
