# C1 r3.1 package identity and storage decision — 2026-11-04

## Exact package identity

- Archive: `dliq_r3_1_candidate.zip`.
- Size: 2,455,000 bytes.
- SHA-256: `4d3faaae13e0263ac1f422a3b6d88904d70057b4bb5271029c1ce5cc9d194ec2`.
- The archive bytes were retrieved from the user's Library and hashed locally. The computed hash matches the value recorded in Issue #4 and the PR #15 package record.
- `sha256sum -c MANIFEST.sha256`: PASS for every file in the extracted candidate package.

## Protocol separation

- Candidate r3.1 protocol: `protocol/PREREG_D-LIQ-SNAPSHOT-CONT4H-v1_r3_DRAFT.md`, SHA-256 `5c05a15de7addd55cade7617fcdcaea570aad82b61c0b16c95d14024fc649948`.
- Original r3 protocol preserved at `protocol/superseded/PREREG_D-LIQ-SNAPSHOT-CONT4H-v1_r3_DRAFT_original_2026-11-03.md`, SHA-256 `449753f9c74bc3d5b41313664f062b50948104906042197f1ed61bacb886df8d`.
- Both values were independently recomputed from the extracted bytes and match the package manifest.
- The candidate index and reproduction record name the two hashes separately. No r3 result is silently relabelled as r3.1.

## Storage decision

**Decision: retain the exact binary ZIP in the user's private Library as the controlled archive; do not add a duplicate binary blob to GitHub at this stage.**

Reasons:
1. The archive is already retrievable in the controlled Library and has a fixed, verified SHA-256.
2. The package contains generated caches and binary artifacts. The Git repository can keep the source files, hash records, review evidence, and reproduction instructions without a second binary copy.
3. Data rights and redistribution terms are not yet fully cleared. Keeping the archive out of GitHub avoids implying that the package is licensed for redistribution.

Limit: the Library archive is controlled by the user account. A collaborator who does not have access to that Library cannot retrieve the ZIP from GitHub alone. Any later hand-off must provide the exact archive and re-check its SHA-256 before use.

## Component and test retrievability

The exact archive contains the candidate protocol, Writer, primary verifier, active independent verifier, preserved as-delivered independent verifier, direct regression tests, differential harness, manifest, and reproduction instructions. The C3 evidence note records their exact hashes and the direct NONE-slot test results.

The following checks passed in this review:
- Package manifest verification.
- Writer/primary verifier suite: 199 checks, 0 failures.
- Active independent verifier suite: 93 tests, all passed.
- r3 consistency: 16 checks, 0 failures.

## C1 checklist

- [x] Candidate archive SHA-256 matches the recorded value.
- [x] Candidate protocol SHA-256 matches the recorded value.
- [x] Original r3 and candidate r3.1 remain separate and byte-identifiable.
- [x] Binary storage decision recorded: controlled private Library, not GitHub binary.
- [x] Protocol, Writer, both verifier variants, tests, and manifest are retrievable from the exact hash-verified archive.

**C1 = 5/5 complete.** This establishes package identity and reproducibility evidence only. It does not lock the protocol, approve third-party review, authorize live collection, T0, scoring, or trading.
