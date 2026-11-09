#!/usr/bin/env bash
# One command that runs every repository check, on a Mac or Linux. Usage (from anywhere):
#   bash scripts/check_all.sh            # integrity + docs + mirrors + guard self-tests + the synthetic D-LIQ r4-draft and r5-draft suites (one differential seed)
#   FULL=1 bash scripts/check_all.sh     # also the four-seed differential corpus that CI runs and the G-2 / dry-run mutation checks (about 6 minutes)
# A pass confirms file identity, documentation structure and the tested synthetic fixtures only. It is not research evidence,
# a TradingView compile, a live-feed property, or rights clearance.
set -uo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"
TMP="$(mktemp -d)" || exit 2
trap 'rm -rf "$TMP"' EXIT
FAILS=0
step() { printf '\n== %s\n' "$*"; }
ok()   { printf '   OK   %s\n' "$*"; }
bad()  { printf '   FAIL %s\n' "$*"; FAILS=$((FAILS+1)); }
shacheck() { if command -v sha256sum >/dev/null 2>&1; then sha256sum -c "$1"; else shasum -a 256 -c "$1"; fi; }

step "no untracked files (check_docs and check_mirrors only look at TRACKED files; an untracked file would pass here and fail in CI)"
UNTRACKED="$(git ls-files --others --exclude-standard 2>/dev/null)"
if [ -z "$UNTRACKED" ]; then ok "no untracked files"; else bad "untracked files are invisible to the guards: git add them (or remove them) and rerun"; printf '%s\n' "$UNTRACKED" | head -8; fi
step "inventory regeneration is clean"
# Compare the regenerated inventory with the file as it is now (committed or not), then put the original back: a check must not edit the tree.
INV=docs/FILE_INVENTORY_SHA256.csv
cp "$INV" "$TMP/inventory.before"
if python3 scripts/generate_inventory.py >/dev/null && cmp -s "$INV" "$TMP/inventory.before"; then ok "inventory"
else bad "inventory differs from a fresh regeneration (run: python3 scripts/generate_inventory.py, then review the diff)"; fi
cp "$TMP/inventory.before" "$INV"
step "SHA-256 manifests"
python3 scripts/verify_sources.py >"$TMP/verify_sources.out" 2>&1 && ok "verify_sources" || { bad "verify_sources"; tail -5 "$TMP/verify_sources.out"; }
step "archive and sensitive-content screening"
python3 scripts/audit_archive_contents.py >"$TMP/audit_archive.out" 2>&1 && ok "audit_archive_contents" || { bad "audit_archive_contents"; tail -5 "$TMP/audit_archive.out"; }
step "documentation structure"
python3 scripts/check_docs.py && ok "check_docs" || bad "check_docs"
step "mirrored files"
python3 scripts/check_mirrors.py && ok "check_mirrors" || bad "check_mirrors"
step "guard self-tests (the guards must fail on known-bad inputs)"
python3 -I scripts/test_guards.py >"$TMP/guards.out" 2>&1 && ok "test_guards" || { bad "test_guards"; tail -12 "$TMP/guards.out"; }

R4=research/d-liq/r4-draft
step "D-LIQ r4-draft manifest"
( cd "$R4" && shacheck MANIFEST.sha256 ) >"$TMP/manifest.out" 2>&1 && ok "r4-draft manifest" || { bad "r4-draft manifest"; grep -v ': OK$' "$TMP/manifest.out" | head -8; }
run() { name="$1"; shift; ( cd "$R4" && "$@" >"$TMP/step.out" 2>&1 ) && ok "$name" || { bad "$name"; tail -8 "$TMP/step.out"; }; }
step "D-LIQ r4-draft synthetic suites"
run "writer + primary verifier"        python3 -I src/test_dliq_journal_v2.py
run "partially independent verifier"   python3 -I indep_verifier/test_indep.py
run "message contract"                 python3 -I src/test_dliq_msg_contract_v1.py
run "NONE-slot regressions"            python3 -I tests/test_none_slot_regressions.py
run "builder end-to-end"               python3 -I -W ignore builder/test_build_slots_v2_e2e.py
step "deliberate-bug (mutation) checks and differential corpus (strict: exit status, expected counts, no survivors)"
if [ "${FULL:-0}" = "1" ]; then SEEDS="11 12 13 14"; N=30000; else SEEDS="11"; N=5000; fi
# shellcheck disable=SC2086
bash scripts/check_dliq_strict.sh "$R4" 15 "$N" $SEEDS && ok "strict mutation + differential" || bad "strict mutation + differential"

