# پژوهش جهانی ابزارهای تحلیل بیت‌کوین و بازار مشتقات — نسخهٔ گسترش‌یافته ۲

**تاریخ بررسی:** ۲۴ اکتبر ۲۰۲۶  
**هدف عملی:** کمک به معاملهٔ دستی BTC، مقایسهٔ داده‌های چندمنبعی و کنترل ریسک؛ بدون اتصال حساب صرافی، بدون ارسال سفارش، و بدون ادعای سیگنال سودآور.  
**دامنه:** ابزارهای نمودار و تحلیل، دادهٔ خام و API صرافی، مشتقات، Order Flow و دفتر سفارش، آپشن، آن‌چین، جریان ETF/سرمایه، رویدادهای کلان، دادهٔ تاریخی، بک‌تست و ابزارهای توسعه.

## پاسخ روشن به سؤال «آیا هیچ‌چیز از قلم نیفتاده؟»

**نه؛ نمی‌توانم تضمین کنم هیچ ابزار یا منبعی در جهان از قلم نیفتاده است.** هیچ جست‌وجوی وبی نمی‌تواند همهٔ سرویس‌های خصوصی، محلی، نوپا، دعوت‌محور، بسته یا تازه‌منتشرشده در همهٔ کشورها را به‌طور قطعی فهرست کند. گزارش قبلی نیز فهرست اولویت‌بندی‌شده بود، نه سرشماری کامل جهانی.

