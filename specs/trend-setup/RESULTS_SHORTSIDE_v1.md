# Results: mirrored short side and alerts per week (run 44994463505)

Run on GitHub Actions, commit 3c55b25 (request) after the pre-registration commit 696d076 (`PREREG_SHORTSIDE_v1.md`). Tool sha256 `c80409d8c59474b77b6d587bd7c68fd0cb443450da460cedabe37a9dd59800b1`, frozen rule `e5e17e3d...`, unchanged. The tables below are the tool's own output, copied without edits. Same author; synthetic tests only; funding, borrow and margin are not modelled; crypto is in-sample and burned for this rule family. Nothing here is evidence of future returns.

**خلاصه‌ی فارسی:** شورتِ آینه‌ای (بدون پارامتر تازه) در هر ۱۰ بازار غیرکریپتو، در کریپتو و در BTC سال‌های ۲۰۱۱–۲۰۱۷ ضرر کرد. حکم پیش‌ثبت‌شده: NOT_SUPPORTED. پس محصول «شورت» اعلام نمی‌کند، فقط «لانگ / کم‌کردن / خروج به نقد».

# Trend Setup v0: mirrored short side (pre-registered, descriptive)

**Same author; synthetic tests only; funding, borrow and margin not modelled; the crypto sample is in-sample and burned for this rule family. Nothing is evidence of future returns.**

## Crypto universe (26 coins, equal weight over active coins)

| basket | period | long-only per yr | short leg per yr | long-short per yr | long-only Sharpe | short leg Sharpe | long-short Sharpe | long-only max DD | long-short max DD | hold per yr |
|---|---|---|---|---|---|---|---|---|---|---|
| all (26) | full | +20.5% | -5.0% | +15.9% | 1.00 | -0.11 | 0.68 | -29% | -34% | +19.2% |
| all (26) | from2023 | +15.5% | -9.8% | +5.4% | 0.83 | -0.39 | 0.34 | -23% | -32% | +14.0% |
| btc (1) | full | +25.5% | -8.5% | +15.3% | 0.92 | -0.21 | 0.56 | -44% | -55% | +23.5% |
| btc (1) | from2023 | +19.7% | -13.3% | +4.1% | 0.83 | -0.59 | 0.28 | -28% | -43% | +38.6% |

## Other markets (each on its own bars)

| market | years | long-only per yr | short leg per yr | long-short per yr | long-only Sharpe | short leg Sharpe | long-short Sharpe | long-short max DD | share of days short |
|---|---|---|---|---|---|---|---|---|---|
| S&P 500 | 55.8 | +2.4% | -4.5% | -2.1% | 0.35 | -0.44 | -0.12 | -80% | 50% |
| Nasdaq Composite | 54.8 | +8.3% | -2.5% | +5.7% | 0.87 | -0.16 | 0.46 | -53% | 50% |
| Dow Jones | 33.8 | +1.7% | -4.9% | -3.2% | 0.26 | -0.47 | -0.23 | -78% | 50% |
| Nikkei 225 | 55.8 | +3.4% | -3.4% | +0.1% | 0.41 | -0.24 | 0.07 | -78% | 56% |
| FTSE 100 | 41.8 | +0.7% | -4.8% | -4.0% | 0.14 | -0.44 | -0.29 | -90% | 57% |
| DAX | 37.8 | +3.0% | -4.1% | -1.1% | 0.35 | -0.27 | 0.00 | -74% | 53% |
| Hang Seng | 38.8 | +2.6% | -4.4% | -1.8% | 0.28 | -0.27 | -0.02 | -71% | 59% |
| CAC 40 | 35.7 | -0.4% | -5.9% | -6.2% | 0.01 | -0.40 | -0.34 | -90% | 57% |
| Gold futures | EXCLUDED_BAD_DATA  | | | | | | | | |
| Silver futures | EXCLUDED_BAD_DATA  | | | | | | | | |
| Crude oil futures | 25.2 | +2.0% | -3.3% | -1.1% | 0.20 | -0.09 | 0.08 | -62% | 57% |
| Copper futures | EXCLUDED_BAD_DATA  | | | | | | | | |
| 10y Treasury note futures | 25.1 | -0.7% | -0.7% | -1.3% | -0.19 | -0.19 | -0.28 | -36% | 66% |
| BTC/USD Bitstamp to 2017-08-16 | 5.2 | +151.3% | -5.8% | +138.6% | 2.51 | -0.14 | 2.17 | -44% | 43% |

