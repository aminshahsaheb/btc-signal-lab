# C3 NONE-slot / OUTCOME verification — 2026-11-04

## Exact package identity

- Candidate archive: `dliq_r3_1_candidate.zip`, 2,455,000 bytes, SHA-256 `4d3faaae13e0263ac1f422a3b6d88904d70057b4bb5271029c1ce5cc9d194ec2`.
- Candidate protocol: `protocol/PREREG_D-LIQ-SNAPSHOT-CONT4H-v1_r3_DRAFT.md`, SHA-256 `5c05a15de7addd55cade7617fcdcaea570aad82b61c0b16c95d14024fc649948`.
- Original r3 protocol: SHA-256 `449753f9c74bc3d5b41313664f062b50948104906042197f1ed61bacb886df8d`.
- Candidate `MANIFEST.sha256`: all entries verified with `sha256sum -c MANIFEST.sha256`.
- The candidate ZIP is retained in the user's controlled Library archive, not committed as a binary Git blob. The exact archive hash is recorded above. The repository does not contain the ZIP bytes.

## Source identity inside the candidate

| Component | Path | SHA-256 |
|---|---|---|
| Writer | `src/dliq_journal_v2.py` | `51f0996f815466cb977bd46a6e5891b1f20f7fe42dc8de5cfcc494d54c59d06f` |
| Primary verifier | `src/dliq_journal_verify_v2.py` | `816f8d9fd37cc3cfa9001badc6af5a9a69ed025f41ba32a4e5be4b4ef9cbffa5` |
| Active independent verifier | `indep_verifier/verify_indep.py` | `f967c77c825f278961ab361a2d844a561d886c14a57c51938901d87bc84b0650` |
| Preserved original independent verifier | `indep_verifier/verify_indep_as_delivered.py` | `e4ba6e57e2d524c0b109c03467395e41dced6b232419ece06bb69efdc8bdd033` |

## Direct adversarial check

A synthetic journal was constructed with this exact order:

1. SESSION.
2. SLOT with `status=NONE`.
3. A valid CHECKPOINT covering that SLOT.
4. OUTCOME with `status=NO_PRICE`, deliberately appended through the unchecked test path to create the forbidden journal.

Observed results:

| Component | Result |
|---|---|
| Writer normal append guard | Refused the OUTCOME with `JournalError` |
| Primary verifier | `FAIL`, hard finding `OUTCOME_FOR_NONE_SLOT` at line 4 |
| Active r3.1 independent verifier | `FAIL`, hard finding `OUTCOME_FOR_NONE_SLOT` at line 4 |
| Preserved `verify_indep_as_delivered.py` | `PASS`, no hard finding |

The last row is intentional provenance evidence: the original delivered independent verifier did not contain this r3.1 rule. The r3.1 candidate preserves that original file for comparison and ships the corrected active `verify_indep.py`. Do not mistake the preserved baseline file for the active candidate verifier. This also confirms why the r3.1 change is needed.

## Test evidence executed in this pass

- Writer + primary verifier suite: 199 checks, 0 failed.
- Active independent verifier suite: 93 tests, all passed.
- r3 consistency suite: 16 checks, 0 failed; candidate protocol hash and component hash table match.
- Differential harness, seed 11, 3,000 random mutations plus 84 hand-built baseline/time checks: 3,084 journal comparisons, 0 disagreements.
- `OUTCOME_FOR_NONE_SLOT` was observed in 64 mutated journals in the seed-11 run.
- A separate base-corpus-only run compared 84 journals and found 0 disagreements.
- The full `REPRODUCE.sh` run completed package integrity, analysis (27), discard (12), control (45), message contract (59), writer/primary (199), and independent verifier (93) checks, then exceeded the execution time limit during the full four-seed differential phase. The full 120,336-journal differential result remains a package-reported result, not a complete rerun in this pass.

## C3 disposition

- [x] Candidate writer refuses OUTCOME for a NONE SLOT.
- [x] Primary and active independent verifiers both return hard `OUTCOME_FOR_NONE_SLOT`.
- [x] Negative regression coverage exists in writer/primary tests, active independent tests, and the differential corpus; direct synthetic check also passed.
- [x] The project-level rule that the OUTCOME itself must be checkpoint-covered remains a stricter Builder acceptance rule.
- [x] The distinction between Builder policy and immutable r3.1 protocol text is documented.
- [ ] No protocol amendment is being made. The conditional amendment workflow (new version, hash, manifest, tests, and owner decision) is not applicable unless the protocol owner later chooses to amend r3.1.

**C3 = 5/6 complete; item 6 is conditional and currently N/A.** The package remains DRAFT / NOT LOCKED. This evidence does not authorize a collector, T0, outcome scoring, or live use.
