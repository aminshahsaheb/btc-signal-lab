# Reconstruction amendment v1: OUTCOME requires a VALID SLOT

Status: draft; r3-reconstruction; unlocked. This amendment supplements the preserved r3 contract and does not edit the r3 protocol or its archived manifest.

For each journal OUTCOME, the verifier resolves the first preceding SLOT for the same `tau_ms`. If that SLOT is absent, the existing orphan rule applies. If the reference SLOT exists and its status is not `VALID`, the verifier emits hard finding `OUTCOME_FOR_NONE_SLOT` at the OUTCOME line and the journal verdict is `FAIL`. The journal writer also refuses to append such an OUTCOME. A SLOT with status `NONE` cannot be converted into an outcome row by `NO_PRICE`.

The primary and partially independent verifier implement the rule. The second verifier is partially independent: it shares a model family, uses a Claude-built corpus, and was written by a subagent. The preserved `verify_indep_as_delivered.py` is the unmodified r3 verifier and is retained to demonstrate the prior behavior on the adversarial synthetic journal.

## Regression evidence

The synthetic regression writes SESSION, an anchored NONE SLOT, and an unchecked adversarial OUTCOME. The checked writer refuses the OUTCOME. The modified primary and partially independent verifier fail with `OUTCOME_FOR_NONE_SLOT` at line 4. The preserved as-delivered verifier does not emit the new finding. A second mixed-slot test puts a NONE SLOT first, then a VALID SLOT with a clean outcome, then an adversarial outcome for the NONE slot; the valid outcome is not falsely flagged and the NONE outcome is hard.

## Owner-set policies and remaining work

OPEN-22 has no hard delay ceiling. The intended collector policy is an immediate checkpoint after every OUTCOME, a reported coverage-lag distribution, and a final drain checkpoint. Prolonged anchor outage means INCONCLUSIVE; rows are not silently dropped. No collector or live behavior is implemented here.

The owner selected per-OUTCOME coverage status in the verifier report, not builder-only. That broader report field, its contract definition, and r4 implementation are intentionally outside this amendment; the owner will build them on this reconstruction.

All evidence in this draft is synthetic. No probe, T0, collector, market data, or production claim is included.
