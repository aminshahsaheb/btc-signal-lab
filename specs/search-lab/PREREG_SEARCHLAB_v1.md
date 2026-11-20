# PREREG_SEARCHLAB_v1 — a declared search over 97 rules, one frozen confirmation on unseen coins and later years

**Status: FROZEN WITH THE CODE HASH BELOW, BEFORE ANY REAL-DATA OUTPUT.** No real-data result of this experiment exists when this file is committed. Nothing here is self-certified: the tests are synthetic and were written by the author of the code, and no independent review has taken place. A PASS in this document would mean "worth a forward test", never "proven". The expected outcome is INCONCLUSIVE (section 11 says why).

`research/search-lab/searchlab.py` SHA-256: `2e303a86e545c02892739bf43919889d55be8e99262fa4080e27247dc978323e` (also in `research/search-lab/CODE_SHA256.txt`; CI and the run workflow refuse to run if the file differs).

## 0. Summary in Persian (for the owner)

- هدف: پیدا کردن «بهترین قاعده» با روشی که فریب نمی‌خورد. ۹۷ قاعده‌ی از پیش‌اعلام‌شده (روند، شکست کانال، میانگین متحرک، برگشت به میانگین، RSI، مومنتوم مقطعی، روز هفته و ...) روی ۱۰ ارز و دوره‌ی ۲۰۱۸ تا ۲۰۲۲ **فقط برای کشف** رتبه‌بندی می‌شوند. سه قاعده‌ی برتر (یکی از هر خانواده) **به‌صورت مکانیکی و بدون دخالت انسان** انتخاب و قفل می‌شوند، به‌علاوه‌ی یک «کاندیدای مرجع» (روند Donchian ترکیبی، چون تنها نامزد دارای پشتوانه‌ی مقاله بود).
- سپس این ۴ قاعده **فقط یک بار** روی داده‌ای سنجیده می‌شوند که کشف هرگز ندیده: ۱۵ ارز دیگر و دوره‌ی ۲۰۲۳-۰۱-۰۱ تا ۲۰۲۶-۱۱-۱۶. مقدار «بهترین در جست‌وجو» همیشه خوش‌بینانه است؛ فقط این تأیید روی داده‌ی تازه حساب می‌شود.
- PASS یعنی «لایق آزمون رو‌به‌جلو با ریسک کوچک»، نه اثبات. FAIL و INCONCLUSIVE هم نتیجه‌ی معتبرند. **«ستاپ طلایی» ممکن است وجود نداشته باشد** و جست‌وجوی تکراری تا پیدا شدن آن ممنوع است (بودجه‌ی چندگانگی ثابت: ۹۷ آزمایش، ۴ تأیید).
- هشدار صادقانه (بخش ۱۱): در سنجش مصنوعی، وقتی ارزها مثل بازار واقعی به‌هم وابسته‌اند، **قدرت این آزمون تقریباً برابر خطای کاذب است**؛ یعنی حتی اگر اثر واقعی کوچکی باشد، احتمالاً INCONCLUSIVE می‌شود. فقط اثر خیلی قوی تأیید می‌شود. نبودن PASS = نبودن اثر نیست.

## 1. Question and mapping to RESEARCH_RULES rule 1

| Rule-1 item | Where |
|---|---|
| hypothesis, direction | §3 (each rule declares long-flat "LF" or long-short "LS"); no direction is chosen after seeing data |
| feature definition, sampling grid | §3, §4 (daily bars, UTC; decision at the close of bar i, held over bar i+1) |
| horizon | §3 (per rule); returns are daily |
| cost model | §5 |
| primary statistic | §6 (annualised Sharpe of the equal-weight volatility-scaled portfolio, plus alpha against the always-long benchmark) |
| practical-effect threshold | §7 Q4 (Sharpe ≥ 0.5) |
| sample requirements | §7 Q1 (≥ 700 confirmation days) |
| stopping rules | §8 (one run; the only allowed re-run) |
| exclusions | §4 |
| analysis code hash | header; data end fixed at 2026-11-17 00:00 UTC (exclusive) |

Question: among a fixed menu of 97 simple rules, does the best of them, as chosen on 10 coins in 2018–2022, still earn a positive, practically sized, cost-surviving risk-adjusted return, above simply holding the same coins, on 15 other coins in 2023–2026, with a pre-computed family-wise error budget? This is a trading-economics test on public spot data (RESEARCH_RULES rule 6); a PASS does not establish KCEX execution quality.

## 2. How the menu was chosen (disclosure)

