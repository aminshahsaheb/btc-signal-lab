# D-LIQ r6 conformance vectors (journal contract v3): inputs, hand-written expectations, a small oracle

STATUS: **DRAFT. Synthetic. By the same author as the contract text. Not reviewed, nothing locked, no r6 verifier exists yet.** This is step 2 of GPT's work order of 2026-11-11 (after the r6 contract text, `../README.md`, pull request #39): "contract tests / boundary cases", before the primary verifier (3), the independent verifier (4), the builder fix (5), the differential and mutation tests (6) and the independent review with its own LOCK decision (7). It is a separate pull request from `main`; it does **not** read the contract text (which is in #39, not yet on `main`): every vector says in `contract_refs` which section of that text it follows, and the vectors must be re-read against the text once both are on `main`.

GPT's caution for this step: the tests must not merely agree with their own reference implementation, and independent checking must be possible. What this package therefore is, and is not:

* **It is a set of INPUTS and EXPECTED OUTPUTS** (`vectors/<id>/journal.jsonl` and `expect.json`), written by hand in `make_vectors.py`, that any implementation of the r6 text can be run against. An independent verifier (step 4) needs nothing from this package but those files.
* **It is not a verifier.** `oracle_r6.py` (129 lines) implements only the rules that are NEW in r6 (feed, `CONN_FEED_CONFLICT`, `MSG_CONN_UNKNOWN`, the structural findings, `CANDLE_LAG_UNSET`, the v3 genesis). It is a second derivation of the hand-written expectations by the author of the text, not independent evidence.
* **Everything that did NOT change in r6 is cross-checked against the existing r5 verifier** (`../../r5-draft/src/dliq_journal_verify_v2.py`; it has its own suites and deliberate-bug checks, see `../../r5-draft/README.md`; it too has no independent review) after a documented transformation (below). Because the SLOT fields of the vectors were derived by hand from the construction (5 BUY messages of weight 60000 each), the r5 verifier REPLAYING them without a `SLOT_MISMATCH` is a check of the hand-derived values against code the author did not write for this step.

Not claimed: no real journal exists; the one real BTCUSDT `forceOrder` frame (run 9, one machine behind a VPN) is not a distribution; no collector, T0, probe, live or edge claim; Pine not compiled; step 8 stays BLOCKED; independent review absent. Green checks here prove that the vectors agree with a second derivation by the same author and with the existing r5 code on the unchanged rules, and nothing more.

## Files
| file | what |
|---|---|
| `make_vectors.py` | the generator and the hand-written expectations (`--check` compares the committed files with a fresh generation) |
| `vectors/<id>_<slug>/journal.jsonl` | the journal: canonical JSON lines (contract 1.4); `seq` = line number except in V14 |
| `vectors/<id>_<slug>/expect.json` | the expectation (format below) |
| `oracle_r6.py` | the oracle of the NEW r6 rules |
| `check_vectors.py` | the checks S, O, R5, C, G below; `python3 -I -B check_vectors.py` |
| `test_r6_vectors.py` | 26 unit tests including 12 NEGATIVE tests (the checker must fail on a wrong vector, a wrong expectation, a stale file, a wrong oracle) |
| `mutation_check_oracle.py` | 37 deliberate wrong readings of the text applied to the oracle: 35 must be killed by some vector, 2 are expected to survive (open questions) |
| `MANIFEST.sha256` | hashes of the files above; the CI workflow `.github/workflows/verify-dliq-r6-vectors.yml` checks it and runs everything |

