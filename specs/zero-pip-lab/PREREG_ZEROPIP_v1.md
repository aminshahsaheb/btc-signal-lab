# PREREG_ZEROPIP_v1 — "0-pip" entries on BTC 1-hour history: how common are they, and does any declared pattern before them survive the holdout?

**Status: FROZEN WITH THE CODE HASH BELOW, BEFORE ANY REAL-DATA OUTPUT.** No real-data result of this experiment exists when this file is committed. Nothing here is self-certified: the tests are synthetic and were written by the author of the code, and no independent review of the results exists. A PASS would mean "worth a forward paper test", never "proven". The expected outcome is NO_CANDIDATE (section 12 says why).

`research/zero-pip-lab/zeropip.py` SHA-256: `b93e1f997819e778e029adc2fd68a221cc03c99f3824209065466800d1ec6b2b` (also in `research/zero-pip-lab/CODE_SHA256.txt`; CI and the run workflow refuse to run if the file differs).

## 0. Summary in Persian (for the owner)

- درخواست مالک: «نقاط ۰ پیپ» را در کل تاریخچه‌ی BTC پیدا کنیم (ورودهایی که قیمت بعد از آن‌ها تقریباً هیچ‌وقت علیه ما نرفته)، بعد ببینیم چه الگوی مشترکی **قبل از** آن نقاط قابل‌دیدن بوده، و چه حد ضرر کوچک و حد سود مشخصی برایش می‌شود.
- تعریف دقیق (بخش ۲): ورود در بازشدن کندل ساعتیِ بعد از تصمیم؛ حد ضرر = ۱ برابر ATR(۱۴) (بخش ۸ فاصله‌ی ضرر را به درصد قیمت گزارش می‌کند)، حد سود = ۳ برابر فاصله‌ی ضرر، حداکثر ۲۴ ساعت. «ورود تمیز (۰ پیپ)» = به حد سود رسید و تا آن لحظه بیش از ۲۵٪ فاصله‌ی حد ضرر هم علیه ما نرفت. «صفرِ مطلق» در عمل وجود ندارد (اسپرد، لغزش، قدرت تفکیک کندل ساعتی)؛ برای همین آستانه‌ی ۲۵٪ اعلام شده است.
- دو بخش جداست. (الف) **توصیفی**: جدول‌ها نشان می‌دهند ورود تمیز چقدر نادر است، با حد ضرر ۰٫۵/۱/۲ ATR و حد سود ۲ یا ۳ برابر و هزینه‌ی ۰٫۰۴/۰٫۱۰/۰٫۱۶٪؛ و ویژگی‌های میانه‌ی ورودهای تمیز نسبت به همه‌ی ورودها. (ب) **تأییدی**: ۵۸۱ قاعده‌ی ساده‌ی از پیش‌اعلام‌شده برای هر جهت (خرید/فروش) فقط روی داده‌ی تا ۲۰۲۲-۱۲-۳۱ رتبه‌بندی می‌شوند؛ ۳ قاعده‌ی برتر هر جهت (در مجموع ۶ قاعده) **فقط یک بار** روی BTC در ۲۰۲۳–۲۰۲۶ و روی ۶ ارز دیگر سنجیده می‌شوند.
- PASS فقط اگر همه برقرار باشد: میانگین سود خالص هر معامله ≥ +۰٫۱۰R با کران پایین مثبت؛ **بهتر از «ورود در همه‌ی ساعت‌های آزاد» در همان دوره** (تا صعود بازار به‌تنهایی قاعده را تأیید نکند)؛ همین دو شرط روی ۶ ارز دیگر؛ و دست‌کم ۳ از ۴ سال مثبت. PASS یعنی «لایق آزمون رو‌به‌جلو»، نه اثبات.
- هشدار صادقانه: پیش‌بینی نویسنده NO_CANDIDATE است. هزینه‌ی رفت‌وبرگشت روی حد ضرر تنگ، بخش بزرگی از هر R است؛ در سنجش مصنوعی فقط اثر قوی تأیید می‌شود و اثر کوچک نه. همه‌ی تاریخچه‌ی BTC «سوخته» است و این سنجش فرضیه‌ساز است، نه گواه سود آینده.

