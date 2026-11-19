# RESULTS_SETUPLAB_v1 — the single scoring run of PREREG_SETUPLAB_v1

**Status: RESULT RECORD. Verdicts below were produced mechanically by the frozen code under the frozen rule; nothing was changed after the output was seen.** Nothing here is self-certified: the tests of the code are synthetic and written by the same author, and no independent review has taken place. This is not evidence of profitability.

- Preregistration: `specs/setup-lab/PREREG_SETUPLAB_v1.md`; code SHA-256 `0bca0bd5a6e6698f931e377d599fa63072300ad197445932712e1a82ed0d069d` (hash check passed inside the run).
- Run: GitHub Actions workflow "Setup Lab v1 scoring run (real public data)", run id 44456059772, job 135331233719, commit `f1a6a2b3769e34f23fb706e22165db3d9a47d77a`, 2026-11-19. Python 3.12.16, numpy 2.5.3. The workflow ran the 38 synthetic tests first (all passed). It ran once; no re-run was needed (all data fetched, no asset excluded).
- Data: Binance spot daily klines for 10 pooled pairs and BTCUSDT (reference), 2017-08-17 .. 2026-11-16, no missing days; per-asset data SHA-256 are in the table below so a re-fetch can be compared.

## Verdicts under the frozen rule (the only conclusions)

| setup | verdict | why (frozen criteria) |
|---|---|---|
| S1 trend breakout | INCONCLUSIVE | mean net +0.113 R, n=1266; 99% interval of the mean [-0.014, +0.229] includes 0 and +0.10, so P2 and P3 failed narrowly; the data neither show an edge at the pre-set confidence nor exclude one of practical size |
| S2 pullback in trend | FAIL | mean net -0.112 R, n=1098; upper 99% bound +0.061 R < +0.10 R: an edge of practical size is excluded |
| S3 overextension fade | FAIL | mean net -0.088 R, n=1258; upper 99% bound +0.015 R < +0.10 R: an edge of practical size is excluded |
| S4 compression then expansion | INCONCLUSIVE | mean net +0.191 R, n=715; 99% interval [-0.018, +0.416]; P2 and P3 failed narrowly |
| S5 capitulation / blow-off fade | INCONCLUSIVE | n=200 < 300 (P1): underpowered |

No setup passed. By the preregistration (rule 10 and section 8.5), S2 and S3 are closed in this form; S1, S4 and S5 are not shown to work and are not shown to fail. Under section 9, there is **no candidate** from this run.

## Descriptive observations (post-hoc; NOT conclusions, NOT a basis for tuning)

- S1 and S4 both have positive pooled means. They are both trend/expansion rules on the same assets, so they are not independent evidence of each other.
- S1's mean is larger before 2022 (+0.209 R, n=557) than from 2022 (+0.037 R, n=709). S4 is similar in both halves (+0.196 / +0.188).
- S4's long side (+0.324 R, n=407) is far better than its short side (+0.016 R, n=308); S2's short side is the worst part of S2 (-0.191 R, n=661). These splits were not pre-registered; acting on them on this same data would be post-failure rescue (RESEARCH_RULES rule 4).
- Typical stop distance is large: about 14% of price (S1), 10% (S2, S3), 16% (S4), 23% (S5). Position sizes consistent with a fixed small risk per trade would therefore be small.
- Rough sample-size arithmetic from the reported intervals (not a pre-registered quantity): for the 99% lower bound to clear zero at the observed means, S4 would need roughly 2.4 times the trades of this run and S1 roughly 2.1 times, i.e. on the order of 10–20 more years of this 10-coin pool. A single-asset manual trader cannot reach that in a useful time.
- Every non-BTC series used here has now been inspected for direction decisions. It is burned for any follow-up setup (RESEARCH_RULES rule 2); a follow-up that looks at the same history is exploration that inflates the false-positive rate and can only be confirmed on data not yet seen.

## Cumulative count

