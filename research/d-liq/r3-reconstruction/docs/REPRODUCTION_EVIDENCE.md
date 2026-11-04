# Reconstruction verification record

Date: 2026-11-05. All commands below were run on the r3-derived reconstruction tree. Tests use synthetic journals, local mock anchors, or synthetic message fixtures.

## Baseline and source provenance

- Supplied r3 archive SHA-256: `0431fb5431810f4f98bbbffe44534c98f0b388f8fd6f2ad14569a1ec27e1b529`.
- Supplied r3.1 candidate archive SHA-256: `4d3faaae13e0263ac1f422a3b6d88904d70057b4bb5271029c1ce5cc9d194ec2`.
- The initial r3 patch SHA was `aba55b12172325d89bd5b43345cdf3cfdc07edf197a4ee6817b6559c1e5b24ce`. After code review, the primary verifier and differential harness were aligned to the candidate implementation; README and verifier docstrings were also qualified. The committed tree is therefore identified by its own `MANIFEST.sha256`, not that earlier patch hash.
- The original r3 protocol and original package manifest were not edited. The consistency suite's hash-table check consequently reports the five expected source/hash mismatches (writer, primary verifier, primary test, second verifier, second-verifier test). The suite result was **16 checks, 1 failed**; every other parameter/constant check passed. The versioned amendment and reconstruction manifest record the new files without rewriting the archived protocol.
- Candidate archive manifest audit: all 104 file records in its `MANIFEST.json` matched their archive contents, but the top-level `n_files` field says 94. This is an internal count mismatch in the supplied candidate metadata; it is not copied into this reconstruction.

## Test results

Commands and results on the reconstructed files:

- `python3 -I test_dliq_analysis_v1.py` from the clean r3 extraction: exit 0; all tests passed (27 PASS cases).
- `python3 -I test_dliq_bootstrap_discard_v1.py`: exit 0; 12 checks, 0 failures.
- `python3 -I test_dliq_control_v1.py`: exit 0; 45 checks passed.
- `python3 -I test_dliq_msg_contract_v1.py`: exit 0; 59 checks, 0 failures.
- `python3 -I test_dliq_journal_v2.py`: exit 0; 199 checks, 0 failed.
- `python3 -I test_indep.py`: exit 0; 93 tests, OK.
- `python3 -I tests/test_none_slot_regressions.py`: exit 0; 2 tests, OK. It covers the line-4 NONE-slot case and a mixed sequence with a clean VALID outcome plus an adversarial NONE-slot outcome.
- `python3 -I diff_test_verifiers.py indep_verifier 30000 <seed>`: four seeds 11–14; each compared 30,084 synthetic journals with 0 disagreements. Runtimes were 20.293 s, 21.481 s, 19.414 s, and 19.454 s. `OUTCOME_FOR_NONE_SLOT` appeared in 638, 645, 639, and 636 journals respectively. `SLOT_MISMATCH` was never exercised because replay remains out of scope for this verifier.

The journal/writer, partially independent verifier, mixed regression, and message-contract suites are run by the included GitHub Actions workflow. The earlier full r3 consistency suite is not included in CI because its immutable historical hash table must differ for a reconstruction.

## Actual-report fixture comparison

The two journal/report fixtures in PR #15's file `research/d-liq/r3-tools/fixtures/r3_1_actual_verifier_fixtures.json.gz` were fetched at PR #15 head `4faa7393f4293417b7d4e1bd8e334a57bb088334`. The reconstruction's primary and partially independent reports matched the stored `findings`, `hard`, `head_hex`, `missing`, `n_events`, `slots`, `soft`, and `verdict` fields for both `anchored_outcome` and `unanchored_outcome_tail` (four report comparisons total). Conclusion: **matches r3.1 on these two fixture cases only**.

The fixture did not contain separate anchor-file bytes, so a local mock anchor was reconstructed from each checkpoint receipt embedded in the fixture journal. Verification time was the maximum `rec_ms` in the fixture journal: `1793016300200`. This is an explicit fixture-comparison assumption, not evidence of external anchoring.

A fresh anchored NONE-slot/OUTCOME journal was also checked. The checked writer refused the OUTCOME; the primary and partially independent verifier returned FAIL with `OUTCOME_FOR_NONE_SLOT` at line 4. The preserved as-delivered verifier did not report the new finding (PASS on this isolated case). In the mixed-slot test, the valid outcome did not receive `OUTCOME_FOR_NONE_SLOT`; only the NONE-slot outcome was flagged.

## Source hashes

The writer hash matches the supplied candidate table. The final verifier hashes are recorded in `MANIFEST.sha256`; primary and second-verifier comment headers were qualified to call the latter partially independent, so their final hashes differ from the candidate's table. These are source identity values, not equivalence claims.

## Claims not made

No complete r3.1 equivalence, r4 result, collector readiness, live probe, T0, real-message validation, trading edge, or production readiness is claimed. The repository PR is draft and requires external review.
