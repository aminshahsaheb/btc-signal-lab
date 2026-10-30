# Move-Odds v0.1.2 package portability review — 2026-10-30

## Verdict

**Source package identity: PASS. Static result artifacts: preserved. Standalone reproducibility from a clean checkout: NOT PASS / not established. TradingView compilation: NOT TESTED.**

This review does not change the original v0.1.2 package. The source ZIP and its internal checksums remain preserved byte-for-byte. Any repair must be a new version or a separate verification harness.

## What was checked

- The standalone `MoveOdds_Panel_v0_1_2.pine` has SHA-256 `d07865ebf10a7f5908aca69a90f792c90af601ef36bb5c4ef76b0ae1c192a84d`.
- The original v0.1.2 source ZIP is pinned in `artifacts/SHA256SUMS.txt`.
- Its internal 16-file checksum manifest passes the repository verifier.
- The archived package includes the Pine source, 12 golden vectors, expected table text, `atlas_tiers.csv`, lookup arrays and previous static/replica outputs.

## Portability limitations found

1. `verification/replica_panel.py` hard-codes `A = "../atlas/"` and imports `common.py` plus `edges.json`, `cellmat.npz`, and `cells_meta.csv` from that external sibling folder. Those exact dependencies are not included under a sibling `atlas/` folder in this package layout.
2. `verification/lint_pine.py` reads source/helper paths from `sys.argv[1]` and `sys.argv[2]`, then loads `../atlas/atlas_tiers.csv`. The package contains a copy at `verification/atlas_tiers.csv`, but the script does not use that path.
3. `verification/emulate_table.py` explicitly opens `MoveOdds_Panel_v0_1_1.pine`, even in the v0.1.2 source package. That filename is not the active v0.1.2 Pine filename in this directory. The script also imports from the same external `../atlas/` dependency.
4. Consequently, the prior lint/replica output files are evidence that those checks were run in the original workspace, but the scripts are not yet a turnkey, self-contained verification suite for a fresh clone.

## Interpretation

- A passing checksum confirms that source bytes match the pinned package; it does not validate the code's semantics.
- The prior reported 141 lookup values / 0 mismatches and replica comparisons remain historical static-check outputs. Their original execution environment and data dependencies must be available to reproduce them independently.
- The Pine source has not been compiled in TradingView. No static Python check can replace that compiler/runtime check.

## Safe next step

Create a new, separately versioned verification harness that accepts explicit paths for (a) the current v0.1.2 Pine file, (b) the Risk-First helper used as a reference, and (c) the Atlas inputs. It should fail closed when any source path or hash is absent, print exact versions/hashes, and run from a clean checkout. Do not modify the archived v0.1.2 package or rewrite its old output logs to make the package appear self-contained.
