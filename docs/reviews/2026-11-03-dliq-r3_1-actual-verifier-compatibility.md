# D-LIQ r3.1 candidate — actual verifier compatibility review

Review date: 2026-11-03  
Repository workstream: PR #15 (`research/dliq-r3-slots-builder-draft`)  
Disposition: **COMPATIBILITY PROBE PASSED; BUILDER CONFORMANCE NOT ESTABLISHED; PR REMAINS DRAFT**

## 1. Immutable input identity

- Supplied archive: `dliq_r3_1_candidate.zip`
- Archive SHA-256: `4d3faaae13e0263ac1f422a3b6d88904d70057b4bb5271029c1ce5cc9d194ec2`
- Candidate protocol SHA-256: `5c05a15de7addd55cade7617fcdcaea570aad82b61c0b16c95d14024fc649948`
- Original r3 protocol SHA-256: `449753f9c74bc3d5b41313664f062b50948104906042197f1ed61bacb886df8d`
- Manifest: all entries passed `sha256sum -c MANIFEST.sha256`.

The candidate archive contains the writer, primary verifier, independent verifier, verifier tests, journal contract, calibration records, and reproduction logs. This closes the earlier *file-availability* gap. It does not close real-feed, anchor, collector, or protocol-lock gates.

## 2. Reproduction performed in this review

The following suites were run from the extracted candidate archive with Python 3.13:

| Suite | Observed result |
|---|---:|
| Analysis engine | 27 passed |
| Bootstrap discard | 12 checks, 0 failures |
| Prior-return control | 45 passed |
| Message contract | 59 checks, 0 failures |
| Journal writer / primary verifier | 199 checks, 0 failures |
| Independent verifier | 93 tests, OK |
| r3 consistency | 16 checks, 0 failures |
| Manifest | all entries OK |

Differential verifier reproduction in this review: seed 11 completed with 30,084 journals and zero disagreements. A combined attempt to run seeds 11–14 exceeded the 300-second execution limit during seed 12. The archive's supplied reproduction record reports seeds 11–14, 30,084 journals each, zero disagreements (120,336 total); that complete four-seed result is package-supplied evidence, not a complete four-seed rerun in this review.

The seed-11 finding coverage included `OUTCOME_FOR_NONE_SLOT` in 638 generated journals. `SLOT_MISMATCH` was not exercised; replay-based verification remains a separate gap.

## 3. Actual verifier output-contract probe

A fresh synthetic journal was created with the candidate writer and local `MockAnchor`. The primary verifier and independent verifier were then called directly against the same journal and anchor. Their reports were serialized to JSON and read back.

Observed output:

- Primary verifier: `PASS`, no hard findings, slot map `{1793001600000: "OK"}`, 7 events.
- Independent verifier: `PASS`, no hard findings, same slot map, same 7 events.
- Both reports had exactly the keys expected by the builder: `verdict`, `findings`, `hard`, `soft`, `n_events`, `head_hex`, `slots`, `missing`.
- Journal head and event count matched exactly.
- Slot maps and missing-grid lists matched exactly.
- Hard-finding lists matched exactly.
- JSON round-trip passed for both reports.

This establishes that the **actual candidate verifier functions produce the report shape and shared journal identity expected by the builder** for this clean synthetic case. It is not an end-to-end execution of `build_slots_v1.py` against these actual reports. The PR's current builder tests still use synthetic verifier-report fixtures. Do not describe actual Builder/verifier integration as passed.

## 4. Normative boundary: OUTCOME anchoring

The candidate protocol A.6 states that an `OUTCOME` must be recorded only after a checkpoint that covers the `SLOT` for the same `tau`. The writer and both verifiers enforce this by requiring a checkpoint between the `SLOT` and its `OUTCOME` that covers the `SLOT`.

The current PR #15 builder adds another condition: it treats an `OUTCOME` as pending unless a checkpoint also covers the `OUTCOME` event itself (`outcome_seq <= max_checkpoint_anchored_seq`). This is stricter than the literal A.6 wording and stricter than the verifier's reported `OUTCOME_BEFORE_ANCHOR` rule.

A.6 does not clearly state that the `OUTCOME` event itself must be covered by a later checkpoint before it can enter `slots.csv`. This may be a prudent fail-closed policy, but it is not established as a normative requirement by the current text. Do not silently call this protocol conformance.

**Required owner decision:** either (a) retain the stricter builder rule and adopt an explicit dated protocol clarification that an `OUTCOME` must itself be checkpoint-covered before analysis, or (b) align the builder with the current A.6 wording and define how an unanchored journal tail affects analysis integrity. Until that decision exists, this gate remains OPEN.

## 5. PR #15 disposition

| Gate | Status |
|---|---|
| Candidate archive identity | PASS |
| Candidate manifest integrity | PASS |
| Candidate writer / verifier unit suites | PASS |
| Independent verifier unit suite | PASS |
| Four-seed differential reproduction | PACKAGE-SUPPLIED; only seed 11 rerun here |
| Actual verifier report-shape compatibility | PASS for one clean synthetic journal |
| Builder run against actual verifier outputs | NOT RUN |
| Builder OUTCOME checkpoint policy vs A.6 | OPEN — owner decision required |
| Replay-based `SLOT_MISMATCH` differential coverage | OPEN |
| Independent third-party review | NOT PRESENT |
| Real Binance / anchor / collector evidence | BLOCKED / NOT AUTHORIZED |
| Protocol lock / T0 / strategy scoring | NOT AUTHORIZED |

PR #15 must remain DRAFT and unmerged. The candidate package resolves the missing-source problem, but it does not justify merging the Builder or locking r3.1.

## 6. Safety boundary

All checks above use synthetic journals and a local mock anchor. No exchange connection, external anchor request, collector, T0, market outcome scoring, or strategy evaluation was performed.
