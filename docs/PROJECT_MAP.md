# Project map

## Four separate layers

### 1. Move-Odds — timing of volatility/movement

The panel uses a historical Atlas lookup table to describe the relative frequency of large moves in the cells it displays. It is not a Long/Short indicator. Its historical results are not forward proof; the Pine source still needs real TradingView compilation and golden-vector comparison.

### 2. D-LIQ — candidate directional hypothesis

The current draft, `D-LIQ-SNAPSHOT-CONT4H-v1`, asks whether a weighted imbalance of delivered Binance USD-M liquidation snapshots over a fixed 15-minute window predicts continuation over the following 4 hours. It is only a hypothesis. The stream is a snapshot feed, not a complete liquidation tape. r1 is not locked and its review lists blocking specification issues.

### 3. Risk-First Helper — pre-trade risk checklist

The Pine helper uses manually configured account/risk/entry assumptions to evaluate a proposed plan. It does not predict direction, track live position state automatically, or verify exchange fills. Costs and inputs must match the instrument/account before use.

### 4. Execution — real venue economics

A reference return on Binance is not equivalent to a fill on KCEX. The execution layer requires separate pre-registration and timestamp-aligned observations of fees, spread, slippage, funding, and fills. It has not started.

## No silent combination

Move-Odds, D-LIQ, and Risk-First answer different questions. Do not multiply their scores, create a composite threshold, or optimize entry/stop/target on the same evaluation period. Every new combined hypothesis needs a new identifier, preregistration, multiplicity count, and independent forward data.

## Complete source inventory

See [`PROJECT_AUDIT_2026-10-30.md`](PROJECT_AUDIT_2026-10-30.md) for the full inventory and exclusions. Historical Move-Odds releases and journal r5/r6 are preserved under `tools/move-odds-panel/archive/`, `artifacts/archives/legacy/`, and `specs/forward-journal/archive/`.
