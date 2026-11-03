# Status register — 2026-11-03 (reconciled)

## Overall

**Research infrastructure: useful. Trading edge: not established.** The repository remains private. No strategy in this repository is proven profitable or independently validated.

This register was reconciled against the live GitHub state on 2026-11-03. Main is unchanged at `da64085fe1c066026a6bee219b600d2b42f280f6`. The current work is proposed on draft PRs; a green CI run does not mean that a draft PR has been accepted or merged.

## Verified repository and merged work

- Main baseline: `da64085fe1c066026a6bee219b600d2b42f280f6`.
- PR #9: Risk-First v0.3.1 label and inventory correction; exact-head CI passed; merged as `0ae8a0cd9af36d681a88fbd4849303bd7039210a`.
- PR #11: documentation and strategy-status reconciliation; exact-head CI passed; merged as `69e716ff4ca4a5cd71b63f4107a746371af08706`.
- PR #12: duplicate Pine source synchronization and manifest refresh; exact-head CI passed; merged as `6379cfd1233a16d29787624ef773d295a5b4c265`.
- PR #14: post-PR-12 snapshot correction; exact-head CI passed; merged as current main `da64085fe1c066026a6bee219b600d2b42f280f6`.
- PR #1/#2/#3/#10: closed without merge for the documented superseding or temporary-audit reasons. Their useful history remains preserved.
- Master execution ledger: [Issue #7](https://github.com/aminshahsaheb/btc-signal-lab/issues/7). It remains open.

## Active draft PRs — exact live state

### PR #15 — D-LIQ r3 slots builder

- Branch: `research/dliq-r3-slots-builder-draft`.
- Exact head: `86adcaffe9f22ff89354123b9b8316d9baabd64a`.
- State: OPEN / DRAFT / NOT MERGED. Main base: `da64085fe1c066026a6bee219b600d2b42f280f6`.
- Latest pull-request workflow: run #258, completed SUCCESS on this exact head. The branch's push workflow #257 was also recorded as PASS in the execution ledger.
- Review submissions: none recorded. Independent third-party review is still open.

Completed on the PR branch (not yet part of main):

- [x] Implement deterministic `build_slots_v1.py` and its unit tests.
- [x] Add 23 Builder tests to CI, including actual-verifier-report fixture integration tests.
- [x] Reproduce the supplied r3.1 candidate in a clean extraction; verify archive identity and all 105 manifest entries.
- [x] Re-run the four differential seeds (11–14): 30,084 journals per seed; 120,336 comparisons total; zero disagreements.
- [x] Record the strict OUTCOME checkpoint-coverage owner decision `DLIQ-DEC-2026-11-03-OUTCOME-ANCHOR-01`. This is a conservative Builder acceptance rule, not an amendment to the immutable r3.1 protocol.
- [x] Test both anchored OUTCOME → EVAL and uncovered OUTCOME tail → PENDING using immutable JSON reports emitted by the exact candidate writer and both verifiers.
- [x] Record the replay-coverage boundary: `SLOT_MISMATCH` is not in the independent differential corpus because the independent verifier does not implement optional SLOT replay. Primary-verifier tests exercise replay tampering.

Still open:

- [ ] Independent third-party/adversarial review.
- [ ] Owner decision on whether future Builder/collector runs must enable optional primary SLOT replay.
- [ ] Resolve OPEN-17, OPEN-18, OPEN-21, N-6, and remaining dated protocol decisions. OPEN-21 remains a scientific blocker: synthetic outcome-dependent missingness raised false-PASS from 0.050 to 0.177 when 5% of losing outcomes were missing; no allowance was adopted.
- [ ] Approved Binance format-only dry run on a reachable host.
- [ ] Real external anchor qualification and end-to-end evidence.
- [ ] Collector host, clock, network, and retention controls.
- [ ] Final immutable candidate and separate lock decision after all applicable P0 gates pass.

No collector, T0, price/outcome scoring, forward directional test, or strategy use is authorized.

### PR #16 — Forward Journal r7 D1–D25 audit

- Branch: `research/forward-journal-r7-audit-draft`.
- Exact head: `0f450809ee0a2318308e6072cdf952b8c10a4e3a`.
- State: OPEN / DRAFT / NOT MERGED. Main base: `da64085fe1c066026a6bee219b600d2b42f280f6`.
- Latest pull-request workflow: run #235, completed SUCCESS on this exact head. The branch's push workflow #234 was also recorded as PASS in the execution ledger.
- Review submissions: none recorded. Independent review is still open.

Completed on the PR branch (audit/documentation only):

- [x] Map D1–D25 to repository evidence or an explicit unproven status.
- [x] Confirm that r7 is SPEC ONLY / NOT LOCKED: no separate r7 writer, collector, auditor, verifier, metrics implementation, executable KAT harness, or KAT run report exists in the audited tree.
- [x] Identify two specification copies that differ only by a trailing newline; canonical path remains undecided.
- [x] Establish the D25 two-stage interpretation: Stage A pre-lock target qualification and Stage B post-lock implementation E2E. Neither has evidence.
- [x] Record the four unresolved Stage A/B normative details and the independent evidence needed for D25.

Still open:

- [ ] Independent review of the D1–D25 mapping and D25 proof boundary.
- [ ] Owner decisions on Stage A code identity, Stage A config, evidence reuse versus Stage B repetition, and invalidation conditions.
- [ ] Choose the canonical r7 specification path before implementation.
- [ ] Implement and run the required r7 components and KATs.
- [ ] Complete both D25 stages with independently attributable destination, readback, receipt/time, and truncation evidence.
- [ ] Separate lock decision only after all gates pass.

No external anchor was contacted. No collector, T0, Binance connection, or market scoring was started.

## Component status

| Component | Verified status | Next evidence needed |
|---|---|---|
| Move-Odds Panel v0.1.2 | Static Python/vector checks recorded; Pine source has not been compiled in TradingView. | Compile exact source on standard 1h `BINANCE:BTCUSDT.P`; preserve compiler output and compare all 12 vectors. |
| Risk-First Helper v0.3.1 | Static math review and source/inventory correction recorded; manual checklist only; Pine runtime not verified. | Compile exact source in TradingView and test long/short, risk cap, stop/target, leverage cap, and alerts. |
| D-LIQ r3.1 candidate | Builder and four-seed rerun completed on PR #15; protocol remains DRAFT / NOT LOCKED. | Close independent, scientific, feed, anchor, host, and owner-decision gates. |
| Forward Journal r7 | Evidence-gap audit completed on PR #16; SPEC ONLY / NOT LOCKED. | Resolve specification decisions, implement KATs, complete independent review and D25 evidence. |
| Atlas v1 | Archive/input identity and structural checks recorded; prior isolated historical reproduction recorded. | Optional fresh clean-checkout reproduction; path classification and data-rights review remain open. |
| Strategy research | No active independently validated candidate. Prior rejected families remain closed on burned data. | New preregistration and independent data; no parameter rescue on burned history. |
| KCEX execution | Not started. | Separate venue economics only after directional evidence and separate authorization. |

## Historical and scientific controls

- Discovery/confirmation history is burned. Do not rename it as holdout.
- Synthetic tests establish behavior only for the tested fixtures. They do not establish live-feed, anchor, clock, production, or market validity.
- The r3 and r3.1 package identities are distinct. Do not combine their evidence.
- The four-seed zero-disagreement result applies to the supplied r3.1 candidate and its defined differential scope. It does not establish independent SLOT replay parity.
- The 602,208-row BTCUSDT 5-minute historical dataset ends on 2026-09-22. Its hashes and structure do not prove a trading edge or independent source quality.
- The repository remains private. Do not add credentials, private account data, raw conversation exports, or unreviewed live capture.

## Current order of work

1. Complete independent review and remaining offline decisions for PR #15 and PR #16.
2. Keep both PRs draft and unmerged until review and evidence gates close.
3. Obtain TradingView compile/runtime evidence for both Pine tools.
4. Resolve D-LIQ missingness and protocol decisions; then separately qualify real feed, anchor, and collector infrastructure.
5. Resolve r7 specification decisions, implement KATs, and prove both D25 stages.
6. Only after a separate protocol lock decision, consider a bounded format-quality probe. No price/outcome analysis in that probe.
7. Only after directional gates pass, preregister strategy execution and measure KCEX economics separately.

A task is complete only when its evidence, exact commit, and required checks are recorded. A CI pass on a draft branch does not close external or independent-review gates.
