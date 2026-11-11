# D-LIQ r6-draft: contract TEXT only (journal contract v3, revision r6)

STATUS: **DRAFT, text only. Not locked, not reviewed, nothing in it is implemented or tested.** No verifier, builder, collector, test or fixture changes in this package; the r5 package (`../r5-draft`) stays as it is. This is the first step of GPT's work order of 2026-11-10 ("PR for the r6 contract text") after the decisions recorded in the G-1 proposal (`../g1-candle-draft/docs/G1_CANDLE_CONTRACT_PROPOSAL.md`, sections 8 to 12, in the decisions PR at the time of writing). The tests, the primary verifier, the independent verifier, the builder integration, and the differential and mutation tests are separate, later pull requests.

## Files
- `contract/JOURNAL_CONTRACT_v3.md`: the r6 text. It is the r5 text (`../r5-draft/indep_verifier/JOURNAL_CONTRACT_v2.md`) with exact replacements, so every untouched sentence is byte-identical.
- `contract/R5_TO_R6.diff`: the unified diff r5 -> r6 (generated; the text guard fails if it is stale). Read this first.
- `tools/check_contract_text.py`: a TEXT guard (not a verifier): the diff is current, every finding name of 8.1 is used and every used name is listed, every section reference exists, the genesis string is v3. `--selftest` shows that each check fails on a known-bad text.
- `MANIFEST.sha256`; the CI workflow `.github/workflows/verify-dliq-r6-draft.yml` runs the manifest check and the text guard (a structure check of the text, not a verification of any rule).

## What r6 changes (decision letters from the G-1 proposal)
| topic | where |
|---|---|
| A2: journal format and genesis v3 | 3.2, 3.3 |
| A: required `CONN.feed` (`FORCE` / `KLINE`), replay inputs filtered to FORCE, `CANDLE.msg_seq` | 2.1, 2.3, 6.5, 7.2 |
| A3: two separate connections, no combined stream on the FORCE path | 2.3d |
| B: CANDLE provenance rules with `L` UNSET (`CANDLE_LAG_UNSET`, never PASS) | 6.5-6.9, 8.1, 8.2 |
| `o.ps`, `o.st` known optional fields; top-level `st` forbidden; the `st_not_1` rule removed | 7.5a |
| run-level pass over every FORCE message, independent of any SLOT; findings `FORCE_MSG_STRUCTURE`, `FORCE_UNKNOWN_KEY` | 7.7, 8.1, 8.4 |
| feed integrity findings `CONN_FEED_CONFLICT`, `MSG_CONN_UNKNOWN` | 2.3 |
| no override, re-verification under a new revision | 8.5 |
| minimum conformance cases for the test step | 10 |

The verdict stays `PASS` / `FAIL` / `INCOMPLETE` (GPT, 2026-11-11: no new value); a structural anomaly gives `FAIL`.

## Still OPEN (not decided; marked [OPEN] in the text)
`U = 250 ms`, `E_RANGE`, the meaning of `k.x`, and the value of `L` (decision B: unset). A real anchor, the collector host, the replay, missingness and the independent review also stay open. One real BTCUSDT `forceOrder` frame (run 9) is not enough for a lock.

## Details I chose without a decision ([C] in the text) -- all seven CONFIRMED by GPT on 2026-11-11 (conditional approval, see below)
1. `feed` is required on EVERY CONN event (open and close); a later event naming another feed is the hard `CONN_FEED_CONFLICT`.
2. A MSG whose connection has no valid `open` event is the hard `MSG_CONN_UNKNOWN` and is treated as a FORCE message by the replay and by 7.7 (the conservative reading).
3. A KLINE frame that no CANDLE refers to is not checked at all; a PING of an unknown connection has no rule.
4. The run-level hard finding covers only the `ps` / `st` reasons (five on 2026-11-11: `st_top_level`, `ps_type`, `ps_ne_s`, `st_type`, `st_ne_1`; six since 2026-11-12, `ps_no_s` added, see the last section). Every other MALFORMED reason (bad JSON, wrong symbol, ...) stays slot-voiding only. GPT confirmed (2026-11-11): NOT every MALFORMED reason; the consequence is a decided limit (contract section 9).
5. The names, the reason codes, their evaluation order, the exact detail strings (`conn_id=<int> reason=<reason>`; `conn_id=<int> keys=<k1,k2,...>`) and `where` = the physical line number of the MSG event (not `seq`).
6. The `ps` / `st` anomaly is evaluated on the parsed object independently of any earlier MALFORMED reason (7.7b).
7. `CANDLE_LAG_UNSET` is reported on every journal while `L` is unset, even one without CANDLE events (as the G-1 reference checker does).