در این نسخه، پوشش را گسترده‌تر و روش‌مندتر کردم: یک فهرست کشف ابزار با ۱۰۸ محصول در ۸ دسته (به‌روزرسانی ۹ اکتبر ۲۰۲۶)، یک فهرست جامعه‌محور با حدود ۱۹۳ سرویس و ابزار معامله‌گری، مستندات رسمی چند صرافی بزرگ، چند منبع دادهٔ نهادی و بازار آپشن، منابع آن‌چین و ETF، و تقویم‌های رسمی کلان را کنار هم گذاشتم. این فهرست‌ها **فهرست کشف‌اند، نه ممیزی عملی تک‌تک محصولات**؛ فهرست ۱۰۸تایی نیز در زمان مشاهده هیچ محصولی را hands-on tested علامت نزده بود. بنابراین من هم نباید ادعا کنم همه را نصب، استفاده یا از نظر دقت مستقلاً تأیید کرده‌ام. منابع روش‌شناسی: [CryptoMarkets.tools](https://cryptomarkets.tools/) و [trading-awesome directory](https://git.mitgai.net/lentrade/trading-awesome).

### چه چیزی در نسخهٔ ۲ اضافه شده است؟

- **ابزارهای تازهٔ تجمیع داده:** Coinperps، Basis Charts، Swolecharts، CoinAnk و ابزارهای کشف بازار مثل CryptoMarkets.tools.
- **دادهٔ مستقیم از خود venueها:** مستندات رسمی Binance، Bybit، OKX، Bitget، Gate، Hyperliquid، Coinbase و CME؛ همراه با محدودیت تاریخچه یا زمان‌بندی‌هایی که برای بعضی APIها مهم‌اند.
- **دادهٔ تخصصی آپشن:** SignalPlus، Newhedge، Derivasys، Hedgehog Data و Alpha Finance در کنار Laevitas و Deribit.
- **دادهٔ DEX/پرپچوال آن‌چین و ریزساختار:** 0xArchive، Hyperliquid، Lighter، dYdX، Bitquery، Allium و Nansen.
- **توسعه و آزمون تاریخی:** CCXT، cryptofeed، Backtesting.py، HftBacktest، NautilusTrader، LEAN/QuantConnect، VectorBT و ابزارهای مرتبط.
- **منابع کلان رسمی در چند منطقه:** تقویم‌های Fed، BLS، BEA، ECB، Bank of England، Bank of Japan، RBA، Bank of Canada و RBNZ؛ نه ادعای پوشش تمام کشورها.

## ۱. خلاصهٔ اجرایی: چه چیزهایی ارزش استفادهٔ واقعی دارند؟

### پشتهٔ اولیهٔ کم‌هزینه برای تو

1. **TradingView** — نمودار اصلی، Pine Script و هشدارها؛ محاسبات ریسک روی نمودار.
2. **Basis Charts** — آزمایش یک محیط چندپنلی برای قیمت، مشتقات، آپشن و Order Flow، مشروط به بررسی نماد، زمان‌مهر و کیفیت داده.
3. **Swolecharts** — یک نمای سریع برای OI، Funding، لیکوئید و screenerها.
4. **فقط یکی از CoinGlass / CoinAnk / Coinalyze / Coinperps** — برای مقایسهٔ مشتقات؛ نه اینکه همه را هم‌زمان به‌عنوان تأیید مستقل بشماریم.
5. **فقط یکی از Bookmap / GoCharting / Exocharts / TradingLite / TensorCharts** — برای دفتر سفارش، Footprint و جریان معاملات؛ انتخاب بر اساس کیفیت دادهٔ همان بازار و هزینه.
6. **منابع رسمی venue** — برای کنترل نهایی قیمت، Funding، OI و Order Book همان بازار اجرا.
7. **Farside/SoSoValue + تقویم رسمی رویدادها** — فقط برای زمینهٔ روزانه و ریسک رویداد.
8. **Laevitas / Deribit DVOL / Basis Options / SignalPlus** — مرحلهٔ بعدی، فقط اگر فرضیهٔ معامله واقعاً از دادهٔ آپشن استفاده کند.

**اولویت اول نیست:** خرید اشتراک‌های گران دادهٔ tick/L2، نصب چند ترمینال تکراری، ربات اجرا یا اتصال کلید API خصوصی. تا وقتی مزیت معاملاتی تأیید نشده، هزینهٔ چنین زیرساختی را توجیه نمی‌دانم.

## ۲. واقعیت «کل کشورها»: بازار را باید بر اساس venue و قرارداد پوشش داد، نه فقط کشور

بیت‌کوین یک قیمت مرکزی واحد ندارد. قیمت، اسپرد، OI، Funding، قرارداد، عمق دفتر سفارش و زمان تأمین داده می‌تواند بین صرافی‌ها فرق کند. بنابراین «دادهٔ همهٔ کشورها» را نمی‌شود معادل یک API دانست؛ روش درست، پوشش venueهای اصلی و مستندسازی venueهایی است که هر سرویس در واقع شامل می‌شود.

### منابع رسمی venue و آنچه باید از آن‌ها گرفت

| venue / منبع | دادهٔ رسمی مهم | محدودیت یا نکته‌ای که باید در نظر گرفت | لینک رسمی |
|---|---|---|---|
| Binance USDⓈ-M / COIN-M Futures | کندل، معامله، Mark/Index price، Funding، OI، order book و بعضی تاریخچه‌ها | API تاریخچهٔ OI در برخی endpointها پنجرهٔ محدود (مثلاً ۳۰ روز برای endpoint خاص) دارد؛ نباید از API جاری، آرشیو کامل از ۲۰۲۱ فرض کرد. | [Docs](https://developers.binance.com/docs/derivatives/usds-margined-futures/market-data) · [Public data](https://github.com/binance/binance-public-data) |
| Bybit | کندل، order book، معاملات، Mark/Index price، Funding history، OI، historical volatility و L/S ratio | پاسخ‌های OI صفحه‌بندی می‌شوند و تعداد نقاط هر پاسخ محدود است؛ پوشش/تاریخچه بر اساس نماد متفاوت است. | [V5 API](https://bybit-exchange.github.io/docs/v5/market/open-interest) |
| OKX | کندل، معاملات، order book، Funding و مشتقات | مستندات دربارهٔ cache جداگانهٔ endpointهای بازار هشدار می‌دهند؛ درخواست‌های پشت‌سرهم لزوماً snapshot کاملاً هم‌زمان نمی‌دهند. کندل ۱ثانیه‌ای تاریخچهٔ کوتاه‌تری از بازه‌های بلندتر دارد. | [API docs](https://www.okx.com/docs-v5/en/) |
| Bitget | ticker، best bid/ask، mark/index، OI، Funding و تاریخچهٔ کندل/معاملات منتخب | پوشش بازار و عمق تاریخچه باید برای قرارداد دقیق کنترل شود؛ Data Download Center با endpointهای لحظه‌ای یکی نیست. | [API docs](https://www.bitget.com/api-doc/common/intro) · [Download center](https://www.bitget.com/en/fee/data-download) |
| Gate.io | قراردادها، Funding، mark/index price و order-book updates | نوع قرارداد و بازهٔ Funding را برای همان نماد بخوان؛ دادهٔ mark price را با آخرین معامله یکی نکن. | [API docs](https://www.gate.com/docs/developers/apiv4/en/) |
| Coinbase | بازار نقدی، order book و public trades در APIهای عمومی | Coinbase Advanced Trade را با Coinbase International derivatives اشتباه نگیر؛ endpoint هر محصول متفاوت است. | [Market data](https://docs.cdp.coinbase.com/advanced-trade/docs/ws-overview) |
| Kraken | بازار نقدی، معاملات و order book؛ برخی محصولات مشتقه بر اساس منطقه/محصول جدا هستند | دسترسی و محصول‌های مشتقه بر حسب کشور و حساب ممکن است متفاوت باشد؛ صرف وجود API عمومی به معنای دسترسی قانونی همهٔ کاربران نیست. | [API docs](https://docs.kraken.com/api/) |
| Deribit | بازار آپشن و فیوچرز، زنجیرهٔ آپشن، IV و DVOL | مرجع مهم برای آپشن BTC، ولی نمای آن به‌تنهایی کل بازار آپشن یا همهٔ venueهای دیگر نیست. | [API docs](https://docs.deribit.com/) · [DVOL data](https://docs.deribit.com/api-reference/market-data/public-get_volatility_index_data) |
| CME Group | فیوچرز/آپشن‌های نهادی، حجم و Open Interest گزارش‌شده | دادهٔ روزانه/گزارش نهایی با تأخیر، برای زمینه و positioning نهادی مفید است؛ ماشهٔ ورود ۱۵دقیقه‌ای نیست. | [Crypto product data](https://www.cmegroup.com/markets/cryptocurrencies.html) · [Volume & OI reports](https://www.cmegroup.com/market-data/volume-open-interest.html) |
| Hyperliquid | perpetual DEX، trades، order book و کندل از public info API | برخی endpointها کل تاریخچه را یک‌جا نمی‌دهند؛ `candleSnapshot` حداکثر ۵۰۰۰ کندل در هر فراخوانی دارد و باید صفحه‌بندی کرد. | [API docs](https://hyperliquid.gitbook.io/hyperliquid-docs/for-developers/api) |
| dYdX | perpetual DEX، trades، market data و order book | دیتای on-chain/perp را با قراردادهای CEX یک‌کاسه نکن؛ ساختار بازار و timestamp متفاوت است. | [Developer docs](https://docs.dydx.exchange/) |
| Lighter | perpetual DEX و API بازار | منبع جدا برای دادهٔ DEX؛ کیفیت تاریخچه و عمق باید عملی کنترل شود. | [Docs](https://docs.lighter.xyz/) |
| BitMEX | قراردادهای مشتقهٔ کریپتو، معاملات، Funding و order book | یکی از venueهای تاریخی مشتقات؛ پوشش بازار و نماد را به نیاز امروز BTC تطبیق بده. | [API explorer](https://www.bitmex.com/app/apiOverview) |
| Crypto.com Exchange | بازار نقدی و مشتقات با APIهای جداگانه | پوشش قراردادها و دسترسی قانونی وابسته به محصول و منطقه است. | [API docs](https://exchange-docs.crypto.com/exchange/v1/rest-ws/index.html) |

این فهرست، **venueهای مهمی که ارزش پوشش دارند** را شامل می‌شود؛ فهرست همهٔ صرافی‌های محلیِ تمام کشورها نیست. برای هر venue باید جداگانه بررسی کرد: قرارداد دقیق، حجم واقعی، spread، Funding period، precision/tick size، تاریخچه، delay، وضعیت مجازبودن سرویس برای محل استفاده و امکان برداشت. از مخفی‌کردن محل حضور یا دورزدن محدودیت‌های سرویس استفاده نکن.

## ۳. دستهٔ تازه: ترمینال‌های تجمیعی که ممکن است چند پنجره را حذف کنند

| ابزار | چه چیزی را ادعا می‌کند؟ | چه زمانی ارزش آزمایش دارد؟ | محدودیت/تأیید لازم |
|---|---|---|---|
| [Basis Charts](https://www.basischarts.com/) | نمودار، footprint/Order Flow، مشتقات، گزینه‌های آپشن، screener و ابزارهای بازبینی در یک محیط | وقتی می‌خواهی تعداد پنجره‌های باز را کم کنی | ادعای ارائه‌دهنده است؛ باید timestamp، venue، نماد، export و تأخیر واقعی را امتحان کنیم. |
| [Swolecharts](https://swolecharts.com/) | OI/Funding/لیکوئید، تغییر حجم، CVD، screeners و liquidity heatmap | برای نظارت رایگان و شروع سریع | دادهٔ لیکوئید در برخی venueها ممکن است sampled یا ناقص باشد؛ راهنمای coverage خودش را بخوان. |
| [Coinperps](https://www.coinperps.com/) | نمای تجمیعی مشتقات، Funding، OI، لیکوئید و نسبت‌ها از چندین exchange | برای مقایسهٔ سریع و یافتن حرکت‌های غیرعادی در چند بازار | ابزار کشف/نمای کلی؛ روش تجمیع، کامل‌بودن liquidation و عمق تاریخچه را قبل از استفادهٔ تصمیمی کنترل کن. |
| [CoinGlass](https://www.coinglass.com/) | دادهٔ مشتقات چند venue، نقشهٔ لیکوئید، OI، Funding و API | وقتی نقشه و تاریخچهٔ مشتقات لازم است | تعرفه و endpointها پلن‌محور است؛ liquidation map مدل است، نه نقشهٔ تضمینی قیمت آینده. |
| [CoinAnk](https://coinank.com/) | OI، Funding، نقشهٔ لیکوئید، نسبت‌ها، ETF و سنجه‌های depth | جایگزین برای مقایسه با CoinGlass | منبع underlying را بررسی کن؛ شباهت نمودارها الزاماً تأیید مستقل نیست. |
| [Coinalyze](https://coinalyze.net/) | OI/Funding/لیکوئید و نمودارهای مشتقات و API | cross-check و دریافت دادهٔ محدود | تاریخچهٔ intraday و تعداد نقاط محدود است؛ برای بازسازی چندساله کافی‌بودن را فرض نکن. |
| [The Kingfisher](https://thekingfisher.io/liquidations-map) | نقشهٔ تخمینی نواحی لیکوئید و positioning | سناریوسازی نواحی فشار | مدل‌محور؛ جایگزین دادهٔ ثبت‌شدهٔ لیکوئید نیست. |
| [Hyblock Capital](https://hyblockcapital.com/) | سنجه‌های positioning، نسبت retail/whale، screener و مدل‌های مشتقات | وقتی شاخص مشخصی نیاز داری که در منابع رایگان نیست | قیمت و تعریف شاخص‌ها باید از صفحهٔ جاری بررسی شود؛ مدل‌های اختصاصی را واقعیت مشاهده‌شده فرض نکن. |
| [Velo](https://velo.xyz/) | Funding، basis، OI، CVD و تحلیل cross-exchange | اگر تفاوت venueها بخش مهم فرضیه باشد | دسترسی فعلی و تاریخچه بر اساس پلن بررسی شود. |
| [D.Terminal](https://dterminal.trade/) | پنل‌های مشتقات، screener و heatmap | گزینهٔ مقایسه با Coinalyze/Swolecharts | قدمت، timestamp، پوشش و pricing پیش از اتکا تأیید شود. |
| [TradingView](https://www.tradingview.com/) | نمودار و دادهٔ نمادهای پشتیبانی‌شده و Pine | محل اصلی اسکریپت ریسک | Pine اسکریپت‌ها به هر API آزاد دسترسی ندارند؛ دادهٔ چند venue فقط در صورت داشتن نماد/دادهٔ مناسب. |

### یک گزینهٔ دادهٔ DEX که در فهرست قبلی نبود

[0xArchive](https://0xarchive.io/) روی داده‌های Hyperliquid و Lighter متمرکز است و L2/L3/L4، چرخهٔ عمر سفارش، معاملات، لیکوئیدها، Funding، OI و ابزار replay/خروجی آرشیوی را تبلیغ می‌کند. برای کسی که فقط Binance USDT perpetual معامله می‌کند، اولویت نخست نیست؛ برای تحقیق دربارهٔ پرپچوال‌های DEX یا دادهٔ order-level، گزینهٔ مهمی برای بررسی است. [محدودیت:** قیمت و ادعای پوشش از صفحهٔ ارائه‌دهنده است و اینجا با اجرای واقعی مستقل نشده است.**]

AGGR نیز در فهرست اکتشافی به‌عنوان tape چندصرافی و نمایش لیکوئید متن‌باز آمده، اما پیش از نصب باید repo رسمی/نگهداری، منبع داده و مدل امنیتی آن را جداگانه تأیید کرد. فقط از نام در یک کاتالوگ برای اجرای کد ناشناس استفاده نکن.

## ۴. Order Flow، Footprint، DOM و Heatmap: مواردی که باید با هم مقایسه شوند

| ابزار | نوع داده/کارکرد | مناسب چه چیزی است؟ | نکتهٔ کلیدی |
|---|---|---|---|
| [Bookmap](https://bookmap.com/en/crypto) | نقشهٔ سفارشات محدود، حجم، CVD، قیمت‌سطوح، Replay و Multibook | تغییرات نقدشوندگی و تعامل قیمت با دفتر سفارش | پلن رایگان کریپتو دادهٔ زنده دارد؛ محدودیت «۱ ساعت» در صفحهٔ پلن مربوط به history/backfill است. سفارش‌های limit می‌توانند لغو شوند. |
| [GoCharting](https://gocharting.com/) | Footprint، Delta، Volume Profile، DOM، Time & Sales | تحلیل جریان معامله و توزیع حجم در قیمت | بازار/فید و پلن واقعی را کنترل کن. |
| [Exocharts](https://exocharts.com/) | Footprint، clusters، Delta، Volume Profile، TPO و دادهٔ مشتقات | تحلیل حجمی/ساختاری | جایگزین، نه ابزار لازم در کنار هر گزینهٔ دیگر. |
| [TradingLite](https://www.tradinglite.com/) | Liquidity heatmap و order flow | مشاهدهٔ نقدشوندگی سفارش‌های باز | عمق و تاریخچهٔ هر exchange/پلن را بررسی کن؛ سفارش روی heatmap سفارش قطعی قابل‌اجرا نیست. |
| [TensorCharts](https://tensorcharts.com/) | Heatmap و order-flow | مرورگر جایگزین | پلن رایگان و تاریخچه محدودیت دارند؛ اطلاعات جاری را تأیید کن. |
| [ATAS](https://atas.net/) | دسکتاپ Footprint/Cluster و Volume Profile | کاربر دسکتاپی که اتصال داده‌اش پشتیبانی می‌شود | connector و لایسنس داده مهم است. |
| [Quantower](https://www.quantower.com/) | DOM، cluster و volume profile و اتصالات چندبازاری | کاربر دسکتاپ/چندبازاری | قابلیت‌ها بر اساس اتصال و پلن متفاوت است. |
| [Insilico Terminal](https://insilicoterminal.com/) | ترمینال داده و ابزارهای تحلیل کریپتو | کشف یک گزینهٔ ترمینالی تازه | قبل از اعتماد، دقیقاً بررسی کن کدام بازار و چه زمان‌مُهری پوشش داده می‌شود. |
| [AGGR](https://github.com/) | کاتالوگ آن را ابزار tape تجمیعی/متن‌باز معرفی می‌کند | فقط اگر کد رسمی و نگهداری معتبر تأیید شد | URL رسمی پروژه از جست‌وجوی این دور قطعی نشد؛ repository تصادفی نصب نکن. |

**تفسیر:** Liquidation heatmap، دفتر سفارش resting و معاملات اجراشده سه چیز جدا هستند. نقشهٔ لیکوئید معمولاً تخمینی است؛ دفتر سفارش نشان می‌دهد در آن لحظه چه سفارش‌هایی قابل‌مشاهده بوده‌اند؛ tape معاملات اجراشده را نشان می‌دهد. این‌ها را به‌عنوان سه نوع شاهد متفاوت ثبت کن، نه سه گواه یک جهت قطعی.

## ۵. گزینه‌ها و نوسان ضمنی: منابع تازهٔ اضافه‌شده

| ابزار | داده | جایگاه پیشنهادی |
|---|---|---|
| [Deribit](https://docs.deribit.com/) + [DVOL API](https://docs.deribit.com/api-reference/market-data/public-get_volatility_index_data) | chain آپشن، IV، skew، Greeks و نوسان ضمنی | منبع اصلی بررسی آپشن در BTC؛ با درک اینکه فقط یک venue است. |
| [Laevitas](https://app.laevitas.ch/assets/options/overview/btc) / [Laevitas CLI](https://cli.laevitas.ch/) | IV surface، skew، term structure، block trades، OI، futures/options | برای تحقیق تخصصی آپشن و مشتقات؛ قیمت و دسترسی را بررسی کن. |
| [Basis Options](https://www.basischarts.com/free/free-crypto-options-data) | chain و OI، IV، skew، max pain و Greeks/GEX مدل‌شده از چند venue | گزینهٔ مرور سریع و بدون حساب طبق ادعای سایت | مقادیر مدل‌شده را با دادهٔ venue و روش محاسبه مقایسه کن. |
| [SignalPlus](https://www.signalplus.com/) | ترمینال آپشن، vol lab و GreeksBook | برای تحلیل آپشن و مدیریت دلتا | برای معاملهٔ بدون آپشن، اولویت پایین. |
| [Newhedge](https://newhedge.io/options) | IV term structure، skew، OI بر strike/expiry و put/call | نمای خلاصهٔ آپشن BTC | ابزاری زمینه‌ای، نه ماشهٔ ورود perp. |
| [Derivasys](https://www.derivasys.com/) | SVI fit و سطح نوسان، diagnostics و snapshotهای API روزانه | بررسی کیفیت fit و ساختار IV | snapshot روزانه با feed زنده/تیکی یکی نیست. |
| [Hedgehog Data](https://www.hedgehogdata.org/) | سطوح IV و residual diagnostics | مقایسهٔ کیفیت مدل نوسان | آستانه‌های خطای fit را بدون اعتبارسنجی مستقل به قاعدهٔ معاملاتی تبدیل نکن. |
| [Alpha Finance](https://alphafinance.io/crypto-options-data/) | OI به تفکیک strike/expiry، IV/skew و put/call | نمای تکمیلی آپشن | پوشش venue و تازگی داده را کنترل کن. |
| [Greeks.live](https://www.greeks.live/) | جریان معاملات آپشن، IV surface، skew و OI | مشاهدهٔ شرایط بازار آپشن | توجه کن block/whale flow به تنهایی جهت آینده را اثبات نمی‌کند. |

برای معاملهٔ دستی کوتاه‌مدت، آپشن را در فاز اول صرفاً به‌عنوان زمینهٔ نوسان/ریسک رویداد نگه می‌داریم. «max pain»، GEX یا skew به‌تنهایی محل ورود معتبر ایجاد نمی‌کنند.

## ۶. آن‌چین، ETF، موقعیت‌گیری نهادی و دادهٔ سرمایه

| منبع | پوشش | تأخیر/محدودیت اصلی | اولویت |
|---|---|---|---|
| [CryptoQuant](https://cryptoquant.com/) | ذخایر و جریان صرافی، ماینر/نهنگ، holder metrics و داده‌های spot/perp | برچسب‌گذاری آدرس‌ها می‌تواند اصلاح شود؛ بعضی تاریخچه‌ها لزوماً point-in-time نیستند. | زمینهٔ روزانه، نه ۱۵ دقیقه‌ای |
| [Glassnode](https://glassnode.com/) | آن‌چین، holder behavior، market/derivatives و برخی point-in-time metricها | بخش زیادی از پوشش و API پولی؛ تعریف metric باید خوانده شود. | پژوهش/زمینه |
| [Nansen](https://www.nansen.ai/) | برچسب آدرس، Smart Money، flows، پوزیشن‌های perp منتخب | برچسب و تخمین‌های smart-money وابسته به روش ارائه‌دهنده‌اند. | فقط اگر فرضیهٔ آن‌چین مشخص است |
| [Arkham](https://arkhamintelligence.com/) | برچسب آدرس‌ها و entity flows | برچسب/انتساب یک آدرس ممکن است اشتباه یا تغییر کند. | مشاهده، نه مدرک قطعی قصد معامله |
| [Bitquery](https://bitquery.io/) / [Allium](https://www.allium.so/) | داده‌های تراکنش، DEX، آدرس و تاریخچهٔ چندزنجیره‌ای با API | هزینه، chain coverage و archive depth وابسته به plan است. | تحقیق DEX/on-chain |
| [Dune](https://dune.com/) | query و داشبوردهای on-chain با SQL | خروجی داشبورد ممکن است به query و cadence سازنده وابسته باشد. | کاوش داده، نه حقیقت مستقل خودکار |
| [DeFiLlama](https://defillama.com/) | TVL، flows و داده‌های DeFi | تعریف TVL و source coverage اهمیت دارد؛ مستقیماً سنجهٔ ورود BTC نیست. | زمینهٔ کریپتو/ریسک سیستمیک |
| [Farside Investors](https://farside.co.uk/btc/) | جریان روزانهٔ ETFهای اسپات BTC آمریکا | روزانه و گاهی قابل‌اصلاح؛ برای تایمینگ ۱۵دقیقه‌ای کند است. | زمینهٔ روزانه |
| [SoSoValue](https://www.sosovalue.com/) | ETF flow، داشبورد و market data | تعریف/زمان به‌روزرسانی را با منبع صادرکننده تطبیق بده. | cross-check ETF |
| [CoinShares Research](https://coinshares.com/research/) | جریان هفتگی محصولات سرمایه‌گذاری دارایی دیجیتال | هفتگی؛ نماد «flows» را با جریان لحظه‌ای اشتباه نگیر. | زمینهٔ هفتگی |
| [Alternative.me Fear & Greed](https://alternative.me/crypto/fear-and-greed-index/) | شاخص احساسات روزانه | شاخص ترکیبی و کند؛ برای timing مستقیم مناسب نیست؛ attribution لازم است اگر در محصول عمومی بازنشر شود. | کم‌اولویت |
| [CFTC COT](https://www.cftc.gov/MarketReports/CommitmentsofTraders/index.htm) | موقعیت‌های گزارش‌شده برای بازارهای Futures از جمله قراردادهای CME مربوط به BTC | هفتگی و با تأخیر؛ نه دادهٔ لحظه‌ای | نگاه نهادی/هفتگی |
| [CME](https://www.cmegroup.com/markets/cryptocurrencies.html) | حجم و OI قراردادهای Futures/Options تنظیم‌شده | گزارش‌ها می‌توانند preliminary/final و با تأخیر باشند. | زمینهٔ نهادی |

**قانون نقطه‌درزمان (point-in-time):** اگر دادهٔ آن‌چین یا برچسب آدرس بعداً اصلاح شود، ممکن است backtest با مقدار امروز اطلاعاتی دریافت کند که در تاریخ معامله هنوز در دسترس نبود. برای آزمون تاریخی، timestamp انتشار و نسخهٔ داده را هم ثبت کن.

## ۷. دادهٔ تاریخی و API حرفه‌ای — منابع و محدودیت

| منبع | داده | استفادهٔ منطقی |
|---|---|---|
| [Binance public data](https://github.com/binance/binance-public-data) | فایل‌های OHLCV، trades/aggTrades و بخش‌هایی از Futures data | شروع رایگان برای قیمت/معامله؛ پوشش OI تاریخی جداگانه کنترل شود. |
| [Bybit API](https://bybit-exchange.github.io/docs/v5/market/open-interest) | OI و public market data | جمع‌آوری از endpoint رسمی؛ صفحه‌بندی و rate limit رعایت شود. |
| [OKX API](https://www.okx.com/docs-v5/en/) | Market data، trades، depth و Funding | time-synchronization و cache endpointهای مستقل را لحاظ کن. |
| [Bitget API](https://www.bitget.com/api-doc/common/intro) | market data، OI، Funding و تاریخچهٔ منتخب | بررسی پوشش تاریخی و قرارداد دقیق. |
| [CoinGlass API](https://www.coinglass.com/CryptoApi) | دادهٔ تجمیعی مشتقات، spot، futures، options و historical L2/L3 | پوشش حرفه‌ای، ولی قیمت/مجوز استفاده و endpoint موردنیاز باید توجیه شود. ادعاهای حجم داده و completeness ارائه‌دهنده‌اند. |
| [Tardis.dev](https://tardis.dev/) | tick trades، L2 snapshots/updates، funding، OI، options و replay | بهترین نوع منبع برای پژوهش ریزساختار، ولی احتمالاً گران؛ اول فرضیه و زمان‌مهر را روشن کن. |
| [Kaiko](https://www.kaiko.com/) | دادهٔ نهادی تاریخی و زنده، trades و order books | تحقیق حرفه‌ای/سازمانی؛ قیمت و مجوز داده مهم است. |
| [Amberdata](https://www.amberdata.io/market-data) | market + derivatives + order book + on-chain API | جایگزین نهادی با پوشش گسترده؛ نیاز به توجیه بودجه دارد. |
| [CoinAPI](https://www.coinapi.io/) | trades، quote، OHLCV و order book تجمیعی/تاریخی | API vendor برای ساخت پژوهش؛ تاریخچه/قیمت/حقوق بازنشر را بررسی کن. |
| [Coin Metrics](https://docs.coinmetrics.io/market-data) | market data و on-chain | برای تحقیق و دادهٔ ساخت‌یافته؛ پلن و metric definitions مهم‌اند. |
| [CoinDesk Data](https://data.coindesk.com/) | بازار و مشتقات | گزینهٔ نهادی؛ قیمت/پوشش باید دریافت شود. |
| [Crypto Lake](https://crypto-lake.com/) | دادهٔ بازار/ترید ریزدانه در بازارهای منتخب | به‌عنوان vendor تخصصی برای بررسی اضافه می‌شود؛ پوشش هر venue پیش از خرید کنترل شود. |
| [Coinperps](https://www.coinperps.com/) | dashboard تجمیعی بازار perpetual | برای دیدن overview؛ نه جایگزین raw event data برای backtest. |

### توسعهٔ داده: ابزارها و کتابخانه‌ها

این‌ها ابزار دیدن چارت نیستند؛ برای جمع‌آوری/تحلیل/تست خودکار در آینده‌اند. فعلاً نصب همه لازم نیست.

- [CCXT](https://github.com/ccxt/ccxt): wrapper عمومی برای REST API بسیاری از صرافی‌ها؛ برای market data مجاز/عمومی، با کنترل دقیق نام فیلدها و قرارداد. اتصال به private account/order را لازم نداریم.
- [cryptofeed](https://github.com/bmoscon/cryptofeed): دریافت جریان‌های زندهٔ trades/order book از exchangeهای پشتیبانی‌شده؛ برای data engineering، نه ابزار معاملهٔ دستی.
- [Backtesting.py](https://kernc.github.io/backtesting.py/): بک‌تست سادهٔ پایتون.
- [VectorBT](https://vectorbt.dev/) / [VectorBT PRO](https://vectorbt.pro/): تحلیل و آزمون برداری.
- [HftBacktest](https://hftbacktest.readthedocs.io/): شبیه‌سازی execution و microstructure؛ برای بک‌تست ریزدانه.
- [NautilusTrader](https://nautilustrader.io/): backtesting و trading engine؛ نیازمند طراحی data/execution درست است.
- [QuantConnect LEAN](https://www.quantconnect.com/lean/): موتور open-source پژوهش/backtest برای چند کلاس دارایی.
- [Freqtrade](https://www.freqtrade.io/): فریم‌ورک بات کریپتو؛ **در پروژهٔ فعلی اجرا/اتصال سفارش استفاده نشود**، ولی ابزار پژوهشی/backtest آن می‌تواند گزینهٔ بعدی باشد.
- [Hummingbot](https://hummingbot.org/): connectors و framework بازار؛ بیش از نیاز فعلی ما، به‌ویژه اگر فقط چارت دستی می‌خواهیم.
- [CCXT Pro](https://github.com/ccxt/ccxt): WebSocket در اکوسیستم CCXT؛ شروط مجوز/هزینه را بررسی کن.

## ۸. منابع رویداد کلان در مناطق اصلی جهان

برای معاملهٔ BTC، لازم نیست دادهٔ اقتصاد کلان تک‌تک کشورها را به نمودار ۱۵دقیقه‌ای وارد کنیم. بهتر است رویدادهای تأثیرگذار بر دلار، نرخ بهره و نقدشوندگی جهانی را رصد کنیم و ساعت دقیق را از منبع رسمی تأیید کنیم.

| منطقه/کشور | منبع رسمی | رویدادهای مهم | کاربرد |
|---|---|---|---|
| آمریکا | [Federal Reserve FOMC](https://www.federalreserve.gov/monetarypolicy/fomccalendars.htm) | نشست نرخ بهره، بیانیه و کنفرانس خبری | ریسک خبر و نوسان |
| آمریکا | [BLS](https://www.bls.gov/schedule/) | CPI، Employment Situation، بیکاری و دستمزد | رویدادهای مهم قیمت‌گذاری نرخ بهره |
| آمریکا | [BEA](https://www.bea.gov/news/schedule) | GDP، PCE و حساب‌های درآمدی | زمینهٔ نرخ بهره/رشد |
| آمریکا | [FRED](https://fred.stlouisfed.org/) | بازده اوراق، شرایط مالی و سری‌های اقتصادی | زمینه، نه سیگنال ۱۵دقیقه‌ای |
| منطقهٔ یورو | [ECB calendar](https://www.ecb.europa.eu/press/calendars/mgcgc/html/index.en.html) | تصمیم نرخ بهره و پیام بانک مرکزی | ریسک یورو/نقدشوندگی جهانی |
| بریتانیا | [Bank of England](https://www.bankofengland.co.uk/monetary-policy/upcoming-mpc-dates) | نشست MPC و نرخ بهره | زمینهٔ کلان |
| ژاپن | [Bank of Japan](https://www.boj.or.jp/en/mopo/mpmsche_minu/index.htm) | نشست سیاست پولی | ریسک yen/carry و نقدشوندگی |
| استرالیا | [RBA](https://www.rba.gov.au/monetary-policy/meetings/) | نشست سیاست پولی | زمینهٔ کلان |
| کانادا | [Bank of Canada](https://www.bankofcanada.ca/press/press-releases/) | تصمیم نرخ بهره و بیانیه‌ها | زمینهٔ کلان |
| نیوزیلند | [RBNZ](https://www.rbnz.govt.nz/monetary-policy/monetary-policy-decisions) | OCR و بیانیهٔ سیاست پولی | زمینهٔ کلان |
| جمع‌کنندهٔ تقویم | [Investing.com](https://www.investing.com/economic-calendar/) / [Trading Economics](https://tradingeconomics.com/calendar) | زمان‌بندی چند کشور در یک نما | برای کشف رویداد؛ زمان را با منبع رسمی تطبیق بده |

این لیست رویدادهای کلان اصلی را پوشش می‌دهد، نه همهٔ داده‌های اقتصادی کشورها. برای هدف BTC، بهتر است خبرهای بااهمیت بازار جهانی و تقویم آمریکا/بانک‌های مرکزی را ببینیم و بقیه را فقط وقتی اضافه کنیم که فرضیهٔ مشخصی داشته باشیم.

## ۹. ابزارهای اخبار، رویدادهای کریپتو، sentiment و جریان ETF

- [CoinMarketCal](https://coinmarketcal.com/) و [Coindar](https://coindar.org/): کشف رویدادهای رمزارزی؛ تاریخ/ادعا را از اطلاعیهٔ رسمی پروژه تأیید کن.
- [Farside](https://farside.co.uk/btc/) و [SoSoValue](https://www.sosovalue.com/): جریان ETF؛ دادهٔ روزانه برای زمینه، نه ماشهٔ intraday.
- [CoinShares Research](https://coinshares.com/research/): جریان هفتگی محصولات سرمایه‌گذاری دارایی دیجیتال.
- [LunarCrush](https://lunarcrush.com/) و [Santiment](https://santiment.net/): دادهٔ social/sentiment و بعضی متریک‌های آن‌چین؛ شاخص‌ها ممکن است از نمونه‌گیری شبکه‌های اجتماعی اثر بگیرند.
- [Messari](https://messari.io/) و [Token Terminal](https://tokenterminal.com/): research/fundamentals و metricهای پروژه/شبکه؛ برای تحلیل بنیادی، نه تعیین مستقیم ورود BTC ۱۵دقیقه‌ای.
- [CoinMarketCap](https://coinmarketcap.com/api/) و [CoinGecko API](https://www.coingecko.com/en/api): reference price، حجم، متادیتا و بازار؛ این‌ها را با قیمت اجرایی perp و order-book یکی نگیر.

## ۱۰. فهرست‌های اکتشافی جهانی و چرا آن‌ها را ممیزی کامل نمی‌نامیم

برای کاهش احتمال از قلم افتادن موارد، از سه سطح کشف استفاده شد:

1. [CryptoMarkets.tools](https://cryptomarkets.tools/) — در صفحهٔ دیده‌شده ۱۰۸ محصول در ۸ دسته فهرست شده بود. کاتالوگ می‌گوید قیمت، انتهای رایگان، پوشش venue/pair، تأخیر و حقوق استفاده را به‌صورت ساختاریافته جمع می‌کند؛ ولی در همان روش‌شناسی اعلام کرده بود هیچ‌یک از محصولات هنوز hands-on test نشده‌اند. این برای کشف مفید است، نه تأیید کیفیت.
2. [trading-awesome directory](https://git.mitgai.net/lentrade/trading-awesome) — فهرست جامعه‌محور با حدود ۱۹۳ سرویس و ابزار شامل APIs، دادهٔ بازار، آن‌چین، چارت، بک‌تست و پژوهش. خود فهرست تصریح می‌کند فهرست‌شدن به معنای audit یا endorsement نیست.
3. [awesome-derivatives-data](https://github.com/ruleaker/awesome-derivatives-data) — فهرست اختصاصی منابع derivatives/market microstructure شامل API صرافی‌ها، Funding، OI، liquidation، basis، options و ابزارهای متن‌باز.

### فهرست ۱۰۸ محصول کاتالوگ اکتشافی (اسامی برای کشف، نه تأیید محصول)

این فهرست به‌صورت عمدی شامل ابزارهای مختلف است و **نباید به معنای توصیه به نصب یا کیفیت تأییدشده خوانده شود**:

0xArchive; 3Commas; AGGR; Allium; Altrady; Amberdata Market Data API; Arkham; Artemis; Aster Market Data API; ATAS; Backtesting.py; Barter; Binance Market Data API; Birdeye Data API; Bitquery; Bitsgap; Bookmap; Bubblemaps; Bybit Market Data API; ccapi; CCXT; ChartIQ; Coin Metrics; Coinalyze; CoinAnk; CoinAPI EMS Trading API; CoinAPI Market Data API; Coinbase Exchange API; CoinDesk Data API; CoinGecko API; CoinGlass; CoinGlass API; Coinigy; CoinMarketCap API; CoinPaprika API; CoinRoutes; Coinrule; Cryptohopper; CryptoQuant; CryptoRank API; DeFiLlama; DEX Screener; DexPaprika; DEXTools; Dune; DXcharts; DXcharts Lite; dYdX v4 Clients; Elwood; Etherscan API; Exocharts; Footprint Analytics; Freqtrade; GeckoTerminal; Glassnode; GoCharting; GoCryptoTrader; growthepie; Gunbot; HaasOnline TradeServer; HftBacktest; Highcharts Stock; Hummingbot; Hyblock Capital; Hyperliquid Python SDK; Insilico Terminal; Jesse; Kaiko Market Data API; KLineChart; L2BEAT; Laevitas; Laevitas API; LEAN; Lumibot; LunarCrush; Massive Crypto API; Messari; Mobula API; Nansen; NautilusTrader; OctoBot; OctoBot Cloud; OKX Market Data API; Paradigm; Passivbot; QuantConnect Cloud; Quantower; SanAPI; Santiment; SignalPlus; SoSoValue; Superalgos; Talos; Tardis.dev; Tealstreet; TensorCharts; The Kingfisher; Token Terminal; Tokenomist; Trading Strategy; TradingView; TradingView Advanced Charts; TradingView Lightweight Charts; VectorBT; VectorBT PRO; Velo; WunderTrading; Wyden.

**یادداشت:** این فهرست نام‌های موجود در یک snapshot از کاتالوگ است؛ بعضی ابزارها ممکن است برای هدف فعلی نامرتبط، پولی، منطقه‌محدود، فقط توسعه‌دهنده‌محور یا دیگر فعال نباشند. ابزارهای دیگری مانند Basis Charts، Swolecharts، Coinperps، Derivasys و Newhedge نیز در بررسی‌های مستقیم/جست‌وجوی این گزارش اضافه شده‌اند؛ پس فهرست بالا خودش تمام محصولات موجود نیست.

## ۱۱. مهم‌ترین اشتباه‌های تحلیلی که این ابزارها باید جلوی آن‌ها را بگیرند

1. **شاهدهای هم‌بسته را مستقل شمردن:** چهار داشبورد ممکن است یک منبع underlying داشته باشند.
2. **OI را جهت‌دار فرض کردن:** OI افزایش می‌یابد، اما در هر قرارداد هر دو سمت وجود دارند.
3. **نقشهٔ لیکوئید را هدف قطعی دیدن:** نقشه معمولاً تخمین سطح فشار است، نه تمام موقعیت‌های واقعی و نه پیش‌بینی قطعی.
4. **Heatmap را حمایت تضمینی فرض کردن:** سفارش limit ممکن است قبل از برخورد لغو شود.
5. **Funding period را یکسان فرض کردن:** نرخ‌ها را بدون تبدیل دورهٔ تسویه مقایسه نکن.
6. **قیمت‌های چند venue را با هم مخلوط کردن:** نماد spot، USDT-perp، coin-margined و قیمت mark یکسان نیستند.
7. **دادهٔ اصلاح‌شونده را point-in-time فرض کردن:** labelهای آن‌چین و بعضی جریان‌ها ممکن است بعداً بازنویسی شوند.
8. **دادهٔ روزانه را برای timing ۱۵دقیقه‌ای مصرف کردن:** ETF flow، COT و شاخص‌های کلان معمولاً زمینه‌اند.
9. **دادهٔ زنده را معادل تاریخچهٔ قابل‌بک‌تست فرض کردن:** ممکن است زنده باشد ولی replay/آرشیو چندساله نداشته باشد.
10. **`PASS` را سیگنال ورود خواندن:** RiskFirst Helper فقط محدودیت‌های ورودی را می‌سنجد؛ خودش مزیت آماری ایجاد نمی‌کند.

## ۱۲. پروتکل عملی برای انتخاب و نصب ابزارها

### مرحلهٔ اول: ابزارهای بدون هزینه/کم‌هزینه

- TradingView + RiskFirst Helper: بررسی compile، حد ضرر، حجم و هزینه.
- Basis Charts: آیا واقعاً با نمادهای مورد نیاز باز می‌شود؟ timestamp/venue هر پنل را ثبت کن.
- Swolecharts + یکی از CoinGlass/CoinAnk/Coinalyze/Coinperps: یک timestamp مشترک برای OI، Funding و liquidation مقایسه کن.
- یکی از Bookmap/GoCharting/Exocharts: همان venue و همان دقیقه را با tape و order book مشاهده کن.
- یک تقویم رویداد رسمی/جمع‌کننده برای بررسی event risk.

### مرحلهٔ دوم: ثبت ۲۰ نمونهٔ کاغذی

برای هر setup پیش از دانستن نتیجه ثبت کن: UTC timestamp، venue، نماد قرارداد دقیق، timeframe، trend regime، OI change، Funding period/rate، CVD یا trade-flow اگر موجود است، depth/heatmap و اینکه observed یا modelled است، هزینهٔ واقعی/تخمینی، ورود فرضی، stop، target و دلیل رد/قبول. سپس نتیجه را به R بعد از هزینه ثبت کن. ۲۰ مورد فقط آزمون فرایند است، نه اثبات سودآوری.

### مرحلهٔ سوم: تصمیم دربارهٔ یک دادهٔ پولی

فقط زمانی که دقیقاً معلوم شد کدام فیلد کم است—مثلاً تاریخچهٔ L2، OI point-in-time یا option surface—برای یک dataset آزمایشی قیمت بگیر. قبل از پرداخت، retention, license, timestamp, missingness, exchange coverage و امکان export را کتبی بررسی کن.

## ۱۳. چه چیزی را نمی‌توانم ادعا کنم؟

- اینکه تمام محصولات همهٔ کشورها در اینترنت پیدا شده‌اند؛ چنین تضمینی ممکن نیست.
- اینکه تمام ابزارهای این گزارش عملاً نصب یا با دادهٔ واقعی تست شده‌اند؛ برخی صفحه‌ها فقط به‌عنوان منبع/ادعای ارائه‌دهنده بررسی شدند.
- اینکه یک منبع داده یا ابزار خاص از نظر قانونی برای هر محل یا هر کاربر قابل‌استفاده است.
- اینکه ترکیب ابزارها یک long/short edge ایجاد می‌کند. پروژهٔ قبلی خودمان، از جمله الگوی pullback EMA20 در آزمونِ پس از هزینه، چنین مزیتی را ثابت نکرده است.
- اینکه اطلاعات یا قیمت‌های پلن‌ها ثابت می‌مانند؛ هزینه و دسترسی با زمان، منطقه و طرح تغییر می‌کند.

## ۱۴. منابع کلیدی تازه‌شده

- [CryptoMarkets.tools — catalog and methodology](https://cryptomarkets.tools/)
- [trading-awesome — community directory](https://git.mitgai.net/lentrade/trading-awesome)
- [awesome-derivatives-data](https://github.com/ruleaker/awesome-derivatives-data)
- [Coinperps](https://www.coinperps.com/)
- [0xArchive](https://0xarchive.io/)
- [Basis free options data](https://www.basischarts.com/free/free-crypto-options-data)
- [SignalPlus](https://www.signalplus.com/)
- [Newhedge options dashboard](https://newhedge.io/options)
- [Derivasys](https://www.derivasys.com/)
- [Hedgehog Data](https://www.hedgehogdata.org/)
- [Alpha Finance options data](https://alphafinance.io/crypto-options-data/)
- [CryptoQuant](https://cryptoquant.com/about)
- [CoinGlass API coverage](https://www.coinglass.com/CryptoApi)
- [Bybit OI API](https://bybit-exchange.github.io/docs/v5/market/open-interest)
- [OKX API](https://www.okx.com/docs-v5/en/)
- [Gate API](https://www.gate.com/docs/developers/apiv4/en/)
- [Hyperliquid API](https://hyperliquid.gitbook.io/hyperliquid-docs/for-developers/api)
- [CME crypto market/data providers](https://www.cmegroup.com/trading/cryptocurrency-products-data-and-connectivity-providers.html)
- [CFTC COT reports](https://www.cftc.gov/MarketReports/CommitmentsofTraders/index.htm)
- [Farside BTC ETF flows](https://farside.co.uk/bitcoin-etf-flow-all-data/)
- [BLS Release Schedule](https://www.bls.gov/schedule/)
- [BEA News Schedule](https://www.bea.gov/news/schedule)
- [Federal Reserve FOMC calendars](https://www.federalreserve.gov/monetarypolicy/fomccalendars.htm)
- [ECB calendar](https://www.ecb.europa.eu/press/calendars/mgcgc/html/index.en.html)
- [Bank of England MPC dates](https://www.bankofengland.co.uk/monetary-policy/upcoming-mpc-dates)
- [Bank of Japan calendar](https://www.boj.or.jp/en/mopo/mpmsche_minu/index.htm)
- [RBA meetings](https://www.rba.gov.au/monetary-policy/meetings/)
- [Bank of Canada](https://www.bankofcanada.ca/press/press-releases/)
- [RBNZ policy decisions](https://www.rbnz.govt.nz/monetary-policy/monetary-policy-decisions)

---

# پیوست A — گزارش پایهٔ نسخهٔ قبلی

## نتیجهٔ اجرایی

پیشنهاد نمی‌شود همهٔ ابزارها را نصب یا هم‌زمان باز کنیم. بخش زیادی از آنها داده‌های مشابه را با تفاوت‌هایی در پوشش صرافی، بازهٔ تاریخی، واحد اندازه‌گیری و روش برآورد نمایش می‌دهند. فهرست زیر یک فهرست گسترده از گزینه‌های مرتبط و قابل بررسی است، نه تضمین اینکه تمام محصولات جهان را پوشش داده باشد.

### پشتهٔ پیشنهادیِ شروع با حداقل هزینه

1. **TradingView** — نمودار اصلی، Pine Script، هشدار و چیدمان تایم‌فریم‌ها.
2. **Basis Charts** — حتماً آزمایش شود؛ ارائه‌دهنده می‌گوید نمودار، footprint/order flow، دادهٔ مشتقات، آپشن، screener، replay، backtest، alert و journal را در هستهٔ رایگان و بدون حساب جمع کرده است. به‌دلیل محصول جدیدتر، قبل از اتکای معاملاتی باید زمان‌مُهر داده، بازارهای در دسترس، پایداری و روش محاسبهٔ هر شاخص بررسی شود.
3. **Swolecharts** — صفحهٔ رایگان و بدون ورود برای OI، Funding، تغییر حجم، CVD، نقدشوندگی و لیکوئیدها؛ مزیتش انتشار شفاف پوشش و نقص داده است.
4. **CoinGlass یا CoinAnk** — یکی را برای نمای دوم از مشتقات و نقشه‌های لیکوئید انتخاب کن. ابتدا هر دو را در چند مورد مقایسه کن؛ اشتراک هم‌زمان معمولاً لازم نیست.
5. **Coinalyze** — نمودارهای مشتقات و API رایگان برای پرس‌وجوهای کم‌تعداد؛ برای cross-check مفید است.
6. **Bookmap Digital یا GoCharting** — فقط یکی را برای مشاهدهٔ Order Flow/footprint/دفتر سفارش امتحان کن. اگر مرورگری می‌خواهی، GoCharting را هم بررسی کن؛ اگر Heatmap دفتر سفارش برایت مهم است، Bookmap را تست کن.
7. **Farside + تقویم اقتصادی** — برای زمینهٔ جریان ETF و زمان رویدادهای کلان، نه نقطهٔ ورود ۱۵دقیقه‌ای.
8. **CryptoQuant Basic / Glassnode عمومی** — فقط برای زمینهٔ آن‌چین و افق بلندتر؛ در شروع برای اسکالپینگ ضروری نیستند.

**نکته:** Basis، CoinGlass، Coinalyze، Swolecharts و CoinAnk هم‌پوشانی زیادی دارند. ابزار بیشتر به معنی شواهد مستقل بیشتر نیست.

---

## ۱. نمودار، اسکریپت و محیط اصلی

| ابزار | چه کاری می‌کند؟ | وضعیت دسترسی که بررسی شد | جایگاه پیشنهادی و محدودیت |
|---|---|---|---|
| [TradingView](https://www.tradingview.com/) | نمودار چندتایم‌فریمی، Pine Script، هشدار، فیلتر و Pine Screener؛ شاخص‌های OI و Long/Short Accounts برای برخی صرافی‌ها | نسخهٔ پایه دارد؛ ویژگی‌ها و محدودیت‌ها بر حسب طرح متفاوت‌اند | **محیط اصلی** به‌دلیل Pine و اسکریپت RiskFirst. Pine به هر API دلخواه دسترسی مستقیم نمی‌دهد. Pine Screener روی ۵۰۰ کندل آخرِ محاسبه، تایم‌فریم‌های مشخص و حداکثر ۴۰ درخواست `request.*` محدودیت دارد. |
| [Basis Charts](https://www.basischarts.com/) | یک محیط یکپارچهٔ مرورگری: کندل، یک‌ثانیه‌ای، footprint، order book heatmap، derivatives، options، screener، replay، backtest، alerts، journal و AI/MCP | ارائه‌دهنده هسته را رایگان، بدون حساب و بدون کارت اعلام می‌کند؛ Founders اختیاری است (صفحهٔ رسمی در زمان بررسی: ۱۵ دلار/۳۰ روز یا ۵۰ دلار یک‌باره) | **اولین گزینهٔ تازه برای آزمایش.** منبع‌های اعلام‌شده Binance، Bybit، OKX و Hyperliquid هستند؛ اسکریپت Pine مستقیماً قابل‌انتقال فرض نشود. تأیید مستقل از دقت، کیفیت تاریخی و پایداری انجام نشده است. |
| [GoCharting](https://gocharting.com/trading/market-data/crypto) | نمودار، footprint، delta، volume profile، DOM، Time & Sales، دادهٔ کریپتو و زبان اسکریپت Lipi | صفحهٔ رسمی از دادهٔ زندهٔ Binance، Bybit و Coinbase و دسترسی رایگان به دادهٔ کریپتو سخن می‌گوید؛ برخی امکانات وابسته به پلن‌اند | جایگزین مرورگری خوب برای Basis/TradingView در تحلیل order flow؛ Lipi با Pine یکی نیست. پوشش داده را برای نماد دقیق بررسی کن. |
| [Exocharts](https://exocharts.com/) | Footprint clusters، delta/volume profile، POC، value area، TPO، VWAP، OI و دادهٔ لیکوئید؛ نسخهٔ وب و دسکتاپ | قابلیت‌ها و تاریخچه تابع اشتراک و نسخه‌اند | برای تحلیل حرفه‌ای جریان سفارش؛ احتمالاً لازم نیست در شروع هم‌زمان با Bookmap و GoCharting استفاده شود. |
| [TradingLite](https://www.tradinglite.com/) | Heatmap نقدشوندگی و ابزارهای order flow در بازار کریپتو | قیمت و حدود پلن باید در صفحهٔ فعلی بررسی شود | جایگزین برای نمایش نقدشوندگی روی نمودار؛ پیش از پرداخت، دادهٔ بازار و عمق/تاریخچهٔ پلن را آزمایش کن. |
| [TensorCharts](https://tensorcharts.com/) | Heatmap و تحلیل جریان سفارش | سطح رایگان محدود گزارش شده؛ جزئیات پلن در این بررسی کامل راستی‌آزمایی نشد | گزینهٔ جایگزین، نه افزودهٔ ضروری به همهٔ ابزارها. |
| [ATAS](https://atas.net/) | نرم‌افزار دسکتاپ تحلیل cluster/footprint و اتصال دادهٔ صرافی | اتصال داده بر اساس connector و صرافی انتخابی است | برای کسی که می‌خواهد برنامهٔ دسکتاپ جدا داشته باشد؛ پیش از نصب سازگاری سیستم، صرافی و مجوز داده را چک کن. |
| [Quantower](https://www.quantower.com/charting-and-analytics-features) | Cluster Chart، Volume Profile، VWAP، TPO، Historical Time & Sales و DOM Surface | قابلیت اتصال، داده و امکانات به پلن و connector وابسته است | آلترناتیو دسکتاپ برای تحلیل حرفه‌ای بازار؛ برای شروع رایگان‌بودن کامل فرض نشود. |
| [CoinDesk Trend Indicators](https://indices.coindesk.com/strategies-and-services) | شاخص روند روزانه بر پایهٔ چند پنجرهٔ زمانی برای BTC/ETH | سیگنال روزانه و مستند روش‌شناسی دارد | برای **زمینهٔ روزانه**، نه ورود ۱۵دقیقه‌ای. روش روزانه است و نباید آن را به‌عنوان مدل اثبات‌شدهٔ سودآوری شخصی تلقی کرد. |

### محدودیت مهم TradingView

طبق مستند رسمی، OI در نمودار می‌تواند تجمیعی یا مربوط به قرارداد/صرافی مشخص باشد؛ حساب Long/Short تعداد حساب‌ها را می‌شمارد نه اندازهٔ پوزیشن. در Pine Screener نیز تنها بازه‌های زمانی مشخص پشتیبانی می‌شوند و محاسبه روی ۵۰۰ کندل آخر انجام می‌شود. پس برای backtest بلندمدت از Pine Screener به‌تنهایی استفاده نکن.

---

## ۲. داده‌های مشتقات: Open Interest، Funding، نسبت لانگ/شورت و لیکوئید

| ابزار | داده و ویژگی شاخص | رایگان/پولی و محدودیت | پیشنهاد |
|---|---|---|---|
| [Swolecharts](https://swolecharts.com/) | OI، Funding، liquidation feed، حجم و جهش حجم، CVD، screener، order-book liquidity heatmap، نسبت‌های Long/Short و ابزارهای Hyperliquid | صفحهٔ رسمی می‌گوید استفاده بدون ورود و رایگان است. تاریخچهٔ گزارش‌شده: قیمت/حجم ۱دقیقه‌ای ۳۰ روز، ۵دقیقه‌ای ۹۰ روز؛ OI/Funding در ۵دقیقه ۳۰ روز و ساعتی از زمان شروع ثبت | **اولویت بالا.** مزیت مهمش افشای پوشش داده است: طبق صفحهٔ پوشش، لیکوئید Binance/Bitget/Aster نمونه‌برداری‌شده است و Hyperliquid استریم عمومی تمام لیکوئیدها ندارد. جمع لیکوئیدها را نباید مجموع کامل بازار دانست. |
| [CoinGlass](https://www.coinglass.com/currencies/BTC/futures) | نمای چندصرافی از OI، Funding، لیکوئید، Long/Short، جریان ETF، حجم و نقشه‌های لیکوئید | داشبورد عمومی و ابزارهای پیشرفته دارد؛ API در زمان بررسی از ۲۹ دلار/ماه برای Hobbyist، ۷۹ دلار Startup، ۲۹۹ دلار Standard و ۶۹۹ دلار Professional شروع می‌شد. محدودیت تاریخچه و تعداد endpointها بر اساس پلن فرق می‌کند | **برای نمای دوم/نقشهٔ لیکوئید.** API را در شروع نخر. نقشه‌های لیکوئید مدل/برآورد هستند و سطح قطعی آینده نیستند. |
| [CoinAnk](https://coinank.com/) | Liquidation Map/Heatmap، Funding، Funding Heatmap، OI، Long/Short، top trader ratios، orderbook depth delta، ETF و برخی داده‌های Hyperliquid | داشبورد عمومی در دسترس است؛ قیمت/محدودیت API به‌طور کامل تأیید نشد | جایگزین CoinGlass. یکسانی نقشه‌ها را مقایسه کن؛ اگر دادهٔ تکراری است لازم نیست هر دو را مرتب باز کنی. |
| [Coinalyze](https://coinalyze.net/) | OI، Funding، لیکوئید، basis و نسبت‌های Long/Short با نمودارهای تاریخی | API به کلید نیاز دارد؛ مستند رسمی ۴۰ درخواست/دقیقه را می‌گوید. تاریخچهٔ intraday حدود ۱۵۰۰–۲۰۰۰ نقطه نگه‌داری می‌شود و دادهٔ روزانه قدیمی حذف نمی‌شود. API برای استفادهٔ عمومی رایگان اعلام شده است | **Cross-check مفید و کم‌هزینه.** برای تاریخچهٔ بلندمدت ۵دقیقه‌ای انتظار نداشته باش تمام داده را نگه دارد. |
| [The Kingfisher](https://thekingfisher.io/liquidations-map) | نقشهٔ فشار لیکوئید برآوردی، نقشهٔ چندصرافی/چنداهرم و تاریخچه در terminal | نمونهٔ عمومیِ Binance snapshot محدود است؛ قابلیت کامل در terminal | فقط یک منبع ثانویه برای سنجش سناریو. خود سایت می‌گوید فشار لیکوئید را **مدل‌سازی** می‌کند؛ نقشهٔ عمومی ممکن است قدیمی شود. |
| [Hyblock Capital](https://hyblockcapital.com/) | مدل‌های positioning، retail-vs-whale divergence، top trader accounts/positions، حجم خرید/فروش، vDelta و screener | بسیاری از قابلیت‌ها تخصصی و وابسته به حساب/اشتراک‌اند؛ قیمت جاری در این پژوهش تأیید نشد | برای مرحلهٔ بعدی اگر واقعاً نیاز به دادهٔ positioning مدل‌شده داشتیم؛ فعلاً داده‌های اصلی را با منابع ساده‌تر بررسی کن. |
| [Velo Data](https://velo.xyz/) | OI، Funding، basis، CVD، لیکوئید و مقایسهٔ صرافی‌ها؛ تاریخچه و تحلیل session/ساعت | مستندات عمومی موجودند، اما شرایط فعلی طرح و اشتراک کامل تأیید نشد | ترمینال تخصصی خوب برای مقایسهٔ funding/basis/CVD بین venueها. قبل از وابسته‌شدن به آن، شرایط فعلی حساب و تاریخچه را چک کن. |
| [CoinGecko Derivatives](https://www.coingecko.com/en/derivatives) | جدول سادهٔ OI، تغییر OI، Funding، حجم و نسبت حجم مشتقه به اسپات | صفحهٔ عمومی رایگان | یک نمای دوم سریع برای مقایسه؛ جایگزین نمودار تاریخی عمیق نیست. |
| [D.Terminal](https://dterminal.trade/docs/) | screener فاندینگ/OI چندصرافی و heatmap بر اساس حجم یا OI | صفحهٔ محصول/مستند موجود است؛ قیمت و عمق تاریخچه در این بررسی کامل تأیید نشد | گزینهٔ تازه برای مشاهدهٔ سریع چند venue؛ قبل از افزودن، با Swolecharts و Coinalyze مقایسه شود. |
| [TradingView Crypto Open Interest](https://www.tradingview.com/support/solutions/43000762388-understanding-crypto-open-interest/) | OI تجمیعی یا تک‌صرافی؛ Long/Short Ratio Accounts برای چند venue | داخل نمودار، در صورت پوشش نماد و طرح در دسترس | برای چسباندن OI به قیمت مفید است. توجه: OI افزایش یابد، الزاماً به معنی لانگ بیشتر نیست؛ هر قرارداد هم‌زمان یک لانگ و یک شورت دارد. |

### تفاوت‌های مهم داده

- **Open Interest (OI):** تعداد/ارزش قراردادهای باز است؛ جهت معامله‌گرِ برنده را نشان نمی‌دهد.
- **Long/Short Accounts:** نسبت تعداد حساب‌هاست، نه اندازهٔ پول یا قراردادهای آن‌ها.
- **Funding:** قراردادها و فاصلهٔ تسویه در صرافی‌ها متفاوت‌اند. نرخ‌ها باید به یک بازهٔ زمانی استاندارد (مثلاً معادل ۸ساعته) تبدیل شوند، ولی سالانه‌سازی نرخ لحظه‌ای پیش‌بینی آینده نیست.
- **Liquidations:** همهٔ صرافی‌ها همهٔ رویدادها را منتشر نمی‌کنند. مجموع سرویس‌ها ممکن است ناقص باشد و نقشهٔ «سطوح لیکوئید» معمولاً مدل است، نه دفتر سفارش مشاهده‌شده.
- **Open Interest + قیمت:** افزایش OI می‌تواند همراه بالا رفتن قیمت رخ دهد، اما برای تعیین سمت بازار به واکنش قیمت، جریان معاملات، Funding و ساختار نیاز است.

---

## ۳. Order Flow، Footprint، DOM و نقدشوندگی

| ابزار | بهترین کاربرد | نکتهٔ دسترسی/محدودیت |
|---|---|---|
| [Bookmap Crypto](https://bookmap.com/en/crypto) | Heatmap دفتر سفارش، volume dots، CVD، Volume Profile، POC، AVWAP و مشاهدهٔ تغییر نقدشوندگی | **اصلاح یک سوءبرداشت قبلی:** صفحهٔ رسمی فعلی، دادهٔ کریپتو را در طرح Digital رایگان «real-time» معرفی می‌کند؛ عدد ۱ ساعت در جدول مربوط به **backfill/history** است، نه اینکه لزوماً دادهٔ زنده یک ساعت تأخیر داشته باشد. پلن‌های بالاتر تاریخچهٔ بیشتری دارند. |
| [GoCharting Order Flow](https://gocharting.com/trading/market-data/crypto) | Footprint، delta، volume profile، imbalance، Time & Sales، L2/L3 و alert/scanner | یک جایگزین مرورگری؛ ویژگی‌های خاص می‌توانند به پلن یا feed نیاز داشته باشند. |
| [Exocharts](https://help.exocharts.com/hc/en-us/articles/4413995353489-Web-platform-overview) | Footprint clusters، delta/volume profiles، TPO، OI، liquidation و VWAP | نسخهٔ وب برای خواندن چارت سبک‌تر؛ دسکتاپ برای DOM، tape، replay و نمودارهای غیرزمانی عمیق‌تر است. |
| [TradingLite](https://www.tradinglite.com/) | Heatmap و ساختار نقدشوندگی در چارت کریپتو | گزینهٔ جایگزین Bookmap؛ قبل از پرداخت، پلن و تاریخچه را تأیید کن. |
| [TensorCharts](https://tensorcharts.com/) | Heatmap و flow در نمودار | نسخهٔ رایگان محدود؛ با Bookmap و GoCharting هم‌پوشانی دارد. |
| [ATAS](https://atas.net/) | نرم‌افزار دسکتاپ cluster/footprint با اتصال مستقیم به منبع دادهٔ صرافی | connector دقیق را پیش از اتکا به داده بررسی کن. |
| [Quantower](https://www.quantower.com/charting-and-analytics-features) | Cluster Chart، TPO، Volume Profile، VWAP، DOM Surface و Time & Sales | نرم‌افزار دسکتاپ چندبازاری؛ داده/اتصال/پلن را جدا بررسی کن. |
| [Binance Public Market Data](https://github.com/binance/binance-public-data) | دانلود کندل، معاملات و مجموعه‌هایی از دادهٔ عمومی برای پژوهش | منبع بسیار مفید برای دادهٔ تاریخی؛ عمق داده در همهٔ endpointها یکسان نیست. برای مثال API آمار تاریخی OI در Binance محدودیت پنجرهٔ اخیر دارد، پس آن را با تاریخچهٔ بلندمدت کندل‌ها یکسان فرض نکن. |
| [Bybit Market Data API](https://bybit-exchange.github.io/docs/v5/market/open-interest) | OI تاریخی برای قراردادهای مختلف با پارامترهای بازه و صفحه‌بندی | API رسمی نشان می‌دهد بازه از زمان راه‌اندازی نماد قابل درخواست است، اما هر پاسخ حداکثر ۲۰۰ نقطه دارد و باید صفحه‌بندی انجام شود. محدودیت دسترسی شبکه/API را خودت بیازما. |

### نکتهٔ خواندن Heatmap

Heatmap دفتر سفارش سفارش‌های محدودِ دیده‌شده در آن لحظه را نشان می‌دهد؛ سفارش‌ها می‌توانند لغو شوند یا جابه‌جا شوند. نقشهٔ لیکوئید، برعکس، برآوردی از محل فشار اجباری است. این دو را یکی فرض نکن. «دیوار سفارش» تضمین حمایت/مقاومت نیست و «خوشهٔ لیکوئید» هم تضمین جذب قیمت به آن سطح نیست.

---

## ۴. آپشن، نوسان ضمنی و ریسک رویدادهای انقضا

| ابزار | داده | چه زمانی به کار می‌آید؟ |
|---|---|---|
| [Basis Options](https://www.basischarts.com/free/free-crypto-options-data) | OI و حجم به تفکیک strike/expiry، IV، skew، term structure، max pain و GEX/Greeks مدل‌شده از چند venue | هستهٔ رایگان اعلام شده؛ برای زمینهٔ نوسان و ریسک رویداد. GEX به فرض‌های موقعیت‌گیری dealer وابسته است. |
| [Laevitas](https://app.laevitas.ch/assets/options/overview/btc) | Options flow، IV surface، Greeks، skew، term structure و بازار مشتقات | برای مطالعهٔ حرفه‌ای‌تر آپشن؛ قیمت/محدودیت‌ها پیش از اشتراک بررسی شود. |
| [Laevitas CLI](https://cli.laevitas.ch/) | CLI و داشبورد ترمینالی برای options، perps، spot، order book و بعضی داده‌های پیش‌بینی بازار | ابزار جدید برای کاربر فنی؛ اتصال و شرایط دسترسی را قبل از استفادهٔ مداوم بررسی کن. |
| [Greeks.live](https://www.greeks.live/deribit/tools/datalab/BTC) | گزینه‌ها، IV surface، skew، option flow، OI به تفکیک strike/expiry و max pain | برای زمینهٔ بازار آپشن؛ نه ماشهٔ مستقیم لانگ/شورت در ۱۵ دقیقه. |
| [Deribit DVOL / API](https://docs.deribit.com/api-reference/market-data/public-get_volatility_index_data) | شاخص نوسان ضمنی و دادهٔ بازار آپشن | برای مقایسهٔ نوسان مورد انتظار بازار با نوسان تحقق‌یافته؛ نوسان جهت قیمت را مشخص نمی‌کند. |
| [Basis free implied volatility](https://www.basischarts.com/free/free-crypto-implied-volatility) | DVOL، 30-day ATM IV، 25-delta skew/butterfly و سطح نوسان | راه سادهٔ رایگان برای مشاهدهٔ ساختار نوسان بدون ساخت API. |

**اولویت:** برای هدف فعلیِ معاملهٔ دستی BTC، آپشن‌ها زمینهٔ ثانویه‌اند. قبل از ورود به پیچیدگی GEX و مدل‌های dealer، ابتدا باید دادهٔ قیمت، هزینه، OI و flow به‌درستی هم‌زمان شوند. Max Pain به معنی «قیمت حتماً در آنجا بسته می‌شود» نیست.

---

## ۵. آن‌چین، جریان سرمایه، ETF، سنتیمنت و رویدادها

| ابزار | کاربرد | هزینه/محدودیت و اولویت |
|---|---|---|
| [CryptoQuant](https://cryptoquant.com/asset/btc) | ورود/خروج صرافی‌ها، ذخایر، جریان نهنگ/ماینر، دادهٔ مشتقات و شاخص‌های آن‌چین | پلن Basic رایگان دارد، ولی API Basic برای market data، تاریخچهٔ کوتاه‌تر و تفکیک روزانه محدود است؛ دادهٔ on-chain و resolution بالاتر در پلن‌های پولی. مناسب زمینهٔ میان‌مدت، نه ماشهٔ ورود ۱۵دقیقه. |
| [Glassnode Studio](https://studio.glassnode.com/) | Exchange flows، cohortها، realized profit/loss، شاخص‌های شبکه، مشتقات/آپشن/ETF و macro | امکانات عمومی و اشتراکی؛ صفحهٔ قیمت در زمان بررسی Advanced را ۴۹ دلار/ماه با پرداخت سالانه معرفی می‌کرد. برای معاملات کوتاه‌مدت اولیه ضروری نیست. |
| [Santiment](https://app.santiment.net/) | Social volume/sentiment، رفتار شبکه و داده‌های اجتماعی/آن‌چین | معیارهای اجتماعی می‌توانند نویزی و قابل‌دستکاری باشند؛ فقط به‌عنوان زمینه استفاده شود. پلن فعلی را قبل از پرداخت بررسی کن. |
| [Arkham Intelligence](https://arkhamintelligence.com/) | تحلیل آدرس‌ها/نهادها و alertهای انتقال دارایی آن‌چین | برای بررسی انتقال‌های بزرگ با برچسب نهاد؛ انتقال بزرگ به‌تنهایی معاملهٔ انجام‌شده یا جهت آینده را اثبات نمی‌کند. |
| [Farside Investors — BTC ETF flows](https://farside.co.uk/bitcoin-etf-flow-all-data/) | جدول روزانهٔ ورود/خروج صندوق‌های ETF بیت‌کوین آمریکا | منبع مستقیم و مناسب برای جریان روزانه؛ مربوط به ساعات/روزهای بازار ETF است و سیگنال سریع ۱۵دقیقه‌ای نیست. |
| [DeFiLlama](https://defillama.com/) | عرضهٔ استیبل‌کوین‌ها، TVL، حجم DeFi، جریان ETF و داده‌های اکوسیستم | بیشتر برای زمینهٔ نقدینگی و جریان‌های بزرگ‌تر؛ نسبت مستقیم و قطعی با ورود بعدی BTC ندارد. |
| [Alternative.me Fear & Greed](https://alternative.me/crypto/fear-and-greed-index/) | شاخص روزانهٔ ترس و طمع و API عمومی | رایگان با شرط attribution برای استفاده از داده در سرویس‌های منتشرشده؛ شاخص روزانه است، نه نقطهٔ ورود. |
| [CoinDesk Trending](https://www.coindesk.com/price/trending) | رتبه‌بندی ترکیبی volume surge، price momentum، سرعت خبر و تعامل کاربران | برای کشف دارایی‌های پرتحرک مفیدتر از BTC-only timing؛ ریسک سروصدای خبری دارد. |
| [CoinMarketCal](https://coinmarketcal.com/) | تقویم رویدادهای رمزارز، لیستینگ، آپگرید و tokenomics | برای BTC کمتر از تقویم کلان اهمیت دارد؛ رویدادها را پیش از اتکا از منبع اصلی پروژه تأیید کن. |
| [Coindar](https://coindar.org/) | تقویم رویدادهای پروژه‌های کریپتو و فیلتر اهمیت | جایگزین CoinMarketCal؛ برای معاملهٔ BTC عموماً اولویت پایین‌تر. |
| [Investing.com Economic Calendar](https://www.investing.com/economic-calendar/) | CPI، نرخ بهره، دادهٔ اشتغال و رویدادهای کلان | برای اجتناب از ورود در لحظات رویدادهای حساس، نه پیش‌بینی قطعی جهت. زمان رویداد را با منبع رسمی هم چک کن. |
| [FRED — 10Y Treasury Yield](https://fred.stlouisfed.org/series/DGS10) | بازده اوراق ۱۰سالهٔ خزانه‌داری آمریکا و دادهٔ کلان | دادهٔ روزانه و زمینه‌ای؛ نباید به‌عنوان محرک مستقیم معاملهٔ ۱۵دقیقه‌ای استفاده شود. |
| [CFTC COT reports](https://www.cftc.gov/MarketReports/CommitmentsofTraders/AbouttheCOTReports/index.htm) | موقعیت‌های هفتگی گروه‌های معامله‌گر در بازارهای گزارش‌شده، از جمله بازارهای CME مرتبط | دادهٔ هفتگی با تأخیر؛ برای زمینهٔ موقعیت‌گیری نهادها مفید است، اما برای timing لحظه‌ای مناسب نیست. |

---

## ۶. منابع دادهٔ حرفه‌ای برای مرحلهٔ تحقیق عمیق‌تر

این سرویس‌ها برای زمانی‌اند که بخواهیم دادهٔ tick-level، دفتر سفارش تاریخی یا تحقیق نهادی انجام دهیم. برای شروع توصیه نمی‌کنم هزینهٔ آن‌ها را بپردازیم.

| سرویس | داده | نتیجه برای ما |
|---|---|---|
| [Tardis.dev](https://tardis.dev/) | معاملات tick، L2 order-book updates/snapshots، options chain، funding، OI، mark/index prices و liquidation در ده‌ها صرافی؛ replay تاریخچه | بسیار مناسب برای بازسازی دفتر سفارش و آزمون microstructure؛ قیمت رسمی بررسی‌شده برای پلن‌های انفرادی بالا بود (حدود ۳۵۰ دلار/ماه به بالا). فعلاً هزینه‌اش توجیه ندارد. دادهٔ تازهٔ API با تأخیر حدود ۶ دقیقه نسبت به زنده منتشر می‌شود. |
| [Kaiko](https://www.kaiko.com/) | دادهٔ تاریخی و زندهٔ بازار، tick trades، order book و شاخص‌های نهادها | ارائه‌دهندهٔ دادهٔ حرفه‌ای؛ برای تحقیق عمیق، ولی احتمالاً پرهزینه. قیمت فعلی دقیق تأیید نشد. |
| [CoinAPI](https://www.coinapi.io/) | OHLCV، trades، quotes و order-book history تا L2/L3 در بازارهای پشتیبانی‌شده | API و تاریخچهٔ عمیق؛ باید سهمیهٔ رایگان/قیمت و coverage هر نماد را بر اساس نیاز بررسی کرد. |
| [Amberdata](https://www.amberdata.io/market-data) | قیمت، trades، order-book، futures/options، Funding، OI، Long/Short و liquidation با API و stream | تمرکز بر بازار سازمانی/زیرساخت داده؛ برای نسخهٔ دستی اولیه لازم نیست. |
| [Coin Metrics](https://docs.coinmetrics.io/market-data) | کندل، trades، order-book، futures/options و متریک‌های بازار/on-chain در سطوح مختلف | برای پژوهش و backtest استانداردشده؛ شرایط دسترسی و licensing مهم است. |
| [CoinDesk Data](https://data.coindesk.com/derivatives) | دادهٔ مشتقات با تاریخچهٔ granular، trades، OI، index و funding | ارائه‌دهندهٔ حرفه‌ای؛ پیش از انتخاب باید قیمت، پوشش بازار و حقوق استفاده بررسی شود. |
| [Binance public data](https://github.com/binance/binance-public-data) | کندل، aggTrades و آرشیو عمومی منتخب | بهترین نقطهٔ شروع برای ادامهٔ تحلیل با دادهٔ قبلی؛ ولی برای OI پنج‌دقیقه‌ای تا ۲۰۲۱ نباید بدون بررسی محدودهٔ API فرض گرفت که آرشیو کامل موجود است. |
| [Bybit API — OI](https://bybit-exchange.github.io/docs/v5/market/open-interest) | OI در بازه‌های ۵m تا روزانه با صفحه‌بندی | برای گردآوری تاریخچهٔ موجود نماد؛ خروجی‌ها را با نرخ‌های به‌روزرسانی و محدودیت‌های API کنترل کن. |

---

## ۷. موارد جدیدی که از فهرست قبلی جا افتاده بودند

1. **Basis Charts:** مهم‌ترین گزینهٔ تازه برای تست یک محیط چندپنلی، چون ظاهراً بخش زیادی از کارهای TradingView + derivatives + options + order flow + screener را در یک محیط رایگان جمع می‌کند. اما Pine ندارد/سازگاری Pine تأیید نشده؛ کدهای فعلی ما مستقیماً قابل انتقال فرض نشوند.
2. **Swolecharts:** به‌دلیل اینکه روش پوشش داده را با شفافیت اعلام می‌کند و برخی ابزارهای نظارتی را بدون ورود/هزینه عرضه می‌کند، ارزش تست زودهنگام دارد. مهم‌تر از همه، تفاوت «تکمیل‌شده» و «نمونه‌برداری‌شده» در liquidations را مشخص می‌کند.
3. **D.Terminal:** ترمینال مقایسهٔ funding/OI چند venue؛ باید در برابر Swolecharts/Coinalyze از نظر زمان‌مُهر و پوشش سنجیده شود.
4. **CoinAnk:** جایگزین جدی CoinGlass با heatmapهای مشتقات، orderbook-depth delta و داده‌های ETF/Hyperliquid.
5. **Basis options workspace و Laevitas CLI:** گزینه‌های تازه‌تر برای تحلیل آپشن و ابزارهای خط فرمان؛ فعلاً زمینه‌ای، نه سیگنال ورود.
6. **CoinGlass API Skills/MCP:** برای ساخت دستیار داده‌خوان در آینده مفید است، اما API آن سهمیه و پلن دارد. در نسخهٔ دستی فعلی نیاز نیست؛ API key را هم نباید در کد عمومی قرار داد.
7. **Pine Screener در TradingView:** برای اسکن فهرست نمادها با اسکریپت خودمان، با محدودیت ۵۰۰ کندل و تایم‌فریم‌های پشتیبانی‌شده. برای آزمایش‌های بلندمدت پژوهشی جایگزین Python نیست.
8. **Swolecharts free tools:** volume monitor، CVD screener، OI screener، order-book liquidity heatmap و liquidation calculator؛ بعضی از این قابلیت‌ها در فهرست قبلی اصلاً لحاظ نشده بودند.

---

## ۸. ترکیب داده‌ها برای تصمیم معاملاتی

این جریان کار را پیشنهاد می‌کنم. هدف آن دادن سیگنال قطعی نیست؛ هدف رد کردن موقعیت‌های نامناسب و ساختن تصمیمی مستند است.

### مرحلهٔ A — زمینه و ساختار قیمت

- نمودار BTCUSDT در TradingView یا Basis روی 4h و 1h؛ سطوح روز قبل/هفته، ساختار سقف و کف‌ها، ناحیهٔ رنج یا روند.
- تقویم اقتصادی برای رویدادهای کلان نزدیک.
- اگر ساختار با تایم‌فریم‌های بزرگ‌تر متعارض است، معامله را به اجبار انتخاب نکن.

### مرحلهٔ B — آیا حرکت با مشارکت بازار همراه است؟

در Swolecharts یا Coinalyze، قیمت را کنار OI، Funding، حجم و CVD ببین. مثال‌های قابل‌بررسی (نه قوانین اثبات‌شده):

- قیمت بالا + OI بالا: اهرم جدید در حال اضافه‌شدن است؛ به‌تنهایی نمی‌گوید کدام سمت درست است.
- قیمت بالا + OI پایین: ممکن است بخشی از حرکت از بستن شورت‌ها باشد.
- جهش CVD بدون پیشروی قیمت: می‌تواند نشانهٔ جذب سفارش یا مقاومت باشد؛ برای نتیجه‌گیری باید روی همان venue و timestamp بررسی شود.
- Funding بسیار یک‌طرفه: زمینهٔ شلوغی موقعیت‌ها را نشان می‌دهد، نه دستور قطعی برای خلاف روند معامله‌کردن.

### مرحلهٔ C — نقدشوندگی و ریسک حرکت سریع

- یک liquidation map (CoinGlass یا CoinAnk یا The Kingfisher) فقط برای ناحیه‌های فرضی فشار.
- یک Order Flow chart (Bookmap یا GoCharting یا Exocharts) برای دیدن دفتر سفارش و جریان معاملهٔ واقعیِ همان بازار.
- اگر این دو با هم اختلاف دارند، اختلاف را ثبت کن؛ نقشهٔ لیکوئید و دفتر سفارش یک نوع داده نیستند.

### مرحلهٔ D — ماشهٔ ورود

ورود فقط از روی قاعدهٔ ازپیش‌نوشته‌شده و کندل بسته‌شده بررسی شود. الگوی پولبک EMA20 در آزمون قبلی پروژه پس از هزینه منفی بود؛ پس نباید صرف نصب ابزار یا مشاهدهٔ شکل آشنا، آن را تأییدشده فرض کنیم. تا وقتی قانون ورود edge نشان نداده، خروجی درست چک‌لیست می‌تواند «عدم معامله» باشد.

### مرحلهٔ E — کنترل ریسک

- از RiskFirst Helper فعلی برای اندازهٔ پوزیشن، هزینه نسبت به زیان برنامه‌ریزی‌شده و سقف زیان استفاده کن؛ به یاد داشته باش که اسکریپت فعلاً دادهٔ صرافی را نمی‌خواند و کامپایلر واقعی TradingView آن را هنوز تأیید نکرده است.
- اگر صرافی/نماد اجرای خودت با دیتای مرجع متفاوت است، قیمت، کارمزد، Funding، tick size و نقدشوندگی را از همان venue بررسی کن.
- `PASS` یعنی فقط قواعد ورودی برقرارند؛ نه اینکه LONG/SHORT درست است.

---

## ۹. اختلاف داده‌ها را چطور مدیریت کنیم؟

پیش از اعتماد، برای هر پنل پنج چیز را ثبت کن: (۱) venue، (۲) نام دقیق قرارداد spot/perpetual/inverse، (۳) واحد OI، (۴) timestamp و تأخیر، (۵) آیا مقدار observed است یا مدل‌شده.

برای مثال، OI تجمیعی ۵ venue را با OI یک قرارداد Binance مقایسهٔ مستقیم نکن. نرخ Funding را بدون تبدیل دوره‌های تسویه مقایسه نکن. مجموع لیکوئیدها را کامل فرض نکن. دادهٔ ETF که روزانه منتشر می‌شود را در کنار جریان سفارش ۱۵دقیقه‌ای به‌عنوان تأیید هم‌زمان استفاده نکن.

**برای انجام معامله، قیمت و دفتر سفارش venue واقعی اهمیت نهایی دارند.** اگر از صرافی‌ای استفاده می‌کنی که ارائه‌دهندهٔ داده پوشش نمی‌دهد، یک سرویس تجمیعی نمی‌تواند جای دادهٔ همان صرافی را بگیرد. همچنین پیش از واریز وجه، مجازبودن دسترسی و امکان برداشت را طبق شرایط رسمی سرویس بررسی کن؛ برای دورزدن محدودیت جغرافیایی/حقوقی نباید به مخفی‌سازی محل یا اطلاعات حساب متوسل شد.

---

## ۱۰. چه چیزهایی را فعلاً نخریم یا به سیگنال تبدیل نکنیم؟

- اشتراک CoinGlass API فقط برای «داشبورد»؛ ابتدا از صفحهٔ عمومی استفاده کن و ببین دقیقاً کدام endpoint لازم است.
- هم‌زمان اشتراک CoinGlass + CoinAnk + Hyblock + Coinalyze + Velo بدون مسئلهٔ مشخص؛ احتمالاً اطلاعات زیادی تکرار می‌شود.
- دادهٔ tick-level گران مثل Tardis/Kaiko/Amberdata پیش از داشتن فرضیهٔ قابل‌آزمون.
- مدل‌های GEX، max pain، whale transfer یا Fear & Greed به‌عنوان دستور ورود ۱۵دقیقه‌ای.
- هر «نقشهٔ لیکوئید» به‌عنوان مقصد قطعی قیمت.
- هر ردیف API که واحد، venue، timestamp یا تازگی مشخص ندارد.
- هر سیگنال Long/Short مبتنی بر چند شاخص هم‌بسته که جداگانه به‌عنوان «چند تأیید» شمرده شده باشند.

---

## ۱۱. برنامهٔ تست عملی در چارت

**روز اول: بدون نصب سنگین**
1. بازکردن Basis Charts و بررسی BTCUSDT perpetual در Binance/Bybit/OKX، علامت‌زدن زمان داده و بررسی اینکه کدام پنل‌ها واقعاً در حساب و منطقهٔ شبکهٔ تو باز می‌شوند.
2. بازکردن TradingView و افزودن RiskFirst Helper؛ ابتدا فقط صحت کامپایل و محاسبات، نه معامله.
3. بازکردن Swolecharts در کنار CoinGlass یا CoinAnk؛ مقایسهٔ OI، funding و liquidation مربوط به یک timestamp مشترک.
4. بازکردن Bookmap Digital یا GoCharting و بررسی یک نمونهٔ دفتر سفارش/footprint روی همان venue.

**روزهای بعد: ثبت ۲۰ نمونهٔ بدون معامله**
برای هر موقعیت بالقوه، قبل از دیدن نتیجه ثبت کن: زمان UTC، venue، TF، ساختار قیمت، تغییر OI، Funding استانداردشده، CVD/تیکر، ناحیهٔ نقدشوندگی، هزینهٔ تخمینی، ورود فرضی، حد ضرر، هدف و دلیل لغو. سپس بررسی کن کدام داده واقعاً چیزی اضافه کرده است. اگر اطلاعات یک ابزار در زمان مشاهده در دسترس نبوده، مقدار آن را حدس نزن.

این ۲۰ نمونه فقط برای بررسی کیفیت فرایند و عادت خواندن چارت است؛ برای اثبات edge آماری کافی نیست.

---

## ۱۲. منابع رسمی اصلی

- TradingView OI: https://www.tradingview.com/support/solutions/43000762388-understanding-crypto-open-interest/
- TradingView Long/Short Accounts: https://www.tradingview.com/support/solutions/43000762399-long-short-ratio-accounts/
- TradingView Pine Screener limitations: https://www.tradingview.com/support/solutions/43000742436-tradingview-pine-screener-key-features-and-requirements/
- Basis Charts: https://www.basischarts.com/ ; derivatives: https://www.basischarts.com/docs/derivatives ; options: https://www.basischarts.com/free/free-crypto-options-data
- Swolecharts about/data sources: https://swolecharts.com/about ; coverage/history: https://swolecharts.com/coverage
- CoinGlass Futures dashboard: https://www.coinglass.com/currencies/BTC/futures ; liquidation: https://www.coinglass.com/liquidations ; API pricing: https://www.coinglass.com/pricing ; API Agent: https://docs.coinglass.com/reference/coinglass-agent-skill
- CoinAnk: https://coinank.com/
- Coinalyze: https://coinalyze.net/ ; API docs: https://api.coinalyze.net/v1/doc/
- The Kingfisher: https://thekingfisher.io/liquidations-map
- Hyblock Coin Screener docs: https://academy.hyblockcapital.com/tools/coin-screener
- Bookmap Crypto: https://bookmap.com/en/crypto ; pricing: https://bookmap.com/en/packages-comparison
- GoCharting Crypto: https://gocharting.com/trading/market-data/crypto
- Exocharts: https://help.exocharts.com/hc/en-us/articles/4413995353489-web-platform-overview
- Velo docs: https://docs.velo.xyz/velo-data/futures-page
- CryptoQuant pricing: https://cryptoquant.com/pricing ; APIs: https://cryptoquant.com/apis
- Glassnode: https://studio.glassnode.com/ ; pricing: https://studio.glassnode.com/pricing
- Farside ETF data: https://farside.co.uk/bitcoin-etf-flow-all-data/
- Deribit DVOL API: https://docs.deribit.com/api-reference/market-data/public-get_volatility_index_data
- Laevitas options: https://app.laevitas.ch/assets/options/overview/btc ; CLI: https://cli.laevitas.ch/
- Tardis: https://tardis.dev/ ; historical coverage: https://docs.tardis.dev/historical-data-details
- CoinAPI historical data FAQ: https://www.coinapi.io/products/market-data-api/faq
- Amberdata data: https://www.amberdata.io/market-data
- Coin Metrics market data: https://docs.coinmetrics.io/market-data
- CoinDesk Data derivatives: https://data.coindesk.com/derivatives
- DeFiLlama: https://defillama.com/
- Alternative.me Fear & Greed: https://alternative.me/crypto/fear-and-greed-index/
- CoinMarketCal: https://coinmarketcal.com/
- Coindar: https://coindar.org/
- Investing.com Calendar: https://www.investing.com/economic-calendar/
- FRED Treasury yield: https://fred.stlouisfed.org/series/DGS10
- CFTC COT guide: https://www.cftc.gov/MarketReports/CommitmentsofTraders/AbouttheCOTReports/index.htm
- Binance public data: https://github.com/binance/binance-public-data
- Bybit OI API: https://bybit-exchange.github.io/docs/v5/market/open-interest

---

## نتیجهٔ نهایی

برای استفادهٔ فعلی خودت، این ترتیب بیشترین احتمال را دارد که فایدهٔ واقعی بدهد و کمترین هزینه/شلوغی را تحمیل کند: **TradingView + آزمایش Basis Charts + Swolecharts + یک سرویس مشتقات ثانویه (CoinGlass یا Coinalyze/CoinAnk) + یک ابزار Order Flow (Bookmap یا GoCharting).** داده‌های ETF، تقویم و آن‌چین در پنجره‌های جدا برای زمینه بمانند.

این پشته «سیگنال برنده» تضمین نمی‌کند. پیش از استفاده از هر الگوی ورود، باید آن الگو با قواعد مشخص و هزینهٔ واقع‌گرایانه روی دادهٔ استفاده‌نشده آزموده شود. پژوهش قبلی پروژه، الگوی پولبک EMA20 با فیلتر تایم‌فریم‌های بالاتر را بعد از هزینه تأیید نکرده؛ پس در حال حاضر ابزارها را برای بهتر دیدن و حذف موقعیت‌های نامناسب به کار ببر، نه برای توجیه ورود به یک معامله.
