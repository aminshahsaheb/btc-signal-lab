# SEALED package: expected outputs of the handoff (stage 2 only)

DO NOT give this package to the author of the independent verifier before the author's code SHA and the digest of the author's stage-1 outputs have been recorded.

* `expected/<id>.json`: for each input of the blind package, the twelve report keys of contract 8.2 (`verdict`, `findings`, `hard`, `soft`, `n_events`, `head_hex`, `slots`, `missing`, `outcomes`, `candles`, `replayed`, `analysis_eligible`), or
  `{"unsupported_journal": true}` for the capability-boundary input B01. In `findings`, a `null` detail means "not compared" (see INTERFACE.md section 6 of the blind package).
* `SOURCE_PINS.txt`: where the values come from.

**Provenance, to be stated whenever these files are mentioned.** The nine keys `verdict`, `findings`, `hard`, `soft`, `slots`, `missing`, `candles`, `replayed`, `analysis_eligible` are the hand-written expectations (`expect.json`) of the conformance vectors; `n_events`, `head_hex` and `outcomes`
are the values of `vectors/EXPECT_DERIVED.json`, produced by the oracle of the same author. All of it was written by the author of the contract text, the vectors, the oracle and the primary verifier. It is NOT an independent oracle, and agreement with it is not independent
verification. The independent evidence of this exercise is the DISAGREEMENTS that the author's code and these expectations reveal, each settled against the contract text.
