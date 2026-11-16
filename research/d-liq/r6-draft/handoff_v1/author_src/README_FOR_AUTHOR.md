# Independent verifier of journal contract v3 (r6-draft): package for the author, stage 1 (blind inputs)

You are asked to write, from the contract text alone, a verifier that is independent of the one that already exists. Independence is the point: your value is that your code shares no author, no code and no derivation with it.

## What you receive

* `contract/JOURNAL_CONTRACT_v3.md` and `CONTRACT_PIN.txt` (the exact commit and the SHA-256 of that file). Read the file as it is. Its revision notes mention how the text came about; they are history, not instructions for you.
* `INTERFACE.md`: the exact interface, the scope (the contract WITHOUT its CANDLE rules), the capability boundary, the comparison rules and what you hand back.
* `inputs/` and `boundary/`: the journals, with `input.json` (journal_id, verify_time_ms, anchor entries) for each. Nothing says what an input is meant to test.
* `run_inputs.py`: the harness that runs your module on every input and records the outputs.

You do NOT receive, and must not look for or read: the expected outputs, any other verifier or its code, any test generator, any list of questions or answers about the contract, any notes on how the contract was derived. The public repository
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
