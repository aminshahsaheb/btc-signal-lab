# Research rules

- Preregister the hypothesis, feature, direction, thresholds, horizon, costs, exclusions, sample accounting, and analysis before evaluation.
- No parameter rescue, reverse-direction rescue, or post-hoc subgroup selection.
- Preserve every failed branch and its original specification.
- Distinguish `NONE`, invalid/missing feed, and missing-price outcomes. Never silently drop inconvenient observations.
- Distinguish snapshot notional from unique liquidation volume. Snapshot streams are not complete liquidation archives.
- Separate directional discrimination from actual net strategy returns.
- Include fees, spread, slippage, funding, outages, and rejected orders in execution claims.
- Use untouched future data for forward evidence. Previously reused historical data is not a clean holdout.
- Hash and version source files, raw data, code, protocol, and outputs.
- Static checks are not a TradingView compile; a compile is not a market validation; a market association is not profitability.
