import hashlib
import importlib.util
import json
import os
import tempfile
import unittest

HERE = os.path.dirname(__file__)
SPEC = importlib.util.spec_from_file_location(
    "build_slots_v1", os.path.join(HERE, "build_slots_v1.py"))
BUILDER = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(BUILDER)

GRID = BUILDER.GRID_MS


def canonical(ev):
    return json.dumps(ev, sort_keys=True, separators=(",", ":"), ensure_ascii=True).encode("ascii")


def make_case(events, slot_map, missing=None, hard=None):
    td = tempfile.TemporaryDirectory()
    journal = os.path.join(td.name, "journal.jsonl")
    report1 = os.path.join(td.name, "primary.json")
    report2 = os.path.join(td.name, "independent.json")
    lines = []
    head = hashlib.sha256(BUILDER.GENESIS).digest()
    for n, ev in enumerate(events, 1):
        ev = dict(ev)
        ev["seq"] = n
        line = canonical(ev)
        lines.append(line)
        head = hashlib.sha256(head + line).digest()
    with open(journal, "wb") as f:
        f.write(b"\n".join(lines) + (b"\n" if lines else b""))
    h = head.hex()
    findings = [[name, 1, "synthetic test finding"] for name in (hard or [])]
    report = {
        "verdict": "FAIL" if hard else "PASS",
        "findings": findings, "hard": sorted(hard or []), "soft": [],
        "n_events": len(events), "head_hex": h,
        "slots": {str(k): v for k, v in slot_map.items()},
        "missing": list(missing or []),
    }
    for p in (report1, report2):
        with open(p, "w", encoding="utf-8") as f:
            json.dump(report, f, sort_keys=True)
    return td, journal, report1, report2


def base_events(tau=0, status="VALID", side=1, outcome="EVAL", prior=True):
    events = [{"t": "SESSION", "rec_ms": 1, "session_id": "test"}]
    if prior:
        events.extend([
            {"t": "CANDLE", "rec_ms": 2, "open_time_ms": tau-900000,
             "open": "100", "recv_ms": tau-899000, "raw_b64": "", "sha256": ""},
            {"t": "CANDLE", "rec_ms": 3, "open_time_ms": tau,
             "open": "101", "recv_ms": tau+1000, "raw_b64": "", "sha256": ""},
        ])
    events.append({
        "t": "SLOT", "rec_ms": 4, "tau_ms": tau, "status": status,
        "reasons": [], "primary_conn": 1, "N_total": 1, "N_BUY": 1,
        "N_SELL": 0, "sumW_BUY": "1", "sumW_SELL": "0", "side": side,
        "malformed_voids": 0, "ledger": {}, "n_messages": 1, "X_sn": "1",
    })
    events.append({
        "t": "CHECKPOINT", "rec_ms": 5, "anchored_seq": 4,
        "anchored_head": "a"*64, "receipt": {
            "anchor_id": "mock", "index": 1, "seq": 1, "head": "a"*64,
            "time_ms": 1, "time_resolution_ms": 1, "time_uncertainty_ms": 0,
        },
    })
    if outcome == "EVAL":
        events.extend([
            {"t": "CANDLE", "rec_ms": 6, "open_time_ms": tau+300000,
             "open": "101", "recv_ms": tau+301000, "raw_b64": "", "sha256": ""},
            {"t": "CANDLE", "rec_ms": 7, "open_time_ms": tau+300000+14400000,
             "open": "102", "recv_ms": tau+14701000, "raw_b64": "", "sha256": ""},
            {"t": "OUTCOME", "rec_ms": 8, "tau_ms": tau, "status": "EVAL",
             "entry_open_ms": tau+300000, "exit_open_ms": tau+14700000,
             "entry_price": "101", "exit_price": "102", "r_bps": "98.522"},
        ])
    elif outcome == "NO_PRICE":
        events.append({"t": "OUTCOME", "rec_ms": 8, "tau_ms": tau, "status": "NO_PRICE"})
    return events


