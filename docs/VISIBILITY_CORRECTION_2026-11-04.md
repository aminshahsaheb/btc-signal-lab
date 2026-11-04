# Repository visibility correction — 2026-11-04

## Confirmed state

- Repository: aminshahsaheb/btc-signal-lab
- Visibility: **Public**, confirmed from GitHub repository metadata on 2026-11-04.
- This visibility reflects the owner's explicit choice.
- Older statements that the repository is private are historical records. They do not describe the current state.

## What Public does not mean

Public visibility does not grant a reuse license, prove ownership of third-party data, or clear the repository for general redistribution. No general reuse license is provided. Archive-content and source-specific data-rights review remain open.

The prior A3 screening was limited. It did not perform OCR or full semantic review of PDFs. The v4 archive comparison is incomplete. Data rights remain unresolved. The scan is not release clearance.

## Research gates remain unchanged

- No strategy is independently validated or approved for live trading.
- D-LIQ r3 remains **DRAFT / NOT LOCKED**. Its missingness, builder, differential, independent-review, real-feed, anchor, and collector-host gates remain open.
- Forward Journal r7 remains **DRAFT / NOT LOCKED / SPEC ONLY**. D25 is not satisfied.
- Move-Odds v0.1.2 and Risk-First v0.3.1 still need actual TradingView compile/runtime evidence.
- No collector, T0, forward directional test, or live trading is authorized by this visibility change.

## Pull request disposition

PRs #15–#19 were previously verified as open draft PRs. Their CI successes apply only to their recorded head commits. They are not independent review, approval, merge, protocol lock, or release clearance. Resolve overlapping workflow changes before merging any of them.

## Required follow-up

1. Regenerate docs/FILE_INVENTORY_SHA256.csv with scripts/generate_inventory.py.
2. Reconcile artifacts/SHA256SUMS.txt and verify both manifests.
3. Run CI on the exact final commit.
4. Review PR overlap and obtain independent review where required.
5. Keep data-rights and scientific gates open until evidence closes them.
