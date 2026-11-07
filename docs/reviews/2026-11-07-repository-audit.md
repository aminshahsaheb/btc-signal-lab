# Repository audit — 2026-11-07

Scope: the whole repository at `main` = `4a338f4` plus the live GitHub state (pull requests, issues, Actions runs, branches, the `main` ruleset, commit metadata), read on 2026-11-07. This is an engineering and process audit. It is not a market-data test and does not validate any trading edge.

Method: every top-level directory, document, workflow and script was read; duplicate content was found by hash and by pairwise comparison; relative links and backtick-quoted paths were resolved; the integrity scripts were run on `main`; the GitHub REST API was read for pull requests, issues, workflow runs, branches and the active ruleset; Git history was counted for author and committer addresses. An independent audit by GPT (2026-11-07) was compared claim by claim with the code and the live ruleset.

Not done: the v4 ZIP bytes are not available, so the v4-to-`main` path classification (A3 step 3) is not done; the contents of ZIP and PDF archives were not re-read; no Pine was compiled; nothing was run against Binance or KCEX.

## Result in one paragraph

The research discipline is good (failures preserved, hashes, CI, dated decisions). The infrastructure around it was drifting: five overlapping status documents each carried copied commit SHAs and counts, one of them still said the repository is Private, thirteen documents and Pine files exist in two trees, and the `main` ruleset required neither a review nor a passing check. Three code-level defects in the D-LIQ r4-draft package, found by GPT, are real. The documentation and CI items are fixed in the pull request that adds this file; everything else is listed below with its owner.

## Findings

Severity: P1 = can silently give a wrong conclusion or a wrong state; P2 = quality or reproducibility gap; P3 = minor.

