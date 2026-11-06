"""r4 patch 04: partially independent verifier -- per-OUTCOME coverage (contract 6.4). Integrator patch (not written by the independent author). usage: python3 p04_indep.py <tree>"""
import sys
tree = sys.argv[1]
p = tree + "/indep_verifier/verify_indep.py"
s = open(p, encoding="utf-8").read()
def rep(a, b):
    global s
    assert s.count(a) == 1, (a[:90], s.count(a))
    s = s.replace(a, b)
rep('''    "OUTCOME_UNLINKED", "CANDLE_CONFLICT", "CANDLE_NOT_LIVE", "SLOT_MISMATCH",
))''','''    "OUTCOME_UNLINKED", "CANDLE_CONFLICT", "CANDLE_NOT_LIVE", "SLOT_MISMATCH",
    "SLOT_EARLY_WRITE",  # r4 integrator patch: name of the replay layer (contract 7.3/7.4); this verifier does NOT run the replay
))''')
rep('SOFT_NAMES = frozenset(("SLOT_LATE_ANCHOR", "SLOT_UNANCHORED", "SLOT_MISSING"))','SOFT_NAMES = frozenset(("SLOT_LATE_ANCHOR", "SLOT_UNANCHORED", "SLOT_MISSING", "OUTCOME_UNCOVERED"))   # r4 integrator patch: OUTCOME_UNCOVERED (contract 6.4)')
rep('''    seen_outcome = {}
    for r in valid_recs:''','''    seen_outcome = {}
    outcomes = {}  # r4 integrator patch (contract 6.4): reference OUTCOME of each tau -> COVERED / UNCOVERED
    for r in valid_recs:''')
rep('''        else:
            seen_outcome[tau] = j
        i = ref_slot.get(tau)''','''        else:
            seen_outcome[tau] = j
            if any(c > j and cev["anchored_seq"] >= j for c, cev in ckpts):
                outcomes[tau] = "COVERED"
            else:
                outcomes[tau] = "UNCOVERED"
                add("OUTCOME_UNCOVERED", tau, "no valid CHECKPOINT after line %d anchors the OUTCOME" % j)
        i = ref_slot.get(tau)''')
rep('''        "slots": slots,
        "missing": missing,
    }''','''        "slots": slots,
        "missing": missing,
        "outcomes": outcomes,
    }''')
open(p, "w", encoding="utf-8").write(s)
print("ok")