## 1. Question and mapping to RESEARCH_RULES rule 1

| Rule-1 item | Where |
|---|---|
| hypothesis, direction | §2, §5 (both directions are declared; no direction is chosen after seeing data) |
| feature definition, sampling grid | §4 (hourly UTC bars; decision at the close of bar i, entry at the open of bar i+1) |
| horizon | §2 (24 bars primary; 12 and 24 in the descriptive grid) |
| cost model | §8 |
| primary statistic | §6 (ranking: week-clustered t of month-demeaned gross R; confirmation: mean net R per trade with a lift over the all-free-hours policy) |
| practical-effect threshold | §7 (mean net R ≥ +0.10 R) |
| sample requirements | §7 (≥ 80 BTC holdout trades, ≥ 150 pooled other-coin trades, ≥ 10 trades in each counted year) |
| stopping rules | §9 (one run; the only allowed re-run) |
| exclusions | §3 |
| analysis code hash, T0 | header; there is no forward period (T0 not applicable); data end 2026-11-23 00:00 UTC (exclusive) |

Question (the owner's three steps): (1) What is a "0-pip" entry, precisely? (2) How many exist in the BTC history, and what do they look like in hindsight? (3) Is there a pattern of **causal** information (known at the decision time) that picks entries with a better outcome than entering at any free hour, in years and on coins the ranking never saw, after costs? Steps 1–2 are descriptive; step 3 is the only confirmatory part and the only part that can produce a candidate.

## 2. Definitions

- A **decision** at hourly bar i uses only bars ≤ i. The **entry** is the open of bar i+1 (a market order placed right after the close of bar i).
- **Bracket**: stop distance D = a × ATR14(i) where ATR14 is the simple mean of the true range of the last 14 bars; stop = entry − D; take-profit = entry + k × D; horizon h bars. Within one bar the stop is assumed to hit first. A bracket still open after h bars exits at the close of bar i+h. R = (exit − entry) / D (so a stop is −1 R and a take-profit is +k R before cost).
- **Shorts** are evaluated as longs on the mirrored series (prices negated, high and low swapped, taker-buy volume replaced by taker-sell volume). Cost is always charged on the original price.
- **Cost**: a round-trip fraction c of the entry price, converted to R as c × entry / D, subtracted from every trade.
- **MAE** (maximum adverse excursion) = the largest distance below the entry reached by any bar's low from bar i+1 until the exit bar inclusive (the take-profit bar's own low counts, which is conservative), in units of D.
- **CLEAN ("0-pip") entry** = the take-profit was hit AND MAE ≤ 0.25 D. Exactly zero adverse excursion is not observable on hourly bars (the low of an entry bar is almost always below its open), so 25% of the stop distance is declared as the practical definition.
- **Primary bracket** (used by the confirmatory part): a = 1.0, k = 3, h = 24, c = 0.10%. **Descriptive grid**: a ∈ {0.5, 1, 2} × k ∈ {2, 3} × h ∈ {12, 24} × c ∈ {0.04%, 0.10%, 0.16%}, both directions, discovery and holdout periods.
- A decision hour is **valid** only if the entry bar, the ATR and every bar of the whole h-bar window exist (no gaps) and 480 bars of warm-up have passed. Invalid hours are counted and reported (hours per period are in the report) and never contribute; requiring the whole window (not only the bars until the exit) avoids a censoring bias.

## 3. Data, window, exclusions

- Source: Binance spot klines `1h` via `data-api.binance.vision` (fallback `api.binance.com`), fetched inside the run workflow. No market data is stored in the repository (DATA_POLICY); the run prints a SHA-256 prefix of each coin's arrays.
- BTC (discovery and holdout): BTCUSDT from its first bar (2017-08-17) to 2026-11-23 00:00 UTC (exclusive, closed bars only). Other coins (confirmation only, never used by the ranking): ETHUSDT, BNBUSDT, XRPUSDT, ADAUSDT, LTCUSDT, TRXUSDT, each from its own first bar.
- Missing hours stay as gaps (NaN). A coin is excluded (and listed) if its fetch fails, the data are malformed (non-positive price, high < low, non-hourly or non-increasing timestamps, an unexpected close time, taker-buy volume above volume, a bar past the data end) or more than 1% of its hours are missing. If BTCUSDT is unavailable the run is INVALID (an infrastructure failure, not a result). If other coins are excluded the confirmation uses the rest.
- **Split**: *discovery* = decisions whose latest possible exit bar (i + h) is before 2023-01-01 00:00 UTC; *holdout* = decisions whose entry bar opens on or after 2023-01-01 00:00 UTC. The last 24 hours before the split belong to neither (purge). Tail thresholds (§5) use only decisions whose information was complete before the split.

