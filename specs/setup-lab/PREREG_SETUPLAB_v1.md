# PREREG_SETUPLAB_v1 — five pre-registered trade setups, one scoring run

**Status: FROZEN WITH THE CODE HASH BELOW, BEFORE ANY REAL-DATA OUTPUT.** No real-data result of this experiment exists when this file is committed. Nothing here is self-certified: the tests are synthetic and were written by the author of the code, and no independent review has taken place. A PASS in this document would mean "worth a forward test", never "proven".

`research/setup-lab/setuplab.py` SHA-256: `0bca0bd5a6e6698f931e377d599fa63072300ad197445932712e1a82ed0d069d` (also in `research/setup-lab/CODE_SHA256.txt`; CI and the run workflow refuse to run if the file differs).

## 0. Summary in Persian (for the owner)

- هدف: به‌جای اینکه کسی ستاپ بدهد، ۵ ستاپ مبتنی بر سازوکار بازار را **پیش از دیدن هیچ نتیجه‌ای** قفل می‌کنیم و روی تاریخچه‌ی بلند ۱۰ ارز عمومی Binance (۲۰۱۷ تا ۲۰۲۶، کندل روزانه) فقط **یک بار** می‌سنجیم. معیار پاس‌شدن از همین حالا ثابت است.
- BTC (داده‌ی سوخته) در حکم شرکت ندارد، فقط توصیفی گزارش می‌شود.
- حکم هر ستاپ: PASS / FAIL / INCONCLUSIVE. PASS یعنی «لایق آزمون رو‌به‌جلو با ریسک کوچک»، نه اثبات. FAIL یعنی همان ستاپ با همان پارامترها بسته می‌شود؛ نجات با تغییر پارامتر ممنوع است.
- ضعف‌های شناخته‌شده در بخش ۱۰ صادقانه آمده (بقا‌ـسوگیری، ورود در open کندل بعد، هزینه‌ی فرضی، کندل روزانه).

## 1. Question and mapping to RESEARCH_RULES rule 1

| Rule-1 item | Where |
|---|---|
| hypothesis, direction | §3 (each setup states its direction; long and short are tested together, side results are descriptive) |
| feature definition, sampling grid | §3, §4 (daily bars, UTC; signal at the close of bar i) |
| horizon | §3 (time exit T bars per setup) |
| cost model | §5 |
| primary statistic | §6 (mean net R per trade, pooled over assets) |
| practical-effect threshold | §7 P4 (0.10 R) |
| sample requirements | §7 P1 (n ≥ 300), P6, P7 |
| stopping rules | §8 (one scoring run; the only allowed re-run) |
| exclusions | §4 |
| analysis code hash | header; T0 = start of the scoring run, data end fixed at 2026-11-17 00:00 UTC |

Question: does any of five simple, mechanism-based setups have a positive expectation, after assumed costs, that is larger than what entering at random with the same exits would give, on a long public history of liquid spot pairs? This is a trading-economics test (RESEARCH_RULES rule 6): a PASS does not establish KCEX execution quality, which is a separate later stage.

## 2. How the setups were chosen (disclosure)

The author chose five well-known setup families from general market-structure reasoning, and fixed round-number parameters, **before running any code on any real data**. The selection is not blind: the author knows in general terms that trend-following was widely reported to have worked in crypto in 2017–2021, and that earlier projects in this repository tried other ideas (for example D-LIQ, move-odds, and eight hypotheses on BTC futures data reported by the product repository) on BTC. Those BTC datasets are **burned** (RESEARCH_RULES rule 2) and are not used for any verdict here. To the author's knowledge no earlier analysis in this project used the non-BTC series below; this is unverified. Parameters are not tuned, no parameter is read from data, and none will be changed after the run.

## 3. The five setups (frozen definitions)

Bars are daily UTC candles. All signals use only bars ≤ i (checked by a prefix-recomputation test). ATR14 is Wilder's ATR; RSI is Wilder's RSI; SMA/Bollinger use the close; Bollinger sd is the population sd over the 20 closes ending at bar i.

