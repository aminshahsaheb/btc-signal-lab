# D-LIQ r5-draft — replay cannot be skipped (G-2) and a reproducible rebuild (G-3)

STATUS: **DRAFT. Not locked. Not independently reviewed. Synthetic fixtures only.** Nothing here authorizes a collector, T0, a probe, a live feed, scoring or any trading action, and nothing here is evidence of a trading edge.

This package is `research/d-liq/r4-draft` (on `main`) plus the patch scripts in `patches/`. It answers point B (G-2) of the second GPT audit of 2026-11-07 and starts point C (G-3). It does **not** touch r4-draft.

## What changed relative to r4-draft

| Area | Change |
|---|---|
| Contract (`indep_verifier/JOURNAL_CONTRACT_v2.md`) | New section 7.6; hard finding `REPLAY_NOT_RUN`; verdict `INCOMPLETE`; `replayed` and `analysis_eligible` in every report. |
| Primary verifier | `replay_slots` defaults to **True**. The replay runs only when the argument is exactly `True`; any other value (`False`, `None`, `0`, `1`, a string) is a fail-closed opt-out that yields `replayed: false`, `analysis_eligible: false`, hard `REPLAY_NOT_RUN` (where 0) and verdict `INCOMPLETE` (or `FAIL` when another hard finding exists). It never returns `PASS` without the replay. |
| "Independent" verifier | Has no SLOT replay. It now reports `REPLAY_NOT_RUN` on every run, so its verdict is `INCOMPLETE` or `FAIL`, never `PASS`; it cannot be mistaken for a complete verification. |
| Builder | Refuses reports without the replay markers; flags a primary that did not replay (`PRIMARY_REPLAY_NOT_RUN`); checks `verdict` / `analysis_eligible` / `replayed` for consistency; adds `independent_replayed`, `independent_replay_required` and `analysis_eligible` to the summary. `REQUIRE_INDEPENDENT_REPLAY = True` (most conservative reading): **no build is analysis-eligible and no analysis CSV is written until an independent SLOT replay exists.** |
| Tests | Old section-level assertions are kept through an explicit adapter that asserts the new markers on every opt-out call; new tests state the contract directly (see `logs/`). |
| Checks | New mutants for every new rule (see `patches/mutation_check_*.py`), run by `scripts/check_dliq_strict.sh` on a throw-away copy. |

## Rebuild (G-3)

`python3 -I patches/assemble_r5.py <r4-draft dir> <empty output dir>` verifies the r4-draft directory completely (pinned `MANIFEST.sha256`, every file hash, no extra or missing file, no symlink), copies it, applies `patches/p01..p05`
(exact-text replacements that abort on any mismatch), refreshes the pinned verifier copies and writes the result. `python3 -I patches/check_rebuild.py check <assembled dir> <this dir>` compares it with
`patches/ASSEMBLED_MANIFEST.sha256` and with the committed tree. CI runs both in `verify-dliq-r5-draft.yml`.

Known limit: the r4-draft base itself was assembled from the r3 reconstruction (PR #23) and PR #15's builder; that step is checked separately in the same workflow
(`patches/check_r4_from_base.py`, the base commit is fetched by SHA and compared with a pinned manifest). It is only as durable as that commit stays reachable.

## What is NOT done (unchanged or still open)

- No independent SLOT replay exists (`ROADMAP.md`, order 3 second half). The differential harness still cannot exercise `SLOT_MISMATCH` or `SLOT_EARLY_WRITE`.
- G-1 (CANDLE provenance): raw kline bytes are still hashed but not parsed; `open` and `open_time_ms` are still free fields. Not in this package.
- The "independent" verifier is only partially independent (same model family, same author session).
- A replay over a journal with no reference SLOT is vacuous (`replayed: true`, nothing compared); the builder's own checks expose an empty analysis.
- All tests use synthetic journals. Step 8 (a real Binance message, a real anchor, a collector host) is BLOCKED.
