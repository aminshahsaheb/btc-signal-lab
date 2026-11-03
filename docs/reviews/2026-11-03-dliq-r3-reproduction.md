# D-LIQ r3 reproduction and decision review — 2026-11-03

## Scope

This is an independent local reproduction of the delivered r3 audit package and a review note for OPEN-17/18/21 and anchor selection. It is not a live-feed test, a protocol lock, or a market-result analysis.

## Source identity

- Package: `dliq_r3_audit_package.zip`
- Package SHA-256: `0431fb5431810f4f98bbbffe44534c98f0b388f8fd6f2ad14569a1ec27e1b529`
- Normative r3 draft SHA-256: `449753f9c74bc3d5b41313664f062b50948104906042197f1ed61bacb886df8d`
- Environment: Python 3.13.5, Linux x86_64.
- The package manifest passed after clean extraction.

## Reproduced test suites

Commands were run from the extracted package:

```bash
cd src
python3 -I test_dliq_analysis_v1.py
python3 -I test_dliq_bootstrap_discard_v1.py
python3 -I test_dliq_control_v1.py
python3 -I test_dliq_msg_contract_v1.py
python3 -I test_dliq_journal_v2.py
python3 -I test_r3_consistency.py
cd ../indep_verifier
python3 -I test_indep.py
```

| Suite | Result |
|---|---:|
| Analysis engine | 27 passed |
| Bootstrap discard | 12 passed |
| Prior-return control | 45 passed |
| Message contract | 59 passed |
| Journal v2 | 197 passed |
| r3 consistency | 16 passed |
| Independent verifier | 92 passed |

## Differential verifier reproduction

Commands:

```bash
cd src
python3 -I diff_test_verifiers.py ../indep_verifier 30000 11
python3 -I diff_test_verifiers.py ../indep_verifier 30000 12
```

- Seed 11: 30,081 journals, zero disagreements.
- Seed 12: 30,081 journals, zero disagreements.
- Seed 13 exceeded the 120-second execution limit in this environment.
- Seed 14 was not rerun in this pass.
- The package-supplied log records seeds 11–14, 120,324 comparisons, zero disagreements. That result remains package-supplied evidence; it was not fully re-executed here.
- `SLOT_MISMATCH` remains unexercised by the differential harness.

## Missingness calibration

The supplied synthetic calibration summary was regenerated from the shipped raw CSVs.

| Scenario | True theta | Coverage | P(PASS) |
|---|---:|---:|---:|
| S0 baseline | 10 bps | 0.951 | 0.050 |
| S10: 5% of losing outcomes missing | 10 bps | 0.823 | 0.177 |
| S0 baseline | 20 bps | 0.948 | 0.926 |
| S10: 5% of losing outcomes missing | 20 bps | 0.799 | 0.984 |

S10 has an overall NO_PRICE share near 2.1–2.3%, so the current 5% guard does not fire. The synthetic mechanism raises false-PASS at true theta=10 from 5.0% to 17.7%.

The proposed fixed 100 bps allowance reduces S10 P(PASS) at theta=10 to 0.059 in the supplied sensitivity analysis, but it also reduces power in the benign S8 theta=20 case from 0.926 to 0.816. This supports rejecting the fixed allowance as mechanism-tuned. It does not identify a universally valid correction for MNAR.

## Decision recommendations — not adopted / not a lock

- **OPEN-21:** Reject the fixed `c=100 bps` allowance. Do not silently impute missing returns. Before any confirmatory PASS, require a dated, pre-registered missingness policy with calibration under multiple MNAR mechanisms. A stricter `N_noprice=0` gate is a conservative candidate, but it changes the protocol and requires explicit approval.
- **OPEN-17:** Keep the current proposed guards unchanged: each side × prior-sign cell >=30; NO_CTRL <=5%; stratified one-sided lower bound >0; only `LIQ_INCREMENTAL` opens the next stage.
- **OPEN-18:** Keep the proposed 5% unanchored cap; above it, INCONCLUSIVE.
- **OPEN-14:** Prefer the D-LIQ journal v2 contract for the r3 candidate until Forward Journal r7 has its own KAT harness and D25 end-to-end evidence.
- **No lock:** These recommendations require a dated decision record. r3 remains DRAFT / NOT LOCKED.

