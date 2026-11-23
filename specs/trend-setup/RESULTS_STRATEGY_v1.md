# Results: strategy tester (Alert B replay, trend trades, today table) — run 3, GitHub Actions run 45093397248

Run on GitHub Actions after the request commit 18d5838 (tool sha256 `7b2cf1b1a75d820e1e5effbad0ade06b9a8758d789d5f693e1cda29d1087b7a8`, listed in `CODE_SHA256_STRATEGY.txt`; frozen trend code `e5e17e3d...` unchanged). Data end fixed with `--now-ms 1795395600000 --asof-ms 1795392000000` (2026-11-23 01:00 / 00:00 UTC). Data hashes: BTCUSDT 1h `633a20b4efe40168` (81109 bars, 128 missing), BTCUSDT 1d `ceaffead16b48874`. Runs 1 and 2 (commits 4b378b4, f93e587) saw the same data hashes; run 1 numbers were identical to run 3 (every Alert B statistic and every trend basket statistic compared by the author). Run 2 printed one very long log line that the log service dropped, so only run 3 carries the full output; it is stored in `STRATEGY_RESULT_run3.json.gz` (gzip of the tool's JSON).

**Same author, synthetic tests only (29), no independent review. Both rules were seen on parts of this history, so a good past is not evidence; nothing here is evidence of future returns. Costs: 0.16% of the reference price (Alert B), 0.08% per side (trend); slippage, funding, alert delay and KCEX prices are not modelled.**

**خلاصه‌ی فارسی:** تستر قانون Alert B ربات را تا ۹ رقم اعشار بازسازی کرد (هشدار لاگ ۲۰ نوامبر). هشدار تلگرامیِ ۱۹ نوامبر (شورت) به هدف رسید (+1.96R)؛ هشدار ۲۰ نوامبر هنوز باز است. ردیف ۱۹ نوامبر در لاگ عمومی نیست و به همین دلیل قانون ۲۴ ساعت جلوی هشدار ۲۰ نوامبر را نگرفت. روی ۹ سال: ۴۵۵ هشدار، ۰٫۹۴ در هفته، میانگین +0.13R، ولی از ۲۰۲۳ تقریباً صفر. قاعدهٔ روند: افت سرمایه کمتر از نگه‌داشتن، رشد سالانه کمتر یا برابر؛ امروز همهٔ ۷ ارز نقد است.

## A. Alert B (BREAK20D) replay on BTCUSDT spot

Rule: ALERT_RULES_v1 (20 completed daily bars, level break on the 1h close, R = ATR14 daily, stop 1R / target 2R / 168 h, stop first on a shared bar, 24 h cooldown per side counted from the last sent alert, cost 0.16% of ref). 455 alerts in 484 weeks (0.94/week; LONG 0.61, SHORT 0.33); 836 raw breaks before the cooldown.

| period | side | n | profitable | mean R net | sum R | profit factor | equity at 0.5% risk | max DD |
|---|---|---|---|---|---|---|---|---|
| all | LONG | 297 | 43% | +0.142 | +42.1 | +1.25 | 1.23 | 8% |
| all | SHORT | 158 | 41% | +0.118 | +18.7 | +1.21 | 1.09 | 8% |
| all | both | 455 | 43% | +0.134 | +60.8 | +1.23 | 1.34 | 10% |
| before_live | LONG | 297 | 43% | +0.142 | +42.1 | +1.25 | 1.23 | 8% |
| before_live | SHORT | 156 | 41% | +0.114 | +17.8 | +1.20 | 1.09 | 8% |
| before_live | both | 453 | 43% | +0.132 | +59.9 | +1.23 | 1.33 | 10% |
| since_live | SHORT | 2 | 50% | +0.465 | +0.9 | +1.90 | 1.00 | 1% |
| since_live | both | 2 | 50% | +0.465 | +0.9 | +1.90 | 1.00 | 1% |
| from_2023 | LONG | 125 | 41% | -0.005 | -0.6 | +0.99 | 0.99 | 8% |
| from_2023 | SHORT | 70 | 37% | +0.075 | +5.2 | +1.12 | 1.02 | 8% |
| from_2023 | both | 195 | 39% | +0.024 | +4.6 | +1.04 | 1.02 | 10% |
| last_365d | LONG | 20 | 25% | -0.466 | -9.3 | +0.35 | 0.95 | 5% |
| last_365d | SHORT | 24 | 54% | +0.575 | +13.8 | +2.20 | 1.07 | 3% |
| last_365d | both | 44 | 41% | +0.102 | +4.5 | +1.17 | 1.02 | 4% |

Baseline (same exits and costs, entry every 24 h unrelated to any signal, sides alternating): n 3357, mean R net -0.011, profitable 41%. Equity is an approximation (risk 0.5% per trade, trades applied in exit order, overlap not capped).

### By year (mean R net, n)

| year | LONG | SHORT |
|---|---|---|
| 2017 | +0.83 (26) | -1.01 (1) |
| 2018 | +0.04 (13) | +0.05 (33) |
| 2019 | +0.51 (26) | +0.28 (12) |
| 2020 | +0.23 (50) | +1.17 (5) |
| 2021 | +0.14 (40) | +0.13 (11) |
| 2022 | -0.57 (17) | +0.08 (26) |
| 2023 | +0.16 (30) | -0.36 (11) |
| 2024 | +0.08 (50) | +0.09 (15) |
| 2025 | -0.04 (26) | -0.30 (20) |
| 2026 | -0.44 (19) | +0.58 (24) |

### Reproduction of the live bot

- **alert-log row (sent 2026-11-20T18:30:59Z)** (alerts.csv on the alert-log branch): reproduced with cooldown = False; found without cooldown = True; bar 2026-11-20 15:00 UTC, replay ref 59475.47, level 61428.26, ATR 2642.3393215804913, stop 62117.80932158049, target 54190.79135683902; outcome PENDING (168 h window not complete; neither stop nor target touched yet); suppressed in the replay by the alert of 2026-11-19 21:00 UTC (18 h earlier)
- **Telegram screenshot (not in the public log)** (owner's screenshot, numbers read by eye (1 decimal)): reproduced with cooldown = True; found without cooldown = True; bar 2026-11-19 21:00 UTC, replay ref 61542.01, level 62006.0, ATR 2641.55465400976, stop 64183.56465400976, target 56258.90069198048; outcome TARGET at 2026-11-21 04:00 UTC (31.0 h), r_net +1.963

The logged live alert (alert-log branch, row sent 2026-11-20T18:30:59Z) equals the replay to about 1e-10 in R, stop and target (the bot starts ATR14 from 400 daily bars, the replay from the first bar). The 2026-11-19 21:00 alert (owner's Telegram screenshot, numbers read by eye) matches the replay within 0.1 but is **not in the public alert log**; with it logged, the 24 h cooldown would have suppressed the 2026-11-20 15:00 alert and the bot would have sent the 2026-11-21 03:00 SHORT instead (stopped after 10 h, -1.03R). Delivery delay seen in the log row: 2.5 h after the 1h candle closed.

## B. Trend rule (frozen, trendsetup.py) — equal-weight portfolio, cost 0.08% per side, from 2018

| basket | period | CAGR | Sharpe | max DD | hold CAGR | hold max DD |
|---|---|---|---|---|---|---|
| BTC | full | +0.255 | 0.92 | 44% | +0.238 | 77% |
| BTC | from 2023 | +0.197 | 0.83 | 28% | +0.394 | 53% |
| 7 coins | full | +0.240 | 1.05 | 35% | +0.290 | 72% |
| 7 coins | from 2023 | +0.183 | 0.90 | 23% | +0.262 | 60% |
| all 26 | full | +0.205 | 1.00 | 29% | +0.194 | 82% |
| all 26 | from 2023 | +0.155 | 0.83 | 23% | +0.143 | 69% |

7-coin yearly rule vs hold: 2018 -13% / -60%, 2019 +25% / +19%, 2020 +85% / +243%, 2021 +93% / +382%, 2022 -20% / -57%, 2023 +21% / +90%, 2024 +70% / +125%, 2025 +2% / -8%, 2026 -9% / -37%.

Trade episodes (a run of non-zero weight; net return on the coin's own slice): 
- BTC: n 40, profitable 28%, mean +8.4%, avg win +39%, avg loss -3.0%, profit factor 4.83, worst -14.0%, mean days 56
- 7 coins: n 274, profitable 23%, mean +8.1%, avg win +47%, avg loss -3.1%, profit factor 4.37, worst -14.0%, mean days 52
- all 26: n 940, profitable 23%, mean +5.2%, avg win +34%, avg loss -3.2%, profit factor 3.13, worst -17.4%, mean days 45

## C. Today (last closed daily bar 2026-11-22 UTC), 7 coins

All 7 coins have signal 0.0 (states 00000): the rule holds cash. Signal changes in the last 60 days are in the JSON (`C.changes_last_60d`): BTC, ETH and LTC went to zero at the close of 2026-11-08.

## What this does and does not show

- The replay is faithful to the bot's rule (one logged alert reproduced to ~1e-10), so the trade list and statistics describe what the rule would have done on this data.
- Alert B: positive mean R over 9 years, but about all of it before 2022; since 2023 the mean is within noise of zero (SE about 0.1R, trades not independent). Frequency is 0.94/week on BTC, not 3-4.
- Trend rule: much smaller drawdown than holding, lower or equal CAGR; 2025 +2%, 2026 -9% (7 coins).
- Neither result is evidence of future returns; the forward record (alerts after 2026-11-15, paper track from T0 2026-11-22) is the only confirmation.
