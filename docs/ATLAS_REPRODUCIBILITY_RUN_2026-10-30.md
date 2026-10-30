# Atlas v1 reproducibility run — 2026-10-30

## Input identity

The uploaded compressed BTCUSDT 5m file was decompressed and matched to the exact Atlas `pkg_data.csv` dependency by SHA-256 prefix. The decompressed file is 45,203,887 bytes with SHA-256:

`0bea138cc96dfec0da229c6dce0107a99e2875a3ad3d34acca058674995affc3`

The original gzip is preserved byte-for-byte in `artifacts/data/`.

## Commands executed

In an isolated workbench extracted from `artifacts/archives/Atlas_v1_package.zip`, with the verified input placed at `../pkg_data.csv`:

1. `python3 build.py` — completed; 50,184 decision points, 164 cells, labels generated.
2. `python3 test_engine.py` — completed; all T1–T6 checks passed, including brute-force labels, anchor comparison, causality truncation checks, independent feature re-derivation, FVG checks, and NY-open DST behavior.
3. `python3 test_stats.py` — completed; independent pandas groupby implementation matched the statistics engine.
4. `python3 run_main.py` — completed; 984 tests, 984 testable.
5. `python3 run_placebo.py` — completed; 300 placebo draws per family.
6. `python3 tiers.py` — completed.
7. `python3 desc1.py`, `desc2.py`, `desc3.py` — completed.

## Selected reproduced outputs

- Decision points: 50,184.
- Cells: 164 across CAL, CALEV, CTX, FLOW, FVG, LOC, VOL.
- L2 move rate: 0.2942; UP 7,169; DOWN 7,595; NONE 35,412.
- Confirmation-window hourly anchor AUC reported by desc1: 0.669277; the Atlas output notes the all-5m-bar ledger anchor as 0.6721.
- Placebo: CAL/MOVE explicitly marked invalid for clock/hour/day cells because circular time shifts relocate clock effects; Bonferroni only. Other families report their placebo statistics in `placebo_summary.csv`.

## Critical interpretation

This run demonstrates that the archived Atlas code can be executed with the recovered, hash-matching input in the current Python environment and that its included internal tests pass. It does **not** create new independent evidence: this is the same historical, already-used dataset and frozen analysis. It does not establish a tradable directional edge, profitability after costs, or live-feed performance.

The Atlas package remains a descriptive research artifact. Its own README says the data are burned and no cell is a validated edge. Reproduced output files are preserved separately in `artifacts/reproduced/Atlas_v1_reproduced_outputs_2026-10-30.zip`; the original archive remains unchanged.