R5=research/d-liq/r5-draft
step "D-LIQ r5-draft manifest"
( cd "$R5" && shacheck MANIFEST.sha256 ) >"$TMP/manifest5.out" 2>&1 && ok "r5-draft manifest" || { bad "r5-draft manifest"; grep -v ': OK$' "$TMP/manifest5.out" | head -8; }
run5() { name="$1"; shift; ( cd "$R5" && "$@" >"$TMP/step.out" 2>&1 ) && ok "$name" || { bad "$name"; tail -8 "$TMP/step.out"; }; }
step "D-LIQ r5-draft synthetic suites (replay contract 7.6)"
run5 "r5 writer + primary verifier"       python3 -I -B src/test_dliq_journal_v2.py
run5 "r5 partially independent verifier"  python3 -I -B indep_verifier/test_indep.py
run5 "r5 message contract"                python3 -I -B src/test_dliq_msg_contract_v1.py
run5 "r5 NONE-slot regressions"           python3 -I -B tests/test_none_slot_regressions.py
run5 "r5 builder end-to-end"              python3 -I -B -W ignore builder/test_build_slots_v2_e2e.py
step "D-LIQ r5-draft rebuild from r4-draft (G-3) and its negative tests"
python3 -I -B "$R5/patches/assemble_r5.py" "$R4" "$TMP/r5_rebuilt" >"$TMP/assemble5.out" 2>&1 && python3 -I -B "$R5/patches/check_rebuild.py" check "$TMP/r5_rebuilt" "$R5" >>"$TMP/assemble5.out" 2>&1 && ok "r5 rebuild equals the committed tree" || { bad "r5 rebuild"; tail -8 "$TMP/assemble5.out"; }
python3 -I -B "$R5/patches/test_rebuild_checks.py" "$R4" "$R5" >"$TMP/rebuild_tests.out" 2>&1 && ok "rebuild checks fail on tampering" || { bad "rebuild negative tests"; tail -8 "$TMP/rebuild_tests.out"; }
step "r5 deliberate-bug (mutation) checks and differential corpus (strict)"
# shellcheck disable=SC2086
bash scripts/check_dliq_strict.sh "$R5" 32 "$N" $SEEDS && ok "r5 strict mutation + differential" || bad "r5 strict mutation + differential"
echo "note: the r4-from-base rebuild (needs the PR #23 commit) runs only in CI: .github/workflows/verify-dliq-r5-draft.yml"

G1=research/d-liq/g1-candle-draft
step "D-LIQ G-1 draft (CANDLE provenance proposal): manifest, tests, mutants, feed-conflict demo"
( cd "$G1" && shacheck MANIFEST.sha256 ) >"$TMP/manifestg1.out" 2>&1 && ok "g1 manifest" || { bad "g1 manifest"; grep -v ': OK$' "$TMP/manifestg1.out" | head -8; }
( cd "$G1" && python3 -I -B src/test_dliq_kline_v1.py >"$TMP/g1_tests.out" 2>&1 ) && grep -q '^Ran 64 tests' "$TMP/g1_tests.out" && ok "g1 tests (64)" || { bad "g1 tests"; tail -8 "$TMP/g1_tests.out"; }
( cd "$G1" && python3 -I -B mutation_check_kline.py . >"$TMP/g1_mut.out" 2>&1 ) && grep -qx 'mutants: 62, problems: 0' "$TMP/g1_mut.out" && [ "$(grep -c '^KILLED' "$TMP/g1_mut.out")" = 62 ] && ok "g1 mutants (62 killed)" || { bad "g1 mutants"; grep -v '^KILLED' "$TMP/g1_mut.out" | head -8; }
( cd "$G1" && python3 -I -B src/demo_topology_conflict.py >"$TMP/g1_demo.out" 2>&1 ) && ok "g1 feed-conflict demo" || { bad "g1 demo"; tail -8 "$TMP/g1_demo.out"; }

