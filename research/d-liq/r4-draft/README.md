# D-LIQ r4 increment (DRAFT — not a lock candidate)

**What this is.** The r4 changes that GPT's r3 audit (2026-11-02) ordered, re-implemented on top of the r3-reconstruction (PR #23, zip sha256 `85fd4080dd3c7d38f0da512d82d21f3b38457c7758f4c06308aad1a9911c9a19`) and on the current PR #15 builder (blob `505ffdcc…960f7`).
Claude's earlier r4 work-tree was lost in a container reset on 2026-11-04; **nothing here is a restoration of numbers from it**. Everything below was re-run in this tree (logs in `logs/`).

**What this is not.** Not r3.1, not a protocol lock, not a "ready for lock" claim, no collector, no T0, no real Binance message, no real anchor, no market return scoring, no edge claim. All data are synthetic. The "independent" verifier is **partially independent** (same model family, Claude-built corpus, subagent-written implementation; the r4 coverage code in it is an integrator patch, not written by its author).

## Rebuild (deterministic)
```
python3 -I patches/assemble.py <dir of dliq_r3_reconstruction> <new out dir>      # applies p01..p12; output is byte-identical to this tree (checked with diff -r)
```
## Run everything (from the tree root)
```
python3 -I src/test_dliq_journal_v2.py                      # writer + primary verifier         219 checks
python3 -I indep_verifier/test_indep.py                     # partially independent verifier    102 tests
python3 -I src/test_dliq_msg_contract_v1.py                 # executable message contract       59 checks
python3 -I tests/test_none_slot_regressions.py              # r3-reconstruction NONE-slot regressions, 2 tests
python3 -I builder/test_build_slots_v2_e2e.py               # builder, real journals + mandatory replay, 17 tests
for s in 11 12 13 14; do python3 -I src/diff_test_verifiers.py indep_verifier 30000 $s; done     # ~30 s per seed, 30105 journals each
python3 -I patches/mutation_check_verifiers.py $PWD ; python3 -I patches/mutation_check_builder.py $PWD/builder    # 9 + 6 deliberate bugs must be KILLED
```
Results of this session: logs/*.txt (all suites rc=0; four seeds 0 disagreements each; 15/15 mutants killed).

## Response to the seven orders (GPT r3 audit) — status, with what is NOT claimed
| # | Order | Status | Evidence | Not claimed |
|---|---|---|---|---|
| 1 | every OUTCOME needs its own valid anchoring coverage; unanchored outcomes must not enter EVAL; rule in journal contract, verifier, builder | **DONE (synthetic)** | contract §6.4; both verifiers return `outcomes` + soft `OUTCOME_UNCOVERED`; builder re-derives coverage from the raw journal and compares with both reports (`BUILDER_OUTCOME_COVERAGE_MISMATCH`), UNCOVERED ⇒ PENDING ⇒ no rows / no CSV | real anchor behaviour; OPEN-22 lag is reported (`coverage_lag`), not capped (owner decision) |
| 2 | slots.csv builder incl. N_unanch, prior_sign, missing, late/unanchored, NO_PRICE, hard verifier findings; adversarial tests | **PARTIAL** | PR #15 builder (Codex) + r4 delta; 17 e2e tests: clean, tail outcome, tampered, omitted, re-sequenced omission, flipped SLOT, early SLOT, NONE-slot outcome, duplicate, forged reports, pin changes | PR #15 itself is still Draft and needs independent review; prior_sign/missing/late logic not re-audited here |
| 3 | SLOT replay mandatory before T0, or an independent replay verifier | **PARTIAL** | contract §7 mandatory; `SLOT_EARLY_WRITE` (hard); builder runs the primary verifier with `replay_slots=True`, refuses a report without `replayed`, pins the message contract by hash; test shows a side-flipped SLOT with a perfectly consistent chain passes sections 1-6 and is caught only by the replay | **no independent replay implementation exists** (needs the r3 protocol §4 + docs/07 message-contract text, not in this base); differential harness cannot exercise the replay (`SLOT_MISMATCH`/`SLOT_EARLY_WRITE` listed "never exercised"); replay cost is O(slots × messages) (OPEN-23) |
| 4 | tests for tampered, omitted and tail-unanchored OUTCOME records | **DONE (synthetic)** | primary suite PART 7, independent suite `TestOutcomeCoverageR4`, differential operators `o_del/o_tamper/o_tail/o_cut/o_status`, builder e2e | a tail-unanchored record cannot be authenticated by the chain (documented limit 4.4); r4 only makes it visible and unusable |
| 5 | OPEN-21 unapproved, sensitivity only | **not touched here** | protocol/analysis text is outside this base | — |
| 6 | LIQ_INCREMENTAL = positive conditional estimate under the limited prior-sign control, not causal/tradable edge | **not touched here** | needs the r3 protocol/analysis files | — |
| 7 | no "ready for lock" before real Binance dry-run, real anchor test, end-to-end test | **respected** | step 8 BLOCKED: real forceOrder messages (endpoint path unverified), real anchor, collector host | — |

## Equivalence to r3.1 (new evidence)
The actual r3.1 verifier files are in PR #15 (`research/d-liq/r3-tools/verifiers/`). Compared with the r3-reconstruction: primary `816f8d9f…` vs `86db4125…` and independent `f967c77c…` vs `4cabc798…` differ **only in one docstring line each** (checked with `diff`); the writer hash equals r3.1's (`51f0996f…`). So the base verifier *code* is identical to r3.1; the test files and the differential harness were not compared line-by-line.

## Files changed vs the reconstruction (sha256)
| file | sha256 |
|---|---|
| src/dliq_journal_v2.py (writer; + `outcome_and_anchor`) | 02537fbfc0b6182321c5c8a57fc976243121a7b4c5907a846e64a6537051c614 |
| src/dliq_journal_verify_v2.py (primary; + coverage, `SLOT_EARLY_WRITE`, `replayed`) | 2eedfbe9d56a31297bab3956d165b93e21cd0e72779d19de607883f85ca006be |
| indep_verifier/verify_indep.py (+ coverage; no replay) | 8409e5845ffb91f9e7df02ecb3de87a171f1d71e28364dbbe5ee1a2c34bb5cc1 |
| indep_verifier/JOURNAL_CONTRACT_v2.md (r4-draft: §6.1e, §6.4, §7, §7.5) | e38d1db3bb20964677180236c6a95bbeee5bbfc422785c4693861c4fed9c7564 |
| builder/build_slots_v2.py (PR #15 head + r4 delta, pins the three files below) | 88bfb7ee19e8151f6b777b0c979122c239f54290682769cc685002cca05d8157 |
| src/dliq_msg_contract_v1.py (unchanged, now pinned by the builder) | e41678d794fb24480c148d7a3507c5d1d3346dabe53c29796b3bb2b271aee7dc |
`builder/verifiers/` holds the byte-identical copies that the builder pins by hash (a test asserts equality with `src/` and `indep_verifier/`).

## Known limits / open items (do not read past these)
- Independent SLOT replay: not done. §7.5 was re-checked clause by clause against the executable contract by reading only.
- The PR #15 hand-made builder fixtures (SLOTs with invented fields) are not replayable; with the mandatory replay their "clean" case reports `SLOT_MISMATCH`. The e2e file replaces them; 22 of the 23 PR #15 builder tests still pass unchanged but only because they assert narrow things.
- Contract §7.5 relies on the message classes of the r3 package (`docs/07_MESSAGE_CONTRACT_v1.md`, protocol §4.2), which are not in this base.
- OPEN-21, OPEN-23 (replay cost, `recv_ms ≥ tau−16 min` filter), the entry-candle decision, real-feed semantics, anchor choice, collector host: open.
- Pine panels not compiled in TradingView. KCEX not measured.
