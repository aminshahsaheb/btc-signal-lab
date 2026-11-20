# RESULTS_SEARCHLAB_v1 — result record of the single scoring run

**Status: RESULT PUBLISHED. All four candidates: INCONCLUSIVE. No candidate passed.** Nothing here is self-certified: the tests are synthetic and by the same author, and no independent review has taken place.

- Preregistration: `specs/search-lab/PREREG_SEARCHLAB_v1.md` (frozen with the code hash below before any real-data output).
- Code: `research/search-lab/searchlab.py`, SHA-256 `2e303a86e545c02892739bf43919889d55be8e99262fa4080e27247dc978323e`.
- Run: GitHub Actions workflow "Search Lab v1 scoring run (real public data)", run id 44700213346, commit `941e13e`, single run (no re-run), all 10 OLD and 15 NEW coins fetched, none excluded, data hashes below.
- The report below is the program output copied verbatim from the job log (nothing suppressed, nothing edited).

## Verdict (mechanical, per the preregistration)

| candidate | role | verdict | failed criteria |
|---|---|---|---|
| PRICESMA:L20LF | discovery | INCONCLUSIVE | Q2, Q3 |
| MACROSS:5_20LS | discovery | INCONCLUSIVE | Q2, Q3, Q6 |
| TSMOM:L10LF | discovery | INCONCLUSIVE | Q2, Q3 |
| ENSEMBLE:DONCH5LF | reference | INCONCLUSIVE | Q2, Q3 |

Per prereg §9: no candidate. The search yields no setup that qualifies for a forward journal as "confirmed". Per §8.5 the four candidates are closed in this form, and the 2023-01-01..2026-11-16 window and the 15 NEW coins are burned for this rule menu. Cumulative tests registered in this lab: 5 (Setup Lab) + 97 declared trials (this lab); confirmatory tests here: 4.

## Descriptive notes (written after the output; not used for any decision; nothing is tuned or re-selected from them)

- All four candidates had a positive Sharpe on the 15 unseen coins (0.70 to 0.88) above the always-long benchmark on the same coins and days (0.52), positive alpha point estimates (+0.08 to +0.30 per year), and stayed positive at 0.15% per side. The 98.75% intervals are wide (about −0.7 to +2.1 for Sharpe), so none is separable from zero or from holding. This is what the synthetic calibration (prereg §11) said to expect with strongly correlated coins and about 3.9 years: low power, so INCONCLUSIVE is not evidence of absence.
- The direction matches Setup Lab v1 (S1 and S4 slightly positive, inconclusive) and the abstract-level literature (trend following with volatility sizing). It does not prove that any of them is real.
- The discovery stage preferred fast trend rules (20-day price vs. SMA, 5/20 cross, 10-day momentum). On the unseen coins the slow, low-turnover reference ensemble (daily turnover 0.011 vs 0.051 to 0.064, max drawdown 0.24 vs 0.31 to 0.43) did at least as well in point estimate. Choosing it now because of that would be a post-hoc choice on confirmation data and is not allowed; it is a pointer for a new preregistration or a forward record only.
- Q6 (old coins, 2023+) is only a weak replication because those coins were already used in Setup Lab v1.
- Known limitations of the run are those in prereg §10 (survivorship, daily open entry, assumed costs, funding not modelled, one common factor).

## Program output (verbatim)

# Search Lab v1 results (searchlab-v1)

code sha256: `2e303a86e545c02892739bf43919889d55be8e99262fa4080e27247dc978323e`
Nothing here is self-certified: tests are synthetic and by the same author; no independent review exists.

## Stage 1: discovery (97 declared variants, 10 coins, 2018-06-01 .. 2022-12-31, cost 0.16% round trip)

Always-long vol-scaled benchmark: Sharpe +0.56, annualised return +0.27.

| rank | variant | Sharpe | ann. return | max DD | deflated-Sharpe prob. (descriptive) |
|---|---|---|---|---|---|
| 1 | PRICESMA:L20LF | +1.43 | +0.42 | 0.31 | 0.05 |
| 2 | PRICESMA:L20LS | +1.39 | +0.57 | 0.29 | 0.04 |
| 3 | MACROSS:5_20LS | +1.35 | +0.55 | 0.30 | 0.03 |
| 4 | MACROSS:5_20LF | +1.35 | +0.41 | 0.37 | 0.04 |
| 5 | TSMOM:L10LF | +1.28 | +0.39 | 0.41 | 0.03 |
| 6 | MACROSS:10_50LF | +1.25 | +0.37 | 0.33 | 0.03 |
| 7 | TSMOM:L10LS | +1.24 | +0.50 | 0.32 | 0.02 |
| 8 | TSMOM:L30LF | +1.22 | +0.36 | 0.38 | 0.02 |
| 9 | PRICESMA:L50LF | +1.21 | +0.36 | 0.42 | 0.02 |
| 10 | TSMOM:L20LF | +1.17 | +0.36 | 0.41 | 0.02 |
| 11 | MACROSS:10_50LS | +1.16 | +0.46 | 0.29 | 0.01 |
| 12 | TSMOM:L120LF | +1.15 | +0.33 | 0.37 | 0.01 |
| 13 | TSMOM:L30LS | +1.13 | +0.44 | 0.30 | 0.01 |
| 14 | DONCH:N30LF | +1.13 | +0.30 | 0.36 | 0.01 |
| 15 | DONCH:N20LF | +1.11 | +0.30 | 0.32 | 0.01 |

