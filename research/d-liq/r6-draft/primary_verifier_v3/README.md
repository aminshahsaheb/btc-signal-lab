# D-LIQ r6 primary verifier v3 (draft)

**Status: DRAFT, not locked, not reviewed, not independent.** It is step 3 of GPT's work order of 2026-11-11 (after the r6 text, PR #39, and the conformance
vectors, PR #40). It is written by the same author as the text, the vectors and the oracle, and it is derived from the r5 verifier (same author again). A pass
against the vectors says "this code agrees with hand-written expectations of its own author"; it is not independent evidence, it is not a LOCK, it is no
collector / T0 / live-feed / edge claim, and a TradingView (Pine) compile is not involved. Step 8 (a real Binance message, a real anchor, a collector host)
stays BLOCKED.

## What it is

A Python 3 standard-library verifier of **journal contract v3** (the r6 text of PR #39, commit `8969b65e716ba290041571ebf2ada64a7cc847db`, file
`research/d-liq/r6-draft/contract/JOURNAL_CONTRACT_v3.md`, which is NOT on `main`; it was read from the PR branch). It implements, from the text:

- genesis `DLIQ-JOURNAL-v3-GENESIS` (3.2); `CONN.feed` (`FORCE` | `KLINE`) required; `CANDLE.msg_seq` required (2.1);
- the feed of a connection = the feed of its first valid `open`, from that line on; `CONN_FEED_CONFLICT`, `MSG_CONN_UNKNOWN` (2.3);
- no event of a KLINE connection, from its first valid `open` on, is replay input (7.2);
- the six structural reasons for `ps` / `st` in the fixed order (7.5a) and the run-level pass over every FORCE-or-feedless message, independent of any SLOT:
  hard `FORCE_MSG_STRUCTURE`, soft `FORCE_UNKNOWN_KEY` (7.7);
- `CANDLE_LAG_UNSET` on every journal while `L` is unset, so the verdict is never `PASS` (6.8); verdicts `FAIL` / `INCOMPLETE` / `PASS` as in 8.2;
- report keys `candles` (always `{}`), `replayed`, `analysis_eligible`.

**Not implemented:** the CANDLE rules (6.2, 6.3, 6.5 to 6.9). A journal with a valid CANDLE event raises `UnsupportedJournal` and gets no verdict (GPT,
2026-11-12, Q5). No SLOT / OUTCOME field is verified against a CANDLE. See `QUESTIONS.md` for every place where the text was silent and a reading was chosen.

## Files

| File | What |
|---|---|
| `r6_rules.py` | ALL r6-specific logic (the only new module): strict parse of a frame, the six reasons, unknown keys, feed of a connection, feed findings, run-level findings. Imports nothing but `base64` and `json`. |
| `dliq_journal_verify_v3.py` | The r5 verifier with small, listed changes (below). |
| `dliq_msg_contract_v3.py` | The r5 message contract with ONE rule replaced (the `st_not_1` check becomes `R6.structure_reason`, same position in the order). |
| `PROVENANCE_verify.diff`, `PROVENANCE_msg_contract.diff` | Unified diffs of the r5 files this package was derived from against the files here. They are regenerated and checked by `make_provenance.py` (`--check` fails when stale); this is GPT's condition of 2026-11-12 (Q4) that code derived from r5 is documented and the r6 logic isolated. |
| `run_vectors.py` | Runs the verifier UNCHANGED on a directory of conformance vectors; same code path for every vector; prints the vector-set digest and the hashes of the verifier files; `--expect-digest`, `--expect-count`. Does not import the oracle or the vector generator and does not read `r6_only`, `r5_only_extra`, `cases`. |
| `test_primary_v3.py` | 35 unit tests on journals built inside the test (synthetic), including negative tests of the runner and guards (no oracle import, standard library only, provenance current). |
| `sanity_mutants.py` | 34 deliberate breakages applied to a temporary copy of the verifier; the vectors and the unit tests must notice each. **Not the mutation / differential suite of step 6.** |
| `QUESTIONS.md` | Readings chosen where the text is silent (Q1 to Q8). |
| `MANIFEST.sha256` | SHA-256 of every file of this directory. |

## Provenance (what is r5 code and what is not)

- **Unchanged r5 code:** the chain, checkpoint, anchor, SLOT / OUTCOME bookkeeping, `parse_file`, the findings list and the replay driver of the r5 verifier; the
  message contract except its `st` rule.
