"""r4 patch 02: writer helper outcome_and_anchor + primary verifier (OUTCOME coverage, SLOT_EARLY_WRITE). usage: python3 p02_writer_primary.py <tree>"""
import sys
tree = sys.argv[1]

def patch(path, edits):
    s = open(path, encoding="utf-8").read()
    for a, b in edits:
        assert s.count(a) == 1, (path, a[:80], s.count(a))
        s = s.replace(a, b)
    open(path, "w", encoding="utf-8").write(s)

patch(tree + "/src/dliq_journal_v2.py", [
("  * Journal.slot_and_anchor() writes the SLOT and the CHECKPOINT back to back (the only supported way to record a signal);",
 "  * Journal.slot_and_anchor() writes the SLOT and the CHECKPOINT back to back (the only supported way to record a signal);\n"
 "  * Journal.outcome_and_anchor() (r4, contract 6.4) writes the OUTCOME and the CHECKPOINT that covers it back to back (the only supported way to record an outcome);"),
("    def close(self):\n        try:\n            fcntl.flock",
 "    def outcome_and_anchor(self, outcome_rec, anchor):\n"
 "        \"\"\"the only supported way to record an outcome (r4, contract 6.4): OUTCOME immediately followed by the CHECKPOINT that covers it, so that no outcome sits in the unanchored tail\n"
 "        (an UNCOVERED outcome may not be used in the analysis). `outcome_rec` is passed to append(\"OUTCOME\", ...), i.e. all writer refusals apply. Returns (outcome_seq, checkpoint_seq).\"\"\"\n"
 "        s = self.append(\"OUTCOME\", **outcome_rec)\n"
 "        return s, self.checkpoint(anchor)\n\n"
 "    def close(self):\n        try:\n            fcntl.flock"),
])

patch(tree + "/src/dliq_journal_verify_v2.py", [
('"OUTCOME_BEFORE_ANCHOR", "OUTCOME_FOR_NONE_SLOT", "OUTCOME_TIMING", "OUTCOME_MISMATCH", "OUTCOME_UNLINKED", "CANDLE_CONFLICT", "CANDLE_NOT_LIVE", "SLOT_MISMATCH"}',
 '"OUTCOME_BEFORE_ANCHOR", "OUTCOME_FOR_NONE_SLOT", "OUTCOME_TIMING", "OUTCOME_MISMATCH", "OUTCOME_UNLINKED", "CANDLE_CONFLICT", "CANDLE_NOT_LIVE", "SLOT_MISMATCH",\n        "SLOT_EARLY_WRITE"}'),
('SOFT = {"SLOT_LATE_ANCHOR", "SLOT_UNANCHORED", "SLOT_MISSING"}', 'SOFT = {"SLOT_LATE_ANCHOR", "SLOT_UNANCHORED", "SLOT_MISSING", "OUTCOME_UNCOVERED"}'),
('Does not import the writer. The optional SLOT-replay layer (contract section 7) imports dliq_msg_contract_v1 lazily.',
 'Does not import the writer. The SLOT-replay layer (contract section 7; MANDATORY for the analysis pipeline, the slots builder always calls verify(..., replay_slots=True)) imports dliq_msg_contract_v1 lazily.'),
('verify(path, anchor, journal_id, verify_time_ms, replay_slots=False) -> dict(verdict, findings, hard, soft, n_events, head_hex, slots, missing)',
 'verify(path, anchor, journal_id, verify_time_ms, replay_slots=False) -> dict(verdict, findings, hard, soft, n_events, head_hex, slots, missing, outcomes)\n'
 'r4: `outcomes` = {tau_ms: "COVERED" | "UNCOVERED"} for the reference OUTCOME of each tau (contract 6.4; soft finding OUTCOME_UNCOVERED).'),
('''    seen_outcome = set()
    for j, ev in sorted(valid.items()):
        if ev["t"] != "OUTCOME":
            continue
        tau = ev["tau_ms"]
        if tau in seen_outcome:
            F(["DUPLICATE_OUTCOME", j, "second OUTCOME for tau_ms %d" % tau])
        seen_outcome.add(tau)''',
'''    seen_outcome = set()
    outcomes = {}
    for j, ev in sorted(valid.items()):
        if ev["t"] != "OUTCOME":
            continue
        tau = ev["tau_ms"]
        if tau in seen_outcome:
            F(["DUPLICATE_OUTCOME", j, "second OUTCOME for tau_ms %d" % tau])
        else:
            # 6.4: the covering checkpoint of the reference OUTCOME is the first valid checkpoint line c > j with anchored_seq >= j
            if any(c > j and e["anchored_seq"] >= j for c, e in cps):
                outcomes[tau] = "COVERED"
            else:
                outcomes[tau] = "UNCOVERED"
                F(["OUTCOME_UNCOVERED", tau, "no valid checkpoint after line %d anchors this OUTCOME" % j])
        seen_outcome.add(tau)'''),
('''            if diff:
                F(["SLOT_MISMATCH", i, "recomputed slot differs in " + ",".join(diff)])''',
'''            if diff:
                F(["SLOT_MISMATCH", i, "recomputed slot differs in " + ",".join(diff)])
            if ev["rec_ms"] < tau + 10_000:
                F(["SLOT_EARLY_WRITE", i, "SLOT written at rec_ms %d < tau_ms + 10 s = %d" % (ev["rec_ms"], tau + 10_000)])'''),
('    # 7 optional replay', '    # 7 replay (mandatory for the analysis pipeline; r4)'),
('            "slots": slots, "missing": missing}', '            "slots": slots, "missing": missing, "outcomes": outcomes}'),
])
print("ok")
