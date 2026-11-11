# D-LIQ evidence journal -- contract v3, revision r6-draft (verifier-facing; supersedes the r5 text; DRAFT, not locked)

REVISION r4 (answer to GPT's r3 audit, orders 1-4): adds 6.1e (`OUTCOME_FOR_NONE_SLOT`, from the r3-reconstruction amendment), 6.4 (every reference OUTCOME is COVERED by a later valid checkpoint or UNCOVERED; the verifier reports `outcomes`),
makes the SLOT replay of section 7 MANDATORY for the analysis pipeline, and adds the hard finding `SLOT_EARLY_WRITE`. The event format and the genesis string are unchanged.

REVISION r5 (answer to the second GPT audit, 2026-11-07, point B / G-2): the SLOT replay can no longer be skipped silently. New section 7.6; new hard finding `REPLAY_NOT_RUN`; new verdict `INCOMPLETE`;
every report carries `replayed` and `analysis_eligible`. Sections 1-6, the event format and the genesis string are unchanged.

REVISION r6 (first contract-text draft of GPT's decisions of 2026-11-10 and 2026-11-11, recorded as a working basis in `research/d-liq/g1-candle-draft/docs/G1_CANDLE_CONTRACT_PROPOSAL.md` sections 8 to 12; NOTHING in this text is implemented, tested or reviewed yet). Changes against r5, each with its decision letter:
- A2: the journal format and the genesis string become v3 (3.2, 3.3). No v2 journal exists, so there is nothing to stay compatible with.
- A: `CONN` has a required `feed` ("FORCE" or "KLINE"); the replay of section 7 uses only FORCE connections (2.3, 7.2); `CANDLE` has a required `msg_seq` (2.1, 6.5).
- A3: the FORCE feed and the KLINE feed are two separate connections; a FORCE connection carries unwrapped forceOrder frames only (2.3d, 7.5a).
- B: CANDLE provenance rules (6.5-6.9) with the maximum receipt lag `L` UNSET: the hard finding `CANDLE_LAG_UNSET`, a verdict that is never PASS (6.8).
- `o.ps` and `o.st` are known OPTIONAL fields of a forceOrder frame; a top-level `st` is forbidden; the r5 rule `st_not_1` is removed (7.5a).
- A run-level pass over EVERY FORCE message, independent of any SLOT (7.7); new hard findings `FORCE_MSG_STRUCTURE`, `MSG_CONN_UNKNOWN`, `CONN_FEED_CONFLICT`; new soft finding `FORCE_UNKNOWN_KEY` (8.1). New 8.5 (no override, re-verification) and a new section 10 (minimum conformance cases for the test step).
Marks used below: **[OPEN]** = not decided (`U = 250 ms`, `E_RANGE`, the meaning of `k.x`); **[C]** = a detail chosen by the author of this text that GPT has not decided, GPT is asked to confirm each; **[VERIFY]** = not checked against real data. Sections 1, 4 and 5 are unchanged.

STATUS: DRAFT, not locked. This text is the specification a verifier is written from. Where this text is silent or ambiguous the implementer MUST NOT guess silently:
write each question into a file `QUESTIONS.md` next to the code and implement the most conservative reading (the one that reports more hard findings).
Words MUST / MUST NOT / MAY have their RFC 2119 meaning. All integers are Python-style integers; "ms" = milliseconds since the Unix epoch (UTC).

## 1. File format
1.1 A journal is a file of lines separated by the byte `0x0A`. A non-empty file MUST end with `0x0A`. An empty file is a valid journal with zero events.
1.2 Each complete line is the UTF-8 (in fact ASCII) bytes of one JSON object. The line bytes WITHOUT the final `0x0A` are called `line_n` (n = 1-based line number).
1.3 Parsing rules for a line: it MUST decode as strict UTF-8, MUST parse as JSON, MUST be a JSON object, MUST NOT contain duplicate keys at any nesting level,
    MUST NOT contain the constants NaN / Infinity / -Infinity, and MUST NOT contain any number token with a fraction or exponent (any token containing `.`, `e` or `E`)
    -- all numbers are plain integers. A line that violates this is `BAD_ENCODING` at that line number and **parsing of the file stops there** (later lines are
    not authenticated and are ignored for every other check). If the file is non-empty and does not end with `0x0A`, the final partial line is discarded and
    one `BAD_ENCODING` is reported at line number (number of `0x0A` bytes + 1).
1.4 Canonical form: for a parsed line `ev`, `canon(ev)` = the ASCII bytes of `json.dumps(ev, sort_keys=True, separators=(",", ":"), ensure_ascii=True, allow_nan=False)`.
    If `canon(ev) != line_n` the line is `NOT_CANONICAL` (one finding per such line). The line is still used as parsed (its stored bytes enter the hash chain).

## 2. Events
2.1 Every event MUST have `t` (string), `seq` (integer, not boolean), `rec_ms` (integer, not boolean). `t` MUST be one of
    SESSION, CONN, PING, MSG, CLOCK, CANDLE, SLOT, OUTCOME, CHECKPOINT. Per-type required fields (type in parentheses; `dec` = string matching `^(0|[1-9][0-9]*)(\.[0-9]+)?$`):
- CONN: conn_id (int), ev ("open" or "close"), ms (int), feed ("FORCE" or "KLINE")  [r6, A; `feed` is required on EVERY CONN event [C]]
- PING: conn_id (int), ms (int)
- MSG: conn_id (int), recv_ms (int), raw_b64 (string), sha256 (string)
- CLOCK: offset_ms (int), ms (int)
- CANDLE: open_time_ms (int), open (dec), recv_ms (int), raw_b64 (string), sha256 (string), msg_seq (int, not boolean)  [r6, A]
- SLOT: tau_ms (int), status ("VALID" or "NONE"), reasons (list of strings), primary_conn (int or null), N_total, N_BUY, N_SELL, side, malformed_voids, n_messages (int), sumW_BUY, sumW_SELL (dec), X_sn (string or null), ledger (object whose values are ints)
- OUTCOME: tau_ms (int), status ("EVAL" or "NO_PRICE"); if status is "EVAL" also entry_open_ms, exit_open_ms (int), entry_price, exit_price (dec), r_bps (string)
- CHECKPOINT: anchored_seq (int), anchored_head (string), receipt (object) with anchor_id (string), index (int), seq (int), head (string), time_ms (int), time_resolution_ms (int), time_uncertainty_ms (int)
- SESSION: no required fields.
A field listed as "(int or null)" or "(string or null)" is still REQUIRED to be present as a key; a missing key is `BAD_EVENT`, JSON `null` is accepted.
A parsed line violating 2.1 (unknown `t`, missing or mistyped field) is `BAD_EVENT` at that line; such an event takes part in the hash chain and in 3 (SEQ_GAP) but is EXCLUDED from every check in 4-8.
Extra fields beyond those listed are allowed and ignored (except as stated in 5.2).
2.2 `raw_b64` MUST be valid standard base64; the SHA-256 (lowercase hex) of the decoded bytes MUST equal `sha256` for MSG and CANDLE events, else `RAW_HASH_MISMATCH`
    (invalid base64 is also `RAW_HASH_MISMATCH`).
2.3 Feed of a connection (r6, decision A; GPT 2026-11-11, point A). Every connection has ONE fixed feed.
  a. The feed of a connection id is the `feed` of its FIRST valid `open` CONN event (the same convention as `open_ms` in 7.2). A connection id with no valid `open` event has no feed.
  b. `CONN_FEED_CONFLICT` (hard, `where` = the CONN line): every valid CONN event (open or close) of a connection id that has a feed, whose `feed` differs from that feed. One finding per such event.
  c. `MSG_CONN_UNKNOWN` (hard, `where` = the MSG line): every valid MSG whose `conn_id` has no valid `open` event at a line BEFORE the MSG. One finding per such MSG. A MSG that has no feed is treated as a FORCE message by 7.2 and 7.7 [C: the conservative reading; the journal fails anyway].
  d. Decision A3: the two feeds are two separate connections, and no combined stream is used on the FORCE path. A FORCE connection carries only unwrapped `forceOrder` frames, a KLINE connection only kline frames. The journal does not record the URL, so this contract checks only what the bytes show: a wrapped or otherwise non-forceOrder frame on a FORCE connection is MALFORMED (7.5a) and voids the slots it falls in (7.5d); a frame on a KLINE connection is never a replay input (7.2) and is judged only through the CANDLE rules (6.5-6.9) [C: a KLINE frame that no CANDLE refers to is not checked].

## 3. Sequence and chain
3.1 The event at line n MUST have `seq == n`. The first line n where this fails gets ONE finding `SEQ_GAP` (later mismatches are not reported separately).
3.2 `GENESIS = b"DLIQ-JOURNAL-v3-GENESIS"` (r6, A2; r5: `DLIQ-JOURNAL-v2-GENESIS`). `h_0 = SHA-256(GENESIS)` (32 raw bytes). `h_n = SHA-256(h_{n-1} + line_n)` (raw bytes concatenation, line_n WITHOUT the newline),
    computed over every parsed line in file order (including BAD_EVENT / NOT_CANONICAL lines). `head_hex` of the result is the lowercase hex of `h_N`, N = number of parsed lines.
3.3 (r6, A2) A journal written under the v2 genesis is not a valid v3 journal: its hash chain differs from the one 3.2 computes, so it fails with `HEAD_MISMATCH` at its first checkpoint. No v2 journal exists (pre-T0). The schema, the manifests and the names of every package that implements this contract MUST say v3.

## 4. Checkpoints and the anchor
4.1 The verifier is given an `anchor` object with `get(journal_id, index) -> dict or None` and `latest(journal_id) -> int`. A dict returned by `get` has at least
    anchor_id, index, seq, head, time_ms, time_resolution_ms, time_uncertainty_ms. `journal_id` is supplied by the caller.
4.2 Walk the CHECKPOINT events (valid per 2.1) in file order. Let `prev_k` = 0 and `prev_index` = 0 initially. For the checkpoint at line i with `k = anchored_seq`, `idx = receipt.index`:
  a. `CHECKPOINT_ORDER` if NOT (0 < k < i) or `k <= prev_k` or `idx != prev_index + 1`. After the checks set `prev_k = max(prev_k, k)` and `prev_index = idx`.
  b. `HEAD_MISMATCH` if `0 < k <= N` and `hex(h_k) != anchored_head`.
  c. `RECEIPT_INVALID` if any of: `anchor.get(journal_id, idx)` is None; the returned entry `e` has `e.head != anchored_head`, or `e.seq != k`, or `e.time_ms != receipt.time_ms`,
     or `e.time_resolution_ms != receipt.time_resolution_ms`, or `e.time_uncertainty_ms != receipt.time_uncertainty_ms`, or `e.anchor_id != receipt.anchor_id`;
     or `receipt.head != anchored_head`, or `receipt.seq != k`; or `receipt.time_resolution_ms < 1` or `receipt.time_uncertainty_ms < 0`.
4.3 Let `M` = number of valid CHECKPOINT events and `top = anchor.latest(journal_id)`. For every `idx` with `M < idx <= top`: let `e = anchor.get(journal_id, idx)`.
    If `e` exists, `e.seq <= N` and `hex(h_{e.seq}) == e.head`, report informational `ANCHOR_AHEAD_BENIGN`; otherwise report `TRUNCATION_OR_REPLACEMENT`.
4.4 Informational findings: `NO_CHECKPOINT` if M == 0; `TAIL_UNANCHORED` if M > 0 and there is at least one parsed line after the LAST CHECKPOINT line.

## 5. Signals (SLOT) and the anchoring deadline
5.1 Constants: `GRID_MS = 14_400_000` (4 h), `ENTRY_DELAY_MS = 300_000` (5 min), `HORIZON_MS = 14_400_000`.
5.2 For every valid SLOT at line i:
  a. `SLOT_OFF_GRID` (hard) if `tau_ms % GRID_MS != 0`.
  b. `SLOT_HAS_OUTCOME_FIELDS` (hard) if the event has any of the keys entry_open_ms, exit_open_ms, entry_price, exit_price, r_bps, outcome.
  c. `DUPLICATE_SLOT` (hard) for every second and later valid SLOT with the same `tau_ms` (the first one is the reference SLOT for that tau).
5.3 Deadline. For the reference SLOT of a tau at line i, the covering checkpoint is the FIRST valid CHECKPOINT line c (c > i) with `anchored_seq >= i`. If a covering checkpoint exists let
    `anchor_upper_ms = receipt.time_ms + receipt.time_resolution_ms - 1 + receipt.time_uncertainty_ms` (receipt values from the journal's checkpoint event). The slot is `OK` iff
    `anchor_upper_ms < tau_ms + ENTRY_DELAY_MS` (STRICT). Otherwise the slot is reported `SLOT_LATE_ANCHOR` (soft).
    If no covering checkpoint exists: the slot is `SLOT_UNANCHORED` (soft) iff the caller-supplied `verify_time_ms >= tau_ms + ENTRY_DELAY_MS`; otherwise it is pending (no finding).
5.4 Grid completeness: let `tmin`, `tmax` be the smallest and largest `tau_ms` among reference SLOTs that are on the grid. Every grid point `tmin + j*GRID_MS <= tmax` without a SLOT is
    `SLOT_MISSING` (soft), reported once per missing tau.
5.5 Soft findings do NOT make the verdict FAIL. Their consequence, defined in the protocol (not by the verifier), is that such a slot enters the analysis as NONE with reason UNANCHORED
    whatever its recorded status. The verifier reports them in `slots`: a dict `tau_ms -> "OK" | "LATE" | "UNANCHORED" | "PENDING"` for reference SLOTs and a list `missing` of missing taus.

## 6. Outcomes
6.1 For every valid OUTCOME at line j (status as recorded):
  a. `DUPLICATE_OUTCOME` (hard) for every second and later OUTCOME with the same `tau_ms`.
  b. `OUTCOME_ORPHAN` (hard) if no reference SLOT with that `tau_ms` exists at a line before j.
  c. `OUTCOME_BEFORE_ANCHOR` (hard) if the reference SLOT exists but no valid CHECKPOINT line c with `i < c < j` has `anchored_seq >= i` (i = the SLOT line).
  d. For status "EVAL" only:
     - `OUTCOME_TIMING` (hard) if NOT (`entry_open_ms == tau_ms + ENTRY_DELAY_MS` and `exit_open_ms == entry_open_ms + HORIZON_MS`).
     - `OUTCOME_MISMATCH` (hard) if `abs(float(r_bps) - 10000.0 * math.log(float(exit_price) / float(entry_price))) > 1e-6` (also if `r_bps`, a price, or the log argument is not usable: non-numeric r_bps, a price equal to 0).
     - `OUTCOME_UNLINKED` (hard): the entry minute and the exit minute must each be linked to a USABLE reference CANDLE. The rule is 6.9 (r6); it replaces the r5 text, which compared only the free fields `open_time_ms` and `open`.
  e. `OUTCOME_FOR_NONE_SLOT` (hard) if a reference SLOT with that `tau_ms` exists (at any line) and its recorded `status` is not "VALID". A NONE slot cannot become an outcome row, not even NO_PRICE. The journal writer refuses to append such an OUTCOME.
     (An OUTCOME whose reference SLOT lies after it yields OUTCOME_ORPHAN, OUTCOME_BEFORE_ANCHOR and, when that SLOT is not VALID, also OUTCOME_FOR_NONE_SLOT.)
6.2 For every pair of valid CANDLE events with the same `open_time_ms` but different `open`: `CANDLE_CONFLICT` (hard), reported once per open_time_ms.
6.3 `CANDLE_NOT_LIVE` (hard) for every valid CANDLE that was certainly received before its minute opened. The r6 definition (clock-corrected, with an uncertainty bound) is in 6.8 and replaces the r5 text `recv_ms < open_time_ms`.

6.4 Coverage of outcomes (r4; GPT audit P0-1, order 1). For the reference OUTCOME of each tau (the FIRST valid OUTCOME with that `tau_ms` in file order, at line j) the covering checkpoint is the FIRST valid CHECKPOINT
    line c > j with `anchored_seq >= j`. The outcome is `COVERED` if such a checkpoint exists, otherwise `UNCOVERED`. Every UNCOVERED reference OUTCOME (status EVAL or NO_PRICE) yields one soft finding
    `OUTCOME_UNCOVERED` with `where` = `tau_ms`. The verifier reports `outcomes`: a dict `tau_ms -> "COVERED" | "UNCOVERED"` for reference OUTCOMEs only. Later duplicates (DUPLICATE_OUTCOME, hard) are not entered.
    The verifier sets NO deadline on the covering checkpoint (owner decision OPEN-22, 2026-11-05: no hard lag cap; the collector must checkpoint immediately after each OUTCOME, report the lag distribution and write a final drain
    checkpoint; a prolonged anchor outage makes the run INCONCLUSIVE and never silently removes rows). Consequence, implemented by the slots builder and not by the verifier: an UNCOVERED reference OUTCOME MUST NOT enter the analysis;
    the builder reports it PENDING and refuses to write the analysis CSV (owner decision 2026-11-05; it is NOT converted to NO_PRICE). The writer helper `outcome_and_anchor` appends an OUTCOME and the checkpoint that covers it.

6.5 CANDLE link to the recorded MSG (r6, A) -- hard finding `CANDLE_LINK` (`where` = the CANDLE line, at most ONE finding per CANDLE record). For every valid CANDLE at line c with `msg_seq = m`, `CANDLE_LINK` if any of:
  * the event at line m is not a valid MSG, or `m >= c`;
  * the CANDLE's `raw_b64` or `sha256` differs from the MSG's;
  * the CANDLE's `recv_ms` differs from the MSG's `recv_ms`;
  * the MSG's connection has no valid `open` event before line m (2.3), or its feed is not `KLINE`, or the MSG was not received while the connection was open (`open_ms <= recv_ms` and, if a `close` event exists, `recv_ms <= close_ms` of the LAST close event).
6.6 CANDLE frame grammar (r6) -- failure is the hard finding `CANDLE_PARSE` (`where` = the CANDLE line). The kline frame parser `parse_kline_frame(raw)` is the ONE component the two verifiers MAY share (GPT, 2026-11-07); the link rule 6.5 and the rules 6.7-6.9 MUST be implemented separately by each verifier. The decoded `raw_b64` MUST be, in order:
  valid UTF-8; JSON without duplicate keys at any depth and without NaN / Infinity; a JSON object (a JSON array is a REST response; REST backfill is forbidden); either the RAW form or the COMBINED form `{"stream": "btcusdt@kline_1m", "data": {...}}` with exactly those two keys and the stream name equal to the subscription exactly.
  In the message: `e == "kline"` (not `continuous_kline`); `E` an integer in `[1.7e12, 4.1e12]`; the outer `s == "BTCUSDT"`; `k` an object with `k.s == "BTCUSDT"`, `k.i == "1m"`, `k.t` an integer multiple of 60000, `k.T == k.t + 59999`, `k.o` a decimal string (the `dec` grammar of 2.1, length at most 30, not zero), `k.x` a boolean.
  **[OPEN]** the meaning of `k.x`: it is type-checked only, no rule uses its value. Observed on the 18 real kline frames of 2026-11-09 (6 RAW, 12 COMBINED; one machine, one VPN path): these field names, the two-key COMBINED wrapper and `k.T == k.t + 59999`; one closing message (`x = true`) had `E` = `T` + 596 ms. That is evidence of format for those frames only, not a distribution.
  Declared fields: `open_time_ms == k.t` and `open == k.o` (string equality); otherwise the hard finding `CANDLE_FIELD_MISMATCH` (`where` = the CANDLE line; not reported when the frame failed to parse).
6.7 Reference CANDLE and conflicts (r6). The first CANDLE (by line) with a declared `open_time_ms` is the REFERENCE for that minute; later records never replace it. If the reference record has any defect (`CANDLE_LINK`, `CANDLE_PARSE`, `CANDLE_FIELD_MISMATCH`, `CANDLE_NOT_LIVE`) or is unusable (6.8), that minute is unusable and no later record rescues it. `CANDLE_CONFLICT` (6.2, hard, once per minute, `where` = the first later record whose declared `open` differs from the reference's) is unchanged. Later records are only checked for the hard integrity findings; the closing message of a minute (it arrives after `T`) is therefore normal and creates no finding.
6.8 CANDLE time rules (r6) -- clock-corrected, with an uncertainty bound `U`. `off` = `offset_ms` of the last CLOCK event before the CANDLE line (0 if none; the sign convention local minus exchange is assumed **[VERIFY]**: the CLOCK event does not define it today). `U = 250` **[OPEN]** (the message contract's `max_clock_offset_ms`; GPT: stays open until reviewed and tested). With `r = recv_ms - off`:
  * hard `CANDLE_NOT_LIVE` (`where` = the CANDLE line): `r + U < open_time_ms` (certainly received before the candle opened).
  * The reference record makes its minute UNUSABLE (no finding of its own; the state is reported in `candles`, 8.2) if, in this order: `|off| > U` -> `CLOCK`; not `t <= E <= T` -> `E_RANGE` **[OPEN]**; `r + U > T` -> `LATE_MINUTE`; `r - E < -U` -> `LAG_NEGATIVE`; the maximum lag `L` unset -> `LAG_UNSET`; `r - E > L` -> `LAG_TOO_OLD`; otherwise `USABLE`. A reference record with a defect gets `DEFECT_<kind>`, kind in `LINK`, `PARSE`, `FIELD_MISMATCH`, `NOT_LIVE`.
  * Decision B: `L` is UNSET and 5000 ms is NOT approved (GPT, 2026-11-10: no empirical basis). `L` is fixed only from a measurement on the clock-verified intended collector host, with a recorded clock uncertainty, by a method registered before any market result is seen. Until then EVERY verifier reports the hard finding `CANDLE_LAG_UNSET` (`where` = 0) on every journal, no minute is `USABLE`, and the verdict is never PASS (8.2). This MUST NOT be weakened to make tests easier. The lag rule bounds the age of a frame, it does not prove the frame was live; the link to a recorded MSG on an open connection (6.5) is the stronger evidence, and TLS and the collector's integrity stay inside the trust boundary.
6.9 OUTCOME link (r6; replaces the CANDLE part of 6.1d). For each referenced entry / exit minute: `OUTCOME_UNLINKED` unless the reference CANDLE of that `open_time_ms` is written before the OUTCOME line, its state in `candles` is `USABLE`, and its declared `open` equals the OUTCOME price (string equality). At most two findings per OUTCOME (entry, exit), as in 8.4.

## 7. SLOT replay (MANDATORY for the analysis pipeline before T0; r4)
7.1 Requirement (GPT audit P0-3, order 3). The slots builder MUST run the replay of every reference SLOT and MUST refuse to produce an analysis file from a journal whose replay was not run or reported any hard finding.
    A journal that passes sections 1-6 but was not replayed is NOT sufficient evidence for the analysis. The replay implemented in this package is the author's (`verify(..., replay_slots=True)` of the primary verifier,
    using the executable message contract). Before a lock an independent implementation of this section, written from the written specifications only and compared by a differential harness, MUST also exist; it is NOT part of this package.
7.2 Input of the replay of the reference SLOT at line i (tau = its `tau_ms`). Use ONLY the valid (2.1) events at lines `< i`, in file order:
  * every MSG whose connection feed is FORCE, or which has no feed (2.3c): message `{conn_id, recv_ms, raw = base64-decoded raw_b64}`; the frame times of a connection (for the health rule) are the `recv_ms` of its MSG events and the `ms` of its PING events, in file order;
  * (r6, A) NO event of a connection whose feed is KLINE is an input of the replay: its CONN, PING and MSG events are skipped entirely, so they affect no count, no ledger label, no health, no `primary_conn` and no `malformed_voids`;
  * every CONN of a connection whose feed is not KLINE: `open_ms[conn_id]` = the `ms` of the FIRST `open` event of that connection id (later opens of the same id are ignored); `close_ms[conn_id]` = the `ms` of the LAST `close` event (absent if none);
  * every CLOCK: `clock_offset_ms` = `offset_ms` of the LAST CLOCK event (0 if none);
  * the end of the observation horizon of every connection is the `rec_ms` of the SLOT event itself.
  Events at lines `>= i` MUST NOT be used. The message classes, the feature window, the late rule, the void interval, the health rule, the primary-connection rule and the NONE reasons are those of the message contract
  (`dliq_msg_contract_v1.py`, `docs/07_MESSAGE_CONTRACT_v1.md` of the r3 package); the result is the SLOT fields of 7.3.
7.3 Compared fields (the replayed value MUST equal the journalled value; `X_sn` as the string `repr(float)` or null): status, reasons (as a list, same order), primary_conn, N_total, N_BUY, N_SELL, sumW_BUY, sumW_SELL
    (decimal strings, same text), side, malformed_voids, ledger (object), n_messages, X_sn. Any difference: `SLOT_MISMATCH` (hard), `where` = the SLOT line, the detail names the differing fields, sorted, comma separated.
7.4 `SLOT_EARLY_WRITE` (hard, `where` = the SLOT line): a reference SLOT whose `rec_ms < tau_ms + 10_000` (the late rule admits frames with `recv_ms <= tau + 10 s`; a SLOT written earlier could omit admissible frames that
    the journal records after it). Reported only when the replay layer is run; it is reported in addition to a possible SLOT_MISMATCH.
7.5 Derivation of the SLOT fields (normative description of what `dliq_msg_contract_v1.build_slot` / `health_intervals` compute; checked against that code by reading, NOT yet by an independent implementation).
    Let `V = [tau - 960_000, tau + 10_000]` (closed), `W = [tau - 900_000, tau)` (half-open, on the JSON integer `E`), `rec` = the `rec_ms` of the SLOT event.
  a. Message class (MALFORMED / INELIGIBLE / ELIGIBLE) per the message contract (r3 package `docs/07_MESSAGE_CONTRACT_v1.md`, protocol 4.2); not restated here, EXCEPT this r6 change to its structural rules. The r5 rule `st_not_1` (a top-level `st` that is present must equal the integer 1) is REMOVED. In its place, at the same position in the classification order (after the `symbol` check, before the `side` check), a message is MALFORMED for the FIRST of these reasons that applies, checked in this order:
     `st_top_level`: the top-level object has a key `st`, whatever its value; `ps_type`: `o` has a key `ps` and its value is not a JSON string; `ps_ne_s`: `o.ps` is a string different from `o.s`; `st_type`: `o` has a key `st` and its value is not a JSON integer (a boolean, a string, a float with a fraction or an exponent, an object, an array and null are all `st_type`; a boolean is NOT the integer 1); `st_ne_1`: `o.st` is an integer different from 1.
     `o.ps` and `o.st` are KNOWN OPTIONAL fields (GPT, 2026-11-10: one real BTCUSDT frame carries both inside `o`, which does not prove that every future frame does): their absence is not an error, and they are never used for the side, the weight or any other value. Known keys: top level `e`, `E`, `o` (and the forbidden `st`); inside `o`: `s`, `S`, `o`, `f`, `q`, `p`, `ap`, `X`, `l`, `z`, `T`, `ps`, `st`. Every other key, at the top level (including a top-level `ps`) or inside `o`, is kept in the raw bytes, ignored by every calculation, and produces only the soft finding of 7.7c; it never makes a message MALFORMED and never voids a slot (a genuinely new key may be an additive change by the exchange). The required-field, data-type and structure rules of the message contract are unchanged and stay strict.
  b. Health. For every connection `c` that has an `open` event: `stop` = `close_ms[c]` if it has a close event, else `rec`. `pts` = [`open_ms[c]`] + the frame times `t` of `c` (7.2) with `open_ms[c] <= t <= stop`, sorted ascending.
     Split `pts` into maximal runs in which successive points differ by AT MOST 200_000. A run with first point `s` and last point `p` covers the interval `[s, min(p + 200_000, stop)]` (runs with `s > stop` do not exist).
     `c` is healthy iff ONE run covers V completely: `s <= tau - 960_000` and `min(p + 200_000, stop) >= tau + 10_000`. Healthy runs are never stitched across a larger gap. `primary_conn` = the smallest healthy
     connection id, `null` if there is none. A connection without an open event is never a candidate.
  c. Ledger. The seven keys MALFORMED, NO_PRIMARY, NON_PRIMARY, OUT_OF_WINDOW, LATE, INELIGIBLE, COUNTED are ALWAYS present (zero counts included). Each replay input message gets exactly ONE label, by this priority:
     MALFORMED (class MALFORMED); else NO_PRIMARY (`primary_conn` is null); else NON_PRIMARY (its `conn_id` differs from `primary_conn`); else OUT_OF_WINDOW (`E` not in W); else LATE (`recv_ms > tau + 10_000`);
     else INELIGIBLE (class INELIGIBLE); else COUNTED. `n_messages` = the number of replay input messages (every valid MSG event before the SLOT line, 7.2).
  d. `malformed_voids` = the number of MALFORMED messages, on ANY connection, whose `recv_ms` is in V or whose `E` (when a valid `E` could be read) is in V.
  e. COUNTED messages: `N_BUY` / `N_SELL` = the counts by side; `N_total = N_BUY + N_SELL`; `sumW_BUY` / `sumW_SELL` = exact decimal sums of `z * ap` (precision 200 digits), written as `format(Decimal, "f")` (plain, no exponent, no normalisation).
  f. `reasons` (a list, in THIS order, each at most once): "GAP" if `primary_conn` is null; "CLOCK" if `|clock_offset_ms| > 250`; "MALFORMED" if `malformed_voids > 0`; "N_TOTAL" if `primary_conn` is not null and `N_total < 5`;
     "ZERO" if `N_total > 0` and `sumW_BUY == sumW_SELL` and "N_TOTAL" is not in `reasons`.
  g. `status` = "NONE" if `reasons` is non-empty, else "VALID". `side` = 0 if `reasons` is non-empty, else 1 if `sumW_BUY > sumW_SELL`, else -1. `X_sn` = null if `N_total == 0`, else `repr(float((sumW_BUY - sumW_SELL) / (sumW_BUY + sumW_SELL)))`
     (exact decimal division at 200 digits, converted to float once at the end); `X_sn` is journalled also when the status is NONE.

7.6 Replay is not optional (r5; GPT audit 2026-11-07, G-2). A verifier that implements section 7 MUST run the replay by default. Disabling it is allowed only as an explicit opt-out for fixture-only tests, and then:
  * `replayed` MUST be false and `analysis_eligible` MUST be false;
  * the hard finding `REPLAY_NOT_RUN` (where = 0) MUST be reported;
  * `verdict` MUST be "FAIL" if any other hard finding exists (other than `CANDLE_LAG_UNSET`, which like `REPLAY_NOT_RUN` only makes the verdict INCOMPLETE, 6.8) and "INCOMPLETE" otherwise. It MUST NEVER be "PASS".
  The opt-out is fail-closed: the replay runs only when the caller passes exactly the boolean true; any other value (None, 0, 1, a string) is treated as an opt-out.
  `analysis_eligible` is true only if `verdict` is "PASS" and `replayed` is true; "PASS" therefore means that sections 1-6 AND the replay completed without a hard finding.
  A verifier that does NOT implement section 7 (today: the partially independent verifier of this package) MUST report `replayed: false`, `analysis_eligible: false` and the hard finding `REPLAY_NOT_RUN` on every run;
  its verdict is therefore "FAIL" or "INCOMPLETE" and never "PASS". This is what keeps its output from being mistaken for a complete verification.
  A consumer (the slots builder) MUST NOT accept a primary report without `replayed: true`, MUST NOT mark a build analysis-eligible unless every report it consumed has `replayed: true`,
  and MUST NOT use a report without `analysis_eligible: true` for the analysis. While no independent replay exists, no build is analysis-eligible.
  A replay over a journal without any reference SLOT is vacuous (`replayed: true`, nothing was compared); the consumer's own checks (missing grid points, N_eval) are what expose an empty analysis.

7.7 Run-level pass over every FORCE message (r6; GPT 2026-11-11). The replay of 7.2-7.5 looks, for each SLOT, only at the messages recorded BEFORE that SLOT, so by itself it never examines a message recorded after the last SLOT and examines a message once per SLOT that follows it. The structural rules therefore get a pass of their own, which does not depend on any SLOT:
  a. For EVERY valid MSG event at line m whose connection feed is FORCE or which has no feed (2.3c) -- before, between or after the SLOT events, and also in a journal that has no SLOT -- exactly once: if the decoded raw bytes are NOT a strictly parsable JSON object (strict UTF-8, no duplicate key at any depth, no NaN / Infinity, a JSON object) nothing is reported by this section (the message is MALFORMED for the replay and voids slots by 7.5d, but it is not a structural anomaly) [C: GPT's "anomaly" is read as the ps / st anomalies of 7.5a; every other MALFORMED reason stays slot-voiding only. GPT to confirm that no other malformed reason is meant to be a run-level finding].
  b. Otherwise the FIRST of the reasons `st_top_level`, `ps_type`, `ps_ne_s`, `st_type`, `st_ne_1` (the definitions and the order of 7.5a) that applies yields ONE hard finding `FORCE_MSG_STRUCTURE`: `where` = m (the MSG's `seq`, equal to its line number by 3.1), detail EXACTLY `conn_id=<int> reason=<reason>`. This is evaluated on the parsed object, independently of every other classification reason: a message that is also MALFORMED for an earlier reason of 7.5a (for example a wrong symbol) still yields this finding if it is a parsable object and the anomaly is present.
  c. If the parsable object has unknown keys (7.5a), ONE soft finding `FORCE_UNKNOWN_KEY` per message: `where` = m, detail EXACTLY `conn_id=<int> keys=<k1,k2,...>` with the unknown key names sorted by code point and joined by a comma (a top-level `st` is not an unknown key; it is the hard case of b). Several unknown keys in one message are ONE finding. It has no consequence for the verdict or for the analysis; it is reported so that a change of the exchange's message format is visible.
  d. Multiplicity: one finding per violating MSG, exactly as b and c say, however many SLOT replays contain that message. The findings of 7.7 are NOT produced by the replay of any SLOT and do not depend on any SLOT. A message that lies in the window of a SLOT additionally affects THAT slot by 7.5d (MALFORMED -> NONE, reason MALFORMED); the slot effect and the run-level effect are separate, and no artificial SLOT is created for a message that lies after the last SLOT.
  e. Run-level consequence: one `FORCE_MSG_STRUCTURE` makes the verdict "FAIL" (8.2) and `analysis_eligible` false. The finding is STICKY because it is derived from the journal bytes: later healthy messages cannot clear it, and no later event can. Reception and verification continue: the collector does not disconnect, the replay does not stop and does not truncate the journal, and every later message is still classified as usual for diagnosis.
  f. Independence: both verifiers MUST implement 7.5a and 7.7 on their own; the shared kline parser (6.6) does not extend to the FORCE rules. The reports are compared on the tuple (`finding name`, `where`, `conn_id`, `reason`), where `conn_id` and `reason` are read from the detail string of the finding.

## 8. Result
8.1 Hard findings: BAD_ENCODING, NOT_CANONICAL, BAD_EVENT, RAW_HASH_MISMATCH, SEQ_GAP, HEAD_MISMATCH, RECEIPT_INVALID, CHECKPOINT_ORDER, TRUNCATION_OR_REPLACEMENT, SLOT_OFF_GRID,
    SLOT_HAS_OUTCOME_FIELDS, DUPLICATE_SLOT, DUPLICATE_OUTCOME, OUTCOME_ORPHAN, OUTCOME_BEFORE_ANCHOR, OUTCOME_FOR_NONE_SLOT, OUTCOME_TIMING, OUTCOME_MISMATCH, OUTCOME_UNLINKED, CANDLE_CONFLICT, CANDLE_NOT_LIVE,
    SLOT_MISMATCH, SLOT_EARLY_WRITE (the last two only when the replay layer is run), REPLAY_NOT_RUN (r5; 7.6);
    r6: CONN_FEED_CONFLICT (2.3b), MSG_CONN_UNKNOWN (2.3c), FORCE_MSG_STRUCTURE (7.7b), CANDLE_LINK (6.5), CANDLE_PARSE (6.6), CANDLE_FIELD_MISMATCH (6.6), CANDLE_LAG_UNSET (6.8; INCOMPLETE-class like REPLAY_NOT_RUN).
    Soft findings: SLOT_LATE_ANCHOR, SLOT_UNANCHORED, SLOT_MISSING, OUTCOME_UNCOVERED, FORCE_UNKNOWN_KEY (r6; 7.7c).  Informational: NO_CHECKPOINT, TAIL_UNANCHORED, ANCHOR_AHEAD_BENIGN.
8.2 `verify(path, anchor, journal_id, verify_time_ms)` returns a dict with keys:
    `verdict` ("FAIL" if at least one hard finding other than REPLAY_NOT_RUN and CANDLE_LAG_UNSET exists; else "INCOMPLETE" if REPLAY_NOT_RUN or CANDLE_LAG_UNSET is present; else "PASS"), `findings` (list of `[name, where, detail_string]`, `where` fixed by the table in 8.4), `hard` (sorted list of the distinct hard finding names present), `soft` (sorted distinct soft names), `n_events` (N), `head_hex`, `slots` and `missing` as in 5.5, `outcomes` as in 6.4, `candles` (r6: dict `open_time_ms` -> "USABLE" or the reason code of 6.8, for REFERENCE CANDLEs only), `replayed` (bool: whether the replay layer ran; r5: reported by EVERY verifier) and `analysis_eligible` (bool; r5: true only if `verdict` is "PASS" and `replayed` is true). A consumer that requires the replay (7.1, 7.6) MUST refuse a report without `replayed: true`.
8.3 Findings are about the file as given; the verifier MUST NOT modify any file, MUST NOT use the network and MUST NOT depend on the wall clock (only `verify_time_ms`).

8.4 `where` and multiplicity (normative; two verifiers MUST agree on (name, where) multisets):
  - `where` = tau_ms: SLOT_LATE_ANCHOR, SLOT_UNANCHORED, SLOT_MISSING, OUTCOME_UNCOVERED.
  - `where` = anchor index `idx` (the index looped over in 4.3): TRUNCATION_OR_REPLACEMENT, ANCHOR_AHEAD_BENIGN.
  - `where` = 0: NO_CHECKPOINT, REPLAY_NOT_RUN, CANDLE_LAG_UNSET (r6).
  - `where` = 1-based line number of the event the finding is about, for everything else; in particular: DUPLICATE_SLOT = line of each second-or-later SLOT; SLOT_OFF_GRID and SLOT_HAS_OUTCOME_FIELDS = the SLOT line;
    DUPLICATE_OUTCOME and every OUTCOME_* except OUTCOME_UNCOVERED = the OUTCOME line j; CANDLE_CONFLICT = line of the first CANDLE whose `open` differs from the `open` of the first CANDLE with that open_time_ms;
    CANDLE_NOT_LIVE = the CANDLE line; CHECKPOINT_ORDER / HEAD_MISMATCH / RECEIPT_INVALID = the CHECKPOINT line; SEQ_GAP = first line with seq != n; BAD_ENCODING as in 1.3;
    TAIL_UNANCHORED = (line of the last valid CHECKPOINT) + 1; SLOT_MISMATCH and SLOT_EARLY_WRITE = the SLOT line;
    r6: CONN_FEED_CONFLICT = the CONN line; MSG_CONN_UNKNOWN, FORCE_MSG_STRUCTURE and FORCE_UNKNOWN_KEY = the MSG line; CANDLE_LINK, CANDLE_PARSE and CANDLE_FIELD_MISMATCH = the CANDLE line. The detail string of FORCE_MSG_STRUCTURE and FORCE_UNKNOWN_KEY is fixed by 7.7b and 7.7c.
  - Multiplicity (r6 additions: one CANDLE_LINK, CANDLE_PARSE or CANDLE_FIELD_MISMATCH rule outcome per CANDLE record as 6.5 / 6.6 say; one CONN_FEED_CONFLICT per conflicting CONN event; one MSG_CONN_UNKNOWN, FORCE_MSG_STRUCTURE or FORCE_UNKNOWN_KEY per MSG): one finding per violating item exactly as the rule in question says ("once per ..." / "for every ..."); in particular an OUTCOME is checked in 6.1 in full even if it is a DUPLICATE_OUTCOME,
    OUTCOME_UNLINKED yields one finding for each failing reference (entry candle, exit candle) so at most two per OUTCOME, and an OUTCOME whose reference SLOT lies AFTER it yields both
    OUTCOME_ORPHAN and OUTCOME_BEFORE_ANCHOR.

8.5 No override; re-verification (r6; GPT 2026-11-10 and 2026-11-11). A hard finding is never cleared by deleting or editing a raw message, by a later message, or by a human decision. A human review is a SEPARATE record kept outside the verifier; it MUST NOT delete a finding or turn a "FAIL" into a "PASS", and a consumer (the slots builder) MUST NOT accept such a record in place of a report. If a contract change is accepted, the PRESERVED raw journal is verified again under the new contract revision; the new report is a separate result and the old report is kept.

## 9. Known limits (not defects of a verifier)
Events after the last anchored head and everything before the first checkpoint are not authenticated (4.4). A cut exactly before the last CHECKPOINT line is reported only as
ANCHOR_AHEAD_BENIGN (4.3), because it cannot be told apart from a crash between anchor submission and the CHECKPOINT write. Trust in the anchor itself is assumed.
One genuine BTCUSDT `forceOrder` frame has been observed (the owner's run 9 of 2026-11-10, from one machine behind a VPN; SHA-256 `537a499a9b1f10c62cf7f65c7d2a02f7d6038c0d56135bcad588fc92b32074ce`; the capture is not in Git). It carries `ps` and `st` inside `o`; that is why 7.5a makes them known optional fields and not mandatory ones. One frame is not a distribution. Nothing in this text has been tested against a real journal, and the real kline and forceOrder frames seen so far say nothing about latency (the laptop clock was not calibrated), about `L`, `U`, `E_RANGE`, `k.x`, or the behaviour of the exchange over days.

## 10. Minimum conformance cases for the test step (r6; GPT 2026-11-11; the tests are a separate pull request and do not exist yet)
Each case is checked on BOTH verifiers, and the two reports are compared on (finding name, where, conn_id, reason):
 1. a structurally anomalous FORCE message (each of `st_top_level`, `ps_type`, `ps_ne_s`, `st_type`, `st_ne_1`) recorded BEFORE a SLOT;
 2. one recorded BETWEEN two SLOTs;
 3. one recorded AFTER the last SLOT (and in a journal with no SLOT at all): exactly one finding, verdict FAIL, no artificial SLOT;
 4. one on a NON-primary FORCE connection;
 5. a structurally anomalous frame on a KLINE connection: no FORCE finding, never a replay input;
 6. one FORCE message with several unknown keys: ONE `FORCE_UNKNOWN_KEY`, sorted key list, no slot voided, no hard finding;
 7. `st = true` (a boolean is not the integer 1) and `ps = 1` (a number is not a string);
 8. one anomalous message that follows many SLOTs and is replayed by each of them: ONE run-level finding;
 9. an anomalous message inside the window of a SLOT: that slot is NONE (reason MALFORMED), the run-level finding is present once, and later healthy messages do not clear it;
10. a top-level `ps` (without `st`): soft finding only; a top-level `st = 1`: hard `FORCE_MSG_STRUCTURE`, reason `st_top_level`; `o.ps` and `o.st` absent: no finding; `o.ps == o.s` and `o.st == 1`: no finding;
11. feed: a CONN without `feed` or with another value is BAD_EVENT; a `conn_id` whose later CONN event names another feed gives `CONN_FEED_CONFLICT`; a MSG with no earlier `open` gives `MSG_CONN_UNKNOWN`; adding a KLINE connection with a SMALLER connection id and many kline frames changes no SLOT field (the case `demo_topology_conflict` of the G-1 package, as a test of the replay);
12. genesis: a journal chained from the v2 genesis fails with `HEAD_MISMATCH`;
13. `CANDLE_LAG_UNSET` is reported on every journal while `L` is unset, no minute is USABLE, the verdict is never PASS.