| id | setup | long if | short if | k | m | T |
|---|---|---|---|---|---|---|
| S1 | trend breakout | close[i] > max(high[i−20..i−1]) and close[i] > SMA100[i] | close[i] < min(low[i−20..i−1]) and close[i] < SMA100[i] | 2.0 | 1.5 | 30 |
| S2 | pullback in trend | RSI5[i] < 30 and close[i] > SMA200[i] | RSI5[i] > 70 and close[i] < SMA200[i] | 1.5 | 2.0 | 24 |
| S3 | overextension fade | close[i] < SMA20[i] − 2.5·sd20[i] | close[i] > SMA20[i] + 2.5·sd20[i] | 1.5 | 1.0 | 12 |
| S4 | compression then expansion | squeeze[i−1] and close[i] > max(high[i−10..i−1]) | squeeze[i−1] and close[i] < min(low[i−10..i−1]) | 3.0 | none | 14 |
| S5 | capitulation / blow-off fade | close[i]−close[i−1] ≤ −2.5·ATR14[i−1] and RSI14[i] < 30 | close[i]−close[i−1] ≥ +2.5·ATR14[i−1] and RSI14[i] > 70 | 3.0 | 0.5 | 10 |

`squeeze[j]` = the fraction of the 120 values ATR14/close at bars j−120..j−1 that are strictly below ATR14[j]/close[j] is ≤ 0.20 (volatility is among the lowest in its recent history).

Mechanisms (reasons to ask, not findings): S1 trend persistence and stop-order cascades at range breaks; S2 dips inside an established trend are bought by trend participants; S3 moves beyond 2.5 sd are often forced or liquidity-driven and partly retrace; S4 volatility clusters, and expansion out of compression tends to start a directional move; S5 forced-liquidation and blow-off bars overshoot and partly retrace within days.

Trade mechanics (all setups): entry at the **open of bar i+1**; D = k·ATR14[i]; stop = entry ∓ D; target = entry ± m·D if m is set; time exit at the **close of bar i+T**. Within a bar the **stop is checked first**; a gap through the stop fills at the open (worse), a target fills at the target price (not better). One position at a time per asset; a signal on the exit bar may be taken (entry at the next open). Trades that would run past the last bar are dropped. R = (side·(exit−entry) − cost·entry)/D.

## 4. Data, window, exclusions

- Source: Binance spot daily klines `1d` for the pairs below, via `data-api.binance.vision` (fallback `api.binance.com`), fetched inside the run workflow. No market data is stored in this repository (DATA_POLICY); the run prints a SHA-256 of each asset's OHLC arrays so anyone can compare a re-fetch.
- Pooled assets (10): ETHUSDT, BNBUSDT, XRPUSDT, ADAUSDT, LTCUSDT, TRXUSDT, LINKUSDT, XLMUSDT, ETCUSDT, NEOUSDT. Reference only, never in a verdict: BTCUSDT (burned).
- Window: bars opening on or after 2017-08-17 00:00 UTC and before 2026-11-17 00:00 UTC (so only closed bars). Time halves for P7 split at 2022-01-01 00:00 UTC.
- An asset is excluded (and listed in the report) if its fetch fails, its data are malformed (non-positive price, high<low, duplicate or non-daily timestamps), it has fewer than 1000 bars, or more than 5 missing days. If fewer than 7 pooled assets remain, the run is INVALID (infrastructure failure, not a result).
- Missing days (≤ 5) are bridged (consecutive bars are treated as adjacent); the count is reported.

## 5. Cost model

Round-trip cost 0.16% of the entry price in the primary analysis (assumption covering fees and slippage; the D-LIQ r1 draft records KCEX fees of maker 0% / taker 0.01% per side as read from the official text, much smaller than this; that figure is not re-verified here and real slippage on KCEX is unmeasured). Sensitivities: 0.06% and 0.30%. Funding and leverage are not modelled.

## 6. Statistics

