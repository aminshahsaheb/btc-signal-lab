# Project map

## Layers

1. **Movement timing — Move-Odds:** estimates when a large move may be more likely. It does not select Long or Short.
2. **Directional hypothesis — D-LIQ:** tests whether a pre-defined imbalance in delivered liquidation snapshots predicts continuation over a fixed horizon.
3. **Risk controls — Risk-First:** checks a manually proposed trade plan. It does not prove a directional edge.
4. **Execution — venue validation:** evaluates actual fees, spread, slippage, funding and operational failures.
5. **Evidence — Forward Journal:** records immutable protocol versions, data-quality events, signals, prices, costs, outcomes, and verification receipts.

## Evidence order

Source integrity → specification lock → data-quality feasibility → forward collection → pre-defined statistical analysis → independent execution validation.

A later layer cannot rescue a failure in an earlier layer. Any combined strategy requires a new preregistration and independent data.
