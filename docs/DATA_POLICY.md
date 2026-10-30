# Data and artifact policy

## Include

- Curated project state, decisions, reviews, preregistrations and code.
- Original historical Atlas package, exact matching input and reproduced outputs.
- Move-Odds versions, golden vectors, lookup tables and verification artifacts.
- D-LIQ and Forward Journal drafts with immutable version history.
- Risk-First source and checksums.

## Exclude

- Raw conversation exports and unrelated personal information.
- Credentials, API keys, tokens, account exports and private details.
- Live collector logs or real-time liquidation messages unless a separate data-handling decision explicitly authorizes them.
- Unrelated projects.

## Historical data

Atlas history is burned by prior exploration, discovery, confirmation, holdout use, and reproduction. Storing it in Git does not restore virgin status. Do not use it as fresh evidence for a new candidate.

## Archive rules

1. Keep received source ZIPs and compressed datasets byte-for-byte unchanged.
2. Preserve old versions; never overwrite a preregistration or release.
3. Update SHA manifests in the same change as any pinned artifact.
4. A checksum pass is not scientific validation.
5. Keep the repository private until license and source-data rights are reviewed.
6. Never silently substitute a different dataset for a required input.