Setups tested by this lab on non-BTC daily data: 5 (S1–S5), one scoring run.

## Raw report printed by the run (verbatim; headings demoted one level)

## Setup Lab v1 results (setuplab-v1)

code sha256: `0bca0bd5a6e6698f931e377d599fa63072300ad197445932712e1a82ed0d069d`
Nothing here is self-certified: the tests of this code are synthetic and written by the same author; no independent review exists.

### Data
| symbol | status | bars | missing | first | last | sha256(data) |
|---|---|---|---|---|---|---|
| ETHUSDT | OK | 3379 | 0 | 2017-08-17 | 2026-11-16 | 4fcf5f38c8d8412b |
| BNBUSDT | OK | 3298 | 0 | 2017-11-06 | 2026-11-16 | 6d50e1144bc845ce |
| XRPUSDT | OK | 3119 | 0 | 2018-05-04 | 2026-11-16 | 3d3cac5834017815 |
| ADAUSDT | OK | 3136 | 0 | 2018-04-17 | 2026-11-16 | eae2723235656146 |
| LTCUSDT | OK | 3261 | 0 | 2017-12-13 | 2026-11-16 | 082e8ddb0a68a56f |
| TRXUSDT | OK | 3081 | 0 | 2018-06-11 | 2026-11-16 | 6cc7a7ce011cc609 |
| LINKUSDT | OK | 2862 | 0 | 2019-01-16 | 2026-11-16 | 9ed2bd2f4c1ea307 |
| XLMUSDT | OK | 3092 | 0 | 2018-05-31 | 2026-11-16 | b1efa74366f66a6f |
| ETCUSDT | OK | 3080 | 0 | 2018-06-12 | 2026-11-16 | 68fa8cc976a7f879 |
| NEOUSDT | OK | 3284 | 0 | 2017-11-20 | 2026-11-16 | df0312b881b06dfb |
| BTCUSDT | OK | 3379 | 0 | 2017-08-17 | 2026-11-16 | 4d9a17e7648604ae |

### Verdicts (cost 0.16% round trip; alpha 0.01 one-sided per setup; 5 setups)

| setup | k | m | T | n | mean net R | 99% lower | 99% upper | excess vs random entry | excess 99% lower | high-cost mean | verdict | failed criteria |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| S1 trend breakout | 2.0 | 1.5 | 30 | 1266 | +0.113 | -0.014 | +0.229 | +0.093 | -0.033 | +0.100 | **INCONCLUSIVE** | P2_net_lower99>0, P3_excess_lower99>0 |
| S2 pullback in trend | 1.5 | 2.0 | 24 | 1098 | -0.112 | -0.265 | +0.061 | -0.123 | -0.274 | -0.129 | **FAIL** | P2_net_lower99>0, P3_excess_lower99>0, P4_mean_net>=0.10, P5_high_cost_mean>0, P6_assets_pos>=60%, P7_both_halves>0 |
| S3 overextension fade | 1.5 | 1.0 | 12 | 1258 | -0.088 | -0.183 | +0.015 | -0.063 | -0.159 | -0.104 | **FAIL** | P2_net_lower99>0, P3_excess_lower99>0, P4_mean_net>=0.10, P5_high_cost_mean>0, P6_assets_pos>=60%, P7_both_halves>0 |
| S4 compression then expansion | 3.0 | None | 14 | 715 | +0.191 | -0.018 | +0.416 | +0.151 | -0.052 | +0.181 | **INCONCLUSIVE** | P2_net_lower99>0, P3_excess_lower99>0 |
| S5 capitulation / blow-off fade | 3.0 | 0.5 | 10 | 200 | -0.045 | -0.182 | +0.079 | -0.022 | -0.160 | -0.053 | **INCONCLUSIVE** | P1_n>=300, P2_net_lower99>0, P3_excess_lower99>0, P4_mean_net>=0.10, P5_high_cost_mean>0, P6_assets_pos>=60%, P7_both_halves>0 |

