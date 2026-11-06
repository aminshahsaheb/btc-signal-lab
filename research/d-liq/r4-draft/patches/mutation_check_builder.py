import subprocess, sys, os
T = sys.argv[1]
muts = [
 ('if own_cov.get(tau) != "COVERED":', 'if False:'),
 ('hard.add("BUILDER_OUTCOME_COVERAGE_MISMATCH")', 'pass'),
 ('journal_path, anchor, snapshot["journal_id"], snapshot["verify_time_ms"], replay_slots=True)', 'journal_path, anchor, snapshot["journal_id"], snapshot["verify_time_ms"])'),
 ('    _check_pinned_file(MSG_CONTRACT_PATH, MSG_CONTRACT_SHA256)      # r4', '    pass      # r4'),
 ('raise BuildError("verifiers disagree on per-OUTCOME coverage")', 'pass'),
 ('        raise BuildError("the pinned primary verifier did not run the mandatory SLOT replay")', '        pass'),
]
path = os.path.join(T, "build_slots_v2.py"); orig = open(path, encoding="utf-8").read()
for a, b in muts:
    assert orig.count(a) == 1, a
    open(path, "w", encoding="utf-8").write(orig.replace(a, b))
    r = subprocess.run([sys.executable, "-I", "-B", "test_build_slots_v2_e2e.py"], cwd=T, capture_output=True, text=True)
    print("KILLED " if r.returncode else "SURVIVED", a[:70])
open(path, "w", encoding="utf-8").write(orig)
