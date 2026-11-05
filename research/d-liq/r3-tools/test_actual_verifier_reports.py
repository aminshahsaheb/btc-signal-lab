"""Integration tests against JSON reports emitted by the immutable r3.1 verifier executables.

Archive SHA-256: 4d3faaae13e0263ac1f422a3b6d88904d70057b4bb5271029c1ce5cc9d194ec2
Protocol SHA-256: 5c05a15de7addd55cade7617fcdcaea570aad82b61c0b16c95d14024fc649948
Writer SHA-256: 51f0996f815466cb977bd46a6e5891b1f20f7fe42dc8de5cfcc494d54c59d06f
Primary verifier SHA-256: 816f8d9fd37cc3cfa9001badc6af5a9a69ed025f41ba32a4e5be4b4ef9cbffa5
Independent verifier SHA-256: f967c77c825f278961ab361a2d844a561d886c14a57c51938901d87bc84b0650
All fixtures use a local MockAnchor; no external service was contacted.
"""
import gzip
import importlib.util
import json
import os
import tempfile
import unittest

HERE = os.path.dirname(__file__)
SPEC = importlib.util.spec_from_file_location("build_slots_v1", os.path.join(HERE, "build_slots_v1.py"))
BUILDER = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(BUILDER)
FIXTURE_FILE = os.path.join(HERE, "fixtures", "r3_1_actual_verifier_fixtures.json.gz")


def run_fixture(name):
    with gzip.open(FIXTURE_FILE, "rt", encoding="utf-8") as stream:
        case = json.load(stream)[name]
    with tempfile.TemporaryDirectory() as td:
        journal = os.path.join(td, "journal.jsonl")
        primary = os.path.join(td, "primary.json")
        independent = os.path.join(td, "independent.json")
        with open(journal, "w", encoding="utf-8") as f:
            f.write(case["journal"])
        for path, key in ((primary, "primary"), (independent, "independent")):
            with open(path, "w", encoding="utf-8") as f:
                json.dump(case[key], f)
        return BUILDER._build_diagnostics(journal, primary, independent)


class ActualVerifierReportIntegrationTests(unittest.TestCase):
    def test_anchored_outcome_is_eligible(self):
        summary, primary, control = run_fixture("anchored_outcome")
        self.assertTrue(summary["registry_ok"])
        self.assertEqual(summary["verifier_verdicts"], ["PASS", "PASS"])
        self.assertEqual(summary["N_eval"], 1)
        self.assertEqual(summary["N_pending"], 0)
        self.assertEqual(primary, [[0, "EVAL", 1, "49.87541511038968"]])
        self.assertEqual(control, [[0, "EVAL", 1, "49.87541511038968", 0]])

    def test_actual_verifiers_pass_but_unanchored_outcome_tail_stays_pending(self):
        summary, primary, _ = run_fixture("unanchored_outcome_tail")
        self.assertEqual(summary["verifier_verdicts"], ["PASS", "PASS"])
        self.assertTrue(summary["registry_ok"])
        self.assertEqual(summary["N_pending"], 1)
        self.assertEqual(summary["N_eval"], 0)
        self.assertEqual(primary[0][1], "PENDING")
        self.assertEqual(summary["diagnostics"][0]["reason"], "PENDING_OUTCOME_ANCHOR")


if __name__ == "__main__":
    unittest.main()