G2=research/d-liq/g2-replay-draft
step "D-LIQ G-2 candidate independent replay: manifest, suites, differential (mutation check only with FULL=1)"
( cd "$G2" && shacheck MANIFEST.sha256 ) >"$TMP/manifestg2.out" 2>&1 && ok "g2 manifest" || { bad "g2 manifest"; grep -v ': OK$' "$TMP/manifestg2.out" | head -8; }
( cd "$G2" && python3 -I -B src/test_replay_indep.py >"$TMP/g2_clean.out" 2>&1 ) && grep -q '^Ran 188 tests' "$TMP/g2_clean.out" && ok "g2 clean-room suite (188)" || { bad "g2 clean-room suite"; tail -8 "$TMP/g2_clean.out"; }
( cd "$G2" && python3 -I -B src/test_replay_indep_supplement.py >"$TMP/g2_supp.out" 2>&1 ) && grep -q '^Ran 3 tests' "$TMP/g2_supp.out" && ok "g2 supplementary suite (3)" || { bad "g2 supplementary suite"; tail -8 "$TMP/g2_supp.out"; }
( cd "$G2" && python3 -I -B tools/diff_replay.py ../r5-draft/src src 11 "${DIFFN:-1500}" >"$TMP/g2_diff.out" 2>&1 ) && grep -q '"disagreements": 0}$' "$TMP/g2_diff.out" && ok "g2 differential (0 disagreements)" || { bad "g2 differential"; head -3 "$TMP/g2_diff.out" | cut -c1-300; }
if [ "${FULL:-0}" = "1" ]; then
  ( cd "$G2" && python3 -I -B tools/mutate_indep.py . ../r5-draft/src 4 >"$TMP/g2_mut.out" 2>&1 ) && grep -q '"unreviewed": 0, "stale": 0}$' "$TMP/g2_mut.out" && ok "g2 mutation check" || { bad "g2 mutation check"; tail -5 "$TMP/g2_mut.out"; }
fi

DR=research/d-liq/g1-dryrun-draft
step "D-LIQ G-1 dry-run tool (draft): manifest, tests against a loopback fake server (no real host is contacted), mutants"
( cd "$DR" && shacheck MANIFEST.sha256 ) >"$TMP/manifestdr.out" 2>&1 && ok "dry-run manifest" || { bad "dry-run manifest"; grep -v ': OK$' "$TMP/manifestdr.out" | head -8; }
( cd "$DR" && python3 -I -B -W error::ResourceWarning test_dliq_format_dryrun.py >"$TMP/dr_tests.out" 2>&1 ) && grep -q '^Ran 54 tests' "$TMP/dr_tests.out" && ok "dry-run tool tests (54)" || { bad "dry-run tool tests"; tail -8 "$TMP/dr_tests.out"; }
if [ "${FULL:-0}" = "1" ]; then
  ( cd "$DR" && python3 -I -B mutation_check_dryrun.py . >"$TMP/dr_mut.out" 2>&1 ) && grep -qx 'mutants: 47, problems: 0' "$TMP/dr_mut.out" && ok "dry-run mutants (47 killed)" || { bad "dry-run mutants"; grep -v '^KILLED' "$TMP/dr_mut.out" | head -8; }
fi

printf '\n'
if [ "$FAILS" -eq 0 ]; then echo "ALL CHECKS PASSED (synthetic / structural only; not research evidence)"; exit 0; fi
echo "$FAILS CHECK(S) FAILED"; exit 1
