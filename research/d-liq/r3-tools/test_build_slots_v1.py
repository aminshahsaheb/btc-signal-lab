import contextlib
import hashlib
import importlib.util
import io
import json
import os
import tempfile
import unittest
from unittest import mock

HERE = os.path.dirname(__file__)
SPEC = importlib.util.spec_from_file_location(
    "build_slots_v1", os.path.join(HERE, "build_slots_v1.py"))
BUILDER = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(BUILDER)

GRID = BUILDER.GRID_MS


def canonical(ev):
    return json.dumps(ev, sort_keys=True, separators=(",", ":"), ensure_ascii=True).encode("ascii")


def make_case(events, slot_map=None, missing=None, hard=None, verify_time_ms=0):
    td = tempfile.TemporaryDirectory()
    journal = os.path.join(td.name, "journal.jsonl")
    report1 = os.path.join(td.name, "primary.json")
    report2 = os.path.join(td.name, "independent.json")
    lines = []
    normalized = []
    heads = [hashlib.sha256(BUILDER.GENESIS).digest()]
    head = hashlib.sha256(BUILDER.GENESIS).digest()
    for n, ev in enumerate(events, 1):
        ev = dict(ev)
        ev["seq"] = n
        if ev.get("t") == "CHECKPOINT":
            anchored_seq = ev.get("anchored_seq")
            if isinstance(anchored_seq, int) and 0 <= anchored_seq < n:
                hx = heads[anchored_seq].hex()
                ev["anchored_head"] = hx
                ev["receipt"]["head"] = hx
                ev["receipt"]["seq"] = anchored_seq
        line = canonical(ev)
        lines.append(line)
        head = hashlib.sha256(head + line).digest()
        heads.append(head)
        normalized.append(ev)
    with open(journal, "wb") as f:
        f.write(b"\n".join(lines) + (b"\n" if lines else b""))
    anchor_path = os.path.join(td.name, "anchor.json")
    entries = []
    for ev in normalized:
        if ev.get("t") == "CHECKPOINT":
            rc = ev["receipt"]
            entries.append({key: rc[key] for key in (
                "index", "seq", "head", "anchor_id", "time_ms",
                "time_resolution_ms", "time_uncertainty_ms")})
    with open(anchor_path, "w", encoding="utf-8") as f:
        json.dump({"journal_id": "synthetic", "verify_time_ms": verify_time_ms,
                   "entries": entries}, f, sort_keys=True)
    reports = list(BUILDER.run_pinned_verifiers(journal, anchor_path)[:2])
    for report in reports:
        if slot_map is not None:
            report["slots"] = {str(k): v for k, v in slot_map.items()}
        if missing is not None:
            report["missing"] = list(missing)
        if hard:
            report["hard"] = sorted(hard)
            report["verdict"] = "FAIL"
            report["findings"].extend(
                [[name, 1, "synthetic test finding"] for name in hard])
    for p, report in zip((report1, report2), reports):
        with open(p, "w", encoding="utf-8") as f:
            json.dump(report, f, sort_keys=True)
    return td, journal, report1, report2


