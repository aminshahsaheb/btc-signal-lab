"""r4 patch 10: primary verifier reports `replayed` (bool); contract 8.2 / 7.1 mention it. usage: python3 p10_replayed_key.py <tree>"""
import sys
tree = sys.argv[1]
def patch(path, edits):
    s = open(path, encoding="utf-8").read()
    for a, b in edits:
        assert s.count(a) == 1, (path, a[:80], s.count(a))
        s = s.replace(a, b)
    open(path, "w", encoding="utf-8").write(s)
patch(tree + "/src/dliq_journal_verify_v2.py", [
    ('"slots": slots, "missing": missing, "outcomes": outcomes}', '"slots": slots, "missing": missing, "outcomes": outcomes, "replayed": bool(replay_slots)}'),
    ('head_hex, slots, missing, outcomes)\n', 'head_hex, slots, missing, outcomes, replayed)\n'),
])
patch(tree + "/indep_verifier/JOURNAL_CONTRACT_v2.md", [
    ("`slots` and `missing` as in 5.5, and `outcomes` as in 6.4.", "`slots` and `missing` as in 5.5, `outcomes` as in 6.4, and -- only for an implementation of section 7 -- `replayed` (bool: whether the replay layer ran). A consumer that requires the replay (7.1) MUST refuse a report without `replayed: true`."),
])
print("ok")