## 4. Features (all use bars ≤ i only; a prefix-recomputation test checks every feature on the original and the mirrored series)

Continuous (14): `dlow24`, `dlow168`, `dlow480` = (close − lowest low of the last 24/168/480 bars) / ATR14 (for shorts: distance below the highest high); `ret6`, `ret24` = (close − close 6/24 bars ago) / ATR14; `lowwick` = (min(open, close) − low) / (high − low) of bar i (for shorts: the upper wick); `body` = (close − open) / ATR14; `range` = (high − low) / ATR14; `downrun` = number of consecutive down bars (close < open) ending at bar i, capped at 8 (for shorts: up bars); `atrratio` = ATR14 / mean true range of the last 168 bars; `volratio` = volume of bar i / mean volume of the previous 24 bars; `tbr` = taker-buy volume / volume of bar i (for shorts: taker-sell); `tbr24` = the same ratio summed over the last 24 bars; `rounddist` = |close − nearest multiple of L| / ATR14 with L = 10^(floor(log10 close) − 1) (1,000 for prices 10,000–99,999; original price for both directions).

Boolean (6): `sweep24`, `sweep168` = the low of bar i is below the lowest low of the previous 24/168 bars and its close is above that level (for shorts: highs); `s_asia`, `s_eu`, `s_us` = the entry bar opens in UTC hours 0–7, 8–15, 16–23; `wkend` = the entry bar opens on a Saturday or Sunday (UTC).

## 5. Declared family of rules (frozen)

Per direction: 34 single rules (each continuous feature ≤ its 20th percentile or ≥ its 80th percentile = 28 rules, plus the 6 booleans equal to 1) and 547 pairs (a conjunction of two singles on **different** features): 581 rules. Percentile thresholds come from the pre-split decisions of BTC (§3) and are applied **unchanged** to every other period and coin. A rule is eligible only with at least 300 discovery hours spread over at least 30 weeks. No other rule is ever evaluated.

## 6. Discovery: a ranking, not a test

For each direction, on discovery hours of BTC only: take the **gross** R of the primary bracket (costs excluded, so that cost arithmetic cannot masquerade as a pattern), subtract the mean of its calendar month (UTC; so a rule gets no credit for merely picking bull or bear months), and for every eligible rule compute the mean θ over the rule's hours and its **week-clustered** standard error (7-day blocks counted from 2017-08-17; neighbouring brackets overlap, so a week is the independent unit; SE² = G/(G−1) · Σ_w (a_w − θ n_w)² / N², G = weeks with a rule hour). Rank by t = θ/SE. The **top 3 per direction (6 rules in total)** are frozen and evaluated; ties are broken by declared order. No p-value is computed and no rule is "significant" at this stage.

Disclosure: an earlier draft of this experiment used a family-wise permutation p-value as an additional gate. Calibration on synthetic data of the real size (3 null variants, 40 random-walk series each) showed that the null was mis-calibrated in either direction depending on the rule (its z-variance was off by a factor of 0.5–2.4 for individual rules and its best-of-family p-value never fired), so the gate was **removed before any real-data output** and replaced by this ranking plus the out-of-sample verdict below. Multiplicity is controlled by the design: only 6 pre-ranked rules ever touch the holdout, and each needs several independent conditions at once (section 7).

## 7. Confirmation and verdict (each of the 6 rules, mechanically)

Policy for every number below: **one position at a time**. Walk through time; at the first signal while flat enter; stay until the bracket resolves; a new decision may use the close of the resolving bar. The **baseline** is the same policy applied to every free hour (no rule) in the same period and coin.

