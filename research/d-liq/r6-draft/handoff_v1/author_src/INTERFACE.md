# Interface of the verifier you write (journal contract v3, revision r6-draft)

This file is exact. Where it and the contract text (`contract/JOURNAL_CONTRACT_v3.md`) seem to differ about WHAT a verifier reports, the contract text wins and you write the difference into your `QUESTIONS.md`
(the contract asks you to do that wherever it is silent or ambiguous). This file only fixes the shape of the call, of the inputs and of the files you hand back.

## 1. Scope

You write a verifier of the contract text in `contract/JOURNAL_CONTRACT_v3.md`, together with the specification documents of section 1.1. The task is the contract WITHOUT its CANDLE rules. Because some expected outputs still contain findings that sections 6.8 and 6.9
define in terms of CANDLE, this section says exactly what is in and what is out. You are not asked to, and must not claim to, implement the whole contract.

**NOT part of this task (not required in any expected output):** `CANDLE_CONFLICT` (6.2), `CANDLE_NOT_LIVE` (6.3 and the first bullet of 6.8), `CANDLE_LINK` (6.5), `CANDLE_PARSE` and the kline frame grammar (6.6), `CANDLE_FIELD_MISMATCH` (6.6), the reference-CANDLE rules (6.7), the
states of a candle (`USABLE`, `LAG_TOO_OLD`, ...) of 6.8, and the case of 6.9 in which a reference CANDLE exists and is USABLE.

**Still REQUIRED, because they hold while no candle can be USABLE, or concern a CANDLE event that violates 2.1:**

1. `candles` is `{}` in every report.
2. `CANDLE_LAG_UNSET` is reported on every journal, once, with `where` = 0 (6.8, "Decision B": `L` is unset). The verdict is therefore never `PASS` (8.2).
3. For every reference OUTCOME with status `EVAL`, exactly two `OUTCOME_UNLINKED` findings are reported, first `endpoint=entry`, then `endpoint=exit` (6.9 with `L` unset).
4. For an OUTCOME with status `NO_PRICE` neither of the two findings is reported (6.9).
5. **Capability boundary (fail closed).** After the parsing of 1.3 and the validation of 2.1, if the journal contains at least one event of type `CANDLE` that is VALID per 2.1 (it has every field 2.1 lists for CANDLE, `msg_seq` included, with the listed types), `verify` MUST raise
   `UnsupportedJournal` and MUST NOT return a report: such a journal gets no verdict. The input `boundary/B01` tests only this. It is not a test of CANDLE support and nothing in this package implies that CANDLE is supported.
6. A CANDLE event that violates 2.1 (for example one without `msg_seq`) does not trigger the boundary; it is a `BAD_EVENT` (2.1), and nothing else is said about it.

Everything else in the contract is in scope, including the mandatory replay of section 7 (`replayed` is `true` in every report of this task).

### 1.1 Specification documents and their precedence

The contract does not restate how a received message is classified, nor the parameters it uses; section 7.2 and 7.5a send you to the message contract and to protocol 4.2. Those texts are in `spec/` (verbatim; `spec/SPEC_PINS.txt` lists their SHA-256):

* `spec/07_MESSAGE_CONTRACT_v1.md`: the message-validity contract (classes MALFORMED / INELIGIBLE / ELIGIBLE, the slot rules).
* `spec/protocol_r3_section4_fa.md`: protocol section 4 (the authoritative text of 4.2 to 4.5), in Persian. Read it yourself or have it translated by someone who is not involved in this project; a translation is not normative.
* `spec/protocol_r3_appendixB_params.md`: the machine-readable parameter block; only its `message_contract` entries are in scope.

Order of precedence where they disagree: (1) the contract text, always; (2) the message contract; (3) the protocol extracts. Known cases: the contract's 7.5a REMOVES the rule `st_not_1`, adds the reason `undecodable_base64` and the six structural reasons, and so overrides what the message contract and protocol 4.2 say about `st`;
the parameter block's `journal.genesis` (`DLIQ-JOURNAL-v2-GENESIS`) is superseded by 3.2 (`DLIQ-JOURNAL-v3-GENESIS`); only the `message_contract` block of the parameter block is used. These documents also name source files, tests and fixtures of an earlier package (for example `dliq_msg_contract_v1.py`). None of them is part
of this task and you must not look for them: here the TEXT is authoritative. Where the documents are silent, ambiguous or contradict each other, write your reading into `QUESTIONS.md`; do not guess silently.

## 2. The call

Python 3, standard library only (no network, no wall clock: contract 8.3). One module that defines:

```python
class UnsupportedJournal(Exception): ...

def verify(path, anchor, journal_id, verify_time_ms) -> dict:     # contract 8.2
    ...
```

