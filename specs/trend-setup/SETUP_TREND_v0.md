# SETUP_TREND_v0 — our own trading setup, version 0: multi-coin trend ensemble with volatility sizing (UNPROVEN)

**Status: FROZEN WITH THE CODE HASHES BELOW BEFORE T0 (2026-11-22 00:00 UTC).** This is a *setup specification and a forward-only record plan*, not a research result. Nothing here is self-certified: the tests are synthetic and by the same author, no independent review has taken place, and no historical run supports a claim of profit. The setup is **UNPROVEN**. It exists so that one concrete, rule-bound, low-turnover way of trading can be followed and recorded from a fixed start date, with risk limits decided in advance.

- `research/trend-setup/trendsetup.py` SHA-256: `e5e17e3de5d8ed36b33712726cfe81256a0ee7ec8ad66cf87f2885fd3fc2bc6f`
- `research/trend-setup/golden_vectors.json` SHA-256: `7278894ddc3eecdb8d71eb021561f1e4aa8ca88124d96651f24fe0f98014f43e`
(both also in `research/trend-setup/CODE_SHA256.txt`; CI refuses to run if either file differs). `tools/trend-ensemble/TrendEnsemble_v0.pine` is a display aid for TradingView, **not hash-frozen**: compile fixes are allowed and logged, any change of logic is a new version.

## 0. Summary in Persian (for the owner)

- این ستاپ «مال خودمان» است: **روند چنددارایی با اندازه‌ی نوسان‌محور**، فقط خرید یا نقد (بدون شورت، بدون اهرم)، روی کندل روزانه. برای هر ارز پنج کانال Donchian (۱۰، ۲۰، ۳۰، ۵۵، ۱۰۰ روزه) میانگین گرفته می‌شود و سیگنال ۰ تا ۱ می‌دهد؛ وزن = سیگنال × min(1، ۰٫۵ ÷ نوسان سالانه‌ی ۳۰ روزه). هر روز ساعت ۰۳:۳۰ تهران (۰۰:۰۰ UTC) کندل بسته‌شده بررسی می‌شود؛ فقط وقتی سیگنال عوض شد معامله می‌کنی. معاملات کم است (گردش روزانه حدود ۱٪).
- **ادعای سود ندارد.** در آزمون ما (۱۵ ارز تازه، ۲۰۲۳ تا ۲۰۲۶) همین قاعده Sharpe حدود ۰٫۸۸ با بازه‌ی خیلی پهن (از ۰٫۵- تا ۲٫۰+) داشت و از «نگه‌داشتن» جدا نشد. افت سرمایه‌ی مشاهده‌شده ۲۴٪ بود و در آینده می‌تواند بدتر شود. این **۲–۳٪ در روز نیست**؛ هیچ ستاپی در شواهد ما چنین چیزی نشان نداد.
- از ۲۰۲۶-۱۱-۲۲ (T0) یک «مسیر کاغذی» رو‌به‌جلو خودکار از داده‌ی عمومی قابل بازمحاسبه است. تصمیم آماری درباره‌ی اثر کوچک سال‌ها طول می‌کشد (بخش ۷)؛ هدف نسخه‌ی ۰ تمرین منضبط با ریسک کوچک و پایش فاجعه است، نه اثبات.
- سقف‌های ریسک از پیش ثابت‌اند (بخش ۶): فقط پولی که می‌توانی کامل از دست بدهی، بدون اهرم، بدون دخالت سلیقه‌ای، توقف و بازبینی اگر افت از قله ≥ ۳۵٪ یا هزینه‌ی واقعی > ۰٫۳۰٪ رفت‌وبرگشت.

## 1. What this is and is not

Is: a fixed rule list that turns public daily candles into a long-or-flat weight per coin; a daily table (tool) and a chart panel (Pine); a deterministic paper track from T0; fixed risk limits and stop criteria.
Is not: a proven edge; a promise of any return; a signal for a single coin in isolation (the evidence below is for a diversified portfolio); advice (this document is not financial advice and its author is not a financial advisor); an intraday scalping or day-trading system (the little evidence we read on retail day trading is strongly negative: in the Brazilian futures study summarised by Quantpedia, 97% of persistent day traders lost money; secondary source, different market).

## 2. Design record: where each choice comes from and how well it is supported

