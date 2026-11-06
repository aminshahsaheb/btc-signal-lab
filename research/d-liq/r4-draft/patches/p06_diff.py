"""r4 patch 06: differential harness -- compares `outcomes`, adds covered-outcome bases and OUTCOME-targeted mutations (tamper / omit / move to tail / cut after outcome). usage: python3 p06_diff.py <tree>"""
import sys
tree = sys.argv[1]
p = tree + "/src/diff_test_verifiers.py"
s = open(p, encoding="utf-8").read()
def rep(a, b):
    global s
    assert s.count(a) == 1, (a[:90], s.count(a))
    s = s.replace(a, b)
rep('outcome_before_anchor=False, late_outcome_status="EVAL", invalid_none_outcome=False):', 'outcome_before_anchor=False, late_outcome_status="EVAL", invalid_none_outcome=False, anchor_outcomes=False):')
rep('''            else:
                jr.append("OUTCOME", **outcome_fields)
    now[0] += 5000''','''            else:
                jr.append("OUTCOME", **outcome_fields)
            if anchor_outcomes == "all" or (anchor_outcomes == "alt" and s % 2 == 0):
                now[0] += 1
                jr.checkpoint(an)                       # r4: the OUTCOME is covered (contract 6.4); otherwise it stays in the unanchored tail
    now[0] += 5000''')
rep('''"slots": {str(k): v for k, v in dict(res["slots"]).items()}, "missing": sorted(res["missing"]), "where"''','''"slots": {str(k): v for k, v in dict(res["slots"]).items()}, "missing": sorted(res["missing"]),
            "outcomes": {str(k): v for k, v in dict(res["outcomes"]).items()}, "where"''')
rep('''        bases.append(build(tmp, "nooutcome", nslots=2, outcomes=False))
        bases.append(build(tmp, "outcome_for_none_slot", nslots=1, outcomes=True, invalid_none_outcome=True))''','''        for ns in (1, 2, 3):                            # r4: outcomes covered by their own checkpoint (all / alternating); the loop above leaves them in the unanchored tail
            bases.append(build(tmp, "outcov_all_%d" % ns, nslots=ns, anchor_outcomes="all"))
            bases.append(build(tmp, "outcov_alt_%d" % ns, nslots=ns, anchor_outcomes="alt"))
        bases.append(build(tmp, "nooutcome", nslots=2, outcomes=False))
        bases.append(build(tmp, "outcome_for_none_slot", nslots=1, outcomes=True, invalid_none_outcome=True))
        bases.append(build(tmp, "outcome_for_none_slot_anchored", nslots=2, outcomes=True, invalid_none_outcome=True, anchor_outcomes="all"))''')
rep('''        for k in ("verdict", "head", "n", "slots", "missing"):''','''        for k in ("verdict", "head", "n", "slots", "missing", "outcomes"):''')
# OUTCOME-targeted mutation operators
rep('''"anchor_add", "bool_int", "float_int", "empty_file", "shuffle_receipt", "change_t", "dup_key"])''','''"anchor_add", "bool_int", "float_int", "empty_file", "shuffle_receipt", "change_t", "dup_key",
                         "o_del", "o_tamper", "o_tail", "o_cut", "o_status"])''')
rep('''        i = rng.randrange(len(L)) if L else 0
        try:''','''        i = rng.randrange(len(L)) if L else 0
        if op.startswith("o_"):                       # r4: choose an OUTCOME line (if any)
            oi = [k for k, l in enumerate(L) if b'"t":"OUTCOME"' in l]
            if not oi:
                continue
            i = rng.choice(oi)
        try:''')
rep('''        elif op == "garbage":''','''        elif op == "o_del":
            del L[i]                                  # omit an OUTCOME record
        elif op == "o_tamper":
            for k in ("r_bps", "exit_price", "entry_price", "tau_ms", "status"):
                if k in ev:
                    ev[k] = (ev[k] + 300_000) if isinstance(ev[k], int) else (ev[k][:-1] + ("1" if ev[k][-1:] != "1" else "2") if ev[k] else "x")
                    break
            L[i] = dump([ev])[0]                      # tamper with an OUTCOME record (re-canonicalised, so only the chain/anchor can notice)
        elif op == "o_tail":
            L.append(L.pop(i))                        # move an OUTCOME to the very end (after every checkpoint)
        elif op == "o_cut":
            L = L[:i + 1]                             # cut the file right after an OUTCOME (tail-unanchored outcome)
        elif op == "o_status":
            ev["status"] = "NO_PRICE" if ev.get("status") == "EVAL" else "EVAL"
            L[i] = dump([ev])[0]
        elif op == "garbage":''')
open(p, "w", encoding="utf-8").write(s)
print("ok")
