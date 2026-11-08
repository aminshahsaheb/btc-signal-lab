# PROPOSED protocol text — OPEN-21 and LIQ_INCREMENTAL (GPT orders 5 and 6)

STATUS: **PROPOSED. Not adopted. Not part of any protocol until the owner dates and approves it and an independent review has read it.** This file records wording only. It changes no code, no threshold and no result, and it authorizes nothing (no collector, T0, probe, scoring or trading action).

Origin: wording drafted by GPT in its audit of 2026-11-07 (sections F1 and F2), recorded here verbatim; the review notes below are Claude's.

Integration target: the r3 protocol / analysis text. **That text is not in this repository** (`research/d-liq/r4-draft/README.md`, rows 5 and 6: "protocol/analysis text is outside this base"; the older `PREREG_D-LIQ-SNAPSHOT-CONT4H-v1_r1_DRAFT.md` here does not use either term). The wording below is therefore kept as a stand-alone amendment proposal until the r3 protocol files are on `main` (see `docs/ROADMAP.md`, D-PR-15-23), and must then be inserted as it stands or with a dated change.

## F1 — OPEN-21 (order 5)

```
OPEN-21 STATUS: NOT ADOPTED.

No missingness allowance, correction, or exclusion rule
is approved for the primary or confirmatory analysis.

All simulations and sensitivity analyses involving
outcome-dependent or volatility-dependent missingness,
including S10, are sensitivity analysis only.

These analyses MUST be reported separately.

They MUST NOT:
- change the primary sample;
- change the primary estimator;
- change thresholds or stopping rules;
- restore a failed or inconclusive result to PASS;
- justify treating missing outcomes as ignorable.

Required missing outcomes MUST continue to follow
the current preregistered missingness policy.

Any future adoption requires:
1. a dated protocol amendment;
2. a complete specification of the mechanism;
3. preregistration before access to new outcome data;
4. independent review;
5. new tests for the primary and stratified estimators.

Until those conditions are met, OPEN-21 remains
unapproved and sensitivity-analysis only.
```

## F2 — LIQ_INCREMENTAL (order 6)

```
LIQ_INCREMENTAL INTERPRETATION:

A positive LIQ_INCREMENTAL value is a positive
conditional estimate under the limited prior_sign
control specified in this protocol.

It is a conditional statistical estimate.

It is NOT:
- a causal estimate of liquidation-flow impact;
- proof of a causal mechanism;
- proof of incremental predictive value beyond
  all relevant confounders and selection effects;
- evidence of a tradable edge;
- evidence of profitability;
- evidence of positive net returns after execution costs.

The estimate MUST be interpreted only within
the preregistered sample, estimator, uncertainty,
missingness, and multiple-testing controls.

LIQ_INCREMENTAL MUST NOT be described as a causal
effect or used as a trading signal by itself.
```

## Review notes (Claude; for GPT and the owner to confirm or reject)

1. **Consistent with the recorded evidence.** Synthetic S10 (docs/STATUS.md, "Update 2026-11-06" and the 2026-11-05 list) showed the false-PASS rate rising from 0.050 to 0.177 when 5 % of losing outcomes were missing, and the 2026-11-03 decision records that the OPEN-21 allowance was not adopted. F1 states exactly that and goes no further.
2. **F1 refers to "the current preregistered missingness policy".** That policy text is in the missing r3 protocol, not here. Until it is on `main`, this sentence cannot be checked and is marked `[VERIFY against the r3 protocol]`. F1 must not be inserted into a document in which that policy is absent.
3. **F1 item 3 ("preregistration before access to new outcome data")** is the same discipline the r4 builder enforces mechanically (`analysis_eligible` is false until the replay conditions hold). The wording does not conflict with the r4/r5 code.
4. **F2 "limited prior_sign control"** must name the same control as the estimator specification. Because the estimator text is not in this repository, the term is `[VERIFY against the r3 analysis plan]`.
5. **F2 is an interpretation rule, not a pass criterion.** It adds no threshold. It narrows how a result may be described; it cannot make a failed gate pass.
6. Neither text is evidence of anything about the market. They only restrict claims.

Open decisions: D-DLIQ-OPEN in `docs/ROADMAP.md` (owner); independent review of the integrated text (GPT, human reviewer).
