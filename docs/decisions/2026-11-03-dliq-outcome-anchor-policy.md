# D-LIQ OUTCOME checkpoint-coverage decision

Decision ID: DLIQ-DEC-2026-11-03-OUTCOME-ANCHOR-01  
Decision date: 2026-11-03  
Status: **APPROVED — project-level fail-closed policy**  
Applies to: PR #15, D-LIQ r3.1 candidate Builder and every downstream analysis export.

## Decision

A journal OUTCOME event is eligible for `slots.csv` only when a valid CHECKPOINT covers the OUTCOME event itself.

A checkpoint covers an OUTCOME when its verified `anchored_seq` is greater than or equal to the OUTCOME event sequence, and the CHECKPOINT event occurs after the covered sequence. Both the primary and independent verifiers must pass for the same journal head and event count. Their slot maps and missing-grid lists must agree.

## Required Builder behaviour

1. A VALID SLOT with an OUTCOME that is absent remains `PENDING`.
2. A VALID SLOT with an OUTCOME outside the verified checkpoint-covered prefix remains `PENDING`, even when the SLOT itself is anchored and both verifiers return PASS.
3. Neither EVAL nor NO_PRICE may be emitted for that row while it is PENDING.
4. Any PENDING row blocks both analysis CSV files. A failed build must remove stale CSV outputs.
5. A later valid checkpoint that covers the OUTCOME may make the row eligible, subject to all other Builder and verifier gates.
6. A malformed, regressing, impossible, or otherwise invalid checkpoint cannot establish coverage. Verifier hard findings invalidate the registry.
7. This rule applies per OUTCOME. A trailing unanchored event that is not an OUTCOME does not by itself invalidate an already covered OUTCOME; all other verifier findings and gates still apply.

## Rationale

A checkpoint that covers a SLOT proves only the journal prefix through that SLOT. It does not prove that a later OUTCOME was present in that prefix. If the Builder accepts the later OUTCOME without a later checkpoint, an unanchored journal tail can affect the statistical input.

The immutable r3.1 A.6 wording requires the OUTCOME to follow a checkpoint that covers its SLOT. It does not clearly require the OUTCOME itself to be covered. This decision deliberately adds a stricter project acceptance condition. It does not rewrite, amend, or change the SHA-256 identity of the supplied immutable r3.1 protocol or candidate package. Any future protocol amendment must be separately versioned, reviewed, and hashed.

## Evidence and test requirement

The repository includes tests that use JSON reports emitted by the exact writer, primary verifier, and independent verifier from the supplied candidate archive. They cover:
- covered OUTCOME → Builder emits EVAL;
- uncovered OUTCOME tail → both verifiers return PASS with TAIL_UNANCHORED, but Builder emits PENDING and refuses analysis CSV.

Fixture provenance identifies the exact archive, protocol, writer, and verifier SHA-256 values. Fixtures use a local MockAnchor only. They are not live-anchor, real-feed, protocol-lock, or trading-edge evidence.

## Approval and limits

This is the user's explicit owner decision in the project conversation on 2026-11-03. It authorizes this conservative Builder policy and its tests only. It does not authorize changing the immutable candidate protocol, merging PR #15, locking r3.1, starting a collector or T0, connecting to Binance or an external anchor, scoring market outcomes, or evaluating a strategy.

Independent third-party review remains required before merge.
