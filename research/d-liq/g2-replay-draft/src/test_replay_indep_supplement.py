#!/usr/bin/env python3
"""SUPPLEMENTARY tests for replay_indep.py, written AFTER the automatic mutation review (tools/mutate_indep.py) found two gaps in the
clean-room author's own suite. They are NOT part of the clean-room delivery and were written by the integrating author (Claude), who had seen
the code; src/test_replay_indep.py is kept byte-for-byte as delivered. Run:  python3 -I -B src/test_replay_indep_supplement.py"""
import os
import subprocess
import sys
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
sys.dont_write_bytecode = True
import test_replay_indep as T  # noqa: E402


class Supplement(T.Base):
    def test_conn_with_unknown_ev_string_is_ignored_not_read_as_close(self):
        # contract 2.1: CONN.ev is "open" or "close"; any other string makes the event BAD_EVENT (excluded). If it were read as a close at TAU-500,
        # the primary connection would end before the window and the slot would be NONE/GAP instead of VALID.
        j = T.J()
        T.add_healthy(j)
        T.add_std(j)
        j.conn(1, "bogus", T.TAU - 500)
        j.slot(T.TAU, T.REC, T.base_valid())
        self.assertReplay(j, [T.base_valid()])

    def test_cli_usage_error_exit_status(self):
        r = subprocess.run([sys.executable, "-I", "-B", os.path.join(HERE, "replay_indep.py")], capture_output=True, text=True)
        self.assertEqual(r.returncode, 2)
        self.assertIn("usage", r.stderr)

    def test_cli_prints_the_findings_list(self):
        j = T.J()
        T.add_healthy(j)
        T.add_std(j)
        j.slot(T.TAU, T.REC, T.base_valid())
        p = self.write(j)
        r = subprocess.run([sys.executable, "-I", "-B", os.path.join(HERE, "replay_indep.py"), p], capture_output=True, text=True)
        self.assertEqual((r.returncode, r.stdout.strip()), (0, "[]"))


if __name__ == "__main__":
    unittest.main(verbosity=1)
