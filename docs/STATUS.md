# Repository status — 2026-10-30

## Current decision

**NO LOCK — SPEC REVISION ONLY.**

- D-LIQ r1 is a draft. Its statistical procedure, message-validity rules, deduplication contract, sample accounting, and evidence anchoring need closure before lock.
- No live collector is running.
- No D-LIQ market data has been scored.
- No T0 has been set.
- Move-Odds v0.1.2 has not been compiled in TradingView.
- Risk-First Helper v0.3.1 has not been compiled in TradingView.
- Forward Journal r7 is a draft, not a locked evidence system.

## Component separation

Move-Odds addresses timing, not direction. D-LIQ tests a directional continuation hypothesis. Risk-First checks a proposed plan against configured risk constraints. Execution validation must account for actual fees, spread, slippage, funding, and venue conditions. These claims must not be merged.

## Data limitations

Historical BTC data used in previous exploration is not a clean holdout for new claims. The Atlas archive references an external `pkg_data.csv` input that was not present in the supplied working set. No complete raw OHLC dataset or live capture is included in the current source set.

## Immediate gates

1. Recover and verify missing source data, or explicitly document that historical reruns are not reproducible.
2. Complete D-LIQ r2 without examining evaluation returns.
3. Freeze a standalone statistical analysis implementation and test vectors.
4. Freeze message validity, deduplication, timestamp and missing-price behavior.
5. Complete a standalone evidence journal and anchoring test.
6. Compile Move-Odds and Risk-First in TradingView and retain compiler/runtime evidence.
7. Only then consider a bounded data-quality probe. No T0 before protocol lock.