The author wrote the 97 rules from general knowledge (trend, channel breakout, moving-average cross, price vs. moving average, Bollinger and RSI reversion, volatility breakout, cross-sectional momentum and reversal, day-of-week) with round-number parameters, after reading a small literature scan (abstract-level only; delivered to the owner as a report and not stored in this repository) and **after seeing the Setup Lab v1 results** (S1 and S4 slightly positive but inconclusive on the same ten "old" coins). Therefore the discovery stage is knowingly informed and optimistic; this is acceptable because the verdict comes only from the confirmation stage. No parameter is read from data. The menu, the families, the selection rule and every threshold are fixed here and cannot change after any output.

Burned or contaminated data (RESEARCH_RULES rule 2):
- BTC (Atlas and every BTC dataset inspected in this project): not used at all.
- The ten OLD coins were already used 2017–2026 in Setup Lab v1 (PR #43). They serve as the discovery set (2018-06-01 to 2022-12-31) and their later bars are only a **weak replication check (Q6)**, not independent evidence.
- The fifteen NEW coins and the 2023–2026 period: to the author's knowledge no earlier analysis in this project used them (unverified). The author, however, knows in general terms that 2023–2024 was a strong rally for many large coins; this is not data-blind knowledge.
- Cumulative tests registered in this lab: 5 (Setup Lab) + 97 declared trials (this lab); confirmatory tests here: K = 4.

## 3. The 97 rules (frozen definitions)

All signals at the close of bar i use only bars ≤ i (prefix-recomputation test over every rule). A rule outputs a target position in [−1, 1] per coin; LF = long or flat; LS = long or short. Bars are daily UTC candles.

| family | n | definition |
|---|---|---|
| TSMOM | 16 | long if close[i]/close[i−L]−1 > 0 (LS: short if < 0); L ∈ {10,20,30,60,90,120,180,250} × {LF,LS} |
| DONCH | 10 | Donchian channel: enter long when close[i] > max(high[i−N..i−1]) (LS: short when close[i] < min(low[i−N..i−1])); exit long when close < min(low over N//2 previous bars), exit short when close > max(high over N//2); N ∈ {10,20,30,55,100} × {LF,LS} |
| MACROSS | 12 | long if SMA(fast) > SMA(slow) (LS: short if <); (fast,slow) ∈ {(5,20),(10,50),(20,50),(20,100),(50,200),(30,150)} × {LF,LS} |
| PRICESMA | 10 | long if close > SMA(L) (LS: short if <); L ∈ {20,50,100,150,200} × {LF,LS} |
| ENSEMBLE | 2 | equal-weight average of the five DONCH states N ∈ {10,20,30,55,100}, {LF,LS}. `ENSEMBLE:DONCH5LF` is the literature-prior reference candidate |
| BBREV | 12 | Bollinger reversion: long when z = (close−SMA_L)/sd_L < −k, exit when z > 0 (LS: mirror short); L ∈ {10,20}, k ∈ {1.5,2.0,2.5} × {LF,LS} |
| RSIREV | 12 | Wilder RSI(p) < thr → long, exit when RSI > 50; p ∈ {2,5}, thr ∈ {10,20,30}; filter F = only while close > SMA200, N = none |
| VOLBO | 4 | volatility breakout: squeeze (ATR14/close in the lowest 20% of its previous 120 values) on bar i−1 and close > max(high[i−10..i−1]) → long (LS: mirror short), held H bars; H ∈ {7,14} × {LF,LS} |
| CSMOM | 8 | cross-sectional momentum, weekly rebalance (bar index mod 7 = 0): long top third by L-day return (LS: short bottom third); L ∈ {7,14,28,56} × {LF,LS}; needs ≥ 6 ready coins |
| CSREV | 3 | daily cross-sectional reversal: long bottom third, short top third by L-day return; L ∈ {1,3,7} |
| DOW | 8 | hold coins during bar i+1 only on weekday D (Mon..Sun, 7 rules) or on weekdays Mon–Fri (WK) |

Position size: direction × min(1, 0.50 / σ30), σ30 = annualised 30-day volatility of daily close-to-close returns up to bar i (no leverage above 1 per coin). Bar return is open-to-open (position decided at close i, return from open of bar i+1 to open of bar i+2). Portfolio return = equal-weight average over active coins (listed for ≥ 260 bars); days with fewer than 3 active coins are dropped.

## 4. Data, window, exclusions

- Source: Binance spot daily klines `1d` via `data-api.binance.vision` (fallback `api.binance.com`), fetched inside the run workflow. No market data is stored in the repository (DATA_POLICY); the run prints a SHA-256 of each coin's OHLC arrays.
- OLD coins (10, discovery and replication): ETHUSDT, BNBUSDT, XRPUSDT, ADAUSDT, LTCUSDT, TRXUSDT, LINKUSDT, XLMUSDT, ETCUSDT, NEOUSDT.
- NEW coins (15, confirmation): SOLUSDT, DOGEUSDT, AVAXUSDT, DOTUSDT, ATOMUSDT, UNIUSDT, AAVEUSDT, FILUSDT, ALGOUSDT, VETUSDT, NEARUSDT, XTZUSDT, ZECUSDT, DASHUSDT, HBARUSDT. These were chosen by the author as well-known liquid coins; all trade today (survivorship, section 10).
- Data start 2017-08-17; data end 2026-11-17 00:00 UTC exclusive (closed bars only). Discovery window 2018-06-01 .. 2022-12-31 (earlier bars are warm-up). Confirmation window 2023-01-01 .. 2026-11-16.
- **Stage 1 cannot see the future:** the OLD-coin fetch is cut at 2023-01-01; the confirmation data are fetched only after the selection has been computed and printed.
- A coin is excluded (and listed) if its fetch fails, data are malformed (non-positive price, high<low, duplicate or non-daily timestamps), it has fewer than 300 bars, more than 5 missing days, or (NEW coins) it has no bar on or before 2022-04-30 (warm-up). Fewer than 7 OLD or fewer than 8 NEW coins remaining = INVALID run (infrastructure failure, not a result).

## 5. Cost model

0.08% of the traded notional per side (0.16% round trip) in the primary analysis; high-cost sensitivity 0.15% per side. Cost is charged on the change of the volatility-scaled position (so reduced exposure is cheaper). Funding, borrow cost for shorts, leverage, liquidation and KCEX-specific prices are not modelled; LS rules assume a perpetual-style short without funding.

## 6. Statistics

- Primary statistic: annualised Sharpe of the daily equal-weight portfolio return (mean/sd × √365).
- Benchmark: always-long, same volatility scaling, same coins and days. Alpha = intercept of the regression of strategy daily returns on benchmark returns, annualised (×365).
- Block bootstrap: 30-day blocks, whole blocks resampled with replacement, 5,000 resamples, seed 20261120 + candidate index; one-sided bounds at the 1.25th and 98.75th percentiles (Bonferroni of 0.05 over K = 4). Sharpe and alpha bounds of a candidate come from the same seeded generator.
- Deflated Sharpe (Bailey–López de Prado; formula as implemented, not verified against the paper) is reported for the discovery ranking as a descriptive number only and enters no verdict.
- Discovery ranking: Sharpe over 2018-06-01..2022-12-31 on the 10 OLD coins. Mechanical selection: the best variant of each of the 3 families with the highest best-variant Sharpe (ties by id). The reference candidate `ENSEMBLE:DONCH5LF` is always added (K stays 4 even if it is already among the three).

## 7. Verdict rule (per candidate; applied mechanically)

A candidate passes only if **all** hold on the 15 NEW coins, 2023-01-01..2026-11-16, except Q6:

- Q1 at least 700 confirmation days with ≥ 3 active coins;
- Q2 the one-sided 98.75% lower bound of the Sharpe is > 0;
- Q3 the one-sided 98.75% lower bound of the alpha against the always-long benchmark is > 0;
- Q4 Sharpe ≥ 0.5 (practical-size threshold, not a promise of profit);
- Q5 Sharpe > 0 at 0.15% per side;
- Q6 Sharpe > 0 on the OLD coins over 2023-01-01..2026-11-16 (weak replication; see section 2).

**PASS** if all hold. **FAIL** if Q1 holds and the 98.75% upper bound of the Sharpe is below 0.5. Otherwise **INCONCLUSIVE**, listing the failed criteria. Underpowered results are never turned into PASS or FAIL. All candidates are reported, with Sharpe, interval, alpha, beta, maximum drawdown, turnover and the benchmark's own Sharpe, whether or not they pass.

## 8. Run protocol

1. CI (`verify-search-lab.yml`) must be green on the Draft PR: synthetic tests pass, code hash and preregistration hash match.
2. One run, triggered by pushing `research/search-lab/RUN_REQUEST.txt` (workflow `run-search-lab.yml`). It re-checks the hashes, re-runs the tests, runs Stage 1, prints the selection, then fetches confirmation data, runs Stage 2 and prints the full report.
3. A re-run is allowed only for an infrastructure failure (data not fetched, run INVALID) with an unchanged code hash.
4. A defect in the code found after the run is not patched silently: a v2 preregistration lists it, v1 results stay published, and the cumulative count is updated.
5. No rule, coin, window, cost or threshold may change after any output. FAIL or INCONCLUSIVE closes the candidate in this form (RESEARCH_RULES rule 10). After this run the 2023–2026 window and the 15 NEW coins are **burned** for any rule in this menu; a new idea needs a new preregistration and counts toward multiplicity.
6. If more than one candidate passes, no choice is made from confirmation performance. All passing candidates go to a forward journal; the reference candidate is preferred only on grounds of simplicity and prior.

## 9. What a verdict permits

- No PASS: the search yields no candidate. The project continues with level 1 (risk tool) and level 2 (UNPROVEN attention alerts), says so plainly, and a forward-only record is the only remaining route for small effects.
- PASS for a candidate: it becomes a **candidate** for (a) a portfolio-level weekly signal list, (b) a small-risk forward journal with measured fees and slippage, (c) an independent code review. It is not called proven, validated or profitable until a forward gate says so.

## 10. Known limitations (stated before the run)

- Survivorship: all 25 coins still trade; delisted coins are absent; the NEW list was chosen as well-known liquid coins. This favours long-biased rules, which Q3 partly controls; a PASS still needs forward confirmation.
- Execution: entry at the next daily open (00:00 UTC, 03:30 Tehran). A manual trader will enter later; not modelled. A rule that needs a portfolio of many coins is not the same as a single-asset manual setup.
- Coin returns are strongly correlated; the confirmation sample is effectively close to one common factor, which is why power is low (section 11).
- The 97-rule menu and the reference candidate were fixed after reading Setup Lab v1 results; the discovery stage is optimistic by construction.
- Costs are an assumption; funding, borrow, leverage and liquidation are not modelled. Daily bars only.
- Synthetic generators (section 11) have no fat tails or volatility clustering; real error rates may be worse.

## 11. Synthetic calibration performed before the freeze (not evidence about any rule)

- 26 synthetic unit tests pass (all 97 rules causal by prefix recomputation, a deliberately leaky rule is caught, lag and cost arithmetic, benchmark formula, no leakage between stages, selection mechanics, an oracle rule is confirmed, false-PASS after best-of-97 selection on random data ≤ 1 of 12 seeds, a rule with no power is not turned into FAIL, pagination/validation/exclusions).
- Real-size synthetic panels (3,377-day span, 10 OLD coins listing staggered from the start, 15 NEW coins listing from day 500 onwards, about 1,400 confirmation days, 1,000 bootstrap resamples, 24 seeds per scenario, daily volatility 4%, drift 0.0003/day, AR(1) daily autocorrelation φ per coin, common-factor weight 0.7 or independent coins), full pipeline including discovery:

| scenario | runs with at least one PASS (of 24) | candidate PASS | reference PASS |
|---|---|---|---|
| no autocorrelation, coins correlated | 1 | 1/96 | 0/24 |
| no autocorrelation, independent coins | 1 | 1/96 | 0/24 |
| φ = 0.05, coins correlated | 1 | 1/96 | 0/24 |
| φ = 0.10, coins correlated | 1 | 1/96 | 0/24 |
| φ = 0.05, independent coins | 4 | 7/96 | 1/24 |
| φ = 0.10, independent coins | 23 | 45/96 | 3/24 |

- Reading: the false-PASS rate under no effect is about 1 run in 24 (about 4%; 24 runs cannot resolve it better than roughly 1–20%). The lone PASSes under the null came from different seeds and different (mean-reversion) rules, not one artefact. **With correlated coins the power equals the false-PASS rate**: a trend of φ = 0.10 (stronger than the daily autocorrelation typically reported for crypto) is not confirmed. Only an independent-coin, strong-effect world is confirmed reliably. A real effect of ordinary size will therefore usually end as INCONCLUSIVE. This limit comes from about 3.9 years of nearly one common factor, not from the code, and it was not "fixed" by loosening thresholds, because that would raise false PASSes. Before this, the first calibration on short windows (180 runs) had 0 to 1 false PASS.
- During calibration two defects were found and fixed in code before the freeze: NaN propagation for late-listed coins in Wilder/ATR/RSI, and an unsuitable information-ratio criterion (replaced by the regression-alpha criterion Q3). The reference candidate and K = 4 were added during calibration, using synthetic data only, after a diagnosis showed discovery cannot separate trend from noise with correlated coins.

## 12. Environment

GitHub Actions `ubuntu-latest`, Python 3.12, `numpy==2.5.3`. No secrets; workflows have `contents: read` only.

## 13. Change log

- v1 (2026-11-20): first and only version; frozen at the code hash above.
