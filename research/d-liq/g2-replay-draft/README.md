# D-LIQ G-2 draft, second half — candidate independent SLOT replay (clean-room, spec-only) and its differential check

STATUS: **DRAFT.** A candidate for the "independent SLOT replay" of GPT's order 4. **Not reviewed. Not adopted.** It does not change `REQUIRE_INDEPENDENT_REPLAY` in the builder, does not make any journal `analysis_eligible`, and is not evidence about any market. Synthetic fixtures only. No collector/T0/probe/live/edge claim.

## What it is
- `src/replay_indep.py` (509 lines): a second implementation of the SLOT replay (contract section 7) plus the message classification it needs. Written by a separate agent session from the specification files in `SPEC_INPUTS.txt` ONLY (it was not given the author's code). Delivered unchanged here (hash in `MANIFEST.sha256`).
- `src/test_replay_indep.py`: its own 188 tests, expected values derived by hand from the specification (10 are marked KNOWN_AMBIGUOUS: the specification does not force the reading; they pass under the reading its author chose).
- `src/test_replay_indep_supplement.py`: 3 supplementary tests written afterwards by the integrating author (Claude, who had seen the code) to close two gaps found by the mutation check below. Not part of the clean-room delivery.
- `tools/diff_replay.py`: differential harness, independent replay vs the author's verifier (`verify(..., replay_slots=True)`) over random synthetic journals: honest SLOT must reproduce field by field; a tampered SLOT field must give SLOT_MISMATCH with the same field list in both; a SLOT before tau+10 s must give SLOT_EARLY_WRITE in both.
- `tools/mutate_indep.py` + `tools/mutants_reviewed.txt`: automatic mutation check of the independent replay (comparison/boolean/arithmetic/`if`/constant mutations from the AST).
- `spec/messages.jsonl`: byte-identical copy of the r4-draft fixture (needed by the delivered tests).

## Results (all synthetic; logs in `logs/`)
- Delivered suite: 188 tests OK; supplement: 3 tests OK.
- Differential, seeds 11-14, 4000 scenarios each against `research/d-liq/r5-draft/src`, and seed 11 against r4-draft: **0 disagreements** (about 2360 scenarios whose honest slot is VALID; all eleven tamper field kinds and the early-write case are generated). The harness exits non-zero for a disagreement and for a vacuous run (fewer than n/25 VALID slots).
- Mutation check: 279 mutants; 245 killed by the suites; 0 killed only by the differential harness; **34 survivors, all reviewed** by the integrating author as equivalent, unobservable (OUTCOME/CHECKPOINT validity does not reach the replay) or immaterial (>4300-digit integer tokens, diagnostic reason label). The reviews are in `tools/mutants_reviewed.txt` and are **not independent**; GPT or a human must confirm them.

## What went wrong on the way (kept, not hidden)
1. The first differential run showed 67 "disagreements" in 300 scenarios. They were harness bugs, not replay differences: the harness compared the free text of the SLOT_MISMATCH detail (contract 7.3 fixes only the field LIST) and let a tamper turn `sumW_BUY` into an invalid decimal (BAD_EVENT, excluded from every check).
2. The first scenario mix produced a VALID slot in only 4 of 3000 scenarios, i.e. the counted path was barely exercised, and the `valid_status` counter was dead code. The mix was changed (about 15 % VALID now) and the harness refuses vacuous runs.
3. The mutation review found a real gap: a CONN event with an unknown `ev` string would have been read as a close. Fixed by a supplementary test (the replay itself was already correct).

## Limits — read before relying on this
- **Only partly independent.** The author of the clean-room replay and the integrating author are the same model family and the same project; the "independent" verifier of r4/r5 and this replay are independent in construction (specification-only) but not in provenance. Whether that satisfies "independent" is GPT's and the owner's call.
- **Reproducibility gap (D-SPEC-1).** Three of the five specification inputs (`07_MESSAGE_CONTRACT_v1.md`, protocol section 4 and appendix B extracts) are NOT in this repository. The replay's classification rules came from them. Anyone re-doing the clean-room exercise needs them from the owner's r3 package; their hashes are in `SPEC_INPUTS.txt`.
- The harness' scenario generator was written by the author of the primary replay and shares its blind spots; scenarios rarely produce the `ZERO` reason (1 in 16000) and never exceed what `diff_replay.py` generates (no >4300-digit tokens, no duplicate-key edge cases beyond the delivered tests).
- The replay covers contract section 7 as written in r4/r5. The G-1 `feed` question (see `research/d-liq/g1-candle-draft`) would change section 7.2 and therefore this replay.
- `SPEC_NOTES.md` of the clean-room author (its readings of ambiguous points) was not preserved; the ten KNOWN_AMBIGUOUS tests are the only record.

## Run
```
python3 -I -B src/test_replay_indep.py
python3 -I -B src/test_replay_indep_supplement.py
python3 -I -B tools/diff_replay.py ../r5-draft/src src 11 4000          # exit 0 = no disagreement and not vacuous
python3 -I -B tools/mutate_indep.py . ../r5-draft/src 4                 # about 5-10 minutes; exit 0 = every survivor is in tools/mutants_reviewed.txt
sha256sum -c MANIFEST.sha256
```
