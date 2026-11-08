"""r5 patch 3: partially independent verifier. It has no SLOT replay, so it reports REPLAY_NOT_RUN on every run and can never return PASS (contract 7.6)."""
import os
import sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from _lib import replace_once

root = sys.argv[1]
I = "indep_verifier/verify_indep.py"

replace_once(root, I, '    "SLOT_EARLY_WRITE",  # r4 integrator patch: name of the replay layer (contract 7.3/7.4); this verifier does NOT run the replay\n))',
             '    "SLOT_EARLY_WRITE",  # r4 integrator patch: name of the replay layer (contract 7.3/7.4); this verifier does NOT run the replay\n'
             '    "REPLAY_NOT_RUN",  # r5 integrator patch (contract 7.6): reported on EVERY run of this verifier\n))')
replace_once(root, I, "    # ---- 8.2 result ----------------------------------------------------------------------------\n",
             "    # ---- 7.6 this verifier implements no SLOT replay (r5 integrator patch) -------------------------\n"
             '    add("REPLAY_NOT_RUN", 0, "this verifier implements no SLOT replay; its report is not a complete verification (contract 7.6)")\n\n'
             "    # ---- 8.2 result ----------------------------------------------------------------------------\n")
replace_once(root, I, '        "verdict": "FAIL" if hard else "PASS",\n',
             '        "verdict": "FAIL" if any(h != "REPLAY_NOT_RUN" for h in hard) else "INCOMPLETE",   # r5: never PASS (no replay)\n')
replace_once(root, I, '        "outcomes": outcomes,\n    }\n', '        "outcomes": outcomes,\n        "replayed": False,\n        "analysis_eligible": False,\n    }\n')
print("p03 ok")
