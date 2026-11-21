# Pre-registration: long-history structure check of Trend Setup v0 (v1)

Written 2026-11-21 15:35 UTC, before the tool has ever been run on real data. Status: pre-registered, descriptive. Not evidence of future returns.

**خلاصه‌ی فارسی:** همان قاعده‌ی قفل‌شده‌ی ستاپ روند، بدون هیچ تغییر، روی تاریخچه‌ی بلندمدت بازارهایی که این آزمایشگاه هرگز برای این قاعده ندیده (۱۳ بازار غیرکریپتو از ۱۹۷۰، و BTC روی Bitstamp از ۲۰۱۱ تا ۱۶ اوت ۲۰۱۷) اجرا می‌شود. معیارها همین‌جا و قبل از اجرا ثابت شده‌اند. قبولی یعنی «قاعده در بازارهای دیگر هم مثل یک قاعده‌ی روند رفتار می‌کند»، نه «در کریپتو در آینده سود می‌دهد».

## 1. Question

Is the behaviour seen in crypto (similar return to holding, much smaller drawdowns) a property of this trend rule that also shows up in other markets and eras, or something particular to the 2017-2026 crypto history on which the rule family was designed and tested? This is a check of the structure of the rule. It does not test the crypto forecast: the only real out-of-sample evidence for that is the forward paper track from T0 (2026-11-22 00:00 UTC).

## 2. What is frozen

- Rule and code: `research/trend-setup/trendsetup.py` (sha256 `e5e17e3de5d8ed36b33712726cfe81256a0ee7ec8ad66cf87f2885fd3fc2bc6f`), unchanged: five Donchian states N = 10, 20, 30, 55, 100, exit on the previous N//2-bar low, signal = mean of states, vol30 scaling with cap 0.50 (annualisation sqrt(365) as in the frozen code), active from 0-based bar index 260, long-or-flat, decision at the close of bar j-1, held from the open of j to the open of j+1, cost 0.08% per side. No parameter is adapted to any market.
- Tool: `research/trend-setup/longhistory_report.py` (sha256 `2a0adb7b1b8f81b52061719b7d1223dfe7a79502b8e0214429f076ad53650a86`), recorded in `research/trend-setup/CODE_SHA256_LONGHISTORY.txt`. The tool is run unchanged; if it must change, this pre-registration is superseded by a new version and the first run is reported as it was.

## 3. Data (fixed before the run)

- Yahoo Finance chart API daily OHLC, `range=max`, bars from 1970-01-01 to 2026-11-19, per market, each market on its own bars (no cross-market alignment in the primary results):
  - equity indices (8): ^GSPC, ^IXIC, ^DJI, ^N225, ^FTSE, ^GDAXI, ^HSI, ^FCHI
  - continuous futures (5): GC=F gold, SI=F silver, CL=F crude oil, HG=F copper, ZN=F 10-year Treasury note
- Bitstamp BTC/USD daily OHLC from 2011-09 to 2017-08-16 (before the Binance window of the Search Lab, which starts 2017-08-17).
- The list is final. Nothing is added or dropped after seeing a result. FX pairs were left out on purpose (a long-only rule on a quoted pair has an arbitrary orientation). A source that cannot be fetched is reported as SOURCE_ERROR and is not replaced.
- Rows with missing or non-positive prices, inconsistent OHLC, or duplicate dates are rejected and counted. A market with more than 1% rejected rows is EXCLUDED and listed. Today's partial bar is excluded (last bar 2026-11-19).
- Annualisation: observations per calendar year of each series (about 252 for weekday markets), not 365.

## 4. Primary outputs

Per market: first counted bar (the day after the 261st bar), years counted, rule and hold per-year return, Sharpe and max drawdown, average exposure. Hold = always long, open-to-open, no cost, on the same bars the rule counts. Secondary: equal-weight average over the non-crypto markets available on each date.

## 5. Criteria (applied mechanically by the tool)

Eligible market = at least 10 counted years.
- **P1 (drawdown):** rule max drawdown <= 0.75 x hold max drawdown in at least 70% of eligible markets.
- **P2 (risk-adjusted):** rule Sharpe >= hold Sharpe in at least 50% of eligible markets.
- Markets verdict: CONSISTENT if P1 and P2 are met; PARTIAL if only P1; NOT_CONSISTENT otherwise.
- **P3 (BTC 2011-2017):** rule max drawdown <= 0.75 x hold max drawdown. Reported separately; one asset in one regime, so it is a sanity check, not a test.

No other number is a criterion. No p-values or confidence intervals are claimed.

## 6. What the outcome means

- CONSISTENT: the rule behaves like a trend rule across markets and eras (drawdown reduction with Sharpe not worse than holding). That makes it less likely that the crypto result is purely a fluke of the crypto sample. It says nothing about the size of any future return and is not a reason to raise risk limits.
- PARTIAL or NOT_CONSISTENT: the crypto result may depend on crypto-specific history; the rule stays UNPROVEN and the forward paper track is the only evidence that counts. The result is reported as it is.
- BTC 2011-2017 is not virgin for the project (the lab looked at the whole BTC history for other hypotheses) and the later part of that period is a famous bull run: treat it as weak evidence.

## 7. Known limits

- Same author as the rule and the tool; tests are synthetic; no independent review.
- Trend-following on these markets is widely documented, and N = 20 and 55 are classic (turtle-style) windows; the choice of the rule was not blind to that literature, so a pass here is not a surprise and a fail would be informative.
- Yahoo continuous futures are spliced contracts: roll gaps add noise. Index bars before the 1980s may have degenerate highs and lows (flat-bar share is reported).
- The rule's vol cap (0.50) almost never binds outside crypto, so on these markets the rule is mostly a pure Donchian-ensemble timing signal.
- Costs 0.08% per side are applied everywhere: conservative for index futures, optimistic for some early-period spreads.
- Different markets share global risk cycles, so the number of independent observations is smaller than the number of markets.
- KCEX, funding, taxes and manual execution are not modelled.

## 8. Change log

- v1 (2026-11-21 15:35 UTC): first version, before any real-data run.
