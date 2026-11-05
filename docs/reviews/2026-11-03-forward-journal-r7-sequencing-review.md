# Forward Journal r7 — pre-lock / post-lock sequencing review

Review date: 2026-11-03  
Reviewed source: `research/forward-journal/FORWARD_JOURNAL_SPEC_v1_r7_DRAFT.md`  
Source Git blob: `ffacc1c7d4c329b787be222937d2ae9c9d943245`  
Disposition: **OPEN SPECIFICATION CLARIFICATION — NOT A PROTOCOL CHANGE**

## Finding: D25 / B.7(4) and C.1 do not define the same test stage clearly

The current text gives two timing requirements:

1. **Pre-lock qualification:** B.7(4) says destination selection, independent confirmation, and a complete rehearsal of B.7(7) on the selected destination (with a test journal and test namespace) are conditions that remain open before lock. D25 repeats that a complete exercise must be performed before lock and reported.
2. **Post-lock formal execution:** C.1 orders the formal process as LOCK (step 1), BUILD and synthetic KATs (step 2), DRY-RUN (step 3), CODE FREEZE (step 4), GENESIS (step 5), CONFIG (step 6), and then the real two-namespace E2E anchoring test (step 7), before COLLECTOR_START.

A literal single-run reading is circular: the post-lock E2E in C.1 step 7 depends on the implementation and CONFIG created after LOCK, while B.7(4)/D25 require a complete exercise before LOCK.

A plausible intended reading is a **two-stage process**:
- Stage A, before lock: a disposable target-qualification rehearsal using a non-production test journal, temporary client/configuration, and test namespaces. It validates the target's actual semantics and the feasibility of every B.7(7) operation.
- Stage B, after lock: the formal E2E run in C.1 step 7, using the frozen implementation and the actual journal CONFIG. This produces the journal event and evidence required before collector start.

However, this two-stage interpretation is not explicitly stated. It must not be silently assumed.

## Required clarification before lock

The spec owner should state, in normative language:

1. Whether B.7(4)/D25 require a separate pre-lock target-qualification rehearsal, distinct from C.1 step 7.
2. Which code is allowed in Stage A (small disposable probe vs. the eventual writer), and whether its code hash is recorded.
3. Which configuration is used in Stage A, and how it is tied to the exact ten-key target contract later frozen in CONFIG.
4. Which evidence Stage A must preserve: both namespace records, raw request/response, duplicate-sequence rejection, independent readback, receipt uniqueness across the target, timestamp verification/trust class, truncated-copy hash, verifier output, and an independently attributable report.
5. Which Stage A results are reusable after lock, and which checks must be repeated by the frozen Stage B implementation.
6. Whether a target, namespace, operator, receipt method, or read-client change invalidates Stage A and requires a new rehearsal.
7. Whether Stage B must be repeated if the frozen code or CONFIG changes after the run.

## Suggested acceptance rule (review proposal, not adopted protocol text)

Treat Stage A as **target qualification only**, never as proof that the frozen writer passed. Treat Stage B as the authoritative implementation-specific E2E test. Require both stages for lock/T0 readiness if that is the intended design. Bind each report to its exact target identity, namespace names, code hash (where applicable), config hash (where applicable), timestamp evidence, and raw output hashes.

Do not treat a mocked destination as Stage A evidence. Do not treat Stage A as a substitute for Stage B. Do not mark D13 or D25 passed until the spec owner resolves the timing and the required evidence exists.

## Scope and status

- This note reviews source wording only.
- No r7 protocol file was modified.
- No implementation, target selection, external request, live feed, collector, T0, or market scoring was performed.
- This is not an independent external code review.
- r7 remains **DRAFT / NOT LOCKED**.

## Correction after line-by-line source re-check

The first wording of this review overstated the timing ambiguity. A line-by-line comparison of B.7(4), B.7(7), D25 and C.1 shows that the specification does distinguish two separate exercises:

- **Pre-lock target qualification:** B.7(4) makes a complete rehearsal of B.7(7), on the selected real destination with a test journal and test namespace, a condition of lock. D25 repeats this pre-lock requirement and requires a report.
- **Post-lock implementation E2E:** C.1 step 7 runs the formal test after LOCK, BUILD, CODE FREEZE, GENESIS and CONFIG, using the frozen implementation and the actual journal CONFIG, before COLLECTOR_START.

Therefore the timing is not inherently circular if these are treated as two distinct tests. The two-stage reading is supported by the text; the earlier statement that it was not explicit should be narrowed.

The remaining specification gaps are narrower:
1. B.7(4)/D25 do not state which code must run in the pre-lock rehearsal or whether its source hash is required.
2. They do not define which parts of the pre-lock configuration must match the final ten-key CONFIG, beyond using the same selected destination and test namespace.
3. They do not define which Stage A evidence can be reused and which Stage B checks must be repeated.
4. They do not state the invalidation rule if the destination, operator, namespaces, receipt method, or read client changes between stages.

**Updated review position:** keep the two-stage interpretation, but request normative detail for the four points above. D25 remains unpassed because neither the pre-lock rehearsal nor the post-lock E2E evidence exists. This correction does not change the protocol and does not authorize any live target request.
