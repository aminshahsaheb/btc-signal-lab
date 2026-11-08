"""r5 patch 2: primary verifier. replay_slots defaults to True; anything but exactly True is an opt-out that yields REPLAY_NOT_RUN / INCOMPLETE / analysis_eligible=false."""
import os
import sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from _lib import replace_once

root = sys.argv[1]
P = "src/dliq_journal_verify_v2.py"

replace_once(root, P, "the slots builder always calls verify(..., replay_slots=True)) imports dliq_msg_contract_v1 lazily.",
             "the slots builder always calls verify(..., replay_slots=True); r5: True is also the default) imports dliq_msg_contract_v1 lazily.")
replace_once(root, P, "verify(path, anchor, journal_id, verify_time_ms, replay_slots=False) -> dict(verdict, findings, hard, soft, n_events, head_hex, slots, missing, outcomes, replayed)\n",
             "verify(path, anchor, journal_id, verify_time_ms, replay_slots=True) -> dict(verdict, findings, hard, soft, n_events, head_hex, slots, missing, outcomes, replayed, analysis_eligible)\n"
             "r5 (contract 7.6, GPT audit G-2): the replay runs only when replay_slots is exactly True. Otherwise: hard REPLAY_NOT_RUN (where 0), replayed=False, analysis_eligible=False, verdict INCOMPLETE (or FAIL if another hard finding exists) -- never PASS.\n")
replace_once(root, P, '        "SLOT_EARLY_WRITE"}\nSOFT =', '        "SLOT_EARLY_WRITE", "REPLAY_NOT_RUN"}\nSOFT =')
replace_once(root, P, "def verify(path, anchor, journal_id, verify_time_ms, replay_slots=False):", "def verify(path, anchor, journal_id, verify_time_ms, replay_slots=True):")
replace_once(root, P, "    if replay_slots:\n        import dliq_msg_contract_v1 as MC\n", "    if replay_slots is True:\n        import dliq_msg_contract_v1 as MC\n")
replace_once(root, P,
             '                F(["SLOT_EARLY_WRITE", i, "SLOT written at rec_ms %d < tau_ms + 10 s = %d" % (ev["rec_ms"], tau + 10_000)])\n'
             '    hard = sorted(set(f[0] for f in findings if f[0] in HARD))\n',
             '                F(["SLOT_EARLY_WRITE", i, "SLOT written at rec_ms %d < tau_ms + 10 s = %d" % (ev["rec_ms"], tau + 10_000)])\n'
             '    else:\n'
             '        F(["REPLAY_NOT_RUN", 0, "the SLOT replay was not run (replay_slots is not exactly True); this report is not evidence for the analysis (contract 7.6)"])\n'
             '    hard = sorted(set(f[0] for f in findings if f[0] in HARD))\n')
replace_once(root, P,
             '    return {"verdict": "FAIL" if hard else "PASS", "findings": findings, "hard": hard, "soft": soft, "n_events": N, "head_hex": heads[-1].hex(),\n'
             '            "slots": slots, "missing": missing, "outcomes": outcomes, "replayed": bool(replay_slots)}\n',
             '    replayed = replay_slots is True\n'
             '    verdict = "FAIL" if any(h != "REPLAY_NOT_RUN" for h in hard) else ("INCOMPLETE" if "REPLAY_NOT_RUN" in hard else "PASS")\n'
             '    return {"verdict": verdict, "findings": findings, "hard": hard, "soft": soft, "n_events": N, "head_hex": heads[-1].hex(),\n'
             '            "slots": slots, "missing": missing, "outcomes": outcomes, "replayed": replayed, "analysis_eligible": verdict == "PASS" and replayed}\n')
print("p02 ok")