- Primary statistic: mean net R per trade, pooled over the 10 assets.
- **Random-entry baseline:** for each asset and side, the mean R of entering at the open of **every** bar with the same stop/target/time exit (this removes drift, survivorship drift and the exit rule's own bias). Excess R of a trade = its net R minus that baseline for its asset and side.
- **Block bootstrap:** 30-calendar-day blocks, whole blocks resampled with replacement across all assets at once (so cross-asset correlation and clustering are kept), empty blocks stay in the pool, 10,000 resamples, seed 20261118 + setup index. The 1st and 99th percentiles of the resampled mean give the one-sided 99% bounds.
- Multiplicity: 5 setups, each tested one-sided at α = 0.01 (Bonferroni of 0.05). Long and short are one setup. This lab's cumulative count of tested setups is 5 after this run.

## 7. Verdict rule (applied mechanically; nothing is added afterwards)

A setup passes only if **all** hold:

- P1 n ≥ 300 trades;
- P2 99% lower bound of mean net R > 0;
- P3 99% lower bound of mean **excess** R over the random-entry baseline > 0;
- P4 mean net R ≥ +0.10 R (practical-size threshold, not a promise of profit);
- P5 mean net R > 0 at the 0.30% cost;
- P6 at least 5 assets have ≥ 20 trades and at least 60% of those have positive mean net R (not one coin);
- P7 both time halves (before / from 2022-01-01) have n ≥ 50 and positive mean net R.

Verdict: **PASS** if all hold. **FAIL** if P1 holds and the 99% upper bound of mean net R is below +0.10 R (an edge of practical size is excluded). Otherwise **INCONCLUSIVE**, listing the failed criteria; underpowered results are never turned into FAIL or PASS.

## 8. Run protocol

1. CI (`verify-setup-lab.yml`) must be green on this Draft PR: synthetic tests pass and the code hash matches.
2. The scoring run is triggered once by pushing `research/setup-lab/RUN_REQUEST.txt` (workflow `run-setup-lab.yml`). It re-checks the hash, re-runs the tests, fetches data, evaluates all five setups and prints the full report; nothing is suppressed.
3. A re-run is allowed only for an infrastructure failure (data not fetched, run INVALID), with unchanged code hash; the data hashes are compared and recorded.
4. If a defect in the code is found after the run, it is not patched silently: a v2 preregistration lists the defect, v1 results stay published, and the cumulative setup count is updated.
5. No parameter, asset, window, cost or threshold may change after any output is seen. A FAIL or INCONCLUSIVE closes the setup in this form (RESEARCH_RULES rule 10); a new idea needs a new preregistration and counts toward multiplicity.
6. All five results are reported, in the order above, with the full table and the per-asset, per-year and per-side detail printed by the code.

## 9. What a verdict permits

- FAIL or INCONCLUSIVE for all five: the setup-lab path yields no candidate; the project continues with levels 1–2 only (risk control, alerts) and says so.
- PASS for a setup: it becomes a **candidate** for (a) a daily-close Telegram alert, (b) a small-risk forward journal on KCEX with measured fees and slippage, (c) an independent code review. It is not called proven, validated or profitable until a forward gate says so.

## 10. Known limitations (stated before the run)

- Survivorship: all ten pairs still trade today; delisted coins are absent. This favours long-biased setups. The random-entry baseline removes much of the drift, but a PASS still needs forward confirmation; a FAIL is robust to this bias.
- Execution: entry at the next daily open (00:00 UTC, 03:30 Tehran). A manual trader will enter later and at a different price; this is not modelled.
- Daily bars only; no intraday path inside a bar beyond high/low, so stop-first ordering is a convention, not a measurement.
- Costs are an assumption; funding, leverage, liquidation and KCEX-specific prices are not modelled.
- Pooling assumes the five rules are meaningful across ten correlated coins; the block bootstrap handles correlation in time, not a regime that exists only in 2017–2021.
- Spot data are used as a proxy for the KCEX BTC market; BTC itself is burned and excluded.
- Synthetic calibration (below) used a geometric-random-walk generator without fat tails or volatility clustering, so real-data error rates may be worse than measured.

## 11. Synthetic calibration performed before the freeze (not evidence about any setup)

- 38 synthetic unit tests pass (causality by prefix recomputation, leaky-signal detection, stop-first, gap fill, cost, one-at-a-time, vectorised-vs-scalar equality on about 3,000 cases, pagination, validation, oracle detected as PASS).
- On random signals, 10 assets × 3,000 bars (about 1,280 trades), price-martingale walks, 100 seeds, cost 0: P2 passed in 1% and P3 in 1% of seeds (nominal 1%). With long-only random signals on a positive-drift walk, P2 alone passed in 14% of seeds while P3 passed in 1%; this is why P3 is a required criterion. Confidence intervals of a 100-seed estimate are about ±2 percentage points.
- On price-martingale synthetic data the baseline gross R of every setup's exit rule is within ±0.05 R of zero.

## 12. Environment

GitHub Actions `ubuntu-latest`, Python 3.12, `numpy==2.5.3` (the version the tests ran with). No secrets are used; the workflow has `contents: read` only.

## 13. Change log

- v1 (2026-11-19): first and only version; frozen at the code hash above.
