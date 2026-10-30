# Atlas v1 reproducibility run — 2026-10-30

## Input

The recovered gzip decompresses to the exact Atlas `pkg_data.csv` input by the hash prefix recorded in Atlas README. Full decompressed SHA-256: `0bea138cc96dfec0da229c6dce0107a99e2875a3ad3d34acca058674995affc3`.

## Commands completed

In an isolated workbench with the verified input at the expected relative path:

1. `build.py` — completed; 50,184 decision points, 164 cells.
2. `test_engine.py` — ALL PASS (T1–T6).
3. `test_stats.py` — independent pandas groupby comparison PASS.
4. `run_main.py` — completed; 984 tests, 984 testable.
5. `run_placebo.py` — completed; 300 placebo draws per family.
6. `tiers.py`, `desc1.py`, `desc2.py`, `desc3.py` — completed.

Selected outputs: L2 MOVE rate 0.2942 (UP 7,169; DOWN 7,595; NONE 35,412). Confirmation-window hourly anchor AUC reported by desc1: 0.669277; Atlas notes the all-5m-bar ledger anchor as 0.6721. CAL/MOVE circular-shift placebo is marked invalid for clock/hour/day cells; Bonferroni only.

Reproduced outputs are preserved separately in `artifacts/reproduced/Atlas_v1_reproduced_outputs_2026-10-30.zip` in the prepared v3 bundle.

## Interpretation

This shows the archived code runs with the recovered historical input and its included internal tests pass in this environment. It is not new independent evidence, not a fresh holdout, not a profitable trading strategy, and not a live-feed or execution test. The dataset is burned historical data.
