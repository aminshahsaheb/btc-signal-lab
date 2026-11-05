# Repository visibility and publication safeguards

The repository aminshahsaheb/btc-signal-lab is **Public** as of 2026-11-04. The owner selected this visibility. This document replaces the old private-repository setup instructions; those instructions are historical and must not be used to create or configure a new repository.

Public visibility does not grant a license, establish ownership of third-party data, or confirm that every archived file is cleared for redistribution. No general reuse license is provided. Data-rights, archive-content, and disclosure review remain open.

## Required safeguards

- Do not commit API keys, tokens, passwords, exchange account details, raw private conversations, or private live captures.
- Do not assume that public availability permits reuse or redistribution of datasets, archives, screenshots, or third-party materials.
- Keep historical research artifacts and rejected hypotheses for audit. Do not describe them as validated trading systems.
- Before adding new data, record its source, terms, permitted use, and redistribution status.
- Use GitHub noreply commit email for future public commits where possible. Do not rewrite existing history without a separate impact review and explicit authorization.
- A passing checksum or CI run verifies only the tested files and checks. It does not provide legal clearance or prove a trading edge.

## Current release gate

The repository is public, but it is **not cleared for general redistribution**. The A3 scan was limited screening. PDF content was not OCRed or semantically reviewed; the v4 comparison is incomplete; source-specific data rights remain unresolved. No license file is present.

## Git verification

Run from a clean checkout:

    python3 scripts/verify_sources.py
    git status --short
    git log -1 --oneline

Regenerate docs/FILE_INVENTORY_SHA256.csv with scripts/generate_inventory.py after intentional file changes. Then run the verifier. Update artifacts/SHA256SUMS.txt only when a pinned file changes. Preserve the exact commit SHA and CI result in the status register.
