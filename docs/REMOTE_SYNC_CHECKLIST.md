# Remote synchronization checklist — 2026-10-30

## Verified state

GitHub repository: `aminshahsaheb/btc-signal-lab`
Branch: `main`
Verified head at audit: `f6557d1aee92382c6d797e4fdda9ffc9c2f3f32f`
Remote tree: 24 files; API reported `truncated=false`.

The current remote tree contains README, project status/map/rules, upload and artifact manifests, Atlas data/reproduction reports, selected Pine sources, D-LIQ and Forward Journal drafts/reviews, and dataset helper scripts.

## Not verified on remote

- `artifacts/data/BTCUSDT_5m_2021_to_latest_csv.gz`
- `artifacts/archives/Atlas_v1_package.zip`
- `artifacts/reproduced/Atlas_v1_reproduced_outputs_2026-10-30.zip`
- Move-Odds source ZIPs, legacy ZIPs, golden vectors and verification files
- Atlas Persian PDF report
- Remaining local docs, scripts, workflow, policies and source inventory.

These files exist in the prepared local v3 package where listed. Their presence in the remote tree has not been established.

## Safe completion path

1. Download and extract `btc-signal-lab-complete-v3.zip`.
2. Clone the existing remote repository; do not initialize a new one or force-push.
3. Copy the bundle over the clone, preserving `.git`.
4. Review `git status --short`; inspect additions, updates and deletions.
5. Run `python3 scripts/verify_sources.py` and `python3 scripts/verify_dataset.py`.
6. Commit and push normally.
7. Fetch the remote Git tree and verify exact paths and binary sizes/hashes.

Large binary artifacts should use Git LFS or GitHub Releases if repository limits and account entitlements permit. Do not commit the raw conversation export, secrets, or live account data.
