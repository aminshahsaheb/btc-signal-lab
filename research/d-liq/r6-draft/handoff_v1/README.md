# D-LIQ r6: handoff package for the independent verifier (builder, harness, comparator) — DRAFT

**What this is.** The tools that turn the pinned sources into the two packages GPT specified on 2026-11-15 (decisions B, C and D) for the independent verifier of journal contract v3 (r6-draft): a BLIND input package for the author and a SEALED
package of expected outputs, with separate digests. It is a preparation step. **The independent verifier has NOT been started, the packages have been given to nobody, and nothing here is independently verified.** The author (a human who has seen neither the
primary verifier nor the oracle) is chosen by the owner; that is not decided here.

Draft, base `main`, not stacked, nothing merged. No PR merge. No LOCK. No collector. No T0. No probe. No live feed. No edge claim.

## Source pins (read as data; none of them is on `main`)

| What | Pin | Value |
|---|---|---|
| contract text (PR #39) | commit `53a7a3a820f720fc0c1b4a73cff4cfd774f0c56a`, file `research/d-liq/r6-draft/contract/JOURNAL_CONTRACT_v3.md` | sha256 `37d268343c193c86219db8883dccb3416c14ea8879c953d5c6b130dd00b84e95` |
| conformance vectors (PR #40) | commit `7bb06f0de2a5f0728ce9c02051a6b15f012a2e97` | 46 vectors + `EXPECT_DERIVED.json`, 93 files, digest `dfebd45409bac7c6e95e613cec7045758e1ab2b25bcc4f7559072e038c44d5d0` |
| primary verifier (PR #41), for the dry run ONLY | commit `1797b886f4c5323f3f374e35ec71f3bf5c05eb44` | never part of a package |

GPT, 2026-11-15, froze the contract and vector pins "for a controlled independent-verification handoff"; this does not approve the primary verifier or the wider D-LIQ project. `HANDOFF_PINS.json` holds all of this and the two package digests.

## The two packages (`make_handoff.py`, deterministic)

| Package | Files | Digest (sha256 of the `sha256sum` lines, byte-order sort, prefix `./`) |
|---|---|---|
| `dliq_r6_handoff_inputs` (BLIND, for the author) | 99 | `a9db29ad9ec90b7d6109b45437425045dccf5b570414435e77be2d5e05483167` |
| `dliq_r6_handoff_expected` (SEALED, stage 2 only) | 49 | `c34d97fe2a0b1d7db432e20a5c73a365c2d6c48c15e4a6d8431bc23e47559d61` |

* Blind package: the exact contract file and `CONTRACT_PIN.txt`; `INTERFACE.md` (exact interface, the anchor methods `get(journal_id, index)` and `latest(journal_id)`, report keys, scope, comparison rules, what to hand back); `README_FOR_AUTHOR.md`; the harness `run_inputs.py`;
  for each of the 46 vectors `inputs/<id>/journal.jsonl` and `input.json` (`journal_id`, `verify_time_ms`, `anchor`); and `boundary/B01` (below).
* Sealed package: for each id `expected/<id>.json` with the twelve report keys of contract 8.2 (the nine of `expect.json` plus `n_events`, `head_hex`, `outcomes` of `EXPECT_DERIVED.json`), `README_SEALED.md` and `SOURCE_PINS.txt`.
* Removed from what the author sees, as GPT ordered: `r6_only`, `r5_only_extra`, `cases`, `contract_refs`, `title`, `description`, and the descriptive part of every vector directory name (ids are bare: V01 ... V28c). Not copied at all: the oracle, the vector generator, `QUESTIONS.md`, the PROVENANCE files, any verifier source.
* Two-stage procedure (also in `README_FOR_AUTHOR.md`): stage 1 the author works blind, runs `run_inputs.py` and sends code, `QUESTIONS.md`, outputs and a statement; the owner records the code SHA and the outputs digest; only then does the sealed package reach the author and `compare_outputs.py` runs (stage 2).
  Every difference is settled against the contract text; a code change after stage 1 is a new version with a log naming the clause that justifies it.
* `build` writes deterministic `.zip` files too (`--zip`; stored, sorted, fixed timestamps); the package digest is defined on the directories, not on the archives.

**Capability-boundary test B01 (GPT, decision B).** One journal with a single CANDLE event that is valid per contract 2.1. Expectation: `UnsupportedJournal`, no verdict (fail closed). It is NOT a CANDLE vector and says nothing about CANDLE support; the independent task is explicitly the
non-CANDLE subset (INTERFACE.md section 1). Full CANDLE implementation needs its own vectors, tests and review later.

**Expected values are not an independent oracle.** The nine hand-written keys, `n_events`, `head_hex` and `outcomes` all come from the author of the text, the vectors, the oracle and the primary verifier (GPT, decision A: keep `EXPECT_DERIVED.json` as a supplement, with provenance, stage 2 only).
**Sealing is procedural.** The same values are public in PR #40 (`expect.json`, `EXPECT_DERIVED.json`); an author who reads that repository is no longer blind. `README_FOR_AUTHOR.md` says so and asks the author to declare anything seen.

**On "slot NONE / VALID" in some vector descriptions (GPT, 2026-11-15).** The journal's `SLOT.status` (`VALID`/`NONE`, 2.1) and the `slots` of the report (`OK`/`LATE`/`UNANCHORED`/`PENDING`, 5.5) are different things. The vector package is frozen (its digest is the pin), so the descriptions were NOT edited;
the author never sees them; the clarification is `INTERFACE.md` section 5, "Terminology".

## Results (local; CI runs the same steps on the pinned sources)

* `test_handoff.py`: 28 tests; with the sources given (`DLIQ_R6_VECTORS`, `DLIQ_R6_CONTRACT`) all run and pass; without them 9 are SKIPPED and say so (a skip is not a pass). Includes negative tests of the comparator (every one of the twelve keys; order of `missing`; multiset of findings; endpoint and order of `OUTCOME_UNLINKED`;
  exact FORCE details; malformed findings; fail-closed boundary; missing / unexpected outputs), of the harness (anchor semantics, boundary, error and non-dict recording, code and output hashes), and of the builder (determinism of the packages and the archives, pins, no removed field, bare ids, byte-identical contract and journals, digest = shell definition, refusal of other sources).
* `sanity_mutants.py`: 28 deliberate breakages of the comparator, harness, builder and a blind document, **28 of 28 noticed** (one, a non-deterministic zip timestamp, survived the first version of the tests, which built both archives in the same second; the test now checks the stored timestamps and the mutant is killed). Not the step 6 mutation suite.
* **Dry run with the primary verifier (package plumbing only; NOT independent).** `run_inputs.py` from the blind package with the primary verifier at `1797b88` as the module, then `compare_outputs.py` against the sealed package: **47 of 47 agree** (46 vectors plus B01 = `UnsupportedJournal`), `problems: 0`. This shows the blind package holds everything a verifier needs
  (anchor, journal_id, verify_time_ms) and that the sealed expectations equal what the primary produces under the stated comparison rules. It says nothing about the correctness of either. **Sensitivity check:** the previous primary head `de41160` (lenient base64 in the replay) through the same package fails exactly six ids: V24a, V24b, V24c, V25a, V25b, V26.
* `scripts/check_all.sh`: new step; the builder and dry-run parts run only with the sources given and print SKIP (not a pass) otherwise.

## Files

`make_handoff.py` (builder), `compare_outputs.py` (stage 2), `author_src/` (the three files copied into the blind package), `sealed_src/README_SEALED.md`, `HANDOFF_PINS.json`, `test_handoff.py`, `sanity_mutants.py`, `MANIFEST.sha256`; workflow `verify-dliq-r6-handoff.yml`.

```
python3 -I -B make_handoff.py --vectors <vectors of PR #40 at 7bb06f0> --contract <JOURNAL_CONTRACT_v3.md of PR #39 at 53a7a3a> --out <new directory> [--zip]
DLIQ_R6_VECTORS=... DLIQ_R6_CONTRACT=... python3 -I -B test_handoff.py
DLIQ_R6_VECTORS=... DLIQ_R6_CONTRACT=... python3 -I -B sanity_mutants.py
python3 -I -B compare_outputs.py --expected <sealed>/expected --outputs <outdir>/outputs
```

## Not done / not claimed

Nothing is self-certified. Same author as the text, the vectors, the oracle and the primary verifier; synthetic tests only; the real runs of the project are 27 frames from one machine behind a VPN; step 8 stays BLOCKED; independent review is absent; Pine was not compiled (not involved).
Not done: the independent verifier (step 4), the builder fix (step 5), the differential and mutation suite (step 6), the independent review and the separate LOCK decision (step 7). LOCK would not be a statement about profitability. D-LIQ is one data-integrity component of the wider multi-source trading assistant; it is not the decision engine.
