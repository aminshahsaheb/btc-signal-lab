# FORWARD_JOURNAL_SPEC_v1 — revision r6 — Path A: forward validation of MO-BIN-2%-8h-v1

**وضعیت:** DRAFT r6 — NOT LOCKED — SPEC ONLY. نسخه‌ی r5 (SHA-256 `e6fdf34cdb1b78f35d5dc0373eb99ba6dd33f24bbe10ae59c3fa983d2e6fb81e`)، r4 (SHA-256 `59e8f8fa1497477ed26deafacd6797f2e73640e0eef9384808a73de6e47169ba`)، r3 (SHA-256 `6be468ec9995a421f003680e1b284dac12eae082f1792f73334ef54f9cf26950`)، r2 (SHA-256 `8ac30415bddd513ac4ce982d0431d8528c2eb8b50bb6d976dd323d539835e46c`) و r1 (SHA-256 `b60da29c825e5479e091a05d9d0e4de51172535957a9133fb8b71066edc5bd1c`) هرگز قفل نشدند و با r6 جایگزین می‌شوند. تا دستور `lock` از GPT و ثبت SHA-256 این فایل، هیچ بخشی معتبر نیست.
**هدف:** پروتکل ثبت و ارزیابی پیش‌بینی‌های آینده‌ی MO-BIN-2%-8h-v1 از T0 به بعد. Path A است، نه v3.
**مرجع:** شرط‌های ۱ تا ۱۷ در پیام GPT (تأیید Section F)، شش اصلاح بازبینی GPT روی r1، شش اصلاح بازبینی روی r2، چهار اصلاح بازبینی مستقل GPT روی r3 (۲۰۲۶-۱۰-۱۱)، پنج مورد بازبینی مستقل GPT روی r4 (۲۰۲۶-۱۰-۱۲) و بازبینی مستقل GPT روی r5 (رسیده در ۲۰۲۶-۱۰-۱۴؛ نتیجه‌ی آن «NO LOCK» بود) با این موارد: (۱) سیاست انتشار و تلاش دوباره‌ی `CHECKPOINT` ها و ترتیب پذیرش مقصد: فقط آخرین `CHECKPOINT` دوباره منتشر می‌شود و قدیمی‌ترِ منتشرنشده با `EVENT(CHECKPOINT_SUPERSEDED)` برای همیشه کنار می‌رود (B.7 بند ۲ و ۵، KAT-10c)؛ (۲) قرارداد مقصد انتشار (ده کلید در `CONFIG` و دو namespace: `checkpoints` و `manifests`) و جای ذخیره‌ی manifest (B.7 بند ۴ و ۹)؛ مقصد در این سند **نام برده نمی‌شود** و شرط lock باز است؛ (۳) یک گرامر یکتای زمان؛ تاریخ و ساعت ناممکن `MALFORMED_*` است نه crash (B.2 بند ۸، KAT-15a)؛ (۴) envelope دقیقاً سه‌کلیدی و انواع مقدار مجاز (B.2 بند ۱ و ۶، KAT-15b و KAT-15c)؛ (۵) manifest `FJ-ANALYSIS-3` و ثبت hash های gate، benchmark و کد تحلیل (C.17، KAT-12)؛ (۶) شاهد کامل کندل: هر `CANDLE` و `CANDLE_ANOMALY` پیام خام خود را نگه می‌دارد و verifier آن را دوباره اعتبارسنجی می‌کند (B.3، B.6 بند ۱۱، KAT-16)؛ (۷) قاعده‌ی قطعی انتخاب `clock_offset_ms` از چند منبع NTP (C.2، KAT-11c)؛ (۸) تفکیک «حد مستندشده‌ی سرویس» از «رفتار عملیاتی مشاهده‌شده» برای عمر ۲۴ ساعته‌ی اتصال (C.16)؛ به‌علاوه‌ی بسته‌ی بازتولیدپذیر harness با گزارش جداگانه‌ی mutantهای «کشته‌شده با شکست تست» و «کشته‌شده فقط با crash». این سند هیچ feature، threshold هشدار، مدل، ضریب، target، قاعده‌ی سوختن داده یا پروتکل پژوهشی تازه‌ای اضافه یا عوض نمی‌کند؛ r6 فقط ثبت شواهد (journal، ساعت، اتصال، anchoring، تحلیل) را دقیق‌تر می‌کند.
**ممنوعیت‌ها:** اجرای تاریخی جدید؛ امتیازدهی تاریخی؛ v3؛ جست‌وجوی threshold؛ feature جدید؛ ساخت پیاده‌سازی زنده؛ شروع collector؛ اتصال به feed زنده؛ تعیین T0. پیاده‌سازی بعد از lock و قبل از T0 ساخته و تأیید می‌شود (C.1).
**زمان:** همه‌ی زمان‌ها UTC هستند. تصمیم‌ها در `hh:00 UTC` هستند، یعنی هر تصمیم در دقیقه‌ی ۳۰ ساعت تهران (UTC+03:30).
**پارامترهای [P]:** مقدارهای پیشنهادی نگارنده‌اند و در لحظه‌ی `lock` دقیقاً به همین شکل قفل می‌شوند، مگر GPT قبل از lock تغییرشان دهد. هیچ [P] بعد از lock قابل تغییر نیست. فهرست کامل در انتهای سند است.
---

## 0. وضعیت شواهد و داده‌ی سوخته (شرط ۱۵ و ۱۶)

- داده‌ی تاریخی ۵ دقیقه‌ای (۲۰۲۱-۰۱-۰۱ ۰۰:۰۰ تا ۲۰۲۶-۰۹-۲۲ ۲۳:۵۵ UTC) برای این پروتکل **virgin نیست**:
  - Discovery `2021-01-01 .. 2023-12-31` (۳۱۵٬۳۶۰ ردیف): برای fit و همه‌ی انتخاب‌های قبلی سوخته.
  - Confirmation `2024-01-01 .. 2025-01-06` (۱۰۷٬۱۳۶ ردیف): semi-burned؛ ۹ اسکریپت در ۸ branch روی آن امتیاز داده‌اند.
  - Holdout `2025-01-07 .. 2026-09-22` (۱۷۹٬۷۱۲ ردیف): برای model selection در پروژه سوخته.
  - داده‌ی تاریخی بعد از `2026-09-22 23:55` در این پروتکل استفاده نمی‌شود.
- نتایج confirmation قبلی MO-BIN-2%-8h-v1 (مثلاً AUC 0.6721) **پیش‌بینی آینده حساب نمی‌شوند** و نباید به‌عنوان شاهد forward ارائه شوند.
- تنها منبع validation پاک: رکوردهای forward که با real-time capture بعد از spec lock و بعد از T0 ثبت می‌شوند و در adjudication واجد شرایط (ELIGIBLE) شناخته می‌شوند.
- در تهیه‌ی r2، r3، r4، r5 و r6 هیچ داده‌ی بازار (OHLC) اجرا یا امتیازدهی نشد. تنها خواندنِ مربوط به مصنوعات، که فقط یک‌بار و در r2 انجام شد، خواندن سه ستون خروجی مدل (`a`, `b`, `p_MO_2_8`) از `mo_bin_2_8h_confirmation.csv` برای بازیابی ضرایب بود (A.5)؛ ستون `Y` خوانده نشد. در r3، r4، r5 و r6 هیچ فایل تاریخی خوانده نشد، به هیچ feed زنده وصل نشد و همه‌ی آزمون‌ها ساختگی‌اند. آزمون‌های ساختگی r6 با یک harness جداگانه (`spec_checks_r6.py`) اجرا می‌شوند که **پیاده‌سازی زنده نیست**؛ فقط رفتار مرجع‌ِ نوشته‌شده در این spec را روی داده‌ی ساختگی نشان می‌دهد.

---

## A — Exact frozen definition

**A.1 هویت:** `model_id = "MO-BIN-2%-8h-v1"` (Path A). **هویت مدل حفظ می‌شود**: ضرایب forward همان ضرایب تاریخی‌اند (A.5)، نه یک variant. هیچ refit، recalibration، تغییر وزن، تغییر target یا variant در دوره‌ی forward مجاز نیست.

**A.2 ورودی (شرط ۳):** Binance USD-M BTCUSDT perpetual، کندل ۵ دقیقه‌ای. هر کندل با `open_time` (UTC) شناخته می‌شود و `close = open + 5 min`. فقط `high`، `low`، `close` استفاده می‌شوند. کندل در زمان τ قابل‌استفاده است اگر `close ≤ τ`.

**A.3 شبکه‌ی تصمیم (شرط ۳، ۴، ۵):**
- زمان تصمیم `d` = هر ساعت گرد UTC (`hh:00:00Z`) از T0 به بعد. نمونه‌برداری ثابت است و به هشدار وابسته نیست.
- کندل مرجع `t`: `open = d − 5 min`، `close = d`. `C_ref = close(t)`.
- اطلاعات مجاز در `d`: فقط کندل‌هایی با `close ≤ d`.
- `T0` یک نقطه‌ی مشخص روی شبکه‌ی ساعتی است که در ورودی `T0_DECLARATION` اعلام و قفل می‌شود (C.1). اولین تصمیم دقیقاً در T0 است.

**A.4 Features:**
- `range12 = (max H[۱۲ کندل] − min L[۱۲ کندل]) / C_ref`، کندل‌ها با `open ∈ [d−60 min, d−5 min]`؛ این ۱۲ کندل شامل کندل مرجع هستند.
- `range288 = (max H[۲۸۸ کندل] − min L[۲۸۸ کندل]) / C_ref`، کندل‌ها با `open ∈ [d−1440 min, d−5 min]`.
- `a = ln(max(range12, 1e−5))`، `b = ln(max(range288, 1e−5))`.

**A.5 امتیاز و ضرایب (شرط ۲) — اصلاح ۱:**
- `z = w0 + w1·a + w2·b` با ضرایب literal زیر (رشته‌های اعشاری که به float64 تبدیل می‌شوند):

| ضریب | literal |
|---|---|
| `w0` (intercept) | `6.12290270591053` |
| `w1` (ضریب `a`) | `0.778912190870879` |
| `w2` (ضریب `b`) | `0.948640151481306` |

- `z_c = clip(z, −30, +30)`، `p_raw = 1 / (1 + exp(−z_c))`. ذخیره‌ی `p_raw` به‌صورت رشته‌ی کوتاه‌ترین نمایش round-trip float64.
- **اعداد چهار رقمی `6.1229`، `0.7789`، `0.9486` فقط نمایش گرد‌شده‌ی تاریخی‌اند و در کد مجاز نیستند.** استفاده از آن‌ها یک مدل عددی متفاوت است و KAT-1 تا KAT-2 آن را رد می‌کنند (اختلاف `p` تا حدود `2.5e−5`).
- **منشأ (provenance):** فایل `.npy` وزن‌های دقیق (`mo_bin_2_8h_weights_discovery.npy`) در مصنوعات و فهرست bundle نیست. ضرایب از ستون‌های `a`، `b`، `p_MO_2_8` در `mo_bin_2_8h_confirmation.csv` (SHA-256 `9cde7539d4a0f75e284b99bd8cae4171cd5f73eb077c467df031089a4a5a0c80`) بازیابی شدند: کمترین مربعات `logit(p)` روی `[1, a, b]` در ۱۰۵٬۱۵۰ ردیف با `0.05 < p < 0.95`.
  - مقدار بازیابی‌شده با دقت کامل: `[6.1229027059105325, 0.7789121908708792, 0.9486401514813056]`.
  - بیشینه‌ی باقی‌مانده در مقیاس logit: `6.7e−15`؛ انحراف معیار روی ۲۰ زیرنمونه‌ی تصادفی ≤ `2.3e−14`.
  - literal های بالا همان مقدار با ۱۵ رقم معنادارند و ستون `p_MO_2_8` را روی همه‌ی ۱۰۷٬۱۳۶ ردیف تا `1.9e−15` بازتولید می‌کنند.
  - گرد‌شده به چهار رقم، دقیقاً `[6.1229, 0.7789, 0.9486]` می‌شوند.
  - این ضرایب «بازیابی‌شده» هستند، نه فایل اصلی float64؛ عدم قطعیت ≲ `3e−14` است و روی `p` اثری بیش از `1e−13` ندارد.
- ضرایب از fit روی discovery با ۹۶ لیبل مرزی (n = ۳۱۵٬۰۷۳) می‌آیند. refit با embargo (`[6.1212, 0.7790, 0.9478]`) مدل دیگری است و استفاده نمی‌شود.
- در صورت تغییر ضرایب (حتی در رقم‌های آخر) هویت مدل عوض می‌شود و یک نسخه‌ی جدید spec لازم است (C.15).

**A.6 Target / outcome (شرط ۱):**
- برای تصمیم `d`، ۹۶ کندل forward: `k = 1..96` با `open = d + 5(k−1) min` (یعنی از `d` تا `d + 7h55m`). `C_k = close(کندل k)`.
- `m_k = |ln(C_k / C_ref)|`. ابتدا نسبت، سپس لگاریتم. هرگز `ln C_k − ln C_ref`.
- `M96 = max_{k=1..96} m_k`؛ `k* = اولین k که بیشینه را می‌دهد`.
- `Y = 1[M96 ≥ ln(1.02)]`، با `ln(1.02) = 0.01980262729617973` (float64).
- فقط close های ۵ دقیقه‌ای. فتیله‌ی داخل کندل حساب نمی‌شود.
- معنای هم‌ارز: در پنجره‌ی ۸ ساعته، یکی از close ها نسبت ≥ 1.02 یا ≤ 1/1.02 (≈ 0.980392، یعنی حدود −1.9608٪) به `C_ref` داشته باشد. در درصد ساده این شرط نامتقارن است.
- **زمان resolution:** `R = d + 8h`. Y فقط وقتی محاسبه می‌شود که هر ۹۶ کندل بسته و موجود باشند.
- **Y هرگز برای outcome حل‌نشده تولید نمی‌شود.** outcome حل‌نشده برچسب منفی نیست (C.3).

**A.7 Threshold (شرط ۸):** در این spec هیچ threshold هشدار انتخاب نشده است. تنها خروجی مدل `p_raw` است. عدد ۱.۰۲ بخشی از تعریف target است و پارامتر قابل تنظیم نیست.

**A.8 Known-answer tests (فقط داده‌ی ساختگی؛ هیچ داده‌ی بازار در این بخش نیست):**

**KAT-1 — تابع feature به p (ضرایب A.5):**

| range12 | range288 | a | b | z | p_raw |
|---|---|---|---|---|---|
| 0.004 | 0.02 | −5.52146091786225 | −3.91202300542815 | −1.88893261089720 | 0.131366220369780 |
| 0 (clip) | 0 (clip) | −11.5129254649702 | −11.5129254649702 | −13.7662786484249 | 1.05046283162816e−06 |
| 0.5 | 0.5 | −0.693147180559945 | −0.693147180559945 | 4.92545467053938 | 0.992792894557858 |

**KAT-2 — زنجیره‌ی کامل روی ۳۸۴ کندل ساختگی:**
- کندل `i = 0..383`: `open_i = 2030-01-01T00:00Z + 5i min`؛ `C_i = 100000 + 7·((37i) mod 101) − 5·((13i) mod 53)`؛ `H_i = C_i + 11 + (i mod 7)`؛ `L_i = C_i − 13 − (i mod 5)`.
- checksum متن سری (سطرهای `i,C_i,H_i,L_i` با `\n`): `sha256 = a6a5da833b81eefb7e09c0528fd25c796b2399fb6b68b9cfa080ac96caba4013`.
- `d = 2030-01-02T00:00Z` (همان open کندل ۲۸۸)، کندل مرجع `t = کندل ۲۸۷`.
- `C_t = 99993`؛ `H12 = 100561`، `L12 = 99836`؛ `H288 = 100683`، `L288 = 99736`.
- `range12 = 0.00725050753552749`، `range288 = 0.00947066294640625`.
- `a = −4.92668380766544`، `b = −4.65955636933404`، `z = −2.13479363248697`، `p_raw = 0.105760774280049`.
- `M96 = 0.00687678366303584` در `k* = 76` (`C_{t+76} = 100683`)، `Y = 0`.
- با ضرایب چهار رقمی، `p` برابر `0.105783894786563` می‌شود؛ این مقدار **رد** است.

**KAT-3 — مرزها و ترتیب عملیات.** در همه‌ی ردیف‌ها `C_ref = 50000` (به‌جز ردیف آخر) و ۹۵ close دیگر برابر `C_ref` هستند:

| `C_ref` | `k*` | `C_{k*}` | نسبت `C_{k*}/C_ref` | `Y` |
|---|---|---|---|---|
| 50000 | 40 | 51000 | 1.02 | 1 |
| 50000 | 40 | 50999 | 1.01998 | 0 |
| 50000 | 70 | 49019 | 0.98038 | 1 |
| 50000 | 70 | 49020 | 0.98040 | 0 |
| 100.0 | 40 | 102.0 | 1.02 | 1 |

ردیف آخر **ترتیب عملیات** را می‌آزماید: با «نسبت اول» `Y = 1`. با «اختلاف لگاریتم‌ها» مقدار `0.019802627296178876 < ln(1.02) = 0.01980262729617973` می‌شود و `Y = 0`؛ این پیاده‌سازی رد است. همچنین close در `k = 97` (خارج از پنجره) نباید روی `M96` اثر بگذارد.

**KAT-4 — زنجیره‌ی hash و serialization (بند B.2):** مقدارها در B.2 آمده‌اند.

**KAT-5 — متریک‌ها و bootstrap (بند C.12):** مقدارها در C.12 آمده‌اند.

**KAT-6 — جدول eligibility (بند C.7):** مقدارها در C.7 آمده‌اند.

**KAT-7 — bootstrap روی شبکه‌ی کامل با ساعت‌های خالی (بند C.12):** مقدارها در C.12 آمده‌اند.

**KAT-8 — اعتبارسنجی payload کندل و endpoint (بند C.2):** مقدارها در C.2 آمده‌اند.

**KAT-9 — ترتیب زمانی conflict و ترتیب finalization/adjudication (بندهای C.4 و C.7):** مقدارها در همان بندها آمده‌اند.

**KAT-10 — anchoring و truncation چک‌پوینت (بند B.7):** مقدارها در B.7 آمده‌اند.

**A.9 هم‌خوانی با کد تاریخی:** `mo_bin_2_8h.py` همین ترتیب feature و target را دارد (`rolling(12)` و `rolling(288)` که کندل جاری را شامل می‌شوند، `np.log(c[k:]/c[:-k])`، clip به `1e−5`، `ln(1.02)`). **هشدار:** docstring آن فایل بازه را `H[t-11:t]` می‌نویسد که در slice پایتون کندل `t` را شامل نمی‌شود؛ کد اجرا‌شده `rolling` است و کندل `t` را شامل می‌شود. کد تعریف است، نه docstring.

---

## B — Data schema

**B.0 اصل:** تنها شاهد معتبر `journal` است. جدول‌های دیگر **نمای مشتق‌شده (derived view)** از journal هستند و هر ردیفشان `journal_seq` و `journal_entry_hash` ورودی منبع را دارد. نمای مشتق قابل بازسازی قطعی است؛ ردیفی که با بازسازی نخواند، ردیف جعلی یا دست‌کاری‌شده است.

**B.1 فایل‌ها:** `journal.jsonl` (شاهد اصلی) و `human_journal.jsonl` (جدا، B.4). هر دو append-only، UTF-8، پایان خط LF.

**B.2 فرمت ورودی journal و عملیات hash — بایت به بایت (اصلاح ۴):**
1. هر ورودی یک `payload` (شیء JSON) دارد. مقدارها فقط `string`، `integer` (قدر مطلق ≤ 2^53)، `boolean`، `null`، آرایه یا شیء هستند. **هیچ عدد اعشاری در payload نیست**: هر مقدار غیرصحیح به‌صورت رشته ذخیره می‌شود (رشته‌ی کوتاه‌ترین نمایش round-trip، یا رشته‌ی اصلی صرافی برای کندل‌ها). **(r6)** عدد اعشاری (`1.5`)، عدد صحیح‌نمای اعشاری (`1.0`)، نماد علمی (`1e2`)، `NaN`، `Infinity` و عدد صحیح با قدر مطلق بیش از `2^53` در خط journal `MALFORMED_VALUE` است (خودِ `±2^53` مجاز است)؛ KAT-15c.
2. **Canonical serialization** `canon(x)`: بایت‌های ASCII خروجی `json.dumps(x, sort_keys=True, separators=(",", ":"), ensure_ascii=True, allow_nan=False)`. یعنی کلیدها به ترتیب code point مرتب، بدون فاصله، هر نویسه‌ی غیر ASCII به‌صورت `\uXXXX` با hex حروف کوچک (جفت surrogate برای بالاتر از `U+FFFF`)، و escape های استاندارد `\"` `\\` `\n` `\r` `\t` `\b` `\f` و `\u00XX` برای بقیه‌ی کنترل‌ها.
3. `payload` همیشه شامل `seq` (عدد صحیح؛ GENESIS برابر ۰ و هر ورودی بعدی یکی بیشتر)، `type` و `recorded_at_utc` (`YYYY-MM-DDTHH:MM:SS.mmmZ`، دقیقاً سه رقم کسر؛ گرامر بند ۸) است؛ به‌جز GENESIS همه‌ی ورودی‌ها `run_id` هم دارند. ورودی بدون `seq` صحیح یا `type` رشته‌ای `MALFORMED_ENTRY` و ورودی با `recorded_at_utc` نامعتبر `MALFORMED_TIMESTAMP` است.
4. `prev_raw` = ۳۲ بایت خام digest ورودی قبلی (از hex ۶۴ حرفی با `bytes.fromhex`). برای GENESIS، `prev_raw = bytes.fromhex(spec_sha256)`، یعنی زنجیره مستقیماً به hash فایل spec وصل می‌شود.
5. `entry_hash = SHA-256( prev_raw ‖ canon(payload) )`. اتصال بدون جداکننده است (prefix طول‌ثابت ۳۲ بایت، ابهام ندارد). مقدار ذخیره‌شده hex ۶۴ حرفی با حروف کوچک است.
6. هر خط فایل برابر `canon({"entry_hash": <hex>, "payload": {...}, "prev_hash": <hex>})` و سپس `\n` است. `prev_hash` همان hex ورودی قبلی (برای GENESIS، `spec_sha256`) است. **(r6)** envelope **دقیقاً** همین سه کلید را دارد (نه کمتر و نه بیشتر؛ کلید اضافه‌ی بی‌اثر بر hash هم نقض است)، `entry_hash` و `prev_hash` هر دو رشته‌ی hex ۶۴ نویسه‌ی حروف کوچک‌اند و `payload` یک شیء است؛ وگرنه `MALFORMED_ENVELOPE`. خطی که JSON معتبر نیست «parse error»، خطی که `canon` آن با متن خط یکی نیست (فاصله، ترتیب کلید، نویسه‌ی غیر ASCII بدون escape، کلید تکراری) «non-canonical» و خطی که مقدار غیرمجاز دارد (بند ۱) `MALFORMED_VALUE` گزارش می‌شود؛ KAT-15b و KAT-15c.
7. **ورودی‌های ناقص:** خط آخری که با `\n` تمام نشده یا parse نمی‌شود «ورودی» نیست. با یک `EVENT` از نوع `TORN_LINE` (شامل SHA-256 بایت‌های ناقص) ثبت می‌شود و فایل در خط جدید ادامه می‌یابد.
8. **گرامر زمان (r6).** هر مقدار زمانی journal (`recorded_at_utc`، `decision_time_utc`، `resolution_time_utc`، `ref_open_utc`، `t0_utc`، `collector_start_utc`، `S_utc`، `prefix_published_at_utc`، `manifest_published_at_utc`، `affected_from_utc`، `affected_to_utc`)، `published_at_utc` هر رکورد مقصد و هر زمان داخل فایل manifest باید **یک رشته‌ی کامل** با این گرامر باشد: `YYYY-MM-DDTHH:MM:SS(.mmm)?Z`. (الف) رقم‌ها فقط ASCII `0`..`9` هستند (رقم‌های عربی-هندی، فارسی و تمام‌عرض رد می‌شوند). (ب) تطابق روی **کل رشته** است: فاصله یا خط جدید در ابتدا یا انتها رد می‌شود (در regex باید `\Z` به‌کار رود، نه `$` که پیش از `\n` پایانی هم می‌خواند). (پ) کسر ثانیه یا نیست یا **دقیقاً سه رقم** است؛ `recorded_at_utc` همیشه کسر سه‌رقمی دارد (بند ۳). (ت) سال `2000..2999`، ماه `01..12`، روز در محدوده‌ی واقعی همان ماه با قاعده‌ی کبیسه‌ی میلادی (۲۹ فوریه فقط در سال کبیسه)، ساعت `00..23` (`24:00` مجاز نیست)، دقیقه `00..59`، ثانیه `00..59` (ثانیه‌ی کبیسه‌ی `60` مجاز نیست). (ث) مقدار نامعتبر **هرگز exception نمی‌دهد**: در خط journal `MALFORMED_TIMESTAMP`، در رکورد مقصد `MALFORMED_PUBLICATION` و در رکورد namespace مربوط به manifest `MALFORMED_MANIFEST_PUBLICATION` است (B.6 بند ۱، B.7 بند ۵ و ۹). `maintenance_time_utc` ساعت روز است و timestamp نیست. KAT-15a.

**KAT-4 (ساختگی):** `spec_sha256 = "00…00"` (۶۴ صفر)

| seq | `canon(payload)` | `entry_hash` |
|---|---|---|
| 0 | `{"journal_format":"FJ-JOURNAL-1","model_id":"KAT","recorded_at_utc":"2030-01-01T00:00:00.000Z","seq":0,"spec_sha256":"0000000000000000000000000000000000000000000000000000000000000000","type":"GENESIS"}` | `285406718b447a3df7e531606724c9f4641984b4eddcada20623dc806665a057` |
| 1 | `{"detail":"caf\u00e9 \"q\" \\ \n","event_type":"KAT","recorded_at_utc":"2030-01-01T00:00:01.000Z","run_id":"kat","seq":1,"type":"EVENT"}` | `649660f456787f12a43a5166c339717e4eb0ab46d421e8757b1ad5a35dcb0b9f` |
| 2 | `{"arr":["b","a"],"flag":true,"n":1893456000000,"nothing":null,"recorded_at_utc":"2030-01-01T00:00:02.000Z","run_id":"kat","seq":2,"type":"EVENT"}` | `3f57938701e5c711173d229d227c7eb8f67316d7f4d0716975f25e71b7eabb0d` |

