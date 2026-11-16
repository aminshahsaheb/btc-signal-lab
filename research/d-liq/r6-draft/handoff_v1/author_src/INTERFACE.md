# Interface of the verifier you write (journal contract v3, revision r6-draft)

This file is exact. Where it and the contract text (`contract/JOURNAL_CONTRACT_v3.md`) seem to differ about WHAT a verifier reports, the contract text wins and you write the difference into your `QUESTIONS.md`
(the contract asks you to do that wherever it is silent or ambiguous). This file only fixes the shape of the call, of the inputs and of the files you hand back.

## 1. Scope

You write a verifier of the contract text in `contract/JOURNAL_CONTRACT_v3.md` WITHOUT its CANDLE rules (6.2, 6.3 and 6.5 to 6.9). Everything else is in scope, including what the contract says about a CANDLE
event that violates 2.1 (it is `BAD_EVENT`). You are not asked to, and must not claim to, implement the whole contract.

**Capability boundary (fail closed).** After the parsing of 1.3 and the validation of 2.1, if the journal contains at least one event of type `CANDLE` that is VALID per 2.1 (it has every field 2.1 lists for
CANDLE, `msg_seq` included, with the listed types), `verify` MUST raise `UnsupportedJournal` and MUST NOT return a report: such a journal gets no verdict. A CANDLE event that violates 2.1 (for example one without
`msg_seq`) does not trigger the boundary; it is a `BAD_EVENT`. The input `boundary/B01` tests only this boundary. It is not a test of CANDLE support and nothing in this package implies that CANDLE is supported.

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

A dict with exactly these twelve keys (more keys are ignored):

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
