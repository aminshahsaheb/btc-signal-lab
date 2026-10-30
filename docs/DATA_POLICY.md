# Data and artifact policy

## Included

- Curated project state, research inventory, decisions, independent reviews, and source audit.
- The original Atlas v1 package, its Persian explanatory PDF, and the exact historical `pkg_data.csv` input in gzip form.
- Move-Odds v0.1.2 Pine source, golden vectors, lookup data, verification code/reports, and original source ZIP.
- Historical Move-Odds v0.1 and v0.1.1 source packages, the v0.1.2 patch package, and the v0.1.1 standalone Pine file.
- D-LIQ r0/r1 preregistration drafts and the independent review history.
- Forward Journal r5/r6/r7 drafts, with earlier versions clearly archived and r7 marked unlocked.
- Risk-First Helper Pine source and SHA-256 manifests.

## Deliberately excluded

- The raw conversation export (`chat-share (12).txt`). It is not an appropriate source-controlled project artifact and can include unrelated personal/sensitive material. Curated research findings and decisions are preserved in project documents.
- Live collector logs, real-time liquidation messages, account exports, exchange API keys, credentials, tokens, and private account details.
- Unrelated Fanus project material.
- Any claim that a historical artifact is a clean holdout or forward proof.

## Historical reuse / burned data

The Atlas input dataset is included for provenance and reproducibility. Its historical ranges were previously inspected for exploration, discovery, confirmation, and holdout analysis. Storing data in Git does not restore its virgin status. Do not use it as fresh evidence for a new directional candidate.

## Archive rules

1. Keep received source ZIPs and received compressed data byte-for-byte unchanged.
2. Preserve prior versions under an archive directory; do not overwrite a prior preregistration or software release.
3. Refresh SHA manifests only as part of a documented artifact change. A refreshed checksum does not imply that scientific results were revalidated.
4. Before changing repository visibility, inspect the complete archive contents and confirm data/license terms. This repository has no `LICENSE` file by design at this stage.
5. Never silently substitute a different dataset for a missing research input. For Atlas, the decompressed input must match the recorded SHA-256 prefix in its README.
