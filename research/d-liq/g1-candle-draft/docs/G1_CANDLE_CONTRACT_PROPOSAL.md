# G-1 — CANDLE provenance: contract amendment PROPOSAL (r6 text), 2026-11-08

STATUS: **PROPOSAL. Not adopted, not locked, not integrated into any verifier or the builder.** Written by Claude from GPT's audit of 2026-11-07, section A. Everything marked **[VERIFY]** follows public documentation or a third-party client and has NOT been checked against a real captured frame (the exchange is unreachable from the owner's location; the collector host is undecided). Everything marked **[DECISION]** needs GPT and/or the owner before any code is changed. Nothing here is a research result, and nothing self-certifies anything: the tests are synthetic and the reference checker was written and tested by the same author.

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
- Nothing here was checked against a real frame; field names and the stream shape are documentation-level assumptions.
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