- H1 (BTC holdout, entries from 2023-01-01 to the data end): n ≥ 80 trades; mean net R ≥ +0.10 with a 90% week-cluster bootstrap interval whose lower end is > 0; **and** the lift (rule mean − baseline mean, bootstrapped on the same resampled weeks) has a lower end > 0.
- H2 (the six other coins pooled, holdout period): n ≥ 150 trades; mean net R > 0 with a positive lower end; **and** a positive lower end of the pooled lift over the same coins' baselines.
- H3: at least 3 of the 4 calendar years 2023, 2024, 2025, 2026 (the last one partial) have a positive mean net R, each counted only with at least 10 trades.
- **PASS** if H1, H2 and H3 hold. **INCONCLUSIVE** if the trade counts required by H1 or H2 are not reached. Otherwise **FAIL**. Overall: **CANDIDATE_FOR_FORWARD_TEST** if at least one of the 6 rules PASSes, otherwise **NO_CANDIDATE**.
- Bootstrap: 2,000 resamples of calendar weeks, seeds 20261124 + (1 discovery trades, 2 BTC holdout, 3 other coins, 4 BTC lift, 5 other-coin lift). Intervals are 5th–95th percentiles.
- Reported but not part of the verdict: discovery-period trade statistics of each rule; the holdout mean at costs 0.04%/0.10%/0.16%; per-coin statistics; all-period other-coin statistics; the share of CLEAN trades.

## 8. Cost model

