#!/usr/bin/env python3
"""Rebuild the r4 increment from its two inputs, deterministically.
usage: python3 -I assemble.py <base dir: dliq_r3_reconstruction (zip sha 85fd4080...9a19)> <out dir (must not exist)>
inputs (besides the patches): patches/inputs/build_slots_v1_pr15_head.py = `git show pr/15:research/d-liq/r3-tools/build_slots_v1.py` (blob sha256 505ffdcc...960f7)"""
import hashlib, os, shutil, subprocess, sys
HERE = os.path.dirname(os.path.abspath(__file__))
base, out = os.path.abspath(sys.argv[1]), os.path.abspath(sys.argv[2])
assert not os.path.exists(out), "out dir exists"
shutil.copytree(base, out)
sha = lambda p: hashlib.sha256(open(p, "rb").read()).hexdigest()
assert sha(os.path.join(HERE, "inputs", "build_slots_v1_pr15_head.py")) == "505ffdcce544e4aa4ea94100c9bc73e2f42aacab02e159d0c1177dbe800960f7"
for p in ("p01_contract", "p02_writer_primary", "p03_tests_a", "p03_tests_b", "p04_indep", "p05_indep_tests", "p06_diff", "p07_contract_75", "p08_primary_tests", "p10_replayed_key"):
    subprocess.run([sys.executable, "-I", os.path.join(HERE, p + ".py"), out], check=True, stdout=subprocess.DEVNULL)
b = os.path.join(out, "builder")
for d in ("verifiers/primary", "verifiers/independent"):
    os.makedirs(os.path.join(b, d))
shutil.copy(os.path.join(out, "src", "dliq_journal_verify_v2.py"), os.path.join(b, "verifiers", "primary"))
shutil.copy(os.path.join(out, "src", "dliq_msg_contract_v1.py"), os.path.join(b, "verifiers", "primary"))
shutil.copy(os.path.join(out, "indep_verifier", "verify_indep.py"), os.path.join(b, "verifiers", "independent"))
subprocess.run([sys.executable, "-I", os.path.join(HERE, "p12_builder_delta.py"), os.path.join(HERE, "inputs", "build_slots_v1_pr15_head.py"), os.path.join(b, "build_slots_v2.py"),
                os.path.join(b, "verifiers", "primary", "dliq_journal_verify_v2.py"), os.path.join(b, "verifiers", "independent", "verify_indep.py"),
                os.path.join(b, "verifiers", "primary", "dliq_msg_contract_v1.py")], check=True, stdout=subprocess.DEVNULL)
shutil.copy(os.path.join(HERE, "files", "test_build_slots_v2_e2e.py"), b)
print("assembled", out)
