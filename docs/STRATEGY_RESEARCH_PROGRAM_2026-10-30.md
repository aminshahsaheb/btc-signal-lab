# برنامه‌ی مهندسی پژوهش برای رسیدن به استراتژی قابل‌اجرا — v1
**تاریخ:** 2026-10-30  
**وضعیت:** برنامه‌ی پژوهشی؛ هیچ استراتژی جدیدی قفل یا تأیید نشده است.

## 1. مأموریت

هدف، ساخت یک سیستم BTC برای یافتن فرصت‌های معاملاتی قابل‌اجرا با شواهد قابل‌ممیزی است؛ نه تولید اجباری سیگنال یا وعده‌ی بازده روزانه.

دو مسئله مستقل‌اند:
1. **WHEN:** چه زمانی احتمال حرکت معنادار (مثلاً ۱ تا ۲ درصد در افق مشخص) بالا می‌رود تا معامله‌گر دستی چارت را بررسی کند؟
2. **DIRECTION + EXECUTION:** آیا Long یا Short در زمان و قیمت قابل‌اجرا، پس از هزینه و لغزش، امید ریاضی مثبت دارد؟

Move-Odds فقط مسئله‌ی اول را هدف می‌گیرد. مدل احتمال حرکت به‌تنهایی استراتژی Long/Short نیست. برای معامله باید جهت، ورود، خروج، ریسک و اجرای مستقل سنجیده شوند. هدف ۱ تا ۵ درصد سود روزانه معیار پذیرش پژوهش نیست.

## 2. وضعیت شواهد

### 2.1 داده‌ی تاریخی موجود

مخزن شامل BTCUSDT پنج‌دقیقه‌ای با 602,208 کندل از 2021-01-01 تا 2026-09-22 است. ستون‌ها: timestamp، OHLC، base volume و taker_buy_base. بررسی ساختاری ثبت‌شده: بدون timestamp تکراری، گپ پنج‌دقیقه‌ای، null یا OHLC نامعتبر. SHA-256 فایل استخراج‌شده با ورودی مورد انتظار Atlas مطابقت دارد.

محدودیت‌ها:
- داده برای discovery، confirmation، انتخاب مدل و تحلیل‌های قبلی استفاده شده؛ holdout پاک برای ادعای تازه نیست.
- hash تطبیق با Atlas، provenance مستقل صرافی را اثبات نمی‌کند.
- فایل شامل order book، tick trades، OI، funding، DVOL یا liquidation tape کامل نیست.
- آخرین کندل 2026-09-22 است، نه داده‌ی زنده یا آخرین.

در آرشیو قدیمی Bitstamp یک‌دقیقه‌ای، دقیقه‌های زیادی با کندل تخت و حجم صفر پر شده‌اند؛ برای ادعای microstructure یا fill دقیق مناسب نیست مگر با ماسک کیفیت.

### 2.2 خانواده‌های جهت‌دار بررسی‌شده

دفتر پژوهش نتایج زیر را ثبت کرده است:
- Bridge v1 / MA sequence + EMA50 pullback: FAIL؛ 2,498 معامله، PF=0.66 و افت مرکب گزارش‌شده 83%-.
- MA-ribbon stepwise order: ARTIFACT؛ random-walk control بخش عمده‌ی الگو را بازتولید کرده است.
- Ribbon completion moment: FAIL.
- Volume delta / taker imbalance proxy: FAIL یا فاقد انتقال پایدار بین splitها.
- Funding level، basis و expiry reversal: رد یا نامعتبر تحت قواعد ازپیش‌ثبت‌شده.
- Momentum(20)+Reversal(3): روی Binance شکست؛ 354 معامله با PF=1.014 و holdout گزارش‌شده 56 معامله با PF=0.912.
- Ensemble2: در گزارش 18 بلوک، 11/18 بلوک مثبت، میانگین بازده بلوک +1.28% با SD=3.00%، t-test حدود p=0.089 و sign-test حدود p=0.240 گزارش شده است. برتری paired نسبت به Momentum-only نیز p=0.228 بود. ممیزی بعدی تنها شاهد نسبتاً تازه‌ی 2025–26 را 57 معامله، PF=1.058 و سود +1.07% توصیف کرد؛ این شاهد برای ادعای مزیت اقتصادی قوی نیست.
- SMC با آزمون بازده کندل بعدی به‌تنهایی نه اثبات و نه رد قطعی استراتژی کامل محسوب می‌شود.