0.10% of the entry price per round trip in the primary analysis (about 0.05% per side), 0.04% and 0.16% as sensitivities. This is an assumption and not a measured KCEX cost: the owner states that KCEX charges no fee on this account, which still leaves spread and slippage, and the tight stops make cost a large share of each R (the report prints the median stop distance as a percentage of price; at stop = 0.4% of price a cost of 0.10% is 0.25 R, and the break-even win rate of a k = 3 bracket is (1 + cost_R) / (k + 1)). Funding, leverage and liquidation are not modelled; shorts are assumed to be possible without funding (the owner's rule is spot long-or-flat, so the short direction is research only).

## 9. Run protocol

1. CI (`verify-zero-pip-lab.yml`) must be green on the Draft PR: synthetic tests pass, code hash and preregistration hash match.
2. One run, triggered by pushing `research/zero-pip-lab/RUN_REQUEST.txt` on a `research/zero-pip-**` branch (workflow `run-zero-pip-lab.yml`). It re-checks the hashes, re-runs the tests, fetches the data and prints the full report plus the results as encoded JSON lines.
3. A re-run is allowed only for an infrastructure failure (data not fetched, run INVALID) with an unchanged code hash.
4. A defect in the code found after the run is not patched silently: a v2 preregistration lists it, the v1 results stay published, and the cumulative test count is updated.
5. No rule, coin, window, threshold, cost or feature may change after any output. NO_CANDIDATE closes the branch in this form (RESEARCH_RULES rule 10). No flipping of direction, no change of k, stop, horizon, feature or threshold after the result (rule 4); a new idea needs a new preregistration and counts toward multiplicity.
6. If more than one rule passes, no choice is made from holdout performance; every passing rule goes to a forward paper test, and the simplest is preferred only on grounds of simplicity.

## 10. What a verdict permits

- NO_CANDIDATE: the descriptive tables remain as information about how rare clean entries are, how large a stop must be, and what costs do to a tight stop; they are not evidence of a tradable pattern. The Trend Setup v0 paper record (frozen, separate) is unaffected.
- CANDIDATE_FOR_FORWARD_TEST: only a **forward paper test** under a new, separately dated preregistration with real KCEX fill prices recorded, after an independent code review. It is not called validated or profitable until a forward gate says so, and real money would start only at the owner's small-amount step.

## 11. Known limitations (stated before the run)

- All BTC history is burned (RESEARCH_RULES rule 2): the author has seen BTC's history in earlier labs, and the six other coins' daily history in the Setup Lab. The 2023–2026 holdout is temporal and out-of-sample for **this** ranking, but it is not independent of the author's prior knowledge that 2023–2025 was largely a rising market. The lift conditions in H1 and H2 exist because of that.
- A rule that captures nothing but market direction cannot pass (lift), but a rule that captures a real regime effect in 2023–2026 only (and not in 2017–2022, the ranking period) cannot be told apart from luck by this design; H3 asks for most years to agree.
- Hourly bars hide the order of events inside a bar: the stop-first rule is conservative for the stop and optimistic about nothing else, but "zero adverse excursion" cannot be observed exactly (section 2).
- Execution: a manual trader on KCEX enters seconds to minutes after the open of the next bar, not at the open; spread and slippage are inside the 0.10% assumption only roughly.
- The 6 other coins move together with BTC; H2 is less independent than six separate tests (the week-cluster bootstrap pools them on the same weeks).
- Survivorship: all seven coins trade today. Binance spot data only; no futures, funding or liquidation data.
- The feature panel and the family were chosen by the author (round-number percentiles, common indicators) and after discussing the owner's "0 pip" idea; they are knowingly incomplete (no order book, no multi-timeframe confluence, no discretionary chart patterns).
- The tests are synthetic and by the same author; the code was read by an independent reviewer only if section 13 says so.

## 12. Why NO_CANDIDATE is expected, and what the synthetic calibration showed (before the freeze; not evidence about BTC)

- Earlier labs (Setup Lab, Search Lab, the engine's replay of the break-out alerts) found no stable edge on this data; a tight stop with a 0.10% round trip costs about a quarter of an R; the author's prior for a PASS is below 10%.
- 30 synthetic unit tests pass (bracket outcomes against a brute-force reference for longs and shorts, including gaps; every feature causal by prefix; the discovery output unchanged when the holdout bars are replaced; thresholds from before the split; the week-clustered t against a direct computation; the verdict branches; fetch pagination, failover, validation, gaps; a planted pattern found; no false PASS on random walks with and without a strong drift, where the absolute criterion alone **would** have approved rules).
- Real-size synthetic runs (7 coins × 81,236 hourly bars, constant volatility, no fat tails, the full default configuration):

| scenario | runs | runs with a PASS | rule verdicts | best discovery t (median, range) |
|---|---|---|---|---|
| pure random walks | 12 | 0 | 72 FAIL | 3.6 (2.9–4.8) |
| random walks with a strong common drift (3e-5 per bar) | 12 | 0 | 72 FAIL | 3.8 (2.7–4.4) |
| extra drift 0.0003 per bar on bars starting 00–07 UTC (7.5% of one bar's standard deviation) | 6 | 0 | 36 FAIL | 3.9 (3.4–4.2) |
| extra drift 0.0008 per bar on bars starting 00–07 UTC (20% of one bar's standard deviation) | 6 | 6 | 17 PASS, 19 FAIL | 5.9 (5.1–6.8) |

- Reading: no false PASS in 24 runs without an effect (24 runs cannot resolve a rate better than roughly 0–12%); a moderate effect is **not** confirmed (costs and the +0.10 R threshold eat it); only a strong effect is. The absence of a PASS is therefore not proof of absence of any effect. This limit was not "fixed" by loosening thresholds.
- Defects found and fixed during calibration, before the freeze: NaN-order dependence in a brute-force reference; a censoring bias in the validity of brackets (now the whole window is required); a circular-shift null that kept periodic effects aligned; a block-resampling null with duplicated hours that made the test nearly powerless at real size; a permutation null whose per-rule variance was off by up to a factor of 2.4 (the gate was dropped, section 6).

## 13. Review status

Written by the author of the code. **No independent review of the code had been completed when this was frozen.** One attempt (a fresh reviewer agent of the same model family as the author, so independent only in the sense of not having written the code) was interrupted twice by an API rate limit and returned no findings. After the last code change the author ran only their own checks: the 30 synthetic tests, a smoke run on fat-tailed, volatility-clustered synthetic data with gaps, zero-volume bars and late-listed coins (no error), and the real-size synthetic scenarios of section 12. An independent review by the red-team auditor is requested after the run; a defect found then is handled by section 9.4 (v2 preregistration; the v1 results stay published), and any forward test is blocked until such a review has been done.

## 14. Environment

GitHub Actions `ubuntu-latest`, Python 3.12, `numpy==2.5.3`. No secrets; workflows have `contents: read` only.

## 15. Change log

- v1 (2026-11-25): first and only version; frozen at the code hash above.
