# Remote synchronization checklist — 2026-10-30

## Verified state

Repository: `aminshahsaheb/btc-signal-lab`  
Branch: `main`  
Latest verified head: `e9672400c3918f192aa5ccbf2aeba452d8fadbb1`  
Remote tree: 27 files; GitHub API reported `truncated=false`.

The remote tree contains the README, status/map/rules/roadmap, upload and artifact manifests, Atlas audit/reproduction reports, selected Pine sources, D-LIQ and Forward Journal drafts/reviews, and data helper scripts. See `UPLOAD_MANIFEST.md` for exact paths.

## Not verified on remote

- `artifacts/data/BTCUSDT_5m_2021_to_latest_csv.gz`
- `artifacts/archives/Atlas_v1_package.zip`
- `artifacts/reproduced/Atlas_v1_reproduced_outputs_2026-10-30.zip`
- Move-Odds source ZIPs, legacy ZIPs, golden vectors and verification trees
- Atlas Persian PDF report
- Remaining local source inventory, scripts, policies, workflows and configuration files

These are included in the complete local v4 bundle. Their presence on GitHub has not been established.

## Safe completion path

1. Extract the v4 ZIP; it contains a top-level `btc-signal-lab/` directory.
2. Clone the existing repository; do not initialize a new one or force-push.
3. Copy the package over the clone while preserving `.git`.
4. Review `git status --short`, especially deletions and binary additions.
5. Run `python3 scripts/verify_sources.py` and `python3 scripts/verify_dataset.py`.
6. Commit and push normally.
7. Fetch the remote Git tree and verify exact paths, sizes and hashes.

Large binaries should use Git LFS or GitHub Releases where available. The current connector workflow can update UTF-8 text files but has not verified a binary upload path for these archives.

## Exclusions

Do not commit raw conversation exports, credentials, API keys, tokens, private account details, or live account data. The repository should remain private pending review of licensing and source-data rights.
