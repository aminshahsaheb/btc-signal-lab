# RESULTS_ZEROPIP_v2 — result record of the single scoring run

**Status: RESULT PUBLISHED. Overall: NO_CANDIDATE. All six evaluated rules FAIL.** Nothing here is self-certified: the tests are synthetic and by the same author, and no independent review has taken place. All BTC history is burned (RESEARCH_RULES rule 2); this is hypothesis generation, not evidence of future returns.

- Preregistration: `specs/zero-pip-lab/PREREG_ZEROPIP_v2.md` (frozen with the code hash below before any real-data result; it references the unchanged `PREREG_ZEROPIP_v1.md`).
- Code: `research/zero-pip-lab/zeropip_v2.py`, SHA-256 `09b23b4df09f144c3c78c53afe122ed4c1ef1c0348ded3ac522b0be75b1288dd`.
- Run: GitHub Actions workflow "Zero-Pip Lab v2 scoring run (real public data)", run id `45801961153`, commit `2d47cb5`, single run (no re-run). Hash, prereg and 38 synthetic tests were re-checked by the workflow before the data were fetched.
- Data: public Binance spot 1h klines through 2026-11-23 00:00 UTC (exclusive); all seven coins read, none excluded. Valid bars / missing hours (absent + invalid) / of which invalid rows: BTCUSDT 81,094 / 142 / 14; ETHUSDT 81,094 / 142 / 14; BNBUSDT 79,158 / 135 / 13; XRPUSDT 74,895 / 97 / 9; ADAUSDT 75,306 / 98 / 10; LTCUSDT 78,270 / 135 / 13; TRXUSDT 73,980 / 97 / 9 (data hashes in the report).
- Program output copied from the job log, not edited: `specs/zero-pip-lab/RESULTS_ZEROPIP_v2_report.md` (SHA-256 `634ec433e5edaf821516a6e9cab925d5132026cc2091faa796e07e159586bfd5`); full decoded results `specs/zero-pip-lab/RESULTS_ZEROPIP_v2_results.json` (SHA-256 `f1ec62ce945896229beb21c420cfd8dd2e7432a0f4666a7316290ea1af681af9`; decoded from the `ZP|` lines of the log with the program's own `decode_chunks`).

## 0. Summary in Persian (for the owner)

- **نتیجه: NO_CANDIDATE.** هیچ‌کدام از ۶ قاعده‌ی برتر (۳ خرید، ۳ فروش) شرط‌های PASS را نیاورد. روی BTC در دوره‌ی holdout (۲۰۲۳ تا ۲۰۲۶) همه‌ی شش قاعده بعد از هزینه‌ی ۰٫۱۰٪ **منفی** بودند (از −۰٫۱۲ تا −۰٫۳۰ R در هر معامله) و بازه‌ی اطمینان ۹۰٪ هر شش‌تا کاملاً زیر صفر است.
- **نقاط «۰ پیپ» پیشاپیش قابل تشخیص نیستند.** اگر در یک ساعت تصادفی وارد شوید (حد ضرر ۱×ATR، حد سود ۳ برابرِ حد ضرر، ۲۴ ساعت)، حدود ۶ تا ۷٫۵٪ ورودها «تمیز» می‌شوند (به حد سود می‌رسند و بیشینه‌ی حرکت خلاف جهت ≤ ۲۵٪ حد ضرر). در نگاه بعد از وقوع، هفته‌ای حدود ۴ تا ۵ نقطه‌ی تمیز هست؛ ولی میانه‌ی ۱۴ ویژگی در لحظه‌ی ورودِ تمیز با میانه‌ی همه‌ی ساعت‌ها تقریباً یکی است (صدک ۰٫۴۱ تا ۰٫۵۷)، یعنی الگوی مشترکِ قابل‌استفاده‌ای دیده نشد.
- **حد ضرر کوچک‌تر کمک نمی‌کند:** با ۰٫۵×ATR (حدود ۰٫۳ تا ۰٫۴۷٪ قیمت) نقاط تمیز بیشتر می‌شود (۸ تا ۹ در هفته برای k=3)، اما هزینه ۰٫۱۰٪ چند برابرِ سهمِ هر R می‌شود و میانگین ورود تصادفی −۰٫۳۳ تا −۰٫۴۱ R است.
- بهترین قواعد کشف (t حدود ۳٫۵ و ۳٫۲) از بهترین قاعده‌ی ۵۸۱ قاعده‌ی تصادفی در کالیبراسیون مصنوعی (میانه‌ی t = ۳٫۶) بهتر نبود؛ و تنها نامزدِ «مثبت و معنی‌دار در کشف» (فروش، dlow168≥q80 و ret24≤q20: +۰٫۳۶ R) در holdout به −۰٫۳۰ R برگشت.
- محدودیت‌ها: بازبینی مستقل نشده؛ تست‌ها مصنوعی و هم‌نویسنده‌اند؛ دیتای BTC سوخته است؛ نبودِ PASS یعنی «اثر قوی پیدا نشد»، نه «هیچ اثری وجود ندارد».

## 1. Verdict (mechanical, per the preregistration)

| dir | rank | rule | verdict | H1 BTC holdout | H2 other coins | H3 years > 0 |
|---|---|---|---|---|---|---|
| long | 1 | ret6>=q80 & volratio>=q80 | FAIL | no | no | 0 of 4 |
| long | 2 | dlow24>=q80 & volratio>=q80 | FAIL | no | no | 0 of 4 |
| long | 3 | body>=q80 & range>=q80 | FAIL | no | no | 1 of 4 |
| short | 1 | dlow168>=q80 & ret24<=q20 | FAIL | no | no | 0 of 4 |
| short | 2 | ret6>=q80 & volratio>=q80 | FAIL | no | no | 0 of 4 |
| short | 3 | dlow24<=q20 & s_asia==1 | FAIL | no | no | 0 of 4 |

Enough trades existed everywhere (no INCONCLUSIVE). Overall: NO_CANDIDATE; no forward test is warranted by this study.

Numbers behind it (sequential one-position policy, net R at the primary cost 0.10%; 90% week-cluster bootstrap intervals; "lift" = rule minus the same policy on every free hour):

| rule | disc. trades / mean net | BTC holdout n | mean net R [90% CI] | lift [90% CI] | other coins n | mean net R [90% CI] | lift [90% CI] |
|---|---|---|---|---|---|---|---|
| long 1 | 1,516 / +0.034 | 1,395 | −0.167 [−0.245, −0.084] | +0.018 [−0.042, +0.078] | 7,846 | −0.097 [−0.145, −0.055] | +0.049 [+0.015, +0.082] |
| long 2 | 1,114 / +0.066 | 1,024 | −0.151 [−0.241, −0.056] | +0.034 [−0.046, +0.113] | 5,692 | −0.122 [−0.172, −0.074] | +0.024 [−0.016, +0.062] |
| long 3 | 2,432 / −0.073 | 2,177 | −0.121 [−0.179, −0.056] | +0.065 [+0.016, +0.112] | 11,884 | −0.116 [−0.154, −0.081] | +0.030 [+0.005, +0.056] |
| short 1 | 193 / +0.359 | 281 | −0.300 [−0.460, −0.131] | −0.081 [−0.237, +0.088] | 1,591 | −0.079 [−0.182, +0.029] | +0.058 [−0.034, +0.151] |
| short 2 | 1,677 / +0.028 | 1,418 | −0.205 [−0.278, −0.131] | +0.015 [−0.046, +0.074] | 8,140 | −0.115 [−0.163, −0.069] | +0.022 [−0.013, +0.057] |
| short 3 | 1,247 / −0.007 | 793 | −0.164 [−0.254, −0.063] | +0.056 [−0.032, +0.148] | 5,630 | −0.153 [−0.207, −0.100] | −0.016 [−0.060, +0.028] |

BTC holdout mean net R at the cost sensitivities 0.04% / 0.10% / 0.16%: long 1 −0.043 / −0.167 / −0.291; long 2 −0.026 / −0.151 / −0.276; long 3 +0.007 / −0.121 / −0.249; short 1 −0.103 / −0.300 / −0.497; short 2 −0.091 / −0.205 / −0.319; short 3 −0.051 / −0.164 / −0.277. Even at the lowest assumed cost no rule reaches the +0.10 R threshold. Holdout years 2023 / 2024 / 2025 / 2026 (mean net R): long 1 −0.16 / −0.10 / −0.21 / −0.21; long 3 −0.12 / 0.00 / −0.14 / −0.24; all other rules negative in all four years.

## 2. What the data say about the owner's three questions

1. **Meaning of "0 pip".** Operationalized in the preregistration as CLEAN: a bracket entry (stop a×ATR14, TP k×stop, horizon h hours, stop-first within a bar) that reaches its TP with a maximum adverse excursion of at most 0.25 of the stop distance.
2. **The past points (descriptive, BTC; primary bracket a=1, k=3, h=24; discovery 2017–2022 / holdout 2023–2026).**

| dir | P(win) | P(CLEAN) | median stop (% of price) | CLEAN points per week, one at a time, with hindsight | random-entry mean net R at 0.04% / 0.10% / 0.16% |
|---|---|---|---|---|---|
| long, discovery | 0.192 | 0.062 | 0.95 | 3.8 | −0.080 / −0.153 / −0.226 |
| long, holdout | 0.212 | 0.075 | 0.59 | 4.7 | −0.050 / −0.171 / −0.292 |
| short, discovery | 0.206 | 0.067 | 0.95 | 4.2 | −0.062 / −0.135 / −0.208 |
| short, holdout | 0.205 | 0.072 | 0.59 | 4.8 | −0.114 / −0.235 / −0.356 |

About a third of the winning brackets are CLEAN. The smaller the stop (a=0.5: median 0.47% / 0.30% of price), the more CLEAN points exist in hindsight (7.8 / 9.1 per week for k=3, h=24; about 13–14 for k=2) but the more the fixed 0.10% round trip eats (random-entry net −0.33 / −0.41 R for long k=3, h=24). Only the widest bracket (a=2, k=3, h=24) is marginally positive for random entries, and only at the assumed 0.04% cost (+0.011 to +0.016 R long, +0.003 R short discovery): not a finding. The full 48-row base-rate table is in the verbatim report.
3. **The common pattern.** None usable. The median of each of the 14 continuous features at CLEAN entries sits at the 0.41–0.57 percentile of the all-hours distribution, for both directions (the one outlier, short `downrun` at 0.76, is a discrete feature whose median is 1 in both samples). The ranked rules that came out on top of the discovery period are one idea in two directions, "a large 6-hour move in the trade direction on high volume" (long 1 and short 2), plus a few variations on volatility, time of day and distance from recent lows. Their best week-clustered t was 3.47 (long) and 3.21 (short), against a median of 3.6 (range 2.9–4.8) for the best of the family on pure random walks of real size in the pre-freeze calibration (preregistration v1, section 12): indistinguishable from selection among 581 rules. In the holdout the effect was gone (above).

## 3. Reading, with its limits

- One thing is mildly positive and should be read with caution: the lift of three rules over the all-free-hours policy has a positive lower bound (long 1 on the other coins, long 3 on BTC and on the other coins; +0.02 to +0.07 R per trade). That is 3 of 12 lift intervals, from rules that share volume and range ingredients, none with a positive absolute net result; this is about what chance and correlated rules give, it does not make money after costs, and it is not a pass criterion on its own.
- The pre-freeze calibration showed that this design confirms only strong effects (about 0.2 of a bar's standard deviation per bar in a planted window). A moderate real effect would very likely also have ended in FAIL. The result therefore says "no strong, cost-surviving, out-of-sample-stable entry rule among these 581 per direction", not "nothing can ever work".
- Costs are an assumption (0.10% round trip; sensitivities 0.04% and 0.16%), not measured KCEX costs. Entry at the next bar's open and stop-first within a bar are conservative conventions; real fills would differ.
- Holdout and "other coins" are not clean in the sense of a never-seen future: the history 2023–2026 is known to the humans involved (RESEARCH_RULES rule 2). The study was designed to be hard to pass for noise, not to be a proof.
- The family was fixed in advance (34 singles + 547 pairs per direction, 14 continuous features at 20/80 percentile thresholds from pre-split data, 6 boolean); only the top three per direction by discovery t were carried to the holdout; no rule, threshold or bracket was added or changed after the result.

## 4. Known issues found while reading the code after the run (disclosed, not fixed: the code is frozen)

- `boot_diff_ci` draws its resampling matrix twice (a duplicated line; the second draw is used). Both draws are valid i.i.d. resamples, so the intervals are unbiased; only the exact random numbers differ from a version without the duplicate. It is in v1 and v2 alike. Any later version should remove it and says so.
- Decoded JSON re-rendered by `render` reproduces every number of the printed report; only the order of dictionary keys differs (the one-line family summary and the order of the feature rows in the CLEAN-profile tables), a cosmetic effect of `sort_keys`.

## 5. Checks made after the run (author's own, not independent)

- The stored verdict of every evaluated rule re-derived with the frozen `verdict` function from the stored numbers: 6 of 6 identical; no PASS anywhere; the stored configuration equals the code's.
- Base-rate table: for all 48 rows P(CLEAN) ≤ P(win) ≤ 1, "clean share of wins" = P(CLEAN)/P(win), and mean net R falls monotonically with cost.
- The log-decoded JSON re-rendered into the same report lines as the printed report (section 4). The run artifact itself could not be downloaded from this workspace (blocked host), so the log is the only transcription path; the 10 transmitted chunks were all present and decoded.
- Data notes in the log match diagnostic 2 (invalid rows per coin; missing hours = absent hours + invalid rows).

## 6. Status and next steps

- Per RESEARCH_RULES rule 10, NO_CANDIDATE closes this study in this form. No change of direction, stop multiple, TP multiple, horizon, feature or threshold on this data may follow; a new idea needs a new preregistration and counts toward multiplicity.
- Requested from the red-team auditor: independent review of `zeropip_v2.py` (and its ~70-line difference from v1) and of this record. A defect found there is handled by section 5.4 of the v2 preregistration (a v3 preregistration, results left published).
- PR #46 stays Draft until that review; nothing in the engine or the live record (the 90-day Trend record from 2026-11-22) is affected by this result.
