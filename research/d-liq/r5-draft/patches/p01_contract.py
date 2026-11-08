"""r5 patch 1: contract text. G-2 (GPT audit 2026-11-07, point B): the SLOT replay cannot be skipped silently."""
import os
import sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from _lib import replace_once

root = sys.argv[1]
C = "indep_verifier/JOURNAL_CONTRACT_v2.md"

replace_once(root, C, "# D-LIQ evidence journal -- contract v2, revision r4-draft (verifier-facing;",
             "# D-LIQ evidence journal -- contract v2, revision r5-draft (verifier-facing;")
replace_once(root, C, "The event format and the genesis string are unchanged.\n",
             "The event format and the genesis string are unchanged.\n\n"
             "REVISION r5 (answer to the second GPT audit, 2026-11-07, point B / G-2): the SLOT replay can no longer be skipped silently. New section 7.6; new hard finding `REPLAY_NOT_RUN`; new verdict `INCOMPLETE`;\n"
             "every report carries `replayed` and `analysis_eligible`. Sections 1-6, the event format and the genesis string are unchanged.\n")

replace_once(root, C, "    SLOT_MISMATCH, SLOT_EARLY_WRITE (the last two only when the replay layer is run).\n",
             "    SLOT_MISMATCH, SLOT_EARLY_WRITE (the last two only when the replay layer is run), REPLAY_NOT_RUN (r5; 7.6).\n")

replace_once(root, C, '`verdict` ("FAIL" if at least one hard finding else "PASS")',
             '`verdict` ("FAIL" if at least one hard finding other than REPLAY_NOT_RUN exists; else "INCOMPLETE" if REPLAY_NOT_RUN is present; else "PASS")')
replace_once(root, C, "and -- only for an implementation of section 7 -- `replayed` (bool: whether the replay layer ran). A consumer that requires the replay (7.1) MUST refuse a report without `replayed: true`.",
             "`replayed` (bool: whether the replay layer ran; r5: reported by EVERY verifier) and `analysis_eligible` (bool; r5: true only if `verdict` is \"PASS\" and `replayed` is true). A consumer that requires the replay (7.1, 7.6) MUST refuse a report without `replayed: true`.")

replace_once(root, C, "  - `where` = 0: NO_CHECKPOINT.\n", "  - `where` = 0: NO_CHECKPOINT, REPLAY_NOT_RUN.\n")

replace_once(root, C, "## 8. Result\n",
             "7.6 Replay is not optional (r5; GPT audit 2026-11-07, G-2). A verifier that implements section 7 MUST run the replay by default. Disabling it is allowed only as an explicit opt-out for fixture-only tests, and then:\n"
             "  * `replayed` MUST be false and `analysis_eligible` MUST be false;\n"
             "  * the hard finding `REPLAY_NOT_RUN` (where = 0) MUST be reported;\n"
             "  * `verdict` MUST be \"FAIL\" if any other hard finding exists and \"INCOMPLETE\" otherwise. It MUST NEVER be \"PASS\".\n"
             "  The opt-out is fail-closed: the replay runs only when the caller passes exactly the boolean true; any other value (None, 0, 1, a string) is treated as an opt-out.\n"
             "  `analysis_eligible` is true only if `verdict` is \"PASS\" and `replayed` is true; \"PASS\" therefore means that sections 1-6 AND the replay completed without a hard finding.\n"
             "  A verifier that does NOT implement section 7 (today: the partially independent verifier of this package) MUST report `replayed: false`, `analysis_eligible: false` and the hard finding `REPLAY_NOT_RUN` on every run;\n"
             "  its verdict is therefore \"FAIL\" or \"INCOMPLETE\" and never \"PASS\". This is what keeps its output from being mistaken for a complete verification.\n"
             "  A consumer (the slots builder) MUST NOT accept a primary report without `replayed: true`, MUST NOT mark a build analysis-eligible unless every report it consumed has `replayed: true`,\n"
             "  and MUST NOT use a report without `analysis_eligible: true` for the analysis. While no independent replay exists, no build is analysis-eligible.\n"
             "  A replay over a journal without any reference SLOT is vacuous (`replayed: true`, nothing was compared); the consumer's own checks (missing grid points, N_eval) are what expose an empty analysis.\n\n"
             "## 8. Result\n")
print("p01 ok")
