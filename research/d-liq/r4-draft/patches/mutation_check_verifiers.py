import subprocess, shutil, sys, os
T = sys.argv[1]
muts = [
 ("src/dliq_journal_verify_v2.py", 'if any(c > j and e["anchored_seq"] >= j for c, e in cps):', 'if True:', "src/test_dliq_journal_v2.py"),
 ("src/dliq_journal_verify_v2.py", 'if any(c > j and e["anchored_seq"] >= j for c, e in cps):', 'if any(c >= 0 and e["anchored_seq"] >= j for c, e in cps):', "src/test_dliq_journal_v2.py"),
 ("src/dliq_journal_verify_v2.py", 'if ev["rec_ms"] < tau + 10_000:', 'if ev["rec_ms"] < tau + 9_000:', "src/test_dliq_journal_v2.py"),
 ("src/dliq_journal_verify_v2.py", 'if ev["rec_ms"] < tau + 10_000:', 'if ev["rec_ms"] <= tau + 10_000:', "src/test_dliq_journal_v2.py"),
 ("src/dliq_journal_verify_v2.py", 'F(["OUTCOME_UNCOVERED", tau,', 'F(["OUTCOME_UNCOVERED", 0,', "src/test_dliq_journal_v2.py"),
 ("indep_verifier/verify_indep.py", 'if any(c > j and cev["anchored_seq"] >= j for c, cev in ckpts):', 'if True:', "indep_verifier/test_indep.py"),
 ("indep_verifier/verify_indep.py", 'if any(c > j and cev["anchored_seq"] >= j for c, cev in ckpts):', 'if any(c > j for c, cev in ckpts):', "indep_verifier/test_indep.py"),
 ("indep_verifier/verify_indep.py", 'outcomes[tau] = "UNCOVERED"', 'outcomes[tau] = "COVERED"', "indep_verifier/test_indep.py"),
 ("src/dliq_journal_v2.py", 'return s, self.checkpoint(anchor)\n\n    def close', 'return s, s\n\n    def close', "src/test_dliq_journal_v2.py"),
]
for f, a, b, t in muts:
    path = os.path.join(T, f); orig = open(path, encoding="utf-8").read()
    assert orig.count(a) == 1, (f, a)
    open(path, "w", encoding="utf-8").write(orig.replace(a, b))
    cwd = os.path.dirname(os.path.join(T, t))
    r = subprocess.run([sys.executable, "-I", "-B", os.path.basename(t)], cwd=cwd, capture_output=True, text=True)
    open(path, "w", encoding="utf-8").write(orig)
    print("KILLED " if r.returncode != 0 else "SURVIVED", f, "|", a[:50], "->", b[:40])
