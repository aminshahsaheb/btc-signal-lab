# D-LIQ r6 primary verifier v3 (draft)

**Status: DRAFT, not locked, not reviewed, not independent.** It is step 3 of GPT's work order of 2026-11-11 (after the r6 text, PR #39, and the conformance
vectors, PR #40). It is written by the same author as the text, the vectors and the oracle, and it is derived from the r5 verifier (same author again). A pass
against the vectors says "this code agrees with hand-written expectations of its own author"; it is not independent evidence, it is not a LOCK, it is no
collector / T0 / live-feed / edge claim, and a TradingView (Pine) compile is not involved. Step 8 (a real Binance message, a real anchor, a collector host)
stays BLOCKED.

## What it is

A Python 3 standard-library verifier of **journal contract v3** (the r6 text of PR #39, file `research/d-liq/r6-draft/contract/JOURNAL_CONTRACT_v3.md`, which is NOT on `main`; it
is read from the PR branch). It implements, from the text:

**Contract text pin (changed in the revision of 2026-11-15, with this paragraph as the traceable record).** The first revisions of this PR were written against commit
`8969b65e716ba290041571ebf2ada64a7cc847db` of PR #39, which did not yet say what the verifier does for an undecodable `raw_b64` (Q1), whether 7.7 runs when the replay is off (Q3)
or how the two `OUTCOME_UNLINKED` findings differ (Q4). GPT decided those points on 2026-11-14 and authorized the amendment; it is commit `53a7a3a820f720fc0c1b4a73cff4cfd774f0c56a` of
PR #39 (the old commit is unchanged; the exact diff is `contract/AMENDMENT_2026-11-14.diff` on that branch). From the revision of 2026-11-15 the implemented text is `53a7a3a` (GPT, 2026-11-15, noticed that two docstrings still named `8969b65`; they now name `53a7a3a`, with `8969b65` only as history); everything that
`8969b65` says and `53a7a3a` does not touch is unchanged. The pinned vector revisions `d10ba97` and `0b2dc95` contain no case the amendment changes, and still run unchanged (below).

- genesis `DLIQ-JOURNAL-v3-GENESIS` (3.2); `CONN.feed` (`FORCE` | `KLINE`) required; `CANDLE.msg_seq` required (2.1);
- the feed of a connection = the feed of its first valid `open`, from that line on; `CONN_FEED_CONFLICT`, `MSG_CONN_UNKNOWN` (2.3);
- no event of a KLINE connection, from its first valid `open` on, is replay input (7.2);
- the six structural reasons for `ps` / `st` in the fixed order (7.5a) and the run-level pass over every FORCE-or-feedless message, independent of any SLOT:
  hard `FORCE_MSG_STRUCTURE`, soft `FORCE_UNKNOWN_KEY` (7.7);
- `CANDLE_LAG_UNSET` on every journal while `L` is unset, so the verdict is never `PASS` (6.8); verdicts `FAIL` / `INCOMPLETE` / `PASS` as in 8.2;
- STRICT, CANONICAL base64 (2.2): the text of `raw_b64` must be RFC 4648 section 4 base64 (alphabet and padding only, no whitespace, no other character) AND the standard encoding of its own
  bytes (no non-zero trailing bits); otherwise it is UNDECODABLE: `RAW_HASH_MISMATCH`, no bytes (`raw = None`, never empty bytes), a replay input that is MALFORMED (`undecodable_base64`),
  voiding a SLOT whose V(tau) contains its `recv_ms`, and NO structural check on it (7.7a). One decoder (`r6_rules.decode_raw`) serves the hash check, the replay and the run-level pass;
- report keys `n_events`, `head_hex`, `outcomes`, `candles` (always `{}`), `replayed`, `analysis_eligible` (all twelve keys of 8.2 are produced and, on the newest vector pin, compared).

