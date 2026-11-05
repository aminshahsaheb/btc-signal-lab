"""r4 patch 07: contract 7.5 (derivation of the SLOT fields). Text from the earlier (lost) r4 work, RE-CHECKED clause by clause against dliq_msg_contract_v1.py in this session; not independently implemented. usage: python3 p07_contract_75.py <tree>"""
import sys
tree = sys.argv[1]
p = tree + "/indep_verifier/JOURNAL_CONTRACT_v2.md"
s = open(p, encoding="utf-8").read()
add = '''7.5 Derivation of the SLOT fields (normative description of what `dliq_msg_contract_v1.build_slot` / `health_intervals` compute; checked against that code by reading, NOT yet by an independent implementation).
    Let `V = [tau - 960_000, tau + 10_000]` (closed), `W = [tau - 900_000, tau)` (half-open, on the JSON integer `E`), `rec` = the `rec_ms` of the SLOT event.
  a. Message class (MALFORMED / INELIGIBLE / ELIGIBLE) per the message contract (r3 package `docs/07_MESSAGE_CONTRACT_v1.md`, protocol 4.2); not restated here.
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
'''
j = s.index("\n## 8. Result")
s = s[:j].rstrip("\n") + "\n" + add + s[j:]
open(p, "w", encoding="utf-8").write(s)
print("ok")