### Detail per setup (descriptive; the verdict above is the only conclusion)

#### S1 trend breakout
- trades/asset/year 13.7; mean stop distance 13.62% of price; mean holding 11.3 bars; outcomes stop 48% / target 39% / time 13%
- mean gross +0.127 R; random-entry baseline (same exits, every bar) +0.020 R; low-cost mean +0.122; high-cost mean +0.100
- sides: long n=734 mean=+0.160; short n=532 mean=+0.047
- halves: before_2022 n=557 mean=+0.209; from_2022 n=709 mean=+0.037
- years: 2017: n=3 -0.18; 2018: n=70 +0.15; 2019: n=129 +0.23; 2020: n=183 +0.18; 2021: n=172 +0.25; 2022: n=134 -0.07; 2023: n=149 +0.02; 2024: n=186 +0.10; 2025: n=127 +0.02; 2026: n=113 +0.10
- assets: ETHUSDT n=136 +0.21; BNBUSDT n=140 +0.21; XRPUSDT n=118 +0.05; ADAUSDT n=129 +0.19; LTCUSDT n=133 +0.06; TRXUSDT n=126 +0.07; LINKUSDT n=120 +0.08; XLMUSDT n=118 -0.12; ETCUSDT n=122 +0.14; NEOUSDT n=124 +0.20
- criteria: P1_n>=300=yes; P2_net_lower99>0=NO; P3_excess_lower99>0=NO; P4_mean_net>=0.10=yes; P5_high_cost_mean>0=yes; P6_assets_pos>=60%=yes; P7_both_halves>0=yes

#### S2 pullback in trend
- trades/asset/year 11.9; mean stop distance 10.35% of price; mean holding 10.5 bars; outcomes stop 62% / target 23% / time 14%
- mean gross -0.092 R; random-entry baseline (same exits, every bar) +0.011 R; low-cost mean -0.100; high-cost mean -0.129
- sides: long n=437 mean=+0.008; short n=661 mean=-0.191
- halves: before_2022 n=445 mean=-0.130; from_2022 n=653 mean=-0.099
- years: 2018: n=46 -0.06; 2019: n=144 -0.19; 2020: n=132 -0.28; 2021: n=123 +0.07; 2022: n=138 +0.02; 2023: n=139 -0.28; 2024: n=129 -0.00; 2025: n=129 -0.08; 2026: n=118 -0.14
- assets: ETHUSDT n=128 -0.13; BNBUSDT n=102 -0.08; XRPUSDT n=104 -0.28; ADAUSDT n=121 +0.01; LTCUSDT n=107 -0.07; TRXUSDT n=106 -0.10; LINKUSDT n=93 -0.10; XLMUSDT n=111 -0.07; ETCUSDT n=106 -0.16; NEOUSDT n=120 -0.15
- criteria: P1_n>=300=yes; P2_net_lower99>0=NO; P3_excess_lower99>0=NO; P4_mean_net>=0.10=NO; P5_high_cost_mean>0=NO; P6_assets_pos>=60%=NO; P7_both_halves>0=NO

#### S3 overextension fade
- trades/asset/year 13.6; mean stop distance 10.26% of price; mean holding 4.1 bars; outcomes stop 49% / target 41% / time 10%
- mean gross -0.069 R; random-entry baseline (same exits, every bar) -0.025 R; low-cost mean -0.076; high-cost mean -0.104
- sides: long n=464 mean=-0.040; short n=794 mean=-0.115
- halves: before_2022 n=601 mean=-0.114; from_2022 n=657 mean=-0.063
- years: 2017: n=16 -0.14; 2018: n=84 -0.19; 2019: n=170 -0.14; 2020: n=188 -0.09; 2021: n=143 -0.08; 2022: n=126 -0.15; 2023: n=141 +0.08; 2024: n=173 -0.04; 2025: n=111 -0.09; 2026: n=106 -0.15
- assets: ETHUSDT n=131 -0.26; BNBUSDT n=137 -0.22; XRPUSDT n=132 -0.01; ADAUSDT n=117 -0.07; LTCUSDT n=130 -0.07; TRXUSDT n=121 -0.01; LINKUSDT n=102 -0.12; XLMUSDT n=121 -0.04; ETCUSDT n=133 -0.08; NEOUSDT n=134 +0.00
- criteria: P1_n>=300=yes; P2_net_lower99>0=NO; P3_excess_lower99>0=NO; P4_mean_net>=0.10=NO; P5_high_cost_mean>0=NO; P6_assets_pos>=60%=NO; P7_both_halves>0=NO