(در ردیف ۱ مقدار منطقی `detail` عبارت است از `café` (چهار نویسه) + فاصله + `"q"` + فاصله + `\` + فاصله + خط جدید. در `canon` نویسه‌ی `é` (U+00E9) به صورت شش نویسه‌ی ASCII یعنی `\u00e9` درمی‌آید، نقل‌قول به `\"`، بک‌اسلش به `\\` و خط جدید به `\n`. ستون وسط جدول بایت‌های واقعی `canon` است و همان چیزی است که hash می‌شود.)

**KAT-15a (ساختگی، r6) — گرامر زمان (بند ۸).** هر ردیف یک مقدار JSON خام است؛ دو ستون نتیجه می‌گویند آیا آن مقدار در فیلدی که کسر ثانیه‌اش اختیاری است (مثل `published_at_utc` یا `S_utc`) و در `recorded_at_utc` (کسر سه‌رقمی الزامی) معتبر است یا نه. مقدار نامعتبر verdict می‌دهد، نه exception.

| مورد | مقدار JSON | کسر اختیاری | `recorded_at_utc` | توضیح |
|---|---|---|---|---|
| TS01 | `"2030-01-02T00:00:00.000Z"` | معتبر | معتبر | شکل کامل |
| TS02 | `"2030-01-02T00:00:00Z"` | معتبر | نامعتبر | بدون کسر ثانیه: فقط برای فیلدهایی که کسر اختیاری دارند |
| TS03 | `"2030-01-02T23:59:59.999Z"` | معتبر | معتبر | آخرین میلی‌ثانیه‌ی روز |
| TS04 | `"2032-02-29T12:00:00.000Z"` | معتبر | معتبر | ۲۹ فوریه‌ی سال کبیسه |
| TS05 | `"2030-02-29T12:00:00.000Z"` | نامعتبر | نامعتبر | ۲۰۳۰ کبیسه نیست |
| TS06 | `"2030-02-30T00:00:00.000Z"` | نامعتبر | نامعتبر | ۳۰ فوریه |
| TS07 | `"2030-04-31T00:00:00Z"` | نامعتبر | نامعتبر | آوریل ۳۰ روز دارد |
| TS08 | `"2030-13-01T00:00:00Z"` | نامعتبر | نامعتبر | ماه ۱۳ |
| TS09 | `"2030-00-10T00:00:00Z"` | نامعتبر | نامعتبر | ماه ۰۰ |
| TS10 | `"2030-01-00T00:00:00Z"` | نامعتبر | نامعتبر | روز ۰۰ |
| TS11 | `"2030-01-02T24:00:00Z"` | نامعتبر | نامعتبر | ساعت ۲۴ |
| TS12 | `"2030-01-02T23:60:00Z"` | نامعتبر | نامعتبر | دقیقه‌ی ۶۰ |
| TS13 | `"2030-06-30T23:59:60Z"` | نامعتبر | نامعتبر | ثانیه‌ی کبیسه (۶۰) مجاز نیست |
| TS14 | `"2030-01-02T00:00:00.1Z"` | نامعتبر | نامعتبر | کسر ثانیه با یک رقم |
| TS15 | `"2030-01-02T00:00:00.12Z"` | نامعتبر | نامعتبر | کسر ثانیه با دو رقم |
| TS16 | `"2030-01-02T00:00:00.1234Z"` | نامعتبر | نامعتبر | کسر ثانیه با چهار رقم |
| TS17 | `"2030-01-02T00:00:00.Z"` | نامعتبر | نامعتبر | نقطه‌ی بدون رقم |
| TS18 | `"2030-01-02T00:00:00.000Z\n"` | نامعتبر | نامعتبر | خط جدید در انتها (یک regex با `$` آن را می‌پذیرد) |
| TS19 | `" 2030-01-02T00:00:00.000Z"` | نامعتبر | نامعتبر | فاصله در ابتدا |
| TS20 | `"2030-01-02 00:00:00.000Z"` | نامعتبر | نامعتبر | فاصله به‌جای `T` |
| TS21 | `"2030-01-02t00:00:00.000z"` | نامعتبر | نامعتبر | حروف کوچک `t` و `z` |
| TS22 | `"2030-01-02T00:00:00.000+00:00"` | نامعتبر | نامعتبر | offset به‌جای `Z` |
| TS23 | `"2030-01-02T00:00:00.000"` | نامعتبر | نامعتبر | بدون `Z` |
| TS24 | `"2030-01-02T00:00Z"` | نامعتبر | نامعتبر | بدون ثانیه |
| TS25 | `"2030-1-2T0:0:0Z"` | نامعتبر | نامعتبر | بدون صفر پیشین |
| TS26 | `"\u0662\u0660\u0663\u0660-01-02T00:00:00.000Z"` | نامعتبر | نامعتبر | رقم‌های عربی-هندی (U+0662…) به‌جای ASCII |
| TS27 | `"\u06f2\u06f0\u06f3\u06f0-01-02T00:00:00.000Z"` | نامعتبر | نامعتبر | رقم‌های فارسی (U+06F2…) به‌جای ASCII |
| TS28 | `"\uff12\uff10\uff13\uff10-01-02T00:00:00.000Z"` | نامعتبر | نامعتبر | رقم‌های تمام‌عرض (U+FF12…) به‌جای ASCII |
| TS29 | `"1999-12-31T23:59:59.999Z"` | نامعتبر | نامعتبر | سال کمتر از ۲۰۰۰ |
| TS30 | `"3000-01-01T00:00:00.000Z"` | نامعتبر | نامعتبر | سال بیشتر از ۲۹۹۹ |
| TS31 | `"0000-01-01T00:00:00.000Z"` | نامعتبر | نامعتبر | سال ۰۰۰۰ |
| TS32 | `"2000-01-01T00:00:00.000Z"` | معتبر | معتبر | حد پایین سال |
| TS33 | `"2999-12-31T23:59:59.999Z"` | معتبر | معتبر | حد بالای سال |
| TS34 | `""` | نامعتبر | نامعتبر | رشته‌ی تهی |
| TS35 | `null` | نامعتبر | نامعتبر | `null` رشته نیست |
| TS36 | `20300102` | نامعتبر | نامعتبر | عدد صحیح رشته نیست |
| TS37 | `"2030-01-02T00:00:00,000Z"` | نامعتبر | نامعتبر | ویرگول به‌جای نقطه |
| TS38 | `"20300102T000000.000Z"` | نامعتبر | نامعتبر | شکل «پایه» ISO بدون خط تیره و دونقطه |

**KAT-15b (ساختگی، r6) — منفی‌های envelope و خط (بند ۶).** هر ردیف **یک** ویرایش روی یک خط سالم journal است (بقیه‌ی خط‌ها دست‌نخورده‌اند). ستون آخر کلمه‌ی verdict است؛ «non-canonical» و «parse error» عبارت‌های ثابت verifier هستند.

| مورد | ویرایش | verdict |
|---|---|---|
| E01 | کلید اضافه‌ی `x` در envelope (چهار کلید) | `MALFORMED_ENVELOPE` |
| E02 | کلید `prev_hash` نیست | `MALFORMED_ENVELOPE` |
| E03 | کلید `entry_hash` نیست | `MALFORMED_ENVELOPE` |
| E04 | کلید `payload` نیست | `MALFORMED_ENVELOPE` |
| E05 | `payload` آرایه است | `MALFORMED_ENVELOPE` |
| E06 | `payload` برابر `null` است | `MALFORMED_ENVELOPE` |
| E07 | `entry_hash` با حروف بزرگ hex | `MALFORMED_ENVELOPE` |
| E08 | `entry_hash` با ۶۳ نویسه | `MALFORMED_ENVELOPE` |
| E09 | `prev_hash` عدد صحیح `0` است | `MALFORMED_ENVELOPE` |
| E10 | کل خط یک آرایه‌ی JSON است (`[]`) | `MALFORMED_ENVELOPE` |
| E11 | کل خط یک رشته‌ی JSON است | `MALFORMED_ENVELOPE` |
| E12 | کل خط `null` است | `MALFORMED_ENVELOPE` |
| E13 | خط با فاصله‌ی انتهایی (بعد از شیء) | `non-canonical` |
| E14 | خط با فاصله بعد از `:` و `,` (JSON خوش‌چاپ) | `non-canonical` |
| E15 | کلید تکراری `entry_hash` در خط (parser آخری را برمی‌دارد) | `non-canonical` |
| E16 | خط تهی | `parse error` |
| E17 | نویسه‌ی غیر ASCII بدون escape در payload | `non-canonical` |
| E18 | کلیدهای envelope به ترتیب مرتب نیستند | `non-canonical` |

**KAT-15c (ساختگی، r6) — منفی‌های مقدار (بند ۱).** هر ردیف یک `EVENT` سالم است که کلید `n` در payload آن این literal JSON خام را دارد (خط پس از ساخت دوباره canonical نمی‌شود، تا literal دقیقاً همان‌طور که هست دیده شود). «پذیرفته» یعنی `MALFORMED_VALUE` نمی‌آید.

| مورد | literal | verdict | توضیح |
|---|---|---|---|
| VL01 | `1.5` | `MALFORMED_VALUE` | عدد اعشاری |
| VL02 | `1.0` | `MALFORMED_VALUE` | عدد صحیح‌نما با نقطه (`1.0`) هم اعشاری است |
| VL03 | `1e2` | `MALFORMED_VALUE` | نماد علمی |
| VL04 | `9007199254740993` | `MALFORMED_VALUE` | ۲^۵۳ + ۱ (بزرگ‌تر از حد) |
| VL05 | `-9007199254740993` | `MALFORMED_VALUE` | −(۲^۵۳ + ۱) |
| VL06 | `NaN` | `MALFORMED_VALUE` | `NaN` |
| VL07 | `Infinity` | `MALFORMED_VALUE` | `Infinity` |
| VL08 | `[1,[2,3.5]]` | `MALFORMED_VALUE` | عدد اعشاری در آرایه‌ی تودرتو |
| VL09 | `{"a":{"b":0.1}}` | `MALFORMED_VALUE` | عدد اعشاری در شیء تودرتو |
| VL10 | `9007199254740992` | پذیرفته | ۲^۵۳ دقیقاً مجاز است (مقدار پذیرفته می‌شود؛ خطای دیگری از این مقدار نمی‌آید) |
| VL11 | `-9007199254740992` | پذیرفته | −۲^۵۳ دقیقاً مجاز است |

**B.3 انواع ورودی (همه‌ی شواهد در journal):**

| `type` | فیلدهای اضافه بر فیلدهای مشترک | نقش |
|---|---|---|
| `GENESIS` | `journal_format` (`FJ-JOURNAL-1`)، `spec_filename`، `spec_revision`، `spec_sha256`، `model_id`، `weights` (سه رشته‌ی A.5)، `lock_reference` | قفل spec |
| `CONFIG` | `feed_id`، `feed_url` (آدرس کامل endpoint، C.2)، `stream_name`، `realtime_latency_limit_ms`، `logging_offset_s`، `logging_deadline_s`، `clock_offset_limit_ms`، `clock_policy` (شیء با **دقیقاً** پنج کلید: `ntp_sources` (فهرست **مرتب** دست‌کم دو رشته‌ی متمایز؛ اولی منبع اصلی است)، `clock_poll_s`، `clock_sample_max_age_ms`، `clock_step_limit_ms`، `clock_source_spread_ms`؛ ثابت‌های C.2)، `rotation_policy` (شیء: `max_connection_age_s`، `rotation_start_age_s`، `rotation_attempt_timeout_s`، `rotation_retry_s`، `boundary_guard_s`، `reconnect_backoff_s`، `silence_timeout_s`؛ C.16)، `outcome_first_check_s`، `outcome_finalization_s`، `audit_tolerance`، `maintenance_time_utc`، `checkpoint_publication_target` (**شیء** با دقیقاً ده کلید: `name`، `operator`، `operator_independent_of_writer`، `time_source`، `receipt_kind`، `receipt_verification`، `receipt_verification_material`، `read_client`، `namespaces`، `seq_monotonic_enforced_by_target`؛ قرارداد B.7 بند ۴)، `runtime_manifest` (زبان، نسخه‌ها، lock file، `feed_url`)، `code_sha256` (tree hash فایل‌های کد، **پیش از** نوشتن همین ورودی محاسبه‌شده؛ C.1، KAT-14) | هویت feed، ساعت، اتصال و پیکربندی |
| `T0_DECLARATION` | `t0_utc`، `config_entry_hash`، `code_sha256`، `spec_sha256`، `collector_start_utc` | T0 |
| `CANDLE` | `open_time_ms`، `o`، `h`، `l`، `c`، `v`، `taker_buy_base` (رشته‌ی دریافتی)، `feed_id`، `feed_url` (آدرس اتصال فعال)، `connection_id` (عدد صحیح؛ اتصالی که پیام از آن آمد، C.16)، `event_time_ms`، `ingested_ms` (لحظه‌ی دریافت، ms، ساعت محلی)، `clock_status`، `clock_offset_ms`، `clock_sample_age_ms`، `clock_step_ms` (رکورد ساعت در لحظه‌ی دریافت، C.2)، `latency_ms` (= `ingested_ms − clock_offset_ms − (open_time_ms + 300000)`)، `is_final` (true)، **(r6)** `raw_message` (متن خام دریافتی، حداکثر ۴۰۹۶ نویسه) و `raw_message_sha256` (SHA-256 بایت‌های UTF-8 همان متن) | هر کندل نهایی real-time که از `validate_kline` (C.2) گذشته؛ اولین دریافت معتبر **با ساعت معتبر** |
| `CANDLE_ANOMALY` | `anomaly_type` (`DUPLICATE_IDENTICAL` \| `DUPLICATE_CONFLICT` \| `NON_REALTIME` \| `MALFORMED` \| `FEED_MISMATCH` \| `CLOCK_INVALID`)، `open_time_ms` (یا `null` اگر قابل‌استخراج نبود)، `feed_url`، `connection_id`، `ingested_ms`، رکورد ساعت (`clock_status`، `clock_offset_ms`، `clock_sample_age_ms`، `clock_step_ms`)، `latency_ms` (فقط اگر ساعت معتبر و `open_time_ms` موجود باشد، وگرنه `null`)؛ برای `DUPLICATE_*`، `NON_REALTIME` و `CLOCK_INVALID`: رشته‌های دریافتی `o`، `h`، `l`، `c`، `v`؛ برای `DUPLICATE_*`: `first_candle_seq`؛ برای `CLOCK_INVALID`: `clock_reasons` (آرایه‌ی CK01..CK04)؛ برای `MALFORMED`: `malformed_reasons` (آرایه‌ی V01..V08)؛ برای `MALFORMED` و `FEED_MISMATCH`: `connection_url`؛ **(r6)** برای **همه‌ی** انواع: `raw_message` (حداکثر ۴۰۹۶ نویسه) و `raw_message_sha256` (SHA-256 بایت‌های UTF-8 **متن کامل** دریافتی)، و `raw_truncated` (`true` فقط برای `MALFORMED [V01]` با متن بلندتر از ۴۰۹۶ نویسه که فقط ۴۰۹۶ نویسه‌ی اولش ذخیره می‌شود؛ وگرنه `false` یا غایب) | ناهنجاری کندل؛ هرگز مقدار اول را بازنویسی نمی‌کند و هرگز `CANDLE` نمی‌سازد |
| `DECISION` | `decision_id`، `decision_time_utc`، `origin` (`SCHEDULED` \| `GAP_FILL`)، `model_id`، `target_def_version`، `spec_sha256`، `code_sha256`، `config_ref` (hash ورودی `CONFIG`)، `ref_open_utc`، `decision_validity` (`ACCEPTED` \| `REJECTED`)، `reject_code`، `reject_reasons` (آرایه)، `feature_bar_count` (عدد صحیح ۰ تا ۲۸۸ یا `null`)، `feature_entries_digest`، رکورد ساعت **در لحظه‌ی نوشتن تصمیم** (`clock_status`، `clock_offset_ms`، `clock_sample_age_ms`، `clock_step_ms`؛ برای `GAP_FILL` همه `null`)، `C_ref`، `range12`، `range288`، `a`، `b`، `z`، `p_raw` | تصمیم؛ یک ورودی برای هر نقطه‌ی شبکه |
| `OUTCOME` | `decision_seq`، `decision_entry_hash`، `resolution_time_utc`، `outcome_status`، `outcome_reasons` (آرایه)، `fwd_bar_count` (۰ تا ۹۶)، `fwd_entries_digest`، `c_ref_used`، `M96`، `k_star`، `Y` | نتیجه‌ی نهایی؛ فقط برای تصمیم ACCEPTED و حداکثر یکی برای هر `decision_seq` |
| `AUDIT` | `decision_seq`، `decision_entry_hash`، `audit_status` (`MATCH` \| `MISMATCH` \| `NOT_COMPUTABLE`)، `p_audit`، `abs_diff`، `tolerance`، `auditor_code_sha256` | بازمحاسبه‌ی canonical |
| `ADJUDICATION` | `decision_seq`، `decision_entry_hash`، `outcome_seq`، `outcome_entry_hash`، `audit_seq`، `audit_entry_hash`، `eligibility` (`ELIGIBLE` \| `INELIGIBLE`)، `ineligibility_reasons` (آرایه)، `adjudication_rule` (`FJ-ADJ-1`) | واجد شرایط بودن جفت پیش‌بینی–outcome |
| `EVENT` | `event_type`، `detail`، `affected_from_utc`، `affected_to_utc` | restart، outage، `COLLECTOR_START` (`collector_start_utc`، `code_tree_sha256`، `startup_url_check`؛ C.1)، `FEED_CONNECT` (`connection_id`، `role` = `ACTIVE` \| `STANDBY`، `connection_url`، `http_status`)، `FEED_DISCONNECT` (`connection_id`، `reason`، `connection_age_s`)، `FEED_ROTATION` (`phase`، `old_connection_id`، `new_connection_id`، `old_age_s`، `reason`)، `FEED_STALL` (`connection_id`، `silent_ms`) (C.16)، `CLOCK_STATE` (گذار بین `clock_ok` و نامعتبر، اطلاعاتی؛ C.2)، `ANALYSIS_MANIFEST` (`analysis_prefix_seq`، `analysis_prefix_entry_hash`، `prefix_published_at_utc`، `prefix_receipt`، `S_utc`، `analysis_code_sha256`، `gate_spec_sha256`، `benchmark_spec_sha256`، `analysis_mode`، `manifest_sha256`، `manifest_published_at_utc`، `manifest_receipt`، `t0_utc`؛ C.17)، `FINALIZER_ERROR` (`decision_seq`)، `CHECKPOINT_PUBLISH_FAILED`، `CHECKPOINT_SUPERSEDED` (`checkpoint_seq`، `superseded_by_seq`؛ B.7 بند ۲ و ۵)، `CHECKPOINT_E2E_TEST` (`result`، `published_seq`)، `SPEC_REGISTRATION` (`spec_kind` ∈ {`GATE`، `BENCHMARK`، `ANALYSIS_CODE`}، `spec_sha256`، `spec_name`؛ C.17)، تغییر config UI، amendment، `TORN_LINE`، `DEVIATION` |
| `CHECKPOINT` | `head_seq` و `head_entry_hash` (هر دو به ورودی **پیش** از خودِ `CHECKPOINT` اشاره می‌کنند، B.7)، `human_head_hash`، `previous_publication` (شیء `{seq, entry_hash, receipt}` یا `null`؛ `receipt` را **مقصد** می‌دهد نه writer، B.7 بند ۳ و ۵)، `published_to` | سر زنجیره (روزانه)؛ anchoring خارجی در B.7 |

- `feature_entries_digest = SHA-256( concat(ورودی hash خام ۳۲ بایتی هر ورودی CANDLE ۲۸۸ کندل، به ترتیب صعودی open) )`؛ `fwd_entries_digest` همین کار برای ۹۶ کندل forward. این‌ها دقیقاً مشخص می‌کنند کدام ورودی‌های journal مبنای محاسبه بوده‌اند. برای تصمیم REJECTED یا GAP_FILL مقدار `null` است.
- `decision_id = "MO2-8h-v1|" + decision_time_utc`. `target_def_version = "Y96_LN1.02_CC_RATIO_v1"`.
- هر `DECISION` دقیقاً یک بار برای هر `decision_time_utc` وجود دارد. ورودی دوم با همان کلید «تکراری» است: اولی معتبر است، دومی نادیده گرفته می‌شود و `EVENT` از نوع `DEVIATION` لازم دارد.
- برای هر `decision_seq` حداکثر یک `OUTCOME`، یک `AUDIT` و یک `ADJUDICATION` وجود دارد؛ ورودی دوم با همان کلید نامعتبر است: اولی معتبر می‌ماند، دومی نادیده گرفته می‌شود و `EVENT` از نوع `DEVIATION` لازم دارد (C.6).

- **کندل قابل‌استفاده (`usable`) — اصلاح ۱ (r4):** یک ورودی `CANDLE` فقط وقتی در feature، outcome و audit به‌کار می‌رود که از **فیلدهای ذخیره‌شده‌ی خودش** بتوان ۵ شرط را بازتولید کرد: (الف) رکورد ساعتش `clock_ok` است (هیچ‌کدام از CK01..CK04 برقرار نیست)؛ (ب) `latency_ms = ingested_ms − clock_offset_ms − (open_time_ms + 300000)`؛ (پ) `−5000 ≤ latency_ms ≤ 60000`؛ (ت) `feed_url` برابر `CONFIG.feed_url` است؛ (ث) `is_final = true`. `CANDLE`ی که یکی از این‌ها را نداشته باشد نقض است (`DEVIATION` از نوع `CANDLE_NONCONFORMING`، B.6 بند ۱۱) و **در همه‌ی محاسبه‌ها «موجود نیست» حساب می‌شود**؛ جای «اولین دریافت» را هم اشغال نمی‌کند (اولین `CANDLE` قابل‌استفاده حاکم است). verifier هیچ‌وقت `CANDLE` غیرقابل‌استفاده را مبنای feature یا outcome قرار نمی‌دهد.
- **محدودیت صریح شاهد ساعت:** رکورد ساعت هر ورودی را collector از NTP و ساعت محلی خودش ثبت می‌کند. verifier می‌تواند **سازگاری درونی** را بازمحاسبه کند (فرمول latency، دلیل‌های CK، R06، R08، NON_REALTIME) ولی نمی‌تواند خودِ offset را بعد از واقعه با مرجع مستقل بسنجد؛ دقت آن به منابع NTP وابسته است و در بند باقی‌مانده‌ها گزارش می‌شود.
- **شاهد کندل (r6):** هر ورودی `CANDLE` و `CANDLE_ANOMALY` متن خام دریافتی (`raw_message`) و SHA-256 بایت‌های UTF-8 **کل** آن متن (`raw_message_sha256`) را نگه می‌دارد؛ حد ذخیره ۴۰۹۶ نویسه [P] است و متن بلندتر `MALFORMED [V01]` می‌شود (C.2). verifier مستقل از collector `validate_kline` (C.2) را روی همین متن، `connection_url` (برای `CANDLE`: `feed_url`)، `ingested_ms` و رکورد ساعت ذخیره‌شده دوباره اجرا می‌کند و باید همان نوع و همان فیلدهای تجزیه‌شده را بدهد (B.6 بند ۱۱، KAT-16). به این ترتیب `k.T` و `k.x`، `E`، V01..V08، `FEED_MISMATCH` و مقدارهای `o`..`V` هر ورودی بدون اعتماد به گزارش collector قابل بازبینی‌اند. **محدودیت صریح:** متن خام را خود collector می‌نویسد؛ این شاهد ثابت نمی‌کند Binance آن را فرستاده است، فقط نشان می‌دهد هر ورودی با متن ذخیره‌شده‌ی خودش سازگار است.

**B.4 `human_journal.jsonl` (جدا، شرط ۱۴):** همان فرمت B.2. ورودی GENESIS آن شامل `main_genesis_entry_hash` است. تنها نوع ورودی: `HUMAN_DECISION` با `hd_id`، `as_of_utc`، `actor`، `ref_decision_id` (اختیاری)، `action` (`none` \| `executed` \| `skipped` \| `other`)، `note`. سر این زنجیره (`human_head_hash`) در `CHECKPOINT` های journal اصلی می‌آید، پس دست‌کاری‌اش آشکار می‌شود، ولی محتوایش هرگز به journal اصلی نمی‌آید و در هیچ متریکی وارد نمی‌شود.

**B.5 نماهای مشتق‌شده (بازسازی قطعی از journal):**
- `candles`، `decisions`، `outcomes`، `audits`، `adjudications`: هر ردیف تصویر یک ورودی journal است؛ فیلدها عیناً از payload کپی می‌شوند و دو ستون `journal_seq`، `journal_entry_hash` دارند.
- `journal_view` (یک ردیف برای هر `DECISION`): `decision_time_utc`، `p_raw`، `target_def_version`، `Y`، `resolution_time_utc`، `eligibility`، `spec_sha256`، `code_sha256`، `config_ref`، `data` (`feature_entries_digest`، `fwd_entries_digest`) و hash های سه ورودی منبع. این نما حداقل‌های **شرط ۷** (timestamp، `p_raw`، نسخه‌ی target، outcome، زمان resolution، نسخه‌ی داده و کد) را در یک ردیف نشان می‌دهد.
- `coverage` (روزانه و هفتگی) و `pending` (تصمیم‌های `PENDING_OUTCOME`، `PENDING_AUDIT`، `PENDING_ADJUDICATION`): از `decisions`، `outcomes`، `audits` و `adjudications` محاسبه می‌شوند.
- هیچ نمای مشتقی نباید «منبع حقیقت» باشد؛ در تعارض، journal حاکم است.

**B.6 Verifier (رویه‌ی مرجع، قطعی):** (۱) هر خط را parse کن (**r6**): envelope دقیقاً سه کلید `entry_hash`، `payload`، `prev_hash` است، دو hash ۶۴ نویسه‌ی hex حروف کوچک و `payload` شیء است (`MALFORMED_ENVELOPE`)؛ مقدارها فقط انواع B.2 بند ۱ هستند (`MALFORMED_VALUE`)؛ `seq` عدد صحیح و `type` رشته است (`MALFORMED_ENTRY`)؛ همه‌ی زمان‌ها با گرامر B.2 بند ۸ می‌خوانند (`MALFORMED_TIMESTAMP`)؛ و `canon` خط با خود خط برابر است («non-canonical»)؛ خطی که parse نمی‌شود «parse error» است. **verifier تام است:** هیچ ورودی‌ای آن را با exception نمی‌اندازد؛ هر چیزی که تفسیر نشود یک verdict نام‌دار می‌گیرد (برای ورودی ناقابل‌تفسیر `MALFORMED_ENTRY`) و آخرین سد verdict `VERIFIER_EXCEPTION` است که در هیچ اجرای قراردادی نباید ظاهر شود (harness ظاهر شدن آن را شکست می‌گیرد)؛ (۲) `seq` از ۰ بدون شکاف بالا می‌رود؛ (۳) `prev_hash` هر ورودی برابر `entry_hash` قبلی و `entry_hash` بازمحاسبه‌شده برابر ذخیره‌شده است؛ (۴) `prev_hash` ورودی GENESIS برابر SHA-256 فایل spec قفل‌شده است؛ (۵) هر `OUTCOME`/`AUDIT`/`ADJUDICATION` به یک `DECISION` موجود با `(seq, entry_hash)` صحیح ارجاع می‌دهد و ارجاع‌ها فقط به ورودی‌های قبلی هستند؛ (۶) ناوردایی‌ها: `p_raw ≠ null ⇔ decision_validity = ACCEPTED`، `Y ≠ null ⇔ outcome_status = RESOLVED`، هر `decision_time_utc` یکتا و روی شبکه؛ (۷) برای هر `DECISION` ACCEPTED مقدارهای `C_ref`، `range12`، `range288`، `a`، `b`، `z`، `p_raw` و `feature_entries_digest` از ورودی‌های `CANDLE` journal **با `seq` کوچک‌تر از `seq` همان `DECISION`** بازمحاسبه و با مقدار ذخیره‌شده مقایسه می‌شوند؛ دلیل‌های داده‌ای `R01`، `R02`، `R06` نیز از همان ورودی‌ها (با «کندل قابل‌استفاده» B.3 و با `CANDLE_ANOMALY(CLOCK_INVALID)` در `R06`) و دلیل `R08` از رکورد ساعتِ ذخیره‌شده در خودِ `DECISION` (CK01..CK04، C.2) بازمحاسبه می‌شوند: برای ACCEPTED باید تهی باشند و برای `DECISION` رد‌شده‌ی SCHEDULED باید دقیقاً برابر زیرمجموعه‌ی داده‌ای `reject_reasons` باشند (`R02` فقط وقتی مجاز است که `DUPLICATE_CONFLICT` با `seq` کوچک‌تر از `seq` تصمیم وجود داشته باشد)؛ برای هر `OUTCOME` با وضعیت RESOLVED مقدارهای `M96`، `k_star`، `Y`، `c_ref_used` و `fwd_entries_digest` هم به همین شکل از ورودی‌های با `seq` کوچک‌تر از `seq` همان `OUTCOME`؛ (۸) هر `ADJUDICATION` با بازمحاسبه‌ی C.7 (FJ-ADJ-1 روی ورودی‌های با `seq` کوچک‌تر از `seq` خودش) برابر است؛ برای هر `decision_seq` حداکثر یک `OUTCOME`، `AUDIT` و `ADJUDICATION` وجود دارد؛ هیچ `ADJUDICATION` برای تصمیم ACCEPTED بدون `OUTCOME` نهایی یا بدون `AUDIT` نوشته نشده؛ و فهرست تصمیم‌های در انتظار (`PENDING_OUTCOME`، `PENDING_AUDIT`، `PENDING_ADJUDICATION` و آن‌هایی که از `R + 86400 s` گذشته‌اند) جدا گزارش می‌شود، نه به‌صورت `E02` یا `E04`؛ (۹) نماهای مشتق بازسازی و بایت‌به‌بایت مقایسه می‌شوند؛ (۱۰) هر `CHECKPOINT` و رکوردهای منتشرشده در `checkpoint_publication_target` طبق B.7 بند ۵ بررسی می‌شوند (شکل هفت‌فیلدی رکورد، `receipt` و `published_at_utc` تعیین‌شده توسط مقصد، یکتایی و ترتیب آن‌ها، ترتیب پذیرش `seq` در مقصد، `previous_publication`، و سیاست `CHECKPOINT_SUPERSEDED`)؛ (۱۱) **ناوردایی‌های دریافت و ساعت (r4):** برای هر `CANDLE` و `CANDLE_ANOMALY`: `latency_ms` برابر فرمول B.3 است وقتی رکورد ساعت `clock_ok` و `open_time_ms` موجود است، و `null` است وگرنه؛ `ingested_ms ≤ recorded_at_utc + 250 ms` (دریافت پیش از append)؛ هر `CANDLE` باید «قابل‌استفاده» باشد وگرنه `DEVIATION(CANDLE_NONCONFORMING)`؛ `CLOCK_INVALID` فقط وقتی مجاز است که `clock_reasons` با بازمحاسبه از رکورد ساعت ذخیره‌شده برابر و ناتهی باشد؛ `NON_REALTIME` فقط وقتی مجاز است که ساعت معتبر و `latency_ms > 60000` باشد؛ **(r6، شاهد)** هر `CANDLE` و `CANDLE_ANOMALY` باید `raw_message` (رشته) و `raw_message_sha256` (hex ۶۴) داشته باشد (`WITNESS_MISSING`)؛ `raw_message_sha256` برابر SHA-256 بایت‌های UTF-8 متن ذخیره‌شده است؛ و اجرای دوباره‌ی `validate_kline` (C.2) روی `raw_message`، `connection_url` (برای `CANDLE`: `feed_url`)، `ingested_ms` و رکورد ساعت ذخیره‌شده، با جدول «اولین `CANDLE` قابل‌استفاده» ساخته‌شده از ورودی‌های **قبلی**، باید همان نوع ورودی (`CANDLE` یا همان `anomaly_type`)، همان `open_time_ms` و همان `malformed_reasons` یا `clock_reasons` را بدهد، و فیلدهای تجزیه‌شده‌ی ورودی (`o`، `h`، `l`، `c`، `v`، `taker_buy_base`، `event_time_ms`، `is_final`، `feed_id`، و برای `DUPLICATE_*` `first_candle_seq`) با پیام خام برابر باشند (`WITNESS_MISMATCH`)؛ پیام با `k.T ≠ k.t + 299999`، `k.x = false`، `connection_url` نادرست یا متنی بلندتر از ۴۰۹۶ نویسه پس نمی‌تواند `CANDLE` شده باشد. `raw_truncated = true` فقط برای `MALFORMED [V01]` با دقیقاً ۴۰۹۶ نویسه‌ی ذخیره‌شده مجاز است؛ در آن حالت `raw_message_sha256` hash متن کامل است و verifier نمی‌تواند آن را بازمحاسبه کند چون متن کامل ذخیره نشده (KAT-16)؛ (۱۲) **اتصال‌ها (C.16):** قواعد verifier چرخش و اتصال (پیام از اتصال ناشناخته یا پیش از باز شدنش یا پس از `FEED_DISCONNECT` آن، اتصال با URL غلط، سن اتصال بیش از `max_connection_age_s + 60 s`، چرخش برنامه‌ریزی‌شده بدون READY یا CUTOVER یا بدون اثبات تحویل داده از جانشین یا داخل گارد مرزی، CUTOVER با `A_LOST` بدون READY)؛ (۱۳) **manifest تحلیل (C.17، r6):** برای هر `EVENT(ANALYSIS_MANIFEST)`: `S_utc ≤ recorded_at_utc` خودِ `EVENT`؛ `analysis_prefix_seq` کوچک‌تر از `seq` خودِ `EVENT` است و به یک `CHECKPOINT` با `analysis_prefix_entry_hash` برابر اشاره می‌کند؛ رکورد هفت‌فیلدی همان `CHECKPOINT` در مقصد وجود دارد و `entry_hash`، `published_at_utc` و `receipt` آن با مقدارهای manifest برابر است؛ `published_at_utc ≤ S`؛ و آن `CHECKPOINT` **آخرین** `CHECKPOINT` با رکورد انتشار و `published_at_utc ≤ S` است؛ رکوردهای مقصد خودشان طبق B.7 بند ۵ سالم‌اند. **(r6)** `analysis_code_sha256` (هرگز `null`)، `gate_spec_sha256` و `benchmark_spec_sha256` (`null` فقط در حالت `DESCRIPTIVE`) هر کدام ۶۴ نویسه‌ی hex حروف کوچک‌اند (`HASH_FORMAT`)؛ در حالت `OFFICIAL` هر سه غیر `null` اند (`OFFICIAL_NEEDS_HASH`)؛ و هر سه برابر `spec_sha256` **آخرین** `EVENT(SPEC_REGISTRATION)` از نوع متناظر (`ANALYSIS_CODE`، `GATE`، `BENCHMARK`) با `seq ≤ P` هستند (`HASH_NOT_REGISTERED`)؛ `SPEC_REGISTRATION` بدشکل `SPEC_REGISTRATION_MALFORMED` است. رکوردی با همین `manifest_sha256` در namespace `manifests` مقصد وجود دارد (`MANIFEST_NOT_PUBLISHED`)، `manifest_published_at_utc` و `manifest_receipt` در `EVENT` با آن رکورد برابرند (`MANIFEST_RECORD_MISMATCH`)، `S_utc` دیرتر از زمان انتشار manifest نیست (`S_AFTER_MANIFEST_PUBLICATION`)، و `EVENT` بیش از ۵ ثانیه پیش از زمان انتشار manifest در مقصد ثبت نشده است (`MANIFEST_EVENT_BEFORE_PUBLICATION`)؛ فیلد بدشکل در `EVENT` (مثل `analysis_mode` نامعتبر) `MANIFEST_EVENT_MALFORMED` است؛ رکوردهای namespace `manifests` طبق B.7 بند ۹ سالم‌اند. اگر فایل manifest و فایل‌های کد تحلیل در اختیار verifier باشند، فایل با `EVENT` و ثابت‌ها برابر است و tree hash کد (KAT-14) با `analysis_code_sha256` می‌خواند (`CODE_HASH_MISMATCH`)؛ وگرنه گزارش verifier `NOT_CHECKED` می‌گوید و آن را «پاس» نمی‌شمارد. `recorded_at_utc` نویسنده در انتخاب prefix نقشی ندارد. (۱۴) **ترتیب پیش از T0 (C.1):** ترتیب یکتای ورودی‌های GENESIS، CONFIG، `CHECKPOINT` واقعی و `CHECKPOINT_E2E_TEST`، `COLLECTOR_START`، feed، اولین چرخش برنامه‌ریزی‌شده‌ی کامل، `T0_DECLARATION`، اولین `DECISION`، و برابری hash کد، CONFIG و spec در همه‌ی آن‌ها. هر ناسازگاری یک `DEVIATION` است و ارزیابی از بازمحاسبه‌ی verifier استفاده می‌کند، نه از نمای مشتق. (۱۵) **CONFIG (r6):** تنها ورودی `CONFIG` یک `checkpoint_publication_target` با قرارداد ده‌کلیدی B.7 بند ۴ و یک `clock_policy` دقیقاً پنج‌کلیدی با ثابت‌های C.2 دارد (`CONFIG_INVALID`).

**KAT-16 (ساختگی، r6) — شاهد کندل (بند ۱۱).** journal سالمی با `CANDLE` های کامل (پیام پایه‌ی M00 از KAT-8)؛ هر ردیف **یک** ویرایش روی یک ورودی است و زنجیره‌ی hash پس از آن دوباره محاسبه می‌شود، تا فقط قاعده‌ی معنایی بند ۱۱ بگیرد. ستون آخر verdict است («تمیز» یعنی verifier چیزی گزارش نمی‌کند). W16 و W18 روی یک journal ساختگی جدا (پیام بلندتر از ۴۰۹۶ نویسه) هستند.

| مورد | ویرایش یا حالت | verdict |
|---|---|---|
| W01 | `CANDLE` بدون `raw_message` | `WITNESS_MISSING` |
| W02 | `CANDLE` بدون `raw_message_sha256` | `WITNESS_MISSING` |
| W03 | `raw_message_sha256` برابر SHA-256 (UTF-8) متن `raw_message` نیست | `WITNESS_MISMATCH` |
| W04 | `raw_message` دست‌کاری شد (قیمت بسته شدن) و `sha256` هم‌خوان شد؛ فیلدهای `CANDLE` همان قبلی‌اند | `WITNESS_MISMATCH` |
| W05 | فیلد `c` در `CANDLE` دست‌کاری شد، `raw_message` سالم است | `WITNESS_MISMATCH` |
| W06 | `open_time_ms` در `CANDLE` با `k.t` پیام خام فرق دارد | `WITNESS_MISMATCH` |
| W07 | `raw_message` دارای `k.T ≠ k.t + 299999` است ولی ورودی `CANDLE` ثبت شده (باید `MALFORMED [V08]` می‌شد) | `WITNESS_MISMATCH` |
| W08 | `raw_message` دارای `k.x = false` است ولی ورودی `CANDLE` ثبت شده (باید دور ریخته می‌شد) | `WITNESS_MISMATCH` |
| W09 | `feed_url` ورودی `CANDLE` برابر آدرس قفل‌شده نیست (پیام باید `FEED_MISMATCH` می‌شد) | `WITNESS_MISMATCH` |
| W10 | `event_time_ms` با `E` پیام خام فرق دارد | `WITNESS_MISMATCH` |
| W11 | `DUPLICATE_IDENTICAL` که پیام خامش با اولین `CANDLE` آن کندل یکی نیست (در واقع تعارض است) | `WITNESS_MISMATCH` |
| W12 | `raw_truncated = true` روی یک `CANDLE` | `WITNESS_MISMATCH` |
| W13 | `raw_message` با ۴۰۹۷ نویسه به‌طور کامل ذخیره شده و ورودی `CANDLE` است (طبق V01 باید `MALFORMED` می‌شد) | `WITNESS_MISMATCH` |
| W14 | `CANDLE` با پیام خامی که نویسه‌ی غیر ASCII (`é`) دارد؛ SHA-256 روی بایت‌های UTF-8 است | تمیز |
| W15 | `CANDLE` با پیام خامی که دقیقاً ۴۰۹۶ نویسه است | تمیز |
| W16 | `MALFORMED [V01]` برای پیامی بلندتر از ۴۰۹۶ نویسه: `raw_truncated = true`، دقیقاً ۴۰۹۶ نویسه ذخیره، SHA-256 کل متن | تمیز |
| W17 | `DUPLICATE_IDENTICAL` که `first_candle_seq` آن `seq` اولین `CANDLE` قابل‌استفاده‌ی همان کندل نیست (یکی بیشتر) | `WITNESS_MISMATCH` |
| W18 | `MALFORMED [V01]` با `raw_truncated = true` که متن ذخیره‌شده‌اش دقیقاً ۴۰۹۶ نویسه نیست (فقط ۱۰۰ نویسه) | `WITNESS_MISMATCH` |

**B.7 Checkpoint و anchoring خارجی (اصلاح ۵ در r3؛ بندهای ۲، ۳، ۴، ۵، ۸ و KAT-10b اصلاح r5؛ بندهای ۲، ۴، ۵، ۶، ۹ و KAT-10c اصلاح r6):**
1. **معنای فیلدها.** `CHECKPOINT` با `seq = c` شامل `head_seq = c − 1` و `head_entry_hash = entry_hash(ورودی c − 1)` است؛ یعنی هر دو به **سر journal دقیقاً پیش از خودِ CHECKPOINT** اشاره می‌کنند. یک ورودی نمی‌تواند hash خودش را داشته باشد؛ hash خودِ `CHECKPOINT` (`H_c`) فقط بعد از append شدن معلوم می‌شود و در رکورد انتشار می‌آید.
2. **ترتیب و سیاست انتشار (r6)** (مرحله‌ی ۵ و ۶ هر maintenance، C.7): (الف) `CHECKPOINT` شماره‌ی `c` به journal append و fsync می‌شود؛ (ب) `H_c` از همان ورودی خوانده می‌شود؛ (پ) **قدیمی‌های منتشرنشده کنار می‌روند:** هر `CHECKPOINT` قدیمی‌تر `a` که در مقصد رکورد ندارد و `CHECKPOINT` بعدی‌اش `b ≤ c` است «جایگزین‌شده» (`SUPERSEDED`) است؛ برای آن دقیقاً یک `EVENT(CHECKPOINT_SUPERSEDED)` با `checkpoint_seq = a` و `superseded_by_seq = b` (نخستین `CHECKPOINT` پس از `a`) نوشته می‌شود؛ این `EVENT` **پس از** `CHECKPOINT` جانشین append می‌شود (`seq` آن بزرگ‌تر از `b` است) و `a` از آن پس **هرگز** دوباره منتشر نمی‌شود؛ (ت) **پنج مقدار نویسنده** رکورد انتشار (بند ۳) برای `c` به namespace `checkpoints` مقصد فرستاده می‌شود و مقصد خودش دو مقدار دیگر (`published_at_utc` و `receipt`) را تعیین و به رکورد می‌افزاید؛ (ث) رکورد هفت‌فیلدی از مقصد با یک خواندن مستقل بازخوانی می‌شود و باید پنج مقدار نویسنده‌اش برابر مقدارهای ارسالی و دو مقدار مقصد طبق بند ۳ معتبر باشند؛ فقط در این صورت انتشار «موفق» است و `receipt` همان رکورد در `CHECKPOINT` بعدی (`previous_publication`) می‌آید. شکست → `EVENT(CHECKPOINT_PUBLISH_FAILED)` و تلاش دوباره (حداکثر ساعتی [P]). **فقط آخرین `CHECKPOINT` journal دوباره منتشر می‌شود** (وضعیت `UNPUBLISHED_LATEST`)؛ تلاش دوباره‌ی `CHECKPOINT`ی که `CHECKPOINT` بعدی دارد ممنوع است (writer آن را رد می‌کند: `SupersededError`) و مقصد هم رکوردی با `seq` کوچک‌تر یا مساوی آخرین `seq` خودش را نمی‌پذیرد (`TargetReject`). هر تلاش دوباره **پیش از ارسال** رکورد این `seq` را از مقصد می‌خواند و اگر هست و پنج مقدارش برابر است همان را موفق می‌شمارد؛ در مقصد هر `seq` حداکثر یک رکورد دارد. نتیجه: رکوردهای مقصد به ترتیب **پذیرش** همیشه `seq` اکیداً صعودی دارند (بند ۵ (v)) و `previous_publication` (بند ۵ (vii)) هیچ‌گاه به رکوردی که بعداً پذیرفته شود وابسته نیست. وضعیت هر `CHECKPOINT` در گزارش verifier یکی از `PUBLISHED`، `SUPERSEDED` و `UNPUBLISHED_LATEST` است؛ `CHECKPOINT` بعدی همیشه نوشته می‌شود و `previous_publication` آن آخرین انتشار موفق‌شده است (بند ۵ (vii)).
3. **رکورد انتشار (r5: هفت مقدار؛ r4 اشتباهاً شش مقدار و بدون `receipt` می‌گفت).** رکورد ذخیره‌شده در مقصد (append-only) دقیقاً این هفت کلید را دارد. **پنج کلید نویسنده:** `journal_id` (= `entry_hash` ورودی GENESIS)، `seq = c`، `entry_hash = H_c`، `head_seq = c − 1`، `head_entry_hash = H_{c−1}`. **دو کلید مقصد** که نویسنده نمی‌تواند بدهد یا عوض کند: `published_at_utc` (زمان پذیرش رکورد طبق ساعت **خودِ مقصد**، UTC، با گرامر B.2 بند ۸: `YYYY-MM-DDTHH:MM:SS(.mmm)?Z`) و `receipt` (رشته‌ی ASCII چاپ‌شدنی بدون فاصله، ۱ تا ۲۵۶ نویسه [P]، شناسه‌ی همین رکورد در مقصد، مثلاً شناسه‌ی commit یا توکن سرویس زمان‌گذاری). مقدار anchor‌شده `(c, H_c)` است؛ چون هر hash به hash قبلی وابسته است، `H_c` همه‌ی ورودی‌های `0..c` را متعهد می‌کند، از جمله خودِ `CHECKPOINT`. **معنای `receipt`:** برای verifier سه خاصیت دارد: (الف) با رکوردی که از مقصد خوانده می‌شود برابر است؛ (ب) در میان همه‌ی رکوردها یکتاست؛ (پ) در `previous_publication` `CHECKPOINT` بعدی می‌آید و به این ترتیب hash زنجیره آن را متعهد می‌کند، پس نویسنده نمی‌تواند بعداً یک receipt دیگر را جای آن بگذارد. verifier اعتبار رمزنگاری خودِ receipt را نمی‌سنجد مگر مقصد روش بررسی‌پذیری داشته باشد که در `CONFIG.checkpoint_publication_target` نام برده شده؛ وگرنه receipt فقط به اندازه‌ی اعتماد به مقصد معتبر است (بند ۶).
4. **الزام و قرارداد مقصد (r6).** مقصد باید append-only و دارای زمان‌گذاری باشد، writer نتواند رکورد قدیمی را حذف یا ویرایش کند، و **`published_at_utc` را خودِ مقصد بگذارد، نه نویسنده** (مثلاً زمان دریافت سرور یا زمان صدور یک سرویس timestamp سوم‌شخص؛ نه تاریخ author/committer یک commit که نویسنده می‌نویسد). **قرارداد مقصد در `CONFIG.checkpoint_publication_target` یک شیء با دقیقاً ده کلید است:** `name` (نام مقصد)؛ `operator` (چه کسی آن را اداره می‌کند)؛ `operator_independent_of_writer` (**باید `true` باشد**: مقصدی که نویسنده کنترل می‌کند anchor نیست)؛ `time_source` (چه ساعت یا سرویسی `published_at_utc` را تعیین می‌کند)؛ `receipt_kind` (نوع receipt)؛ `receipt_verification` (روشی که receipt مستقل از نویسنده بررسی می‌شود، یا مقدار ثابت `NONE_TRUST_ONLY`)؛ `receipt_verification_material` (گواهی عمومی، اثرانگشت کلید یا نشانی لازم برای آن بررسی؛ **`null` اگر و فقط اگر** `receipt_verification = NONE_TRUST_ONLY`)؛ `read_client` (کلاینت مستقلی که رکوردها با آن بازخوانی می‌شوند)؛ `namespaces` (شیء با دقیقاً دو کلید `checkpoints` و `manifests` و دو مقدار رشته‌ای ناتهی **متمایز**؛ بند ۹)؛ و `seq_monotonic_enforced_by_target` (boolean: آیا خودِ مقصد رکوردی با `seq` غیرصعودی را رد می‌کند). هر مقدار متنی بین ۱ و ۵۱۲ نویسه و بدون فاصله‌ی ابتدا یا انتها است. verifier این شکل را در `CONFIG` می‌سنجد (B.6 بند ۱۵، `CONFIG_INVALID`). این spec مقصد را **نام نمی‌برد و هیچ مقصدی را از پیش نمی‌پذیرد**؛ انتخاب مقصد، تعیین مقدار این ده کلید و تأیید مستقل آن (از جمله اینکه ساعت مقصد از ساعت نویسنده مستقل است و receipt چگونه بررسی می‌شود) تصمیم جدا و **شرط lock باز** است. تست end-to-end بند ۷ الزامی است.
5. **تشخیص (B.6 مرحله‌ی ۱۰)** — رکوردهای مقصد به ترتیب **پذیرش در مقصد** خوانده می‌شوند و هرگز مرتب نمی‌شوند: (i) journal ورودی با `seq = r.seq` دارد، وگرنه `TRUNCATED`؛ (ii) `entry_hash` آن ورودی برابر `r.entry_hash` است، وگرنه `REWRITTEN`؛ (iii) آن ورودی از نوع `CHECKPOINT` است با `head_seq = r.seq − 1` و `head_entry_hash` برابر `entry_hash` ورودی `seq − 1` و برابر `r.head_entry_hash`، و `r.journal_id` برابر `entry_hash` GENESIS است؛ (iv) **شکل (r6):** رکورد دقیقاً هفت کلید بند ۳ را دارد؛ `seq` و `head_seq` اعداد صحیح بین ۰ و `2^53`؛ `journal_id`، `entry_hash` و `head_entry_hash` رشته‌ی hex ۶۴ نویسه با حروف کوچک؛ `published_at_utc` با گرامر B.2 بند ۸؛ و `receipt` رشته‌ی ASCII چاپ‌شدنی بدون فاصله با ۱ تا ۲۵۶ نویسه. هر کلید کم یا اضافه یا مقدار بدشکل (از جمله تاریخ ناممکن) `MALFORMED_PUBLICATION` است، بدون exception؛ (v) **ترتیب و زمان (r6):** `seq` رکوردها در ترتیب پذیرش **اکیداً صعودی** است (وگرنه `SEQ_ORDER_VIOLATION`؛ هر `seq` حداکثر یک رکورد)، `published_at_utc` در همان ترتیب **غیرنزولی** است (وگرنه `TARGET_TIME_REGRESSION`) و `published_at_utc ≥ recorded_at_utc(CHECKPOINT) − 5000 ms` (حد `clock_offset_limit_ms`؛ وگرنه `TARGET_TIME_ANOMALY`: ساعت نویسنده یا مقصد معتبر نیست)؛ (vi) `receipt` ها در همه‌ی رکوردهای مقصد (هر دو namespace، بند ۹) یکتا هستند (`DUPLICATE_RECEIPT`)؛ (vii) `previous_publication` هر `CHECKPOINT` با شماره‌ی `c`: **`null`** است اگر هیچ رکوردی با `seq < c` و `published_at_utc ≤ recorded_at_utc(c) − 5000 ms` نیست؛ وگرنه برابر `{seq, entry_hash, receipt}` رکوردی `q` از مقصد با `q.seq < c` و `published_at_utc(q) ≤ recorded_at_utc(c) + 5000 ms` است که هیچ رکورد `q'` با `q.seq < q'.seq < c` و `published_at_utc(q') ≤ recorded_at_utc(c) − 5000 ms` ندارد؛ ناهمخوانی (از جمله `receipt` متفاوت با مقصد) `PREV_PUBLICATION_MISMATCH` است؛ (viii) **سیاست جایگزینی (r6):** هر `CHECKPOINT` که رکورد مقصد ندارد و `CHECKPOINT` بعدی دارد باید دقیقاً یک `EVENT(CHECKPOINT_SUPERSEDED)` معتبر داشته باشد، وگرنه `SUPERSEDED_UNRECORDED`؛ (ix) آن `EVENT` فقط وقتی معتبر است که `checkpoint_seq` یک `CHECKPOINT` بدون رکورد مقصد باشد، `superseded_by_seq` نخستین `CHECKPOINT` پس از آن باشد، `seq` خودِ `EVENT` از `superseded_by_seq` بزرگ‌تر باشد و برای همان `checkpoint_seq` یکتا باشد؛ هر `EVENT` دیگر (برای `CHECKPOINT`ی که رکورد مقصد دارد، تکراری، یا با `superseded_by_seq` نادرست یا پیش از `CHECKPOINT` جانشین) `SUPERSEDED_INVALID` است. آخرین `CHECKPOINT` که هنوز منتشر نشده (`UNPUBLISHED_LATEST`) نقض نیست. دست‌کاری payload خودِ `CHECKPOINT` یا `entry_hash` را عوض می‌کند (زنجیره می‌شکند) یا اگر زنجیره دوباره hash شود با رکورد منتشرشده نمی‌خواند.
6. **محدودیت باقی‌مانده (صریح):** ورودی‌های بعد از آخرین انتشار موفق تا انتشار بعدی (حداکثر یک دوره‌ی maintenance، ۲۴ ساعت [P]، به‌علاوه‌ی تأخیر انتشار) به‌طور خارجی anchor نیستند: در آن فاصله دست‌کاری فقط با زنجیره‌ی داخلی تشخیص داده می‌شود و بازنویسی کامل دم زنجیره بعد از آخرین انتشار قابل‌تشخیص نیست. این محدودیت پذیرفته و گزارش می‌شود. **اعتماد به زمان مقصد:** `published_at_utc` و `receipt` را مقصد تعیین می‌کند؛ verifier فقط سازگاری درونی (بند ۵: ترتیب، یکتایی، حد ۵ ثانیه نسبت به ساعت نویسنده) را می‌سنجد و نمی‌تواند صحت مطلق ساعت مقصد را ثابت کند. **journal محلی به‌تنهایی هیچ تغییرناپذیری بیرونی ندارد:** هر که به فایل دسترسی دارد می‌تواند کل آن را بازنویسی کند؛ فقط رکوردهای یک مقصد مستقل (با ساعت مستقل خودش) این بازنویسی را قابل‌تشخیص می‌کنند.
7. **تست end-to-end قبل از T0 (D13):** بعد از ثبت `CONFIG` یک `CHECKPOINT` واقعی append و منتشر می‌شود، رکورد هفت‌فیلدی با کلاینت مستقل بازخوانی می‌شود، verifier با آن می‌گذرد (از جمله اینکه `published_at_utc` و `receipt` را مقصد گذاشته نه نویسنده)، و روی یک **کپی** از journal که تا قبل از آن `CHECKPOINT` بریده شده verifier باید `TRUNCATED` گزارش کند. نتیجه به‌صورت `EVENT(CHECKPOINT_E2E_TEST)` ثبت می‌شود.
8. **ارتباط با تحلیل (r5):** prefix تحلیل (C.17) باید `CHECKPOINT`ی باشد که **طبق زمان مقصد** تا `S` منتشر شده؛ یعنی هر تحلیل رسمی فقط روی شواهدی ایستاده است که تا `S` به‌طور خارجی anchor بوده‌اند. ورودی‌های بعد از آن `CHECKPOINT` (چه پیش از `S` append شده باشند و چه بعد از آن) در آن تحلیل خوانده نمی‌شوند؛ محدودیت بند ۶ برای تحلیل فقط به این شکل اثر می‌گذارد که دم anchor‌نشده در آن تحلیل نیست.
9. **namespace `manifests` (r6).** manifest تحلیل (C.17) در همان مقصد ولی در namespace جدا (`CONFIG.checkpoint_publication_target.namespaces.manifests`) و با رکوردی **چهارکلیدی** نگه‌داری می‌شود و هرگز با رکورد هفت‌فیلدی بند ۳ مخلوط نمی‌شود: `journal_id` (= `entry_hash` GENESIS) و `manifest_sha256` (SHA-256 بایت‌های `canon` فایل manifest) از نویسنده، و `published_at_utc` (گرامر بند ۸) و `receipt` (مثل بند ۳) که مقصد می‌گذارد. ترتیب: نویسنده manifest را به مقصد می‌فرستد، رکورد را بازمی‌خواند و **سپس** `EVENT(ANALYSIS_MANIFEST)` را با `manifest_published_at_utc` و `manifest_receipt` همان رکورد می‌نویسد. قواعد verifier: رکورد دقیقاً چهار کلید و مقدار معتبر دارد (`MALFORMED_MANIFEST_PUBLICATION`)؛ `journal_id` برابر GENESIS است؛ `manifest_sha256` در namespace یکتاست (`DUPLICATE_MANIFEST`؛ **اولین** رکورد در ترتیب پذیرش معتبر است)؛ `published_at_utc` در ترتیب پذیرش غیرنزولی است (`TARGET_TIME_REGRESSION`)؛ و `receipt` در کل مقصد یکتاست (`DUPLICATE_RECEIPT`). قواعد پیوند با `EVENT` در C.17 و B.6 بند ۱۳ است. تست end-to-end بند ۷ فقط namespace `checkpoints` را می‌آزماید؛ انتشار manifest با اولین manifest واقعی و **پیش از** دیدن هر متریک آزموده می‌شود: اگر انتشار آن شکست بخورد تحلیل رسمی انجام نمی‌شود (`MANIFEST_NOT_PUBLISHED`). فایل خودِ manifest (نه فقط hash آن) کنار گزارش نگه‌داری می‌شود؛ اگر در اختیار verifier نباشد، گزارش `NOT_CHECKED` می‌گوید.

**KAT-10 (ساختگی؛ ادامه‌ی زنجیره‌ی KAT-4):** ورودی `seq = 3` (از نوع `CHECKPOINT`، `previous_publication = null`، `published_to = "KAT-TARGET"`، `human_head_hash` شصت‌وچهار صفر) روی سه ورودی KAT-4:

| seq | `canon(payload)` | `entry_hash` |
|---|---|---|
| 3 | `{"head_entry_hash":"3f57938701e5c711173d229d227c7eb8f67316d7f4d0716975f25e71b7eabb0d","head_seq":2,"human_head_hash":"0000000000000000000000000000000000000000000000000000000000000000","previous_publication":null,"published_to":"KAT-TARGET","recorded_at_utc":"2030-01-01T00:00:03.000Z","run_id":"kat","seq":3,"type":"CHECKPOINT"}` | `2e167d33ad6a1db833216d8fb70b6a619174f1192d18866deb541ed0ffde1452` |

رکورد منتشرشده‌ی هفت‌فیلدی (`canon`): `{"entry_hash":"2e167d33ad6a1db833216d8fb70b6a619174f1192d18866deb541ed0ffde1452","head_entry_hash":"3f57938701e5c711173d229d227c7eb8f67316d7f4d0716975f25e71b7eabb0d","head_seq":2,"journal_id":"285406718b447a3df7e531606724c9f4641984b4eddcada20623dc806665a057","published_at_utc":"2030-01-01T00:00:04.000Z","receipt":"KAT-R3","seq":3}` (`published_at_utc` و `receipt = "KAT-R3"` را مقصد گذاشته است).

| مورد | تغییر | نتیجه‌ی verifier |
|---|---|---|
| K10-1 | بدون تغییر | پاس |
| K10-2 | journal بریده به `seq` ۰ تا ۲ (آخرین `CHECKPOINT` حذف شده) | `TRUNCATED` |
| K10-3 | یک نویسه‌ی `head_entry_hash` در payload ورودی ۳ عوض شود | شکست زنجیره (`entry_hash` بازمحاسبه‌شده نمی‌خواند) |
| K10-4 | مورد K10-3 و hash خودِ ورودی ۳ دوباره محاسبه شود | `head_entry_hash` با hash ورودی ۲ نمی‌خواند و `REWRITTEN` نسبت به رکورد منتشرشده |
| K10-5 | ورودی ۲ دست‌کاری (`n = 1893456000001`) و ورودی‌های ۲ و ۳ کامل دوباره hash شوند (`entry_hash` ۲ برابر `6fe9d8e080fd112beaa26fa74f132a675a5185368465340b2aff0ae98069dd0d`، ۳ برابر `811128668c820dce033e3916686eae0d99336b85a1ee95cd4c5eccdba0f34a93`) | زنجیره‌ی داخلی سازگار است؛ `REWRITTEN` فقط نسبت به رکورد منتشرشده |

**KAT-10b (ساختگی، r5) — `previous_publication` غیرتهی و رکورد هفت‌فیلدی:** ادامه‌ی KAT-10: ورودی `seq = 4` از نوع `CHECKPOINT` با `head_seq = 3`، `head_entry_hash` برابر hash ورودی ۳، `human_head_hash` شصت‌وچهار صفر، `published_to = "KAT-TARGET"`، `recorded_at_utc = 2030-01-01T00:00:15.000Z` و `previous_publication` برابر `{seq: 3, entry_hash: H3, receipt: "KAT-R3"}` (رکورد ورودی ۳ در مقصد؛ `H3` = hash ورودی ۳):

| seq | `canon(payload)` | `entry_hash` |
|---|---|---|
| 4 | `{"head_entry_hash":"2e167d33ad6a1db833216d8fb70b6a619174f1192d18866deb541ed0ffde1452","head_seq":3,"human_head_hash":"0000000000000000000000000000000000000000000000000000000000000000","previous_publication":{"entry_hash":"2e167d33ad6a1db833216d8fb70b6a619174f1192d18866deb541ed0ffde1452","receipt":"KAT-R3","seq":3},"published_to":"KAT-TARGET","recorded_at_utc":"2030-01-01T00:00:15.000Z","run_id":"kat","seq":4,"type":"CHECKPOINT"}` | `92f1396edac7ceeced2196a974ed3a05db6519d3e66cf1367eb86370934c6c34` |

رکورد منتشرشده‌ی ورودی ۴ (`canon`): `{"entry_hash":"92f1396edac7ceeced2196a974ed3a05db6519d3e66cf1367eb86370934c6c34","head_entry_hash":"2e167d33ad6a1db833216d8fb70b6a619174f1192d18866deb541ed0ffde1452","head_seq":3,"journal_id":"285406718b447a3df7e531606724c9f4641984b4eddcada20623dc806665a057","published_at_utc":"2030-01-01T00:00:16.000Z","receipt":"KAT-R4","seq":4}`. رکورد ورودی ۳ همان رکورد KAT-10 است. برای ورودی ۴ قاعده‌ی بند ۵ (vii) برقرار است: رکورد ۳ با `published_at_utc = 00:00:04` از `00:00:15 − 5 s = 00:00:10` قدیمی‌تر است، پس `previous_publication` نباید `null` باشد.

| مورد | تغییر | نتیجه‌ی verifier |
|---|---|---|
| K10b-1 | بدون تغییر (journal ۰..۴ و دو رکورد مقصد) | پاس |
| K10b-2 | `previous_publication.receipt` در ورودی ۴ برابر `"KAT-R3x"` و hash ورودی ۴ دوباره محاسبه شود (`c7a3ea9eb93c21ee67c7e22af9557e2f67097a74ebdf01d76b35204301f40593`) | `PREV_PUBLICATION_MISMATCH` و `REWRITTEN` نسبت به رکورد ورودی ۴ |
| K10b-3 | `previous_publication = null` در ورودی ۴ و hash آن دوباره محاسبه شود (`8a02addb629c3febf7e2a6280921bc712b8c2b222a85247b33e0aa62259a4a67`) | `PREV_PUBLICATION_MISMATCH` و `REWRITTEN` نسبت به رکورد ورودی ۴ |
| K10b-4 | رکورد ورودی ۳ در مقصد بدون کلید `receipt` (شش کلید) | `MALFORMED_PUBLICATION` (و در پی آن `PREV_PUBLICATION_MISMATCH`، چون ورودی ۴ به رکورد معتبری اشاره نمی‌کند) |
| K10b-5 | رکورد ورودی ۳ در مقصد با کلید اضافه `note` | `MALFORMED_PUBLICATION` (و در پی آن `PREV_PUBLICATION_MISMATCH`، مثل K10b-4) |
| K10b-6 | رکورد ورودی ۳ در مقصد با `receipt = ""` | `MALFORMED_PUBLICATION` (و در پی آن `PREV_PUBLICATION_MISMATCH`، مثل K10b-4) |
| K10b-7 | `published_at_utc` رکورد ۳ در مقصد برابر `2030-01-01T00:00:20.000Z` (دیرتر از رکورد ۴) | `TARGET_TIME_REGRESSION` |
| K10b-8 | `receipt` رکورد ۴ هم `"KAT-R3"` | `DUPLICATE_RECEIPT` |
| K10b-9 | `receipt` رکورد ۳ در مقصد برابر `"KAT-R3x"` ولی journal دست‌نخورده است (ورودی ۴ همچنان `KAT-R3` را متعهد کرده) | `PREV_PUBLICATION_MISMATCH` (receipt متعهدشده با مقصد نمی‌خواند) |
| K10b-10 | `published_at_utc` رکورد ۳ برابر `2029-12-31T23:59:50.000Z` (بیش از ۵ ثانیه پیش از `recorded_at_utc` ورودی ۳) | `TARGET_TIME_ANOMALY` |
| K10b-11 | رکورد ورودی ۳ در مقصد حذف شود ولی رکورد ورودی ۴ بماند | `PREV_PUBLICATION_MISMATCH` (`previous_publication` به رکوردی اشاره می‌کند که در مقصد نیست) و `SUPERSEDED_UNRECORDED` (r6: `CHECKPOINT` ۳ رکورد مقصد ندارد ولی `CHECKPOINT` ۴ بعد از آن هست و `EVENT(CHECKPOINT_SUPERSEDED)` ندارد) |

**KAT-10c (ساختگی، r6) — انتشار ناموفق، جایگزینی و ترتیب پذیرش.** journal سالمی با چند `CHECKPOINT` `c1 < c2 < c3` که در آن `c2` منتشر نشده است، با یک مقصد ساختگی که رکوردها را به ترتیب پذیرش نگه می‌دارد و رکوردی با `seq` کوچک‌تر یا مساوی آخرین `seq` خودش را رد می‌کند؛ هر ردیف یک سناریو است. ستون آخر verdict verifier است («تمیز» یعنی هیچ نقضی)، یا برای SU9 و SU10 استثنای writer و مقصد.

| مورد | سناریو | نتیجه |
|---|---|---|
| SU1 | CHECKPOINT `c2` منتشر نشد (`CHECKPOINT_PUBLISH_FAILED`)؛ `c3` بعدی منتشر شد؛ نویسنده `EVENT(CHECKPOINT_SUPERSEDED)` برای `c2` نوشته است | تمیز |
| SU2 | همان SU1 ولی `EVENT(CHECKPOINT_SUPERSEDED)` نوشته نشده | `SUPERSEDED_UNRECORDED` |
| SU3 | `EVENT(CHECKPOINT_SUPERSEDED)` برای `CHECKPOINT` ای که رکورد مقصد دارد | `SUPERSEDED_INVALID` |
| SU4 | دو `EVENT(CHECKPOINT_SUPERSEDED)` برای همان `c2` | `SUPERSEDED_INVALID` |
| SU5 | `superseded_by_seq` برابر `CHECKPOINT` بعدیِ `c2` نیست (و `c2` عملاً بی‌پوشش می‌ماند) | `SUPERSEDED_INVALID` و `SUPERSEDED_UNRECORDED` |
| SU6 | `EVENT` پیش از `CHECKPOINT` جانشین نوشته شده (`seq` آن کوچک‌تر از `superseded_by_seq`؛ `c2` عملاً بی‌پوشش می‌ماند) | `SUPERSEDED_INVALID` و `SUPERSEDED_UNRECORDED` |
| SU7 | `c2` آخرین `CHECKPOINT` است و هنوز منتشر نشده (وضعیت `UNPUBLISHED_LATEST`): بدون `EVENT` تمیز است؛ پس از retry موفق (مقصد `seq` بزرگ‌تر از آخرین `seq` خودش را می‌پذیرد) نیز تمیز است | تمیز |
| SU8 | رکوردهای مقصد به ترتیب پذیرش با `seq` نزولی خوانده می‌شوند (رکورد `c3` و بعد رکورد `c2`، با زمان مقصد غیرنزولی) | `SEQ_ORDER_VIOLATION` |
| SU9 | نویسنده می‌خواهد `c2` را پس از ثبت `c3` دوباره منتشر کند (retry) | استثنای `SupersededError` |
| SU10 | مقصد رکوردی با `seq` کوچک‌تر یا مساوی آخرین `seq` خودش دریافت می‌کند | استثنای `TargetReject` |


---

## C — Forward logging protocol

**C.1 قفل‌ها و ترتیب یکتای پیش از T0 (شرط ۴ و ۱۷) — اصلاح ۴ (r4):** در r3 ابهام این بود که `code_sha256` در `CONFIG` ثبت می‌شود ولی «ساخت پیاده‌سازی» بعد از `CONFIG` آمده بود. در r4 ترتیب دقیقاً این **یازده گام** است؛ هر گام فقط بعد از کامل شدن گام قبل شروع می‌شود و B.6 بند ۱۴ ترتیب ورودی‌های journal را بازبینی می‌کند:

1. **LOCK:** SHA-256 همین فایل spec با دستور `lock` از GPT ثبت می‌شود. بدون این دستور هیچ گام بعدی رسمی نیست. بعد از lock، spec تغییر نمی‌کند (تغییر = C.15).
2. **BUILD:** writer، collector، auditor، verifier و کد متریک در مخزن جدا ساخته می‌شوند و آزمون‌های ساختگی D (KAT-1 تا KAT-14) پاس می‌شوند. هیچ ورودی journal رسمی هنوز وجود ندارد.
3. **DRY-RUN (خارج از شواهد):** handshake آزمایشی به `feed_url` (D19)، سنجش آهنگ پیام‌های واقعی برای تأیید `silence_timeout_s`، آزمون‌های اتصال C.16 (قطع اجباری، شکست reconnect، چرخش موفق با سیاست کوتاه‌شده، کندل مرزی) و آزمون ساعت C.2؛ **(r5)** به‌علاوه‌ی: (الف) **مشاهده‌ی رفتار عملیاتی عمر اتصال** (در برابر حد مستندشده‌ی C.16): یک اتصال مشاهده‌ای بدون چرخش تا بسته شدن توسط سرور (حداکثر ۲۵ ساعت) و ثبت سن آن در لحظه‌ی بسته شدن (C.16)؛ (ب) تأیید اینکه روی پیام‌های واقعی `k.T = k.t + 299999` است (V08، C.2)؛ (پ) پاسخ pong به ping سرور. **اگر dry-run مقداری از [P] یا ثابت‌های C.2/C.16 (مثل `max_connection_age_s`، `silence_timeout_s`، `299999`) را رد کند، spec قفل‌شده کنار گذاشته می‌شود و نسخه‌ی اصلاح‌شده lock می‌شود (C.15)؛ چون هنوز `GENESIS` نیست، هیچ شاهدی از بین نمی‌رود.** خروجی این گام فقط به مخزن dry-run می‌رود و جزو journal نیست؛ گزارش dry-run `code_tree_sha256` کدی را که واقعاً اجرا شده ثبت می‌کند.
4. **CODE FREEZE:** `code_sha256` از فایل‌های نهایی محاسبه می‌شود (tree hash در پایین، KAT-14). بعد از این گام هیچ بایتی از کد، فایل lock وابستگی‌ها یا اسکریپت شروع تغییر نمی‌کند. **کد هرگز hash ورودی `CONFIG` یا هیچ hash دیگر journal را در خود ندارد**؛ وگرنه `code_sha256` به `CONFIG` و `CONFIG` به `code_sha256` وابسته می‌شد و هیچ‌کدام محاسبه‌پذیر نبود. collector در زمان اجرا `CONFIG` را از journal می‌خواند و `code_sha256` ثبت‌شده را با hash فایل‌های در حال اجرای خودش مقایسه می‌کند (گام ۸). **هر dry-run فقط برای همان بایت‌ها معتبر است:** `code_sha256` باید با `code_tree_sha256` گزارش dry-run (گام ۳) برابر باشد؛ اگر بعد از dry-run حتی یک بایت کد یا فایل lock عوض شود، گام‌های ۲ و ۳ از نو انجام می‌شوند و بعد دوباره گام ۴.
5. **GENESIS:** ورودی `GENESIS` با `spec_sha256` (B.2 بند ۴).
6. **CONFIG:** یک ورودی `CONFIG` شامل `code_sha256` گام ۴، `feed_url` (C.2)، `clock_policy`، `rotation_policy`، `checkpoint_publication_target` و بقیه‌ی فیلدهای B.3. hash همین ورودی `config_ref` همه‌ی تصمیم‌هاست. بعد از این ورودی هیچ فیلد پیکربندی تغییر نمی‌کند.
7. **E2E ANCHORING واقعی:** بعد از `CONFIG` یک `CHECKPOINT` واقعی append و منتشر می‌شود، با کلاینت مستقل بازخوانی می‌شود، verifier با آن می‌گذرد، و روی کپیِ بریده‌شده `TRUNCATED` می‌دهد (B.7 بند ۷)؛ نتیجه `EVENT(CHECKPOINT_E2E_TEST)` با `result = "PASS"` است. این گام **پیش از** `COLLECTOR_START` است.
8. **COLLECTOR START:** collector شروع می‌شود و `EVENT(COLLECTOR_START)` می‌نویسد: `collector_start_utc`، `code_tree_sha256` (hash فایل‌های در حال اجرا که خودِ collector حساب کرده؛ باید برابر `CONFIG.code_sha256` باشد) و `startup_url_check = "OK"` (فقط اگر ثابت کد، `CONFIG.feed_url`، `runtime_manifest.feed_url` و C.2 بایت‌به‌بایت برابرند؛ در غیر این صورت collector شروع نمی‌شود، U7). سپس اولین `FEED_CONNECT`. `GENESIS ≤ collector_start ≤ T0 − 25 h` [P]. هیچ `CANDLE`، `FEED_CONNECT` یا `DECISION` پیش از `COLLECTOR_START` در journal نیست.
9. **WARM-UP:** collector دست‌کم تا `T0 − 25 h` شروع شده است، ۲۸۸ کندل زنده‌ی قبل از T0 را جمع کرده و **دست‌کم یک چرخش برنامه‌ریزی‌شده‌ی کامل** اتصال (C.16: `FEED_ROTATION` با `phase = CUTOVER` و `reason = PLANNED`) را در شرایط واقعی انجام داده است. هیچ `p_raw` پیش از T0 نوشته نمی‌شود.
10. **T0_DECLARATION:** بعد از اولین چرخش برنامه‌ریزی‌شده‌ی کامل و قبل از T0 نوشته می‌شود (`recorded_at_utc < t0_utc`)؛ `t0_utc` روی شبکه‌ی ساعتی است و `config_entry_hash`، `code_sha256`، `spec_sha256` و `collector_start_utc` را دارد. **T0 تا نوشته شدن همین ورودی تعیین‌شده نیست:** اگر اولین چرخش کامل هنوز انجام نشده باشد، `T0_DECLARATION` منتظر می‌ماند و T0 به نقطه‌ی ساعتی بعدیِ مجاز (با رعایت `collector_start ≤ T0 − 25 h`) می‌رود؛ تا آن لحظه هیچ `DECISION` نوشته نشده است. بعد از نوشته شدن، تغییر آن فقط با amendment و T0 جدید ممکن است.
11. **T0:** اولین `DECISION` دقیقاً برای `d = T0` است. هیچ `DECISION` برای `d < T0` و هیچ `DECISION` پیش از `T0_DECLARATION` نوشته نمی‌شود.

اگر T0 در زمان downtime باشد، همان نقطه‌ی شبکه با `GAP_FILL` ثبت می‌شود (C.4). T0 جابه‌جا نمی‌شود.

**`code_sha256` — tree hash (KAT-14):** `code_sha256 = SHA-256( canon({"files": [[path, sha256_hex(بایت‌های فایل)], …]}) )` با `canon` طبق B.2، `path` مسیر نسبی POSIX با `/`، و فهرست به ترتیب صعودی code point مسیر. فایل‌ها: همه‌ی منبع‌های writer، collector، auditor و verifier، اسکریپت شروع و فایل lock وابستگی‌ها (از جمله نسخه‌ی numpy)؛ بایت‌ها همان‌طور که روی دیسک‌اند خوانده می‌شوند (بدون تبدیل پایان خط). journal، log، `__pycache__` و داده‌ی آزمون داخل فهرست نیستند.

**KAT-14 (ساختگی):** سه فایل:

| مسیر | محتوا (متن) | `sha256` بایت‌های فایل |
|---|---|---|
| `collector.py` | `print('collector')\n` | `26413fbafb9c56a68865d13f3ee5a61d6f267bf592e7d99bf76958088108bb36` |
| `lock.txt` | `numpy==2.5.3\n` | `5c12d85e7c08038d1dd9ffbf8119d12ce808885230a47e2bf65dcd9f114659d5` |
| `writer.py` | `print('writer')\n` | `0acdf7bf3cd1f0b743fc7b56bbd714e8a073e2c429e8555a355f8b325964ea8f` |

`canon` فهرست: `{"files":[["collector.py","26413fbafb9c56a68865d13f3ee5a61d6f267bf592e7d99bf76958088108bb36"],["lock.txt","5c12d85e7c08038d1dd9ffbf8119d12ce808885230a47e2bf65dcd9f114659d5"],["writer.py","0acdf7bf3cd1f0b743fc7b56bbd714e8a073e2c429e8555a355f8b325964ea8f"]]}`

`code_sha256 = 54a68dba740d3ca2ba427362ca413167267c5f4056d95c6f60c6dc4d8484c696`.

**مقدارهای ردشده:** فهرست بدون مرتب‌سازی (ترتیب `writer.py`، `collector.py`، `lock.txt`) → `ca7b7f3bd86a076a34ea9f307de725c5b70a1a3d55a37473c39728a2fc903d40`؛ فایل `writer.py` با یک بایت کمتر (بدون LF پایانی) → `e648bd0c7e32dedb8270aa6193195035840bc7f165ae20b17515504eb1449a66`. پیاده‌سازی‌ای که این مقدارها را بدهد رد است.

**C.2 Feed زنده، ساعت و تعریف «کندل real-time» — اصلاح ۶ (r2)، اصلاح ۲ و ۶ (r3)، اصلاح ۱ (r4) و اصلاح ۶ و ۷ (r6):**
- **Feed:** `feed_id = "BINANCE_UM_WS_KLINE_5M_BTCUSDT_v1"`.
- **آدرس کامل و قفل‌شده** (نه فقط میزبان و stream): `feed_url = "wss://fstream.binance.com/market/ws/btcusdt@kline_5m"` (Binance USD-M Futures، دسته‌ی `/market`، raw stream، symbol `btcusdt` با حروف کوچک، interval `5m`).
- **منشأ:** مستندات رسمی Binance (صفحه‌ی «Important WebSocket Change Notice» و Change Log، بررسی‌شده در ۲۰۲۶-۱۰-۱۰): آدرس‌های قدیمی USDⓈ-M Futures تا ۲۰۲۶-۰۴-۲۳ در دسترس بودند و بعد از آن بازنشسته‌اند؛ پایه‌ی خانواده‌ی market برابر `wss://fstream.binance.com/market` است؛ stream های Kline در دسته‌ی Market‌اند و فرم raw آن‌ها `wss://fstream.binance.com/market/ws/<symbol>@kline_<interval>` است. مسیر قدیمی بدون `/market` و هر URL دیگر (از جمله combined `…/market/stream?streams=…`، حروف بزرگ، `/` پایانی) در این آزمایش **مجاز نیست**.
- **قفل و اعتبارسنجی URL:**
  1. `CONFIG.feed_url`، `runtime_manifest.feed_url` و ثابت داخل کد collector باید با رشته‌ی بالا **بایت‌به‌بایت** برابر باشند؛ در غیر این صورت collector شروع نمی‌شود (D13، D19).
  2. هر اتصال و اتصال مجدد یک `EVENT(FEED_CONNECT)` با `connection_id` (عدد صحیح صعودی از ۱)، `role` (`ACTIVE` یا `STANDBY`)، `connection_url` و `http_status` handshake می‌نویسد. فقط اتصالی که `connection_url` آن برابر `feed_url` است مجاز است. هر `CANDLE` و `CANDLE_ANOMALY` شماره‌ی اتصالی را که پیام از آن آمده در `connection_id` دارد؛ باز و بسته شدن اتصال‌ها و چرخش ۲۴ ساعته طبق C.16 است.
  3. هر `CANDLE` فیلد `feed_url` دارد. پیام نهایی‌ای که روی اتصالی با URL متفاوت برسد `CANDLE_ANOMALY(FEED_MISMATCH)` می‌شود و هرگز `CANDLE` نمی‌شود.
- **رکورد ساعت در لحظه‌ی دریافت (اصلاح ۱ در r4):** latency بدون اعتبار ساعت بی‌معنی است: ساعتی که ۱۰ ثانیه عقب است، پیامی را که در واقع ۶۵ ثانیه دیر رسیده با latency ظاهری ۵۵ ثانیه «به‌موقع» نشان می‌دهد. بنابراین collector در **همان لحظه‌ی دریافت** پیام (پیش از صف و پیش از append، در یک عمل اتمی) این مقدارها را می‌خواند و همراه ورودی ثبت می‌کند:
  - `ingested_ms`: ساعت محلی (wall clock) بر حسب ms.
  - `clock_status` ∈ {`SYNCHRONIZED`، `UNSYNCHRONIZED`، `UNKNOWN`}: وضعیت آخرین نمونه‌ی ساعت. نمونه هر `clock_poll_s = 30` [P] از دست‌کم دو منبع NTP (`clock_policy.ntp_sources`) گرفته می‌شود؛ `SYNCHRONIZED` فقط وقتی همه‌ی منابع پاسخ دهند و offset هر منبع حداکثر `clock_source_spread_ms = 1000` [P] با منبع اصلی (اولین منبع `ntp_sources`) فاصله داشته باشد (قاعده‌ی قطعی پایین)؛ وقتی هیچ دور کاملی نیست `UNKNOWN`.
  - `clock_offset_ms` = ساعت محلی − ساعت مرجع از همان نمونه، فقط از **منبع اصلی** (عدد صحیح؛ مثبت یعنی ساعت محلی جلوتر است).
  - `clock_sample_age_ms` = سن آن نمونه در لحظه‌ی دریافت، با ساعت **monotonic**.
  - `clock_step_ms` = (تغییر wall clock از لحظه‌ی نمونه تا دریافت) − (تغییر ساعت monotonic در همان فاصله)؛ پرش ساعت را آشکار می‌کند.
  وقتی `clock_status ≠ SYNCHRONIZED` است، offset، age و step می‌توانند `null` باشند و مقدارشان هرگز در محاسبه به‌کار نمی‌رود.
  - **قاعده‌ی قطعی انتخاب `clock_offset_ms` (r6).** هر دور نمونه‌برداری (هر `clock_poll_s`) از هر منبع `i` (به ترتیب `clock_policy.ntp_sources`، که فهرست مرتب است) یک offset گزارش‌شده‌ی `d_i` (ms؛ ساعت محلی − مرجع) می‌گیرد. حساب **دقیق** است و به اعشار دودویی وابسته نیست: `d_i` با کوتاه‌ترین نمایش round-trip‌اش به‌صورت عدد دهدهی خوانده و به **میکروثانیه‌ی صحیح** `u_i = ⌊1000·d_i + ½⌋` (نیم رو به بالا) تبدیل می‌شود؛ همه‌ی مقایسه‌ها روی همین عددهای صحیح است. (۱) منبع **اول** منبع اصلی است و **تنها** `clock_offset_ms` را می‌دهد: `clock_offset_ms = ⌊(u_0 + 500) / 1000⌋` (گردکردن دوم؛ ترتیب دو گردکردن ثابت است؛ نه میانگین و نه میانه). (۲) هر منبع دیگر فقط توافق را می‌سنجد: برای هر `i ≥ 1` باید `|u_i − u_0| ≤ 1 000 000` (یعنی `clock_source_spread_ms = 1000` [P] میلی‌ثانیه؛ حد **شامل** است). (۳) اگر کمتر از دو منبع تنظیم شده باشد، پاسخ هر منبع نرسیده یا `null`، `NaN` یا بی‌نهایت باشد، یا (۲) برقرار نباشد، این دور `UNSYNCHRONIZED` است و `clock_offset_ms`، `clock_sample_age_ms` و `clock_step_ms` هر سه `null` اند (CK01). (۴) **سن و پرش از نمونه‌ی منبع اصلی** سنجیده می‌شود: `clock_sample_age_ms = mono_now − mono_reply` و `clock_step_ms = (wall_now − wall_reply) − (mono_now − mono_reply)` که `mono_reply` و `wall_reply` خوانش ساعت monotonic و ساعت دیواری در لحظه‌ی رسیدن پاسخ منبع اصلی همان دور و `mono_now` و `wall_now` خوانش‌های لحظه‌ی دریافت پیام‌اند. (۵) هر دور کامل دور قبلی را جایگزین می‌کند؛ قبل از اولین دور کامل `clock_status = UNKNOWN`. قاعده‌ی دودویی ساده (`round(1000·d)` روی عدد اعشاری دودویی یا گرد کردن مستقیم به میلی‌ثانیه) در نیم‌میکروثانیه‌ها نتیجه‌ی دیگری می‌دهد؛ قاعده‌ی r6 همین است و باید دقیقاً پیاده شود (KAT-11c).
- **دلیل‌های نامعتبر بودن ساعت** (به ترتیب صعودی در `clock_reasons` می‌آیند):
  - **CK01:** `clock_status ≠ SYNCHRONIZED`، یا یکی از `clock_offset_ms`، `clock_sample_age_ms`، `clock_step_ms` موجود نیست. اگر CK01 برقرار باشد CK02 تا CK04 ارزیابی نمی‌شوند.
  - **CK02:** `clock_sample_age_ms > 120000` [P] (نمونه کهنه است).
  - **CK03:** `|clock_step_ms| > 250` [P] (ساعت بعد از نمونه پریده است).
  - **CK04:** `|clock_offset_ms| > 5000` [P] (همان `clock_offset_limit_ms`).
  `clock_ok` یعنی هیچ‌کدام برقرار نیست. **فقط وقتی `clock_ok` است** `latency_ms = ingested_ms − clock_offset_ms − (open_time_ms + 300000)` محاسبه می‌شود؛ وگرنه `latency_ms = null` و هیچ تصمیمی از latency خام ساعت محلی گرفته نمی‌شود.
- **اعتبارسنجی payload و ساعت (اصلاح ۶ در r3، اصلاح ۱ در r4):** تابع قطعی `validate_kline(raw_text, connection_url, ingested_ms, رکورد_ساعت)` به این ترتیب عمل می‌کند. payload raw شامل `e`، `E`، `s` و شیء `k` با `t`، `T`، `s`، `i`، `o`، `c`، `h`، `l`، `v`، `V`، `x` است؛ `open_time_ms = k.t`. `ingested_ms` لحظه‌ی **دریافت** پیام در collector است، ولی `recorded_at_utc` لحظه‌ی append است و می‌تواند دیرتر باشد.
  1. **V01 PARSE:** متن JSON معتبر نیست، شیء نیست، `e ≠ "kline"`، یا هر یک از فیلدهای لازم (`E`، `s`، `k.t`، `k.T`، `k.s`، `k.i`، `k.o`، `k.c`، `k.h`، `k.l`، `k.v`، `k.V`، `k.x`) وجود ندارد یا نوعش درست نیست (`E`، `k.t` و `k.T` عدد صحیح، یعنی literal JSON بدون نقطه‌ی اعشار و بدون نما، و نه boolean؛ `o`، `c`، `h`، `l`، `v`، `V` رشته؛ `x` boolean). نتیجه `MALFORMED[V01]` و ارزیابی همین‌جا تمام می‌شود. **(r6)** V01 همچنین وقتی برقرار است که طول متن خام بیش از `4096` نویسه [P] باشد (متنی که کامل ذخیره نمی‌شود شاهد قابل‌بازبینی نیست؛ طول بر حسب نویسه‌ی Unicode و حد **شامل** است: ۴۰۹۶ نویسه پذیرفته و ۴۰۹۷ نویسه رد می‌شود؛ KAT-8 M30 و M31)؛ این بررسی پیش از parse انجام می‌شود.
  2. اگر `k.x = false`، پیام **بی‌صدا دور ریخته می‌شود** (بدون ورودی و بدون ارزیابی ساعت)، چون stream در طول هر کندل مرتب پیام ناپایدار می‌فرستد. این پیام‌ها فقط برای تشخیص سکوت (C.16) شمرده می‌شوند.
  3. اگر `connection_url ≠ feed_url` → `FEED_MISMATCH`.
  4. CK01..CK04 ارزیابی می‌شوند (`clock_ok` یا نه).
  5. کدهای زیر همه ارزیابی می‌شوند و همه‌ی کدهای ناموفق به ترتیب صعودی در `malformed_reasons` می‌آیند: **V02 SYMBOL:** `s ≠ "BTCUSDT"` یا `k.s ≠ "BTCUSDT"`. **V03 INTERVAL:** `k.i ≠ "5m"`. **V04 GRID:** `k.t mod 300000 ≠ 0`. **V05 NUMERIC:** دست‌کم یکی از `k.o`، `k.h`، `k.l`، `k.c` با regex `^[0-9]+(\.[0-9]+)?$` نمی‌خواند یا مقدار Decimal آن صفر است (پس NaN، Infinity، منفی، نمای علمی، رشته‌ی خالی و صفر همه رد می‌شوند). **V06 OHLC_RELATION:** (فقط اگر V05 برقرار نیست) شرط `l ≤ min(o, c) ≤ max(o, c) ≤ h` با مقایسه‌ی Decimal برقرار نیست. **V07 FUTURE:** (**فقط اگر `clock_ok`**) `latency_ms < −clock_offset_limit_ms` (کندلی که پیش از پایان نامی‌اش «نهایی» رسیده). **V08 CLOSE_TIME (r5):** `k.T ≠ k.t + 299999` (زمان close یک کندل ۵ دقیقه‌ای `open + 300000 ms − 1 ms` است؛ این معنای `k.T` از قرارداد فیلدهای کندل Binance **فرض** شده، نگارنده آن را روی پیام زنده نسنجیده، و در dry-run با پیام‌های واقعی تأیید می‌شود، C.1 گام ۳؛ ثابت `299999` [P] است). V08 به ساعت وابسته نیست و مستقل از V02..V07 ارزیابی می‌شود. `k.T` فیلد جدا در `CANDLE` ندارد، ولی در `raw_message` هر `CANDLE` و `CANDLE_ANOMALY` هست و verifier V08 (و بقیه‌ی V01..V07) را از همان بازمحاسبه می‌کند (B.3 «شاهد کندل»، B.6 بند ۱۱، KAT-16).
  6. اگر هر یک از V02..V08 ناموفق باشد → `CANDLE_ANOMALY(MALFORMED)` (`latency_ms` فقط اگر `clock_ok` ذخیره می‌شود).
  7. اگر `clock_ok` نیست → `CANDLE_ANOMALY(CLOCK_INVALID)` با `clock_reasons` و رشته‌های `o`، `h`، `l`، `c`، `v` و `latency_ms = null`. این ورودی **هرگز `CANDLE` نمی‌سازد** و جای «اولین دریافت» را نمی‌گیرد.
  8. اگر `latency_ms > 60000` [P] → `CANDLE_ANOMALY(NON_REALTIME)`.
  9. اگر قبلاً `CANDLE` قابل‌استفاده برای همین `open_time_ms` وجود دارد: مقدار یکسان (`o`، `h`، `l`، `c`) → `DUPLICATE_IDENTICAL`؛ متفاوت → `DUPLICATE_CONFLICT`. (تکراری‌ای که با ساعت نامعتبر برسد در گام ۷ `CLOCK_INVALID` شده است، نه `DUPLICATE_*`.)
  10. در غیر این صورت `CANDLE` (اولین دریافت معتبر **با ساعت معتبر**).
- **`CLOCK_STATE`:** گذار collector بین `clock_ok` و نامعتبر (و برعکس) به‌صورت `EVENT(CLOCK_STATE)` با دلیل‌ها و offset هر منبع ثبت می‌شود. این ورودی اطلاعاتی است؛ تصمیم‌ها فقط از رکورد ساعت خودِ هر ورودی می‌آیند.
- **اثر قطعی ساعت (بدون backfill):** هر کندلی که در بازه‌ی نامعتبر بودن ساعت برسد `CLOCK_INVALID` است و برای همیشه «موجود نیست» می‌ماند؛ پس از بازیابی ساعت چیزی بازنویسی یا پر نمی‌شود. اثر آن: تصمیمی که پنجره‌ی ۲۸۸تایی‌اش چنین کندلی دارد `R06` و `R01` می‌گیرد (C.4)؛ outcome با چنین کندلی در پنجره‌ی forward بعد از `R + 86400 s` `UNRESOLVABLE_NON_REALTIME_BAR` می‌شود (C.6) و ADJUDICATION آن `E02` است (C.7). تصمیمی که ساعتِ خودش در لحظه‌ی نوشتن نامعتبر است `R08` می‌گیرد.
- `MALFORMED`، `FEED_MISMATCH`، `NON_REALTIME` و `CLOCK_INVALID` **هرگز** در feature، outcome یا audit استفاده نمی‌شوند و «اولین دریافت» را اشغال نمی‌کنند: اگر بعداً پیام معتبر و real-time (با ساعت معتبر) برای همان `open_time` برسد، آن `CANDLE` اول است. کندلی که فقط چنین ورودی‌هایی دارد «موجود نیست» حساب می‌شود. `v` و `V` به‌صورت رشته‌ی دریافتی ثبت می‌شوند و در هیچ محاسبه‌ای استفاده نمی‌شوند.
- **(r6)** هر `CANDLE` و هر `CANDLE_ANOMALY` (نه فقط `MALFORMED` و `FEED_MISMATCH`) `raw_message` و `raw_message_sha256` را نگه می‌دارد (B.3). متن خام حداکثر ۴۰۹۶ نویسه [P] است؛ متن بلندتر `MALFORMED [V01]` است و فقط ۴۰۹۶ نویسه‌ی اولش با `raw_truncated = true` ذخیره می‌شود، در حالی که `raw_message_sha256` همچنان SHA-256 بایت‌های UTF-8 **متن کامل** است. پیام غیرقابل‌parse هم همین‌طور ثبت می‌شود (`open_time_ms = null`).
- **REST backfill:** هر داده‌ای از REST (`/fapi/v1/klines`) یا از فایل تاریخی، یا هر کندلی که `feed_id` متفاوتی دارد، هرگز `CANDLE` نمی‌شود و در هیچ تصمیم، outcome یا audit استفاده نمی‌شود. کندلی که فقط از این مسیرها در دسترس باشد «موجود نیست» حساب می‌شود.
- هویت feed و پیکربندی (`feed_id`، `feed_url`، `stream_name`، حدها، `runtime_manifest`، `code_sha256`) قبل از T0 در `CONFIG` ثبت می‌شود و بعد تغییر نمی‌کند.
- **Warm-up:** هر تصمیم به ۲۸۸ کندل زنده‌ی قبل از خودش نیاز دارد؛ پس collector دست‌کم ۲۴ ساعت قبل از T0 شروع می‌شود (بند C.1-۴). **هیچ `p_raw` پیش از T0 در journal نوشته نمی‌شود.** dry-run ها به مخزن جدا می‌روند که خارج از شواهد است.

**KAT-8 (ساختگی، بدون اتصال شبکه):** پیام پایه M00: `e = "kline"`، `s = "BTCUSDT"`، `k.t = 1893456000000`، `k.T = 1893456299999`، `k.i = "5m"`، `k.o = "100000.10"`، `k.h = "100020.50"`، `k.l = "99990.00"`، `k.c = "100010.00"`، `k.v = "12.5"`، `k.V = "6.1"`، `k.x = true`؛ روی اتصال `feed_url`؛ `ingested_ms = k.t + 300000 + 800` (با `k.t` خودِ همان ردیف) و رکورد ساعت پایه‌ی B0 = (`SYNCHRONIZED`، offset `0`، age `1000`، step `0`)، پس `latency_ms = 800`. هر ردیف روی journal تازه اجرا می‌شود مگر نوشته شده باشد. **(r5)** ردیفی که `k.t` را عوض می‌کند `k.T` را هم متناسب (`k.t + 299999`) می‌کند، مگر خلافش نوشته شده باشد (M29).

| مورد | تغییر نسبت به M00 | نتیجه |
|---|---|---|
| M01 | بدون تغییر | `CANDLE` |
| M02 | `k.x = false` | دور ریخته می‌شود (بدون ورودی) |
| M03 | `s` و `k.s` برابر `ETHUSDT` | `MALFORMED` [V02] |
| M04 | `k.i = "1m"` | `MALFORMED` [V03] |
| M05 | `k.t = 1893456060000` (روی شبکه‌ی ۵ دقیقه نیست) | `MALFORMED` [V04] |
| M06 | `k.o = "NaN"` | `MALFORMED` [V05] |
| M07 | `k.h = "Infinity"` | `MALFORMED` [V05] |
| M08 | `k.l = "0"` | `MALFORMED` [V05] |
| M09 | `k.c = "-5.0"` | `MALFORMED` [V05] |
| M10 | `k.o = "1e5"` | `MALFORMED` [V05] |
| M11 | `k.h = "100005.00"` (کمتر از `k.c`) | `MALFORMED` [V06] |
| M12 | `k.l = "100005.00"` (بیشتر از `k.o`) | `MALFORMED` [V06] |
| M13 | `s` و `k.s` برابر `ETHUSDT` و `k.h = "99000.00"` | `MALFORMED` [V02, V06] |
| M14 | فیلد `k.h` وجود ندارد | `MALFORMED` [V01] |
| M15 | `k.x = "true"` (رشته) | `MALFORMED` [V01] |
| M16 | `ingested_ms = k.t + 300000 + 60001` | `NON_REALTIME` |
| M17 | `ingested_ms = k.t + 300000 + 60000` | `CANDLE` (حد شامل است) |
| M18 | `ingested_ms = k.t + 300000 − 5001` | `MALFORMED` [V07] |
| M19 | `ingested_ms = k.t + 300000 − 5000` | `CANDLE` (حد شامل است) |
| M20 | M01 و سپس M00 دوباره | `CANDLE` و سپس `DUPLICATE_IDENTICAL` |
| M21 | M01 و سپس M00 با `k.c = "100010.50"` | `CANDLE` و سپس `DUPLICATE_CONFLICT` |
| M22 | M05 (روی شبکه نیست) و سپس M01 (پیام پایه) | `MALFORMED` و سپس `CANDLE` (پیام نامعتبر جا را اشغال نمی‌کند) |
| M23 | فیلد `k.T` وجود ندارد | `MALFORMED` [V01] |
| M24 | `k.T = "1893456299999"` (رشته) | `MALFORMED` [V01] |
| M25 | `k.T = true` (boolean) | `MALFORMED` [V01] |
| M26 | `k.T = 1893456299999.0` (literal با نقطه‌ی اعشار) | `MALFORMED` [V01] |
| M27 | `k.T = k.t + 300000` (`1893456300000`) | `MALFORMED` [V08] |
| M28 | `k.T = k.t + 299998` (`1893456299998`) | `MALFORMED` [V08] |
| M29 | `k.t = 1893456060000` ولی `k.T` همان مقدار پایه `1893456299999` (نامتناسب) | `MALFORMED` [V04, V08] |
| M30 | پیام M00 با یک کلید اضافه‌ی سطح‌بالای `pad` که مقدارش `x` تکراری است، طوری که طول **کل متن JSON** برابر `4097` نویسه شود | `MALFORMED` [V01] (متن بلندتر از ۴۰۹۶ نویسه) |
| M31 | همان پیام M30 ولی با طول کل متن دقیقاً `4096` نویسه | `CANDLE` (حد شامل است؛ `raw_message` کامل ذخیره می‌شود) |

| مورد | `connection_url` | نتیجه |
|---|---|---|
| U1 | `wss://fstream.binance.com/market/ws/btcusdt@kline_5m` | `CANDLE` |
| U2 | `wss://fstream.binance.com/ws/btcusdt@kline_5m` (مسیر قدیمی) | `FEED_MISMATCH` |
| U3 | `wss://fstream.binance.com/market/ws/btcusdt@kline_1m` | `FEED_MISMATCH` |
| U4 | `wss://fstream.binance.com/market/ws/BTCUSDT@kline_5m` | `FEED_MISMATCH` |
| U5 | `wss://fstream.binance.com/market/stream?streams=btcusdt@kline_5m` | `FEED_MISMATCH` |
| U6 | `wss://fstream.binance.com/market/ws/btcusdt@kline_5m/` | `FEED_MISMATCH` |
| U7 | `CONFIG.feed_url` یا ثابت کد با رشته‌ی C.2 برابر نیست | collector شروع نمی‌شود |

**KAT-11 (ساختگی، بدون شبکه) — اعتبار ساعت در لحظه‌ی دریافت (اصلاح ۱ در r4):** پیام پایه‌ی M00 (KAT-8) روی اتصال `feed_url`؛ `T = k.t + 300000` (لحظه‌ی close؛ **نماد `T` بدون پیشوند فقط متغیر محلی این جدول است و با فیلد `k.T = k.t + 299999` پیام یکی نیست**). رکورد ساعت پایه‌ی B0 = (`SYNCHRONIZED`، offset `0`، age `1000`، step `0`). «U» یعنی `UNSYNCHRONIZED` با offset، age و step برابر `null`. هر ردیف روی journal تازه اجرا می‌شود مگر نوشته شده باشد. مورد CK02 دقیقاً حالت بازبینی GPT است: ساعت ۱۰ ثانیه عقب، پیام ۶۵ ثانیه دیر، latency خام ۵۵ ثانیه.

| مورد | ورودی | نتیجه |
|---|---|---|
| CK01 | `ingested_ms = T + 800`؛ B0 | `CANDLE` (`latency_ms = 800`) |
| CK02 | `ingested_ms = T + 55000`؛ offset `−10000` (latency خام ۵۵۰۰۰ «به‌موقع» می‌نمود؛ latency واقعی ۶۵۰۰۰ است) | `CLOCK_INVALID` [CK04] (هیچ latency ذخیره نمی‌شود؛ الگوریتم r3 اشتباهاً `CANDLE` می‌داد) |
| CK03 | `ingested_ms = T + 57000`؛ offset `−4000` | `NON_REALTIME` (latency اصلاح‌شده ۶۱۰۰۰؛ خام ۵۷۰۰۰ به‌موقع می‌نمود) |
| CK04 | `ingested_ms = T + 55000`؛ offset `−4000` | `CANDLE` (latency اصلاح‌شده ۵۹۰۰۰) |
| CK05 | `ingested_ms = T + 62000`؛ offset `+4000` | `CANDLE` (latency اصلاح‌شده ۵۸۰۰۰؛ خام ۶۲۰۰۰ به‌اشتباه `NON_REALTIME` می‌شد) |
| CK06 | `ingested_ms = T + 800`؛ U | `CLOCK_INVALID` [CK01] |
| CK07 | `ingested_ms = T + 800`؛ `UNKNOWN` (نمونه‌ای نیست) | `CLOCK_INVALID` [CK01] |
| CK08 | `ingested_ms = T + 800`؛ B0 با age `120001` | `CLOCK_INVALID` [CK02] |
| CK09 | `ingested_ms = T + 800`؛ B0 با age `120000` | `CANDLE` (حد شامل است) |
| CK10 | `ingested_ms = T + 800`؛ B0 با step `+251` | `CLOCK_INVALID` [CK03] |
| CK11 | `ingested_ms = T + 800`؛ B0 با step `−251` | `CLOCK_INVALID` [CK03] |
| CK12 | `ingested_ms = T + 800`؛ B0 با step `250` | `CANDLE` (حد شامل است) |
| CK13 | `ingested_ms = T + 5801`؛ offset `5001` | `CLOCK_INVALID` [CK04] |
| CK14 | `ingested_ms = T − 4201`؛ offset `−5001` | `CLOCK_INVALID` [CK04] |
| CK15 | `ingested_ms = T + 5800`؛ offset `5000` | `CANDLE` (latency ۸۰۰؛ حد شامل است) |
| CK16 | `ingested_ms = T + 800`؛ age `130000`، step `300`، offset `6000` | `CLOCK_INVALID` [CK02, CK03, CK04] (همه‌ی دلیل‌ها به ترتیب صعودی) |
| CK17 | M05 (`k.t` روی شبکه نیست)؛ U | `MALFORMED` [V04] (خطای داده بر ساعت مقدم است؛ latency `null`) |
| CK18 | `k.x = false`؛ U | دور ریخته می‌شود (بدون ورودی؛ ساعت اصلاً ارزیابی نمی‌شود) |
| CK19 | `connection_url` برابر U2 (مسیر قدیمی)؛ U | `FEED_MISMATCH` |
| CK20a | `ingested_ms = T − 5001`؛ B0 | `MALFORMED` [V07] |
| CK20b | `ingested_ms = T − 5001`؛ U | `CLOCK_INVALID` [CK01] (V07 بدون ساعت معتبر ارزیابی نمی‌شود) |
| CK21 | M01 با B0 (`T + 800`) و سپس همان پیام در `T + 900` با U | `CANDLE` و سپس `CLOCK_INVALID` [CK01] (تکراریِ با ساعت نامعتبر `DUPLICATE_*` نیست) |
| CK22 | همان پیام در `T + 800` با U و سپس در `T + 40800` با B0 | `CLOCK_INVALID` [CK01] و سپس `CANDLE` (ورودی `CLOCK_INVALID` جای اولین دریافت را نمی‌گیرد؛ latency ۴۰۸۰۰) |

**KAT-11b (ساختگی، سطح journal):** ساعت نامعتبر فقط در لحظه‌ی دریافت کندل `open = 2030-01-01T16:40:00Z` (کندل شماره‌ی ۲۰۰ از ابتدای 2030-01-01T00:00:00Z): همان کندل `CLOCK_INVALID` [CK01] و بدون `CANDLE` است؛ `DECISION` در `T0 = 2030-01-02T00:00:00Z` (پنجره‌ی feature شامل آن کندل) = `REJECTED` با `reject_reasons = ["R06","R01"]`، `reject_code = "R06"` و `feature_bar_count = 287`؛ با offset `6000` به‌جای نمونه‌ی نامعتبر، همان کندل `CLOCK_INVALID` [CK04] است. ساعت نامعتبر فقط در پنجره‌ی forward یک تصمیم ACCEPTED → `OUTCOME` = `UNRESOLVABLE_NON_REALTIME_BAR` با `outcome_reasons = ["UNRESOLVABLE_NON_REALTIME_BAR","UNRESOLVABLE_MISSING_BAR"]`، `Y = null` و ADJUDICATION = INELIGIBLE [E02] (نه RESOLVED، نه برچسب منفی). `DECISION` که ساعتش در لحظه‌ی نوشتن نامعتبر است: `reject_reasons = ["R08"]`؛ ترکیب کندل گمشده به‌خاطر ساعت، ثبت دیرهنگام و پرش ساعت: `["R06","R03","R08","R01"]`.

**KAT-11c (ساختگی، r6) — انتخاب `clock_offset_ms` از چند منبع و رکورد ساعت.** (الف) هر ردیف **یک دور نمونه‌برداری** است: فهرست `d` = offset گزارش‌شده‌ی منابع (ms؛ ساعت محلی − مرجع) به ترتیب `ntp_sources`؛ اولی منبع اصلی است و `null` یعنی منبعی پاسخ نداد. نتیجه وضعیت و `clock_offset_ms` طبق قاعده‌ی قطعی C.2 است (حساب با میکروثانیه‌ی صحیح).

| مورد | `d` (JSON) | نتیجه | توضیح |
|---|---|---|---|
| N01 | `[0.0, 0.0]` | `SYNCHRONIZED`، `clock_offset_ms = 0` | دو منبع هم‌نظر |
| N02 | `[12.4, 13.0]` | `SYNCHRONIZED`، `clock_offset_ms = 12` | فقط منبع اول: `u₀ = 12400`، `⌊(12400+500)/1000⌋ = 12` |
| N03 | `[12.5, 13.0]` | `SYNCHRONIZED`، `clock_offset_ms = 13` | نیم‌ها رو به بالا: `u₀ = 12500`، `⌊13000/1000⌋ = 13` |
| N04 | `[-12.5, -12.0]` | `SYNCHRONIZED`، `clock_offset_ms = -12` | `u₀ = −12500`، `⌊−12000/1000⌋ = −12` |
| N05 | `[-12.6, -12.0]` | `SYNCHRONIZED`، `clock_offset_ms = -13` | `u₀ = −12600`، `⌊−12100/1000⌋ = −13` |
| N06 | `[-0.5, 0.0]` | `SYNCHRONIZED`، `clock_offset_ms = 0` | `u₀ = −500`، `⌊0/1000⌋ = 0` |
| N07 | `[-0.51, 0.0]` | `SYNCHRONIZED`، `clock_offset_ms = -1` | `u₀ = −510`، `⌊−10/1000⌋ = −1` |
| N08 | `[0.49, 0.0]` | `SYNCHRONIZED`، `clock_offset_ms = 0` | `u₀ = 490`، `⌊990/1000⌋ = 0` |
| N09 | `[100.0, 1100.0]` | `SYNCHRONIZED`، `clock_offset_ms = 100` | اختلاف دقیقاً ۱۰۰۰ ms: حد شامل است |
| N10 | `[100.0, 1100.001]` | `UNSYNCHRONIZED`، `clock_offset_ms = null` | اختلاف ۱۰۰۰٫۰۰۱ ms (مقدار گردنشده به کار نمی‌رود) |
| N11 | `[1100.0, 100.0]` | `SYNCHRONIZED`، `clock_offset_ms = 1100` | offset فقط از منبع اول می‌آید، نه میانگین یا میانه |
| N12 | `[0.0, -1000.0]` | `SYNCHRONIZED`، `clock_offset_ms = 0` | اختلاف ۱۰۰۰ منفی: شامل |
| N13 | `[0.0, -1000.5]` | `UNSYNCHRONIZED`، `clock_offset_ms = null` | اختلاف بیش از ۱۰۰۰ |
| N14 | `[0.0, 1000.0, -1000.0]` | `SYNCHRONIZED`، `clock_offset_ms = 0` | سه منبع؛ هر کدام فقط با منبع اول مقایسه می‌شود (اختلاف دو منبع ثانویه ۲۰۰۰ است و بررسی نمی‌شود) |
| N15 | `[0.0, 0.0, 1000.5]` | `UNSYNCHRONIZED`، `clock_offset_ms = null` | منبع سوم از منبع اول بیش از ۱۰۰۰ فاصله دارد |
| N16 | `[null, 0.0]` | `UNSYNCHRONIZED`، `clock_offset_ms = null` | منبع اول جواب نداد |
| N17 | `[0.0, null]` | `UNSYNCHRONIZED`، `clock_offset_ms = null` | منبع ثانویه جواب نداد |
| N18 | `[NaN, 0.0]` | `UNSYNCHRONIZED`، `clock_offset_ms = null` | مقدار غیرمتناهی/NaN |
| N19 | `[0.0, Infinity]` | `UNSYNCHRONIZED`، `clock_offset_ms = null` | مقدار بی‌نهایت |
| N20 | `[5000.4, 5000.4]` | `SYNCHRONIZED`، `clock_offset_ms = 5000` | offset برابر ۵۰۰۰ (CK04 فقط برای بیش از ۵۰۰۰ است) |
| N21 | `[5000.5, 5000.5]` | `SYNCHRONIZED`، `clock_offset_ms = 5001` | offset گردشده ۵۰۰۱: `CK04` |
| N22 | `[0.0]` | `UNSYNCHRONIZED`، `clock_offset_ms = null` | کمتر از دو منبع |
| N23 | `[0.0, 1000.0004]` | `SYNCHRONIZED`، `clock_offset_ms = 0` | ابتدا به میکروثانیه گرد می‌شود: `u₁ = 1000000`، اختلاف دقیقاً `1000000` µs: شامل |
| N24 | `[0.0, 1000.0005]` | `UNSYNCHRONIZED`، `clock_offset_ms = null` | `u₁ = 1000001` (نیم رو به بالا): اختلاف بیش از حد |
| N25 | `[12.4996, 12.4996]` | `SYNCHRONIZED`، `clock_offset_ms = 13` | نخست `u₀ = 12500` (گرد به µs)، سپس `⌊13000/1000⌋ = 13`: ترتیب دو گرد کردن ثابت است |
| N26 | `[32.4995, 32.4995]` | `SYNCHRONIZED`، `clock_offset_ms = 33` | نمایش دهدهی `32.4995` یعنی `u₀ = 32500` و `⌊33000/1000⌋ = 33`؛ حساب دودویی (`32.4995 × 1000 = 32499.499999999996`) `u₀ = 32499` و offset `32` می‌داد: همین تله است |
| N27 | `[-32.5005, -32.5005]` | `SYNCHRONIZED`، `clock_offset_ms = -32` | نمایش دهدهی `−32.5005` یعنی `u₀ = −32500` و `⌊−32000/1000⌋ = −32`؛ حساب دودویی `−32500.500000000004` را به `u₀ = −32501` و offset `−33` می‌برد |

(ب) **رکورد ساعت پیام دریافت‌شده.** دور نمونه‌برداری `d = [0.0, 0.0]` با `mono_reply = 1 000 000 ms` و `wall_reply = 1893456000000 ms` است، مگر ردیف خلاف آن بگوید؛ پیام در `mono_now` و `wall_now` می‌رسد. سن و پرش از نمونه‌ی منبع اصلی سنجیده می‌شود (C.2 قاعده‌ی (۴)).

| مورد | حالت | نتیجه |
|---|---|---|
| CR1 | هنوز هیچ دورِ نمونه‌برداری کامل نشده است | `UNKNOWN`؛ `age_ms=null`؛ `step_ms=null`؛ `reasons=[CK01]` |
| CR2 | نمونه‌ی ۳۰ s پیش؛ ساعت دیواری و یکنوا هر دو ۳۰ s جلو رفته‌اند | `SYNCHRONIZED`؛ `age_ms=30000`؛ `step_ms=0`؛ `reasons=[]` |
| CR3 | همان، ولی ساعت دیواری ۵۰۰ ms پرش کرده (`step = +500`) | `SYNCHRONIZED`؛ `age_ms=30000`؛ `step_ms=500`؛ `reasons=[CK03]` |
| CR4 | همان، ولی ساعت دیواری ۳۰۰ ms به عقب پرش کرده (`step = −300`) | `SYNCHRONIZED`؛ `age_ms=30000`؛ `step_ms=-300`؛ `reasons=[CK03]` |
| CR5 | `step = 250` دقیقاً | `SYNCHRONIZED`؛ `age_ms=30000`؛ `step_ms=250`؛ `reasons=[]` |
| CR6 | `age = 120000` دقیقاً | `SYNCHRONIZED`؛ `age_ms=120000`؛ `step_ms=0`؛ `reasons=[]` |
| CR7 | `age = 120001` | `SYNCHRONIZED`؛ `age_ms=120001`؛ `step_ms=0`؛ `reasons=[CK02]` |
| CR8 | دور آخر UNSYNCHRONIZED است: offset، age و step هر سه `null` | `UNSYNCHRONIZED`؛ `age_ms=null`؛ `step_ms=null`؛ `reasons=[CK01]` |

**C.3 چرخه‌ی عمر رکورد — اصلاح ۲ (r2) و ۴ (r3):** سه وضعیت **جدا** هستند و هرگز با تغییر ورودی قدیمی ادغام نمی‌شوند:

| لایه | تصمیم‌گیرنده | زمان | ورودی journal |
|---|---|---|---|
| **اعتبار تصمیم** (`decision_validity`) | فقط اطلاعات موجود تا مهلت ثبت | `d + 120 s` تا `d + 900 s` | `DECISION` |
| **وضعیت outcome** (`outcome_status`) | فرایند resolution | از `R = d + 8h` | `OUTCOME` |
| **واجد شرایط بودن ارزیابی** (`eligibility`) | تابع قطعی (C.7) از ورودی‌های بالا | بعد از `R + 24 h` | `ADJUDICATION` |

- ورودی‌های `DECISION` و `OUTCOME` بعد از نوشته‌شدن **هرگز** بازنویسی، حذف یا اصلاح نمی‌شوند. اگر بعداً معلوم شود outcome ناقص یا conflict است، `ADJUDICATION` آن را با دلیل ثبت می‌کند، نه تغییر `DECISION`.
- معنای `ACCEPTED` ثابت است: «در زمان تصمیم، به‌موقع و از ورودی معتبر ثبت شد». این معنا هیچ‌وقت عوض نمی‌شود.
- **حالت pending ورودی ندارد، ولی ممنوعیت دارد:** تصمیمی که `OUTCOME` نهایی یا `AUDIT` ندارد «در انتظار» است (`PENDING_OUTCOME`، `PENDING_AUDIT`) و **هرگز** adjudicate نمی‌شود؛ نبودن `OUTCOME` یا `AUDIT` هیچ‌گاه `E02` یا `E04` نمی‌دهد (C.7). هر `OUTCOME` ثبت‌شده نهایی است: `RESOLVED` یا `UNRESOLVABLE_*`.
- **outcome حل‌نشده هرگز برچسب منفی نمی‌شود:** `OUTCOME` نهایی با `UNRESOLVABLE_*` دارای `Y = null` است و `ADJUDICATION` آن `INELIGIBLE` با `E02` است.

**C.4 رویه‌ی تصمیم و رد — اصلاح ۲ و ۳ (r2) و اصلاح ۳ (r3):**
- برای هر `d ≥ T0` دقیقاً یک `DECISION` وجود دارد (ACCEPTED یا REJECTED). نقطه‌ای که ورودی ندارد، نقض است.
- **نویسنده‌ی یکتا و قفل append:** journal را فقط یک فرایند writer می‌نویسد. خواندن سر journal، محاسبه و append ورودی `DECISION` همه زیر یک قفل append انجام می‌شوند و تصمیم فقط از ورودی‌های با `seq` **کوچک‌تر** از `seq` خودش استفاده می‌کند. بنابراین «قبل از ثبت» و «بعد از ثبت» فقط با `seq` تعریف می‌شود، نه با ساعت.
- **`origin = SCHEDULED`:** writer زنده در `d + 120 s` [P] شروع می‌کند: هویت کد/config، offset ساعت، و ۲۸۸ کندل real-time را بررسی و `p_raw` را محاسبه می‌کند. اگر کندلی کم باشد، هر ۱۵ ثانیه تکرار می‌کند. تا `d + 900 s` [P] اگر موفق شد، `ACCEPTED` ثبت می‌شود؛ اگر نه، در `d + 900 s` یک `REJECTED` با دلیل‌های داده ثبت می‌شود.
- **`origin = GAP_FILL`:** برای هر نقطه‌ی `d ≥ T0` که تا `d + 900 s` ورودی `DECISION` ندارد، رویه‌ی gap-fill (در شروع writer و در هر maintenance run، و قبل از هر ارزیابی) یک `REJECTED` با `reject_code = R04` می‌نویسد. این رکورد **هیچ محاسبه‌ای نمی‌کند**، و `p_raw`، `z`، `a`، `b`، range ها، `C_ref`، `feature_bar_count`، `feature_entries_digest` همه `null` هستند. **replay یا backfill ممنوع است.**

**کدهای رد در لایه‌ی تصمیم** (هر رد، همه‌ی دلیل‌های قابل‌اجرا را در `reject_reasons` می‌آورد، و `reject_code` اولین دلیل بر اساس ترتیب اولویت است):

| اولویت | کد | معنی |
|---|---|---|
| ۱ | `R04` | DOWNTIME: تصمیم SCHEDULED توسط writer زنده‌ای در مهلت نوشته نشد؛ رکورد post-hoc با `GAP_FILL` است |
| ۲ | `R07` | CODE_CONFIG_MISMATCH: `spec_sha256`، `code_sha256` یا `config_ref` با `T0_DECLARATION` نمی‌خواند |
| ۳ | `R06` | NON_REALTIME_BAR: برای دست‌کم یک `open_time` پنجره `CANDLE` وجود ندارد ولی `CANDLE_ANOMALY` از نوع `NON_REALTIME`، `MALFORMED`، `FEED_MISMATCH` یا `CLOCK_INVALID` با `seq` کوچک‌تر از `seq` تصمیم برای آن `open_time` ثبت شده |
| ۴ | `R03` | LATE_LOG: writer زنده بود ولی `recorded_at_utc > d + 900 s` |
| ۵ | `R08` | CLOCK_INVALID_AT_DECISION: رکورد ساعتِ لحظه‌ی نوشتن `DECISION` (C.2) `clock_ok` نیست؛ یعنی یکی از CK01..CK04 برقرار است (ساعت synchronized نیست، نمونه کهنه است، پرش ساعت، یا `|offset| > 5 s` [P]) |
| ۶ | `R01` | MISSING_FEATURE_BAR: کمتر از ۲۸۸ ورودی `CANDLE` (با `seq` کوچک‌تر از `seq` تصمیم) در پنجره |
| ۷ | `R02` | FEATURE_CONFLICT: دست‌کم یک کندل پنجره `DUPLICATE_CONFLICT` با `seq` **کوچک‌تر** از `seq` تصمیم دارد |

- **اولویت R03 در برابر R04:** نقطه‌ای که در downtime افتاده و بعداً gap-fill شده، چون بعد از مهلت نوشته می‌شود، هم R04 و هم R03 دارد؛ `reject_reasons = ["R04","R03"]` و `reject_code = "R04"`. R03 فقط وقتی `reject_code` است که ورودی را writer زنده‌ی SCHEDULED با تأخیر نوشته باشد و دلیلی با اولویت بالاتر نباشد.
- در مثال دلیل‌های چندگانه: writer زنده، کندل گمشده و ثبت دیرهنگام → `reject_reasons = ["R03","R01"]`، `reject_code = "R03"`.
- ترتیب عناصر `reject_reasons` همیشه ترتیب اولویت جدول بالا است: `R04 < R07 < R06 < R03 < R08 < R01 < R02`. مثال r4: کندل گمشده به‌خاطر `CLOCK_INVALID`، ثبت دیرهنگام و ساعت نامعتبر در لحظه‌ی تصمیم → `["R06","R03","R08","R01"]`، `reject_code = "R06"`. verifier `R08` را از رکورد ساعت ذخیره‌شده‌ی همان `DECISION` بازمحاسبه می‌کند (B.6 بند ۷).
- **کدهای بازنشسته‌ی r1:** کدهای `R05`، `R09`، `R10`، `R11` در r2 تخصیص داده نمی‌شوند و دوباره استفاده نمی‌شوند، چون به لایه‌ی دیگری رفته‌اند: `R05` (عدم تطابق audit) ← `E03`؛ `R09` و `R10` (کندل forward ناقص یا conflict) ← `UNRESOLVABLE_*` در `OUTCOME` (C.6)؛ `R11` (outcome pending) ← حالت pending بدون ورودی (C.3) و `E02`.
- **قاعده‌ی زمانی R02 و E06 (اصلاح ۳ در r3):**
  1. اگر `CANDLE_ANOMALY(DUPLICATE_CONFLICT)` برای کندلی از پنجره‌ی feature تصمیم با `seq` **کوچک‌تر** از `seq` تصمیم در journal باشد، تصمیم رد می‌شود: `R02` و `p_raw = null`.
  2. اگر conflict برای همان پنجره **فقط بعد از append شدن `DECISION`** برسد (`seq` بزرگ‌تر)، ورودی `DECISION` هرگز بازنویسی نمی‌شود و `R02` هرگز به‌صورت retroactive داده نمی‌شود. تصمیم ACCEPTED می‌ماند، conflict فقط یک `CANDLE_ANOMALY` است و `ADJUDICATION` با `E06` رکورد را INELIGIBLE می‌کند (C.7).
  3. قاعده‌ی مشابه برای outcome: conflict برای کندلی از پنجره‌ی forward با `seq` کوچک‌تر از `seq` ورودی `OUTCOME` → همان `OUTCOME` وضعیت `UNRESOLVABLE_CONFLICT` می‌گیرد؛ با `seq` بزرگ‌تر → `OUTCOME` (RESOLVED) بدون تغییر می‌ماند و `ADJUDICATION` با `E06` رکورد را INELIGIBLE می‌کند.
  4. `NON_REALTIME`، `MALFORMED`، `FEED_MISMATCH` و `DUPLICATE_IDENTICAL` بعد از ثبت هیچ اثری ندارند، چون کندل نمی‌سازند.
  5. verifier (B.6 بند ۷) همین قاعده را با `seq` بازمحاسبه می‌کند.
  6. با پارامترهای [P] فعلی، conflictی که در حد `latency` دریافت شود معمولاً پیش از `d + 120 s` ثبت می‌شود؛ حالت «بعد از `DECISION`» یا «بعد از `OUTCOME`» فقط وقتی رخ می‌دهد که append ورودی از لحظه‌ی دریافت عقب بیفتد (صف، downtime کوتاه writer). قاعده برای همین حالت و برای کامل بودن تعریف شده است، نه چون انتظار می‌رود زیاد رخ دهد.

**KAT-9a — ترتیب conflict (ساختگی):**

| مورد | ترتیب (`seq`) | نتیجه |
|---|---|---|
| S1 | conflict روی کندل پنجره‌ی feature، `seq` کوچک‌تر از `DECISION` | `DECISION` = REJECTED، `reject_reasons = ["R02"]`، `p_raw = null`؛ ADJUDICATION = INELIGIBLE [E01] |
| S2 | همان conflict، `seq` بزرگ‌تر از `DECISION` (قبل از R) | `DECISION` بدون تغییر ACCEPTED با `p_raw`؛ `OUTCOME` عادی؛ ADJUDICATION = INELIGIBLE [E06]؛ بدون `R02` |
| S3 | conflict روی کندل forward، `seq` کوچک‌تر از `OUTCOME` | `OUTCOME` = `UNRESOLVABLE_CONFLICT` با `Y = null`؛ ADJUDICATION = INELIGIBLE [E02] |
| S4 | conflict روی کندل forward، `seq` بزرگ‌تر از `OUTCOME` (RESOLVED) | `OUTCOME` بدون تغییر؛ ADJUDICATION = INELIGIBLE [E06] |
| S5 | `NON_REALTIME` یا `MALFORMED` برای کندل پنجره بعد از `DECISION` | بدون اثر؛ ELIGIBLE می‌ماند اگر شرط‌های دیگر برقرار باشد |
| S6 | conflict بعد از `ADJUDICATION` | رکورد تغییر نمی‌کند؛ verifier «ناهنجاری پس از adjudication» گزارش می‌کند |


**C.5 قاعده‌ی `p_raw` — اصلاح ۳:**
- برای هر نقطه‌ی ساعتی یک رکورد وجود دارد. `p_raw` در رکورد canonical فقط وقتی غیر `null` است که **همه‌ی این‌ها** برقرار باشند: محاسبه و ثبت در مهلت (`recorded_at_utc ≤ d + 900 s`) از ۲۸۸ کندل real-time معتبر؛ هویت کد/config درست؛ ساعت درست؛ `origin = SCHEDULED`.
- ناوردایی: `p_raw ≠ null ⇔ decision_validity = ACCEPTED`. هر رکورد REJECTED مقدار `p_raw = null` دارد و همین برای همیشه می‌ماند.
- هیچ محاسبه‌ی دیرهنگام، replay، backfill یا بازمحاسبه نمی‌تواند رکورد REJECTED را ترمیم کند. `AUDIT` فقط برای تصمیم ACCEPTED نوشته می‌شود.
- `p_raw` همیشه (برای هر `d ≥ T0` که شرایط بالا را دارد) ثبت می‌شود، بدون هیچ گیت هشدار.

**C.6 Resolution و outcome (شرط ۶) — با اصلاح ۴ (r3):**
- `OUTCOME` فقط برای تصمیم ACCEPTED نوشته می‌شود و فقط وقتی `now ≥ R = d + 8h`. هر `OUTCOME` ثبت‌شده **نهایی** است (`RESOLVED` یا `UNRESOLVABLE_*`)؛ وضعیت میانی ثبت نمی‌شود.
- **finalizer** (قطعی و idempotent): برای هر تصمیم ACCEPTED که `OUTCOME` ندارد و `now ≥ R + 900 s` [P]:
  1. اگر هر ۹۶ کندل forward (`open ∈ [d, d + 7h55m]`) به‌صورت `CANDLE` موجودند و هیچ‌کدام `DUPLICATE_CONFLICT` با `seq` کوچک‌تر از `seq` این `OUTCOME` ندارند → `OUTCOME` با `outcome_status = RESOLVED` و `Y` طبق A.6؛
  2. وگرنه اگر `now ≥ R + 86400 s` [P] → `OUTCOME` نهایی با یکی از `UNRESOLVABLE_CONFLICT`، `UNRESOLVABLE_NON_REALTIME_BAR` (کندل ندارد ولی `NON_REALTIME`، `MALFORMED`، `FEED_MISMATCH` یا `CLOCK_INVALID` برای آن `open_time` ثبت شده)، `UNRESOLVABLE_MISSING_BAR` (کمتر از ۹۶ کندل) با همین ترتیب اولویت، `outcome_reasons` شامل همه‌ی دلیل‌ها، و `Y = null`؛
  3. وگرنه تصمیم `PENDING_OUTCOME` می‌ماند و هیچ ورودی نوشته نمی‌شود.
- finalizer در هر maintenance و در فاصله‌ی `R + 900 s` تا `R + 86400 s` ساعتی اجرا می‌شود.
- **Early resolution ممنوع:** حتی اگر قبل از R شرط `Y = 1` برقرار شده باشد، `OUTCOME` زودتر نوشته نمی‌شود.
- `OUTCOME` شامل `c_ref_used` است که باید با `C_ref` تصمیم برابر باشد (C.7).
- **ترتیب finalization → adjudication (اصلاح ۴):** مرحله‌ی finalize در maintenance (C.7) همیشه پیش از adjudicate است و `ADJUDICATION` فقط از `OUTCOME` نهایی ساخته می‌شود. نبودن موقتی `OUTCOME` (مثلاً چون finalizer هنوز اجرا نشده یا شکست خورده) هرگز `E02` نمی‌دهد؛ `E02` فقط برای `OUTCOME` نهایی با `UNRESOLVABLE_*` است.
- **شکست یا ناتمام ماندن finalization، بدون duplicate یا بازنویسی:**
  1. خطای finalizer (exception، شبکه، دیسک) هیچ `OUTCOME` نمی‌نویسد؛ فقط `EVENT(FINALIZER_ERROR)` با `decision_seq` و دلیل ثبت می‌شود. تصمیم `PENDING_OUTCOME` می‌ماند، adjudicate نمی‌شود و maintenance بعدی دوباره تلاش می‌کند.
  2. **کلید یکتایی:** برای هر `decision_seq` حداکثر یک `OUTCOME` (و یک `AUDIT` و یک `ADJUDICATION`) وجود دارد. finalizer قبل از append مجموعه‌ی «در انتظار» را از خودِ journal بازمحاسبه می‌کند (نه از حافظه)، پس بعد از restart تکرار یا بازنویسی رخ نمی‌دهد. ورودی دوم با همان کلید نامعتبر است: اولی معتبر می‌ماند، دومی نادیده گرفته می‌شود و `EVENT(DEVIATION)` لازم دارد.
  3. خط نیمه‌نوشته طبق B.2 بند ۷ «ورودی» نیست؛ بعد از restart writer زنجیره را verify (B.6) و finalizer از روی journal ادامه می‌دهد.
  4. تصمیمی که از `R + 86400 s` گذشته و هنوز `OUTCOME` ندارد نقض عملیاتی است (verifier گزارش می‌کند)، نه `E02`.

**C.7 Audit و adjudication — اصلاح ۲ (r2) و اصلاح ۴ (r3):**
- **maintenance run** هر شب در `00:30:00 UTC` [P] با ترتیب **ثابت و ترتیبی** اجرا می‌شود؛ هر مرحله فقط بعد از append و fsync شدن همه‌ی ورودی‌های مرحله‌ی قبل شروع می‌شود:
  1. **gap-fill** (C.4)؛
  2. **finalize:** finalizer C.6 برای همه‌ی تصمیم‌های ACCEPTED که `OUTCOME` ندارند؛
  3. **audit:** برای همه‌ی تصمیم‌های ACCEPTED که `AUDIT` ندارند؛
  4. **adjudicate:** برای هر `DECISION` بدون `ADJUDICATION` که `now ≥ R + 86400 s` باشد و پیش‌شرط FJ-ADJ-1 برقرار باشد؛
  5. `CHECKPOINT`؛
  6. انتشار خارجی (B.7).
  بنابراین `OUTCOME` نهایی همیشه seq کوچک‌تر از `ADJUDICATION` دارد. در مرز `R + 86400 s` هم finalizer (مرحله‌ی ۲) قبل از adjudicator (مرحله‌ی ۴) در همان run اجرا می‌شود. finalizer در فاصله‌ی R+900s تا R+86400s ساعتی هم اجرا می‌شود، ولی `ADJUDICATION` فقط در maintenance نوشته می‌شود.
- **AUDIT:** برای هر تصمیم ACCEPTED، در اولین maintenance بعد از `d + 900 s`، کد audit (مسیر کد مستقل از مسیر زنده در صورت امکان؛ `auditor_code_sha256` ثبت می‌شود) از ورودی‌های `CANDLE` journal `p_audit` را بازمحاسبه می‌کند. `abs_diff = |p_raw − p_audit|`؛ `MATCH` اگر `abs_diff ≤ 1e−6` [P]؛ در غیر این صورت `MISMATCH`؛ اگر محاسبه ممکن نبود `NOT_COMPUTABLE`. `AUDIT` نهایی است: `NOT_COMPUTABLE` یک وضعیت ثبت‌شده است، نه «هنوز اجرا نشده». `p_raw` با `p_audit` جایگزین نمی‌شود.
- **ADJUDICATION** با قاعده‌ی قطعی `FJ-ADJ-1`. تابع فقط ورودی‌های journal با `seq` **کوچک‌تر** از `seq` همان `ADJUDICATION` را می‌خواند:

```
def FJ_ADJ_1(decision, outcome, audit, journal_before_this_entry):
    if decision.decision_validity == "REJECTED":
        return ("INELIGIBLE", ["E01"])
    if outcome is None or audit is None:
        return PENDING          # هیچ ADJUDICATION نوشته نمی‌شود؛ E02 و E04 هرگز برای «نبودنِ» داده داده نمی‌شوند
    reasons = []
    if outcome.outcome_status != "RESOLVED" or outcome.recorded_at_utc < R:   reasons += ["E02"]
    if audit.audit_status == "MISMATCH":                                      reasons += ["E03"]
    if audit.audit_status == "NOT_COMPUTABLE":                                reasons += ["E04"]
    if outcome.outcome_status == "RESOLVED" and outcome.c_ref_used != decision.C_ref:  reasons += ["E05"]
    if exists CANDLE_ANOMALY(DUPLICATE_CONFLICT) x with x.seq < adjudication.seq and (
         (x.open_time in feature_window(decision) and x.seq > decision.seq) or
         (outcome.outcome_status == "RESOLVED" and x.open_time in forward_window(decision) and x.seq > outcome.seq)):
                                                                               reasons += ["E06"]
    return ("ELIGIBLE" if reasons == [] else "INELIGIBLE", reasons)
```

| کد | معنی |
|---|---|
| `E01` | DECISION_REJECTED |
| `E02` | OUTCOME_UNRESOLVED: `OUTCOME` نهایی با `UNRESOLVABLE_*` (یا نوشته‌شده زودتر از R) |
| `E03` | AUDIT_MISMATCH |
| `E04` | AUDIT_NOT_COMPUTABLE (نه «AUDIT هنوز نیست») |
| `E05` | REF_INCONSISTENT |
| `E06` | CONFLICT_AFTER_LOGGING: conflict با `seq` بعد از `DECISION` (پنجره‌ی feature) یا بعد از `OUTCOME` (پنجره‌ی forward) |

- `ineligibility_reasons` به ترتیب `E01 < E02 < … < E06` مرتب است. `ADJUDICATION` برای هر `decision_seq` حداکثر یک‌بار نوشته می‌شود و پس از نوشته‌شدن نهایی است.
- **PENDING:** تصمیم ACCEPTED بدون `OUTCOME` نهایی (`PENDING_OUTCOME`) یا بدون `AUDIT` (`PENDING_AUDIT`) adjudicate نمی‌شود؛ maintenance بعدی دوباره امتحان می‌کند. تصمیمی که از `R + 86400 s` گذشته و هنوز PENDING است نقض عملیاتی است که verifier جدا گزارش می‌کند؛ تا نوشته‌شدن `ADJUDICATION` در `e_i = 0` و شمارش «بدون adjudication» می‌ماند (C.12).
- **conflict بعد از ADJUDICATION** آن را تغییر نمی‌دهد؛ verifier آن را «ناهنجاری پس از adjudication» (اطلاعاتی) گزارش می‌کند.
- **اصلاح خطا:** ورودی `ADJUDICATION` فقط وقتی معتبر است که با بازمحاسبه‌ی این تابع روی ورودی‌های با `seq` کوچک‌تر برابر باشد. در غیر این صورت بازمحاسبه حاکم است و یک `EVENT(DEVIATION)` ثبت می‌شود. ورودی قدیمی حذف نمی‌شود.

**KAT-6 — eligibility (ساختگی):**

| validity | outcome | audit | `c_ref` | conflict بعدی | نتیجه | دلایل |
|---|---|---|---|---|---|---|
| ACCEPTED | RESOLVED | MATCH | برابر | ندارد | ELIGIBLE | — |
| REJECTED | — | — | — | — | INELIGIBLE | E01 |
| ACCEPTED | UNRESOLVABLE_MISSING_BAR | MATCH | — | ندارد | INELIGIBLE | E02 (نه برچسب منفی) |
| ACCEPTED | RESOLVED | MISMATCH | برابر | ندارد | INELIGIBLE | E03 |
| ACCEPTED | RESOLVED | NOT_COMPUTABLE | برابر | ندارد | INELIGIBLE | E04 |
| ACCEPTED | RESOLVED | MISMATCH | نابرابر | دارد (بعد از `DECISION`) | INELIGIBLE | E03, E05, E06 |
| ACCEPTED | ندارد | MATCH | — | — | PENDING (هیچ ورودی) | — |
| ACCEPTED | RESOLVED | ندارد | برابر | — | PENDING (هیچ ورودی) | — |

**KAT-9b — ترتیب finalization و adjudication (ساختگی):**

| مورد | سناریو | نتیجه |
|---|---|---|
| F1 | maintenance در مرز `R + 86400 s`؛ پنجره‌ی forward ناقص | در همان run اول `OUTCOME(UNRESOLVABLE_MISSING_BAR)` و بعد `ADJUDICATION(E02)`؛ `seq(OUTCOME) < seq(ADJUDICATION)` |
| F2 | خطای تزریق‌شده در finalizer در run مرزی | `EVENT(FINALIZER_ERROR)` با `decision_seq`؛ هیچ `OUTCOME` و هیچ `ADJUDICATION` نوشته نمی‌شود؛ تصمیم `PENDING_OUTCOME`؛ run بعدی ابتدا `OUTCOME` و بعد `ADJUDICATION` می‌نویسد؛ هیچ ورودی تکراری یا بازنویسی‌شده‌ای نیست |
| F3 | crash بعد از append شدن `OUTCOME` و قبل از `ADJUDICATION` | بعد از restart (و verify زنجیره) فقط `ADJUDICATION` نوشته می‌شود؛ `OUTCOME` دوم نوشته نمی‌شود |
| F4 | تلاش برای `OUTCOME` دوم برای همان `decision_seq` | نامعتبر: اولی حاکم؛ writer نمی‌نویسد، و اگر نوشته شده باشد verifier `DEVIATION` می‌دهد |
| F5 | `AUDIT` تا لحظه‌ی adjudication نیست | `PENDING_AUDIT`: بدون `ADJUDICATION` و بدون E04؛ اگر `AUDIT(NOT_COMPUTABLE)` موجود باشد → E04 |
| F6 | `OUTCOME` RESOLVED زود (در `R + 900 s`) نوشته شده | `ADJUDICATION` تا اولین maintenance با `now ≥ R + 86400 s` منتظر می‌ماند؛ conflict رسیده در این فاصله `E06` می‌دهد |

**C.8 داده‌ی ناقص، تکراری، دیرکرد، نامعتبر، restart (شرط ۱۰):**
- **کندل گمشده:** هرگز پر، درون‌یابی یا کپی نمی‌شود. feature ناقص → `R01`. outcome ناقص → `UNRESOLVABLE_MISSING_BAR`.
- **تکراری یکسان:** `CANDLE_ANOMALY(DUPLICATE_IDENTICAL)`؛ بدون اثر.
- **conflict:** مقدار اول می‌ماند و فقط ترتیب `seq` تعیین‌کننده است (قاعده‌ی زمانی C.4): conflict با `seq` کوچک‌تر از `DECISION` → `R02` برای همان تصمیم؛ با `seq` کوچک‌تر از `OUTCOME` → `UNRESOLVABLE_CONFLICT`؛ conflict بعد از نوشته‌شدن `DECISION` یا `OUTCOME` هرگز آن ورودی را تغییر نمی‌دهد و اثرش فقط `E06` در ADJUDICATION است (C.7).
- **کندل دیرکرده یا نامعتبر:** `NON_REALTIME`، `MALFORMED`، `FEED_MISMATCH` و `CLOCK_INVALID` کندل نمی‌سازند و غیرقابل‌استفاده‌اند (C.2)؛ تصمیمی که به همین دلیل کندل کم دارد `R06` و `R01` می‌گیرد. کندلی که بعد از لحظه‌ی ثبت برسد (ولی معتبر و real-time باشد) روی تصمیم قبلی اثری ندارد و تصمیم را ترمیم نمی‌کند.
- **Restart / outage:** نقطه‌های جاافتاده با `GAP_FILL` و `R04` (C.4) ثبت می‌شوند. writer در شروع، زنجیره را کامل verify می‌کند (B.6)، `EVENT(RESTART)` می‌نویسد، و از نقطه‌ی بعدی ادامه می‌دهد؛ تصمیم‌ها یکتا هستند. restart همه‌ی اتصال‌ها را قطع می‌کند: collector با `FEED_CONNECT` تازه و عمر صفر ادامه می‌دهد (C.16) و کندل‌های بازه‌ی restart، بدون REST و بدون backfill، برای همیشه گم می‌مانند. verify ناموفق → writer هیچ ورودی تصمیمی نمی‌نویسد تا اپراتور `DEVIATION` ثبت کند.
- **ساعت (اصلاح ۱ در r4):** ساعت در **دو جا** سنجیده می‌شود و هر دو با رکورد ساعت ذخیره‌شده‌ی همان ورودی قابل بازمحاسبه‌اند: در لحظه‌ی دریافت هر کندل (C.2: `CLOCK_INVALID`، latency اصلاح‌شده با offset) و در لحظه‌ی نوشتن هر `DECISION` (`R08`). قطع ساعت یعنی کندل‌های آن بازه برای همیشه گم‌اند (بدون REST و بدون backfill)؛ یک قطع ۲۴ ساعته‌ی ساعت می‌تواند تا ۲۴ تصمیم ساعتی را `R06/R01` کند و یک کندل گمشده تا ۲۴ تصمیم بعدی را (پنجره‌ی ۲۸۸تایی)؛ این هزینه‌ی پذیرفته‌شده‌ی طراحی است، نه خطای قابل‌ترمیم.

**C.9 جداسازی پیش‌بینی از تصمیم انسانی (شرط ۱۴):** `human_journal` جدا است (B.4). هیچ ورودی انسانی نمی‌تواند هیچ فیلد `DECISION`، `OUTCOME`، `AUDIT` یا `ADJUDICATION` را تغییر دهد. متریک‌های مدل فقط از ورودی‌های ELIGIBLE journal اصلی می‌آیند.

**C.10 Threshold های UI و TradingView (شرط ۸ و ۹):**
- این spec هیچ threshold هشدار انتخاب نمی‌کند.
- هر threshold نمایشی (UI یا TradingView) یک config جدا است، hash دارد و هر تغییرش به‌صورت `EVENT(UI_CONFIG_CHANGE)` ثبت می‌شود.
- در دوره‌ی forward هیچ threshold نمایشی برای بهتر دیده شدن نتایج تغییر نمی‌کند. هر تغییر یک amendment است.
- تعداد هشدارهای نمایشی هیچ متریکی نیست.

**C.11 فهرست ممنوعیت‌ها:**
- تغییر وزن، ثابت یا عدد ۱.۰۲؛ انتخاب threshold؛ تغییر شبکه‌ی ساعتی.
- logging انتخابی، حذف یا بازنویسی ورودی.
- ساختن `p_raw` برای رکورد REJECTED؛ replay یا backfill برای downtime.
- استفاده از REST، فایل تاریخی یا feed دیگر برای ساخت `CANDLE`.
- شمردن outcome حل‌نشده به‌عنوان ۰ یا ۱.
- توقف زودهنگام به دلیل نتیجه.
- استفاده از تصمیم انسانی برای تغییر پیش‌بینی.
- ادعای «پاک» برای ترکیب نتایج forward با confirmation قبلی.

**C.12 متریک‌ها و فاصله‌ی اطمینان (شرط ۱۱) — اصلاح ۶ (r2)، اصلاح ۱ (r3) و اصلاح ۲ (r4):**

**شبکه‌ی کامل و مجموعه‌ی ارزیابی (r3):**
- `S` = لحظه‌ی برش تحلیل (UTC)؛ پیش از دیدن هر متریک `p`–`Y` در manifest تحلیل ثبت می‌شود (C.14، C.17). `P` = `seq` ورودی prefix تحلیل (C.17): **آخرین** `CHECKPOINT` که طبق رکورد مقصد (زمان مقصد، نه ساعت نویسنده) تا `S` منتشر شده، یعنی `published_at_utc ≤ S`.
- **شبکه‌ی کامل:** `d_i = T0 + i · 1 h` برای `i = 0 … N_G − 1` با `N_G = floor((S − T0 − 32 h) / 1 h) + 1`، یعنی همه‌ی نقطه‌هایی که `d_i + 8 h + 24 h ≤ S` (زمان adjudication‌شان رسیده است). اگر `N_G ≤ 0` ارزیابی وجود ندارد. **زمان پایانی شبکه** `d_{N_G−1}` است؛ نقطه‌های بعد از آن بیرون ارزیابی‌اند و «موقعیت خالی» نیستند.
- **ماسک:** `e_i = 1` اگر **اولین `ADJUDICATION` برای `d_i` که `seq ≤ P` دارد** `ELIGIBLE` است (C.17)؛ در غیر این صورت `e_i = 0` (REJECTED، GAP_FILL، outcome حل‌نشده، ineligible، بدون adjudication **تا prefix**، گمشده). `N_E = Σ e_i`. `p_i` و `Y_i` فقط برای `e_i = 1` تعریف‌اند. **هیچ موقعیتی از شبکه حذف یا فشرده نمی‌شود.**

**برش as-of-S (r5):** همه‌ی ورودی‌های محاسبه (`p_raw` از `DECISION`، `Y` از `OUTCOME`، `eligibility` از `ADJUDICATION`) فقط از ورودی‌های journal با `seq ≤ P` خوانده می‌شوند؛ هر ورودی با `seq > P` نادیده است، چه پیش از `S` append شده باشد (دم anchor‌نشده، B.7 بند ۶) چه بعد از آن. تصمیمی که در `P` هنوز PENDING است یا `DECISION` ندارد `e_i = 0` است و در گزارش جداگانه به‌عنوان «در prefix ناموجود» شمرده می‌شود (C.17)، و با اجرای مجدد هم همین‌طور می‌ماند، حتی اگر `ADJUDICATION` آن بعداً (با `seq > P`) نوشته شود. **پیامد صادقانه:** چون `P` تا حدود یک دوره‌ی maintenance (۲۴ ساعت) به‌علاوه‌ی تأخیر انتشار پیش از `S` است و `ADJUDICATION` فقط در maintenance شبانه نوشته می‌شود، آخرین بخش شبکه (تا حدود ۲۴ ساعت و بیشتر اگر انتشار عقب بماند) معمولاً `e = 0` است؛ این در گزارش آشکار می‌شود. جزئیات، manifest و آزمون‌ها: C.17 و KAT-12.

**متریک‌ها (برآورد نقطه‌ای روی همه‌ی موقعیت‌های `e_i = 1`):**
1. `n_grid = N_G`، `n_accepted`، `n_eligible = N_E` و شمارش دلیل‌های E01..E06 و R01..R08، و شمار تصمیم‌های در انتظار (PENDING).
2. **Event rate** = `mean(Y)`.
3. **Mean p** = `mean(p_raw)`.
4. **Brier** = `mean((p_raw − Y)²)`.
5. **LogLoss** = `−mean(Y·ln p̃ + (1−Y)·ln(1−p̃))`، با `p̃ = clip(p_raw, 1e−9, 1−1e−9)`.
6. **Calibration-in-the-large:** شیفت `c` که `Σ σ(logit(p̃_i) + c) = Σ Y_i` را حل می‌کند. همراه با `mean(p) − mean(Y)` گزارش می‌شود.
7. **Calibration slope:** رگرسیون لجستیک بدون regularization از `Y` روی `logit(p̃)` (intercept و slope) با روش Newton؛ گزارش intercept و slope.
8. **AUC:** Mann–Whitney با rank میانگین برای tie.
9. **Valid alerts:** این spec هشدار مدل ندارد؛ شمارش آن N/A است. تعداد هشدار نمایشی متریک نیست.
10. **Valid evaluations** = `N_E`.

**Bootstrap توصیفی — بلوک‌های متوالی از شبکه‌ی کامل (قطعی و قابل بازتولید):**
- برای هر `L ∈ {32, 48, 64, 96, 128}` با `N_G ≥ L`، `B = 4000`، `nb = ceil(N_G / L)`. اگر `N_G < L` آن طول گزارش نمی‌شود.
- RNG: برای هر `L` یک `numpy.random.default_rng(seed)` تازه با `seed = 20261000 + L` که در طول `B` تکرار ادامه می‌یابد.
- **شروع‌های مجاز بلوک:** `s ∈ {0, …, N_G − L}`. در هر تکرار `starts = rng.integers(0, N_G − L + 1, size=nb)`.
- **نمایش بلوک:** هر بلوک `L` موقعیت **متوالی ساعتی** `s, s+1, …, s+L−1` از شبکه‌ی کامل است و موقعیت‌های `e = 0` را هم شامل می‌شود: آن‌ها زمان را اشغال می‌کنند ولی مشاهده‌ای نمی‌دهند.
- **الحاق و برش:** `idx = concatenate([s_j + arange(L) for s_j in starts])[:N_G]`. بلوک‌ها بدون حذف جا پشت‌سرهم می‌آیند و دنباله از انتها بریده می‌شود تا طولش دقیقاً `N_G` باشد. نمونه‌گیری با جایگذاری است؛ یک موقعیت می‌تواند چند بار بیاید و هر بار شمرده می‌شود.
- **مشاهدات تکرار:** `M = [i for i in idx if e_i = 1]` به همان ترتیب؛ متریک روی `(p[M], Y[M])` محاسبه می‌شود. `|M|` بین تکرارها متغیر است و لزوماً `N_E` نیست.
- **تکرار skip‌شده:** اگر `|M| = 0`، همه‌ی متریک‌ها skip می‌شوند. اگر `M` فقط یک کلاس دارد (`ΣY = 0` یا `ΣY = |M|`)، `AUC`، شیفت `c` و slope/intercept skip می‌شوند. slope/intercept همچنین skip می‌شود اگر `logit(p̃)` کلاس‌ها را کامل جدا کند، `var(logit(p̃)) = 0` باشد، یا Newton در ۶۰ تکرار با `max|step| < 1e−10` همگرا نشود. Brier، LogLoss، mean p و event rate برای هر تکرار با `|M| ≥ 1` محاسبه می‌شوند.
- **گزارش:** برای هر متریک و هر `L`: `skipped`، `B_eff = B − skipped`، و بازه‌ی ۹۵٪ = `numpy.percentile(values, [2.5, 97.5], method="linear")` روی `B_eff` مقدار باقی‌مانده به ترتیب تکرار. اگر `B_eff < 0.95 · B` [P]، بازه گزارش **نمی‌شود** و `UNRELIABLE (B_eff = …)` نوشته می‌شود. شمار skip همیشه گزارش می‌شود.
- **هر پنج طول بلوک گزارش می‌شود؛ هیچ‌کدام «اصلی» نیست.** طول بلوک اصلی برای هر gate pass/fail فقط در spec جدای gate می‌آید، قبل از ارزیابی رسمی hash می‌شود، و نباید بعد از دیدن متریک‌ها انتخاب شود.
- نسخه‌ی numpy در `runtime_manifest` ارزیابی ثبت می‌شود؛ جریان `Generator` بین نسخه‌ها تضمین نشده است.
- **چرا شبکه‌ی کامل:** `L = 32` باید ۳۲ ساعت تقویمی پیوسته باشد. فشرده‌کردن `E` دو رکوردی را که چند ساعت از هم فاصله دارند «متوالی» نشان می‌دهد و هم‌پوشانی ۷ از ۸ ساعت outcome را در بازنمونه‌گیری خراب می‌کند. رکوردهای ساعتی متوالی ۷ از ۸ ساعت پنجره‌ی outcome مشترک دارند؛ نمونه‌ی مستقل مؤثر تقریباً `N_E / 8` است.

**KAT-5 (ساختگی، `N_G = N_E = 1000`، همه‌ی موقعیت‌ها ELIGIBLE؛ در این حالت الگوریتم شبکه‌ی کامل با الگوریتم r2 یکی است):** `p_i = (1 + ((37i) mod 97)) / 100`؛ `Y_i = 1` اگر `((53i + 17) mod 101) / 101 < p_i` وگرنه ۰ (`i = 0..999`). مقدارها: `ΣY = 493`، `mean(p) = 0.48911`، `event rate = 0.493`، `mean(p) − mean(Y) = −0.00389`، `Brier = 0.1711357`، `LogLoss = 0.512560944004627`، شیفت `c = 0.0227013837968`، intercept `= 0.0227771930353`، slope `= 1.00389618249`، `AUC = 0.824241551344063`. bootstrap با `L = 32`، `seed = 20261032`، `numpy 2.5.3`: ۸ مقدار اول `starts` برابر `[966, 873, 65, 589, 966, 879, 172, 420]` و بازه‌ی ۹۵٪ Brier برابر `[0.1632745425, 0.1806229325]` است (وابسته به نسخه‌ی numpy).

**KAT-7 (ساختگی) — bootstrap روی شبکه‌ی کامل با ساعت‌های خالی.**

(الف) **بردار دستی با `starts` اجباری** (مستقل از RNG و نسخه‌ی numpy): `N_G = 12`؛ `e = [1,1,1,0,0,0,1,1,1,1,0,1]`؛ `p = [0.2, 0.8, 0.5, –, –, –, 0.1, 0.9, 0.7, 0.3, –, 0.6]`؛ `Y = [0,1,1, –,–,–, 0,1,1,0, –, 1]` (موقعیت‌های `e = 0` مقدار ندارند).

| مورد | `L` | `starts` اجباری | `idx` پس از الحاق و برش | `M` | `n_M` | Brier | AUC | slope | `c` |
|---|---|---|---|---|---|---|---|---|---|
| A | 4 | [2, 8, 5] | [2,3,4,5,8,9,10,11,5,6,7,8] | [2,8,9,11,6,7,8] | 7 | 0.1 | 1 | skip (جداسازی کامل) | 1.00709353665207 |
| B | 3 | [3, 3, 3, 3] | [3,4,5] چهار بار | [ ] | 0 | skip | skip | skip | skip |
| C | 4 | [3, 3, 3] | [3,4,5,6] سه بار | [6,6,6] | 3 | 0.01 | skip (یک کلاس) | skip | skip |
| D | 4، `N_G = 10` (موقعیت‌های ۰ تا ۹) | [6, 0, 2] | [6,7,8,9,0,1,2,3,2,3] (طول ۱۲ → برش به ۱۰) | [6,7,8,9,0,1,2,2] | 8 | 0.0975 | 1 | skip (جداسازی کامل) | 0.715412361496487 |

مورد B نشان می‌دهد بلوکی که کاملاً در یک بازه‌ی خالی افتاده مشاهده‌ای نمی‌دهد و به موقعیت‌های بعدی نمی‌چسبد؛ در الگوریتم فشرده‌ی r2 چنین چیزی ممکن نبود. هر بلوک در ستون `idx` از اعداد متوالی تشکیل شده است.

(ب) **بردار با RNG و ساعت خالی:** `p_i` و `Y_i` همان KAT-5 برای `i = 0..999`؛ `N_G = 1000`؛ `e_i = 0` اگر `i mod 11 = 0` یا `300 ≤ i < 340` (۱۲۸ موقعیت خالی، از جمله یک قطعی ۴۰ ساعته)، پس `N_E = 872`. برآورد نقطه‌ای: Brier `= 0.172077522935780`، AUC `= 0.822410264773498`. با `L = 32`، `seed = 20261032`، `B = 4000` و numpy 2.5.3: ۸ مقدار اول `starts` همان KAT-5 است چون `N_G` برابر است: `[966, 873, 65, 589, 966, 879, 172, 420]`؛ `|M|` در تکرارها بین ۷۳۷ و ۹۱۴ (میانگین ۸۷۱٫۱۲۸) است، نه ثابت ۸۷۲؛ skip برای Brier، AUC، slope و `c` همه ۰ است؛ بازه‌ی ۹۵٪ Brier `= [0.1635141574, 0.1824436166]` و بازه‌ی AUC `= [0.80112824, 0.8403015482]`. **مقدارهای ردشده:** الگوریتم فشرده‌ی r2 روی همین داده Brier `[0.1636014192, 0.1821598108]` می‌دهد؛ پیاده‌سازی‌ای که این مقدار را بدهد رد است.

**C.13 حداقل نمونه (شرط ۱۲):**
- `N_E ≥ 8,000` [P] **و** فاصله‌ی تقویمی از T0 ≥ `365 روز` [P].
- قبل از رسیدن به هر دو شرط، فقط گزارش توصیفی پوشش و ردها تولید می‌شود.
- این حدها **قانون توقف نیستند**: هیچ ارزیابی‌ای نمی‌تواند جمع‌آوری را زودتر متوقف کند، چه نتیجه‌ی خوب باشد چه بد. Checkpoint های میانی فقط توصیفی‌اند و از آن‌ها هیچ تصمیم pass/fail گرفته نمی‌شود.
- در ۳۶۵ روز ۸٬۷۶۰ نقطه‌ی شبکه داریم. رسیدن به ۸٬۰۰۰ رکورد ELIGIBLE یعنی نرخ حدود ۹۱٫۳٪. اگر کمتر باشد، ارزیابی رسمی منتظر می‌ماند و جمع‌آوری ادامه می‌یابد.

**C.14 وضعیت شواهد (شرط ۱۶):**
- تا وقتی `N_E`، فاصله‌ی زمانی، gate spec (جدا، hash‌شده قبل از ارزیابی رسمی و قبل از اولین نگاه به متریک‌های `p`–`Y`) و benchmark spec (جدا) برقرار نباشند، خروجی فقط توصیفی است.
- **Gate و طول بلوک gate در این سند تعریف نشده است.**
- `S` (لحظه‌ی برش تحلیل، C.12)، prefix تحلیل (`analysis_prefix_seq`، `analysis_prefix_entry_hash` و رکورد انتشار آن: `prefix_published_at_utc`، `prefix_receipt`؛ C.17)، فهرست طول‌های بلوک، `B`، seed، نسخه‌ی numpy، **hash های gate، benchmark و کد تحلیل** و `analysis_mode` در یک manifest تحلیل (`FJ-ANALYSIS-3`، r6) hash می‌شوند و manifest در namespace `manifests` مقصد و در journal ثبت می‌شود؛ هیچ‌کدام بعد از دیدن متریک‌ها تغییر نمی‌کند. `analysis_mode = OFFICIAL` فقط با hash ثبت‌شده‌ی gate و benchmark ممکن است (C.17)؛ بدون آن خروجی `DESCRIPTIVE` است. هر manifest که تا کنون ثبت شده در هر گزارش فهرست می‌شود.
- فقط رکوردهای forward ELIGIBLE بعد از T0 شاهد validation هستند.

**C.15 Amendment و تغییرناپذیری (شرط ۱۷):**
- هر تغییر در spec، code، config، شبکه، target یا وزن = نسخه‌ی جدید spec با hash جدید و `EVENT(AMENDMENT)`.
- تغییر تعریف = journal و T0 جدید. رکوردهای قبلی با برچسب نسخه‌ی قبلی می‌مانند و هرگز با قانون جدید بازمحاسبه نمی‌شوند.
- ویرایش یا حذف ورودی‌های journal ممنوع است. اصلاح فقط به‌صورت ورودی جدید انجام می‌شود.

**C.16 عمر ۲۴ ساعته‌ی اتصال Binance و چرخش برنامه‌ریزی‌شده — اصلاح ۳ (r4):**
- **حد مستندشده‌ی سرویس و رفتار عملیاتی مشاهده‌شده — دو چیز جدا (اصلاح r6):**
  1. **حد مستندشده (documented service limit).** صفحه‌ی رسمی «Websocket Market Streams | Connect» در مستندات USDⓈ-M Futures (صفحه‌ی خانواده‌ی درست API، نه قرض‌گرفته از COIN-M یا Spot؛ در بازبینی مستقل GPT با تاریخ به‌روزرسانی ۲۰۲۶-۱۰-۱۳ تأیید شد) می‌گوید هر اتصال حداکثر **۲۴ ساعت** معتبر است، سرور هر **۳ دقیقه** ping می‌فرستد و اگر pong ظرف **۱۰ دقیقه** نرسد اتصال بسته می‌شود؛ همان صفحه سقف ۱۰۲۴ stream در هر اتصال و مسیر تفکیک‌شده‌ی `/market` را هم می‌آورد. نگارنده‌ی spec در ۲۰۲۶-۱۰-۱۲ آن صفحه را فقط با ابزار خلاصه‌ساز خوانده بود و در r5 آن را «فرض» نوشت؛ بازبینی مستقل نشان داد این احتیاط بیش از حد بود. صفحه‌ی اختصاصی Kline همین عدد را تکرار نمی‌کند (فقط مسیر raw `/market/ws/{symbol}@kline_{interval}` و سرعت به‌روزرسانی ۲۵۰ ms را می‌آورد)، ولی این حد برای **اتصال** این خانواده مستند شده است نه برای یک stream. بنابراین `max_connection_age_s = 86400` **حد مستندشده‌ی سرویس** است، نه حدس. مستند ضمانت رفتار آینده نیست و ممکن است عوض شود؛ همان صفحه در dry-run (C.1 گام ۳) دوباره بازبینی و تاریخ به‌روزرسانی آن در گزارش dry-run ثبت می‌شود.
  2. **رفتار عملیاتی مشاهده‌شده (observed operational behaviour).** تا این لحظه **هیچ رفتار عملیاتی مشاهده نشده است** (هیچ اتصال زنده‌ای باز نشده). آنچه spec می‌تواند بگوید فقط «مستند چنین می‌گوید» است، نه «اتصال در عمل تا ۲۴ ساعت می‌ماند و درست در ۲۴ ساعت بسته می‌شود». سنجش عملیاتی کار dry-run است (C.1 گام ۳ بند الف): یک **اتصال مشاهده‌ای بدون چرخش** تا بسته شدن توسط سرور (حداکثر ۲۵ ساعت) و ثبت سن آن. اگر این سن از `rotation_start_age_s + rotation_attempt_timeout_s` کوچک‌تر باشد، spec قفل‌شده کنار گذاشته و نسخه‌ی اصلاح‌شده lock می‌شود (C.15)؛ حتی نتیجه‌ی مثبت فقط مشاهده‌ی یک لحظه است و ضمانت Binance نیست.
  3. **چرخش موفق ۲۳ ساعته در warm-up فقط رویه‌ی چرخش را می‌آزماید؛** نه حد مستند را تأیید می‌کند و نه رفتار عملیاتی هر وضعیت را اثبات می‌کند (اگر سرور اتصال را زودتر از ۲۳ ساعت ببندد، چرخش اصلاً شروع نمی‌شود و مسیر `A_LOST` و از دست رفتن کندل رخ می‌دهد). چون چرخش پیش از رسیدن به حد انجام می‌شود، بزرگ‌تر بودن حد واقعی چیزی را عوض نمی‌کند.
- **سیاست (در `CONFIG.rotation_policy`، [P]):**

| پارامتر | مقدار | معنا |
|---|---|---|
| `max_connection_age_s` | `86400` | حد مستندشده‌ی عمر اتصال (بند ۱ بالا)؛ verifier اتصالی را که از این حد به‌اضافه‌ی ۶۰ ثانیه مسن‌تر باشد نقض می‌شمارد |
| `rotation_start_age_s` | `82800` | سن اتصال ACTIVE (۲۳ ساعت) برای شروع چرخش |
| `rotation_attempt_timeout_s` | `600` | مهلت رسیدن اتصال جانشین به READY |
| `rotation_retry_s` | `60` | فاصله‌ی تلاش بعد از هر تلاش ناموفق |
| `boundary_guard_s` | `10` | گارد دور مرز هر کندل ۵ دقیقه‌ای |
| `reconnect_backoff_s` | `[1,2,4,8,16,32,60]` | فاصله‌ی تلاش‌های اتصال مجدد بعد از قطع (آخرین مقدار تکرار می‌شود) |
| `silence_timeout_s` | `30` | سکوت کامل (بدون هیچ فریم) روی اتصال ACTIVE که قطع شمرده می‌شود؛ آهنگ واقعی پیام‌ها در dry-run سنجیده می‌شود |

- **نقش‌ها:** یک اتصال `ACTIVE` و در زمان چرخش یک اتصال `STANDBY` (جانشین). پیام هر دو اتصال از همان `validate_kline` (C.2) با `connection_id` خودشان می‌گذرد و قاعده همان قاعده‌ی «اولین دریافت معتبر» است: اگر هر دو اتصال یک کندل را بفرستند، اولی `CANDLE` است و دومی با مقدار یکسان `DUPLICATE_IDENTICAL` و با مقدار متفاوت `DUPLICATE_CONFLICT` (ناهنجاری واقعی journal با اثر `R02`/`E06` طبق C.8 و KAT-9a).
- **روال چرخش برنامه‌ریزی‌شده (به ترتیب):**
  1. **شروع:** وقتی سن اتصال ACTIVE به `rotation_start_age_s` می‌رسد و جانشینی نیست، collector اتصال تازه‌ای فقط به `feed_url` باز می‌کند. اگر handshake شکست بخورد: `FEED_ROTATION(ATTEMPT_FAILED)` با `reason = HANDSHAKE` و `new_connection_id = null`؛ تلاش بعدی بعد از `rotation_retry_s`. اگر handshake موفق بود: `FEED_CONNECT(role = STANDBY)` و سپس `FEED_ROTATION(STARTED)`. اگر `connection_url ≠ feed_url`: بلافاصله `FEED_ROTATION(ATTEMPT_FAILED, reason = URL)` و `FEED_DISCONNECT(reason = ATTEMPT_ABORTED)`؛ **هیچ پیامی** از چنین اتصالی پذیرفته نمی‌شود.
  2. **اثبات تحویل (READY):** اولین پیام نهایی جانشین اگر `CANDLE` یا `DUPLICATE_IDENTICAL` شود، `FEED_ROTATION(READY)` ثبت می‌شود. اگر نتیجه‌اش چیز دیگری باشد (`DUPLICATE_CONFLICT`، `MALFORMED`، `FEED_MISMATCH`، `NON_REALTIME` یا `CLOCK_INVALID`)، `FEED_ROTATION(ATTEMPT_FAILED)` با `reason` برابر نوع ناهنجاری و `FEED_DISCONNECT(ATTEMPT_ABORTED)` برای جانشین ثبت می‌شود؛ خودِ ناهنجاری یک ورودی واقعی journal است و اثر معمولش را دارد. تلاش بعدی بعد از `rotation_retry_s`.
  3. **مهلت:** اگر تا `rotation_attempt_timeout_s` بعد از `STARTED` اثبات تحویل نیامد: `ATTEMPT_FAILED(TIMEOUT)` و قطع جانشین (`ATTEMPT_ABORTED`).
  4. **تحویل (CUTOVER):** وقتی جانشین READY است و لحظه‌ی جاری داخل گارد مرزی نیست: ابتدا `FEED_DISCONNECT(connection_id = قدیمی، reason = PLANNED_ROTATION)` و بلافاصله `FEED_ROTATION(CUTOVER, reason = PLANNED)`. **اتصال قدیمی فقط بعد از اثبات تحویل جانشین بسته می‌شود.** سن اتصال جدید از `FEED_CONNECT` خودش شمرده می‌شود و چرخش بعدی در سن `rotation_start_age_s` همان اتصال است.
  5. **همپوشانی:** از READY تا CUTOVER هر دو اتصال پیام می‌گیرند؛ پیام یکسانِ اتصال دوم `DUPLICATE_IDENTICAL` و بی‌اثر است (RT1).
- **گارد مرزی:** `u = t mod 300 s` (t بر حسب ثانیه از 00:00:00 UTC). CUTOVER فقط وقتی مجاز است که `boundary_guard_s ≤ u ≤ 300 s − boundary_guard_s`. در مدل مرجع پیام نهایی هر کندل ۱ ثانیه بعد از close می‌رسد و گارد جلوی بسته شدن اتصال دقیقاً در این بازه را می‌گیرد؛ زمان واقعی رسیدن پیام نهایی در dry-run سنجیده می‌شود. جدول گارد: RT4.
- **از دست رفتن اتصال ACTIVE** (قطع شبکه، سکوت، یا بستن سرور در ۲۴ ساعت): همیشه `FEED_DISCONNECT(connection_id، reason ∈ {NETWORK_ERROR, STALL, SERVER_CLOSE}، connection_age_s)`؛ سپس:
  - اگر جانشین READY است: بلافاصله و **بدون انتظار گارد** `FEED_ROTATION(CUTOVER, reason = A_LOST)`؛
  - اگر جانشین هست ولی READY نیست: `ATTEMPT_FAILED(A_LOST)` و قطع جانشین (`ATTEMPT_ABORTED`)، سپس مسیر اتصال مجدد؛
  - **اتصال مجدد:** تلاش فوری، بعد با فاصله‌های `reconnect_backoff_s`؛ موفقیت = `FEED_CONNECT(role = ACTIVE)` با `affected_from_utc` (لحظه‌ی قطع) و `affected_to_utc` (لحظه‌ی اتصال).
- **سکوت:** اگر `silence_timeout_s` هیچ فریمی (نهایی یا ناپایدار) روی اتصال ACTIVE نرسد: `EVENT(FEED_STALL)` با `silent_ms` و `FEED_DISCONNECT(reason = STALL)`؛ ادامه مثل بالا.
- **هیچ REST و backfill (C.11):** کندلی که در بازه‌ی قطع نرسیده برای همیشه گم می‌ماند. **هزینه‌ی پذیرفته‌شده‌ی طراحی:** هر کندل گمشده `R01` را برای همه‌ی تصمیم‌هایی که پنجره‌ی ۲۸۸تایی‌شان آن را دارد می‌آورد، یعنی تا ۲۴ تصمیم ساعتی. چرخش برنامه‌ریزی‌شده برای همین ساخته شده که قطع ۲۴ ساعته‌ی سرور هر روز یک کندل نبرد.
- **ورودی‌های journal (B.3):**
  - `FEED_CONNECT`: `connection_id`، `role`، `connection_url`، `http_status`؛ برای اتصال مجدد `affected_from_utc` و `affected_to_utc`.
  - `FEED_DISCONNECT`: `connection_id`، `reason` ∈ {`PLANNED_ROTATION`, `SERVER_CLOSE`, `NETWORK_ERROR`, `STALL`, `ATTEMPT_ABORTED`}، `connection_age_s`.
  - `FEED_ROTATION`: `phase` ∈ {`STARTED`, `READY`, `CUTOVER`, `ATTEMPT_FAILED`}، `old_connection_id`، `new_connection_id` (`null` اگر اتصال باز نشد)، `old_age_s`، `reason` (برای `CUTOVER`: `PLANNED` یا `A_LOST`؛ برای `ATTEMPT_FAILED`: `HANDSHAKE`، `URL`، `TIMEOUT`، `A_LOST` یا نوع ناهنجاری پیام؛ در بقیه `null`).
  - `FEED_STALL`: `connection_id`، `silent_ms`.
- **قواعد verifier (B.6 بند ۱۲):** (الف) هر `FEED_DISCONNECT`، `CANDLE` و `CANDLE_ANOMALY` به یک `FEED_CONNECT` موجود ارجاع می‌دهد؛ (ب) پیام پیش از `FEED_CONNECT` یا بعد از `FEED_DISCONNECT` همان اتصال نقض است؛ (پ) پیام پذیرفته‌شده از اتصالی که روی URL غلط باز شده نقض است، و چنین اتصالی باید `ATTEMPT_FAILED(URL)` و `FEED_DISCONNECT` داشته باشد؛ (ت) عمر هر اتصال (تا `FEED_DISCONNECT` یا آخرین پیامش) بیش از `max_connection_age_s + 60 s` نقض است؛ (ث) هر `FEED_DISCONNECT(PLANNED_ROTATION)` باید READY قبلی برای همان اتصال، CUTOVER بعدی، اثبات تحویل جانشین (یک `CANDLE` یا `DUPLICATE_IDENTICAL` از جانشین با `seq` کوچک‌تر) داشته باشد و خارج از گارد باشد؛ (ج) `CUTOVER(A_LOST)` فقط برای جانشینی مجاز است که پیش‌تر READY ثبت شده.
- **آزمون‌های پیش از T0 (D22):** قطع اجباری (RT2)، شکست اتصال مجدد (RT2، RT3، RT7b)، چرخش موفق (RT1)، کندل مرزی (RT1، RT4)، به‌علاوه‌ی RT5..RT10 و منفی‌های RTN1..RTN9. دو نوع اجرا: در dry-run با سیاست کوتاه‌شده (C.1 گام ۳) و **یک چرخش کامل با سیاست واقعی** در warm-up (C.1 گام ۹)؛ بدون چرخش کامل، `T0_DECLARATION` نوشته نمی‌شود.

**KAT-13 (ساختگی، مدل مرجع):** مدل با tick یک‌ثانیه‌ای؛ پیام نهایی هر کندل ۱ ثانیه بعد از close روی اتصال ACTIVE و ۱۰۰ میلی‌ثانیه دیرتر روی اتصال STANDBY؛ اتصال ۱ در `2029-12-31T23:00:01Z` باز می‌شود؛ کندل ۰ = `2030-01-01T00:00:00Z`؛ سیاست = جدول بالا. «اتصال n» = `connection_id = n`. عددها خروجی مدل مرجع‌اند، اندازه‌گیری شبکه نیستند.

| مورد | سناریو | نتیجه |
|---|---|---|
| RT1 | چرخش سالم warm-up | `FEED_CONNECT(STANDBY)` (اتصال ۲) و `STARTED` در `2030-01-01T22:00:01Z` (سن قدیمی ۸۲۸۰۰ ثانیه)؛ `READY` در `22:05:01.100Z` (پیام جانشین برای کندل `22:00:00Z`، یعنی کندل شماره‌ی ۲۶۴، که اتصال ۱ قبلاً در `22:05:01.000Z` آورده)؛ چون `22:05:01.1` داخل گارد است، `FEED_DISCONNECT(PLANNED_ROTATION)` (سن ۸۳۱۰۹ ثانیه) و `CUTOVER(PLANNED)` در `22:05:10.000Z`؛ دقیقاً یک `DUPLICATE_IDENTICAL` (اتصال ۲، کندل ۲۶۴)؛ ۰ کندل گمشده؛ ۳۰۰ `CANDLE` برای کندل‌های `−12..287` |
| RT2 | قطع اجباری شبکه در `10:04:40Z` (سن اتصال ۱ برابر ۳۹۸۷۹ ثانیه)، پنج تلاش اول اتصال مجدد ناموفق | `FEED_DISCONNECT(NETWORK_ERROR)`؛ تلاش‌ها در +0، +1، +3، +7، +15 ثانیه ناموفق و موفقیت در +31 ثانیه (`10:05:11Z`) به‌عنوان اتصال ۲ (`FEED_CONNECT(ACTIVE)` با بازه‌ی `10:04:40Z..10:05:11Z`)؛ **دقیقاً یک کندل گم می‌شود**: کندل `10:00:00Z` (شماره‌ی ۱۲۰) و backfill نمی‌شود؛ تصمیم D1 (`2030-01-02T00:00:00Z`) با `reject_reasons = ["R01"]` و `feature_bar_count = 287` رد می‌شود (ناهنجاری‌ای ثبت نشده، پس `R06` نیست)؛ چرخش بعدی از سن ۸۲۸۰۰ ثانیه‌ی اتصال ۲ شروع می‌شود؛ verifier ترتیب پیش از T0 را نقض می‌داند (اولین چرخش کامل پیش از `T0_DECLARATION` انجام نشده)، یعنی warm-up باید تمدید شود |
| RT3 | جانشین تمام مدت handshake نمی‌گیرد | ۶۰ ورودی `ATTEMPT_FAILED(HANDSHAKE)` هر ۶۰ ثانیه از `22:00:01Z` تا `22:59:01Z`؛ نه READY و نه CUTOVER؛ سرور در سن ۸۶۴۰۰ ثانیه (`2030-01-01T23:00:01Z`) اتصال ۱ را می‌بندد (`SERVER_CLOSE`) و اتصال مجدد بلافاصله اتصال ۲ را می‌سازد؛ تا کندل ۲۷۵ هیچ کندلی گم نشده |
| RT4 | جدول گارد، `u` بر حسب میلی‌ثانیه از مرز ۵ دقیقه‌ای | 0 ممنوع؛ 9999 ممنوع؛ 10000 مجاز؛ 150000 مجاز؛ 290000 مجاز؛ 290001 ممنوع؛ 299999 ممنوع |
| RT5 | اولین پیام جانشین برای کندل `22:00:00Z` با مقدار متفاوت (conflict) | `DUPLICATE_CONFLICT` از اتصال ۲ یک ناهنجاری واقعی journal است؛ `ATTEMPT_FAILED(DUPLICATE_CONFLICT)` در `22:05:01.100Z` و قطع اتصال ۲ (`ATTEMPT_ABORTED`)؛ اتصال ۱ ادامه می‌دهد؛ تلاش دوم (اتصال ۳) در `22:06:02Z` شروع، READY در `22:10:01.100Z` و `CUTOVER(PLANNED)` در `22:10:10Z`؛ ۰ کندل گمشده |
| RT6 | جانشین روی URL غلط (مسیر قدیمی U2) باز می‌شود | `FEED_CONNECT(STANDBY)` اتصال ۲ با همان URL غلط، `ATTEMPT_FAILED(URL)` و `FEED_DISCONNECT(ATTEMPT_ABORTED)` همگی در `22:00:01Z`؛ هیچ پیامی از اتصال ۲ پذیرفته نمی‌شود؛ تلاش بعدی در `22:01:01Z` (اتصال ۳) و `CUTOVER(PLANNED)` در `22:05:10Z` |
| RT7a | اتصال ۱ در `22:05:05Z` (بعد از READY، پیش از CUTOVER برنامه‌ریزی‌شده) قطع می‌شود | `FEED_DISCONNECT(NETWORK_ERROR)` و بلافاصله `CUTOVER(A_LOST)` به اتصال ۲ در `22:05:05Z`؛ ۰ کندل گمشده |
| RT7b | اتصال ۱ در `22:03:00Z` (پیش از READY) قطع می‌شود | `ATTEMPT_FAILED(A_LOST)`، قطع اتصال ۲ (`ATTEMPT_ABORTED`)، اتصال مجدد فوری به‌عنوان اتصال ۳؛ هیچ `CUTOVER(A_LOST)` ثبت نمی‌شود؛ ۰ کندل گمشده |
| RT8 | سکوت اتصال ACTIVE از `10:00:00Z` | `FEED_STALL` (`silent_ms = 30000`) و `FEED_DISCONNECT(STALL)` در `10:00:30Z`، سپس اتصال مجدد (اتصال ۲)؛ کندل `09:55:00Z` (شماره‌ی ۱۱۹) گم می‌شود |
| RT9 | هیچ REST و backfill | در همه‌ی سناریوها کندل گمشده گم می‌ماند (RT2، RT8) و هیچ `CANDLE` با `ingested_ms` بعد از `recorded_at_utc + 250 ms` وجود ندارد |
| RT10 | `rotation_policy` | داخل `CONFIG` است (پس با hash آن قفل می‌شود) و دقیقاً مقدارهای جدول سیاست را دارد |
| RTN1 | حذف `READY` از journal سالم RT1 (زنجیره دوباره hash می‌شود تا فقط قاعده‌ی معنایی بتواند خطا بدهد) | `PLANNED_ROTATION` بدون READY نقض است |
| RTN2 | حذف `DUPLICATE_IDENTICAL` جانشین (بی‌اثبات تحویل) | نقض: جانشین پیش از قطع برنامه‌ریزی‌شده چیزی تحویل نداده |
| RTN3 | زمان `FEED_DISCONNECT(PLANNED_ROTATION)` به `22:05:00.500Z` تغییر می‌کند | نقض: داخل گارد مرزی |
| RTN4 | اولین `CANDLE` اتصال ۲ به اتصال ۱ نسبت داده می‌شود | نقض: پیام بعد از `FEED_DISCONNECT` همان اتصال |
| RTN5 | زمان `FEED_CONNECT` اتصال ۱ به `2029-12-30T20:00:00Z` تغییر می‌کند | نقض: عمر اتصال بیش از `max_connection_age_s + 60 s` |
| RTN6 | حذف `READY` و تغییر دلیل `CUTOVER` به `A_LOST` | نقض: `CUTOVER(A_LOST)` به جانشینی که هرگز READY نبوده |
| RTN7 | حذف `CUTOVER` | نقض: `PLANNED_ROTATION` بدون CUTOVER |
| RTN8 | اولین `CANDLE` اتصال ۲ به اتصال ۹۹ نسبت داده می‌شود | نقض: پیام از اتصال ناشناخته |
| RTN9 | `connection_url` اتصال ۲ به مسیر قدیمی U2 تغییر می‌کند و این اتصال داده‌ی پذیرفته‌شده دارد | نقض: پیام پذیرفته‌شده از اتصال با URL غلط |

**C.17 برش as-of-S تحلیل و manifest — اصلاح ۱ (r5؛ جایگزین قاعده‌ی r4) و اصلاح ۴ و ۵ (r6: manifest `FJ-ANALYSIS-3`، hash های ثبت‌شده، namespace):**
- **مسئله‌ی r4 (ردشده):** r4 `P` را «اولین `CHECKPOINT` منتشرشده با `recorded_at_utc ≥ S`» تعریف می‌کرد. این برش as-of-S نیست: هرچه بین `S` و آن `CHECKPOINT` نوشته می‌شد (مثلاً `DUPLICATE_CONFLICT` که `E06` می‌دهد یا `ADJUDICATION`ی که بعد از `S` نوشته شده) وارد تحلیل می‌شد؛ نتیجه‌ی همان `S` به رشد بعدی journal بستگی داشت (و تا چنین `CHECKPOINT`ی نبود، تحلیلی هم نبود)؛ و ملاک انتخاب `CHECKPOINT` ساعت نویسنده بود، نه ساعت مقصد. r5 این قاعده را کنار می‌گذارد.
- **سیاست یگانه (r5):**
  1. `S` برش شواهد (evidence cutoff) است؛ UTC.
  2. **`P` = `seq` آخرین `CHECKPOINT` که منتشر شده و `published_at_utc` مقصد (B.7 بند ۳) ≤ `S` است.** ملاک زمان مقصد (تعیین‌شده توسط مقصد) است؛ `recorded_at_utc` نویسنده هیچ نقشی در انتخاب `P` ندارد. چون `published_at_utc` در ترتیب `seq` غیرنزولی است (B.7 بند ۵)، `P` همان بزرگ‌ترین `seq` با این شرط است. مساوی (`published_at_utc = S`) شامل است.
  3. تحلیل **فقط** ورودی‌های journal با `seq ≤ P` را می‌خواند. چون `H_P` همه‌ی ورودی‌های `0..P` را متعهد می‌کند و مقصد آن را تا `S` گرفته، این‌ها دقیقاً «شواهدی هستند که تا `S` به‌طور خارجی anchor بوده‌اند».
  4. موقعیتی که در `P` PENDING است (یا `DECISION` ندارد) `e_i = 0` می‌ماند، حتی اگر `ADJUDICATION` آن بعداً نوشته شود.
  5. شبکه‌ی کامل بر اساس `S` (نه `P`) تعریف می‌شود: `d_i = T0 + i·1 h`، `N_G = floor((S − T0 − 32 h) / 1 h) + 1` (C.12). برای هر `d_i`: `DECISION` با `decision_time_utc = d_i` (اولین)، `OUTCOME` آن (اولین) و **اولین `ADJUDICATION` آن با `seq ≤ P`**؛ `e_i = 1` فقط اگر آن `ELIGIBLE` باشد.
  6. اگر هیچ `CHECKPOINT` منتشرشده با `published_at_utc ≤ S` وجود ندارد، **تحلیل رسمی انجام نمی‌شود** (فقط گزارش «بدون prefix»).
  7. موقعیت‌هایی که رکوردهای لازم‌شان در prefix ناموجود بود صریحاً گزارش می‌شوند (بند بعد).
- **گزارش prefix (الزامی در هر گزارش تحلیل):** هر موقعیت `i` از شبکه‌ی کامل دقیقاً در یکی از پنج دسته است، فقط از روی ورودی‌های `seq ≤ P`: `ELIGIBLE` (`e_i = 1`)؛ `INELIGIBLE` (اولین `ADJUDICATION` با `seq ≤ P` وجود دارد و `INELIGIBLE` است؛ دلیل‌های E01..E06 شمرده می‌شوند)؛ `REJECTED_UNADJUDICATED_AT_P` (`DECISION` رد‌شده با `seq ≤ P` و بدون `ADJUDICATION` با `seq ≤ P`؛ `e_i = 0` قطعی)؛ `PENDING_AT_P` (`DECISION` پذیرفته‌شده با `seq ≤ P` بدون `ADJUDICATION` با `seq ≤ P`؛ `OUTCOME` و `AUDIT` ممکن است باشند یا نباشند)؛ `DECISION_ABSENT_AT_P` (هیچ `DECISION` با `seq ≤ P` برای `d_i`). مجموع پنج شمار برابر `N_G` است. **`unavailable_in_prefix = |PENDING_AT_P| + |DECISION_ABSENT_AT_P|`** با فهرست `d_i` ها (به‌صورت بازه‌های ساعتی متوالی) و نسبت `unavailable_in_prefix / N_G` در هر گزارش و کنار هر متریک می‌آید. این موقعیت‌ها `e_i = 0` می‌مانند ولی «ineligible» شمرده نمی‌شوند: در prefix داده‌ی لازم را نداشتند. گزارش برای هیچ موقعیتی ورودی `seq > P` را نمی‌خواند و نمی‌گوید بعداً چه شد.
- **manifest تحلیل (`FJ-ANALYSIS-3`، r6)** یک فایل JSON با `canon` (B.2) است و فیلدهای دقیقاً این **۱۷** مورد است: `manifest_version`، `journal_id`، `spec_sha256`، `t0_utc`، `S_utc`، **`analysis_prefix_seq`**، **`analysis_prefix_entry_hash`**، **`prefix_published_at_utc`** و **`prefix_receipt`** (هر دو از رکورد مقصد `P`)، `block_lengths`، `B`، `seed_base`، `numpy_version`، **`analysis_code_sha256`**، **`gate_spec_sha256`**، **`benchmark_spec_sha256`** و **`analysis_mode`** (`OFFICIAL` یا `DESCRIPTIVE`). `manifest_sha256` = SHA-256 بایت‌های `canon` همین شیء. (`FJ-ANALYSIS-2` در r5 پانزده فیلد داشت؛ `gate_spec_sha256` می‌توانست `null` یا هر رشته‌ای باشد، `benchmark_spec_sha256` نبود و `analysis_code_sha256` اعتبارسنجی نمی‌شد.)
- **ثبت hash های gate، benchmark و کد تحلیل (r6):** هر یک از این سه، پیش از اولین نگاه به متریک‌های `p`–`Y`، با یک `EVENT(SPEC_REGISTRATION)` در journal ثبت می‌شود: `spec_kind` ∈ {`GATE`، `BENCHMARK`، `ANALYSIS_CODE`}، `spec_sha256` (SHA-256 بایت‌های فایل gate spec یا benchmark spec؛ برای کد تحلیل tree hash طبق KAT-14) و `spec_name` (نام فایل یا نسخه). ثبت جدید از همان نوع ثبت قبلی را **جایگزین** می‌کند ولی قبلی در journal می‌ماند؛ برای manifest با prefix `P` فقط ثبت‌های با `seq ≤ P` به حساب می‌آید و از آن‌ها **آخرین** ثبت هر نوع ملاک است (ثبتی با `seq > P` بر آن manifest اثر ندارد). این spec محتوای gate و benchmark را تعریف **نمی‌کند** (C.14)؛ فقط تعیین می‌کند hash آن‌ها کجا تثبیت می‌شود و verifier چه چیزی را با آن تطبیق می‌دهد.
- **حالت تحلیل (r6):** `analysis_mode = OFFICIAL` فقط وقتی مجاز است که `gate_spec_sha256` و `benchmark_spec_sha256` هر دو غیر `null` و ثبت‌شده باشند (`OFFICIAL_NEEDS_HASH`)؛ `DESCRIPTIVE` اجازه می‌دهد این دو `null` باشند ولی `analysis_code_sha256` در هیچ حالتی `null` نیست و خروجی هرگز «رسمی» نامیده نمی‌شود (C.14). `analysis_code_sha256` باید tree hash (KAT-14) فایل‌های کدی باشد که **واقعاً** اجرا می‌شوند؛ اگر آن فایل‌ها به verifier داده شود، verifier آن را بازمحاسبه می‌کند (`CODE_HASH_MISMATCH`)، وگرنه `NOT_CHECKED` گزارش می‌دهد.
- **ثبت manifest و محل نگهداری (r6):** ابتدا فایل manifest به namespace `manifests` مقصد فرستاده و رکورد چهارکلیدی آن بازخوانی می‌شود (B.7 بند ۹)؛ **سپس** `EVENT(ANALYSIS_MANIFEST)` با `detail`، نه فیلد `analysis_prefix_seq`، `analysis_prefix_entry_hash`، `prefix_published_at_utc`، `prefix_receipt`، `S_utc`، `analysis_code_sha256`، `gate_spec_sha256`، `benchmark_spec_sha256` و `analysis_mode` (برابر فایل) و نیز `manifest_sha256`، `manifest_published_at_utc`، `manifest_receipt` (از رکورد namespace) و `t0_utc`، با `seq > P` و `recorded_at_utc ≥ S_utc` (برش در آینده نیست) و پیش از دیدن هر متریک `p`–`Y` ثبت می‌شود. فایل manifest کنار گزارش نیز نگه‌داری می‌شود.
- **اجرای مجدد:** اجرای مجدد همان manifest روی journal کامل (هر طولی) و روی journal بریده در `P` باید `(N_G, e, p, y)` و گزارش دسته‌ها را **بایت‌به‌بایت** یکسان بدهد و bootstrap (فقط تابع این ورودی‌ها، seed و `L`) نتیجه‌ی یکسان بدهد. هر رویداد بعد از `P` (`DUPLICATE_CONFLICT`، `ADJUDICATION`، `CHECKPOINT` های بعدی، چه پیش از `S` append شده باشند چه بعد از آن) هیچ اثری ندارد. تنها شرط وابسته به رشد مقصد قاعده‌ی verifier (ج) پایین است: بعد از `P` هیچ `CHECKPOINT` با زمان مقصد ≤ `S` نمی‌تواند وجود داشته باشد.
- **تحلیل بعدی:** هر تحلیل جدید (`S` دیگر) manifest تازه با prefix خودش دارد. manifest قبلی و ورودی‌هایش دست نمی‌خورند، و **همه‌ی manifest‌هایی که تا کنون ثبت شده‌اند** با هر نتیجه گزارش می‌شوند (جلوی انتخاب `S` بعد از دیدن نتیجه را نمی‌گیرد ولی آن را آشکار می‌کند).
- **قواعد verifier (B.6 بند ۱۳):** (الف) `S_utc ≤ recorded_at_utc` خودِ `EVENT`؛ (ب) `analysis_prefix_seq` کوچک‌تر از `seq` خودِ `EVENT` است؛ (پ) ورودی با آن `seq` از نوع `CHECKPOINT` است و `entry_hash` آن برابر `analysis_prefix_entry_hash` است؛ (ت) رکورد هفت‌فیلدی آن `CHECKPOINT` در مقصد وجود دارد و `entry_hash`، `published_at_utc` و `receipt` آن برابر `analysis_prefix_entry_hash`، `prefix_published_at_utc` و `prefix_receipt` است؛ (ث) `published_at_utc(P) ≤ S`؛ (ج) **آخرین بودن:** هیچ `CHECKPOINT` با `seq > P` رکورد انتشار با `published_at_utc ≤ S` ندارد؛ (چ) رکوردهای مقصد طبق B.7 بند ۵ سالم‌اند (وگرنه prefix نامعتبر است)؛ (ح) فیلدهای فایل manifest با `EVENT` و با ثابت‌های قفل‌شده (`block_lengths`، `B = 4000`، `seed_base = 20261000`، `numpy_version = 2.5.3`) و با `journal_id`، `spec_sha256` و `t0_utc` خود journal برابرند؛ **(r6)** (خ) `analysis_mode` یکی از `OFFICIAL` و `DESCRIPTIVE` است (`MANIFEST_EVENT_MALFORMED`)؛ `analysis_code_sha256` هرگز `null` نیست و هر hash غیر `null` ۶۴ نویسه‌ی hex حروف کوچک است (`HASH_FORMAT`)؛ در `OFFICIAL` هیچ‌کدام از gate و benchmark `null` نیست (`OFFICIAL_NEEDS_HASH`)؛ (د) هر hash برابر `spec_sha256` **آخرین** `SPEC_REGISTRATION` از نوع خودش با `seq ≤ P` است (`HASH_NOT_REGISTERED`)؛ ثبت بدشکل `SPEC_REGISTRATION_MALFORMED` است؛ (ذ) رکوردی در namespace `manifests` برای `manifest_sha256` هست (`MANIFEST_NOT_PUBLISHED`)، `manifest_published_at_utc` و `manifest_receipt` در `EVENT` با آن برابرند (`MANIFEST_RECORD_MISMATCH`)، `S_utc` از زمان انتشار آن رکورد دیرتر نیست (`S_AFTER_MANIFEST_PUBLICATION`) و `EVENT` بیش از ۵ ثانیه پیش از آن زمان ثبت نشده است (`MANIFEST_EVENT_BEFORE_PUBLICATION`)؛ رکوردهای namespace طبق B.7 بند ۹ سالم‌اند (`MALFORMED_MANIFEST_PUBLICATION`، `DUPLICATE_MANIFEST`)؛ (ر) اگر فایل‌های کد تحلیل داده شود، tree hash آن‌ها برابر `analysis_code_sha256` است (`CODE_HASH_MISMATCH`)؛ اگر فایل manifest یا فایل‌های کد داده نشود، گزارش verifier `NOT_CHECKED` می‌گوید و آن را «پاس» نمی‌شمارد.
- **حدود (صریح):** (۱) prefix اثبات نمی‌کند که `S` پیش از دیدن متریک‌ها انتخاب شده؛ فقط ثبت و گزارش همه‌ی manifest‌ها آن را آشکار می‌کند. (۲) اعتماد به `published_at_utc` اعتماد به ساعت مقصد است (B.7 بند ۶). (۳) دم anchor‌نشده و ناتمامیِ adjudication تا `S` در هر تحلیل از دست می‌رود؛ انتخاب `S` درست بعد از انتشار یک `CHECKPOINT` این فاصله را کوتاه می‌کند، ولی انتخاب `S` آزاد نیست و همه‌ی manifest‌ها گزارش می‌شوند. (۴) **(r6)** manifest و hash های gate، benchmark و کد تحلیل فقط **ثبت** می‌شوند؛ این spec ثابت نمی‌کند gate محتوای مناسبی دارد یا کد تحلیلِ اجراشده همان کد ثبت‌شده است (فقط بازمحاسبه‌ی tree hash آن را وقتی فایل‌ها داده شود می‌سنجد). «پیش از دیدن متریک‌ها» رویه‌ای است: ثبت زمان‌دار `SPEC_REGISTRATION` در journal (پیش از `P`) آن را آشکار می‌کند، اثبات نمی‌کند.

**KAT-12 (ساختگی) — برش as-of-S.** (الف) **بردار انتزاعی** (`T0 = 2030-01-02T00:00:00Z`، `d_k = T0 + k·1 h`؛ زمان‌ها با maintenance `00:30` سازگارند). فقط `d_0..d_3` در journal هستند و هر موقعیت دیگر شبکه‌ی هر تحلیل «بدون `DECISION`» است؛ این ساده‌سازی بردار است، نه رفتار journal واقعی. ورودی‌های **J0** به ترتیب `seq`:

| seq | ورودی | زمان |
|---|---|---|
| 1، 2، 3 | `EVENT(SPEC_REGISTRATION)` برای `GATE`، `BENCHMARK` و `ANALYSIS_CODE` با hash های `88…88`، `99…99` و `44…44` (هر کدام ۶۴ نویسه؛ ثبت‌شده پیش از `P`) | `recorded_at_utc = 2030-01-01T23:59:59Z` |
| 10..13 | `DECISION` برای `d_0..d_3`، همه ACCEPTED با `p_raw = 0.2، 0.6، 0.7، 0.4` | — |
| 20..23 | `OUTCOME` برای `d_0..d_3`، همه RESOLVED با `Y = 0، 1، 1، 1` | — |
| 24 | `CANDLE_ANOMALY(DUPLICATE_CONFLICT)` روی کندلی از پنجره‌ی forward `d_3` (بعد از `OUTCOME(d_3)`) | `recorded_at_utc = 2030-01-03T12:00:00Z` |
| 30، 31، 32 | `ADJUDICATION(d_0)` ELIGIBLE؛ `ADJUDICATION(d_2)` ELIGIBLE؛ `ADJUDICATION(d_3)` INELIGIBLE [E06] (به‌خاطر seq 24) | maintenance `2030-01-04T00:30Z` |
| 33 | `CHECKPOINT` **CP_A** | `recorded_at_utc = 2030-01-04T00:30:05.000Z`؛ زمان مقصد `published_at_utc = 2030-01-04T00:31:10.000Z` |
| 34 | `CANDLE_ANOMALY(DUPLICATE_CONFLICT)` روی کندلی از پنجره‌ی feature `d_1` (بعد از `DECISION(d_1)`) | `2030-01-04T02:00:00Z` (بین `P` و `S1`) |
| 35 | `CANDLE_ANOMALY(DUPLICATE_CONFLICT)` روی کندلی از پنجره‌ی forward `d_2` (بعد از `ADJUDICATION(d_2)`، پس بی‌اثر است: C.4 S6) | `2030-01-04T12:00:00Z` (بعد از `S1`) |
| 40 | `ADJUDICATION(d_1)`: در J0 INELIGIBLE [E06] (به‌خاطر seq 34) | maintenance `2030-01-05T00:35Z` |
| 41 | `CHECKPOINT` **CP_B** | `recorded_at_utc = 2030-01-05T00:36:00.000Z`؛ انتشارش تا ظهر شکست خورده و زمان مقصد `published_at_utc = 2030-01-05T12:00:30.000Z` است |

ورودی‌های 24، 34 و 35 conflict هایی هستند که در زمان واقعی دریافت شده‌اند (`ingested_ms` نزدیک بسته شدن کندل) ولی با تأخیر در صف نوشتن append شده‌اند (B.6 بند ۱۱ فقط `ingested_ms ≤ recorded_at_utc + 250 ms` را می‌خواهد)؛ این ساده‌سازی بردار انتزاعی است و رفتار معمول collector نیست. گونه‌ها: **J1** = J0 که در آن به‌جای ورودی 34 یک `EVENT` خنثی می‌آید (تا `seq` ها یکسان بمانند) و `ADJUDICATION(d_1)` در seq 40 ELIGIBLE است؛ **J2** = J0 بریده در seq 33. `S1 = 2030-01-04T10:00:00Z`، `S2 = 2030-01-05T06:00:00Z`، `S3 = 2030-01-05T12:00:30.000Z`.

| مورد | ورودی | نتیجه |
|---|---|---|
| AP1 | `S1` روی J0 | `N_G = floor((58 h − 32 h) / 1 h) + 1 = 27`؛ `P = 33` (زمان مقصد CP_A برابر `00:31:10 ≤ S1`؛ زمان مقصد CP_B بعد از `S1` است) |
| AP2 | ورودی‌های تحلیل روی prefix 33 | `e = [1, 0, 1, 0, …]` (۲۷ موقعیت، `N_E = 2`)، `p = [0.2, –, 0.7, …]`، `Y = [0, –, 1, …]`، Brier `= 0.065`؛ دسته‌ها: `ELIGIBLE` ۲ (`d_0`، `d_2`)، `INELIGIBLE` ۱ (`d_3`: E06)، `PENDING_AT_P` ۱ (`d_1`)، `REJECTED_UNADJUDICATED_AT_P` ۰، `DECISION_ABSENT_AT_P` ۲۳ (`d_4..d_26`)؛ `unavailable_in_prefix = 24` |
| AP3 | همان manifest (`S1`) روی J1 و روی J2 | ورودی‌ها و گزارش دسته‌ها **بایت‌به‌بایت** برابر AP2: conflict ‌های seq 34 و 35 و `ADJUDICATION(d_1)` (با هر نتیجه) همه بعد از `P` هستند و خوانده نمی‌شوند |
| AP4 | `S2` روی J0 و J1 | `N_G = 47`؛ `P = 33` چون زمان مقصد CP_B (`12:00:30`) بعد از `S2` است، هرچند `recorded_at_utc` آن (`00:36`) پیش از `S2` است؛ `e` مثل AP2؛ `DECISION_ABSENT_AT_P` = ۴۳ و `unavailable_in_prefix = 44` |
| AP5 | `S3` (برابر زمان مقصد CP_B) | `N_G = 53`، `P = 41` (مساوی شامل است). روی J0: `e = [1, 0, 1, 0, …]`، `INELIGIBLE` ۲ (`d_1`: E06؛ `d_3`: E06)، `PENDING_AT_P` ۰، `DECISION_ABSENT_AT_P` ۴۹، `unavailable_in_prefix = 49`، Brier `= 0.065`. روی J1: `e = [1, 1, 1, 0, …]`، `INELIGIBLE` ۱ (`d_3`)، Brier `= 0.29 / 3 = 0.0966667` |
| AP6 | `S3 − 1 ms` | `N_G = 53`، `P = 33` (CP_B هنوز منتشر نشده)؛ دسته‌ها مثل AP2 ولی `DECISION_ABSENT_AT_P` = ۴۹ و `unavailable_in_prefix = 50` |
| AP7 | `S = 2030-01-04T00:31:10.000Z` (برابر زمان مقصد CP_A) و سپس `S` یک میلی‌ثانیه کمتر | با مساوی: `P = 33`، `N_G = 17`. با یک میلی‌ثانیه کمتر: هیچ `CHECKPOINT` منتشرشده‌ای با زمان مقصد ≤ `S` نیست → **تحلیل رسمی انجام نمی‌شود** (CP_A پیشتر در journal append شده بود ولی هنوز منتشر نشده بود) |
| AP8 | لبه‌های `N_G` | `S = T0 + 32 h` → `N_G = 1`؛ `S = T0 + 32 h − 1 ms` → `N_G = 0` (ارزیابی وجود ندارد) |
| AP9 | **خوانش‌های ردشده** | (۱) قاعده‌ی r4 («اولین `CHECKPOINT` با `recorded_at_utc ≥ S`»): `S1` روی J1 → `P = 41` و `e = [1, 1, 1, 0, …]` با Brier `0.0966667`؛ `S1` روی J0 → `P = 41` و `d_1` به‌صورت `INELIGIBLE` [E06]؛ `S1` روی J2 → هیچ prefixی نیست؛ یعنی نتیجه‌ی همان `S1` به رشد journal بستگی دارد. (۲) «آخرین `CHECKPOINT` با `recorded_at_utc ≤ S`» (ساعت نویسنده): `S2` روی J1 → `P = 41` و `e = [1, 1, 1, 0, …]`. (۳) خواندن کل journal بدون prefix: `S1` روی J1 → `e = [1, 1, 1, 0, …]`. پیاده‌سازی‌ای که هر یک را بدهد رد است |

(ب) **manifest KAT (`FJ-ANALYSIS-3`، ۱۷ فیلد):** `canon` شیء زیر (فیلدها به ترتیب صعودی کلید):

`{"B":4000,"S_utc":"2031-01-02T00:00:00Z","analysis_code_sha256":"4444444444444444444444444444444444444444444444444444444444444444","analysis_mode":"OFFICIAL","analysis_prefix_entry_hash":"5555555555555555555555555555555555555555555555555555555555555555","analysis_prefix_seq":401,"benchmark_spec_sha256":"9999999999999999999999999999999999999999999999999999999999999999","block_lengths":[32,48,64,96,128],"gate_spec_sha256":"8888888888888888888888888888888888888888888888888888888888888888","journal_id":"6666666666666666666666666666666666666666666666666666666666666666","manifest_version":"FJ-ANALYSIS-3","numpy_version":"2.5.3","prefix_published_at_utc":"2031-01-01T00:31:10.000Z","prefix_receipt":"KAT-R401","seed_base":20261000,"spec_sha256":"7777777777777777777777777777777777777777777777777777777777777777","t0_utc":"2030-01-02T00:00:00Z"}`

`manifest_sha256 = 11ae254a6916d48d2df611fe9daa2fc182dc869cb5e02137cac1cde3e0eb0d2b` (با python و openssl یکسان). نکته: `analysis_prefix_seq = 401`، `prefix_receipt = "KAT-R401"` و hash های `44…`، `55…`، `66…`، `77…`، `88…`، `99…` مقدار ساختگی‌اند (`44…` کد تحلیل، `88…` gate، `99…` benchmark).

(پ) **منفی‌های verifier روی `EVENT(ANALYSIS_MANIFEST)`** (روی J0 و رکوردهای مقصدش؛ manifest در `seq = 42` با `recorded_at_utc = 2030-01-05T13:00:00Z` ثبت می‌شود؛ r6: manifest در `2030-01-05T12:59:59.000Z` در namespace `manifests` منتشر شده است و سه `SPEC_REGISTRATION` در seq 1..3 هستند؛ همه‌ی موارد غیر از PM0 و سه ردیف تمیز PM13، PM26 و PM28 باید نقض گزارش شوند):

| مورد | تغییر | نتیجه |
|---|---|---|
| PM0 | manifest صحیح برای `S1`: prefix 33، `prefix_published_at_utc = 2030-01-04T00:31:10.000Z`، `prefix_receipt` برابر رکورد مقصد | تمیز |
| PM1 | `analysis_prefix_entry_hash` با journal برابر نیست | نقض |
| PM2 | `analysis_prefix_seq` به ورودی غیر-`CHECKPOINT` (مثلاً 12) اشاره می‌کند | نقض |
| PM3 | رکورد انتشار CP_A در مقصد نیست (CP_A «منتشر‌نشده») | نقض |
| PM4 | `S1` با prefix 41 (زمان مقصد CP_B بعد از `S1` است) | نقض |
| PM5 | `S3` با prefix 33 (CP_B تا `S3` منتشر شده؛ `P` آخرین نیست) | نقض |
| PM6 | `analysis_prefix_seq ≥ seq` خودِ manifest | نقض |
| PM7 | `S2` با prefix 41 (دام ساعت نویسنده: `recorded_at_utc` CP_B پیش از `S2` است ولی زمان مقصدش بعد از آن) | نقض |
| PM8 | `prefix_published_at_utc` یا `prefix_receipt` با رکورد مقصد نمی‌خواند | نقض |
| PM9 | `S_utc` بعد از `recorded_at_utc` خودِ `EVENT` (برش در آینده) | نقض |
| PM10 | `S0 − 1 ms` با `S0 = 2030-01-04T00:31:10.000Z` و prefix 33 (تا آن لحظه هیچ `CHECKPOINT`ی منتشر نشده) | نقض |
| PM11 | رکورد CP_A در مقصد بدون `receipt` (بدشکل) | نقض (prefix روی انتشار نامعتبر) |
| PM12 | `analysis_mode = OFFICIAL` و `gate_spec_sha256 = null` | نقض (`OFFICIAL_NEEDS_HASH`) |
| PM13 | `analysis_mode = DESCRIPTIVE` و هر دو hash گیت و benchmark برابر `null` (hash کد ثبت‌شده و درست است) | تمیز |
| PM14 | hash گیت در هیچ `SPEC_REGISTRATION(GATE)` با `seq ≤ P` ثبت نشده | نقض (`HASH_NOT_REGISTERED`) |
| PM15 | hash گیت ثبت شده، ولی ثبت دیگری از نوع GATE با hash متفاوت و `seq` بزرگ‌تر (و `≤ P`) هست (آخرین ثبت ملاک است) | نقض (`HASH_NOT_REGISTERED`) |
| PM16 | hash benchmark با ۶۳ نویسه | نقض (`HASH_FORMAT`) |
| PM17 | `analysis_code_sha256 = null` | نقض (`HASH_FORMAT`) |
| PM18 | هیچ رکوردی در namespace `manifests` برای `manifest_sha256` نیست | نقض (`MANIFEST_NOT_PUBLISHED`) |
| PM19 | `EVENT(ANALYSIS_MANIFEST)` بیش از ۵ s پیش از زمان انتشار manifest در مقصد ثبت شده | نقض (`MANIFEST_EVENT_BEFORE_PUBLICATION`) |
| PM20 | `manifest_receipt` در `EVENT` با رکورد مقصد فرق دارد | نقض (`MANIFEST_RECORD_MISMATCH`) |
| PM21 | `S_utc` پس از زمان انتشار manifest در مقصد است | نقض (`S_AFTER_MANIFEST_PUBLICATION`) |
| PM22 | `SPEC_REGISTRATION` با `spec_kind` نامعتبر | نقض (`SPEC_REGISTRATION_MALFORMED`) |
| PM23 | دو رکورد manifest با همان `manifest_sha256` در مقصد | نقض (`DUPLICATE_MANIFEST`) |
| PM24 | رکورد manifest در مقصد با پنج کلید | نقض (`MALFORMED_MANIFEST_PUBLICATION`) |
| PM25 | فایل‌های کد تحلیل داده شد و hash درختی آن‌ها با `analysis_code_sha256` نمی‌خواند | نقض (`CODE_HASH_MISMATCH`) |
| PM26 | فایل‌های کد تحلیل داده شد و hash درختی آن‌ها با `analysis_code_sha256` می‌خواند | تمیز |
| PM27 | `analysis_mode` در `EVENT` مقدار نامعتبر `X` دارد | نقض (`MANIFEST_EVENT_MALFORMED`) |
| PM28 | ثبت جدید GATE با hash متفاوت، ولی با `seq > P` (پس از prefix): بر manifest اثری ندارد | تمیز |
| PM29 | `receipt` رکورد manifest همان `receipt` رکورد `CHECKPOINT` منتشرشده‌ی `seq = 33` است (`EVENT` همان مقدار را دارد، پس فقط یکتایی در کل مقصد نقض می‌شود) | نقض (`DUPLICATE_RECEIPT`) |

هر ویرایش یک فیلد فایل manifest (prefix hash، `prefix_published_at_utc`، `prefix_receipt`، `B`، نسخه‌ی numpy، seed، فهرست طول بلوک، `journal_id`، `S_utc`، `analysis_mode`) یا hash را با `EVENT` ناسازگار می‌کند و نقض گزارش می‌شود.

---

## D — Pre-T0 verification checklist

- ☐ **D1** — SHA-256 فایل قفل‌شده برابر hash در `GENESIS` است و `GENESIS` قبل از collector start نوشته شده.
- ☐ **D2** — پیاده‌سازی MO-BIN-2%-8h-v1 ساخته شده، پیش از نوشتن `CONFIG` (C.1 گام ۴) `code_sha256` آن (tree hash، KAT-14) محاسبه شده، و دقیقاً بندهای A.2 تا A.6 را با ضرایب literal A.5 (نه چهار رقمی) پیاده می‌کند.
- ☐ **D3** — KAT-1، KAT-2 و همه‌ی ردیف‌های KAT-3 (از جمله ترتیب عملیات `100 → 102` و بی‌اثر بودن close در `k = 97`) پاس شده‌اند، با تطابق تا `1e−12` نسبی؛ پیاده‌سازی با ضرایب چهار رقمی KAT-1 و KAT-2 را رد می‌کند.
- ☐ **D4** — KAT-4: serialization canonical و زنجیره‌ی سه ورودی بایت‌به‌بایت با مقدارهای B.2 می‌خوانند (از جمله escape شدن `é`، نقل‌قول، بک‌اسلش و newline).
- ☐ **D5** — تست tamper روی کپی (B.6، B.7)؛ verifier هر یک از ده مورد را تشخیص می‌دهد: (۱) تغییر یک بایت در payload یک `DECISION`، (۲) یک `OUTCOME`، (۳) یک `ADJUDICATION`؛ (۴) حذف یک ورودی؛ (۵) جابه‌جایی دو ورودی؛ (۶) تغییر یک ردیف نمای مشتق `decisions` و (۷) یک ردیف نمای `outcomes`؛ (۸) تغییر payload یک `CHECKPOINT` (`head_entry_hash`) با و بدون بازمحاسبه‌ی hash خودش؛ (۹) truncation: حذف آخرین `CHECKPOINT` و همه‌ی ورودی‌های بعد از آن؛ (۱۰) بازنویسی کامل زنجیره از نقطه‌ی تغییر به بعد با hash های بازمحاسبه‌شده. موارد (۹) و (۱۰) فقط با مقایسه‌ی journal با رکوردهای هفت‌فیلدی منتشرشده در `checkpoint_publication_target` تشخیص داده می‌شوند (KAT-10). **(r5)** KAT-10b: `previous_publication` غیرتهی، رکورد هفت‌فیلدی با `published_at_utc` و `receipt` مقصد، و منفی‌های K10b-2..K10b-11 (`PREV_PUBLICATION_MISMATCH`، `MALFORMED_PUBLICATION`، `TARGET_TIME_REGRESSION`، `TARGET_TIME_ANOMALY`، `DUPLICATE_RECEIPT`). **(r6)** KAT-10c (SU1..SU10: انتشار ناموفق، جایگزینی با `EVENT(CHECKPOINT_SUPERSEDED)`، ترتیب پذیرش مقصد، رد retry قدیمی توسط writer و مقصد) و KAT-15a/b/c (گرامر زمان TS01..TS38، envelope E01..E18، مقدارها VL01..VL11): هیچ‌کدام exception نمی‌دهند و هر کدام verdict نام‌دار خود را می‌دهند.
- ☐ **D6** — تست چرخه‌ی عمر و ترتیب (KAT-6، KAT-9): ورودی `DECISION` بعد از resolution دست‌نخورده می‌ماند؛ outcome ناقص → `OUTCOME` نهایی `UNRESOLVABLE_*` با `Y = null` و `E02` (نه برچسب منفی)؛ نبودن `OUTCOME` یا `AUDIT` هیچ `ADJUDICATION`ی و هیچ `E02`/`E04`ی نمی‌دهد (PENDING)؛ هر دو ترتیب conflict (قبل و بعد از `DECISION`؛ قبل و بعد از `OUTCOME`) مطابق KAT-9a؛ سناریوهای F1..F6 (خطای finalizer، crash، تلاش دوباره، duplicate) مطابق KAT-9b؛ KAT-6 با بازمحاسبه‌ی verifier برابر است.
- ☐ **D7** — تست رد: `GAP_FILL` همیشه `p_raw = null` و `reject_code = R04` با `reject_reasons = ["R04","R03"]`؛ SCHEDULED دیرهنگام → `R03`؛ ترکیب چندگانه (`R03`، `R01`) ترتیب اولویت را رعایت می‌کند؛ ناوردایی `p_raw ≠ null ⇔ ACCEPTED` برقرار است.
- ☐ **D8** — تست collector با ساعت ساختگی و بدون اتصال شبکه: همه‌ی ردیف‌های KAT-8 (M01..M31 و U1..U6، از جمله `k.T`، V08 و حد ۴۰۹۶ نویسه‌ی V01)؛ تکراری یکسان، conflict، کندل گمشده، کندل با `latency_ms > 60000`، پیام `k.x = false`، restart و clock offset؛ هر کدام ورودی و کد مستند را می‌دهد؛ هیچ مسیر REST، فایل، پیام `MALFORMED` یا `FEED_MISMATCH` به `CANDLE` نمی‌رسد.
- ☐ **D9** — تست outcome: هیچ resolution قبل از R؛ close در `k = 97` اثر ندارد؛ `UNRESOLVABLE_*` فقط بعد از `R + 86400 s` و فقط اگر پنجره ناقص باشد؛ `OUTCOME` دوم برای همان `decision_seq` نامعتبر است و اولی حاکم می‌ماند.
- ☐ **D10** — هیچ پارامتر threshold هشدار در config مدل نیست؛ threshold نمایشی جدا و hash‌شده است.
- ☐ **D11** — `human_journal` جدا است؛ هیچ مسیر نوشتنی از آن به journal اصلی (جز `human_head_hash` در `CHECKPOINT`) وجود ندارد.
- ☐ **D12** — KAT-5 و KAT-7: کد متریک‌ها و bootstrap مقدارهای C.12 را (شبکه‌ی کامل، با skip) با همان نسخه‌ی numpy بازتولید می‌کند، دو اجرای پشت‌سرهم bit-for-bit یکسان‌اند، و مقدارهای ردشده‌ی الگوریتم فشرده (KAT-7 ب) را نمی‌دهد.
- ☐ **D13** — `CONFIG` ثبت شده: `feed_id`، `feed_url` (کامل، برابر C.2 بایت‌به‌بایت)، `stream_name`، حدها، `clock_policy` (دقیقاً پنج کلید؛ `ntp_sources` مرتب و دست‌کم دو منبع)، `rotation_policy`، `runtime_manifest`، `code_sha256` (tree hash پیش از `CONFIG`) و `checkpoint_publication_target` (شیء ده‌کلیدی B.7 بند ۴: نام، اداره‌کننده‌ی **مستقل از writer**، منبع زمان‌گذاری که **خودِ مقصد** است، نوع receipt و روش و مواد بررسی آن، کلاینت بازخوانی مستقل، دو namespace متمایز و `seq_monotonic_enforced_by_target`)؛ مقصد **انتخاب و مستقلاً تأیید شده** است (شرط lock)؛ تست end-to-end B.7 بند ۷ موفق بوده است (انتشار، بازخوانی مستقل، verifier، و truncation روی کپی → `TRUNCATED`).
- ☐ **D14** — `spec_lock ≤ collector_start ≤ T0 − 25 h`، warm-up ۲۸۸ کندل real-time کامل است و دست‌کم یک چرخش برنامه‌ریزی‌شده‌ی کامل اتصال (C.16) در شرایط واقعی انجام شده است.
- ☐ **D15** — `T0_DECLARATION` بعد از اولین چرخش برنامه‌ریزی‌شده‌ی کامل و قبل از T0 نوشته شده و hash های آن با `GENESIS` و `CONFIG` یکی است.
- ☐ **D16** — هیچ بررسی تطابق (parity) روی فایل‌های تاریخی (از جمله `mo_bin_2_8h_confirmation.csv`) انجام نمی‌شود. آن فایل‌ها سوخته‌اند و اجرای آن‌ها یک historical run است. تطابق فقط با KAT انجام می‌شود. (بازیابی ضرایب در A.5 یک‌بار و قبل از lock انجام شده است.)
- ☐ **D17** — بیانیه‌ی داده‌ی سوخته (بند ۰) در هر گزارش آینده آورده می‌شود.
- ☐ **D18** — gate spec و benchmark spec، شامل طول بلوک اصلی gate، قبل از اولین نگاه به متریک‌های `p`–`Y` و قبل از ارزیابی رسمی hash شده‌اند، و هر سه hash (gate، benchmark، کد تحلیل) با `EVENT(SPEC_REGISTRATION)` در journal ثبت شده‌اند (C.17)؛ manifest رسمی بدون آن‌ها `OFFICIAL_NEEDS_HASH` یا `HASH_NOT_REGISTERED` است.
- ☐ **D19** — endpoint: ثابت داخل کد = `CONFIG.feed_url` = `runtime_manifest.feed_url` = رشته‌ی C.2 (بایت‌به‌بایت)؛ شروع با URL دیگر رد می‌شود؛ یک handshake آزمایشی به `feed_url` (در مخزن dry-run خارج از شواهد، نه در journal) status `101` می‌دهد و یک پیام kline واقعی از `validate_kline` عبور می‌کند (از جمله `k.T = k.t + 299999`، V08)؛ همه‌ی URL های U2..U6 رد می‌شوند؛ اتصال جانشین چرخش هم فقط با همین URL پذیرفته می‌شود (C.16، RT6).
- ☐ **D20** — تست ساعت (KAT-11، KAT-11b): همه‌ی ردیف‌های CK01..CK22 (۲۳ ردیف)، KAT-11c (N01..N27 و CR1..CR8: قاعده‌ی قطعی offset با حساب میکروثانیه‌ی صحیح، منبع اصلی، حد شامل ۱۰۰۰ ms) و سناریوهای سطح journal. ساعت ۱۰ ثانیه عقب با پیام ۶۵ ثانیه دیر **`CANDLE` نمی‌شود** (CK02)؛ ساعت synchronized نیست → `CLOCK_INVALID` و بدون `CANDLE` (CK06، CK07)؛ ساعت بازیابی‌شده → کندل‌های بازه‌ی نامعتبر بدون backfill گم می‌مانند و اثرشان طبق KAT-11b است (`R06`، `R01`، `E02`)؛ رکورد ساعت (`clock_status`، offset، age، step) با هر `CANDLE`، `CANDLE_ANOMALY` و `DECISION` ذخیره می‌شود؛ verifier هر `CANDLE` غیرقابل‌استفاده (latency جعلی، offset بیش از حد، ساعت نامعتبر، latency بیش از ۶۰۰۰۰) را `DEVIATION(CANDLE_NONCONFORMING)` می‌گیرد و `R08` را فقط با رکورد ساعت ذخیره‌شده‌ی خود `DECISION` می‌پذیرد. **(r6)** KAT-16 (W01..W18): هر `CANDLE` و `CANDLE_ANOMALY` پیام خام و SHA-256 آن را دارد و verifier با اجرای دوباره‌ی `validate_kline` هر ناسازگاری را `WITNESS_MISSING` یا `WITNESS_MISMATCH` می‌گیرد.
- ☐ **D21** — تست برش as-of-S و manifest (KAT-12، r6): ژورنال انتزاعی J0 (با سه `SPEC_REGISTRATION` در seq 1..3) و گونه‌های J1 و J2 با AP1..AP9؛ `P` طبق زمان مقصد (نه `recorded_at_utc`) انتخاب می‌شود و مساوی شامل است؛ بدون `CHECKPOINT` منتشرشده تا `S` تحلیل رسمی نیست؛ ورودی‌ها و گزارش دسته‌ها (شامل `unavailable_in_prefix`) روی J0، J1 و J2 بایت‌به‌بایت یکسان‌اند و conflict و `ADJUDICATION` قبل و بعد از `P` و `S` هیچ اثری بر همان تحلیل ندارند؛ قاعده‌ی r4، قاعده‌ی ساعت نویسنده و خوانش بدون prefix رد می‌شوند؛ manifest `FJ-ANALYSIS-3` (۱۷ فیلد) با hash `11ae254a…`؛ منفی‌های PM1..PM29 (از جمله OFFICIAL بدون hash، hash ثبت‌نشده یا جایگزین‌شده، hash بدشکل، manifest منتشرنشده در namespace، ثبت `EVENT` پیش از انتشار manifest، رکورد تکراری یا بدشکل، و hash کد ناسازگار) و ویرایش هر فیلد manifest شناسایی می‌شوند.
- ☐ **D22** — تست‌های اتصال پیش از T0 (KAT-13): قطع اجباری (RT2)؛ شکست اتصال مجدد و backoff (RT2، RT3، RT7b)؛ چرخش موفق با همپوشانی و `DUPLICATE_IDENTICAL` (RT1)؛ کندل مرزی و گارد ۱۰ ثانیه‌ای (RT1، RT4)؛ conflict و URL غلط جانشین (RT5، RT6)؛ از دست رفتن اتصال بعد و پیش از READY (RT7a، RT7b)؛ سکوت (RT8)؛ بدون REST و backfill (RT9)؛ و منفی‌های verifier RTN1..RTN9. یک چرخش کامل با سیاست واقعی در warm-up انجام شده است (فقط رویه‌ی چرخش را می‌آزماید، نه حد مستندشده و نه رفتار عملیاتی عمر اتصال؛ رفتار عملیاتی را اتصال مشاهده‌ای dry-run می‌سنجد، C.16).
- ☐ **D23** — ترتیب پیش از T0 و hash کد (C.1، KAT-14): ترتیب دقیق freeze spec ← build/test ← code hash ← CONFIG ← تست‌های anchoring ← warm-up ← T0؛ `code_sha256` tree hash است و پیش از `CONFIG` محاسبه شده؛ کد hash `CONFIG` را در خود ندارد؛ `COLLECTOR_START.code_tree_sha256 = CONFIG.code_sha256`؛ verifier هر جابه‌جایی ترتیب را تشخیص می‌دهد (B.6 بند ۱۴).
- ☐ **D24** — verifier تام و سخت‌گیر (r6): KAT-15a/b/c، KAT-16 و KAT-10c پاس شده‌اند؛ هیچ ورودی بدشکلی (تاریخ ناممکن، ماه ۱۳، ساعت ۲۴، ثانیه‌ی ۶۰، رقم غیر ASCII، `\n` پایانی، کلید اضافه‌ی envelope، عدد اعشاری یا بزرگ، `null` به‌جای شیء) verifier را با exception نمی‌اندازد و هر کدام verdict نام‌دار خود را می‌گیرد (`VERIFIER_EXCEPTION` در هیچ اجرای قراردادی ظاهر نمی‌شود).

---

## پیوست ۱ — نگاشت ۱۷ شرط GPT به بندها

| شرط | بند |
|---|---|
| ۱ target دقیق و بدون تغییر | A.6 |
| ۲ وزن‌های frozen | A.5 |
| ۳ زمان تصمیم و availability | A.2، A.3 |
| ۴ T0 مشخص و غیرقابل تغییر | C.1، B.3 |
| ۵ لاگ احتمال خام در شبکه‌ی ثابت | C.4، C.5 |
| ۶ outcome فقط بعد از ۹۶ کندل بسته | C.6 |
| ۷ حداقل فیلدهای هر رکورد | B.3، B.5 |
| ۸ عدم انتخاب threshold هشدار | A.7، C.10 |
| ۹ جدایی threshold های UI | C.10 |
| ۱۰ قواعد داده‌ی ناقص، تکراری، دیرکرد، restart | C.8 |
| ۱۱ متریک‌های از قبل تعیین‌شده | C.12 |
| ۱۲ حداقل نمونه بدون توقف زودهنگام | C.13 |
| ۱۳ تعریف رکورد معتبر و رد‌شده | C.3 تا C.7 |
| ۱۴ جدایی پیش‌بینی از تصمیم انسانی | B.4، C.9 |
| ۱۵ داده‌ی سوخته | بند ۰ |
| ۱۶ فقط داده‌ی forward پس از T0 | بند ۰، C.14 |
| ۱۷ هش‌پذیر و قابل قفل قبل از T0 | B.2، C.1، C.15 |

## پیوست ۲ — نگاشت اصلاح‌های r1 به r2