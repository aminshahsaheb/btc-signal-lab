"""Synthetic regressions for OUTCOME/SLOT status binding; no network or market feed."""
import json
import math
import os
import sys
import tempfile
import unittest

ROOT = os.path.dirname(os.path.dirname(__file__))
sys.path.insert(0, os.path.join(ROOT, "src"))
sys.path.insert(0, os.path.join(ROOT, "indep_verifier"))
import dliq_journal_v2 as J
import dliq_journal_verify_v2 as P
import verify_indep as I
import verify_indep_as_delivered as DELIVERED

TAU = 1_793_001_600_000
JID = "R3-RECONSTRUCTION-NONE-OUTCOME"
H = 3_600_000

class AnchorView:
    def __init__(self, path):
        self.rows = [json.loads(x) for x in open(path, "rb").read().split(b"\n") if x]
    def get(self, jid, index):
        return next((x for x in self.rows if x["journal_id"] == jid and x["index"] == index), None)
    def latest(self, jid):
        return sum(x["journal_id"] == jid for x in self.rows)

def none_slot(j, now, tau):
    now[0] = tau + 11_000
    fields = {"tau_ms": tau, "status": "NONE", "reasons": ["N_TOTAL"], "primary_conn": 1,
              "N_total": 0, "N_BUY": 0, "N_SELL": 0, "sumW_BUY": "0", "sumW_SELL": "0",
              "side": 0, "malformed_voids": 0, "ledger": {"COUNTED": 0}, "n_messages": 0, "X_sn": None}
    j.append("SLOT", **J.slot_fields(fields))
    return j.seq

def build_case(mixed=False):
    td = tempfile.TemporaryDirectory()
    jp, ap = os.path.join(td.name, "journal.jsonl"), os.path.join(td.name, "anchor.jsonl")
    now = [TAU - H]
    j = J.Journal(jp, JID, lambda: now[0]); a = J.MockAnchor(ap, lambda: now[0])
    j.append("SESSION", journal_id=JID)
    slot_line = none_slot(j, now, TAU)
    now[0] = TAU + 20_000; j.checkpoint(a)
    valid_tau = TAU
    if mixed:
        valid_tau += 4 * H
        now[0] = valid_tau + 11_000
        fields = {"tau_ms": valid_tau, "status": "VALID", "reasons": [], "primary_conn": 1,
                  "N_total": 1, "N_BUY": 1, "N_SELL": 0, "sumW_BUY": "1", "sumW_SELL": "0",
                  "side": 1, "malformed_voids": 0, "ledger": {"COUNTED": 1}, "n_messages": 1, "X_sn": None}
        j.append("SLOT", **J.slot_fields(fields))
        now[0] = valid_tau + 20_000; j.checkpoint(a)
        entry, exit_ = valid_tau + J.ENTRY_DELAY_MS, valid_tau + J.ENTRY_DELAY_MS + J.OUTCOME_HORIZON_MS
        for ot, price in ((entry, "100000"), (exit_, "100500")):
            now[0] = ot + 100
            raw = ("synthetic-candle-" + str(ot)).encode()
            j.append("CANDLE", **J.candle_fields(ot, price, ot + 100, raw))
        now[0] = exit_ + 200
        r = repr(1e4 * math.log(1.005))
        j.append("OUTCOME", **J.outcome_fields(valid_tau, "EVAL", entry, exit_, "100000", "100500", r))
    # The checked writer must refuse. The unchecked append creates adversarial evidence for verifiers.
    now[0] += 100
    before = j.seq
    try:
        j.append("OUTCOME", **J.outcome_fields(TAU, "NO_PRICE"))
        refused = False
    except J.JournalError:
        refused = True
    assert j.seq == before
    j.append_unchecked("OUTCOME", **J.outcome_fields(TAU, "NO_PRICE"))
    bad_line = j.seq
    verify_time = now[0] + 100
    j.close()
    return td, jp, ap, slot_line, bad_line, verify_time, refused

class NoneOutcomeRegressionTests(unittest.TestCase):
    def check_case(self, mixed):
        td, jp, ap, slot_line, bad_line, vt, refused = build_case(mixed)
        with td:
            a = AnchorView(ap)
            self.assertTrue(refused)
            self.assertEqual(slot_line, 2)
            if not mixed:
                self.assertEqual(bad_line, 4)
            for mod in (P, I):
                r = mod.verify(jp, a, JID, vt)
                self.assertEqual(r["verdict"], "FAIL")
                rows = [f for f in r["findings"] if f[0] == "OUTCOME_FOR_NONE_SLOT"]
                self.assertEqual([(f[0], f[1]) for f in rows], [("OUTCOME_FOR_NONE_SLOT", bad_line)])
            old = DELIVERED.verify(jp, a, JID, vt)
            self.assertNotIn("OUTCOME_FOR_NONE_SLOT", old["hard"])
    def test_anchored_none_outcome_is_hard_at_line_four(self):
        self.check_case(False)
    def test_mixed_slots_keep_valid_outcome_clean_and_reject_none(self):
        self.check_case(True)

if __name__ == "__main__":
    unittest.main()