`path` is the path of a `journal.jsonl`. `journal_id` is a string, `verify_time_ms` an integer. The replay layer of section 7 is ALWAYS run (the harness calls `verify` with these four positional arguments and nothing else; if
your function has further parameters they need defaults that mean "the contract's behaviour"). The file is read as bytes; you must not modify it.

## 3. The anchor object (contract 4.1)

`anchor` has exactly two methods:

* `anchor.get(journal_id, index)` -> the entry (a `dict`) whose `index` equals the integer `index`, or `None` if there is none. An entry has at least `anchor_id`, `index`, `seq`, `head`, `time_ms`, `time_resolution_ms`, `time_uncertainty_ms`. `index` is an integer, `journal_id` a string.
* `anchor.latest(journal_id)` -> an `int`: the largest `index` among the entries, `0` if there are none.

The harness `run_inputs.py` builds it (class `Anchor` in that file) from the list `anchor` of the `input.json` of each input; one anchor serves one journal and ignores `journal_id`. Your code must not assume more.

## 4. The inputs

```
inputs/<id>/journal.jsonl     the journal, exactly as bytes
inputs/<id>/input.json        {"journal_id": <string>, "verify_time_ms": <integer>, "anchor": [<entry>, ...]}
boundary/B01/...              same shape; tests only the capability boundary of section 1
```

The ids are bare labels. They carry no meaning: do not infer anything about a journal from its id. Nothing is said about what an input is meant to test.

## 5. The report (contract 8.2 and the sections it cites)

The report MUST contain these twelve required keys. Additional keys are ignored.

| key | type | defined by |
|---|---|---|
| `verdict` | `"FAIL"`, `"INCOMPLETE"` or `"PASS"` | 8.2 |
| `findings` | list of `[name, where, detail]`: `name` a string, `where` an integer (8.4), `detail` a string | 8.2, 8.4 |
| `hard` | sorted list of the distinct hard finding names present | 8.2 |
| `soft` | sorted list of the distinct soft finding names present | 8.2 |
| `n_events` | integer N | 3.2 |
| `head_hex` | lowercase hex of `h_N` | 3.2 |
| `slots` | dict `tau_ms` -> `"OK"`, `"LATE"`, `"UNANCHORED"` or `"PENDING"` | 5.5 |
| `missing` | list of the missing `tau_ms` | 5.5 |
| `outcomes` | dict `tau_ms` -> `"COVERED"` or `"UNCOVERED"` | 6.4 |
| `candles` | dict (always empty in this task) | 8.2 |
| `replayed` | bool | 8.2 |
| `analysis_eligible` | bool | 8.2 |

Dict keys that are integers are written as decimal strings in the JSON files (the harness does that conversion; the comparison treats a key and its decimal string as the same).

**Terminology, to avoid a misreading.** The journal contains `SLOT` events with a field `status` that is `"VALID"` or `"NONE"` (2.1): that is what the writer recorded about a signal. The key `slots` of the REPORT
is a different thing: for every reference SLOT it states the anchoring state of its tau (`"OK"`, `"LATE"`, `"UNANCHORED"`, `"PENDING"`, 5.5). A journal can contain a `SLOT` with `status` `"NONE"` and the report can still say
`"PENDING"` for it, because the two words answer different questions.

## 6. How outputs will be compared (stage 2)

* An expectation "UnsupportedJournal" is met only by `{"unsupported_journal": true}` (no verdict).
* Otherwise the output must be a report with the twelve keys, and: `verdict`, `replayed`, `analysis_eligible`, `n_events`, `head_hex` must be equal; `hard` and `soft` equal as lists; `missing` equal as a sorted list (the contract does not fix its order);
  `slots`, `outcomes`, `candles` equal as dicts.
* `findings` are compared as multisets of `(name, where)`, plus: for `FORCE_MSG_STRUCTURE` and `FORCE_UNKNOWN_KEY` the exact `detail` string (7.7b, 7.7c); for `OUTCOME_UNLINKED` the endpoint (the detail BEGINS `endpoint=entry` or `endpoint=exit`, 6.9); the
  `OUTCOME_UNLINKED` findings of one OUTCOME must come in the order entry, then exit. Every finding must have the form `[string, integer, string]`.
* NOT compared: every other `detail` string, the relative order of findings other than `OUTCOME_UNLINKED`, extra keys.

## 7. What you hand back (stage 1)

Run `python3 -I -B run_inputs.py --module <your module>.py --inputs . --out <a new empty directory>`. It writes one `outputs/<id>.json` per input (a report, `{"unsupported_journal": true}` or `{"error": ...}`) and
`OUTPUT_RECORD.json` (sha256 of the harness, of every `.py` file next to your module, of every output, and the digest of the outputs). Hand back: your code (and its git commit id if you use git), your `QUESTIONS.md`, the whole output directory, and a
short statement of how the code was written (who wrote it; whether any AI assistant or other tool generated code; what you read besides this package; confirm that you have seen no expected output).