def base_events(tau=0, status="VALID", side=1, outcome="EVAL", prior=True):
    empty_sha = hashlib.sha256(b"").hexdigest()
    events = [{"t": "SESSION", "rec_ms": 1, "session_id": "test"}]
    if prior:
        events.extend([
            {"t": "CANDLE", "rec_ms": 2, "open_time_ms": tau-900000,
             "open": "100", "recv_ms": tau-899000, "raw_b64": "", "sha256": empty_sha},
            {"t": "CANDLE", "rec_ms": 3, "open_time_ms": tau,
             "open": "101", "recv_ms": tau+1000, "raw_b64": "", "sha256": empty_sha},
        ])
    slot_seq = len(events) + 1
    events.append({
        "t": "SLOT", "rec_ms": 4, "tau_ms": tau, "status": status,
        "reasons": [], "primary_conn": 1, "N_total": 1, "N_BUY": 1,
        "N_SELL": 0, "sumW_BUY": "1", "sumW_SELL": "0", "side": side,
        "malformed_voids": 0, "ledger": {}, "n_messages": 1, "X_sn": "1",
    })
    events.append({
        "t": "CHECKPOINT", "rec_ms": 5, "anchored_seq": slot_seq,
        "anchored_head": "a"*64, "receipt": {
            "anchor_id": "mock", "index": 1, "seq": 1, "head": "a"*64,
            "time_ms": 1, "time_resolution_ms": 1, "time_uncertainty_ms": 0,
        },
    })
    if outcome == "EVAL":
        events.extend([
            {"t": "CANDLE", "rec_ms": 6, "open_time_ms": tau+300000,
             "open": "101", "recv_ms": tau+301000, "raw_b64": "", "sha256": empty_sha},
            {"t": "CANDLE", "rec_ms": 7, "open_time_ms": tau+300000+14400000,
             "open": "101.99999016281329", "recv_ms": tau+14701000, "raw_b64": "", "sha256": empty_sha},
        ])
        outcome_seq = len(events) + 1
        events.append({"t": "OUTCOME", "rec_ms": 8, "tau_ms": tau, "status": "EVAL",
                       "entry_open_ms": tau+300000, "exit_open_ms": tau+14700000,
                       "entry_price": "101", "exit_price": "101.99999016281329", "r_bps": "98.522"})
        events.append({"t": "CHECKPOINT", "rec_ms": 9, "anchored_seq": outcome_seq,
                       "anchored_head": "b"*64, "receipt": {
                           "anchor_id": "mock", "index": 2, "seq": 2, "head": "b"*64,
                           "time_ms": 2, "time_resolution_ms": 1, "time_uncertainty_ms": 0,
                       }})
    elif outcome == "NO_PRICE":
        outcome_seq = len(events) + 1
        events.append({"t": "OUTCOME", "rec_ms": 8, "tau_ms": tau, "status": "NO_PRICE"})
        events.append({"t": "CHECKPOINT", "rec_ms": 9, "anchored_seq": outcome_seq,
                       "anchored_head": "b"*64, "receipt": {
                           "anchor_id": "mock", "index": 2, "seq": 2, "head": "b"*64,
                           "time_ms": 2, "time_resolution_ms": 1, "time_uncertainty_ms": 0,
                       }})
    return events


