"""r4 patch 03b: adapt 8 writer/primary tests to outcomes that carry their own checkpoint. usage: python3 p03_tests_b.py <tree>"""
import sys
tree = sys.argv[1]
p = tree + "/src/test_dliq_journal_v2.py"
s = open(p, encoding="utf-8").read()
def rep(a, b):
    global s
    assert s.count(a) == 1, (a[:90], s.count(a))
    s = s.replace(a, b)
rep('''    R.outcome(TAU, "NO_PRICE")
    check("OUTCOME allowed after the covering checkpoint", R.j.seq == ck + 1)''','''    R.outcome(TAU, "NO_PRICE", anchor=False)
    check("OUTCOME allowed after the covering checkpoint", R.j.seq == ck + 1)''')
rep('anchor_of(ap2).latest(JID) == 1 and anchor_of(ap2).get(JID, 2) is None)','anchor_of(ap2).latest(JID) == 2 and anchor_of(ap2).get(JID, 3) is None)')
rep('exact("OUTCOME: clean EVAL outcome", run(jp, ap), infos=["TAIL_UNANCHORED"])','exact("OUTCOME: clean EVAL outcome (covered by its own checkpoint)", run(jp, ap), infos=[])')
rep('outcome_case("r_bps within 1e-6 of the formula is accepted", b_mm_tol, [], infos=["TAIL_UNANCHORED"])','outcome_case("r_bps within 1e-6 of the formula is accepted", b_mm_tol, [], infos=[])')
rep('outcome_case("NO_PRICE outcome needs no candles", b_no_price, [], infos=["TAIL_UNANCHORED"])','outcome_case("NO_PRICE outcome needs no candles", b_no_price, [], infos=[])')
rep('check("truncation fixture has 3 checkpoints", len(cp_lines) == 3, cp_lines)','check("truncation fixture has 5 checkpoints (a slot and an outcome checkpoint per full slot, plus one)", len(cp_lines) == 5, cp_lines)')
rep('has("ANCHOR_AHEAD_BENIGN: where = anchor index", r, "ANCHOR_AHEAD_BENIGN", 3)','has("ANCHOR_AHEAD_BENIGN: where = anchor index", r, "ANCHOR_AHEAD_BENIGN", 5)')
rep('write_lines(jt, L0[:cp_lines[0] + 3])                      # cut a few lines after the first checkpoint, in the middle of the second slot','write_lines(jt, L0[:cp_lines[0] + 2])                      # cut two lines after the first checkpoint, before the first outcome')
open(p, "w", encoding="utf-8").write(s)
print("ok")
