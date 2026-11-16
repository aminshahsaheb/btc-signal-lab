# Independent verifier of journal contract v3 (r6-draft): package for the author, stage 1 (blind inputs)

You are asked to write, from the contract text alone, a verifier that is independent of the one that already exists. Independence is the point: your value is that your code shares no author, no code and no derivation with it.

## What you receive

* `contract/JOURNAL_CONTRACT_v3.md` and `CONTRACT_PIN.txt` (the exact commit and the SHA-256 of that file). Read the file as it is. Its revision notes are part of the pinned file and cannot be removed; they record how the text came about and mention other material of the project (verifiers, vectors, decisions)
  that you do not have and do not need. They are history. The numbered sections are the normative rules; where a revision note and a numbered section seem to differ, the numbered section prevails and you write the difference into `QUESTIONS.md`.
* `spec/`: the specification documents that the contract itself points to for the classification of a received message and for the parameters of the replay (message contract, protocol section 4 in Persian, the `message_contract` parameters), with their SHA-256 in `spec/SPEC_PINS.txt`.
  `INTERFACE.md` section 1.1 says how they rank against the contract. The task cannot be done from the contract file alone; it can be done from the contract plus these documents.
* `INTERFACE.md`: the exact interface, the scope (the contract WITHOUT its CANDLE rules, with the list of the CANDLE-related behaviours that remain required), the capability boundary, the specification documents and their precedence, the comparison rules and what you hand back.
* `inputs/` and `boundary/`: the journals, with `input.json` (journal_id, verify_time_ms, anchor entries) for each. Nothing says what an input is meant to test.
* `run_inputs.py`: the harness that runs your module on every input and records the outputs.

You do NOT receive, and must not look for or read: the expected outputs, any other verifier or its code, any test generator, the executable and the tests that the specification documents name (for example `dliq_msg_contract_v1.py`), any list of questions or answers about the contract, any notes on how the contract was derived. The public repository
`aminshahsaheb/btc-signal-lab` contains such material (pull requests and branches); do not use it. Work from this package only. If you have already seen any of it, say so in your statement (INTERFACE.md section 7) instead of working around it.

## How to work

1. Write the verifier as a person. If an AI assistant or code generator is used for any part, say exactly which part in your statement; this lowers the weight of the result and is not a violation.
2. Where the contract is silent or ambiguous, do what the contract asks (`QUESTIONS.md` next to your code, and the more conservative reading). Do not ask anyone for the intended answer: write down your own reading.
3. Write your own tests from the contract text. Journals are plain JSON lines; build your own.
4. Run the harness (INTERFACE.md section 7). Do not edit `run_inputs.py` or `INTERFACE.md`.
5. Send back the items of INTERFACE.md section 7 to the person who gave you this package. That person records the code SHA and the outputs digest FIRST. Only then does the sealed package of expected outputs reach you (stage 2).

## Stage 2 (after your record is frozen)

You get the expected outputs and the comparison script. Run it. Every difference is settled by reading the contract text, not by guessing what the other side intended: either your code or the expectation is wrong, or the text is ambiguous, and that is a
finding about the TEXT. Do not edit your code silently: a change after stage 1 is a NEW version with a log that names, for each change, the clause of the contract that justifies it. Your stage-1 code and outputs stay on record unchanged.

## Package integrity

Run, inside the directory that holds this file: `find . -type f | LC_ALL=C sort | xargs sha256sum | sha256sum`. The result and the file count (`find . -type f | wc -l`) must equal the values you were given with the package.
