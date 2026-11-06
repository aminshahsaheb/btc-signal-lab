"""r4 patch 01: contract text (JOURNAL_CONTRACT_v2.md) -> r4. All edits asserted; usage: python3 p01_contract.py <tree>"""
import sys
tree = sys.argv[1]
p = tree + "/indep_verifier/JOURNAL_CONTRACT_v2.md"
s = open(p, encoding="utf-8").read()

def rep(a, b):
    global s
    assert s.count(a) == 1, (a[:70], s.count(a))
    s = s.replace(a, b)

rep("# D-LIQ evidence journal -- contract v2 (verifier-facing, normative for r3 Appendix A)",
    "# D-LIQ evidence journal -- contract v2, revision r4-draft (verifier-facing; supersedes the r3 / r3-reconstruction text; DRAFT, not locked)\n\n"
    "REVISION r4 (answer to GPT's r3 audit, orders 1-4): adds 6.1e (`OUTCOME_FOR_NONE_SLOT`, from the r3-reconstruction amendment), 6.4 (every reference OUTCOME is COVERED by a later valid checkpoint or UNCOVERED; the verifier reports `outcomes`),\n"
    "makes the SLOT replay of section 7 MANDATORY for the analysis pipeline, and adds the hard finding `SLOT_EARLY_WRITE`. The event format and the genesis string are unchanged.")

# 6.1 e
rep("6.2 For every pair of valid CANDLE events",
    "  e. `OUTCOME_FOR_NONE_SLOT` (hard) if a reference SLOT with that `tau_ms` exists (at any line) and its recorded `status` is not \"VALID\". A NONE slot cannot become an outcome row, not even NO_PRICE. The journal writer refuses to append such an OUTCOME.\n"
    "     (An OUTCOME whose reference SLOT lies after it yields OUTCOME_ORPHAN, OUTCOME_BEFORE_ANCHOR and, when that SLOT is not VALID, also OUTCOME_FOR_NONE_SLOT.)\n"
    "6.2 For every pair of valid CANDLE events")

# 6.4
add_64 = """
6.4 Coverage of outcomes (r4; GPT audit P0-1, order 1). For the reference OUTCOME of each tau (the FIRST valid OUTCOME with that `tau_ms` in file order, at line j) the covering checkpoint is the FIRST valid CHECKPOINT
    line c > j with `anchored_seq >= j`. The outcome is `COVERED` if such a checkpoint exists, otherwise `UNCOVERED`. Every UNCOVERED reference OUTCOME (status EVAL or NO_PRICE) yields one soft finding
    `OUTCOME_UNCOVERED` with `where` = `tau_ms`. The verifier reports `outcomes`: a dict `tau_ms -> "COVERED" | "UNCOVERED"` for reference OUTCOMEs only. Later duplicates (DUPLICATE_OUTCOME, hard) are not entered.
    The verifier sets NO deadline on the covering checkpoint (owner decision OPEN-22, 2026-11-05: no hard lag cap; the collector must checkpoint immediately after each OUTCOME, report the lag distribution and write a final drain
    checkpoint; a prolonged anchor outage makes the run INCONCLUSIVE and never silently removes rows). Consequence, implemented by the slots builder and not by the verifier: an UNCOVERED reference OUTCOME MUST NOT enter the analysis;
    the builder reports it PENDING and refuses to write the analysis CSV (owner decision 2026-11-05; it is NOT converted to NO_PRICE). The writer helper `outcome_and_anchor` appends an OUTCOME and the checkpoint that covers it.
"""
rep("\n## 7. Optional layer: SLOT replay (OUT OF SCOPE for this partially independent implementation)", add_64 + "\n## 7. SLOT replay (MANDATORY for the analysis pipeline before T0; r4)")