## Anchor research

RFC 3161 is the preferred candidate class because its signed token can contain UTC `genTime` and an explicit `accuracy` bound. The protocol defines how to derive an upper time bound from `genTime + accuracy`; the client must verify the token signature, message imprint, nonce/timeliness, and policy.

- RFC 3161 standard: https://www.rfc-editor.org/rfc/rfc3161.html
- DigiCert documents an RFC 3161 TSA at `http://timestamp.digicert.com`: https://knowledge.digicert.com/general-information/rfc3161-compliant-time-stamp-authority-server
- Sectigo documents `http://timestamp.sectigo.com/rfc3161`, but its CPS states an intended use for software signing; do not select it until terms permit this research use: https://www.sectigo.com/uploads/files/Sectigo_CS_CPS_v1_0_0.pdf
- OpenTimestamps/Bitcoin is an asynchronous, independently verifiable proof-of-existence option. It is not suitable as the sole anchor for a strict <5-minute per-SLOT deadline; it may be a secondary archive anchor: https://www.ietf.org/archive/id/draft-fassbender-scitt-time-anchor-07.html

No provider or host is selected. No live anchor request was made. Any future format-only test must use a synthetic hash and must verify the exact token, explicit accuracy bound, certificate chain, policy, nonce, and endpoint reachability from the intended host.

## Additional contract finding — OUTCOME for a NONE SLOT

A synthetic adversarial journal was constructed with a `SLOT(status=NONE)`, a valid checkpoint, and a later `OUTCOME(status=NO_PRICE)` for the same tau.

- The primary r3 journal verifier returned `PASS`.
- The independent verifier also returned `PASS`.
- Both reported only the expected soft `TAIL_UNANCHORED` finding.
- This violates the r3 A.6 mapping: a NONE signal must remain NONE and must not have an OUTCOME.

A fail-closed guard and regression test were added to the draft builder in PR #15 (`BUILDER_OUTCOME_FOR_NONE_SLOT`). This is only a mitigation at the analysis-builder layer. The normative writer and both verifiers must also reject this event sequence, and their differential harness must include it, before r3 can be locked.

## Remaining blockers

- Patch the normative writer and both verifiers to reject OUTCOME linked to a NONE SLOT; add a differential mutation test.
- Third-party review of the verifier and builder.
- Complete independent differential run for seeds 13 and 14 in a sufficiently provisioned environment.
- Exercise replay-based `SLOT_MISMATCH`.
- Resolve OPEN-17/18/21 and OPEN-14 in a dated decision record.
- Approve and perform the bounded real Binance message-format dry run.
- Select and test a real anchor and collector host.
- Resolve the missingness failure before any confirmatory claim.
- No T0, collector, market scoring, or strategy use before a separate lock decision.

## Remediation test results — patched local candidate

The local package copy was patched to reject an OUTCOME linked to a SLOT whose status is not VALID. The writer now refuses this event; both verifiers emit the hard finding OUTCOME_FOR_NONE_SLOT. The differential corpus includes a fully anchored adversarial fixture for this case.

- Writer/journal suite: 198 checks, zero failures.
- Independent verifier suite: 92 tests passed.
- Differential seeds 11, 12, 13, and 14: 30,084 journals per seed, zero disagreements (120,336 total).
- Direct adversarial test: writer refused the event; both verifiers returned FAIL with the expected hard finding.
- OUTCOME_FOR_NONE_SLOT was exercised by the differential corpus.
- SLOT_MISMATCH remains unexercised.

These results apply to a local patched candidate, not the original package. The source changes alter three component hashes. The r3 consistency check therefore reports hash mismatches until a new immutable candidate is created and its protocol component table and manifest are regenerated. Do not reuse the original package hash. The patch is not merged into the normative package.

The tested remediation is recorded in PR #15 comments. The builder guard in this PR is defense in depth; it does not replace the writer/verifier fix.
