# Research rules

These rules apply to the active workspace.

1. **Pre-register before outcome inspection.** Record the exact hypothesis, direction, feature definition, sampling grid, horizon, cost model, primary statistic, practical-effect threshold, sample requirements, stopping rules, exclusions, analysis code hash, and T0.
2. **Treat previously inspected history as burned.** Data that informed discovery, confirmation, model selection, thresholds, or debugging cannot become a fresh holdout by renaming it.
3. **One branch, one frozen candidate.** Do not run count-weighted and notional-weighted versions side by side unless multiplicity and the new experiment are declared before scoring.
4. **No post-failure rescue.** Do not flip continuation to reversal, change the window, adjust k, tune thresholds, or switch the feature after seeing the result. A new direction needs a new preregistration and an independent forward period.
5. **Preserve `NONE` and missingness.** Every scheduled decision must have a record, including no signal, invalid input, gaps, late messages, and missing prices. Never silently drop inconvenient slots.
6. **Separate signal evidence from trading economics.** Direction discrimination is not net strategy profit. Trading rules and KCEX execution costs are separate stages with separate locked tests.
7. **Never claim more validation than was run.** Static lint, Python replicas, package checksum checks, Pine compiler checks, live feed checks, backtests, forward tests, and venue fills are different kinds of evidence.
8. **Version changes explicitly.** Do not overwrite old preregistrations. Create r2/r3 etc., add a change log, and record SHA-256. Keep draft/locked status visible.
9. **Do not store secrets or live raw capture here.** Keep credentials out of Git. Do not push full OHLC or real-time message logs without an explicit data-handling decision.
10. **Default to a falsifiable result.** `FAIL` or `INCONCLUSIVE` closes the branch if that was the preregistered rule. No daily return target is a reason to force trades.