- **Changed r5 code** (all visible in `PROVENANCE_verify.diff`): genesis string; `CONN` valid only with a `feed` in {FORCE, KLINE}; `CANDLE` valid only with an
  integer `msg_seq`; the hard / soft sets; the verdict rule (`INCOMPLETE` class = `REPLAY_NOT_RUN`, `CANDLE_LAG_UNSET`); the CANDLE bookkeeping loop is replaced by
  `UnsupportedJournal` and two `OUTCOME_UNLINKED` findings per EVAL outcome (6.9 with `L` unset); the replay skips KLINE events and treats an undecodable
  `raw_b64` as empty bytes; `CANDLE_LAG_UNSET` is always appended; `candles` is returned; `open()` is wrapped in `with` (the r5 line leaked the handle).
- **New:** `r6_rules.py`, `run_vectors.py`, the tests, the sanity mutants, this directory's documents.

## Run

```
python3 -I -B test_primary_v3.py
python3 -I -B make_provenance.py --check
python3 -I -B run_vectors.py --vectors <dir with one sub-directory per vector> [--expect-digest HEX] [--expect-count N]
python3 -I -B sanity_mutants.py --vectors <dir> [--expect-digest HEX]
```

The vectors live in PR #40 and are NOT in this package. CI checks out the two pinned commits below as read-only data.

## Results (recorded against the exact commit and the vector-set digest)

The vector-set digest is `find vectors -type f | LC_ALL=C sort | xargs sha256sum | sha256sum`, run next to the `vectors` directory (the byte-order sort is part of
the definition; `run_vectors.py` computes the same value).

| Pin (PR #40 commit) | Vectors | Vector-set digest | Result |
|---|---|---|---|
| `d10ba979e23489f21328076b0cc8df5069961aec` (the pin GPT named, 2026-11-12, Q3 option B; first revision) | 34 (68 files) | `ca1f0352f99928088401425b1cd4f480519ac47a103a91a5c692e8bb97696c78` | 34 of 34 agree, `problems: 0` |
| `0b2dc95181e50388b5438d141e7ad13c1f91d13f` (current head of PR #40; adds V02g and V19b) | 36 (72 files) | `80fd19cbb9c2a4e861bbd692f72d5bed7cc2b43846f579de144399be05ab17a1` | 36 of 36 agree, `problems: 0` |

Deviation from GPT's literal pin, stated openly: GPT's conditional acceptance of the vectors (Q1) named two coverage gaps (a non-string `o.s` and `ps_no_s`
before `st`); they were closed by V02g and V19b in `5b230f2`, so the verifier is run on `0b2dc95` as well. The 34 older vectors are byte-identical in both
pins (the second set only adds two directories), and the first pin is run unchanged, so nothing GPT asked for is dropped.

SHA-256 of the verifier files at the time of writing (the runner prints them on every run; a unit test fails if they differ from this table):

| File | SHA-256 |
|---|---|
| `dliq_journal_verify_v3.py` | `d2078d5775d7c6b9bf0af5615cf54c08bf2afd3ce21193163f5bf91c6f928b5e` |
| `dliq_msg_contract_v3.py` | `1867c7316e790d3c213ca12d100a007c49bf54d2e1082f6f00bd1738a854825e` |
| `r6_rules.py` | `fb80cef398db37c339e04b6c1d69d29fe37c6a043e817efb08bcb81a92721ade` |

The first run of the verifier was green on all 36 vectors at once; that was treated as suspicious, not as success. `sanity_mutants.py` then showed that 34 of 34
deliberate breakages are noticed (31 by the vectors and the unit tests, 3 by the unit tests only: undecodable base64, a CANDLE without `msg_seq`, an EVAL
outcome; for these three the vectors pin nothing, which is information for the vector author).

## What is NOT claimed

- Nothing here is self-certified: the author of the text, the vectors, the oracle and this verifier is one and the same; the tests are synthetic and written by
  that author; the real runs of the project are 27 frames from one machine behind a VPN.
- It is not an independent verifier (step 4 needs a different author with no shared logic), it is not the builder fix (step 5), not the differential and
  mutation suite (step 6), and not the independent review and the separate LOCK decision (step 7). LOCK would not be a statement about profitability.
- The CANDLE rules, the value of `L`, `U` = 250 ms, `E_RANGE`, the meaning of `k.x`, a real anchor and the collector host are open (see the contract's open items).
- No collector, T0, probe, live feed, scoring or trading action is authorized by this package, and no trading edge is established.