## Alerts per week (direction changes: enter long, enter short, flip, exit; size changes are not alerts)

| first n coins | full: long-short | full: long-only | last 2 yrs: long-short | last 2 yrs: long-only | enter long | enter short | flip | exit |
|---|---|---|---|---|---|---|---|---|
| 1 | 0.24 | 0.18 | 0.28 | 0.20 | 0.04 | 0.02 | 0.11 | 0.06 |
| 2 | 0.53 | 0.35 | 0.57 | 0.38 | 0.10 | 0.06 | 0.21 | 0.16 |
| 5 | 1.32 | 0.93 | 1.46 | 1.05 | 0.22 | 0.18 | 0.53 | 0.40 |
| 10 | 2.58 | 1.86 | 2.88 | 2.08 | 0.42 | 0.35 | 1.04 | 0.77 |
| 26 | 6.79 | 5.15 | 7.09 | 5.40 | 1.02 | 1.01 | 2.72 | 2.03 |

## Pre-registered criteria
- eligible markets (>= 10 counted years): 10 of 13 (a verdict needs at least 8)
- S1 long-short Sharpe >= long-only Sharpe in >= 50% of eligible markets: 0% -> NOT MET
- S2 short leg alone has a positive net total return in >= 50% of eligible markets: 0% -> NOT MET
- S3 crypto universe, full period and from 2023: short leg alone positive and long-short Sharpe >= long-only Sharpe -> NOT MET
- verdict: NOT_SUPPORTED

## Author's reading (not a result of the tool)

- **Verdict NOT_SUPPORTED, all three criteria failed, not close.** The short leg alone lost money in 10 of 10 eligible non-crypto markets (S2 0%), long-short Sharpe was below long-only Sharpe in 0 of 10 (S1 0%), and in crypto the short leg lost in the full period (-5.0% a year, 26 coins; -8.5% BTC) and from 2023 (-9.8% and -13.3%) while long-short Sharpe was below long-only (0.68 vs 1.00 full, 0.34 vs 0.83 from 2023). BTC/USD 2011-2017, a bull run, also lost on the short leg (-5.8% a year; reported, not a criterion).
- This matches the prior stated in the pre-registration (Han, Kang and Ryu: short-only mostly loses in crypto) and says that this particular mirror, with these five windows, daily bars and 0.08% per side, does not earn money as a short signal in these samples. It does not say that no short method can work, and funding on perpetuals (positive on average in crypto, so it would favour shorts, but it changes sign) is not modelled; the size of the loss makes it unlikely that funding alone would reverse the verdict, but that is a judgement, not a measurement.
- **Consequence fixed in advance (section 6 of the pre-registration):** the product does not announce SHORT. It announces LONG, size changes and EXIT-TO-CASH; a bearish state means stay out. A short signal can only return through a new pre-registered test of a different mechanism. No market or coin subset is picked to rescue it.
- **Alerts per week, long-only system, last 730 bars (direction changes only: enter or exit):** 1 coin 0.20, 2 coins 0.38, 5 coins 1.05, 10 coins 2.08, 26 coins 5.40. By the basket rule written in advance (smallest n with at least 3.0 direction alerts per week) the answer is 26 coins, which is not realistic by hand (the pre-registration says so); this is reported, not tuned.
- Counting every position change as a trade, including adding to and reducing a position (frequency report, run 44966186808, whole period, signal changes per week): 1 coin 0.61, 2 coins 1.18, 5 coins 2.87, 10 coins 5.71, 26 coins 14.65. If the owner's "3-4 trades a week" includes size changes, about 6 to 8 coins of the fixed list would give that (interpolation between 5 and 10 coins, not measured). Whether size changes count as trades is a product definition, not a performance choice. In the same report, acting only on signal-change bars (V1) was in-sample not worse than the frozen daily re-sizing (top-5 coins 30.8% vs 26.6% a year, Sharpe 1.18 vs 1.12; top-10 coins 23.8% vs 20.0%, Sharpe 0.99 vs 0.92; from 2023: top-5 22.1% vs 18.4%, top-10 18.1% vs 14.2%). That is a descriptive in-sample comparison on burned data.
- Limits: markets are correlated (10 eligible markets are not 10 independent tests); gold, silver and copper futures were excluded for bad data by the earlier pre-registered rule; no independent review of this tool exists; the only out-of-sample evidence the lab will have is the forward paper track from T0 (2026-11-22 00:00 UTC).