## How an implementation consumes a vector
Read `journal.jsonl`, call `verify(path, anchor, journal_id, verify_time_ms)` with `journal_id`, `verify_time_ms` and the `anchor` entries of `expect.json` (entries are dicts with anchor_id, index, seq, head, time_ms, time_resolution_ms, time_uncertainty_ms; `[]` = an anchor without entries), replay ON. The report must equal the expectation on:
* `findings`: the multiset of `(name, where)`; for `FORCE_MSG_STRUCTURE` and `FORCE_UNKNOWN_KEY` also the detail string (`conn_id=<int> reason=<reason>` / `conn_id=<int> keys=<k1,k2,...>`). The other detail strings are free text and are `null` in the expectation. `where` follows 8.4 (physical line number; 0 for `NO_CHECKPOINT` and `CANDLE_LAG_UNSET`).
* `verdict`, `hard`, `soft`, `slots` (`tau_ms` as a string), `missing`, `candles` (always `{}`: no CANDLE event is in any vector), `replayed` (true), `analysis_eligible` (always false: `L` is unset, so `CANDLE_LAG_UNSET` is on every journal and the verdict is never PASS; this is case 13).
Two verifiers can be compared on `(name, where, conn_id, reason)` as the contract says (7.7f); the vectors give the expected value of that tuple.

## The checks (`check_vectors.py`)
* **S** structure: canonical lines, `seq` = line (only V14 differs, on purpose), `sha256` of every MSG, the expect.json keys, sorted findings, the 8.2 verdict rule recomputed from the hard list, no PASS, `CANDLE_LAG_UNSET` present.
* **O** the oracle reproduces the expected findings that are new in r6 (including the detail of the two FORCE findings and `HEAD_MISMATCH` under the v3 genesis).
* **R5** everything else: the journal is transformed (below) and given to the r5 verifier; its `(name, where)` multiset must equal `expected - r6_only + r5_only_extra`, with the same `slots` and `missing`. Transformation, applied only to what r5 cannot know: (1) the events of a connection whose first valid `open` has feed KLINE become SESSION events (same line, so every `where` is kept); (2) a FORCE-side frame with an r6 structural reason gets `o.s = "ETHUSDT"`, i.e. it is MALFORMED (symbol) for r5 exactly as it is MALFORMED (that reason) for r6: same `E`, same `recv_ms`, same ledger and voids. `r6_only` lists what r5 cannot produce; `r5_only_extra` lists what r5 reports and r6 must not (V13b: the genesis differs). V06 is the proof that the transformation is needed (a test shows that r5 without it reports `SLOT_MISMATCH`: the healthy KLINE connection with the smaller id becomes primary).
* **C** every conformance case 1 to 18 of contract section 10 is named by at least one vector.
* **G** the files on disk are what `make_vectors.py` generates; V06's SLOT equals V01's (a KLINE connection changes no SLOT field).

## Vectors
Layout of every journal: one connection per slot, opened 1_000_000 ms before `tau`, a PING every 200_000 ms from `tau-800_000` to `tau` (healthy over V(tau), smallest healthy id of its slot), five BUY messages (`E = tau-700_000+100_000*i`), the SLOT at `rec_ms = tau+10_000`; `verify_time_ms = tau_1+10_000`, so every SLOT is PENDING and no deadline finding appears. `tau_1 = 14_400_000 * 124_000`.