هیچ‌یک از این خانواده‌ها با تغییر threshold، معکوس‌کردن جهت یا انتخاب مجدد پنجره روی همان داده «نجات» داده نمی‌شوند.

### 2.3 نامزد Ribbon + EMA50 Support

در آرشیو، یک نسخه در تقسیم ثابت train/test نتایج زیر داشته است:
- Train 2018–2023: 417 معامله، WR=39.1%، PF=1.220، Net=+34.6%، Sharpe=0.914، DD=-5.3%.
- Test 2023–2025: 76 معامله، WR=42.1%، PF=1.351، Net=+8.4%، Sharpe=0.922، DD=-6.0%.

این نتایج فقط یک **نامزد پژوهشی** می‌سازند:
- walk-forward کامل برای همین نسخه در دست نیست؛
- candle-path Monte Carlo اجرا و تأیید نشده؛
- harness Jesse هشدار داده signature خط لوله‌ی MovingBlockBootstrapCandlesPipeline، کلیدهای metrics، ترتیب ستون‌های candle و بعضی propertyها باید در محیط واقعی بررسی شوند؛
- نسخه‌های مختلف Ribbon و ترتیب EMAها نباید با هم مخلوط شوند؛ هرکدام شناسه و hash مستقل می‌خواهند.

### 2.4 Move-Odds و H-MOVE

- MO-BIN-2%-8h-v1 در confirmation، AUC حدود 0.672 و BSS نسبت به baseline قدیمی حدود +0.104 داشت، اما احتمال‌ها بیش‌برآورد بودند و slope کالیبراسیون حدود 0.784 بود.
- M-RECAL-02 در confirmation شرط تجمیعی را پاس نکرد: بهبود نقطه‌ای Brier مثبت بود، اما هیچ‌یک از پنج بازه‌ی اطمینان بلوکی صفر را کنار نگذاشتند؛ حکم ثبت‌شده FAIL است.
- H-MOVE-04 Stage 1 روی discovery طبق gate لفظی خود PASS شد، اما این PASS به‌تنهایی مزیت مستقل یا قابل‌معامله نیست. تعدیل تقویمی رابطه را شدیداً تضعیف کرد؛ ضریب تعدیل‌شده نزدیک صفر و CI شامل صفر بود. D3 و تشخیص‌های پسینی نیز وابستگی به تقویم/هم‌پوشانی با Move-Odds را برجسته کردند. بسته صریحاً confirmation و holdout را نخوانده است. وضعیت بعدی ثبت‌شده STOPPED / heavily flagged است.
- H-MOVE-04 spec hash: `421682e1cbd9fb186e00c4857fa1296898caad15a765e5582988c5af5412b5db`. این hash متعلق به spec فریز‌شده‌ی Stage 1 است، نه کل ZIP.
- D-LIQ r1 درباره‌ی snapshotهای تحویلی forceOrder است؛ هنوز draft، بدون collector، بدون T0 و بدون داده‌ی امتیازدهی‌شده است. این فید snapshot، کل liquidation tape نیست و r1 موانع P0/P1 دارد.

## 3. اولویت مهندسی

### اولویت 0 — حفظ حقیقت
- مخزن Private بماند.
- PR اصلاح مستندات همگام‌سازی پس از سبزشدن CI تکمیل شود.
- نسخه‌ها و hashها حفظ شوند؛ فایل تاریخی overwrite نشود.
- هر عدد همراه artifact، کد، split، هزینه و روش محاسبه گزارش شود.

### اولویت 1 — ممیزی یک candidate معاملاتی، بدون جستجوی عدد طلایی

نامزد نخست برای ممیزی مهندسی: **نسخه‌ی دقیق Ribbon + EMA50 Support که نتایج 417/76 را تولید کرده است.**

