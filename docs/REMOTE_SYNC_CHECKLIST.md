# Remote synchronization audit — 2026-10-30

## Verified remote state

- Repository: `aminshahsaheb/btc-signal-lab`
- Visibility: **Private**
- Branch: `main`
- Verified head: `1886f9e6b5e424bd6e421b28eded3b068ff25398`
- Commit message: `chore: sync complete audited BTC research bundle`
- Recursive Git tree: **112 file blobs**; API response was not truncated.
- SHA-256 inventory: **111 entries**, excluding the inventory file itself.
- No remote file path containing a literal backslash was found.
- The compressed BTCUSDT five-minute dataset, Atlas archive, reproduced Atlas outputs, Move-Odds archives, Pine sources, research specifications, reviews, scripts, and workflow are present in the remote tree.

## GitHub Actions

Workflow: `.github/workflows/verify.yml`  
Run: https://github.com/aminshahsaheb/btc-signal-lab/actions/runs/40988138287

- Event: `push`
- Head SHA: `1886f9e6b5e424bd6e421b28eded3b068ff25398`
- Job: `verify`
- Conclusion: **success**
- Steps: checkout, Python 3.12 setup, and `python3 scripts/verify_sources.py` all completed successfully.

This is a source-integrity CI pass. It is not a scientific validation, a Pine compiler result, a live-feed quality result, or a venue execution test.

## Earlier stale statements corrected

The previous version of this file described a 27-file remote tree and several local-only artifacts. Those statements described an earlier repository state and became obsolete after commit `1886f9e`.

## Remaining verification limits

- The connector's recursive tree confirms remote paths and blob sizes, not a fresh local clone's complete byte-for-byte equality with the source machine.
- Dataset identity and structural checks are documented in `docs/BTCUSDT_5M_DATA_AUDIT_2026-10-30.md`; the dataset is historical and already used.
- Move-Odds v0.1.2 and Risk-First Helper v0.3.1 still require actual TradingView compilation.
- Historical Move-Odds verification scripts are not yet a self-contained clean-clone harness; see `docs/reviews/2026-10-30-move-odds-package-portability.md`.
- D-LIQ r1 and Forward Journal r7 remain drafts, not locked.
- No live collector, T0, forward directional test, or KCEX execution validation has started.

## Security and publication

Keep the repository private. Do not commit credentials, tokens, raw private conversation exports, or raw live capture. Review data rights and licensing before any public release.