| component | choice | support |
|---|---|---|
| direction | trend following (long while the trend is up, otherwise cash) | Same sign in every test we ran: Setup Lab v1 S1/S4 slightly positive but inconclusive; Search Lab v1: all 4 confirmed candidates had positive point estimates on unseen coins but none passed (intervals include zero). Abstract-level literature (Zarattini–Pagani–Barbon, Donchian ensembles; Fieberg et al. trend factor) points the same way; unreviewed or abstract-only. **Direction consistent, not statistically confirmed.** |
| lookbacks | average of five Donchian states, N = 10, 20, 30, 55, 100, exit channel N//2 | Avoids choosing one parameter. This exact rule was the literature-prior reference candidate in Search Lab v1 (`ENSEMBLE:DONCH5LF`, not tuned on data): Sharpe +0.88, 98.75% interval [−0.52, +2.01], alpha vs holding +0.10 (lower bound −0.05), max drawdown 0.24, mean daily turnover 0.011, positive at 0.15% per side, positive on the old coins 2023+. INCONCLUSIVE. Fast rules selected by discovery did not do better on unseen data. |
| sizing | weight = signal × min(1, 0.50 / annualised 30-day vol); no leverage above 1 per coin | Part of every tested portfolio. Typical crypto vol of 60–100% makes the weights 0.5–0.8, so the portfolio holds cash by construction. |
| universe | 26 liquid Binance spot pairs (fixed list in the code), equal weight over active coins | Tested on 15 + 10 coins. A portfolio of fewer coins is **untested** and swings more. |
| long-or-flat | no shorting | Chosen for manual trading (no funding or borrow on shorts to model). Long-short variants were in the search but are not used. |
| daily bar, act at the next open | decide at the daily close (00:00 UTC = 03:30 Tehran), fill from the next open | Tested as open-to-open. A manual fill hours later is **not** modelled; the journal measures the difference. |
| risk overlay | section 6 | **Our judgment, untested.** |

## 3. The rule (frozen; the code is the exact definition)

Bars are daily UTC candles; every quantity at the close of bar i uses bars ≤ i only (checked by a prefix-truncation test).

