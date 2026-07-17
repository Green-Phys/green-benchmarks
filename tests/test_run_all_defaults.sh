#!/bin/bash
# tests/test_run_all_defaults.sh — run_all defaults to ALL systems (every
# manifest) and takes its version pair from VERSION_OLD/VERSION_NEW.
set -u
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
fail=0

# No env.sh in a bare checkout: VERSION_* fall back to the shipped defaults.
out="$(RUN_ALL_DRY=1 SYSTEMS="" bash "$ROOT/tools/run_all.sh")" || { echo "run_all dry-run failed"; exit 1; }

# Every system with a manifest must appear (compare counts + spot-check names).
want=$(find "$ROOT/systems" -maxdepth 2 -name manifest.yaml | wc -l | tr -d ' ')
got=$(echo "$out" | sed -n 's/^systems: //p' | wc -w | tr -d ' ')
[[ "$want" == "$got" ]] || { echo "system count: want $want, got $got"; fail=1; }
for s in al2o3 h_chain n2 si; do
  echo "$out" | grep -q "systems:.*\b$s\b" || { echo "run_all default omits $s"; fail=1; }
done

# Version pair comes from VERSION_OLD/VERSION_NEW (here: env.sh.template defaults).
echo "$out" | grep -q '^versions: v032 v100a0$' || { echo "versions not from VERSION_OLD/NEW: $(echo "$out"|grep '^versions:')"; fail=1; }

# An explicit override wins.
out2="$(RUN_ALL_DRY=1 SYSTEMS="si n2" VERSIONS="v032" bash "$ROOT/tools/run_all.sh")"
echo "$out2" | grep -q '^systems: si n2$' || { echo "SYSTEMS override ignored"; fail=1; }
echo "$out2" | grep -q '^versions: v032$'  || { echo "VERSIONS override ignored"; fail=1; }

[[ $fail == 0 ]] && echo "test_run_all_defaults: PASS" || echo "test_run_all_defaults: FAIL"
exit $fail