**Not implemented:** the CANDLE rules (6.2, 6.3, 6.5 to 6.9). A journal with a valid CANDLE event raises `UnsupportedJournal` and gets no verdict (GPT,
2026-11-12, Q5). No SLOT / OUTCOME field is verified against a CANDLE. See `QUESTIONS.md` for every place where the text was silent and a reading was chosen.

## Files

| File | What |
|---|---|
| `r6_rules.py` | ALL r6-specific logic (the only new module): strict parse of a frame, the six reasons, unknown keys, feed of a connection, feed findings, run-level findings. Strict, CANONICAL base64 decoding (`decode_raw`, the only decoder of the package; a unit test enforces that). Imports nothing but `base64` and `json`. |
| `dliq_journal_verify_v3.py` | The r5 verifier with small, listed changes (below). |
| `dliq_msg_contract_v3.py` | The r5 message contract with ONE rule replaced (the `st_not_1` check becomes `R6.structure_reason`, same position in the order) and ONE input added (`classify(None)` = MALFORMED, reason `undecodable_base64`). |
| `PROVENANCE_verify.diff`, `PROVENANCE_msg_contract.diff` | Unified diffs of the r5 files this package was derived from against the files here. They are regenerated and checked by `make_provenance.py` (`--check` fails when stale); this is GPT's condition of 2026-11-12 (Q4) that code derived from r5 is documented and the r6 logic isolated. |
| `run_vectors.py` | Runs the verifier UNCHANGED on a directory of conformance vectors; same code path for every vector; prints the vector-set digest and the hashes of the verifier files; `--expect-digest`, `--expect-count`, `--require-derived`. Compares all twelve report keys of 8.2 (`n_events`, `head_hex`, `outcomes` from the vector set's `EXPECT_DERIVED.json`; the endpoint and the order of `OUTCOME_UNLINKED`) and says explicitly when it could not (the two older pins). Does not import the oracle or the vector generator and does not read `r6_only`, `r5_only_extra`, `cases`. |
| `test_primary_v3.py` | 54 unit tests on journals built inside the test (synthetic), including negative tests of the strict decoder (a table, an exhaustive comparison with a hand-written grammar on 137 257 short strings, seven trap texts that a permissive decoder reads as a valid BUY frame), of the runner and of the guards (no oracle import, standard library only, one strict decoder only, provenance current). |
| `sanity_mutants.py` | 49 deliberate breakages applied to a temporary copy of the package (the verifier files and the runner); the vectors and the unit tests must notice each. **Not the mutation / differential suite of step 6.** |
| `QUESTIONS.md` | Readings chosen where the text is silent (Q1 to Q8). |
| `MANIFEST.sha256` | SHA-256 of every file of this directory. |

## Provenance (what is r5 code and what is not)

- **Unchanged r5 code:** the chain, checkpoint, anchor, SLOT / OUTCOME bookkeeping, `parse_file`, the findings list and the replay driver of the r5 verifier; the
  message contract except its `st` rule.
- **Changed r5 code** (all visible in `PROVENANCE_verify.diff`): genesis string; `CONN` valid only with a `feed` in {FORCE, KLINE}; `CANDLE` valid only with an
  integer `msg_seq`; the hard / soft sets; the verdict rule (`INCOMPLETE` class = `REPLAY_NOT_RUN`, `CANDLE_LAG_UNSET`); the CANDLE bookkeeping loop is replaced by
  `UnsupportedJournal` and two `OUTCOME_UNLINKED` findings per EVAL outcome, entry first, each naming its endpoint (6.9 with `L` unset; GPT, 2026-11-14, Q4); the replay skips KLINE events and hands an
  undecodable `raw_b64` to the contract module as `raw = None` (explicit MALFORMED; GPT, 2026-11-14, Q1); the hash check calls the same strict decoder (`R6.decode_raw`) and the `import base64` of the r5 file is gone; `CANDLE_LAG_UNSET` is always appended; `candles` is returned; `open()` is wrapped in `with` (the r5 line leaked the handle).
- **New:** `r6_rules.py`, `run_vectors.py`, the tests, the sanity mutants, this directory's documents.

## Run

```
python3 -I -B test_primary_v3.py
python3 -I -B make_provenance.py --check
python3 -I -B run_vectors.py --vectors <dir with one sub-directory per vector> [--expect-digest HEX] [--expect-count N] [--require-derived]
python3 -I -B sanity_mutants.py --vectors <dir> [--expect-digest HEX] [--require-derived]
```

The vectors live in PR #40 and are NOT in this package. CI checks out the three pinned commits below as read-only data.

## Results (recorded against the exact commit and the vector-set digest)

The vector-set digest is `find vectors -type f | LC_ALL=C sort | xargs sha256sum | sha256sum`, run next to the `vectors` directory (the byte-order sort is part of
the definition; `run_vectors.py` computes the same value).

| Pin (PR #40 commit) | Vectors | Vector-set digest | Result |
|---|---|---|---|
| `d10ba979e23489f21328076b0cc8df5069961aec` (the pin GPT named, 2026-11-12, Q3 option B; first revision) | 34 (68 files) | `ca1f0352f99928088401425b1cd4f480519ac47a103a91a5c692e8bb97696c78` | 34 of 34 agree, `problems: 0` |
| `0b2dc95181e50388b5438d141e7ad13c1f91d13f` (adds V02g and V19b) | 36 (72 files) | `80fd19cbb9c2a4e861bbd692f72d5bed7cc2b43846f579de144399be05ab17a1` | 36 of 36 agree, `problems: 0`; `n_events`, `head_hex`, `outcomes` NOT COMPARED (the pin has no `EXPECT_DERIVED.json`; the run says so) |
| `7bb06f0de2a5f0728ce9c02051a6b15f012a2e97` (current head of PR #40; adds V24a-c, V25a-b, V26, V27, V28a-c and `EXPECT_DERIVED.json`; the 36 earlier directories are byte-identical) | 46 vectors + 1 supplement (93 files) | `dfebd45409bac7c6e95e613cec7045758e1ab2b25bcc4f7559072e038c44d5d0` | 46 of 46 agree, `problems: 0`, run with `--require-derived`: all twelve report keys of 8.2 compared |

Deviation from GPT's literal pin, stated openly: GPT's conditional acceptance of the vectors (Q1) named two coverage gaps (a non-string `o.s` and `ps_no_s`
before `st`); they were closed by V02g and V19b in `5b230f2`, so the verifier is run on `0b2dc95` as well. The 34 older vectors are byte-identical in all
three pins (each later set only adds directories), and the first pin is run unchanged, so nothing GPT asked for is dropped.

**The new vectors catch GPT's blocking finding.** The previous head of this PR (`de41160`, permissive decoder in the replay) run unchanged on the 46 vectors of `7bb06f0` fails SIX of them:
V24a, V24b, V24c, V25a, V25b and V26 (it counts the trap messages as BUY, reports `SLOT_MISMATCH` against a journal that is right, and reports `FORCE_MSG_STRUCTURE` / `FORCE_UNKNOWN_KEY` for
messages that have no bytes); the other 40 agree. This was run once, by hand, for this record; it is not a CI step (CI runs the current package).

SHA-256 of the verifier files at the time of writing (the runner prints them on every run; a unit test fails if they differ from this table):

| File | SHA-256 |
|---|---|
| `dliq_journal_verify_v3.py` | `50998fa22669511b9e67a52d32938c445604191669c632236b27e4cb9b701648` |
| `dliq_msg_contract_v3.py` | `11d647ec2e5c2b23909808721889b5d108a7c393ab940adfa38aa836da2ad81a` |
| `r6_rules.py` | `7bf6e1b81758db90fdfdafb928dd3430934fa0a876726a5f1d7b45b03893cfa2` |

The first run of the verifier was green on all 36 vectors at once; that was treated as suspicious, not as success. `sanity_mutants.py` then showed that 38 of 38
deliberate breakages were noticed, 7 of them by the unit tests only (the vectors of that time pinned nothing about undecodable base64, a CANDLE without `msg_seq` and an EVAL outcome).
**Since 2026-11-15:** 49 breakages (38 older, 11 new: the canonical form not required, the replay decoding permissively, `n_events`, `head_hex`, an uncovered outcome reported COVERED, and six
mutants of the runner itself), run against the 46 vectors of `7bb06f0` with `--require-derived`: 49 KILLED, 0 survived. 41 are noticed by the vectors and the unit tests; 8 by the unit tests only
(the six runner mutants, which cannot be noticed by the vectors because a runner that compares less finds fewer problems, and two mutants of the old Q1 reading whose difference, the reason
string `undecodable_base64` against empty bytes, is not an output of the report). One further mutant, removing `validate=True` from `decode_raw`, is EQUIVALENT (the canonical comparison that follows
already rejects every text that a permissive decoding would skip characters of) and is not listed; the guard test keeps the call strict anyway.

## GPT's red-team review of 2026-11-14 against `de41160` (this revision answers it; it does not approve the implementation)

Disposition at the time: NOT ACCEPTED YET. (1) BLOCKING: the replay decoded `raw_b64` permissively while the hash check was strict, so `e!30=` became `{}` and could be counted: FIXED, one strict
canonical decoder, negative tests, six vectors that catch the old behaviour (above). (2) The runner did not compare `outcomes`, `n_events`, `head_hex`: all three are normative report keys
(8.2; 3.2 and 6.4 define them), the runner now compares them from `EXPECT_DERIVED.json` and says "NOT COMPARED" for a vector set without it; ordinary free-text details stay uncompared (listed in
`run_vectors.py`). (3) The three coverage gaps (undecodable base64, a CANDLE without `msg_seq`, an EVAL outcome with `L` unset) are covered by vectors of PR #40 at `7bb06f0`. (4) The contract text
was amended on PR #39 (`53a7a3a`, see the pin above). The independent verifier has NOT been started: the contract and the vector package are to be frozen first (GPT).

## Decisions of GPT, 2026-11-14, first reply (applied here; they do not approve the implementation)

The 36-vector revision `0b2dc95` is accepted as the current test-data candidate (GPT reviewed nine of its vectors directly: V02f, V02g, V12f, V17, V21, V23, V06, V15, V19b; this is not a
certification of all 36). Both pinned revisions stay in CI with their digest and count checks. QUESTIONS.md Q2, Q3, Q5, Q6, Q7, Q8 accepted as implemented; **Q1** accepted with a
clarification and **Q4** with a requirement, both applied in this revision and covered by tests (`test_q1_*`, the endpoint assertions of `test_an_eval_outcome_has_two_unlinked_findings_a_no_price_outcome_none`);
CANDLE stays unsupported. The independent verifier is to be written by a human author who has seen neither this code nor the oracle (a separate model instance only as a provisional,
lower-trust alternative); that choice and that step are not made here.

## What is NOT claimed

- Nothing here is self-certified: the author of the text, the vectors, the oracle and this verifier is one and the same; the tests are synthetic and written by
  that author; the real runs of the project are 27 frames from one machine behind a VPN.
- It is not an independent verifier (step 4 needs a different author with no shared logic), it is not the builder fix (step 5), not the differential and
  mutation suite (step 6), and not the independent review and the separate LOCK decision (step 7). LOCK would not be a statement about profitability.
- The CANDLE rules, the value of `L`, `U` = 250 ms, `E_RANGE`, the meaning of `k.x`, a real anchor and the collector host are open (see the contract's open items).
- No collector, T0, probe, live feed, scoring or trading action is authorized by this package, and no trading edge is established.