قبل از هر آزمون:
1. کد اصلی دقیق و dependencyها بازیابی شوند؛ بازسازی از حافظه ممنوع.
2. hash کد، تنظیمات، داده، fee، fill model، sizing، stop/target و intrabar rules ثبت شوند.
3. ورود/خروج، next-open fill، gap-through-stop/target و same-candle tie-break مستقل تست شوند.
4. Python/Jesse replica و Pine از نظر رویدادبه‌رویداد تطبیق داده شوند؛ TradingView compile واقعی جدا ثبت شود.
5. معلوم شود نتایج train/test با کد و داده‌ی دقیق قابل بازتولیدند یا نه.

اگر کد اصلی یا قرارداد اجرای واقعی قابل بازیابی نباشد، این candidate قابل ارزیابی نیست و نباید کد مشابهی ساخته و نتایج قبلی به آن نسبت داده شود.

### اولویت 2 — اعتبارسنجی نامزد Ribbon

پارامتر تازه‌ای جستجو نشود. نسخه‌ی موجود freeze شود و پروتکل مستقل قبل از مشاهده‌ی خروجی جدید نوشته شود.

دروازه‌ها:
- بازتولید دقیق نتایج قبلی؛
- baselineهای منصفانه (buy/hold، trend-only یا random-entry با همان stop/target، زمان حضور، exposure و هزینه)؛
- walk-forward بلوکی با purge/embargo متناسب با holding period؛
- fee، spread، slippage، funding و محدودیت leverage؛
- Monte Carlo مسیر کندل با حفظ OHLC consistency و وابستگی زمانی؛ shuffle معاملات آزمون وجود edge نیست؛
- block bootstrap، confidence interval، شمارش آزمون‌ها، Deflated Sharpe / PBO یا معادل؛
- گزارش رژیم/سال فقط تشخیصی، نه مجوز انتخاب رژیم پس از مشاهده؛
- در صورت FAIL یا INCONCLUSIVE، بستن شاخه طبق قاعده‌ی ازپیش‌ثبت‌شده.

داده‌های تاریخی قبلاً دیده‌شده فقط برای بازتولید و ممیزی‌اند؛ holdout تازه نیستند. تأیید نهایی باید از داده‌ی آینده و paper trading شروع شود.

### اولویت 3 — Move-Odds به‌عنوان هشدار مستقل

Move-Odds v3 می‌تواند مسئله‌ی WHEN را بررسی کند، اما پیش‌ثبت خودش باید تکمیل و قفل شود. baseline ضروری: hour-of-week با ساعت نیویورک × نرخ پایه‌ی ۳۰ روزه. مدل پیچیده‌تر فقط وقتی ارزش دارد که در walk-forward از baseline عبور کند.

Move-Odds هرگز نباید به جهت Long/Short تعبیر شود.

### اولویت 4 — D-LIQ مستقل و کم‌اولویت‌تر

D-LIQ r1 تا رفع همه‌ی موانع قفل نمی‌شود:
- bootstrap algorithm و analysis code/hash؛
- اعتبار پیام و malformed attribution؛
- deduplication/fingerprint contract؛
- sample counts و NO_PRICE؛
- PASS/FAIL/INCONCLUSIVE؛
- journal/anchoring مستقل و end-to-end؛
- dry-run فید، clock و uptime.

قبل از پروتکل کامل و probe مجاز، collector دائمی یا سرور خریداری نشود.

## 4. معماری سیستم

1. **Data plane:** داده‌ی خام venue، timestamp exchange/receive، sequence/connection، gap، clock health، provenance و schema version.
2. **Research plane:** feature builders قطعی، point-in-time guards، experiment registry، split registry، model artifacts و تحلیل آماری.
3. **Signal plane:** خروجی سه‌حالته LONG / SHORT / NONE، calibration و علت عدم صدور سیگنال.
4. **Risk plane:** sizing، stop/target، سقف زیان روزانه، leverage، هزینه و رد معامله‌ی نامعتبر.
5. **Execution plane:** ابتدا paper؛ ثبت bid/ask، order intent، fill، partial fill، reject، fee، funding و slippage در venue هدف.
6. **Evidence plane:** append-only journal، hash chain، manifest، checkpoint، independent readback و نسخه‌ی قابل‌بازتولید.

سیگنال Binance بدون اندازه‌گیری spread/fill/funding به KCEX منتقل نمی‌شود. قیمت مرجع و قیمت اجرای کاربر دو منبع متفاوت‌اند.