class BuilderTests(unittest.TestCase):
    def run_build(self, events, slots, missing=None, hard=None):
        td, journal, r1, r2 = make_case(events, slots, missing, hard)
        self.addCleanup(td.cleanup)
        return BUILDER.build(journal, r1, r2)

    def test_eval_and_prior_sign(self):
        summary, primary, control = self.run_build(
            base_events(), {0: "OK"})
        self.assertTrue(summary["registry_ok"])
        self.assertEqual(primary, [[0, "EVAL", 1, "98.522"]])
        self.assertEqual(control, [[0, "EVAL", 1, "98.522", 1]])
        self.assertEqual(summary["N_eval"], 1)

    def test_no_price_has_blank_prior(self):
        summary, primary, control = self.run_build(
            base_events(outcome="NO_PRICE"), {0: "OK"})
        self.assertEqual(primary, [[0, "NO_PRICE", 1, ""]])
        self.assertEqual(control, [[0, "NO_PRICE", 1, "", ""]])
        self.assertEqual(summary["N_noprice"], 1)

    def test_outcome_for_none_slot_invalidates_registry(self):
        summary, primary, _ = self.run_build(
            base_events(status="NONE", outcome="NO_PRICE"), {0: "OK"})
        self.assertEqual(primary, [[0, "NONE", "", ""]])
        self.assertFalse(summary["registry_ok"])
        self.assertIn("BUILDER_OUTCOME_FOR_NONE_SLOT", summary["hard_findings"])

    def test_unanchored_valid_signal_becomes_none_and_is_counted(self):
        summary, primary, control = self.run_build(
            base_events(outcome=None), {0: "UNANCHORED"})
        self.assertEqual(primary, [[0, "NONE", "", ""]])
        self.assertEqual(summary["N_unanch"], 1)
        self.assertEqual(summary["N_none"], 1)

    def test_none_signal_is_none(self):
        summary, primary, _ = self.run_build(
            base_events(status="NONE", outcome=None), {0: "OK"})
        self.assertEqual(primary, [[0, "NONE", "", ""]])
        self.assertEqual(summary["N_unanch"], 0)

    def test_none_signal_with_late_anchor_is_unanchored_but_not_counted(self):
        summary, primary, _ = self.run_build(
            base_events(status="NONE", outcome=None), {0: "UNANCHORED"})
        self.assertEqual(primary, [[0, "NONE", "", ""]])
        self.assertEqual(summary["N_unanch"], 0)
        self.assertEqual(summary["diagnostics"][0]["reason"], "UNANCHORED")

    def test_missing_grid_point_is_synthesized(self):
        events = base_events(tau=0) + base_events(tau=2*GRID)[1:]
        # Re-sequence and keep only the two SLOTs, their checkpoints, and outcomes.
        events = [e for e in events if e.get("t") not in ("CANDLE",)]
        slots = {0: "OK", 2*GRID: "OK"}
        td, j, r1, r2 = make_case(events, slots, missing=[GRID])
        self.addCleanup(td.cleanup)
        summary, primary, _ = BUILDER.build(j, r1, r2)
        self.assertEqual(len(primary), 3)
        self.assertEqual(primary[1], [1, "NONE", "", ""])
        self.assertEqual(summary["N_missing"], 1)

    def test_pending_outcome_blocks_csv_eligibility(self):
        summary, primary, _ = self.run_build(
            base_events(outcome=None), {0: "OK"})
        self.assertEqual(primary[0][1], "PENDING")
        self.assertEqual(summary["N_pending"], 1)

    def test_hard_verifier_finding_marks_registry_invalid(self):
        summary, _, _ = self.run_build(
            base_events(), {0: "OK"}, hard=["BAD_EVENT"])
        self.assertFalse(summary["registry_ok"])
        self.assertIn("BAD_EVENT", summary["hard_findings"])

    def test_verifier_disagreement_fails_closed(self):
        td, journal, r1, r2 = make_case(base_events(), {0: "OK"})
        self.addCleanup(td.cleanup)
        with open(r2, "w", encoding="utf-8") as f:
            json.dump({
                "verdict": "PASS", "findings": [], "hard": [], "soft": [],
                "n_events": 8, "head_hex": "wrong", "slots": {"0": "LATE"},
                "missing": [],
            }, f)
        with self.assertRaises(BUILDER.BuildError):
            BUILDER.build(journal, r1, r2)

    def test_missing_prior_candles_yield_no_control(self):
        summary, primary, control = self.run_build(
            base_events(prior=False), {0: "OK"})
        self.assertEqual(primary[0][1], "EVAL")
        self.assertEqual(control[0][-1], 0)

    def test_r3_1_hard_finding_is_preserved(self):
        summary, _, _ = self.run_build(
            base_events(status="NONE", outcome="NO_PRICE"),
            {0: "OK"}, hard=["OUTCOME_FOR_NONE_SLOT"])
        self.assertFalse(summary["registry_ok"])
        self.assertIn("OUTCOME_FOR_NONE_SLOT", summary["hard_findings"])
        self.assertNotIn("VERIFIER_HARD_LIST_MISMATCH", summary["hard_findings"])

    def test_non_object_verifier_report_is_controlled_error(self):
        td, journal, r1, r2 = make_case(base_events(), {0: "OK"})
        self.addCleanup(td.cleanup)
        with open(r2, "w", encoding="utf-8") as f:
            json.dump([], f)
        with self.assertRaises(BUILDER.BuildError):
            BUILDER.build(journal, r1, r2)

    def test_duplicate_missing_entries_are_rejected(self):
        td, journal, r1, r2 = make_case(base_events(), {0: "OK"}, missing=[0, 0])
        self.addCleanup(td.cleanup)
        with self.assertRaises(BUILDER.BuildError):
            BUILDER.build(journal, r1, r2)

    def test_implausibly_large_grid_is_rejected_before_allocation(self):
        far = 100_000 * GRID
        events = base_events(tau=0, outcome=None)
        events.extend(base_events(tau=far, outcome=None)[1:])
        events = [e for e in events if e.get("t") != "CANDLE"]
        td, journal, r1, r2 = make_case(events, {0: "OK", far: "OK"})
        self.addCleanup(td.cleanup)
        with self.assertRaisesRegex(BUILDER.BuildError, "safety limit"):
            BUILDER.build(journal, r1, r2)




if __name__ == "__main__":
    unittest.main()