1. For each N in {10, 20, 30, 55, 100} and each coin: state_N = 1 (long) after the first close above max(high of the previous N bars); the state returns to 0 when the close falls below min(low of the previous N//2 bars). State 0 otherwise. (N//2 = 5, 10, 15, 27, 50.)
2. signal s = mean of the five states, so s ∈ {0, 0.2, 0.4, 0.6, 0.8, 1}.
3. vol30 = population standard deviation of the last 30 simple daily close-to-close returns × √365. scale = min(1, 0.50 / vol30); scale = 0 if vol30 is missing or zero.
4. A coin is *active* only from its 260th bar on (warm-up) and while its last closed bar is present. (Clarified 2026-11-21, no code change: the code and the Pine file use 0-based bar index ≥ 260, i.e. the first 260 bars are warm-up and the 261st bar is the first active one.) Weight inside the coin's own slice = s × scale. Portfolio weight of the coin = s × scale / (number of active coins). The rest is cash.
5. Fills at the open of bar i+1. Cost assumption: 0.08% of traded notional per side. Funding and spread beyond this are not modelled.

## 4. Universe, T0, paper track

- Universe (26): BTCUSDT, ETHUSDT, BNBUSDT, XRPUSDT, ADAUSDT, LTCUSDT, TRXUSDT, LINKUSDT, XLMUSDT, ETCUSDT, NEOUSDT, SOLUSDT, DOGEUSDT, AVAXUSDT, DOTUSDT, ATOMUSDT, UNIUSDT, AAVEUSDT, FILUSDT, ALGOUSDT, VETUSDT, NEARUSDT, XTZUSDT, ZECUSDT, DASHUSDT, HBARUSDT. A coin whose fetch fails or has more than 5 missing days is excluded and listed; fewer than 8 usable coins = infrastructure failure, not a result. A coin without its last closed bar is treated as flat. A delisting loss is not modelled.
- T0 = 2026-11-22 00:00 UTC. The first counted bar is the bar opening at T0 (decided at the close of 2026-11-21). Earlier days are never part of the record, because all earlier history is burned (it was seen by the authors, and the rule was designed after seeing it).
- Paper track: `python -I -B research/trend-setup/trendsetup.py paper` recomputes the whole track from public Binance daily candles at any time, deterministically; it starts from cash (entry costs of the first day are included) and prints the SHA-256 of each coin's data. Anyone can re-run and compare.
- Daily table: `python -I -B research/trend-setup/trendsetup.py table --equity 10000` prints the signal, vol, scale and suggested weight per coin for the last closed bar. The GitHub Actions workflow `run-trend-setup.yml` runs it from a push to `research/trend-setup/RUN_REQUEST.txt` (a snapshot); a scheduled version is a separate owner decision.
- Pine panel: `tools/trend-ensemble/TrendEnsemble_v0.pine` (daily chart). Uses TradingView's loaded history, so a young or short chart may differ from the tool in the first months; the tool is the authority.

## 5. Daily routine for the manual trader (about 5 minutes)

1. At or after 03:30 Tehran, read the table (or the Pine panel) for the **last closed** bar.
2. Trade only coins whose signal changed (CHANGED). Compute the target from the table: slice = journal capital / M (M = number of coins you actually trade), target = slice × (weight inside own slice). If the change is smaller than the exchange minimum, skip it and log that.
3. Use limit orders near the open price when possible. Record, per fill: reference price (open of the new bar), actual fill price, fee. Slippage = actual − reference. This measures the one cost the research could not.
4. Never add, remove or resize on a feeling. A deviation from the table is allowed only if logged with its reason; deviations are excluded from any later claim about the rule.

## 6. Risk overlay (frozen defaults; our judgment, untested)

- R1 Journal capital = only money you can lose entirely. The owner chooses the amount before T0 and does not increase it during the first 12 months.
- R2 No leverage (total notional ≤ journal capital), no shorting, no averaging down outside the rule.
- R3 If M < 8 coins are traded, the portfolio is less diversified than the evidence: state M in the journal, and expect larger swings.
- R4 Pause rule: if the paper track (or the live journal) falls ≥ 35% from its peak, stop adding exposure and review before continuing. (Observed drawdown of this rule on the unseen coins 2023–2026 was 24%; other tested candidates 31–43%; a longer or harsher period can be worse. This is a review trigger, not a promise of a stop-loss.)
- R5 Cost gate: after 90 days of live journal, if the measured round-trip cost (fees + slippage against the reference open) exceeds 0.30% on average, stop the live journal; the paper track continues.
- R6 Counterparty and exchange risk (KCEX or any venue), funding on perpetuals, liquidation, and taxes/legal limits in the owner's country are **not modelled** and are the owner's responsibility.

## 7. Forward evaluation plan (fixed now)

- Nothing is said about performance before 90 counted days. Reviews at 12, 24 and 36 months are descriptive (return, drawdown, Sharpe, benchmark comparison).
- A formal claim "this rule has a positive edge" needs both: one-sided 95% lower bound of the Sharpe > 0 and one-sided 95% lower bound of the alpha against the always-long benchmark (same coins, same scaling) > 0, with a 30-day block bootstrap, 5,000 resamples. Rough duration, assuming independent daily returns: years needed ≈ (1.645 / true Sharpe)², i.e. about 3 years if the true Sharpe is 0.9, 11 years if 0.5, 30 years if 0.3. With autocorrelation and fat tails it is longer. **Expect "inconclusive" for years.** The practical value of v0 is disciplined, low-turnover, small-risk practice with an honest record and an early warning if something is badly wrong, not a quick proof.
- A paper track far worse than holding the same coins for 24 months closes this setup in this form; changes are then a new version with a new preregistration.

## 8. Known limitations (stated before T0)

- No confirmation: the underlying evidence is direction-consistent but statistically inconclusive; with strongly correlated coins and about 3.9 years the confirmation test had almost no power (Search Lab v1 prereg §11).
- The setup was designed after reading Setup Lab v1 and Search Lab v1 results; the 2017–2026 history of all 25 non-BTC coins is burned and BTC was already burned.
- Survivorship: the universe is today's liquid coins; delisted coins are absent from the research.
- The tested period (2023–2026) contained a strong rally; trend rules often look good in rallies and bad in choppy markets.
- Manual execution lag, spread, funding, KCEX-specific prices, taxes and exchange risk are not modelled.
- Daily bars and Binance spot prices as a proxy for whatever venue is traded.
- The Pine file has not been compiled by its author.

## 9. Change log

- v0 (2026-11-21): first version; frozen at the hashes above before T0.
- 2026-11-21 (documentation only; trendsetup.py and golden_vectors.json unchanged, hashes as above): a read-only review by a separate Claude instance (same model, so not an independent review; cut short by a usage limit) re-implemented the rule from this text and compared it with the code on synthetic panels. Findings written down here instead of changing frozen code:
  1. Primitives matched: Donchian states (0 mismatches in 3000 series x 5 windows, including bars exactly on the entry/exit boundaries), vol30, weights, and the golden vectors agreed to about 1e-12.
  2. Warm-up wording: see item 4 above (0-based index 260).
  3. Cost convention: cost is charged on each coin's own-slice weight change, divided by the number of active coins. When the number of active coins changes (a coin finishes its warm-up or drops out), the other coins' weights shrink and that rebalancing turnover is not charged. On synthetic panels the omitted cost was about 0.02 to 0.04 percentage points of cumulative equity; with the fixed 26-coin universe, all active from T0, it is zero unless a coin is excluded. The same convention was used in the Search Lab.
  4. Missing days (allowed up to 5 per coin): a missing day is treated as flat for that coin on that day, which is not the only reasonable policy. On synthetic panels with missing days the equity differed from an alternative causal policy by up to about 2% over 900 days. All 26 coins have 0 missing days in the real history used so far, so this has no effect on any reported number.
  5. The review was not finished (usage limit): tests that might be tautological and the reporting tools were not fully audited.