## 5. دروازه‌ی ورود به سرمایه

هیچ استراتژی وارد سرمایه‌ی واقعی نمی‌شود مگر اینکه:
- کد و داده نسخه‌دار و قابل‌بازتولید باشند؛
- out-of-sample/forward test ازپیش‌ثبت‌شده داشته باشد؛
- سود خالص پس از هزینه و لغزش مثبت باشد؛
- confidence interval و drawdown قابل‌قبول باشند؛
- نسبت به baseline هم‌ریسک مزیت نشان دهد؛
- نتیجه به یک سال/رژیم یا چند معامله‌ی بزرگ وابسته نباشد؛
- paper trading در venue هدف با ثبت fill واقعی قابل‌قبول باشد؛
- ریسک هر معامله و سقف زیان روزانه از قبل تعیین شده باشد.

پس از عبور، سرمایه‌ی اولیه کوچک و محدود به بودجه‌ی زیان ازپیش‌تعیین‌شده است. افزایش سایز برای جبران افت ممنوع است.

## 6. محصول و بازاریابی

تا پیش از اثبات edge، محصول را «سیگنال سودده» معرفی نکنیم.

جایگاه‌یابی اولیه:
- BTC market-movement alerting؛
- هشدار احتمال حرکت، نه وعده‌ی جهت؛
- risk-first trade planning؛
- journal و evidence trail؛
- گزارش false alerts، calibration، frequency، uptime و هزینه.

پس از شواهد forward، می‌توان قابلیت‌های اندازه‌گیری‌شده را در نسخه‌ی رایگان/آزمایشی و حرفه‌ای عرضه کرد. هیچ ادعای win-rate یا سود ماهانه بدون نمونه‌ی کافی و گزارش مستقل منتشر نشود. بازاریابی باید بر شفافیت، اندازه‌گیری و کنترل ریسک باشد، نه اسکرین‌شات سود یا وعده‌ی ۱–۵٪ روزانه.

## 7. ترتیب اجرایی

1. تکمیل PR مستندات همگام‌سازی پس از سبزشدن CI.
2. بازیابی فایل اصلی Ribbon + EMA50 Support، داده/تنظیمات دقیق و خروجی خام train/test.
3. بازتولید صرفاً ممیزی (بدون تغییر پارامتر و بدون ادعای holdout تازه).
4. نوشتن preregistration frozen برای walk-forward و candle-path stress test.
5. پس از تأیید صریح lock، اجرای آزمایش.
6. اگر PASS: paper-forward در venue هدف و سپس تصمیم درباره‌ی سرمایه‌ی کوچک؛ اگر FAIL/INCONCLUSIVE: بستن شاخه، بدون rescue.
7. به‌صورت موازی اما مستقل، تکمیل preregistration Move-Odds v3 برای WHEN.

## 8. موارد تأییدنشده / نیازمند بازیابی

- کد اصلی دقیق Ribbon + EMA50 Support که نتایج 417/76 را تولید کرده؛
- محیط Jesse و نسخه‌ی dependencyها برای اجرای مستقل Monte Carlo؛
- TradingView compile برای Move-Odds v0.1.2 و Risk-First Helper v0.3.1؛
- داده‌ی point-in-time معتبر OI/DVOL/tick/order-book برای فرضیه‌های چندویژگی؛
- collector زنده، D-LIQ T0 و forward journal قفل‌شده؛
- fills و هزینه‌های timestamp-aligned در KCEX.

این موارد با تخمین یا بازسازی از حافظه جایگزین نمی‌شوند.

## حکم اجرایی

**فعلاً هیچ استراتژی سوددهی تأیید نشده است.** نزدیک‌ترین candidate قابل ممیزی برای ساخت استراتژی معامله‌پذیر، نسخه‌ی دقیق Ribbon + EMA50 Support است؛ اما فقط به‌عنوان candidate برای بازتولید و اعتبارسنجی سخت‌گیرانه. Move-Odds مسیر جداگانه‌ی هشدار زمان حرکت است. D-LIQ هنوز draft و فاقد داده‌ی زنده است.

هیچ آزمایش تازه‌ای روی داده اجرا نمی‌شود تا preregistration آن کامل، hash شود و به‌صراحت قفل گردد.
