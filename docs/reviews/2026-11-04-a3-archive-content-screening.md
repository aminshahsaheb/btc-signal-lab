# A3 archive, privacy, and data-rights screening — 2026-11-04

## Decision and scope

This report records a private-repository screening pass. It is **not** public-release approval, a legal opinion, or proof that every possible secret or personal identifier is absent.

The baseline snapshot is `main` at `da64085fe1c066026a6bee219b600d2b42f280f6`. Its recursive Git tree had 159 entries and 115 file blobs. The path-by-path classification is in [`A3_FILE_CLASSIFICATION_2026-11-04.csv`](../A3_FILE_CLASSIFICATION_2026-11-04.csv).

## Path classification

| Category | Files |
|---|---:|
| Source | 55 |
| Archive | 51 |
| Generated output | 9 |
| Obsolete | 0 |
| Sensitive | 0 |
| **Total** | **115** |

Classification is by repository role and provenance. It does not mean that every archive has redistribution rights. The CSV preserves each baseline path, byte size, category, and reason.

## Content screening evidence

The read-only scanner is `scripts/audit_archive_contents.py`. It scans repository text-like files, ZIP contents (including nested ZIPs), GZIP streams, and raw PDF bytes. It reports paths and counts only; it does not print matched values.

- Final scanner/inventory commit at the time of this report: `4cd198045309f76cccafeb853b2ab3b67d39bb00`.
- Exact push CI run: [#343](https://github.com/aminshahsaheb/btc-signal-lab/actions/runs/41732374243) — SUCCESS.
- Exact PR CI run: [#344](https://github.com/aminshahsaheb/btc-signal-lab/actions/runs/41732383696) — SUCCESS on the same SHA.
- Files seen by scanner: 118 (115 baseline files plus the scanner, classification CSV, and this report).
- Expanded bytes processed: 80,780,825. Nested archive content can be processed more than once; this is a work-volume measure, not a unique-byte count.
- Pattern findings: none. This includes private-key markers, common AWS/GitHub/Slack token patterns, quoted credential assignments, email candidates, formatted phone candidates, and copyright/license notice text.
- License/notice filenames found: none.
- The earlier filename-pattern review found no obvious credential or personal-data filenames.

The existing integrity verifier also passed on the baseline snapshot: five ZIP archives were structurally tested; 34 historical extracted package files were compared with their original ZIPs; the dataset identity/structure check passed. The scanner found no unsafe ZIP paths, encrypted entries, CRC failures, invalid ZIP/GZIP files, or other reported findings.

## Personal-data review: not fully closed

The repository policy states that the raw conversation export, live collector logs, exchange credentials, account exports, private account details, and unrelated Fanus material are deliberately excluded. The tracked historical dataset is OHLCV plus taker-buy-base data, not an account export.

However, pattern screening is not a semantic review. The PDF was scanned as raw bytes only; no OCR or full visual/text review was performed. The pattern set cannot detect every identifier, encoding, or secret format. Therefore this report does not claim a complete personal-data audit.

## Data rights and licensing: unresolved

- The repository has no root `LICENSE` file. `README.md` and `docs/DATA_POLICY.md` state that no license is present because reuse and publication terms have not been decided.
- No license/notice file name or recognizable license/copyright notice was found in the scanned repository and ZIP content.
- The repository contains historical market data, the Atlas package and report, Move-Odds source/archive packages, verification code, and reproduced outputs. Absence of a notice is not evidence that these materials are owned by the project or may be redistributed.
- Source URLs, upstream terms, data-provider terms, and third-party code attribution have not been established for every item. This requires a separate source-by-source rights review.

## v4 archive comparison: blocked

The exact v4 archive bytes are not available in the current repository tree or working runtime. The previously recorded expected SHA-256 is `b82694723aa3b1efbefdfff9df5f77aa15acf7c2bfc50e8b48d372e0beb1db61`, but a hash alone cannot establish its path list or contents. No v4-to-main path comparison is claimed.

## Current A3 checkbox state

- [x] Classify all 115 baseline paths.
- [x] Search repository filenames and content for common secret patterns; no matches in the recorded screening.
- [x] Keep the repository private while the audit remains open.
- [ ] Compare every v4 path with the current `main` tree; exact archive bytes are required.
- [ ] Complete the semantic review of personal files, identifiers, and the PDF; the current scan is pattern-based and the PDF has no OCR review.
- [ ] Record source-specific data and third-party licensing/redistribution terms.

**A3 is 3/6 complete, not accepted as a whole.** Public release remains blocked by the missing v4 comparison, incomplete personal-data review, and unresolved data rights. Private research work can continue.

## Next required evidence

1. Supply the exact v4 ZIP bytes. Verify the recorded SHA-256 before comparing paths.
2. Identify and record upstream terms for each market-data source, Atlas package/report, Move-Odds package, and third-party code/data.
3. Perform a human/OCR review of the PDF and any files flagged by source provenance.
4. Keep repository visibility private until all A3 acceptance conditions are met.
