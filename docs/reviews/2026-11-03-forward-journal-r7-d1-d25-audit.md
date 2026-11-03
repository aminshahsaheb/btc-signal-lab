# Forward Journal r7 — D1–D25 evidence audit

Audit date: 2026-11-03  
Repository snapshot: `main` at `da64085fe1c066026a6bee219b600d2b42f280f6`  
Specification: `research/forward-journal/FORWARD_JOURNAL_SPEC_v1_r7_DRAFT.md`  
Specification SHA-256 is not recomputed in this audit; Git blob identity: `ffacc1c7d4c329b787be222937d2ae9c9d943245`.

## Executive finding

**Disposition: SPEC ONLY / NOT LOCKED / NO T0.**

The repository contains the r7 specification and its r5/r6 archives. The recursive main tree contains no separate Forward Journal writer, collector, auditor, verifier, metrics implementation, runnable r7 KAT harness, or r7 KAT execution report. KAT-1 through KAT-17c are described in the specification as fixtures and expected answers; their presence in prose is not evidence that executable implementations pass them.

The D1–D25 checklist in section D of the specification is still unchecked. This audit does not mark any gate as passed. The purpose is to make the evidence gap explicit and to define the correct implementation order.

## Repository findings

1. The same r7 specification appears at two paths:
   - `research/forward-journal/FORWARD_JOURNAL_SPEC_v1_r7_DRAFT.md` — 178,034 characters.
   - `specs/forward-journal/FORWARD_JOURNAL_SPEC_v1_r7_DRAFT.md` — 178,035 characters.
   The content is identical after removing trailing whitespace. The second copy has one extra final newline. This is a byte-level mismatch, not a semantic difference. Do not silently choose one as authoritative; declare one canonical path and synchronize or remove the duplicate in a separate reviewed change.
2. The only other files under the Forward Journal directories are archived r5/r6 specifications. No KAT source or run artifacts are present in the recursive main tree.
3. Issue #8 records the same starting state: r7 is SPEC ONLY; D25 is open; D1–D24 are requirements, not proof of execution.
4. D-LIQ r3.1 is a separate candidate. Its synthetic journal tests do not implement or validate the Forward Journal r7 collector, two-namespace target contract, or D25.
5. The current repository policy requires exact commands, environment, outputs, hashes, and exact commit evidence. A test result from another SHA does not close a gate.

## D1–D25 evidence map

Status terms:
- **NOT RUN** — no execution evidence was found in the repository snapshot.
- **EXTERNAL BLOCKER** — requires a real external service, live operational exercise, or independent party; a synthetic fixture cannot satisfy it.
- **POLICY ONLY** — a constraint is stated in the specification or repository policy, but no implementation/runtime evidence proves enforcement.

| Gate | Required evidence (short form) | Audit status | Evidence gap |
|---|---|---|---|
| D1 | Frozen spec hash matches GENESIS; GENESIS precedes collector start | NOT RUN | No locked spec package, writer, or journal. |
| D2 | Frozen model implementation; tree hash before CONFIG; exact A.2–A.6 | NOT RUN | No model implementation or code-tree hash run. |
| D3 | KAT-1/2/3 numeric and operation-order results | NOT RUN | Expected answers exist in spec; no executable KAT run. |
| D4 | KAT-4 canonical serialization and byte-exact hash chain | NOT RUN | No writer/verifier implementation or byte comparison log. |
| D5 | Ten tamper classes plus KAT-10b/10c and KAT-15 negatives | NOT RUN | No verifier or tamper harness. |
| D6 | Decision/outcome/adjudication lifecycle, conflicts, finalizer failures | NOT RUN | No journal lifecycle implementation or KAT-6/9 run. |
| D7 | Reject-code priority and p_raw invariants | NOT RUN | No decision/collector implementation or invariant tests. |
| D8 | Offline collector validation of KAT-8, malformed messages, duplicates, gaps, restart | NOT RUN | No collector or executable KAT-8 harness. |
| D9 | Outcome timing, unresolved windows, duplicate outcome rejection | NOT RUN | No outcome finalizer or lifecycle tests. |
| D10 | Alert thresholds excluded from model config and separately hashed | NOT RUN | No configuration implementation or negative test. |
| D11 | Separate human journal; no write path into primary journal except human_head_hash | NOT RUN | No journal implementations or access-control test. |
| D12 | KAT-5/7 metrics and bootstrap; deterministic full hourly grid | NOT RUN | No metrics/bootstrap code or pinned NumPy environment. |
| D13 | Complete CONFIG; independent target; both namespaces; D25 E2E | EXTERNAL BLOCKER | No selected target, independent operator/read client, or real E2E. |
| D14 | Spec lock, collector start, 288 real-time candles, real connection rotation | EXTERNAL BLOCKER | No collector, warm-up, or observed rotation. |
| D15 | T0 declaration after full rotation and before T0 | EXTERNAL BLOCKER | T0 is prohibited until prior gates pass; no declaration. |
| D16 | No parity test on burned historical files; KAT-only parity | POLICY ONLY | Policy is recorded; no live implementation exists to verify compliance. |
| D17 | Burned-data statement in every future report | POLICY ONLY | Rule exists; no forward report exists to inspect. |
| D18 | Gate, benchmark, and analysis hashes registered before p–Y inspection | NOT RUN | No registration events or official analysis manifest. |
| D19 | Exact Binance endpoint, status 101 handshake, real kline validation, reject alternate URLs | EXTERNAL BLOCKER | No endpoint handshake or collector evidence. |
| D20 | Clock KAT-11/11b/11c, journal-level clock evidence, KAT-16 raw witness | NOT RUN | No clock implementation, collector, verifier, or KAT run. |
| D21 | As-of-S prefix, target-time ordering, manifest and negative tests | NOT RUN | No anchor reader, manifest publisher, analysis implementation, or KAT-12 run. |
| D22 | Connection rotation, reconnect/backoff, boundary, standby, no REST/backfill | EXTERNAL BLOCKER | No collector or real rotation/warm-up evidence. |
| D23 | Exact freeze → build/test → code hash → CONFIG → anchor tests → warm-up → T0 | NOT RUN | No implementation or ordered run record. |
| D24 | Total verifier behavior; KAT-15a/b/c, 16, 10c without exceptions | NOT RUN | No verifier or malformed-input run. |
| D25 | KAT-17/17c plus real two-namespace target exercise and independent readback | EXTERNAL BLOCKER | No selected target, two-namespace exercise, receipts, independent readback, or report. |

