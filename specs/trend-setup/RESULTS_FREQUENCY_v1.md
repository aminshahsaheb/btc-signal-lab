# Results: trade frequency of the frozen rule and the "act only on signal change" variant (runs 44966186808 and 44995032404)

Both runs use the frozen rule unchanged (`trendsetup.py` sha256 `e5e17e3d...`). Run 44966186808 used baskets of 1, 2, 5, 10 and 26 coins; run 44995032404 (commit 2b7eeb1) added baskets of 6, 7 and 8 coins because the owner's target is about 3-4 trades a week; all other numbers are identical between the two runs. The tables are the second run's own output, copied without edits. Descriptive and in-sample (burned data), same author; counting only, no performance information was used to choose a basket. Nothing here is evidence of an edge.

**خلاصه‌ی فارسی:** تعداد تغییرهای سیگنال در هفته (ورود، خروج، و کم/زیاد کردن اندازه): ۱ سکه ۰٫۶۱، ۵ سکه ۲٫۸۷، ۶ سکه ۳٫۴۷، ۷ سکه ۴٫۰۱، ۸ سکه ۴٫۶۲، ۱۰ سکه ۵٫۷۱، ۲۶ سکه ۱۴٫۶۵. فقط ورود/خروج: ۶ سکه ≈ ۱٫۱ و ۷ سکه ≈ ۱٫۳ در هفته. پس «۳–۴ معامله در هفته» یعنی حدود ۶ تا ۷ سکه، اگر کم/زیاد کردن هم معامله حساب شود.

# Trend Setup v0: trade frequency and a manual 'act only on signal change' variant

**Descriptive, in-sample, same author; the variant V1 was stated before the run and is not tuned. Nothing here is evidence of an edge.**

## Signal events (the frozen rule asks for a size change only when the signal changes)

| basket | coins | entries/yr | exits/yr | signal events per week |
|---|---|---|---|---|
| first 1 | 1 | 4.6 | 4.7 | 0.61 |
| first 2 | 2 | 8.9 | 9.1 | 1.18 |
| first 5 | 5 | 24.0 | 24.5 | 2.87 |
| first 6 | 6 | 29.3 | 29.9 | 3.47 |
| first 7 | 7 | 32.8 | 33.5 | 4.01 |
| first 8 | 8 | 38.2 | 39.1 | 4.62 |
| first 10 | 10 | 47.9 | 48.9 | 5.71 |
| first 26 | 26 | 132.5 | 135.0 | 14.65 |

BTC alone: 39 entries, 40 exits, 194 steps over 8.6 years; weight-change days per year: frozen rule (daily re-sizing) 156, V1 32.0.

## V1 (trade only on signal-change bars) against the frozen rule, same days, coins and costs

| basket | period | frozen rule per year | V1 per year | frozen Sharpe | V1 Sharpe | frozen max DD | V1 max DD | hold per year | hold max DD |
|---|---|---|---|---|---|---|---|---|---|
| all (26) | full | +20.5% | +23.4% | 1.00 | 1.04 | -29% | -26% | +19.2% | -82% |
| all (26) | from2023 | +15.5% | +19.6% | 0.83 | 0.92 | -23% | -26% | +14.0% | -69% |
| btc (1) | full | +25.5% | +24.0% | 0.92 | 0.87 | -44% | -41% | +23.5% | -77% |
| btc (1) | from2023 | +19.7% | +20.0% | 0.83 | 0.84 | -28% | -28% | +38.6% | -53% |
| top5 (5) | full | +26.6% | +30.8% | 1.12 | 1.18 | -36% | -33% | +31.6% | -75% |
| top5 (5) | from2023 | +18.4% | +22.1% | 0.89 | 0.97 | -24% | -26% | +23.2% | -66% |
| top10 (10) | full | +20.0% | +23.8% | 0.92 | 0.99 | -35% | -32% | +25.0% | -76% |
| top10 (10) | from2023 | +14.2% | +18.1% | 0.74 | 0.82 | -23% | -26% | +21.5% | -63% |

## Author's reading

- A "trade" here is any change of the signal (the signal is the share of five breakout channels that are on, so it moves in steps of 0.2): entering, leaving, or adding to / reducing a position. Enter-or-exit alone is about a third of that: 6 coins 1.14 and 7 coins 1.28 a week.
- The count is a consequence of the number of coins on a daily timeframe, not a performance choice. A basket of 6 to 7 of the first coins of the fixed list gives about 3.5 to 4 changes a week; which coins a KCEX account can trade, and at what fees, is not known to this lab.
- Variant V1 (act only on a signal-change bar and hold that size until the next one) was stated before the first run. In-sample it was not worse than the frozen daily re-sizing in the baskets reported (all 26 coins Sharpe 1.04 vs 1.00; top 5 1.18 vs 1.12; top 10 0.99 vs 0.92). This is a descriptive comparison on burned data, not a test.
