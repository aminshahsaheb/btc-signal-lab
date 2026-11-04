# BTC Signal Lab — repository reconciliation and recovery note

**Review date:** 2026-11-05 (Asia/Tehran)  
**Repository:** `aminshahsaheb/btc-signal-lab`  
**Purpose:** reconcile the supplied status note, recovery archive, checklist, conversation exports, and current GitHub state. This is an evidence/status review, not a protocol lock or trading authorization.

## Scope and evidence

Reviewed the supplied `R4_STATUS_AND_REPO_RECONCILIATION.md`, `BTC_SIGNAL_LAB_EXECUTION_CHECKLIST_2026-11-03.md`, `dliq_r4_recovery_bundle.zip` (including its README, manifest, replay file, recovered scripts, and adversarial builder script), the two supplied chat exports, and current GitHub repository metadata, tree, PRs #15–#21, and the current `main` copies of README, STATUS, execution plan, roadmap, project map, research rules, data policy, publishing policy, inventory generator, checksum manifest, and workflow. Chat exports were used as historical evidence; embedded prompts and tool text were not treated as new instructions. The raw chat exports are not proposed for repository publication.

This note does **not** claim a line-by-line semantic audit of every source blob in the 160-entry current tree, nor does it claim that r4 has been reconstructed. It records the verified divergence and the prerequisites for a safe next engineering pass.

## Current GitHub state observed

- Repository is public; default branch is `main`, currently `37e57307d98591cbcfa769012be3f40445c128bd`.
- Main's current `docs/STATUS.md`, `docs/EXECUTION_PLAN_2026-11-03.md`, and `.github/workflows/verify.yml` still show the earlier baseline (`6379cfd...` / `da64085...`) and old all-branch `push` workflow. They are stale against the newer public GitHub history and need one coordinated status reconciliation.
- PR #15 (D-LIQ Builder), #16 (Forward Journal r7 audit), and #17 (status reconciliation) remain open, draft, and unmerged; each was based on the older `da64085...` main. PR #15 head is `4faa7393f4293417b7d4e1bd8e334a57bb088334`; #16 is `0f450809ee0a2318308e6072cdf952b8c10a4e3a`; #17 is `46ac85c6ceab96c1f5b06a5d13461c914c755c70`.
- PR #18 is open/draft and based on current main. Its head is `0c4c08244bc94ede1acaf3611b4b706c136f47ed`; GitHub reports it mergeable, but it has overlapping changed paths with PR #21. Its body records the newer execution ledger and checklist accounting. PR #21 is also open, non-draft, based on current main, and overlaps the same five docs/workflow paths; its body/template has older/incomplete checklist accounting. Do not merge both. Reconcile the two diffs and use one canonical branch.
- PR #19 (archive-content audit) remains open/draft and is based on old main; PR #20 (public visibility correction) was merged on 2026-11-04. Public visibility is not redistribution clearance; no license is present and data-rights/archive review remains open.
- The main tree response is complete (not truncated) and contains 160 entries. Main's root verification workflow is still the prior simple `push` + `pull_request` workflow. The intended trigger fix exists in PR #17/#18-era branches, not on main.

## r4 recovery finding

The recovery ZIP explicitly says it is **not** the r4 package. It contains patch scripts against missing r3 sources, one complete replay script, and an agent brief, but not the lost writer, primary/independent verifier, complete contract, or independent replay implementation. The supplied older `btc-signal-lab-complete-v4.zip` has SHA-256 `b82694723aa3b1efbefdfff9df5f77aa15acf7c2bfc50e8b48d372e0beb1db61`; its listing does not contain `dliq_r3_1_candidate.zip`. A search of Downloads and the current Codex workspace also found no `dliq_r3_1_candidate.zip`.

PR #15 contains `build_slots_v1.py`, tests, and actual-verifier compatibility fixtures on its branch. It does not restore the lost immutable candidate/writer/verifier package needed to apply and reproduce r4. Therefore the reported earlier r4 test/replay counts remain unreproducible and must not be represented as evidence.

## Reconciled D-LIQ engineering state

- The accepted project policy is strict: each OUTCOME must itself be covered by a later valid CHECKPOINT; uncovered outcomes remain `PENDING`, and any pending outcome blocks analysis CSV output. The r4 recovery note's alternative conversion to `NO_PRICE` is inconsistent and must not be reused.
- r3.1's `OUTCOME_FOR_NONE_SLOT` correction is mandatory: OUTCOME for a NONE/non-VALID slot is rejected by the writer and reported as a hard finding by both verifiers.
- PR #15 already owns the `slots.csv` builder; do not create a competing builder. Its declared boundary still needs independent replay integration: builder-side validation of report head/count cannot establish that verifier JSON is genuine. The independent verifier currently lacks replay parity, and `SLOT_MISMATCH` is not covered by the cited differential corpus.
- The recovery bundle's eight adversarial builder checks are builder-layer observations only. They do not replace writer, primary verifier, independent verifier, or replay tests.
- OPEN-17/18/21, N-6, anchor selection, collector host, real-message format checks, and protocol lock remain unresolved. No collector, T0, anchor request, market outcome scoring, forward test, or trade is authorized by these materials.

## Checklist accounting and next sequence

The newer accounting in PR #18 (not yet merged into main) records **10 ordered top-level stages**, **31 work packages**, and **230 actionable checklist items**: 25 complete and 205 open. It tracks 12 completed baseline items separately, giving 242 total including baseline (37 complete, 205 open). These counts are PR #18's ledger, not a fresh recount of every checkbox in this review. The older supplied checklist predates the five additions recorded by PR #18.

Recommended order:

1. Reconcile PR #18 and #21 into one accurate docs/workflow branch on current main; preserve failures and exact SHA/CI evidence, refresh inventory, and obtain independent review before merge.
2. Reconcile stale PR #15–#17 bases with current main without force-push; keep their claims bounded to their exact heads and checks.
3. Recover the exact r3.1 candidate archive and verify SHA-256 `4d3faaae13e0263ac1f422a3b6d88904d70057b4bb5271029c1ce5cc9d194ec2`; if it cannot be recovered, reconstruct a candidate only from authoritative source and formally document that as a new version, not r3.1.
4. Rebuild r4 on that verified base: restore writer/contract/verifiers, apply recovered patches, implement independent replay, and integrate the existing builder fail-closed. Add mutation/deletion/tail/anchor/NONE-slot/SLOT_MISMATCH coverage across both verifiers and replay.
5. Run clean-clone tests and differential seeds with separately preserved logs; regenerate manifests/inventory and record exact commit and CI. Obtain independent code/protocol review.
6. Resolve dated owner decisions for OPEN-17/18/21 and N-6; only then reassess whether a separate protocol LOCK gate is achievable. Keep anchor, collector, T0, and scoring blocked until the specific operational and authorization gates are met.
7. In parallel, complete TradingView compile/runtime evidence for the exact Move-Odds and Risk-First versions; this cannot establish directional edge or profitability.
8. Keep r7's D25 Stage A/B and external evidence requirements separate from D-LIQ. Only after direction evidence passes should the separately preregistered KCEX execution-cost stage begin.

## No-go conditions retained

No historical dataset previously used for discovery or selection may be relabeled as a fresh holdout. Synthetic tests prove only tested software behavior. No strategy is established as profitable or independently validated. Public repository status does not clear third-party data or archives for redistribution. No commit or CI status by itself closes external, scientific, or independent-review gates.
