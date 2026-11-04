# D-LIQ evidence journal -- contract v2 (verifier-facing, normative for r3 Appendix A)

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
- CONN: conn_id (int), ev ("open" or "close"), ms (int)
- PING: conn_id (int), ms (int)
- MSG: conn_id (int), recv_ms (int), raw_b64 (string), sha256 (string)
- CLOCK: offset_ms (int), ms (int)
- CANDLE: open_time_ms (int), open (dec), recv_ms (int), raw_b64 (string), sha256 (string)
- SLOT: tau_ms (int), status ("VALID" or "NONE"), reasons (list of strings), primary_conn (int or null), N_total, N_BUY, N_SELL, side, malformed_voids, n_messages (int), sumW_BUY, sumW_SELL (dec), X_sn (string or null), ledger (object whose values are ints)
- OUTCOME: tau_ms (int), status ("EVAL" or "NO_PRICE"); if status is "EVAL" also entry_open_ms, exit_open_ms (int), entry_price, exit_price (dec), r_bps (string)
- CHECKPOINT: anchored_seq (int), anchored_head (string), receipt (object) with anchor_id (string), index (int), seq (int), head (string), time_ms (int), time_resolution_ms (int), time_uncertainty_ms (int)
- SESSION: no required fields.
A field listed as "(int or null)" or "(string or null)" is still REQUIRED to be present as a key; a missing key is `BAD_EVENT`, JSON `null` is accepted.
A parsed line violating 2.1 (unknown `t`, missing or mistyped field) is `BAD_EVENT` at that line; such an event takes part in the hash chain and in 3 (SEQ_GAP) but is EXCLUDED from every check in 4-8.
Extra fields beyond those listed are allowed and ignored (except as stated in 5.2).
2.2 `raw_b64` MUST be valid standard base64; the SHA-256 (lowercase hex) of the decoded bytes MUST equal `sha256` for MSG and CANDLE events, else `RAW_HASH_MISMATCH`
    (invalid base64 is also `RAW_HASH_MISMATCH`).

## 3. Sequence and chain
3.1 The event at line n MUST have `seq == n`. The first line n where this fails gets ONE finding `SEQ_GAP` (later mismatches are not reported separately).
3.2 `GENESIS = b"DLIQ-JOURNAL-v2-GENESIS"`. `h_0 = SHA-256(GENESIS)` (32 raw bytes). `h_n = SHA-256(h_{n-1} + line_n)` (raw bytes concatenation, line_n WITHOUT the newline),
    computed over every parsed line in file order (including BAD_EVENT / NOT_CANONICAL lines). `head_hex` of the result is the lowercase hex of `h_N`, N = number of parsed lines.

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
     - `OUTCOME_UNLINKED` (hard) if there is no valid CANDLE at a line before j whose `open_time_ms` equals entry_open_ms (resp. exit_open_ms), or if the FIRST such CANDLE has `open` different (string comparison) from entry_price (resp. exit_price).
6.2 For every pair of valid CANDLE events with the same `open_time_ms` but different `open`: `CANDLE_CONFLICT` (hard), reported once per open_time_ms.
6.3 `CANDLE_NOT_LIVE` (hard) for every valid CANDLE with `recv_ms < open_time_ms`.

## 7. Optional layer: SLOT replay (OUT OF SCOPE for this partially independent implementation)
A verifier MAY recompute each SLOT from journalled MSG/CONN/PING/CLOCK events with the executable message contract (`dliq_msg_contract_v1.build_slot`) and report `SLOT_MISMATCH` (hard)
on any difference. This layer is off in the differential tests.

## 8. Result
8.1 Hard findings: BAD_ENCODING, NOT_CANONICAL, BAD_EVENT, RAW_HASH_MISMATCH, SEQ_GAP, HEAD_MISMATCH, RECEIPT_INVALID, CHECKPOINT_ORDER, TRUNCATION_OR_REPLACEMENT, SLOT_OFF_GRID,
    SLOT_HAS_OUTCOME_FIELDS, DUPLICATE_SLOT, DUPLICATE_OUTCOME, OUTCOME_ORPHAN, OUTCOME_BEFORE_ANCHOR, OUTCOME_TIMING, OUTCOME_MISMATCH, OUTCOME_UNLINKED, CANDLE_CONFLICT, CANDLE_NOT_LIVE, SLOT_MISMATCH.
    Soft findings: SLOT_LATE_ANCHOR, SLOT_UNANCHORED, SLOT_MISSING.  Informational: NO_CHECKPOINT, TAIL_UNANCHORED, ANCHOR_AHEAD_BENIGN.
8.2 `verify(path, anchor, journal_id, verify_time_ms)` returns a dict with keys:
    `verdict` ("FAIL" if at least one hard finding else "PASS"), `findings` (list of `[name, where, detail_string]`, `where` fixed by the table in 8.4), `hard` (sorted list of the distinct hard finding names present), `soft` (sorted distinct soft names), `n_events` (N), `head_hex`, `slots` and `missing` as in 5.5.
8.3 Findings are about the file as given; the verifier MUST NOT modify any file, MUST NOT use the network and MUST NOT depend on the wall clock (only `verify_time_ms`).

8.4 `where` and multiplicity (normative; two verifiers MUST agree on (name, where) multisets):
  - `where` = tau_ms: SLOT_LATE_ANCHOR, SLOT_UNANCHORED, SLOT_MISSING.
  - `where` = anchor index `idx` (the index looped over in 4.3): TRUNCATION_OR_REPLACEMENT, ANCHOR_AHEAD_BENIGN.
  - `where` = 0: NO_CHECKPOINT.
  - `where` = 1-based line number of the event the finding is about, for everything else; in particular: DUPLICATE_SLOT = line of each second-or-later SLOT; SLOT_OFF_GRID and SLOT_HAS_OUTCOME_FIELDS = the SLOT line;
    DUPLICATE_OUTCOME and every OUTCOME_* = the OUTCOME line j; CANDLE_CONFLICT = line of the first CANDLE whose `open` differs from the `open` of the first CANDLE with that open_time_ms;
    CANDLE_NOT_LIVE = the CANDLE line; CHECKPOINT_ORDER / HEAD_MISMATCH / RECEIPT_INVALID = the CHECKPOINT line; SEQ_GAP = first line with seq != n; BAD_ENCODING as in 1.3;
    TAIL_UNANCHORED = (line of the last valid CHECKPOINT) + 1; SLOT_MISMATCH = the SLOT line.
  - Multiplicity: one finding per violating item exactly as the rule in question says ("once per ..." / "for every ..."); in particular an OUTCOME is checked in 6.1 in full even if it is a DUPLICATE_OUTCOME,
    OUTCOME_UNLINKED yields one finding for each failing reference (entry candle, exit candle) so at most two per OUTCOME, and an OUTCOME whose reference SLOT lies AFTER it yields both
    OUTCOME_ORPHAN and OUTCOME_BEFORE_ANCHOR.

## 9. Known limits (not defects of a verifier)
Events after the last anchored head and everything before the first checkpoint are not authenticated (4.4). A cut exactly before the last CHECKPOINT line is reported only as
ANCHOR_AHEAD_BENIGN (4.3), because it cannot be told apart from a crash between anchor submission and the CHECKPOINT write. Trust in the anchor itself is assumed.
