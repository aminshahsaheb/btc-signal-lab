"""r4 patch 03a: writer/primary suite -- the Rig records outcomes with their covering checkpoint (contract 6.4) unless anchor=False. usage: python3 p03_tests_a.py <tree>"""
import sys
tree = sys.argv[1]
p = tree + "/src/test_dliq_journal_v2.py"
s = open(p, encoding="utf-8").read()
def rep(a, b):
    global s
    assert s.count(a) == 1, (a[:90], s.count(a))
    s = s.replace(a, b)
rep('''    def outcome(self, tau, status="EVAL", entry_open=None, exit_open=None, ep="100000.5", xp="100500.5", r=None, checked=True, at=None):
        if at is not None:''','''    def outcome(self, tau, status="EVAL", entry_open=None, exit_open=None, ep="100000.5", xp="100500.5", r=None, checked=True, at=None, anchor=True):
        """r4: by default the OUTCOME is immediately followed by the CHECKPOINT that covers it (contract 6.4); anchor=False leaves it in the unanchored tail"""
        if at is not None:''')
rep('''        return (self.j.append if checked else self.j.append_unchecked)("OUTCOME", **f)

    def full_slot''','''        n = (self.j.append if checked else self.j.append_unchecked)("OUTCOME", **f)
        if anchor:
            self.now[0] += 1
            self.j.checkpoint(self.a)
        return n

    def full_slot''')
open(p, "w", encoding="utf-8").write(s)
print("ok")
