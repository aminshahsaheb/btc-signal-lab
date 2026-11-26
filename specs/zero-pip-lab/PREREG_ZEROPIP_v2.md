# PREREG_ZEROPIP_v2 — the same "0-pip" study as v1, with one data-ingest correction found at the first contact with real data

**Status: FROZEN WITH THE v2 CODE HASH BELOW, BEFORE ANY REAL-DATA RESULT.** No outcome, feature statistic, rule ranking or return has ever been computed on real data for this experiment: the single scoring run of v1 stopped at the data stage (section 1). Nothing here is self-certified: the tests are synthetic and were written by the author of the code, and no independent review exists (section 6). A PASS would mean "worth a forward paper test", never "proven". The expected outcome is still NO_CANDIDATE (PREREG_ZEROPIP_v1.md section 12).

`research/zero-pip-lab/zeropip_v2.py` SHA-256: `09b23b4df09f144c3c78c53afe122ed4c1ef1c0348ded3ac522b0be75b1288dd` (also in `research/zero-pip-lab/CODE_SHA256_V2.txt`; CI and the v2 run workflow refuse to run if the file differs).

Referenced and unchanged (kept published; its hash is pinned here and checked by CI): `specs/zero-pip-lab/PREREG_ZEROPIP_v1.md` SHA-256 `fb6c5f2a0d480b1a9cbc61497019d455f2534ea6aaeda72e287366f954ce2ce2`; v1 code `research/zero-pip-lab/zeropip.py` SHA-256 `b93e1f997819e778e029adc2fd68a221cc03c99f3824209065466800d1ec6b2b`.

## 0. Summary in Persian (for the owner)

- اجرای اول (v1) **هیچ نتیجه‌ای تولید نکرد**. کد قفل‌شده‌ی v1 هنگام خواندن دیتا روی ۱۴ کندل ساعتیِ نامنظم در تاریخچه‌ی خودِ بایننس (توقف/نگهداری‌های صرافی بین ۲۰۱۷ تا ۲۰۲۳؛ زمان بسته‌شدنِ کندل زودتر از ساعت است) متوقف شد و کل BTC را کنار گذاشت. علت شبکه نبود. همین ردیف‌ها (۹ تا ۱۴ عدد) در هر هفت کوین هست.
- v2 **فقط سیاست خواندن دیتا** را عوض می‌کند: ردیفی که زمان بسته‌شدنش دقیقاً «بازشدن + ۳٬۵۹۹٬۹۹۹ میلی‌ثانیه» نیست (یا ردیف خراب است) مثل یک ساعتِ غایب «نامعتبر» حساب می‌شود؛ ترمیم یا استفاده نمی‌شود و هیچ تصمیمی که پنجره‌اش به آن بخورد وارد تحلیل نمی‌شود. سقف ۱٪ ساعت‌های گمشده همان است (واقعاً ≈ ۰٫۱۳ تا ۰٫۱۸٪).
- همه‌ی تعریف‌ها، ویژگی‌ها، ۵۸۱ قاعده، آستانه‌ها، بوت‌استرپ، هزینه و معیار PASS **عیناً v1** است. یک آزمون خودکار درخت نحوی (AST) هر تعریف کد را با v1 مقایسه می‌کند و فقط توابع خواندن دیتا/گزارش را مجاز به تفاوت می‌داند.
- تا این لحظه هیچ بازده یا نتیجه‌ای حساب یا دیده نشده؛ پس این تغییر نمی‌تواند بر اساس نتیجه انتخاب شده باشد. v1 همان‌طور منتشر می‌ماند. هشدار همیشگی: بازبینی مستقل انجام نشده، تست‌ها مصنوعی و هم‌نویسنده‌اند، پیش‌بینی نویسنده NO_CANDIDATE است و هیچ‌چیز شاهد بازدهٔ آینده نیست.

## 1. What happened (facts, in order)