| id | cases | verdict | what |
|---|---|---|---|
| V01 | 10,13 | INCOMPLETE | control: five valid messages with o.ps == o.s and o.st == 1 |
| V02a-e | 1,9 | FAIL | one `st_top_level` / `ps_type` / `ps_ne_s` / `st_type` / `st_ne_1` message inside the window of the only SLOT (slot NONE, reason MALFORMED) |
| V03 | 2 | FAIL | an anomalous message recorded between two SLOTs (slot 1 untouched, slot 2 NONE) |
| V04a | 3 | FAIL | an anomalous message after the last SLOT: one finding, no artificial slot, slot stays VALID |
| V04b | 3 | FAIL | the same in a journal without any SLOT |
| V05a | 4 | FAIL | an anomalous message on a non-primary FORCE connection inside V(tau) (it still voids: MALFORMED outranks NON_PRIMARY) |
| V05b | 4 | FAIL | the same outside V(tau): the slot stays VALID, the journal still FAILs |
| V06 | 5,11,18 | INCOMPLETE | a healthy KLINE connection with the SMALLEST id, sixteen kline frames, a non-JSON frame and an anomalous frame: no FORCE finding, the SLOT is identical to V01's |
| V07 | 6 | INCOMPLETE | one message with unknown keys `extra1`, `aa`, top-level `ps`, `zz`: ONE soft `FORCE_UNKNOWN_KEY`, keys sorted |
| V08 | 7 | FAIL | `o.st = true` and `o.ps = 1` |
| V09 | 8,9 | FAIL | one anomalous message replayed by three SLOTs: one finding; later healthy slots do not clear it |
| V10a | 10 | INCOMPLETE | a top-level `ps` only: soft |
| V10b | 10 | FAIL | a top-level `st = 1`: hard, `st_top_level` (r5 accepted it) |
| V10c | 10 | INCOMPLETE | `o.ps` and `o.st` absent: no finding |
| V12a-c | 11 | FAIL | a CONN without `feed`, with `OTHER`, with `force` (case matters): BAD_EVENT; the connection then has no valid open, so its message is MSG_CONN_UNKNOWN |
| V12d | 11 | FAIL | `CONN_FEED_CONFLICT` for a later event naming another feed (close and reopen); a CONN with feed `OTHER` is BAD_EVENT and not also a conflict |
| V12e | 11,16 | FAIL | a MSG before the first valid open (also when the connection opens later); a MSG of a connection that never opens, treated as a FORCE message (its anomaly is reported) |
| V13a | 12 | FAIL | chained from the v2 genesis: `HEAD_MISMATCH` at the checkpoint |
| V13b | 12 | INCOMPLETE | the same journal chained from the v3 genesis (r5 would report the opposite) |
| V14 | 14 | FAIL | the MSG has `seq` = line + 100: `SEQ_GAP` and `FORCE_MSG_STRUCTURE` carry the line number |
| V15 | 15 | FAIL | wrong symbol AND `o.st = 2`: MALFORMED in the replay and still `st_ne_1` |
| V17 | 17 | INCOMPLETE | the decided limit (contract section 9): a wrong-symbol message after the last SLOT produces no finding. Documents the limit; not to be "fixed" without a new decision |
| V19 | extra | FAIL | several anomalies in one message: the first reason only (also `st = 1.0` is `st_type`) |
| V20 | extra | INCOMPLETE | unparsable frames (not JSON, duplicate key, NaN, not UTF-8, a JSON array) are not structural anomalies (7.7a) |

Not in this package: vectors for the CANDLE rules 6.5 to 6.9 (their grammar rests on a never-verified kline layout; the synthetic G-1 reference checker has its own tests), vectors for `REPLAY_NOT_RUN`, and anything about the builder. Case 13 is covered through `CANDLE_LAG_UNSET` on every vector; no vector contains a CANDLE event, so "no minute is USABLE" is trivially true.

## Open questions this package surfaced (for GPT; the contract text is silent, the vectors avoid them)
1. **The same unknown key name at both levels** (for example top-level `zz` and `o.zz`): listed once or twice in `keys=`? The oracle lists it once (`sorted(set(...))`). Mutant "UNDECIDED: listed twice" survives on purpose.
2. **`o.ps` present while `o.s` is absent**: is it `ps_ne_s`? The oracle says yes (a string differs from "absent"); the message is MALFORMED anyway (`missing_o.s`). Mutant "UNDECIDED: o.ps with o.s absent" survives on purpose.
3. **Feed of a connection whose first valid `open` lies after a MSG or a SLOT**: 2.3a defines the feed from the whole file, 7.2 uses only events at lines `< i`. The oracle takes the feed from the whole file. No vector depends on it except V12e's line 1 (a normal frame).
4. **`o` present but not an object** (a string, null): the text gives no `ps`/`st` reason (the replay classifies the message MALFORMED, `o_not_object`; the run-level pass reports nothing). Consistent with the decided limit; no vector.

If a vector ever decides one of 1 and 2, `mutation_check_oracle.py` fails until its list is updated, so the question cannot be settled by accident.

## Run
```
cd research/d-liq/r6-draft/tests
python3 -I -B make_vectors.py --check        # the files are what the generator produces
python3 -I -B check_vectors.py               # S, O, R5, C, G
python3 -I -B test_r6_vectors.py             # 26 tests (negative tests included)
python3 -I -B mutation_check_oracle.py       # mutants: 37, problems: 0
```