## GPT's review of 2026-11-11 (logical review of the text; not an independent review, not proof of any implementation)
Conditional approval: the main decisions and the seven [C] details are confirmed (the run-level finding covers only the five `ps`/`st` reasons; the consequence is a decided limit, section 9 of the contract: a malformed FORCE message of another kind after the last SLOT is not reported by 7.7). Two text fixes were required before the test step and are applied in this PR: (1) 7.5d said "MALFORMED messages, on ANY connection", which contradicted the KLINE filter of 7.2 (also corrected in 7.5b and 7.5c); (2) `where` of the FORCE findings is the physical line number, not `MSG.seq` (7.7b). Conformance cases 14-18 were added for these points.

## What this package does NOT do
No code, no test, no fixture, no verifier or builder change, no lock, no T0, no collector, no price scoring, no edge claim. The text was written by one author and has had no review; the guard checks its structure only.

## Check
```
python3 -I -B tools/check_contract_text.py --selftest        # from this directory
(cd research/d-liq/r6-draft && sha256sum -c MANIFEST.sha256)  # from the repository root
bash scripts/check_all.sh                                    # everything
```

## GPT's answers of 2026-11-12 to the four questions of the conformance-vectors PR (design proposals by GPT, applied to the text by Claude; not an independent review)
The vectors PR (separate, `research/d-liq/r6-draft/tests`) raised four questions on which this text was silent. GPT answered them as design proposals; they are applied here as a text amendment, and the oracle and the vectors follow in that PR. Changes:
1. **Unknown keys per occurrence (7.7c).** One entry per occurrence, location-qualified: a top-level key as its name, a key inside `o` as `o.<name>`, sorted by code point of the written string, none dropped as a duplicate (`o.zz,zz`). This changes the `keys=` detail format fixed on 2026-11-11 (names only). The comparison key of 7.7f does not use it.
2. **`o.ps` without `o.s` (7.5a, 7.7b, 9, 10).** A new reason `ps_no_s`, evaluated after `ps_type` and before `ps_ne_s`, because the equality cannot be checked. The run-level pass now covers SIX `ps` / `st` reasons; the decided limit of section 9 is worded accordingly. (The smaller alternative would have been to read an absent `o.s` as `ps_ne_s`; GPT's wording asked for a specific reason, so a specific reason was added. One line to revert if GPT prefers the other.)
3. **Feed from the first valid `open` on (2.3a, 2.3b, 2.3c, 7.2, 7.7a).** The feed of a connection applies from its first valid `open` onward; a MSG recorded earlier has no feed, is `MSG_CONN_UNKNOWN`, is treated as a FORCE message (replay input and run-level check), also when the later `open` names KLINE. A CONN event recorded before the first valid `open` cannot be in conflict. This is a change for the case "connection opens as KLINE after a MSG", which the 2026-11-11 text could be read the other way (feed from the whole file).
4. **`o` not an object (7.5a).** MALFORMED by the message contract only; no `ps`/`st` reason; `st_top_level` is still checked on the top-level object independently of `o`.
New conformance cases 19 to 22 (contract section 10). Nothing else changed; the guard (`tools/check_contract_text.py`) passes; the unresolved items (`U`, `E_RANGE`, `k.x`, `L`) stay open and nothing is locked.
