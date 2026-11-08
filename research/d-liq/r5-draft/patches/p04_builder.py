"""r5 patch 4: slots builder (contract 7.6). Reports must carry the replay markers; a primary that did not replay is a hard failure; the independent verifier's
REPLAY_NOT_RUN is expected (it has no replay) but surfaces as independent_replayed=false and analysis_eligible=false. The verifier pins are refreshed by assemble_r5.py
after the verifier copies are made (see PIN_UPDATES there)."""
import os
import sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from _lib import replace_once

root = sys.argv[1]
B = "builder/build_slots_v2.py"

replace_once(root, B, '    "OUTCOME_UNLINKED", "CANDLE_CONFLICT", "CANDLE_NOT_LIVE", "SLOT_MISMATCH", "SLOT_EARLY_WRITE",\n}\n',
             '    "OUTCOME_UNLINKED", "CANDLE_CONFLICT", "CANDLE_NOT_LIVE", "SLOT_MISMATCH", "SLOT_EARLY_WRITE", "REPLAY_NOT_RUN",\n}\n')
replace_once(root, B, '    if report.get("verdict") not in ("PASS", "FAIL"):\n        raise BuildError("verifier report %s has an invalid verdict" % path)\n',
             '    if report.get("verdict") not in ("PASS", "FAIL", "INCOMPLETE"):\n        raise BuildError("verifier report %s has an invalid verdict" % path)\n'
             '    if not isinstance(report.get("replayed"), bool) or not isinstance(report.get("analysis_eligible"), bool):\n'
             '        raise BuildError("verifier report %s lacks the replay markers (`replayed`, `analysis_eligible`): produced by a pre-r5 verifier?" % path)\n')
replace_once(root, B,
             '    for report in (primary, independent):\n'
             '        expected = "FAIL" if report.get("hard") else "PASS"\n'
             '        if report.get("verdict") != expected:\n'
             '            hard.add("VERIFIER_REPORT_INCONSISTENT")\n',
             '    for report in (primary, independent):\n'
             '        report_hard = set(report.get("hard", []))\n'
             '        expected = "FAIL" if report_hard - {"REPLAY_NOT_RUN"} else ("INCOMPLETE" if "REPLAY_NOT_RUN" in report_hard else "PASS")\n'
             '        if report.get("verdict") != expected:\n'
             '            hard.add("VERIFIER_REPORT_INCONSISTENT")\n'
             '        if report.get("analysis_eligible") is not (expected == "PASS" and report.get("replayed") is True):\n'
             '            hard.add("VERIFIER_REPORT_INCONSISTENT")\n'
             '        if (report.get("replayed") is True) == ("REPLAY_NOT_RUN" in report_hard):\n'
             '            hard.add("VERIFIER_REPORT_INCONSISTENT")                       # replayed XOR REPLAY_NOT_RUN\n'
             '    # r5 (contract 7.6): the primary MUST have replayed; the independent verifier has no replay implementation, so its REPLAY_NOT_RUN is expected and is NOT a registry\n'
             '    # failure -- it is surfaced as independent_replayed=false and keeps analysis_eligible=false below.\n'
             '    if primary.get("replayed") is not True or "REPLAY_NOT_RUN" in set(primary.get("hard", [])):\n'
             '        hard.add("PRIMARY_REPLAY_NOT_RUN")\n'
             '    independent_replayed = independent.get("replayed") is True\n'
             '    hard.discard("REPLAY_NOT_RUN")\n')
replace_once(root, B, '        "primary_replayed": primary.get("replayed") is True,\n',
             '        "primary_replayed": primary.get("replayed") is True,\n        "independent_replayed": independent_replayed,\n')
replace_once(root, B, '        "registry_ok": not hard,\n',
             '        "registry_ok": not hard,\n'
             '        "independent_replay_required": REQUIRE_INDEPENDENT_REPLAY,\n'
             '        "analysis_eligible": (not hard) and not pending and primary.get("replayed") is True and (independent_replayed or not REQUIRE_INDEPENDENT_REPLAY),\n')
replace_once(root, B, 'MSG_CONTRACT_PATH = os.path.join(os.path.dirname(__file__), "verifiers", "primary", "dliq_msg_contract_v1.py")\n',
             'MSG_CONTRACT_PATH = os.path.join(os.path.dirname(__file__), "verifiers", "primary", "dliq_msg_contract_v1.py")\n'
             '# r5 (GPT audit G-2, most conservative reading): until an independent SLOT replay exists no build is analysis-eligible and no analysis CSV is written.\n'
             '# Flip to False only in the same reviewed change that adds the independent replay (tests patch it to exercise the CSV path).\n'
             'REQUIRE_INDEPENDENT_REPLAY = True\n')
replace_once(root, B, '    if summary["hard_findings"] or summary["N_pending"]:\n        raise BuildError(\n            "analysis ineligible: hard findings=%s; pending slots=%d" %\n            (summary["hard_findings"], summary["N_pending"]))\n',
             '    if summary["hard_findings"] or summary["N_pending"] or not summary["analysis_eligible"]:\n        raise BuildError(\n            "analysis ineligible: hard findings=%s; pending slots=%d; analysis_eligible=%s (independent_replayed=%s, required=%s)" %\n'
             '            (summary["hard_findings"], summary["N_pending"], summary["analysis_eligible"], summary["independent_replayed"], summary["independent_replay_required"]))\n')
replace_once(root, B, '    if summary["hard_findings"] or summary["N_pending"]:\n        print(json.dumps({\n            "registry_ok": summary["registry_ok"],\n',
             '    if summary["hard_findings"] or summary["N_pending"] or not summary["analysis_eligible"]:\n        print(json.dumps({\n            "registry_ok": summary["registry_ok"],\n            "analysis_eligible": summary["analysis_eligible"],\n')
replace_once(root, B, 'print("Refusing analysis CSV: resolve hard findings and pending slots first.", file=sys.stderr)',
             'print("Refusing analysis CSV: resolve hard findings and pending slots first, and every consumed verifier report must have replayed (analysis_eligible=true).", file=sys.stderr)')
replace_once(root, B, '"note": "This builder does not compute a verdict. Do not run analysis unless registry_ok=true and N_pending=0.",',
             '"note": "This builder does not compute a verdict. Do not run analysis unless analysis_eligible=true (registry_ok=true, N_pending=0, every consumed verifier report replayed). '
             'While no independent SLOT replay exists, analysis_eligible is always false.",')
replace_once(root, B, '"builder": "build_slots_v2.py DRAFT (r4 delta)"', '"builder": "build_slots_v2.py DRAFT (r5 delta)"')
print("p04 ok")