| when | what | where |
|---|---|---|
| 2026-11-25 | v1 code, tests and preregistration frozen at code hash `b93e1f99…` | commit `c05213e` (PR #46, Draft) |
| 2026-11-26 | v1 scoring run (the single run of section 9 of v1) | workflow run `45753329545` (commit `d78f4a7`): failed at the data stage with `BTCUSDT unavailable: infrastructure failure, not a result`; the frozen code did not print the reason |
| 2026-11-26 | read-only fetch diagnostic 1 (BTCUSDT, ETHUSDT; imports the frozen v1 fetcher unchanged, computes nothing) | workflow run `45754505815` (commit `60a2897`) |
| 2026-11-26 | read-only fetch diagnostic 2 (all seven coins, lists every failing row) | workflow run `45799172122` (commit `7299da3`) |

Cause (from diagnostics 1 and 2): the frozen v1 `parse_rows` treats "close time ≠ open time + 3,599,999 ms" as fatal for the whole coin. Public Binance spot history contains a few rows per coin where the bar was cut short or is an empty placeholder around exchange maintenance (examples: a zero-volume row whose close time equals its open time, rows that close 14.8 s or 29.2 minutes after their open, one that closes 999 ms early). Every other check passed on all seven coins: all open times are on the hour, none is out of order, no malformed OHLC or volume row exists. v1 was therefore stricter than the real data allow; the v1 text (section 3) listed "an unexpected close time" among the exclusion causes and section 9.3 allowed a re-run only with an unchanged code hash, which would have failed identically. This is a defect of the v1 ingest policy, found before any analysis ran, so it is handled by section 9.4 of v1: this v2 preregistration, a new hash, and v1 left published.

Diagnostic 2 (rows per coin as returned by the public API up to 2026-11-23 00:00 UTC exclusive; "failing" = rows with an irregular close time; fraction = (absent hours + failing rows) / expected hours):

| coin | rows | absent hours | failing rows | fraction of hours missing or invalid |
|---|---|---|---|---|
| BTCUSDT | 81,108 | 128 | 14 | 0.00175 |
| ETHUSDT | 81,108 | 128 | 14 | 0.00175 |
| BNBUSDT | 79,171 | 122 | 13 | 0.00170 |
| XRPUSDT | 74,904 | 88 | 9 | 0.00129 |
| ADAUSDT | 75,316 | 88 | 10 | 0.00130 |
| LTCUSDT | 78,283 | 122 | 13 | 0.00172 |
| TRXUSDT | 73,989 | 88 | 9 | 0.00131 |

The 14 failing BTCUSDT rows (open time UTC; close − open in ms; volume): 2017-09-06 16:00 (0; 0), 2017-12-18 12:00 (1,753,419; 242.03), 2018-01-04 03:00 (14,838; 4.64), 2018-02-08 00:00 (1,694,788; 1,521.54), 2018-07-04 00:00 (1,345,551; 1,543.48), 2019-06-07 21:00 (793,524; 0), 2020-02-19 11:00 (2,132,286; 405.97), 2020-03-04 09:00 (1,306,694; 254.39), 2020-12-21 13:00 (2,840,521; 3,685.45), 2021-02-11 03:00 (2,454,773; 0), 2021-04-25 04:00 (58,146; 5.89), 2021-08-13 01:00 (3,599,000; 1,980.13), 2021-12-24 04:00 (3,594,362; 560.62), 2023-03-24 12:00 (2,381,646; 0). Thirteen are in the discovery period and one (2023-03-24 12:00) is in the holdout period.

Real data seen by the author for this decision: row counts, timestamps, close-minus-open deltas, volumes, trade counts and a few raw rows of early bars. No return, outcome, feature or rule statistic was computed.

## 2. What changes and what does not

Changed (data ingest and reporting only; `zeropip_v2.py` vs `zeropip.py`; run `diff -u research/zero-pip-lab/zeropip.py research/zero-pip-lab/zeropip_v2.py`, about 70 changed lines):

| item | v1 | v2 |
|---|---|---|
| a row whose close time ≠ open + 3,599,999 ms, or with non-positive low, low above min(open, close), high below max(open, close), negative volume or taker-buy volume above volume | whole coin excluded | that hour is an **invalid hour**: all bar values NaN, exactly like an absent hour; never repaired, never used; counted and listed in the report |
| open time off the hour; open times not strictly increasing; a bar extending past the data end; no valid bar at all | whole coin excluded | unchanged: whole coin excluded |
| exclusion for missing hours | more than 1% of hours missing | more than 1% of hours missing **or invalid** (absent + invalid together) |
| data table of the report | bars, missing hours | valid bars, missing hours (absent + invalid), of which invalid rows |
| diagnostics | exclusion reasons not printed | one `DATA_NOTE` line per coin is printed first (also when BTCUSDT is unavailable, before the run stops) |
| `VERSION`, report title | `zeropip-v1` | `zeropip-v2` |

Unchanged: everything else, by reference to `PREREG_ZEROPIP_v1.md`: sections 1, 2, 4, 5, 6, 7, 8, 10, 11, 12 and 14 apply verbatim (definitions of the bracket, CLEAN, features, the 581-rule family per direction, the ranking, the confirmation and verdict criteria H1–H3, the bootstrap and its seeds, the cost model, the split at 2023-01-01, the data window ending 2026-11-23 00:00 UTC, the six other coins, limitations, why NO_CANDIDATE is expected, the environment). Section 3 of v1 applies except for the exclusion sentence replaced by the table above.

Effect on the analysis: a decision hour is valid only if its entry bar, its ATR and the whole h-bar window exist (v1 section 2). An invalid hour is NaN, so every decision whose features, ATR or window touch it is invalid, as for an absent hour. A test checks that features and outcomes computed with an invalid hour equal those computed with the same hour absent. The 14 BTC invalid hours add 0.017% of hours to the 0.158% already absent; about 480 decisions after each can lose a long-window feature, which is how v1 already treated gaps.

Alternatives not chosen: accepting a partial-hour row as a full-hour bar (its high and low cover only part of the hour and would distort ATR and the bracket outcome); repairing a row; widening the 1% cap.

## 3. Mechanical evidence that only ingest changed (author's own checks)

`research/zero-pip-lab/test_zeropip_v2.py` (38 tests; the 30 v1 tests run against v2 code, `test_validation` rewritten for the new policy, plus 8 new tests) contains:

- an AST comparison of every top-level definition and assignment of `zeropip.py` and `zeropip_v2.py`: only `parse_rows`, `build_series`, `load_all`, `render`, `main` and `VERSION` differ, and the only added definition is `row_problems`;
- a check that `zeropip.py` still has the frozen v1 hash;
- tests that irregular rows become invalid hours, that an invalid hour behaves exactly like an absent hour (features and outcomes identical), that clean data are ingested identically to v1 (same arrays and data hash), that invalid rows count toward the 1% cap, that `main` prints the data notes before stopping, and that the report shows the invalid rows.

A dress rehearsal on synthetic klines for the seven coins (BTC and ETH with 143 missing hours of which 14 irregular rows; fat tails, volatility clustering) ran `main()` end to end without error in a few seconds; the printed result chunks decoded to the same JSON as the file. This is a check of the code path, not evidence about BTC.

## 4. Data policy (replaces the exclusion sentence of v1 section 3)

Missing and invalid hours stay as gaps (NaN). A coin is excluded (and listed) if its fetch fails, if its open times are not on the hour or not strictly increasing, if a bar extends past the data end, if no valid bar exists, or if more than 1% of its hours are missing or invalid. A row with an irregular close time or a malformed bar is an invalid hour (section 2). If BTCUSDT is unavailable the run is INVALID (an infrastructure failure, not a result). If other coins are excluded the confirmation uses the rest.

## 5. Run protocol (replaces section 9 of v1 for this version)

1. CI (`verify-zero-pip-lab-v2.yml`) must be green on the Draft PR: the v2 code hash, this file's code hash, the pinned v1 preregistration hash and the 38 synthetic tests.
2. One run, triggered by pushing `research/zero-pip-lab/RUN_REQUEST_V2.txt` on a `research/zero-pip-**` branch (workflow `run-zero-pip-lab-v2.yml`; the v1 run workflow listens to a different file and cannot start). It re-checks the hashes, re-runs the tests, fetches the data, prints one `DATA_NOTE` line per coin, the full report and the results as encoded JSON lines.
3. A re-run is allowed only for an infrastructure failure (data not fetched, run INVALID) with an unchanged code hash. If a data-validation failure on a condition not seen in diagnostic 2 happens again, one further ingest-only version may be frozen under the same conditions as this one (no real-data result ever computed, cause documented, v1 and v2 left published); once any result has been computed this is no longer allowed.
4. A defect in the analysis code found after a result is not patched silently: a v3 preregistration lists it and the v2 results stay published.
5. No rule, coin, window, threshold, cost or feature may change after any output. NO_CANDIDATE closes the branch in this form (RESEARCH_RULES rule 10). No flipping of direction, no change of k, stop, horizon, feature or threshold after the result (rule 4); a new idea needs a new preregistration and counts toward multiplicity.
6. If more than one rule passes, no choice is made from holdout performance; every passing rule goes to a forward paper test, and the simplest is preferred only on grounds of simplicity.

## 6. Review status

Written by the author of the code. **No independent review of the v1 or v2 code has been completed.** After the v2 change the author ran only their own checks: the 38 synthetic tests, the dress rehearsal of section 3 and the two read-only diagnostics. The earlier attempt at a review by a fresh reviewer agent of the same model family was interrupted twice by an API rate limit and returned no findings (v1 section 13). An independent review by the red-team auditor of the v2 code and of the results is requested after the run; a defect found then is handled by section 5.4, and any forward test is blocked until such a review has been done.

## 7. Change log

- v1 (2026-11-25): first version; its single scoring run (2026-11-26) stopped at the data stage and produced no result.
- v2 (2026-11-26): data-ingest correction of section 2; frozen at the code hash above before any real-data result.