| ID | Sev | Finding | Evidence | Status |
|---|---|---|---|---|
| F1 | P1 | `docs/REMOTE_SYNC_CHECKLIST.md` says "Visibility: Private" and "Keep the repository private"; the repository is Public (owner decision 2026-11-04). | File text; `VISIBILITY_CORRECTION_2026-11-04.md` | Fixed: HISTORICAL banner; `check_docs.py` rule R4 blocks the claim in living documents. |
| F2 | P1 | Status drift: the same "live synchronization" blocks (main SHA, tree counts, PR heads) were copied into README, STATUS, ROADMAP, EXECUTION_PLAN, LEDGER and REMOTE_SYNC_CHECKLIST and went stale after every merge (many reconciliation PRs: #11, #14, #18, #22, #24, #27 and #29 among them). | Those files at `4a338f4`; PR list | Fixed: one source of truth (`STATUS.md`), `INDEX.md`, README without SHAs, ROADMAP rewritten as a checklist, four HISTORICAL banners. |
| F3 | P1 | Thirteen files exist twice: `research/` legacy files ↔ `specs/` and `docs/`; `pine/` ↔ `tools/`. They differ only by a final newline (11 pairs) or not at all (2). New code also lives under `research/`, specs under `specs/`. | `scripts/check_mirrors.py` | Guard added (drift and unregistered files fail CI). Retirement is owner decision D-STRUCT-1. |
| F4 | P1 | Ruleset "Protect Main": pull request required, but 0 required approvals and no required status checks; no bypass actors. A change can be merged without review and without a passing check. | `GET /rulesets/26493235` | Owner action D-RULESET-1. Note: a required review needs a second GitHub identity, because the author cannot approve their own pull request. The D-LIQ r4-draft workflow is path-filtered and therefore cannot be a required check; only `verify` can. |
| F5 | P1 | The owner's personal email is the author address of 66 of 68 commits on `main` (committer address of 51). | `git log --format=%ae` | Owner decision D-PRIV-1 (enable "Keep my email addresses private"; history rewrite not recommended). |
| F6 | P1 | **CANDLE provenance** (GPT, confirmed). Raw CANDLE bytes are hashed but never parsed; `open` and `open_time_ms` are free fields; `CANDLE_NOT_LIVE` only rejects `recv_ms < open_time_ms`, so a REST/backfill kline received later passes. | `dliq_journal_verify_v2.py` lines 83, 230-238, 278; contract 2.1, 6.1-6.3 | Open: roadmap G-1. |
| F7 | P1 | **Replay can be skipped** (GPT, confirmed). `verify()` defaults to `replay_slots=False` and still returns `verdict: PASS`. Only the builder forces replay. | `dliq_journal_verify_v2.py` lines 5, 128, 280, 312 | Open: roadmap G-2. |
| F8 | P2 | **Rebuild not self-contained** (GPT, confirmed). `assemble.py` hash-pins only the PR #15 blob; the base directory has no full manifest check and the output is not compared with `MANIFEST.sha256`. Each patch script asserts exact text replacements, which limits but does not remove the risk. | `patches/assemble.py` | Open: roadmap G-3. |
| F9 | P2 | No independent SLOT-replay implementation; the differential corpus cannot exercise `SLOT_MISMATCH` or `SLOT_EARLY_WRITE`. Known since the r4 README. | `r4-draft/README.md` | Open: roadmap 2D. |
| F10 | P2 | CI gaps: no docs or mirror checks; the r4 workflow ran on every pushed branch as well as on the pull request (duplicate runs); no concurrency group or timeouts; third-party actions pinned by tag, not by commit SHA; no standalone Move-Odds check. | Workflow files | Partly fixed (docs and mirror checks, push only on `main`, concurrency, timeouts). Open: pin actions by SHA; standalone Move-Odds check (roadmap Gate 1). |
| F11 | P2 | No LICENSE; A3 steps 3-6 (v4 comparison, content-level secrets and rights review) are not done. | `docs/STATUS.md` | Owner decision D-LIC-1; A3 open. |
| F12 | P2 | PR #15 and PR #23 are Draft, behind `main`, and their code is superseded by `r4-draft`. PR #15 additionally carries eight review and decision documents that are not on `main`. | `git diff` against `main` | Owner decision D-PR-15-23. |
| F13 | P2 | About 48 MB of binaries are in Git (Atlas ZIPs, a 14 MB dataset, a 3 MB PDF). Immutable and hash-pinned, but every clone pays for them. | `du` per directory | Owner decision D-BIN-1. |
| F14 | P2 | PR #28 reached `main` before any independent review (owner merge, 2026-11-06 07:02 +0330). With F4 fixed (one required approval from a second identity) this would not have been possible. | PR #28 | Recorded in `STATUS.md` (PR #29). |
| F15 | P3 | The Move-Odds verification harness reads an external `../atlas/` folder and needs pandas and scipy, so it is not standalone. | `reviews/2026-10-30-move-odds-package-portability.md` | Open: roadmap Gate 1. |
| F16 | P3 | A local user path (`/Users/<name>/Downloads/...`) appears in the execution ledger. | `grep` | Left as is; it is a dated record. |

## GPT audit of 2026-11-07 — claim by claim

| GPT claim | Verdict | Note |
|---|---|---|
| CANDLE `open`/`open_time_ms` are not derived from the raw bytes; a REST kline after its open time passes `CANDLE_NOT_LIVE`. | Confirmed (F6) | |
| `verify()` defaults to `replay_slots=False` and can return PASS without replay. | Confirmed (F7) | The builder is not affected; direct callers are. |
| `assemble.py` does not pin the r3 base and does not check the final tree. | Confirmed (F8) | |
| The `main` ruleset has 0 required reviews and no required checks. | Confirmed (F4) | A required review needs a second identity; the r4 workflow cannot be a required check. |
| Two copies of the D-LIQ and Forward Journal specs; documents not aligned. | Confirmed and wider (F2, F3) | 13 pairs, not 4. |
| No LICENSE; v4 archive not compared. | Confirmed (F11) | |
| Independent replay is missing and the differential test does not cover `SLOT_MISMATCH`. | Confirmed (F9) | |
| Parts of the older material still name Ribbon + EMA50 as the nearest candidate. | Not re-checked | The 2026-11-03 decision closes that family on the used data; the statement was not searched for in every old document. |

GPT's staged order (stabilize the infrastructure, then data and verifier correctness, then close the D-LIQ protocol, then Forward Journal r7, then a limited live-format test, then the forward direction test, then trade conversion) matches the gate order in `ROADMAP.md`. It is adopted unchanged.
