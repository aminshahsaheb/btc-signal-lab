#!/usr/bin/env bash
# One command that runs every repository check, on a Mac or Linux. Usage (from anywhere):
#   bash scripts/check_all.sh            # integrity + docs + mirrors + the synthetic D-LIQ r4-draft suites (one differential seed)
#   FULL=1 bash scripts/check_all.sh     # also the four-seed differential corpus that CI runs (about 2 minutes)
# A pass confirms file identity, documentation structure and the tested synthetic fixtures only. It is not research evidence,
# a TradingView compile, a live-feed property, or rights clearance.
set -uo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"
FAILS=0
step() { printf '\n== %s\n' "$*"; }
ok()   { printf '   OK   %s\n' "$*"; }
bad()  { printf '   FAIL %s\n' "$*"; FAILS=$((FAILS+1)); }
shacheck() { if command -v sha256sum >/dev/null 2>&1; then sha256sum -c "$1"; else shasum -a 256 -c "$1"; fi; }

step "inventory regeneration is clean"
python3 scripts/generate_inventory.py >/dev/null && git diff --quiet -- docs/FILE_INVENTORY_SHA256.csv && ok "inventory" || bad "inventory differs (run: python3 scripts/generate_inventory.py, then review the diff)"
step "SHA-256 manifests"
python3 scripts/verify_sources.py >/tmp/verify_sources.out 2>&1 && ok "verify_sources" || { bad "verify_sources"; tail -5 /tmp/verify_sources.out; }
step "archive and sensitive-content screening"
python3 scripts/audit_archive_contents.py >/tmp/audit_archive.out 2>&1 && ok "audit_archive_contents" || { bad "audit_archive_contents"; tail -5 /tmp/audit_archive.out; }
step "documentation structure"
python3 scripts/check_docs.py && ok "check_docs" || bad "check_docs"
step "mirrored files"
python3 scripts/check_mirrors.py && ok "check_mirrors" || bad "check_mirrors"

R4=research/d-liq/r4-draft
step "D-LIQ r4-draft manifest"
( cd "$R4" && shacheck MANIFEST.sha256 | grep -v ': OK$' ) | grep . && bad "r4-draft manifest has a mismatch" || ok "r4-draft manifest"
run() { name="$1"; shift; ( cd "$R4" && "$@" >/tmp/check_all_step.out 2>&1 ) && ok "$name" || { bad "$name"; tail -8 /tmp/check_all_step.out; }; }
step "D-LIQ r4-draft synthetic suites"
run "writer + primary verifier"        python3 -I src/test_dliq_journal_v2.py
run "partially independent verifier"   python3 -I indep_verifier/test_indep.py
run "message contract"                 python3 -I src/test_dliq_msg_contract_v1.py
run "NONE-slot regressions"            python3 -I tests/test_none_slot_regressions.py
run "builder end-to-end"               python3 -I -W ignore builder/test_build_slots_v2_e2e.py
step "deliberate-bug (mutation) checks"
( cd "$R4" && python3 -I -W ignore patches/mutation_check_verifiers.py "$PWD" ; python3 -I -W ignore patches/mutation_check_builder.py "$PWD/builder" ) >/tmp/check_all_mut.out 2>&1
grep -q SURVIVED /tmp/check_all_mut.out && { bad "a deliberate bug SURVIVED"; grep SURVIVED /tmp/check_all_mut.out; } || ok "all deliberate bugs killed"
step "differential verifier corpus"
if [ "${FULL:-0}" = "1" ]; then SEEDS="11 12 13 14"; N=30000; else SEEDS="11"; N=5000; fi
for s in $SEEDS; do
  ( cd "$R4" && python3 -I src/diff_test_verifiers.py indep_verifier "$N" "$s" ) >/tmp/check_all_diff.out 2>&1
  grep -q "disagreements: 0" /tmp/check_all_diff.out && ok "seed $s ($N journals)" || { bad "seed $s"; tail -5 /tmp/check_all_diff.out; }
done

printf '\n'
if [ "$FAILS" -eq 0 ]; then echo "ALL CHECKS PASSED (synthetic / structural only; not research evidence)"; exit 0; fi
echo "$FAILS CHECK(S) FAILED"; exit 1