#### S4 compression then expansion
- trades/asset/year 7.7; mean stop distance 16.10% of price; mean holding 12.6 bars; outcomes stop 23% / target 0% / time 77%
- mean gross +0.203 R; random-entry baseline (same exits, every bar) +0.040 R; low-cost mean +0.198; high-cost mean +0.181
- sides: long n=407 mean=+0.324; short n=308 mean=+0.016
- halves: before_2022 n=296 mean=+0.196; from_2022 n=419 mean=+0.188
- years: 2018: n=49 +0.34; 2019: n=89 -0.05; 2020: n=75 +0.53; 2021: n=83 +0.08; 2022: n=95 +0.10; 2023: n=92 +0.20; 2024: n=76 +0.40; 2025: n=87 +0.09; 2026: n=69 +0.18
- assets: ETHUSDT n=71 +0.30; BNBUSDT n=69 +0.22; XRPUSDT n=66 +0.32; ADAUSDT n=68 +0.23; LTCUSDT n=75 -0.08; TRXUSDT n=81 +0.15; LINKUSDT n=66 +0.06; XLMUSDT n=73 +0.41; ETCUSDT n=70 +0.09; NEOUSDT n=76 +0.22
- criteria: P1_n>=300=yes; P2_net_lower99>0=NO; P3_excess_lower99>0=NO; P4_mean_net>=0.10=yes; P5_high_cost_mean>0=yes; P6_assets_pos>=60%=yes; P7_both_halves>0=yes

#### S5 capitulation / blow-off fade
- trades/asset/year 2.2; mean stop distance 22.59% of price; mean holding 3.6 bars; outcomes stop 32% / target 57% / time 10%
- mean gross -0.036 R; random-entry baseline (same exits, every bar) -0.023 R; low-cost mean -0.039; high-cost mean -0.053
- sides: long n=44 mean=-0.017; short n=156 mean=-0.053
- halves: before_2022 n=109 mean=-0.145; from_2022 n=91 mean=+0.074
- years: 2017: n=5 +0.19; 2018: n=13 -0.59; 2019: n=24 -0.05; 2020: n=38 -0.05; 2021: n=29 -0.20; 2022: n=11 +0.12; 2023: n=25 +0.04; 2024: n=26 +0.12; 2025: n=11 +0.16; 2026: n=18 -0.01
- assets: ETHUSDT n=15 -0.16; BNBUSDT n=25 -0.28; XRPUSDT n=27 -0.02; ADAUSDT n=18 +0.18; LTCUSDT n=15 -0.01; TRXUSDT n=16 +0.30; LINKUSDT n=19 -0.35; XLMUSDT n=22 +0.08; ETCUSDT n=28 -0.20; NEOUSDT n=15 +0.24
- criteria: P1_n>=300=NO; P2_net_lower99>0=NO; P3_excess_lower99>0=NO; P4_mean_net>=0.10=NO; P5_high_cost_mean>0=NO; P6_assets_pos>=60%=NO; P7_both_halves>0=NO

### BTCUSDT reference (burned data: descriptive only, never part of a verdict)
| setup | n | mean net R |
|---|---|---|
| S1 | 146 | +0.299 |
| S2 | 115 | -0.100 |
| S3 | 112 | -0.283 |
| S4 | 81 | +0.304 |
| S5 | 25 | -0.451 |
