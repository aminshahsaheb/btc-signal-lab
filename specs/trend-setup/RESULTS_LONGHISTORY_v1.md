# Results: long-history structure check of Trend Setup v0 (v1, pre-registered)

Run 44965222548 on 2026-11-22 00:09 UTC (the sixth run; runs 1-5 were stopped by tool or source errors and are disclosed in the change log of `PREREG_LONGHISTORY_v1.md`). Tool sha256 `445e8a2b509151576da0ffd472a8f5db31d5a01da5b273e5b1b99b9bfca90ddb`, frozen rule `trendsetup.py` unchanged. The output below is copied unchanged from the run log; the reading under it is the author's.

**Descriptive only. Same author as the rule; synthetic tests only; no independent review. A pass would not have been evidence of future crypto returns, and this partial result is not a reason to change the rule (no tuning after seeing results).**

# Trend Setup v0: long-history structure check (frozen rule, unchanged)

**Pre-registered descriptive check on history this lab never used for this rule. A pass is not evidence of future crypto returns; costs 0.08% per side everywhere; hold = always long, no cost.**

| market | kind | first counted | years | rule per year | hold per year | rule Sharpe | hold Sharpe | rule max DD | hold max DD | avg exposure |
|---|---|---|---|---|---|---|---|---|---|---|
| S&P 500 | equity | 1971-01-13 | 55.8 | +2.4% | +8.2% | 0.35 | 0.56 | -33% | -57% | 50% |
| Nasdaq Composite | equity | 1972-02-16 | 54.8 | +8.3% | +10.2% | 0.87 | 0.58 | -31% | -78% | 51% |
| Dow Jones | equity | 1993-01-13 | 33.8 | +1.7% | +8.4% | 0.26 | 0.57 | -33% | -54% | 52% |
| Nikkei 225 | equity | 1971-01-26 | 55.8 | +3.4% | +6.2% | 0.41 | 0.41 | -42% | -82% | 45% |
| FTSE 100 | equity | 1985-01-14 | 41.8 | +0.7% | +5.3% | 0.14 | 0.39 | -48% | -53% | 45% |
| DAX | equity | 1989-01-13 | 37.8 | +3.0% | +8.1% | 0.35 | 0.47 | -30% | -73% | 49% |
| Hang Seng | equity | 1988-01-22 | 38.8 | +2.6% | +6.0% | 0.28 | 0.36 | -34% | -65% | 43% |
| CAC 40 | equity | 1991-03-19 | 35.7 | -0.4% | +4.4% | 0.01 | 0.31 | -51% | -65% | 44% |
| Gold futures | commodity | EXCLUDED_BAD_DATA  | | | | | | | | |
| Silver futures | commodity | EXCLUDED_BAD_DATA  | | | | | | | | |
| Crude oil futures | commodity | 2001-09-13 | 25.2 | +2.0% | +4.1% | 0.20 | 0.31 | -43% | -91% | 42% |
| Copper futures | commodity | EXCLUDED_BAD_DATA  | | | | | | | | |
| 10y Treasury note futures | bond | 2001-10-10 | 25.1 | -0.7% | -0.1% | -0.19 | 0.01 | -21% | -26% | 36% |
| BTC/USD Bitstamp to 2017-08-16 | crypto_pre2017 | 2012-05-19 | 5.2 | +151.3% | +259.4% | 2.51 | 1.89 | -38% | -85% | 44% |

Equal-weight average of 10 non-crypto markets by date: rule +4.1% per year, Sharpe 0.77, max DD -23%; hold +8.3%, Sharpe 0.69, max DD -53% (1972-02-16 to 2026-11-18).

## Pre-registered criteria
- eligible markets (>= 10 counted years): 10 of 13 (a verdict needs at least 8)
- P1 rule max DD <= 0.75 x hold max DD in >= 70% of eligible markets: 70% -> MET
- P2 rule Sharpe >= hold Sharpe in >= 50%: 20% -> NOT MET
- median max-DD ratio (rule / hold): 0.55; median Sharpe difference (rule - hold): -0.16
- markets verdict: PARTIAL
- P3 BTC 2011-2017: rule max DD <= 0.75 x hold: ratio 0.45 -> MET

## Reading (author's, not part of the pre-registered output)

- **What held:** drawdown. The rule's maximum drawdown was smaller than the hold drawdown in all 10 eligible markets and about half of it at the median (ratio 0.55); P1 is met exactly at its 70% threshold (7 of 10; FTSE 100, CAC 40 and the 10-year note have ratios 0.91, 0.80 and 0.83, above 0.75). BTC 2011-2017 also met P3 (0.45).
- **What did not hold:** Sharpe. The rule's Sharpe was below the hold Sharpe in 8 of 10 markets (higher only for the Nasdaq Composite; Nikkei 225 level) (P2 not met, median difference -0.16), and its return per year was typically well below the hold return (ratio of per-year returns 0.14 to 0.82 where hold was positive, median about 0.4; Nasdaq Composite 0.82 and Nikkei 225 level on Sharpe were the closest). So the crypto-sample pattern "similar return to holding with a much smaller drawdown" was not reproduced in these markets; there it is "much smaller drawdown for a lower return". The average across the 10 markets has a higher Sharpe than the hold average (0.77 vs 0.69) because of diversification across markets, not because individual markets improved.
- **Handicaps in this check that favour the hold:** cash earns nothing (the rule is in cash about half the time; in the 1970s-90s cash paid several percent), and orientation/roll noise in futures. Both sides ignore dividends. Gold, silver and copper futures were excluded by the pre-registered 1% bad-row rule (inconsistent OHLC in Yahoo's spliced series), not because of their results.
- **BTC 2011-2017** is not virgin for the project and is one asset in one bull run: weak evidence. Rule Sharpe 2.51 vs hold 1.89 over 5.2 counted years.
- **Net:** the rule is best described as a drawdown-reduction (risk-management) rule. It is not shown to add return over holding anywhere except in crypto samples that the rule family was designed on. The forward paper track from T0 (2026-11-22 00:00 UTC) remains the only out-of-sample evidence for crypto.
