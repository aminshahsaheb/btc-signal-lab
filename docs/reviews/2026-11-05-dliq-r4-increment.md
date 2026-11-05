# D-LIQ r4 increment — status record (2026-11-05)

**Scope.** Source-only Draft addition under `research/d-liq/r4-draft/`: the r4 changes ordered by GPT's r3 audit (2026-11-02), rebuilt on the r3-reconstruction (PR #23) and on the PR #15 builder. It is **not** r3.1, **not** a protocol lock, and **not** evidence of any trading edge. All tests are synthetic; no collector, T0, live feed, real anchor or market-return scoring was used.

**Recorded evidence (run in a fresh extraction of the package, package zip sha256 `160d64016357385348430dfc53c84135d25766fd2c946aec960b6d4330555234`).**
- Writer + primary verifier 219 checks, partially independent verifier 102 tests, message contract 59 checks, NONE-slot regressions 2 tests, builder end-to-end 17 tests: all pass.
- Differential corpus, seeds 11/12/13/14 run separately: 30105 synthetic journals each, 0 disagreements (the corpus never exercises `SLOT_MISMATCH`/`SLOT_EARLY_WRITE`: the independent verifier has no replay).
- 15 deliberate bugs (coverage rule, early-write boundary, helper, builder cross-check, replay flag, message-contract pin) are each detected by the new tests.
- The actual r3.1 verifier files (PR #15) differ from the r3-reconstruction verifiers only in one docstring line each.

**What it adds.** Contract §6.1e/§6.4/§7/§7.5 (per-OUTCOME coverage; mandatory SLOT replay; `SLOT_EARLY_WRITE`); `outcome_and_anchor` in the writer; `outcomes` and soft `OUTCOME_UNCOVERED` in both verifiers; builder delta (coverage cross-check against the raw journal, mandatory replay, message-contract pin, coverage-lag report).

**Open / not claimed.** No independent SLOT-replay implementation (GPT P0-3 is PARTIAL); real Binance message semantics (endpoint path unverified), external anchor, collector host, OPEN-17/18/21/23 and the entry-candle decision remain open; the independent verifier is only partially independent; PR #15 and PR #23 remain Draft and need independent review. See `research/d-liq/r4-draft/README.md`.
