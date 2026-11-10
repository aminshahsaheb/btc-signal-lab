# G-1 — CANDLE provenance: contract amendment PROPOSAL (r6 text), 2026-11-08

STATUS: **PROPOSAL. Not adopted, not locked, not integrated into any verifier or the builder.** On 2026-11-10 GPT's decisions on A, A2, A3 and B (and on the forceOrder `st` rule) were relayed by the owner and are recorded in section 8 as the working basis; they are not yet in any contract text or code. Written by Claude from GPT's audit of 2026-11-07, section A. Everything marked **[VERIFY]** follows public documentation or a third-party client and has NOT been checked against a real captured frame (the exchange is unreachable from the owner's location; the collector host is undecided). Everything marked **[DECISION]** needs GPT and/or the owner before any code is changed. Nothing here is a research result, and nothing self-certifies anything: the tests are synthetic and the reference checker was written and tested by the same author.

Base: `JOURNAL_CONTRACT_v2.md`, revision r5 (PR #32). Sections are numbered as proposed additions/replacements to that text.

## 0. The problem (unchanged from the audit)
In r4/r5 a CANDLE event carries `open_time_ms`, `open`, `recv_ms`, `raw_b64`, `sha256`. The raw bytes are hashed (2.2) but never parsed: `open` and `open_time_ms` are free fields, no connection is named, nothing says the frame was a live 1-minute BTCUSDT kline. An OUTCOME is linked to prices only through those free fields (6.1d `OUTCOME_UNLINKED`).

## 1. [DECISION A — blocks everything else] Feed separation. Recording kline frames as MSG breaks the SLOT replay
GPT's proposal: every raw message is first recorded as `MSG`; the CANDLE points to its MSG with `msg_seq`. Under the **current** replay (section 7) this has two consequences, reproduced by `src/demo_topology_conflict.py` (synthetic frames, asserted):

| case | result |
|---|---|
| force-feed MSGs only (6 BUY frames in the window) | slot VALID |
| the same plus 16 kline frames recorded as MSG on their own connection | **NONE, reason MALFORMED, 15 voids** — a kline frame has `e`/`E` but no `o`, so `classify()` returns MALFORMED (`missing_o`), and 7.5d counts malformed messages on ANY connection |
| kline connection has the smaller connection id | **kline connection becomes `primary_conn`** (7.5b: smallest healthy id); all forceOrder frames are NON_PRIMARY; slot NONE (N_TOTAL) |
| kline connection filtered out of the replay by a feed marker | slot VALID again |

So the two feeds cannot share the replay inputs. Proposal A (Claude's recommendation):
- `CONN` gets a required field `feed`, `"FORCE"` or `"KLINE"` (a missing or other value is `BAD_EVENT`). The feed of a connection is the `feed` of its FIRST `open` event (same convention as `open_ms` in 7.2).
- Section 7.2 changes: the replay uses only the `CONN`, `PING` and `MSG` events of connections whose feed is `FORCE`; `n_messages`, the ledger, health, `primary_conn` and `malformed_voids` are computed over those alone. Events of `KLINE` connections are never replay inputs. A MSG whose connection has no `open` event is replay input as today (it stays NON_PRIMARY/MALFORMED by the existing rules).
- No other change to sections 1–6 events: `MSG` is unchanged.

Alternatives for GPT to weigh: (K) a new event type `KMSG` for kline frames — the replay never sees it, but a `CONN` feed marker is still needed because connection health is per connection; (C) no MSG for kline: the CANDLE carries `conn_id` itself plus the `feed` marker — simplest, but loses the exact-equality link GPT asked for. Journals do not exist yet (pre-T0), so a format change costs no migration; the genesis string and the version name are an open question (**[DECISION A2]**: keep `DLIQ-JOURNAL-v2-GENESIS`, or bump because a required field is added to two event types).

Also **[DECISION A3]**: the message contract's `classify()` expects the UNWRAPPED forceOrder frame (`{"e":"forceOrder",...}`). A combined-stream connection (`/stream?streams=...`) wraps every frame in `{"stream":..., "data":...}`. If one connection ever carried both feeds, every forceOrder frame would be MALFORMED. The proposal therefore assumes **two connections**, one per feed, and the kline connection may use either form (3.2 accepts both).

## 2. Event changes (proposal)
2.1 additions: `CONN`: `feed` (string, see 1). `CANDLE`: `msg_seq` (int, not boolean). A CANDLE without a valid `msg_seq` is `BAD_EVENT` and is then excluded from every check (as 2.1 says); the reference checker is nevertheless defensive and reports `CANDLE_LINK` for such an event if it is handed one.
Verifier/builder consequences are listed in section 6 of this document, not implemented here.

## 3. CANDLE rules (what `src/dliq_kline_v1.py` implements and tests)

### 3.1 Link to the recorded MSG — hard finding `CANDLE_LINK` (where = CANDLE line, at most one per record)
For every valid CANDLE at line c with `msg_seq = m`: `CANDLE_LINK` if any of
- the event at line `m` is not a valid MSG, or `m >= c`;
- the CANDLE's `raw_b64` or `sha256` differs from the MSG's;
- the CANDLE's `recv_ms` differs from the MSG's `recv_ms`;
- the MSG's connection has no `open` event before line `m`; or its feed is not `KLINE`; or the MSG was not received while the connection was open (`open_ms <= recv_ms` and, if a `close` event exists, `recv_ms <= close_ms` of the LAST close event).

### 3.2 Frame grammar — shared parser `parse_kline_frame(raw)`; failure ⇒ hard `CANDLE_PARSE` (where = CANDLE line)
The decoded `raw_b64` MUST be, in order: valid UTF-8; JSON without duplicate keys (any depth) and without NaN/Infinity; an object (a JSON **array** is a REST response ⇒ `rest_array`; REST backfill is forbidden); either **raw form** or **combined form** (`{"stream": "btcusdt@kline_1m", "data": {...}}` with exactly those two keys; the stream name must equal the subscription exactly). In the message: `e == "kline"` (not `continuous_kline`); `E` an integer in `[1.7e12, 4.1e12]`; outer `s == "BTCUSDT"`; `k` an object with `k.s == "BTCUSDT"`, `k.i == "1m"`, `k.t` an integer multiple of 60000, `k.T == k.t + 59999`, `k.o` a decimal string (the contract's `dec` grammar, length ≤ 30, not zero), `k.x` a boolean. Field names and the documented example **[VERIFY]** against a real capture; the combined-stream wrapper and the USD-M plain `kline` (not `continuousKline`) shape are assumptions until then.
Declared fields: `open_time_ms == k.t` and `open == k.o` (string equality). Otherwise hard `CANDLE_FIELD_MISMATCH` (not reported when the frame failed to parse).

### 3.3 Reference CANDLE and conflicts
The first CANDLE (by line) with a declared `open_time_ms` is the **reference** for that minute; later records never replace it. If the reference record has any defect (3.1, 3.2, hard `CANDLE_NOT_LIVE`) or is unusable (3.4), that minute is unusable and no later record rescues it. `CANDLE_CONFLICT` (hard, once per minute, where = the first later record whose declared `open` differs) is unchanged. Later records are only checked for the hard integrity findings; the closing message of a minute (arrives after `T`) is therefore normal and creates no finding.

### 3.4 Time rules — clock-corrected, with the uncertainty bound U = 250 ms
`off` = `offset_ms` of the last CLOCK event before the CANDLE line (0 if none), the sign convention being local − exchange **[VERIFY: the CLOCK event does not define it today]**; `U` = 250 (the contract's `max_clock_offset_ms`). With `r = recv_ms − off`:
- hard `CANDLE_NOT_LIVE`: `r + U < open_time_ms` (certainly received before the candle opened; replaces the old uncorrected `recv_ms < open_time_ms`).
- the reference record makes the minute **unusable** (no finding of its own; reported in `candles`) if, in this order: `|off| > U` → `CLOCK`; not `t <= E <= T` → `E_RANGE`; `r + U > T` → `LATE_MINUTE` (received after the minute may have ended: GPT's rule); `r − E < −U` → `LAG_NEGATIVE`; the maximum lag `L` unset → `LAG_UNSET`; `r − E > L` → `LAG_TOO_OLD`; otherwise `USABLE`. A defective reference record gives `DEFECT_<kind>`.
- **`L` is an open parameter ([DECISION B]).** 5000 ms is NOT approved (GPT: no empirical basis; official update speed is 250 ms). The value must be fixed from a real measurement and recorded BEFORE any market result is examined. Until it is, a verifier reports hard `CANDLE_LAG_UNSET` (where 0), the verdict is `INCOMPLETE` (never PASS), and no minute is `USABLE`. GPT also noted the lag rule does not prove the frame was live (a stale frame can be re-sent inside the minute) — it bounds, it does not prove; the link to a recorded MSG on an open connection is the stronger evidence, and TLS plus collector integrity stay inside the trust boundary.

### 3.5 OUTCOME link (replaces the CANDLE part of 6.1d)
For each referenced entry/exit minute: `OUTCOME_UNLINKED` unless the reference CANDLE of that `open_time_ms` is written before the OUTCOME line, its state in `candles` is `USABLE`, and its declared `open` equals the OUTCOME price (string equality). At most two per OUTCOME, as today.

## 4. Findings and result (additions)
Hard: `CANDLE_LINK`, `CANDLE_PARSE`, `CANDLE_FIELD_MISMATCH`, `CANDLE_LAG_UNSET` (where 0; verdict INCOMPLETE like `REPLAY_NOT_RUN`, FAIL if another hard finding). Existing `CANDLE_CONFLICT` and `CANDLE_NOT_LIVE` keep their names, with the new definitions above. `where` = CANDLE line except `CANDLE_LAG_UNSET` (0). The result gains `candles`: dict `open_time_ms → "USABLE" | reason` for reference CANDLEs only. `analysis_eligible` additionally requires that no `CANDLE_LAG_UNSET` is present (it is hard, so this follows from PASS).

## 5. What is NOT claimed
- **Update 2026-11-10:** after this text was written the owner captured 18 real kline frames (6 RAW, 12 COMBINED) with the dry-run tool (`research/d-liq/g1-dryrun-draft/README.md`, PR #37); `parse_kline_frame` accepted all of them unchanged and one closing message (`x = true`, `E` after `T`) was seen. That confirms the `[VERIFY]` field names, the key set of the COMBINED wrapper and the `k.T = k.t + 59999` rule for these 18 frames only. No kline frame was recorded as a MSG in a journal, and every statement below about lag, clock and liveness stays unverified: the owner's laptop clock was about 4.2 s behind the exchange, so those frames say nothing about latency.
- Before that update, nothing here had been checked against a real frame; field names and the stream shape were documentation-level assumptions.
- The reference checker (`candle_checks`) and its tests have a single author; it is the shared-parser design GPT approved, so the two verifiers would share this parser and only the link/time logic could be written twice.
- No claim about network latency, the value of `L`, or that the lag rule proves liveness.
- No collector, T0, probe, live or edge claim.

## 6. Integration plan after GPT's decisions (not done)
(1) Decide A/A2/A3 and B. (2) Contract text r6 (sections 2.1, 3.x above; 7.2 feed filter; 8.1/8.2/8.4 tables). (3) Primary verifier: import the shared parser; add the CANDLE rules; feed filter in the replay. (4) Independent verifier: implement the link and time rules from the contract text, sharing only the parser. (5) Builder: pin the parser, require `candles` consistency, refuse on `CANDLE_LAG_UNSET`. (6) Differential harness operators for each new rule; mutants; rebuild patches (G-3 style). (7) A real Kline capture on a host that can reach the exchange, to replace every `[VERIFY]`.

## 7. Questions for GPT
1. Decision A: Proposal A (CONN.feed + replay filter), K (KMSG) or C (CANDLE.conn_id only)? A2: bump the genesis/version?
2. A3: confirm two separate connections (one per feed).
3. With feed separation (A), is the `msg_seq` link to a MSG still wanted, or is a `conn_id` on the CANDLE (C) enough? The link gives exact raw-byte equality but doubles the stored bytes.
4. Time rules: is U = 250 ms (the message contract's clock bound) the right uncertainty, and is rejecting a reference record whose receipt is within U of the minute end acceptable?
5. Is `E_RANGE` (`t <= E <= T` for the reference record) too strict (could a legitimate first message carry an `E` slightly outside)? **[VERIFY]**
6. Should `CANDLE_LAG_UNSET` be hard (INCOMPLETE) or a parameter the builder checks?
7. `x` is required to be boolean but otherwise unused — keep as a type check only?

## 8. Decisions of 2026-11-10 (GPT's audit of the real-wire dry run, relayed by the owner)
STATUS: **recorded as the working basis. NOT yet written into the contract text, NOT implemented in any verifier, builder or test, NOT locked.** Source: GPT's message to the owner of 2026-11-10 after the owner's real-wire dry run (PR #37, Draft, unreviewed); the owner relayed it to Claude at 06:39 Tehran time. Below are GPT's decisions with its stated rationale; lines marked **[Claude]** are my own notes and questions, not GPT's. The contract wording, tests and code are separate, reviewable steps (8.9).

8.1 **Decision A - feed separation: adopt Proposal A.** `CONN.feed` is required, `FORCE` or `KLINE`; the replay uses `FORCE` connections only, so kline frames never affect `primary_conn`, the message count, health or any slot. **Keep `CANDLE.msg_seq`**: it links the CANDLE to the raw MSG and allows byte and hash equality; a `conn_id` alone does not give that guarantee.
8.2 **Decision A2 - genesis and version: bump to v3.** `DLIQ-JOURNAL-v3-GENESIS`; schema version and manifests must agree. Rationale: the required structure of `CONN` and `CANDLE` changes, and no real journal exists yet, so there is nothing to stay compatible with. The v2 genesis is not reused.
8.3 **Decision A3 - two separate connections** (BTCUSDT `forceOrder` only; BTCUSDT `kline_1m` only). The combined stream is not used for the primary `forceOrder` path. Rationale: the two message formats differ, the COMBINED wrapper can break the `forceOrder` parser, separate connections make the origin of every message clear, and the replay can check each feed independently.
8.4 **Decision B - `L` stays unset and 5000 ms is not approved.** The dry run cannot set it (the owner's laptop clock was about 4.2 s off). It needs a clock-verified intended collector host, a recorded clock uncertainty, latency measured on that path and host, and a method registered before any market result is seen. Until then `CANDLE_LAG_UNSET` stays a hard finding, no candle is `USABLE`, and analysis eligibility stays blocked; this must not be weakened to make tests easier.
8.5 **The `st` and `ps` fields.** Remove the current top-level `st` rule from the active single-symbol `forceOrder` classifier; do NOT move it to `o.st`. For the all-market stream `ps` and `st` are diagnostic only. For the BTCUSDT single-symbol contract, an unexpected `ps` or `st` is a structural exception that needs review; the schema is not silently widened. This is to be written into the contract text, not only into code. Rationale: the real all-market frames carry `ps` and `st` INSIDE `o`, while the contract reads `st` at the top level, so the rule never fires; `st` marks the market type in the all-market stream, which the study does not use; seeing the fields in 8 all-market frames does not show that the single-symbol stream has them.
   **[Claude]** Open wording question: I read "structural exception" as `classify()` returning MALFORMED with a new reason (for example `unexpected_ps_st`), which voids the slot under 7.5d; GPT to confirm that voiding is intended. No real single-symbol frame has been seen yet, so this rule rests on documentation (a small-model summary of the official page, `[VERIFY]`).
8.6 **All-market scope.** `/market/ws/!forceOrder@arr` is outside the D-LIQ research scope: its messages are not BTCUSDT evidence, are never relabelled, and never enter the research journal. **[Claude]** The check that relabelled the symbol in a COPY of 8 frames was only a grammar exercise and is not evidence about BTCUSDT.
8.7 **A real BTCUSDT frame is required before any lock.** At least one genuine `forceOrder` frame from `/market/ws/btcusdt@forceOrder` is needed to verify the message contract; the post-lock operational probe cannot replace it (the probe measures stability, latency, clock, hang-ups and host adequacy, not the schema). A quiet 51-53 s connection is not evidence that the route is broken: repeat the format-only capture with a longer bounded window. Keep the raw bytes, receive time, HTTP 101 and hash; examine the frame unchanged and without renaming the symbol; an independent check confirms the structure and the parser result. One frame is not sufficient for a lock: a real anchor, the host, the replay, missingness and independent review remain open (checklist C10). **[Claude]** PR #37 version 4 adds a bounded watch mode (reconnects after each hang-up) for this capture; it was not run when this section was written.
8.8 **Still open.** `U = 250 ms`, `E_RANGE` and the other time semantics until they are reviewed and tested; the meaning of `k.x` must be explicit and testable (**[Claude]** observed once: `x = true` in the closing message of a minute with `E` = `T` + 596 ms, `false` in the 17 other kline frames; the parser only type-checks it, so whether the contract should require any relation is a question for GPT); integration of G-1 into the primary verifier, the independent verifier and the builder; independent review of PR #37 and of this record; a real anchor and an end-to-end run.
8.9 **Order of work, each a separate reviewable pull request to `main` (no stacking):** (1) reconcile PR #37's status text with the 2026-11-09 runs and keep the raw captures outside Git unless the owner approves otherwise; (2) capture a real BTCUSDT `forceOrder` frame; (3) contract revision r6 text (A, A2, A3, `st` and `ps`, all-market scope); (4) tests; (5) primary verifier; (6) independent verifier; (7) builder integration; (8) differential and mutation tests; (9) independent review, CI on the exact commit, the other gates, then a separate lock decision. No item counts as complete without the exact commit SHA, passing CI on that SHA and the required review evidence. No lock, no T0, no permanent collector, no price scoring and no edge evaluation in the meantime.
