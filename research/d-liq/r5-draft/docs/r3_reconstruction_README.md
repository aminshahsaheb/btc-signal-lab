# D-LIQ journal r3-reconstruction

**r3-reconstruction، نه r3.1، قفل‌نشده**

This is a source-only reconstruction derived from the supplied r3 audit package and reviewed against the separately supplied r3.1 candidate archive. It is not a claim of byte-for-byte provenance, equivalence beyond the listed fixtures, or lock readiness. The r3 protocol and source archive were not rewritten here.

The change binds each OUTCOME to a VALID SLOT. The writer refuses an OUTCOME attached to a non-VALID SLOT, and the primary and partially independent verifier report hard finding `OUTCOME_FOR_NONE_SLOT`. `verify_indep_as_delivered.py` preserves the unmodified delivered verifier for the regression comparison.

All included tests use synthetic journals and mock anchors. No live exchange messages, market-return claims, collector, T0, probe, external service, or raw market dataset is included. No ZIP archive is committed. This project has no license file; public visibility does not grant reuse or redistribution rights.

The partially independent verifier is not fully independent: it shares a model family, uses the Claude-built corpus, and its implementation was written by a subagent. Both verifier outputs still require external review.

## Owner decisions recorded

- OPEN-22 has no hard time cap for anchoring OUTCOME coverage. The eventual collector should checkpoint immediately after each OUTCOME, measure and report coverage lag, and write a final drain checkpoint. A prolonged anchor outage makes the run inconclusive; rows must not disappear silently. A drain window can be considered later.
- Per-OUTCOME coverage status belongs in the verifier report as well as the builder. This draft implements the NONE-SLOT hard finding only; it does not add the broader coverage-report field or implement r4. The owner will build that work on this reconstruction.

## Reproduction

Run from this directory with Python 3:

```sh
python3 -I src/test_dliq_journal_v2.py
python3 -I indep_verifier/test_indep.py
python3 -I src/test_dliq_msg_contract_v1.py
python3 -I tests/test_none_slot_regressions.py
for seed in 11 12 13 14; do python3 -I src/diff_test_verifiers.py indep_verifier 30000 "$seed"; done
```

The tests establish behavior on these synthetic fixtures only. They do not certify production readiness or r4.