## Important interpretation of D25

The specification explicitly says that the seven `checks` booleans in `EVENT(CHECKPOINT_E2E_TEST)` are written by the writer. The verifier checks their consistency with records held by the destination, but cannot prove from those booleans alone that the independent readback, timestamp verification, duplicate-sequence rejection, and truncation exercise actually occurred.

Therefore, the D25 evidence package must preserve independent evidence from the destination and the read client. At minimum, retain:
- destination-issued records from both `checkpoints` and `manifests` namespaces;
- raw request and response records, including rejection of the duplicate/old sequence;
- independent read-client identity and readback output;
- receipt and timestamp verification output, including the trust class and uncertainty;
- hash of the truncated journal copy and the verifier report showing `TRUNCATED`;
- a signed or otherwise independently attributable test report tied to the exact code tree and CONFIG.

This is an evidence recommendation. It does not change the r7 protocol or claim that the listed material is already available.

## Correct implementation order

1. **Freeze the source contract:** designate one canonical r7 specification path; compare all normative text and record the exact SHA-256. Keep the duplicate-path repair separate from implementation.
2. **Build the offline reference core:** canonical JSON, strict time parser, journal writer, hash-chain verifier, checkpoint/manifest verifier, and model/metrics functions. Pin the runtime and dependencies.
3. **Build an executable KAT suite:** transcribe every KAT into machine-readable fixtures without changing expected answers. Include positive and negative tests. A fixture is not a pass until the exact executable reports the expected result.
4. **Map D1–D12 and D16–D18, D20–D21, D23–D24** to exact tests, commands, output hashes, and a clean-checkout run. Add mutation/fuzz tests around parser and verifier boundaries.
5. **Independent code review:** a reviewer who did not write the implementation checks the spec-to-code mapping, fixture transcription, tamper coverage, and failure behavior.
6. **External target selection and D13/D25:** select an append-only, independently operated target with two namespaces, destination-controlled time and receipts, strict sequence acceptance, and independent readback. Verify terms, API semantics, identity, retention, and timestamp trust. Then run the complete E2E exercise.
7. **Only after all prior gates:** verify endpoint and clock, run collector warm-up and real connection rotation, satisfy D14, and review D15/T0 ordering. T0 remains blocked until a separate lock decision.

## Non-goals and safety holds

- No live Binance connection was opened.
- No external anchor request was made.
- No collector or T0 was started.
- No historical or forward market outcomes were scored.
- No model parameters were changed.
- No strategy or profitability claim is made.
- r7 remains DRAFT / NOT LOCKED.

## Acceptance standard for closing this audit

Do not close a D-gate based on prose, a mock target, a self-reported boolean, or a green test on a different commit. Each closure must name the exact code commit, exact spec hash, command, environment, raw output artifact, output hash, and reviewer. External gates must also include independently sourced evidence.
