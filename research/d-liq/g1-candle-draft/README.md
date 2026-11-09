# D-LIQ G-1 draft — CANDLE provenance (proposal, shared parser, reference checker)

STATUS: **DRAFT / PROPOSAL.** Not locked, not adopted, not integrated into the r4/r5 verifiers or the builder. Branch `research/dliq-g1-candle-draft-2026-11-08`, stacked on PR #32 (r5-draft). No collector, T0, probe, live or edge claim. Everything here is synthetic.

What this package is
- `docs/G1_CANDLE_CONTRACT_PROPOSAL.md` — the contract amendment proposal (r6 text) for GPT's audit item G-1, with the decisions it needs ([DECISION A/A2/A3/B]) and seven questions for GPT.
- `src/dliq_kline_v1.py` — the shared kline-frame parser `parse_kline_frame` and the reference CANDLE checker `candle_checks` / `outcome_unlinked`. Standard library only; opens no socket.
- `src/test_dliq_kline_v1.py` — 64 synthetic tests (invented frames shaped like the documented kline message, not captured data).
- `mutation_check_kline.py` — 62 deliberate-bug mutants of the module; every one must be killed (equivalent mutants are documented in the script, not counted).
- `src/demo_topology_conflict.py` — reproducible, asserted demonstration that kline frames recorded as MSG break the current SLOT replay (slot NONE/MALFORMED; kline connection can become `primary_conn`) and that a per-connection feed filter fixes it.
- `MANIFEST.sha256`, `logs/` — hashes and run logs.

Findings worth reading first
1. The audit's design (record every raw frame as MSG, link the CANDLE by `msg_seq`) conflicts with replay section 7 unless connections carry a `feed` marker. See section 1 of the proposal and the demo.
2. The maximum receipt lag `L` is deliberately NOT given a value; the checker needs it as an argument and reports `CANDLE_LAG_UNSET` / no usable minute while it is `None`.

What is NOT done
- Real Kline capture (blocked: the exchange is unreachable from the owner's location; collector host undecided) — every field name is `[VERIFY]`.
- Integration into the primary and independent verifiers, the builder, the differential harness and the rebuild patches (plan in section 6 of the proposal).
- Independent review. The checker and its tests have one author. A passing run is a synthetic-fixture result only.

Run
```
python3 -I -B src/test_dliq_kline_v1.py
python3 -I -B mutation_check_kline.py .
python3 -I -B src/demo_topology_conflict.py
(cd . && sha256sum -c MANIFEST.sha256)
```