a = s.index("## 7. SLOT replay")
b = s.index("## 8. Result")
new7 = """## 7. SLOT replay (MANDATORY for the analysis pipeline before T0; r4)
7.1 Requirement (GPT audit P0-3, order 3). The slots builder MUST run the replay of every reference SLOT and MUST refuse to produce an analysis file from a journal whose replay was not run or reported any hard finding.
    A journal that passes sections 1-6 but was not replayed is NOT sufficient evidence for the analysis. The replay implemented in this package is the author's (`verify(..., replay_slots=True)` of the primary verifier,
    using the executable message contract). Before a lock an independent implementation of this section, written from the written specifications only and compared by a differential harness, MUST also exist; it is NOT part of this package.
7.2 Input of the replay of the reference SLOT at line i (tau = its `tau_ms`). Use ONLY the valid (2.1) events at lines `< i`, in file order:
  * every MSG: message `{conn_id, recv_ms, raw = base64-decoded raw_b64}`; the frame times of a connection (for the health rule) are the `recv_ms` of its MSG events and the `ms` of its PING events, in file order;
  * every CONN: `open_ms[conn_id]` = the `ms` of the FIRST `open` event of that connection id (later opens of the same id are ignored); `close_ms[conn_id]` = the `ms` of the LAST `close` event (absent if none);
  * every CLOCK: `clock_offset_ms` = `offset_ms` of the LAST CLOCK event (0 if none);
  * the end of the observation horizon of every connection is the `rec_ms` of the SLOT event itself.
  Events at lines `>= i` MUST NOT be used. The message classes, the feature window, the late rule, the void interval, the health rule, the primary-connection rule and the NONE reasons are those of the message contract
  (`dliq_msg_contract_v1.py`, `docs/07_MESSAGE_CONTRACT_v1.md` of the r3 package); the result is the SLOT fields of 7.3.
7.3 Compared fields (the replayed value MUST equal the journalled value; `X_sn` as the string `repr(float)` or null): status, reasons (as a list, same order), primary_conn, N_total, N_BUY, N_SELL, sumW_BUY, sumW_SELL
    (decimal strings, same text), side, malformed_voids, ledger (object), n_messages, X_sn. Any difference: `SLOT_MISMATCH` (hard), `where` = the SLOT line, the detail names the differing fields, sorted, comma separated.
7.4 `SLOT_EARLY_WRITE` (hard, `where` = the SLOT line): a reference SLOT whose `rec_ms < tau_ms + 10_000` (the late rule admits frames with `recv_ms <= tau + 10 s`; a SLOT written earlier could omit admissible frames that
    the journal records after it). Reported only when the replay layer is run; it is reported in addition to a possible SLOT_MISMATCH.

"""
s = s[:a] + new7 + s[b:]

rep("SLOT_HAS_OUTCOME_FIELDS, DUPLICATE_SLOT, DUPLICATE_OUTCOME, OUTCOME_ORPHAN, OUTCOME_BEFORE_ANCHOR, OUTCOME_TIMING, OUTCOME_MISMATCH, OUTCOME_UNLINKED, CANDLE_CONFLICT, CANDLE_NOT_LIVE, SLOT_MISMATCH.",
    "SLOT_HAS_OUTCOME_FIELDS, DUPLICATE_SLOT, DUPLICATE_OUTCOME, OUTCOME_ORPHAN, OUTCOME_BEFORE_ANCHOR, OUTCOME_FOR_NONE_SLOT, OUTCOME_TIMING, OUTCOME_MISMATCH, OUTCOME_UNLINKED, CANDLE_CONFLICT, CANDLE_NOT_LIVE,\n    SLOT_MISMATCH, SLOT_EARLY_WRITE (the last two only when the replay layer is run).")
rep("    Soft findings: SLOT_LATE_ANCHOR, SLOT_UNANCHORED, SLOT_MISSING.  Informational:",
    "    Soft findings: SLOT_LATE_ANCHOR, SLOT_UNANCHORED, SLOT_MISSING, OUTCOME_UNCOVERED.  Informational:")
rep("`slots` and `missing` as in 5.5.", "`slots` and `missing` as in 5.5, and `outcomes` as in 6.4.")
rep("  - `where` = tau_ms: SLOT_LATE_ANCHOR, SLOT_UNANCHORED, SLOT_MISSING.", "  - `where` = tau_ms: SLOT_LATE_ANCHOR, SLOT_UNANCHORED, SLOT_MISSING, OUTCOME_UNCOVERED.")
rep("DUPLICATE_OUTCOME and every OUTCOME_* = the OUTCOME line j;", "DUPLICATE_OUTCOME and every OUTCOME_* except OUTCOME_UNCOVERED = the OUTCOME line j;")
rep("SLOT_MISMATCH = the SLOT line.", "SLOT_MISMATCH and SLOT_EARLY_WRITE = the SLOT line.")
open(p, "w", encoding="utf-8").write(s)
print("contract patched, lines:", s.count("\n"))
