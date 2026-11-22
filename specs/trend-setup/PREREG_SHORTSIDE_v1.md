# Pre-registration: mirrored short side of Trend Setup v0, and alerts per week (v1)

Written 2026-11-22 (Tehran morning), before the tool has ever been run on real data and before any short-side number exists anywhere in this lab. Status: pre-registered, descriptive. Not evidence of future returns.

**خلاصه‌ی فارسی:** مالک می‌خواهد سیستم هم لانگ و هم شورت اعلام کند و حدود ۳ تا ۴ هشدار در هفته بدهد. قاعده‌ی شورت را بدون پارامتر تازه، آینه‌ی قاعده‌ی قفل‌شده می‌سازم و قبل از اجرا معیارها را می‌نویسم: (۱) روی بازارهای غیرکریپتو، (۲) روی کریپتو (نمونه‌ی سوخته؛ توصیفی). اگر شورت معیارها را نیاورد، محصول هشدار شورت نمی‌دهد و فقط «لانگ / خروج به نقد» اعلام می‌کند. تعداد هشدار در هفته فقط شمرده می‌شود و ملاک سودآوری نیست.

## 1. Question

Does adding the mirror image of the frozen long rule (short when price breaks below the N-bar low, cover when price breaks above the N//2-bar high) add anything over the long-or-flat rule, in markets other than crypto and in the crypto sample? And how many direction-change alerts per week would the system give for baskets of 1, 2, 5, 10 and 26 coins?

Prior knowledge, stated before the run so that it cannot be adjusted afterwards: (a) Han, Kang and Ryu (time-series and cross-sectional momentum in crypto, 2013-2023, many look-back pairs tried by the authors, not out of sample) report that long-short time-series momentum underperforms long-only and that the short leg mostly loses money, with the long leg carrying the profit; (b) Hurst, Ooi and Pedersen (2017) and Lempérière et al. (2014) report profitable long-and-short trend following across diversified futures (Sharpe about 0.7-0.8 over decades) but do not show the short side separately, and Lempérière et al. report that very short trends (3 days) have decayed since 1990 and that the strategy has been about flat since 2011. The author therefore expects S3 (crypto) NOT to be met. The test is run anyway because the outcome decides what the product announces.

## 2. What is frozen

- Long leg: `research/trend-setup/trendsetup.py` (sha256 `e5e17e3de5d8ed36b33712726cfe81256a0ee7ec8ad66cf87f2885fd3fc2bc6f`) unchanged. Imported unchanged: `research/trend-setup/longhistory_report.py` (sha256 `445e8a2b509151576da0ffd472a8f5db31d5a01da5b273e5b1b99b9bfca90ddb`) for the fetchers and `describe`; `research/trend-setup/robustness_report.py` (sha256 `ba084e737cce087a0dcf02e17f4dc1f45e18c9490ea3cd585410fc7ed31166fa`) for the equal-weight portfolio.
- Short leg (no new parameter): five short states with the same windows N = 10, 20, 30, 55, 100. A short state turns on when the close is below the lowest low of the previous N bars and turns off when the close is above the highest high of the previous N//2 bars (the frozen `donchian_state` applied to negated, swapped prices; checked in the tests against the reciprocal-price mapping and against an independent plain loop). Short signal = mean of the five short states.
- Weights: long leg = long signal x vol scale (the frozen weight); short leg = minus short signal x the same vol scale; long-short = long leg + short leg. Decision at the close of bar j-1, held from the open of j to the open of j+1, cost 0.08% per side on the change of the (net) weight, active from 0-based bar index 260. Crypto: equal weight over active coins, at least 3 active (1 for the single-coin basket), exactly as the frozen paper track.
- Not modelled: funding on perpetual futures, borrow cost, margin or liquidation, interest on cash or on short proceeds, dividends. In crypto perpetuals the funding rate has been positive on average (longs pay shorts), which would favour shorts; its sign changes in time. Because it is not modelled, the short-side result is incomplete in an unknown direction.
- Tool: `research/trend-setup/shortside_report.py` (sha256 `c80409d8c59474b77b6d587bd7c68fd0cb443450da460cedabe37a9dd59800b1`), recorded in `research/trend-setup/CODE_SHA256_SHORTSIDE.txt`. The tool is run unchanged; if it must change, this pre-registration is superseded by a new version and the first run is reported as it was.

## 3. Data (fixed before the run)

- Non-crypto: the same 13 markets and the same Yahoo daily source, bar range, cleaning rules and exclusion rule (more than 1% rejected rows) as `PREREG_LONGHISTORY_v1.md`; plus Bitstamp BTC/USD 2011-09 to 2017-08-16, reported but not a criterion. The list is final; a source that cannot be fetched is reported as SOURCE_ERROR and not replaced. Disclosure: the long-only results on these markets were seen (RESULTS_LONGHISTORY_v1.md); no short-side number has been computed on them.
- Crypto: the fixed 26-coin Binance spot universe of the frozen paper track, daily bars from 2017-08-17 to the last complete bar before the run. Disclosure: this sample is burned for this rule family (long-only results seen); it is in-sample and descriptive only.
- Annualisation: observations per calendar year of each series for the non-crypto markets, 365 for crypto (as in the earlier reports).

## 4. Primary outputs

Per market and for the crypto baskets: long-only (the frozen rule), short leg alone, long-short, and hold; per-year return, Sharpe, max drawdown, years counted, share of counted bars with a long and with a short position. Crypto baskets are `all` (26) and `btc`, for the full period and from 2023-01-01. Alerts: for the first n coins of the fixed UNIVERSE order (n = 1, 2, 5, 10, 26), direction-change alerts per week = alerts of all members / (mean counted years of the members x 52), over the whole period and over the last 730 bars of each coin, for the long-short system and for the long-only system. A direction alert is enter long (flat to long), enter short (flat to short), flip (long to short or back) or exit (to flat); a change of size inside one direction is not an alert.

## 5. Criteria (applied mechanically by the tool)

Eligible market = at least 10 counted years (long-only counted years). A verdict needs at least 8 eligible non-crypto markets.
- **S1:** long-short Sharpe >= long-only Sharpe in at least 50% of eligible markets.
- **S2:** the short leg alone has a positive net total return in at least 50% of eligible markets.
- **S3 (crypto, `all` basket):** in the full period and from 2023, the short leg alone has a positive net total return and the long-short Sharpe >= the long-only Sharpe (both periods).
- Verdict: SUPPORTED if S1, S2 and S3 are all met; MIXED if at least one but not all; NOT_SUPPORTED if none; INSUFFICIENT_DATA if fewer than 8 eligible markets.

No other number is a criterion. No p-values or confidence intervals are claimed. The markets are correlated, so the share of markets is a weak structure check, not a significance test.

## 6. What the outcome means (decided now)

- SUPPORTED: SHORT alerts may be shown, labelled UNPROVEN and tracked on the forward paper record from T0; no claim that they will earn money.
- MIXED or NOT_SUPPORTED or INSUFFICIENT_DATA: the product does not announce SHORT. It announces LONG / HOLD / EXIT-TO-CASH (a bearish state means stay out), and a short signal can only come back through a new pre-registered test of a different mechanism. No subset of markets or coins is chosen afterwards to rescue the short side.
- Basket size for the alerts is a product choice made from alert counts only, with no performance information: the smallest n in (1, 2, 5, 10, 26) whose last-730-bar alerts per week, for the alert system that the verdict above allows, is at least 3.0; if none reaches 3.0, the largest basket is used and the shortfall is stated. A basket larger than about 10 coins is not realistic for manual trading; this is stated, not tuned.
- The alert rate is a consequence of the number of coins and of the daily timeframe. A faster timeframe on one coin would be a different rule family (new pre-registration, new multiplicity); nothing in this run supports it.

## 7. Change log

- 2026-11-22: first version, before any run.
