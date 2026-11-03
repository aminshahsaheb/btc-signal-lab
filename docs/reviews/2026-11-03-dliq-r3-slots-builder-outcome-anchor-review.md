# D-LIQ r3.1 slots builder — outcome anchoring review

Review date: 2026-11-03  
PR: #15 — `research/dliq-r3-slots-builder-draft`  
Reviewed branch head before this note: `af125b4f110805f951684a42203f52d07453951d`  
Disposition: **FINDING REPRODUCED; CANDIDATE REMEDIATION IMPLEMENTED; INDEPENDENT REVIEW REQUIRED**

## Finding: the builder can emit EVAL from an OUTCOME outside the anchored journal prefix

The builder gates each `SLOT` using the verifier's per-slot anchor map. When the slot is `OK`, it reads `OUTCOME` by `tau` and can emit `EVAL` or `NO_PRICE`. It does not check whether that `OUTCOME` entry itself is covered by a valid external checkpoint.

The verifier's informational `TAIL_UNANCHORED` finding is not used by the builder. The builder report schema also has no per-outcome anchoring state or verified anchored-prefix field.

This is material because the r3 journal contract says events after the last `CHECKPOINT` are not externally confirmed (`TAIL_UNANCHORED`). A validly anchored SLOT does not make a later OUTCOME externally anchored.

## Direct evidence in the current test fixture

In `test_build_slots_v1.py`, `base_events()` creates this order when `outcome="EVAL"`:

1. `SESSION` — seq 1
2. Two prior `CANDLE` events — seq 2 and 3
3. `SLOT` — seq 4
4. `CHECKPOINT` with `anchored_seq = 4) — seq 5
5. Forward `CANDLE` events — seq 6 and 7
6. `OUTCOME` — seq 8

The checkpoint covers only through seq 4. The OUTCOME is seq 8, so it is outside the anchored prefix shown by the fixture. Nevertheless, `test_eval_and_prior_sign` expects the builder to return:

```python
[[0, "EVAL", 1, "98.522"]]
```

The synthetic verifier reports only `slots={"0":"OK"}`, with no hard findings. The test therefore certifies the exact unsafe path described above.

## Impact

An outcome that is present in the local journal but not covered by a valid external checkpoint can enter the analysis CSV as EVAL. If that tail is later edited, removed, or replaced before anchoring, the resulting analysis row is not protected by the external evidence contract.

This can contaminate the statistical input while `registry_ok` remains true. It is not a harmless reporting omission.

## Required remediation before merge

1. Define the outcome-anchoring rule against the exact r3.1 protocol and verifier contract. Do not infer it from SLOT status.
2. Make the authoritative verifier expose enough validated information for the builder to determine whether each OUTCOME is covered by a valid checkpoint. Prefer a per-outcome status or a validated anchored-prefix/coverage map. Do not trust raw `anchored_seq` values without verifier validation.
3. The builder must fail closed or refuse EVAL/NO_PRICE when an OUTCOME is outside verified anchor coverage. Keep the SLOT anchor state and OUTCOME anchor state separate.
4. Add a negative test matching the current fixture: SLOT is OK, checkpoint covers SLOT, OUTCOME occurs after the checkpoint, and no later checkpoint covers the OUTCOME. Expected result: no EVAL/NO_PRICE row and no analysis CSV.
5. Add a positive paired test where a later valid checkpoint covers the OUTCOME. Only then may the row become EVAL/NO_PRICE.
6. Test a malformed, conflicting, duplicated, or invalid later checkpoint. It must not make the OUTCOME eligible.
7. Integrate with the exact primary and independent verifier executables and their real output schema. Synthetic hand-written reports are not enough to close this gate.

## Scope

- This is a source/test review only.
- No protocol file or builder code was changed.
- No live exchange or anchor request was made.
- No market outcome was scored; no T0 or collector was started.
- PR #15 remains DRAFT / NOT MERGED.

## Candidate remediation recorded after the finding

At candidate head `2df9813ba0a96b15e1694330cbffe5eb6a083774`, the builder was changed to:
- derive the maximum `anchored_seq` from CHECKPOINT events;
- reject impossible checkpoint coverage where `anchored_seq` is not an integer, is boolean, is negative, or is not earlier than its CHECKPOINT event;
- keep an otherwise valid SLOT in `PENDING` when its OUTCOME sequence is beyond the checkpoint-covered prefix;
- require a later checkpoint to cover the OUTCOME before emitting EVAL or NO_PRICE;
- reject boolean values where integer sequence/tau/side fields are required.

Tests now cover:
- the original unsafe case (SLOT checkpointed, later OUTCOME not checkpointed) → PENDING;
- a positive case where a later checkpoint covers the OUTCOME → EVAL/NO_PRICE;
- an impossible future checkpoint sequence → hard builder finding;
- a missing-grid fixture with valid checkpoint sequence references.

GitHub Actions run #194 passed on exact head `2df9813ba0a96b15e1694330cbffe5eb6a083774`, including the builder tests and full repository integrity check.

**Important limit:** this is candidate remediation, not independent acceptance. The builder still relies on both real verifier reports to establish that checkpoint receipts, hashes, and ordering are valid. The synthetic tests do not prove that integration. Exact primary/independent verifier executable outputs and their provenance remain a merge gate. Do not merge until an independent reviewer checks the implementation and the report schema against the immutable r3.1 candidate.
