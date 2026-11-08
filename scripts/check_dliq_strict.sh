#!/usr/bin/env bash
# Strict runner for the two D-LIQ check families whose old wiring could not fail loudly:
#   (1) deliberate-bug (mutation) checks: every mutant must be KILLED, the number of KILLED lines must equal the expected number,
#       and each script must exit 0 (a crash, a stale mutation target or a missing script is a failure, not a pass);
#   (2) the differential verifier corpus: each seed must exit 0 and print exactly "journals compared: <n>, disagreements: 0"
#       with n >= the requested corpus size.
# The mutation scripts rewrite source files in place and restore them afterwards. They are therefore run on a throw-away COPY of the
# package so an interrupted run can never leave the working tree mutated.
#
# Usage: scripts/check_dliq_strict.sh <package-dir> <expected-killed> <journals> <seed> [<seed> ...]
#   e.g. scripts/check_dliq_strict.sh research/d-liq/r4-draft 15 30000 11 12 13 14
# A pass is a synthetic-fixture result only. It is not research evidence and not a live-feed property.
set -uo pipefail
if [ "$#" -lt 4 ]; then echo "usage: $0 <package-dir> <expected-killed> <journals> <seed>..." >&2; exit 2; fi
PKG="$(cd "$1" && pwd)" || { echo "FAIL: package directory not found: $1" >&2; exit 2; }
EXPECT="$2"; N="$3"; shift 3
case "$EXPECT$N" in *[!0-9]*) echo "FAIL: expected-killed and journals must be integers" >&2; exit 2;; esac
WORK="$(mktemp -d)" || exit 2
trap 'rm -rf "$WORK"' EXIT
FAILS=0
bad() { printf 'FAIL %s\n' "$*"; FAILS=$((FAILS+1)); }
ok()  { printf 'OK   %s\n' "$*"; }

cp -R "$PKG" "$WORK/pkg" || { bad "cannot copy the package"; exit 1; }

KILLED=0
run_mut() {  # $1 label, $2 script (relative to the package), $3 argument (relative to the copy)
  local label="$1" script="$2" arg="$3" out="$WORK/$1.out" rc=0
  if [ ! -f "$WORK/pkg/$script" ]; then bad "$label: missing $script"; return; fi
  ( cd "$WORK/pkg" && python3 -I -W ignore "$script" "$arg" ) >"$out" 2>&1 || rc=$?
  local k s
  k=$(grep -c '^KILLED' "$out"); s=$(grep -c '^SURVIVED' "$out")
  if [ "$rc" -ne 0 ]; then bad "$label: exit status $rc"; tail -5 "$out"; fi
  if [ "$s" -ne 0 ]; then bad "$label: $s mutant(s) SURVIVED"; grep '^SURVIVED' "$out"; fi
  if [ "$rc" -eq 0 ] && [ "$s" -eq 0 ]; then ok "$label: $k killed"; fi
  KILLED=$((KILLED+k))
}
run_mut "verifier mutants" patches/mutation_check_verifiers.py "$WORK/pkg"
run_mut "builder mutants"  patches/mutation_check_builder.py   "$WORK/pkg/builder"
if [ "$KILLED" -ne "$EXPECT" ]; then bad "expected $EXPECT killed mutants, saw $KILLED"; else ok "total killed mutants: $KILLED"; fi

for seed in "$@"; do
  case "$seed" in *[!0-9]*|'') bad "bad seed: $seed"; continue;; esac
  out="$WORK/diff_$seed.out"; rc=0
  ( cd "$PKG" && python3 -I src/diff_test_verifiers.py indep_verifier "$N" "$seed" ) >"$out" 2>&1 || rc=$?
  line=$(grep -E '^journals compared: [0-9]+, disagreements: [0-9]+$' "$out" | head -1)
  compared=$(printf '%s' "$line" | sed -E 's/^journals compared: ([0-9]+), .*/\1/')
  if [ "$rc" -ne 0 ]; then bad "seed $seed: exit status $rc"; tail -5 "$out"
  elif [ -z "$line" ]; then bad "seed $seed: no 'journals compared' line"; tail -5 "$out"
  elif [ "$line" != "journals compared: $compared, disagreements: 0" ]; then bad "seed $seed: $line"
  elif [ "$compared" -lt "$N" ]; then bad "seed $seed: only $compared journals compared (< $N)"
  else ok "seed $seed: $line"; fi
done

if [ "$FAILS" -eq 0 ]; then echo "STRICT D-LIQ CHECKS PASSED (synthetic fixtures only)"; exit 0; fi
echo "$FAILS STRICT CHECK(S) FAILED"; exit 1
