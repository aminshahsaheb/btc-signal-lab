# Forward Journal r7 — D25 two-stage evidence review

Review date: 2026-11-03  
Source: `research/forward-journal/FORWARD_JOURNAL_SPEC_v1_r7_DRAFT.md`  
Disposition: **CLARIFICATION REVIEW ONLY — NO PROTOCOL CHANGE — NOT LOCKED**

## 1. Source-grounded sequence

The current r7 text supports two distinct exercises:

- **Stage A — pre-lock target qualification.** B.7(4) requires a complete rehearsal of B.7(7) against the selected real destination, using a test journal and test namespace. D25 requires the rehearsal to occur before lock and requires a report.
- **Stage B — post-lock implementation E2E.** C.1 steps 1–7 require LOCK, BUILD, DRY-RUN, CODE FREEZE, GENESIS, CONFIG, then a formal two-namespace E2E using the frozen implementation and actual journal CONFIG. It must pass before COLLECTOR_START.

These are not competing interpretations. They prove different things. Stage A proves target capability and test feasibility. It cannot prove that the final frozen writer/verifier passed. Stage B proves implementation-specific conformance for the exact frozen code and actual CONFIG.

Neither stage alone authorizes COLLECTOR_START or T0.

## 2. Proof boundary

| Requirement | Stage A: pre-lock | Stage B: post-lock |
|---|---|---|
| Real destination selected and reachable | Required | Reconfirm same destination |
| Both namespaces accept required record shapes | Required | Required |
| Destination rejects duplicate/old sequence | Required | Required |
| Destination-issued time and receipt | Required | Required |
| Independent read client reads both records | Required | Required |
| Receipt/time verification | Required | Required |
| Truncated-copy verifier check | Test verifier | Frozen verifier |
| Frozen code hash | Not yet available by sequence | Required; bind to CONFIG |
| Actual GENESIS and CONFIG identity | Not yet available by sequence | Required |
| Formal journal E2E event | Qualification report only | Required |
| Collector start / T0 | Not authorized | Still blocked by later gates |

## 3. Proposed Stage A evidence bundle

This is a review recommendation, not an added r7 requirement. Preserve:

1. Target identity: service/operator, endpoint, non-secret tenant identifier, both namespace names, and documented retention/immutability behavior.
2. Test contract: exact ten-key target-contract values. Exclude credentials; identify secret references only by stable fingerprints.
3. Probe identity: source commit/archive, source-tree SHA-256, runtime/dependency versions, and exact commands.
4. Raw operations: lossless request/response evidence for checkpoint publication, manifest-test publication, and duplicate-sequence rejection.
5. Destination evidence: records from both namespaces, in acceptance order, including destination-issued timestamps and receipts.
6. Independent reader evidence: reader identity, proof it did not use writer credentials/session, commands, and raw readback.
7. Receipt/time evidence: verification output, method, trust class, uncertainty, key/certificate fingerprint, and validation time. If method is `NONE_TRUST_ONLY`, label it trust-only; do not call it cryptographic verification.
8. Truncation evidence: original journal hash, truncated-copy hash, exact cut point, verifier version/hash, command, and output containing `TRUNCATED`.
9. Duplicate rejection evidence: before/after namespace snapshots or equivalent destination records showing rejection and no namespace change.
10. Attributable report: bind evidence hashes to target identity, test namespace, operator, probe hash, reader identity, and test time.

Never store credentials, API tokens, or private keys in the report or repository.

## 4. Stage B evidence and proposed invalidation

Stage B evidence must bind at least:

- locked spec SHA-256;
- writer/verifier/collector code-tree SHA-256;
- dependency lock and runtime manifest;
- GENESIS hash and CONFIG entry hash;
- target identity and both namespace names;
- destination records, receipts, and timestamps from both namespaces;
- duplicate rejection and independent readback evidence;
- receipt/time verification output;
- truncated-copy hash and verifier output;
- `EVENT(CHECKPOINT_E2E_TEST)` and full journal verifier report.

**Proposed invalidation rule:** repeat Stage A if target identity, operator, namespace, sequence-enforcement behavior, time source, receipt/verification method, or independent reader identity changes. Repeat Stage B if any frozen code byte, dependency lock, runtime manifest, actual CONFIG field, target identity, namespace, or evidence-producing client changes after the successful run. This is conservative review advice; r7 does not state this complete rule.

Do not convert a failed Stage B run into a pass by changing the seven self-reported `checks` booleans. Preserve failed evidence. Use a fresh test namespace or destination and fresh journal when B.7(7) requires it.

## 5. D25 closure matrix

| Item | Required evidence | Current status |
|---|---|---|
| KAT-17 X00–X19 | Executable fixtures and exact verifier output | NOT RUN |
| KAT-17c TG13–TG23, TP1–TP5 | Executable CONFIG tests and exact output | NOT RUN |
| Stage A target rehearsal | Real target, test journal/namespace, independent readback, report | NOT RUN |
| Stage B formal E2E | Frozen implementation, actual CONFIG, journal event, raw evidence | NOT RUN |
| Independent review | Reviewer identity and result against exact hashes | NOT PRESENT |

D25 remains **OPEN / NOT PASSED**. Synthetic tests cannot close the two real-target exercises.

## 6. Owner decisions required before lock

1. Must Stage A use the eventual writer, or may it use a disposable probe? If a probe is allowed, which operations must be behaviorally identical to B.7(7), and is its source-tree hash mandatory?
2. Which Stage A contract fields must match final CONFIG exactly, and which may be test-tenant/test-namespace values?
3. Which Stage A evidence may be reused in Stage B? Conservative recommendation: Stage A proves target capability only; Stage B repeats every required check with frozen code and actual CONFIG.
4. Which changes invalidate Stage A and require a new rehearsal? The proposed list is in section 4.

No answer is inferred or adopted here. The canonical r7 spec-path decision also remains open.

## 7. Scope

- No r7 protocol text was changed.
- No target was selected or contacted.
- No external anchor request was made.
- No credentials, collector, live feed, T0, or market scoring were used.
- This is a source review and evidence-design note, not an independent external code review.
- r7 remains **DRAFT / NOT LOCKED**.
