# D-LIQ r6 conformance vectors (journal contract v3): inputs, hand-written expectations, a small oracle

STATUS: **DRAFT. Synthetic. By the same author as the contract text. Not reviewed, nothing locked, no r6 verifier exists yet.** This is step 2 of GPT's work order of 2026-11-11 (after the r6 contract text, `../README.md`, pull request #39): "contract tests / boundary cases", before the primary verifier (3), the independent verifier (4), the builder fix (5), the differential and mutation tests (6) and the independent review with its own LOCK decision (7). It is a separate pull request from `main`; it does **not** read the contract text (which is in #39, not yet on `main`): every vector says in `contract_refs` which section of that text it follows, and the vectors must be re-read against the text once both are on `main`.

**Revision of 2026-11-12.** GPT answered the four questions of the first version (design proposals, applied by Claude to the text on the #39 branch and to this package): unknown keys are listed per occurrence with their location (`o.zz`), `o.ps` without `o.s` has its own reason `ps_no_s` (six `ps` / `st` reasons now), the feed of a connection applies from its first valid `open` on (a MSG recorded earlier has no feed, also when the later `open` names KLINE), and an `o` that is not an object gives no `ps` / `st` reason while a top-level `st` is still checked independently. Four new vectors (V02f, V12f, V21, V23), new conformance cases 19 to 22, the two mutants that survived on purpose are now killed. **Vector-set digest of the first revision (34 vectors)** (the sha256 of the sorted `sha256sum` lines of every file under `vectors/`, run from this directory with `find vectors -type f | LC_ALL=C sort | xargs sha256sum | sha256sum` (byte-order sort: `LC_ALL=C` is part of the definition, because a locale that ignores punctuation orders `V19_...` and `V19b_...` differently and changes the digest)): `ca1f0352f99928088401425b1cd4f480519ac47a103a91a5c692e8bb97696c78`. It identifies the vectors a verifier was run against; the commit SHA of the pull request identifies everything else.

**Second revision of 2026-11-12 (same day, after GPT's reply to the report on this package).** GPT accepted the five interpretations conditionally: each must be explicit in the text and covered by vectors. Two gaps in the vectors were closed (the text was already explicit): **V02g** (`o.ps` = "5" and `o.s` = 5: an `o.s` that is not a string differs from `o.ps`, so the reason is `ps_ne_s`; a reading that compares them as strings reports nothing) and **V19b** (`o.ps` a string, no `o.s`, and a bad `o.st`: the reason is `ps_no_s`, the order of the six reasons is deterministic). Two oracle mutants were added for them (46 now, all killed, each by the intended vector). The other 34 vectors are byte-identical to the first revision (commit `d10ba97`, vector-set digest `ca1f0352f99928088401425b1cd4f480519ac47a103a91a5c692e8bb97696c78`); the vector-set digest of the 36 is **`80fd19cbb9c2a4e861bbd692f72d5bed7cc2b43846f579de144399be05ab17a1`**. The first revision is a subset, so a verifier run on `d10ba97` and a verifier run on this revision can be compared vector by vector.

**Third revision of 2026-11-14 (after GPT's red-team review of the primary verifier, PR #41, and the contract amendment PR #39 at `53a7a3a`).** The amended text (sections 2.1, 2.2, 6.9, 7.2, 7.5, 7.7, 8.4 and the new cases 23 to 27 of section 10) is covered by **ten new vectors, in new directories only**; the 36 directories of the previous revision are byte-identical (a unit test recomputes their digest and compares it with `80fd19cb...` below). **V24a, V24b, V24c** (case 23: an invalid character, whitespace, wrong padding or length in `raw_b64`), **V25a, V25b** (case 24: non-canonical trailing bits, one per padding form, each setting a DIFFERENT spare bit so that a decoder checking only the lowest bit is caught), **V26** (case 25: an undecodable message outside V(tau) and one after the last SLOT), **V27** (case 26: a CANDLE event without `msg_seq` is `BAD_EVENT`; it says NOTHING about the CANDLE rules and no vector contains a valid CANDLE event), **V28a, V28b, V28c** (case 27: an EVAL outcome with `L` unset gives two `OUTCOME_UNLINKED`, entry first, then exit, details `endpoint=entry` / `endpoint=exit`; the same outcome with status NO_PRICE gives none; an uncovered outcome). Every undecodable text is a TRAP for a permissive decoder: it decodes (or, with `validate=True` alone, passes) to a valid frame whose `sha256` matches, so such a verifier would report no `RAW_HASH_MISMATCH`, count the message and, for V24b, V24c and V25b, report a `FORCE_*` finding the contract forbids; a unit test shows that for each of those texts. The report keys `n_events`, `head_hex` and `outcomes` (contract 8.2, 6.4) are now part of the expectation, for ALL 46 vectors, in one added file `vectors/EXPECT_DERIVED.json` (not in the old `expect.json` files, which therefore stay unchanged). 15 new oracle mutants (61 in all, all killed). **Vector-set digest of the 46 vectors plus `EXPECT_DERIVED.json` (93 files): `dfebd45409bac7c6e95e613cec7045758e1ab2b25bcc4f7559072e038c44d5d0`.** All expectations of the new vectors were written by hand before any checker ran; the r5 verifier then agreed with every slot field (no `SLOT_MISMATCH`) after the transformation (3) below, which is the only independent check of the hand-derived ledger and voids for the undecodable messages.

GPT's caution for this step: the tests must not merely agree with their own reference implementation, and independent checking must be possible. What this package therefore is, and is not:

* **It is a set of INPUTS and EXPECTED OUTPUTS** (`vectors/<id>/journal.jsonl` and `expect.json`), written by hand in `make_vectors.py`, that any implementation of the r6 text can be run against. An independent verifier (step 4) needs nothing from this package but those files. The primary verifier (step 3) must not import `oracle_r6.py`.
* **It is not a verifier.** `oracle_r6.py` (192 lines) implements only the rules that are NEW or changed in r6 (feed, `CONN_FEED_CONFLICT`, `MSG_CONN_UNKNOWN`, the structural findings, `CANDLE_LAG_UNSET`, the v3 genesis, strict canonical base64 with `RAW_HASH_MISMATCH`, `BAD_EVENT` for a CANDLE without `msg_seq`, the two endpoint findings of `OUTCOME_UNLINKED`, `n_events` and `head_hex`). It is a second derivation of the hand-written expectations by the author of the text, not independent evidence.
* **Everything that did NOT change in r6 is cross-checked against the existing r5 verifier** (`../../r5-draft/src/dliq_journal_verify_v2.py`; it has its own suites and deliberate-bug checks, see `../../r5-draft/README.md`; it too has no independent review) after a documented transformation (below). Because the SLOT fields of the vectors were derived by hand from the construction (5 BUY messages of weight 60000 each), the r5 verifier REPLAYING them without a `SLOT_MISMATCH` is a check of the hand-derived values against code the author did not write for this step.

Not claimed: no real journal exists; the one real BTCUSDT `forceOrder` frame (run 9, one machine behind a VPN; 27 frames in all from that machine) is not a distribution; no collector, T0, probe, live or edge claim; Pine not compiled; step 8 stays BLOCKED; independent review absent. Green checks here prove that the vectors agree with a second derivation by the same author and with the existing r5 code on the unchanged rules, and nothing more.

## Files
| file | what |
|---|---|
| `make_vectors.py` | the generator and the hand-written expectations (`--check` compares the committed files with a fresh generation) |
| `vectors/<id>_<slug>/journal.jsonl` | the journal: canonical JSON lines (contract 1.4); `seq` = line number except in V14 |
| `vectors/<id>_<slug>/expect.json` | the expectation (format below) |
| `vectors/EXPECT_DERIVED.json` | `n_events`, `head_hex`, `outcomes` for every vector id (added in the third revision; see below) |
| `oracle_r6.py` | the oracle of the NEW r6 rules |
| `check_vectors.py` | the checks S, O, R5, D, C, G below; `python3 -I -B check_vectors.py` |
| `test_r6_vectors.py` | 44 unit tests including 17 NEGATIVE tests (the checker must fail on a wrong vector, a wrong expectation, a wrong supplement, a stale file, a wrong oracle) |
| `mutation_check_oracle.py` | 61 deliberate wrong readings of the text applied to the oracle: every one must be killed by some vector (a mutant may be marked "expected to survive" for a point the text leaves open; none is since 2026-11-12) |
| `MANIFEST.sha256` | hashes of the files above; the CI workflow `.github/workflows/verify-dliq-r6-vectors.yml` checks it and runs everything |

## How an implementation consumes a vector
Read `journal.jsonl`, call `verify(path, anchor, journal_id, verify_time_ms)` with `journal_id`, `verify_time_ms` and the `anchor` entries of `expect.json` (entries are dicts with anchor_id, index, seq, head, time_ms, time_resolution_ms, time_uncertainty_ms; `[]` = an anchor without entries), replay ON. The report must equal the expectation on:
* `findings`: the multiset of `(name, where)`; for `FORCE_MSG_STRUCTURE` and `FORCE_UNKNOWN_KEY` also the detail string (`conn_id=<int> reason=<reason>` / `conn_id=<int> keys=<e1,e2,...>`, one entry per unknown-key occurrence, `o.<name>` for a key inside `o`). The other detail strings are free text and are `null` in the expectation. (The one exception added in the third revision is `OUTCOME_UNLINKED`, whose detail prefix is compared, see below.) `where` follows 8.4 (physical line number; 0 for `NO_CHECKPOINT` and `CANDLE_LAG_UNSET`).
* `verdict`, `hard`, `soft`, `slots` (`tau_ms` as a string), `missing`, `candles` (always `{}`: no VALID CANDLE event is in any vector), `replayed` (true), `analysis_eligible` (always false: `L` is unset, so `CANDLE_LAG_UNSET` is on every journal and the verdict is never PASS; this is case 13).
* `n_events`, `head_hex` and `outcomes` (contract 8.2 lists them as report keys; 3.2 and 6.4 define them), taken from `vectors/EXPECT_DERIVED.json` (`{"vectors": {<id>: {"n_events": int, "head_hex": 64 hex characters, "outcomes": {<tau_ms as a string>: "COVERED" | "UNCOVERED"}}}}`), also for the 36 older vectors (their `outcomes` are `{}`).
* `OUTCOME_UNLINKED` (V28a, V28c) is compared on `(name, where, endpoint)`: its detail begins `endpoint=entry` or `endpoint=exit` and `expect.json` holds exactly that prefix (the rest of a detail is diagnostic); the two findings of one OUTCOME come in the order entry, then exit (6.9).
Two verifiers can be compared on `(name, where, conn_id, reason)` as the contract says (7.7f); the vectors give the expected value of that tuple.

## The checks (`check_vectors.py`)
* **S** structure: canonical lines, `seq` = line (only V14 differs, on purpose), strict canonical base64 and a matching `sha256` of every MSG / CANDLE (a line is bad EXACTLY when the expectation names `RAW_HASH_MISMATCH` for it), the expect.json keys, sorted findings, the 8.2 verdict rule recomputed from the hard list, no PASS, `CANDLE_LAG_UNSET` present.
* **O** the oracle reproduces the expected findings that are new in r6 (including the detail of the two FORCE findings and of `OUTCOME_UNLINKED`, `RAW_HASH_MISMATCH` by strict canonical base64 derived by hand (grammar + trailing bits; the verifier of the project uses `validate=True` + re-encoding; a unit test compares the two methods on 100 000+ strings), `BAD_EVENT` for a CANDLE without `msg_seq`, and `HEAD_MISMATCH` under the v3 genesis).
* **R5** everything else: the journal is transformed (below) and given to the r5 verifier; its `(name, where)` multiset must equal `expected - r6_only + r5_only_extra`, with the same `slots` and `missing`. Transformation, applied only to what r5 cannot know: (1) the events of a connection recorded FROM its first valid `open` on, when that `open` has feed KLINE, become SESSION events (same line, so every `where` is kept; an event recorded before the `open` has no feed and stays); (2) a FORCE-side frame with an r6 structural reason gets `o.s = "ETHUSDT"`, i.e. it is MALFORMED (symbol) for r5 exactly as it is MALFORMED (that reason) for r6: same `E`, same `recv_ms`, same ledger and voids. `r6_only` lists what r5 cannot produce; `r5_only_extra` lists what r5 reports and r6 must not (V13b: the genesis differs). (3) an undecodable `raw_b64` is replaced by the canonical base64 of `b"undecodable"` with its `sha256` kept (r5 decodes permissively or fails; it then sees a non-JSON frame, MALFORMED as `undecodable_base64` is for r6, and a hash mismatch, so it reports `RAW_HASH_MISMATCH` too). V06 is the proof that the transformation is needed (a test shows that r5 without it reports `SLOT_MISMATCH`: the healthy KLINE connection with the smaller id becomes primary).
* **D** `EXPECT_DERIVED.json` names exactly the vectors, has exactly the three keys with sane values, `n_events` and `head_hex` equal what the oracle computes from the journal bytes (the r5 verifier cannot be asked for `head_hex`: its genesis differs) and `outcomes` equal what the r5 verifier reports (check R5).
* **C** every conformance case 1 to 27 of contract section 10 is named by at least one vector.
* **G** the files on disk are what `make_vectors.py` generates; V06's SLOT equals V01's (a KLINE connection changes no SLOT field).

## Vectors
Layout of every journal: one connection per slot, opened 1_000_000 ms before `tau`, a PING every 200_000 ms from `tau-800_000` to `tau` (healthy over V(tau), smallest healthy id of its slot), five BUY messages (`E = tau-700_000+100_000*i`), the SLOT at `rec_ms = tau+10_000`; `verify_time_ms = tau_1+10_000`, so every SLOT is PENDING and no deadline finding appears. `tau_1 = 14_400_000 * 124_000`.

| id | cases | verdict | what |
|---|---|---|---|
| V01 | 10,13 | INCOMPLETE | control: five valid messages with o.ps == o.s and o.st == 1 |
| V02a | 1,9 | FAIL | one `st_top_level` message inside the window of the only SLOT (slot NONE, reason MALFORMED) |
| V02b | 1,9 | FAIL | one `ps_type` message, same layout |
| V02c | 1,9 | FAIL | one `ps_ne_s` message, same layout |
| V02d | 1,9 | FAIL | one `st_type` message, same layout |
| V02e | 1,9 | FAIL | one `st_ne_1` message, same layout |
| V02f | 1,9,20 | FAIL | one `ps_no_s` message (o.ps a string, o.s absent), same layout |
| V02g | 1,9 | FAIL | one `ps_ne_s` message whose `o.s` is not a string (o.ps = "5", o.s = 5: equal as strings, but a non-string `o.s` differs), same layout |
| V03 | 2 | FAIL | an anomalous message recorded between two SLOTs (slot 1 untouched, slot 2 NONE) |
| V04a | 3 | FAIL | an anomalous message after the last SLOT: one finding, no artificial slot, slot stays VALID |
| V04b | 3 | FAIL | the same in a journal without any SLOT |
| V05a | 4 | FAIL | an anomalous message on a non-primary FORCE connection inside V(tau) (it still voids: MALFORMED outranks NON_PRIMARY) |
| V05b | 4 | FAIL | the same outside V(tau): the slot stays VALID, the journal still FAILs |
| V06 | 5,11,18 | INCOMPLETE | a healthy KLINE connection with the SMALLEST id, sixteen kline frames, a non-JSON frame and an anomalous frame: no FORCE finding, the SLOT is identical to V01's |
| V07 | 6 | INCOMPLETE | one message with unknown keys `extra1`, `aa`, top-level `ps`, `o.zz`: ONE soft `FORCE_UNKNOWN_KEY`, `keys=aa,extra1,o.zz,ps` |
| V08 | 7 | FAIL | `o.st = true` and `o.ps = 1` |
| V09 | 8,9 | FAIL | one anomalous message replayed by three SLOTs: one finding; later healthy slots do not clear it |
| V10a | 10 | INCOMPLETE | a top-level `ps` only: soft |
| V10b | 10 | FAIL | a top-level `st = 1`: hard, `st_top_level` (r5 accepted it) |
| V10c | 10 | INCOMPLETE | `o.ps` and `o.st` absent: no finding |
| V12a | 11 | FAIL | a CONN without `feed`: BAD_EVENT; the connection then has no valid open, so its message is MSG_CONN_UNKNOWN |
| V12b | 11 | FAIL | a CONN with feed `OTHER`, same consequence |
| V12c | 11 | FAIL | a CONN with feed `force` (case matters), same consequence |
| V12d | 11 | FAIL | `CONN_FEED_CONFLICT` for a later event naming another feed (close and reopen); a CONN with feed `OTHER` is BAD_EVENT and not also a conflict |
| V12e | 11,16 | FAIL | a MSG before the first valid open (also when the connection opens later as FORCE); a MSG of a connection that never opens, treated as a FORCE message (its anomaly is reported) |
| V12f | 11,21 | FAIL | the feed applies from the first valid open on: a CONN close before it cannot conflict; a MSG before the open of a connection that later opens as KLINE has no feed: MSG_CONN_UNKNOWN, replay input, examined as FORCE |
| V13a | 12 | FAIL | chained from the v2 genesis: `HEAD_MISMATCH` at the checkpoint |
| V13b | 12 | INCOMPLETE | the same journal chained from the v3 genesis (r5 would report the opposite) |
| V14 | 14 | FAIL | the MSG has `seq` = line + 100: `SEQ_GAP` and `FORCE_MSG_STRUCTURE` carry the line number |
| V15 | 15 | FAIL | wrong symbol AND `o.st = 2`: MALFORMED in the replay and still `st_ne_1` |
| V17 | 17 | INCOMPLETE | the decided limit (contract section 9): a wrong-symbol message after the last SLOT produces no finding. Documents the limit; not to be "fixed" without a new decision |
| V19 | extra | FAIL | several anomalies in one message: the first reason only (also `st = 1.0` is `st_type`) |
| V19b | 20 | FAIL | `ps_no_s` takes precedence over the st reasons (o.ps a string, no o.s, o.st = 2 and o.st = "1"): one `ps_no_s` per message |
| V20 | extra | INCOMPLETE | unparsable frames (not JSON, duplicate key, NaN, not UTF-8, a JSON array) are not structural anomalies (7.7a) |
| V21 | 22 | FAIL | `o` is a string / null (with a top-level `st`) / a number: MALFORMED, no ps/st reason, but the top-level `st` is still `st_top_level` |
| V23 | 19 | INCOMPLETE | top-level `zz`, `o.zz` and a top-level key literally named `o.zz`: ONE finding, `keys=o.zz,o.zz,zz` (per occurrence, no de-duplication) |
| V24a | 23 | FAIL | a valid BUY frame whose `raw_b64` has an invalid character (`!`) inside: `RAW_HASH_MISMATCH`, MALFORMED in the replay, one void, slot NONE; a permissive decoder would count it |
| V24b | 23 | FAIL | whitespace: a trailing newline (frame with a ps_type anomaly) and an inner space (frame with an unknown key): two `RAW_HASH_MISMATCH`, two voids, NO `FORCE_*` finding |
| V24c | 23 | FAIL | wrong padding (`==` stripped), one `=` too many (a permissive decoder ignores it), a length cut off: three `RAW_HASH_MISMATCH`, three voids, no crash, no `FORCE_*` finding |
| V25a | 24 | FAIL | non-canonical trailing bits, padding `==`, the highest spare bit set; hash of the decoded bytes matches |
| V25b | 24 | FAIL | the same for padding `=`, the higher spare bit set, a valid frame with an unknown key (a lenient verifier would add `FORCE_UNKNOWN_KEY`) |
| V26 | 25 | FAIL | an undecodable message outside V(tau) (counted as MALFORMED in the ledger and in `n_messages`, voids nothing: slot VALID) and one after the last SLOT (changes nothing) |
| V27 | 26 | FAIL | a CANDLE event without `msg_seq`: `BAD_EVENT` (r6 only); says nothing about the CANDLE rules |
| V28a | 27 | FAIL | an EVAL outcome (VALID slot, correct timing and `r_bps`, covered by a checkpoint), `L` unset: two `OUTCOME_UNLINKED`, `endpoint=entry` then `endpoint=exit` |
| V28b | 27 | INCOMPLETE | the same outcome with status NO_PRICE: no finding |
| V28c | 27 | FAIL | the EVAL outcome without a covering checkpoint: the two findings, `OUTCOME_UNCOVERED`, `TAIL_UNANCHORED`, `outcomes` UNCOVERED |

Not in this package: vectors for the CANDLE rules 6.5 to 6.9 (their grammar rests on a never-verified kline layout; the synthetic G-1 reference checker has its own tests), vectors for `REPLAY_NOT_RUN`, and anything about the builder. Case 13 is covered through `CANDLE_LAG_UNSET` on every vector; the only CANDLE event of the package is the invalid one of V27, so "no minute is USABLE" is trivially true. The vectors give a verifier that lacks the CANDLE rules nothing to do with a VALID CANDLE; such a verifier must give no verdict for a journal that has one (case 26), and no vector tests that.

## The four questions of the first version, and GPT's answers (2026-11-12)
GPT's answers are design proposals, not an approval of the text; they are applied here and in the text on the #39 branch.
1. Same unknown key name at both levels: one entry per occurrence, location-qualified (`o.zz,zz`), none dropped (V23, case 19). This changes the `keys=` detail format of the first version (names only).
2. `o.ps` without `o.s`: a reason of its own, `ps_no_s`, between `ps_type` and `ps_ne_s` (V02f, case 20). The smaller alternative (read an absent `o.s` as `ps_ne_s`) was not taken because GPT asked for a specific reason.
3. A valid `open` after a MSG or SLOT: the earlier MSG is not made valid retroactively; it has no feed, is `MSG_CONN_UNKNOWN`, and is treated as a FORCE message (V12e, V12f, case 21). In the first version the feed was read from the whole file; this is a change.
4. `o` not an object: MALFORMED only; no `ps`/`st` reason; a top-level `st` is still `st_top_level` (V21, case 22).
Known diagnostic ambiguity left as is: a key name that itself contains `.` or `,` makes the `keys=` string ambiguous to a reader (V23 shows a top-level key literally named `o.zz`); the string is diagnostic and is not part of the comparison key.

## Run
```
cd research/d-liq/r6-draft/tests
python3 -I -B make_vectors.py --check        # the files are what the generator produces
python3 -I -B check_vectors.py               # S, O, R5, C, G
python3 -I -B test_r6_vectors.py             # 44 tests (negative tests included)
python3 -I -B mutation_check_oracle.py       # mutants: 61, problems: 0
```
