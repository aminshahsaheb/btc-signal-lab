# D-LIQ r3 slots-builder review — 2026-11-03

## Reviewed implementation

Draft PR #15, branch `research/dliq-r3-slots-builder-draft`.
Reviewed builder source head before this review record: `d165d4413a8d6a585467ebaed54e63272161f487`.

## Changes reviewed

- Deterministic `slots.csv` builder for the r3 A.6 mapping.
- Fail-closed behavior for verifier hard findings, disagreement, pending slots, and outcomes linked to non-VALID slots.
- Explicit recognition of `OUTCOME_FOR_NONE_SLOT`.
- Verifier report schema checks and controlled errors for malformed reports.
- Strict sorted/unique missing-grid validation.
- Safety ceiling of 100,000 grid points before allocation.
- File handles closed with context managers.
- Synthetic regression tests for the above.

## Evidence

- r3.1 candidate protocol SHA-256: `5c05a15de7addd55cade7617fcdcaea570aad82b61c0b16c95d14024fc649948`.
- r3.1 candidate ZIP SHA-256: `4d3faaae13e0263ac1f422a3b6d88904d70057b4bb5271029c1ce5cc9d194ec2`.
- Clean-extraction component tests: analysis 27, discard 12, control 45, message contract 59, journal/writer 199, r3 consistency 16, independent verifier 93; all passed.
- Differential seeds 11–14: 30,084 journals per seed, zero disagreements (120,336 total).
- `SLOT_MISMATCH` is covered by the primary verifier's replay-layer test, but not by the differential corpus; the independent verifier does not implement the optional replay layer.
- Builder PR tests use synthetic verifier reports. Integration against the exact verifier executables' output remains unverified.

## Remaining gates

- Third-party review.
- Confirm the collection window and pending-tail policy. A.6 currently defines the grid from the first to last observed SLOT; this does not define expected leading/trailing slots outside that range.
- Resolve OPEN-17/18/21 and OPEN-14 in dated decision records. OPEN-21/MNAR remains a scientific blocker.
- Real Binance message-format dry run requires an approved, reachable host; no live exchange connection was made.
- Select and test an RFC 3161 anchor and collector host.
- TradingView compile/runtime evidence for Move-Odds and Risk-First.
- Forward Journal r7 KAT/D25 remains separate and unpassed.

## Disposition

PR #15 remains DRAFT / NOT MERGED. D-LIQ r3.1 remains DRAFT / NOT LOCKED. No T0, collector, market scoring, or strategy use is authorized by this review.

## 2026-11-04 addendum — later integration evidence

This review record predates the actual-verifier compatibility fixtures. The following later evidence supersedes the statement above that integration against exact verifier output remained unverified:

- `research/d-liq/r3-tools/test_actual_verifier_reports.py` now loads a compressed fixture whose provenance records the exact r3.1 archive, protocol, writer, primary verifier, and independent verifier SHA-256 values.
- The anchored OUTCOME fixture expects EVAL. The unanchored OUTCOME-tail fixture expects PENDING even when both actual verifier reports say PASS.
- Both cases use a local MockAnchor. This is fixture-level compatibility evidence only; it is not a real external anchor, live feed, or collector test.
- Exact PR #15 head `86adcaffe9f22ff89354123b9b8316d9baabd64a` passed CI run #258, including the 23-test unittest discovery step and SHA-256 manifest verification.
- The PR #15 workflow now preserves the PR #17 trigger policy: push checks only main; feature branches are checked by pull_request lifecycle events. The Builder test step remains enabled. This workflow update is on the PR #15 branch and has not been merged to main.

The independent third-party review, OPEN-17/18/21, N-6, SLOT replay parity, real Binance message verification, external anchor qualification, collector-host qualification, LOCK, and T0 gates remain open.
