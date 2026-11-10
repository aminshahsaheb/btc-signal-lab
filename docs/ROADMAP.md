# Roadmap — master checklist (2026-11-07)

This is the ordered, tickable plan. The current state and blockers are in [`STATUS.md`](STATUS.md); which document is the source of truth for what is in [`INDEX.md`](INDEX.md). This roadmap does not authorize live data collection, a probe, T0, or trading.

## How to read and update this file

- `[x]` done, with evidence: the exact commit SHA and a CI run on that commit, or a linked review. A green run on another SHA does not close an item.
- `[~]` implemented or in a pull request, but **not** independently reviewed or not yet merged. Never counts as done.
- `[ ]` open.
- `[!]` blocked by an external dependency (access, approval, host, third party).
- Owners: **(O)** repository owner, **(C)** Claude (implementation lead), **(G)** GPT or another independent reviewer, **(X)** third party.
- Commit SHAs, tree counts and PR heads are not copied here except as evidence for a ticked item. Do not add "live synchronization" sections: they become stale after the next merge and were the main source of document drift (see the audit record `reviews/2026-11-07-repository-audit.md`).
- Synthetic tests prove behavior only for their tested fixtures. They never establish an edge.

## Gate 0 — Repository baseline, structure, integrity

- [x] Repository is Public by owner decision of 2026-11-04 (open: licence and data-rights review).
- [x] Archived packages, failed results and rejected hypotheses are preserved.
- [x] Source-integrity CI (inventory regeneration, SHA-256 manifests, archive screening) is green on `main` at `4a338f4` (run 42157197785); the D-LIQ r4-draft synthetic workflow is green on the same SHA (run 42157197874). Both workflows are green again on the merge commit `1336d77` (runs 42378627637 and 42378627650).
- [x] Maintenance sequence merged in the owner-approved order: #25 (workflow-only part of #17), #18, #19, #16, #26 (inventory guard), #24, #22, #27, #20; #17 and #21 closed as superseded. History: `EXECUTION_LEDGER_2026-11-04.md`.
- [x] PR #29 — STATUS note that r4-draft is on `main`, unreviewed (docs only): merged by the owner on 2026-11-07 (merge commit `1336d77`), no independent review. CI green on its head `cde9e51` (run 42206484609) and on the merge commit.
- [~] Documentation architecture and drift guards (`INDEX.md`, HISTORICAL banners, this roadmap, `scripts/check_docs.py`, `scripts/check_mirrors.py`, `scripts/check_all.sh`, CI hardening) — PR #30, merged 2026-11-07 (`1336d77`), CI green, **no independent review at merge**. GPT's post-merge review found real defects (E1-E5); they are fixed in `maintenance/guard-fixes-2026-11-07` (Draft PR) and are ticked only after that PR merges and GPT re-reads it.
- [~] Guard fixes E1-E5 (PR #31, merged by the owner 2026-11-08 00:38Z, merge commit `c1242c1`, **no independent review**, CI green on its head `bb902dd`): reference-style and HTML links (R1), exact work-package pattern in `check_mirrors.py`, strict statuses in `check_all.sh` and in the r4 workflow (`scripts/check_dliq_strict.sh`, which also runs the mutation scripts on a throw-away copy), stale STATUS / ROADMAP lines, and `scripts/test_guards.py` (ten deliberate bugs in the guards themselves were all caught). Ticked `[x]` only after GPT re-reads the merged state.
- [ ] D-RULESET-1 — harden the `main` ruleset. Read via the API on 2026-11-07: ruleset "Protect Main" is active (pull request required, deletion and non-fast-forward blocked, no bypass actors) but `required_approving_review_count` is 0 and `required_status_checks` is empty, so a change can reach `main` without a review and without a passing check (O; see the register).
- [ ] D-STRUCT-1 — retire the legacy mirrors (`research/` legacy files, `pine/`) after the guard has run for one cycle (O decision; see the register below).
- [ ] A3 step 3: path-by-path v4-to-main classification (needs the exact v4 ZIP bytes) (O to supply, C to run).
- [ ] A3 steps 4-6: full secrets / personal-data review including PDF content, and source-specific data-rights review (X / O). Public visibility does not clear them.
- [ ] D-PRIV-1 — commit-email exposure (see the register).
- [ ] D-LIC-1 — licence decision (see the register).
- [ ] D-BIN-1 — large-binary policy (see the register).

## Gate 1 — Move-Odds and Risk-First runtime checks

### Move-Odds v0.1.2

- [x] Static local checks: 141 table values parsed, zero lint errors, all 12 golden vectors match the Python replica (see `EXECUTION_LEDGER_2026-11-04.md` and `reviews/2026-10-30-move-odds-package-portability.md`). Static checks are not a Pine compile.
- [ ] Compile the exact Pine source in TradingView on a standard time-based 1-hour `BINANCE:BTCUSDT.P` chart (O).
- [ ] Compare all 12 golden vectors with the rendered values; save compiler output, chart context, values and discrepancies (O).
- [ ] Make the verification harness standalone: it still reads an external `../atlas/` folder and needs pandas/scipy (C).
- [ ] Do not change the algorithm to fit expected values without a dated discrepancy review.

### Risk-First Helper v0.3.1

- [x] Version label, duplicate source copy, root checksum and inventory corrected (PR #9, exact-head CI passed).
- [ ] Compile and test the exact `tools/riskfirst/RiskFirst_Helper_v0_3_1.pine` in TradingView: supported chart types, invalid inputs, long/short checklist, risk cap, stop/target maths, alerts; preserve raw evidence (O).
- [ ] Keep it described as a manual checklist, not a signal.

## Gate 2 — D-LIQ protocol and implementation

Current disposition: **HOLD — DRAFT / NOT LOCKED**. Tracking: Issues #4 and #5. No collector, T0, probe, price scoring, forward directional test, or strategy use until a separate lock decision.

### 2A — Package identity (done)

- [x] r3 audit package identity and internal manifest verified (Issues #4/#5; ZIP SHA-256 `0431fb54…b529`, r3 protocol `449753f9…df8d`).
- [x] r3.1 candidate archive identity verified: SHA-256 `4d3faaae13e0263ac1f422a3b6d88904d70057b4bb5271029c1ce5cc9d194ec2`, 105 manifest entries; its protocol SHA-256 is `5c05a15de7addd55cade7617fcdcaea570aad82b61c0b16c95d14024fc649948`.
- [x] Synthetic S10 outcome-dependent-missingness failure recorded (false PASS 0.050 → 0.177); OPEN-21 allowance **not adopted**.

### 2B — Statistics and protocol text (GPT r3 audit orders 5 and 6)

- [~] Order 5: write OPEN-21 as **unapproved, sensitivity-analysis only** in the protocol text. GPT's wording (2026-11-07, F1) is recorded as a PROPOSAL in `specs/d-liq/PROPOSED_TEXT_OPEN21_LIQ_INCREMENTAL_2026-11-08.md`; not integrated, because the r3 protocol text is not on `main`. Open: GPT / owner confirmation and the target file.
- [~] Order 6: write `LIQ_INCREMENTAL` as "a positive conditional estimate under the limited prior-sign control, not a causal or tradable edge". GPT's wording (F2) is recorded in the same proposal file; not integrated for the same reason.
- [ ] Pre-register and test more than one outcome-dependent and one volatility-dependent missingness mechanism, including the effect on the stratified estimator; justify any policy before lock (C, G).
- [ ] The final report must give NO_PRICE rates by side, by `prior_sign` and by reason (protocol 7.7).

### 2C — Implementation (synthetic, in `research/d-liq/r4-draft/`; on `main` since `4a338f4`)

- [~] Order 1 and 4: per-OUTCOME anchoring coverage (contract §6.4), writer helper `outcome_and_anchor`, both verifiers (`outcomes`, soft `OUTCOME_UNCOVERED`), builder cross-check; tests for tampered, omitted, tail-unanchored, duplicate and NONE-slot OUTCOME records. Evidence: run 42157197874. Counts are the author's own and not independently recounted.
- [~] Order 2: `slots.csv` builder (N_unanch, prior_sign, missing / late / unanchored SLOTs, NO_PRICE, hard verifier findings, pinned verifiers). Same evidence. PR #15 holds the earlier v1 builder, which the r4 builder supersedes in code.
- [~] Order 3 (part 1): mandatory SLOT replay in the primary verifier and in the builder; hard `SLOT_MISMATCH` and `SLOT_EARLY_WRITE`.
- [x] Order 7 is respected: nothing in the tree claims "ready for lock".

### 2C+ — Defects found by the GPT audit of 2026-11-07 (each re-checked by Claude against the code at `4a338f4`)

- [~] **G-1 CANDLE provenance (confirmed, highest priority; proposal, shared parser and reference checker in `research/d-liq/g1-candle-draft`; first PR #34 was merged into the r5 branch, not `main`, so it is re-submitted as a new PR to `main`; not reviewed, not integrated).** The verifier hashes the raw CANDLE bytes but never parses them: `open` and `open_time_ms` are free fields that only have to equal the OUTCOME. `CANDLE_NOT_LIVE` rejects only `recv_ms < open_time_ms`, so a REST/backfill kline received after its open time passes. Needed: a parser for the exchange's kline stream message (symbol, interval, kline start time, open price, event time, message type) that is used by both verifiers and the builder; hard findings when the recorded fields differ from the raw bytes, when the message is not a live-stream kline (a REST array is rejected), or when the event time is outside the kline or inconsistent with `recv_ms`; contract amendment; tests and differential operators. Bounds are `[P]` parameters for GPT to review (C implements, G reviews). **Status 2026-11-08:** the contract proposal, a shared kline-frame parser, a reference CANDLE checker (64 synthetic tests, 62 of 62 deliberate bugs killed) and a reproducible demonstration are in the draft package; the maximum receipt lag `L` is NOT given a value; every exchange field name is `[VERIFY]` (no real Kline capture: exchange unreachable from the owner's location). **Finding:** recording kline frames as MSG (the audit's design) makes every slot NONE/MALFORMED under the current replay, and a kline connection with the smaller id becomes `primary_conn`; the contract needs a per-connection `feed` marker (decision A for GPT). Not done: integration into the verifiers, builder, differential harness and rebuild patches; independent review. **Decisions 2026-11-10 (GPT, relayed by the owner; proposal section 8):** A (required `CONN.feed`, replay over `FORCE` connections only, keep `CANDLE.msg_seq`), A2 (journal and genesis v3), A3 (two separate connections, no combined stream for `forceOrder`) are the working basis; `L` stays open (5000 ms not approved); the top-level `st` rule is to be removed from the single-symbol classifier and an unexpected `ps`/`st` there is a structural exception; the all-market stream is out of scope; at least one real BTCUSDT `forceOrder` frame is required before any lock. **First such frame captured 2026-11-10 (proposal section 9): `ps` and `st` sit inside `o` on the single-symbol stream too, GPT answered the same night (section 10): `o.ps` and `o.st` are known OPTIONAL fields (checked `ps == s` and `st == 1` when present; absence is not an error; an inconsistent value is a structural finding; a top-level `st` is not accepted; never used for direction); working basis only; GPT then answered the follow-up questions (section 11): an inconsistent message is `MALFORMED`, its slot is voided, a sticky run-level hard finding keeps `analysis_eligible = false` until a review and a replay under the controlling contract, reception and replay continue, a top-level `st` is forbidden, other unknown keys are non-hard warnings; GPT then decided (section 12): the verdict stays `FAIL` (no new value), a wrong type of `o.ps`/`o.st` is a hard finding, a top-level `ps` is only a warning, the rules cover all `FORCE` connections, and r6 must specify a run-level check of every `FORCE` message (the current replay does not look at messages after the last `SLOT`); one frame only.** None of this is in the contract text or code yet, and nothing is locked.
- [~] **G-2 Replay cannot be skipped (confirmed; implemented in `research/d-liq/r5-draft`; PR #32 merged by the owner into `main` on 2026-11-08 18:38Z, merge `f8198a2`, with no independent review; not reviewed).** Contract 7.6 (GPT wording): `replay_slots` defaults to True; only exactly `True` replays (any other value is a fail-closed opt-out); an opt-out gives `replayed: false`, `analysis_eligible: false`, hard `REPLAY_NOT_RUN` and verdict `INCOMPLETE` (never PASS; `FAIL` if another hard finding exists). The "independent" verifier has no replay, so it can never return PASS either. The builder refuses reports without the markers and writes no analysis CSV while no independent replay exists (`REQUIRE_INDEPENDENT_REPLAY = True`; most conservative reading, to be confirmed by GPT). Evidence in the PR: suites 234 / 106 / 59 / 2 / 22, 32 of 32 deliberate bugs killed, four differential seeds with 0 disagreements. Not done: the independent replay itself (order 3, second half). Tick `[x]` only after independent review and merge.
- [~] **G-3 Clean-room rebuild (confirmed; started in `research/d-liq/r5-draft`).** r5-draft is rebuilt from `r4-draft` on `main` by `patches/assemble_r5.py`: the base is verified completely (pinned manifest hash, every file hash, no extra or missing file, no symlink), the output is compared with `ASSEMBLED_MANIFEST.sha256` and with the committed tree, and CI runs it with negative tests. r4-draft itself was re-derived once from the r3-reconstruction base (PR #23 commit `b5f5075a`, pinned manifest hash) and matches byte for byte except README, MANIFEST, one renamed base README, logs and patches; CI repeats this (`r4-from-base` job). Still open: the base lives on a pull-request branch (owner decision D-PR-15-23), and the pinned Python version / environment is only the CI image.
- [ ] **G-4 Replay cost (OPEN-23).** Measure replay time and memory on long synthetic journals and record the result with the `recv_ms ≥ tau−16 min` filter decision (C).

### 2D — Independent verification

- [~] Order 3 (part 2) (candidate in `research/d-liq/g2-replay-draft`, 2026-11-09, not reviewed, not adopted; see its README for results, the mutation review, and the three limits: only partly independent, spec inputs missing from the repo (D-SPEC-1), generator shares the author's blind spots): an independent SLOT-replay implementation written clean-room from the written specifications only, compared by a differential harness that actually exercises `SLOT_MISMATCH` (C with a fresh-context agent, G review). The 2026-11-06 attempt was cut off by an API rate limit before its notes file was written; its replay and tests, completed and checked, are the candidate in `research/d-liq/g2-replay-draft`.
- [ ] Independent recount and review of `r4-draft`: re-run every suite, compare the builder with the PR #15 head, check hash equality, attempt to break it (G / X).
- [ ] Independent reproduction of the original r3 package's four-seed differential run in a sufficiently provisioned environment (X).
- [ ] Third-party verifier or adversarial mutation set not authored by the implementation author (X).

### 2E — Protocol decisions (dated decision record each)

- [ ] OPEN-17 control thresholds (cell floor 30, NO_CTRL cap 5 %, lower bound > 0); OPEN-18 UNANCHORED cap 5 %; OPEN-21 (see 2B); OPEN-23 (replay cost and the `recv_ms ≥ tau−16 min` filter); N-6 / the entry-candle decision (exact candle at τ+5 min); OPEN-14 (journal path v2 vs r7/r8); OPEN-15 (accept `X = FILLED` only).
- [x] OPEN-22: no hard lag cap for OUTCOME coverage; checkpoint immediately after each OUTCOME, report the lag distribution, final drain checkpoint; a prolonged anchor outage gives INCONCLUSIVE, never silent row removal (owner decision 2026-11-05).

### 2F — Operational gates (blocked)

- [!] Collector / probe host reachable from where the work is done (OPEN-8, OPEN-20). The owner's own connection to the exchange is not available.
- [!] Format-only dry run of at most 20 raw `forceOrder` messages; the single-symbol endpoint path is unverified (OPEN-10, OPEN-13). Needs explicit approval.
- [!] Real external anchor with its own timestamp, resolution and uncertainty bound, tested end to end from the intended host (OPEN-16). `MockAnchor` is not a production anchor.
- [!] End-to-end run: collector → journal → verifier → `slots.csv` → analysis.

### 2G — Lock

- [ ] Final immutable candidate; every suite re-run on its exact SHA; independent review; then a **separate** lock decision (O + G). Only after that: a bounded format-quality probe with no price or outcome analysis; T0 only after the lock.

### D-LIQ pull requests

- [~] PR #15 (v1 builder + eight review/decision documents) and PR #23 (r3-reconstruction): both open, **marked ready for review by the owner on 2026-11-07** (no longer Draft), both behind `main` and not mergeable (conflicts). Their code is superseded by `r4-draft`. Disposition is an owner decision (D-PR-15-23); do not merge either without independent review.

## Gate 3 — Forward Journal r7

Current disposition: **DRAFT / NOT LOCKED / SPEC ONLY**. Tracking: Issue #8.

- [x] D25 confirmed not satisfied; no real anchoring target and no complete two-namespace end-to-end exercise.
- [x] The D-LIQ r3 package contains the r7 specification but no separate r7 KAT harness or run report.
- [ ] Verify the r7 KAT harness identity, hashes and provenance.
- [ ] Re-run all available synthetic KATs in a clean environment and save exact outputs.
- [ ] Map D1-D24 to evidence or an explicit "untested" status.
- [ ] Independent review of the two-namespace target contract and the D25 acceptance test.
- [ ] Third-party adversarial review.
- [ ] Keep r7 unlocked until every gate has evidence and a separate lock decision.

## Gate 4 — Strategy validation

- [x] Discovery and confirmation data are burned and cannot become a holdout by renaming; rejected hypotheses are preserved.
- [ ] Any new candidate: pre-register hypothesis, direction, target, sample, costs, statistic, stopping rules, code hash and T0 before outcome inspection.
- [ ] Apply the fixed chain: bootstrap/significance, fees, train/test, independent-block walk-forward, trade/candle-path Monte Carlo, multiple-testing / DSR.
- [ ] Do not reopen the closed MA/EMA/Ribbon families on the same historical data.
- [ ] No edge or profitability claim from synthetic tests or historical discovery data.

## Gate 5 — KCEX execution

- [ ] Start only if a directional hypothesis passes its own frozen test.
- [ ] Pre-register entry, stop, target, sizing and exit rules separately.
- [ ] Measure KCEX fees, spread, slippage, funding and actual fills; evaluate net results on independent data and a forward period.
- [ ] Do not infer KCEX profitability from Binance reference returns.

## Owner decisions register

A decision is open until the owner records it with a date. The column "Recommendation" is a proposal, not a decision.

| ID | Question | Options | Recommendation | Status |
|---|---|---|---|---|
| D-PR-29 | Merge PR #29 (docs only, 3 files)? | merge / hold | Merge after reading the 3-file diff; CI is green on its head. | **done** — merged by the owner on 2026-11-07 (`1336d77`) |
| D-RULESET-1 | The `main` ruleset requires a pull request but 0 approvals and no status check (read via the API 2026-11-07; unchanged). | add required check `verify` / add a required review from a second identity / both / leave | Add the required status check `verify` now (it is the only always-running job; the r4 workflow is path-filtered and cannot be required). A required review needs a second GitHub identity (an author cannot approve their own pull request). | open |
| D-MERGE-1 | PR #28 (2026-11-06), PRs #29 / #30 (2026-11-07) and PR #31 (2026-11-08) were merged with no independent review, although #30 was announced as a Draft awaiting review. | accept and record / revert | Record only (done here). Revert nothing: the content is documentation and CI, now post-merge reviewed by GPT. The prevention is D-RULESET-1. | recorded |
| D-STRUCT-1 | The same documents and Pine sources exist twice (13 mirrored pairs: `research/` ↔ `specs/` and `docs/`; `pine/` ↔ `tools/`). Which tree survives? | keep both with the guard / retire the legacy mirrors | Keep the guard now. Then retire `research/` legacy files and `pine/` in one dedicated PR. The root manifest pins only the canonical copies, so the retirement changes no pinned hash; the inventory is regenerated. | open |
| D-PR-15-23 | PR #15 and PR #23: behind `main`, code superseded by `r4-draft`. Both were marked **ready for review** by the owner on 2026-11-07 (14:00Z / 14:02Z) and are no longer Draft; GitHub reports them as not mergeable (conflicts). | convert back to Draft / leave open / close as superseded | Convert both back to Draft (a ready PR can be merged by one click if the conflicts are resolved, and the ruleset would not stop it) and keep them until the independent review of `r4-draft`. Then close both; first move PR #15's eight review and decision documents to `docs/` in a docs-only PR after reading them. | open |
| D-PRIV-1 | The owner's personal email address is the author address of 66 of the 68 commits on `main` (and the committer address of 51); it is therefore public in the Git metadata. | enable GitHub "Keep my email addresses private" and "Block command line pushes that expose my email" now / also rewrite history | Enable both settings now (affects future commits only). Do not rewrite history: it breaks every branch and PR SHA, and the address is already public. `PUBLISHING.md` requires a separate impact review and explicit authorization for a rewrite. | open |
| D-LIC-1 | The repository has no licence. | none for now / all-rights-reserved notice / code licence + documents licence | Keep "none" until the data-rights review (A3) is done; then decide. | open |
| D-BIN-1 | About 48 MB of binaries (Atlas ZIPs, a 14 MB dataset, a 3 MB PDF) are in Git. | keep / move to Releases or LFS | Keep what is already there (immutable, hash-pinned). Add a rule: no new binary over 5 MB without a recorded decision. | open |
| D-DLIQ-OPEN | OPEN-17, OPEN-18, OPEN-23, N-6 / entry candle, OPEN-14, OPEN-15 (see 2E) | adopt the protocol's [P] values / change | Decide only after the independent review of `r4-draft`. Keep OPEN-21 **not adopted** (GPT order 5). | open |
| D-HOST-1 | Where can the collector / probe run and be reached, and which external anchor? | blocked | Needs the owner's access constraints and an explicit approval; no work possible before that. | blocked |
| D-SPEC-1 | The independent replay was written from specification files three of which (`07_MESSAGE_CONTRACT_v1.md`, protocol section 4 and appendix B extracts) are NOT in the repository. | add them to the repo / keep them outside with hashes only | Without them nobody can repeat the clean-room exercise or check the message classification against its source text. Hashes are in `research/d-liq/g2-replay-draft/SPEC_INPUTS.txt`. Owner decides (they are the owner's own protocol files). | open |
| D-REVIEW-1 | Codex is rate-limited until early December. Who is the independent reviewer? | GPT / a fresh-context agent / a human | GPT for the protocol and the recount, plus a fresh-context agent for the clean-room replay. Neither replaces a human third party before lock. | open |

## Closure rules

- Issues #4, #5, #7 and #8 stay open while their gates are open. Do not close #7 until every applicable item above has evidence, an exact commit and required checks.
- Closed without merge, history preserved: PR #1, #2, #3, #10, #13, #17, #21.
- Never force-push. Never merge a Draft without an owner decision. Never lock a protocol from this file.