class BuilderTests(unittest.TestCase):
    def run_build(self, events, slots=None, missing=None, hard=None, verify_time_ms=0):
        td, journal, r1, r2 = make_case(events, slots, missing, hard, verify_time_ms)
        self.addCleanup(td.cleanup)
        return BUILDER._build_diagnostics(
            journal, r1, r2, r1.replace("primary.json", "anchor.json"))

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
        events = [e for e in base_events(outcome=None) if e.get("t") != "CHECKPOINT"]
        summary, primary, control = self.run_build(
            events, {0: "UNANCHORED"}, verify_time_ms=BUILDER.ENTRY_DELAY_MS+1)
        self.assertEqual(primary, [[0, "NONE", "", ""]])
        self.assertEqual(summary["N_unanch"], 1)
        self.assertEqual(summary["N_none"], 1)

    def test_none_signal_is_none(self):
        summary, primary, _ = self.run_build(
            base_events(status="NONE", outcome=None), {0: "OK"})
        self.assertEqual(primary, [[0, "NONE", "", ""]])
        self.assertEqual(summary["N_unanch"], 0)

    def test_none_signal_with_late_anchor_is_unanchored_but_not_counted(self):
        events = [e for e in base_events(status="NONE", outcome=None)
                  if e.get("t") != "CHECKPOINT"]
        summary, primary, _ = self.run_build(
            events, {0: "UNANCHORED"}, verify_time_ms=BUILDER.ENTRY_DELAY_MS+1)
        self.assertEqual(primary, [[0, "NONE", "", ""]])
        self.assertEqual(summary["N_unanch"], 0)
        self.assertEqual(summary["diagnostics"][0]["reason"], "UNANCHORED")

    def test_missing_grid_point_is_synthesized(self):
        first = base_events(tau=0, outcome=None, prior=False)
        second = base_events(tau=2*GRID, outcome=None, prior=False)
        events = [first[0], first[1], first[2], second[1], second[2]]
        # The second checkpoint covers the second SLOT at its new sequence.
        events[2]["anchored_seq"] = 2
        events[4]["anchored_seq"] = 4
        events[4]["receipt"]["index"] = 2
        slots = {0: "OK", 2*GRID: "OK"}
        td, j, r1, r2 = make_case(events, slots, missing=[GRID])
        self.addCleanup(td.cleanup)
        summary, primary, _ = BUILDER._build_diagnostics(
            j, r1, r2, r1.replace("primary.json", "anchor.json"))
        self.assertEqual(len(primary), 3)
        self.assertEqual(primary[1], [1, "NONE", "", ""])
        self.assertEqual(summary["N_missing"], 1)

    def test_unanchored_outcome_blocks_csv_eligibility(self):
        events = base_events(outcome="EVAL")
        # The final checkpoint is the only one that covers the OUTCOME.
        events.pop()
        summary, primary, _ = self.run_build(events, {0: "OK"})
        self.assertEqual(primary[0][1], "PENDING")
        self.assertEqual(summary["N_pending"], 1)
        self.assertEqual(summary["diagnostics"][0]["reason"], "PENDING_OUTCOME_ANCHOR")

    def test_checkpoint_cannot_claim_a_future_sequence(self):
        events = base_events(outcome="EVAL")
        checkpoints = [e for e in events if e.get("t") == "CHECKPOINT"]
        checkpoints[0]["anchored_seq"] = 10_000
        summary, _, _ = self.run_build(events)
        self.assertFalse(summary["registry_ok"])
        self.assertIn("BUILDER_BAD_CHECKPOINT_COVERAGE", summary["hard_findings"])

    def test_checkpoint_coverage_cannot_move_backwards(self):
        events = base_events(outcome="EVAL")
        checkpoints = [e for e in events if e.get("t") == "CHECKPOINT"]
        checkpoints[1]["anchored_seq"] = 3
        summary, primary, _ = self.run_build(events)
        self.assertFalse(summary["registry_ok"])
        self.assertIn("BUILDER_CHECKPOINT_COVERAGE_REGRESSION", summary["hard_findings"])
        self.assertEqual(primary[0][1], "PENDING")

    def test_verifier_slot_map_must_match_journal_exactly(self):
        td, journal, r1, r2 = make_case(base_events(), {0: "OK", GRID: "OK"})
        self.addCleanup(td.cleanup)
        with self.assertRaisesRegex(BUILDER.BuildError, "pinned verifier"):
            BUILDER._build_diagnostics(
                journal, r1, r2, r1.replace("primary.json", "anchor.json"))

    def test_pending_outcome_blocks_csv_eligibility(self):
        summary, primary, _ = self.run_build(
            base_events(outcome=None), {0: "OK"})
        self.assertEqual(primary[0][1], "PENDING")
        self.assertEqual(summary["N_pending"], 1)

    def test_hard_verifier_finding_marks_registry_invalid(self):
        events = base_events()
        next(e for e in events if e.get("t") == "SLOT")["side"] = "invalid"
        summary, _, _ = self.run_build(events)
        self.assertFalse(summary["registry_ok"])
        self.assertIn("BAD_EVENT", summary["hard_findings"])

    def test_public_build_refuses_hard_findings_and_pending_rows(self):
        events = base_events()
        next(e for e in events if e.get("t") == "SLOT")["side"] = "invalid"
        td, journal, r1, r2 = make_case(events)
        self.addCleanup(td.cleanup)
        with self.assertRaisesRegex(BUILDER.BuildError, "analysis ineligible"):
            BUILDER.build(journal, r1, r2, r1.replace("primary.json", "anchor.json"))

        td2, journal2, r12, r22 = make_case(
            base_events(outcome=None), {0: "OK"})
        self.addCleanup(td2.cleanup)
        with self.assertRaisesRegex(BUILDER.BuildError, "analysis ineligible"):
            BUILDER.build(journal2, r12, r22, r12.replace("primary.json", "anchor.json"))

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
            BUILDER.build(journal, r1, r2, r1.replace("primary.json", "anchor.json"))

    def test_forged_report_same_head_and_event_count_fails_closed(self):
        td, journal, r1, r2 = make_case(base_events(), {0: "OK", GRID: "OK"})
        self.addCleanup(td.cleanup)
        with open(r2, encoding="utf-8") as f:
            report = json.load(f)
        # Keep the verifier's superficial identity fields while forging its result.
        report["slots"] = {"0": "LATE", str(GRID): "OK"}
        report["verdict"] = "PASS"
        with open(r2, "w", encoding="utf-8") as f:
            json.dump(report, f, sort_keys=True)
        with self.assertRaisesRegex(BUILDER.BuildError, "pinned verifier"):
            BUILDER.build(journal, r1, r2, r1.replace("primary.json", "anchor.json"))

    def test_missing_prior_candles_yield_no_control(self):
        summary, primary, control = self.run_build(
            base_events(prior=False), {0: "OK"})
        self.assertEqual(primary[0][1], "EVAL")
        self.assertEqual(control[0][-1], 0)

    def test_r3_1_hard_finding_is_preserved(self):
        summary, _, _ = self.run_build(
            base_events(status="NONE", outcome="NO_PRICE"),
            {0: "OK"})
        self.assertFalse(summary["registry_ok"])
        self.assertIn("OUTCOME_FOR_NONE_SLOT", summary["hard_findings"])
        self.assertNotIn("VERIFIER_HARD_LIST_MISMATCH", summary["hard_findings"])

    def test_non_object_verifier_report_is_controlled_error(self):
        td, journal, r1, r2 = make_case(base_events(), {0: "OK"})
        self.addCleanup(td.cleanup)
        with open(r2, "w", encoding="utf-8") as f:
            json.dump([], f)
        with self.assertRaises(BUILDER.BuildError):
            BUILDER.build(journal, r1, r2, r1.replace("primary.json", "anchor.json"))

    def test_duplicate_missing_entries_are_rejected(self):
        td, journal, r1, r2 = make_case(base_events(), {0: "OK"}, missing=[0, 0])
        self.addCleanup(td.cleanup)
        with self.assertRaises(BUILDER.BuildError):
            BUILDER.build(journal, r1, r2, r1.replace("primary.json", "anchor.json"))

    def test_failed_cli_run_removes_stale_analysis_outputs(self):
        td, journal, r1, r2 = make_case(base_events(outcome=None), {0: "OK"})
        self.addCleanup(td.cleanup)
        prefix = os.path.join(td.name, "result")
        for path in (prefix + ".csv", prefix + "_with_prior.csv", prefix + ".summary.json"):
            with open(path, "w", encoding="utf-8") as f:
                f.write("stale output\\n")

        argv = ["build_slots_v1.py", journal, r1, r2,
                r1.replace("primary.json", "anchor.json"), "--out-prefix", prefix]
        with mock.patch.object(BUILDER.sys, "argv", argv):
            with contextlib.redirect_stdout(io.StringIO()), contextlib.redirect_stderr(io.StringIO()):
                rc = BUILDER.main()

        self.assertEqual(rc, 2)
        self.assertFalse(os.path.exists(prefix + ".csv"))
        self.assertFalse(os.path.exists(prefix + "_with_prior.csv"))
        with open(prefix + ".summary.json", encoding="utf-8") as f:
            summary = json.load(f)
        self.assertFalse(summary["analysis_csv_written"])
        self.assertEqual(summary["N_pending"], 1)

    def test_build_error_also_removes_stale_outputs(self):
        td, journal, r1, r2 = make_case(base_events(), {0: "OK"})
        self.addCleanup(td.cleanup)
        with open(r2, "w", encoding="utf-8") as f:
            json.dump({"not": "a verifier report"}, f)
        prefix = os.path.join(td.name, "result")
        for suffix in (".csv", "_with_prior.csv", ".summary.json"):
            with open(prefix + suffix, "w", encoding="utf-8") as f:
                f.write("stale output\\n")

        argv = ["build_slots_v1.py", journal, r1, r2,
                r1.replace("primary.json", "anchor.json"), "--out-prefix", prefix]
        with mock.patch.object(BUILDER.sys, "argv", argv):
            with contextlib.redirect_stdout(io.StringIO()), contextlib.redirect_stderr(io.StringIO()):
                rc = BUILDER.main()

        self.assertEqual(rc, 2)
        for suffix in (".csv", "_with_prior.csv", ".summary.json"):
            self.assertFalse(os.path.exists(prefix + suffix))

    def test_implausibly_large_grid_is_rejected_before_allocation(self):
        far = 100_000 * GRID
        events = base_events(tau=0, outcome=None)
        events.extend(base_events(tau=far, outcome=None)[1:])
        events = [e for e in events if e.get("t") != "CANDLE"]
        checkpoints = [e for e in events if e.get("t") == "CHECKPOINT"]
        checkpoints[1]["anchored_seq"] = 4
        checkpoints[1]["receipt"]["index"] = 2
        td, journal, r1, r2 = make_case(events, {0: "OK", far: "OK"})
        self.addCleanup(td.cleanup)
        with self.assertRaisesRegex(BUILDER.BuildError, "safety limit"):
            BUILDER.build(journal, r1, r2, r1.replace("primary.json", "anchor.json"))




if __name__ == "__main__":
    unittest.main()