Mechanically selected (best variant of each of the best 3 families): **PRICESMA:L20LF, MACROSS:5_20LS, TSMOM:L10LF**; literature-prior reference candidate (always confirmed): **ENSEMBLE:DONCH5LF**; Bonferroni K = 4

## Stage 2: confirmation (15 new coins, 2023-01-01 .. 2026-11-16; frozen rules; one run)

| variant | role | days | Sharpe | 98.75% interval | alpha vs long-only (ann.) | beta | alpha 98.75% lower | high-cost Sharpe | old coins 2023+ Sharpe | verdict | failed |
|---|---|---|---|---|---|---|---|---|---|---|---|
| PRICESMA:L20LF | discovery | 1415 | +0.83 | [-0.64, +2.13] | +0.12 | +0.43 | -0.10 | +0.75 | +0.70 | **INCONCLUSIVE** | Q2_sharpe_lower>0, Q3_alpha_vs_longonly_lower>0 |
| MACROSS:5_20LS | discovery | 1415 | +0.76 | [-0.33, +1.79] | +0.30 | -0.14 | -0.11 | +0.69 | -0.01 | **INCONCLUSIVE** | Q2_sharpe_lower>0, Q3_alpha_vs_longonly_lower>0, Q6_old_coins_2023+_sharpe>0 |
| TSMOM:L10LF | discovery | 1415 | +0.70 | [-0.75, +1.98] | +0.08 | +0.45 | -0.13 | +0.60 | +0.58 | **INCONCLUSIVE** | Q2_sharpe_lower>0, Q3_alpha_vs_longonly_lower>0 |
| ENSEMBLE:DONCH5LF | reference | 1415 | +0.88 | [-0.52, +2.01] | +0.10 | +0.33 | -0.05 | +0.86 | +0.66 | **INCONCLUSIVE** | Q2_sharpe_lower>0, Q3_alpha_vs_longonly_lower>0 |

### PRICESMA:L20LF
- annualised return +0.22, max DD 0.43, mean daily turnover 0.051; always-long benchmark Sharpe on the same coins and days +0.52
- criteria: Q1_days>=700=yes; Q2_sharpe_lower>0=NO; Q3_alpha_vs_longonly_lower>0=NO; Q4_sharpe>=0.5=yes; Q5_high_cost_sharpe>0=yes; Q6_old_coins_2023+_sharpe>0=yes

### MACROSS:5_20LS
- annualised return +0.27, max DD 0.31, mean daily turnover 0.057; always-long benchmark Sharpe on the same coins and days +0.52
- criteria: Q1_days>=700=yes; Q2_sharpe_lower>0=NO; Q3_alpha_vs_longonly_lower>0=NO; Q4_sharpe>=0.5=yes; Q5_high_cost_sharpe>0=yes; Q6_old_coins_2023+_sharpe>0=NO

### TSMOM:L10LF
- annualised return +0.19, max DD 0.42, mean daily turnover 0.064; always-long benchmark Sharpe on the same coins and days +0.52
- criteria: Q1_days>=700=yes; Q2_sharpe_lower>0=NO; Q3_alpha_vs_longonly_lower>0=NO; Q4_sharpe>=0.5=yes; Q5_high_cost_sharpe>0=yes; Q6_old_coins_2023+_sharpe>0=yes

### ENSEMBLE:DONCH5LF
- annualised return +0.18, max DD 0.24, mean daily turnover 0.011; always-long benchmark Sharpe on the same coins and days +0.52
- criteria: Q1_days>=700=yes; Q2_sharpe_lower>0=NO; Q3_alpha_vs_longonly_lower>0=NO; Q4_sharpe>=0.5=yes; Q5_high_cost_sharpe>0=yes; Q6_old_coins_2023+_sharpe>0=yes

