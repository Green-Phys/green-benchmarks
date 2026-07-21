#!/bin/bash
# Regression: "only the first method runs". mbpt.sbatch feeds the per-method
# table to a `while read ... done <<<TABLE` loop on stdin, and srun (like
# ssh/mpirun) reads stdin — so the first method's srun would swallow the
# remaining rows unless its stdin is redirected. The fix is `srun ... </dev/null`.
set -u
cd "$(dirname "${BASH_SOURCE[0]}")/.." || exit 1
fail=0
TABLE=$'hf\ngf2\ngw'

# Fixed pattern: the stdin-reading stand-in is redirected from /dev/null, so all
# three rows are processed.
fixed=0
while read -r _m; do fixed=$((fixed+1)); cat >/dev/null </dev/null; done <<< "$TABLE"
[[ $fixed -eq 3 ]] || { echo "loop-with-redirect ran $fixed/3 (expected 3)"; fail=1; }

# Naive pattern (no redirect): the reader drains the rest -> only the 1st runs.
naive=0
while read -r _m; do naive=$((naive+1)); cat >/dev/null; done <<< "$TABLE"
[[ $naive -eq 1 ]] || echo "  (informational: naive pattern ran $naive/3)"

# The real template must isolate srun from the loop's stdin.
grep -q '</dev/null' templates/mbpt.sbatch || {
  echo "mbpt.sbatch: srun not </dev/null-isolated (methods after the 1st would be skipped)"; fail=1; }

[[ $fail == 0 ]] && echo "mbpt-method-loop OK" || exit 1
