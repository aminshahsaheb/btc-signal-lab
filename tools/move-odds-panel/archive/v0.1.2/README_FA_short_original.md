# Move-Odds Panel v0.1.2 — review patch

**Purpose:** display historical Binance-derived move-likelihood lifts. It is not a Long/Short signal.

## Changes from v0.1.1
1. The chart timeframe limit is now **1 hour or lower**. The previous script allowed up to 1 day even though it requests hourly data. On charts above 1 hour, `request.security()` can return only a lower-timeframe intrabar, so the displayed state may not be the latest complete UTC hour.
2. The atlas data source is fixed to `BINANCE:BTCUSDT.P`. The prior `input.symbol` allowed a user to change the source while the lift tables remained fitted to Binance data.
3. If the panel is displayed on a different chart symbol, the table warns that all state values come from Binance, not the chart's prices.

## Validation status
- The included Pine code has **not** been compiled in TradingView. This patch only corrects the two static-review findings above.
- The v0.1.1 ZIP's existing Python replica and table checks reported 0 mismatches for 141 lookup-table values and 0 membership differences for range/hour/weekday cells; the 24-hour-break definition differed in 5 historical cases because the atlas used a 5-minute window. Those are results reported by the package, not a fresh independent run against the raw atlas dataset in this patch.
- Before use, add the Pine script on TradingView and check that it compiles. For numerical validation, use a standard chart on `BINANCE:BTCUSDT.P`, preferably the 1-hour chart, and compare `golden_vectors.csv` from the v0.1.1 package in the Data Window.

## Important limits
- A coloured `lift` row does not indicate direction.
- A lift is relative to its period's base rate. The displayed implied percentage depends on the user-entered base-rate inputs.
- Showing the panel on a KCEX chart does not validate price-basis, spread, fees, or execution differences between Binance and KCEX.