## Data
| symbol | status | bars | missing | first | last | sha256(data) |
|---|---|---|---|---|---|---|
| ETHUSDT | OK | 1963 | 0 | 2017-08-17 | 2022-12-31 | 02345b904a3fe4f2 |
| BNBUSDT | OK | 1882 | 0 | 2017-11-06 | 2022-12-31 | 30fac3b195db9632 |
| XRPUSDT | OK | 1703 | 0 | 2018-05-04 | 2022-12-31 | 624b320f9abbe5e3 |
| ADAUSDT | OK | 1720 | 0 | 2018-04-17 | 2022-12-31 | 25f3f2497a483d1a |
| LTCUSDT | OK | 1845 | 0 | 2017-12-13 | 2022-12-31 | 1d659955d4ac3776 |
| TRXUSDT | OK | 1665 | 0 | 2018-06-11 | 2022-12-31 | d4ab862bd2aa6565 |
| LINKUSDT | OK | 1446 | 0 | 2019-01-16 | 2022-12-31 | 5e2a5848a0d6094f |
| XLMUSDT | OK | 1676 | 0 | 2018-05-31 | 2022-12-31 | 91d274d06a1f4102 |
| ETCUSDT | OK | 1664 | 0 | 2018-06-12 | 2022-12-31 | 87fa6b9b938446a7 |
| NEOUSDT | OK | 1868 | 0 | 2017-11-20 | 2022-12-31 | 419c25b712f2ff92 |
| ETHUSDT (full) | OK | 3379 | 0 | 2017-08-17 | 2026-11-16 | 4fcf5f38c8d8412b |
| BNBUSDT (full) | OK | 3298 | 0 | 2017-11-06 | 2026-11-16 | 6d50e1144bc845ce |
| XRPUSDT (full) | OK | 3119 | 0 | 2018-05-04 | 2026-11-16 | 3d3cac5834017815 |
| ADAUSDT (full) | OK | 3136 | 0 | 2018-04-17 | 2026-11-16 | eae2723235656146 |
| LTCUSDT (full) | OK | 3261 | 0 | 2017-12-13 | 2026-11-16 | 082e8ddb0a68a56f |
| TRXUSDT (full) | OK | 3081 | 0 | 2018-06-11 | 2026-11-16 | 6cc7a7ce011cc609 |
| LINKUSDT (full) | OK | 2862 | 0 | 2019-01-16 | 2026-11-16 | 9ed2bd2f4c1ea307 |
| XLMUSDT (full) | OK | 3092 | 0 | 2018-05-31 | 2026-11-16 | b1efa74366f66a6f |
| ETCUSDT (full) | OK | 3080 | 0 | 2018-06-12 | 2026-11-16 | 68fa8cc976a7f879 |
| NEOUSDT (full) | OK | 3284 | 0 | 2017-11-20 | 2026-11-16 | df0312b881b06dfb |
| SOLUSDT (full) | OK | 2289 | 0 | 2020-08-11 | 2026-11-16 | 2a79e21ac34eb189 |
| DOGEUSDT (full) | OK | 2692 | 0 | 2019-07-05 | 2026-11-16 | 4d01c3cd78a0aa85 |
| AVAXUSDT (full) | OK | 2247 | 0 | 2020-09-22 | 2026-11-16 | 5dc8af57246f2b5b |
| DOTUSDT (full) | OK | 2282 | 0 | 2020-08-18 | 2026-11-16 | 1ead721dc890e61c |
| ATOMUSDT (full) | OK | 2759 | 0 | 2019-04-29 | 2026-11-16 | f3172118e45df5a7 |
| UNIUSDT (full) | OK | 2252 | 0 | 2020-09-17 | 2026-11-16 | 402c8daa59c6b72f |
| AAVEUSDT (full) | OK | 2224 | 0 | 2020-10-15 | 2026-11-16 | f911ee8a2ef3994e |
| FILUSDT (full) | OK | 2224 | 0 | 2020-10-15 | 2026-11-16 | e676e6dc48ffe3fa |
| ALGOUSDT (full) | OK | 2705 | 0 | 2019-06-22 | 2026-11-16 | 15aa92d7341d42a4 |
| VETUSDT (full) | OK | 3037 | 0 | 2018-07-25 | 2026-11-16 | ece0273ca8064be7 |
| NEARUSDT (full) | OK | 2225 | 0 | 2020-10-14 | 2026-11-16 | 34a69c9e13d92216 |
| XTZUSDT (full) | OK | 2611 | 0 | 2019-09-24 | 2026-11-16 | fa04d457ae3bf7b3 |
| ZECUSDT (full) | OK | 2798 | 0 | 2019-03-21 | 2026-11-16 | 2ca6223e2b930618 |
| DASHUSDT (full) | OK | 2791 | 0 | 2019-03-28 | 2026-11-16 | 1d6c001e757642fb |
| HBARUSDT (full) | OK | 2606 | 0 | 2019-09-29 | 2026-11-16 | b8bf9839194d83c4 |
