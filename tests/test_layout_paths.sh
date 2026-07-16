#!/bin/bash
# Asserts the version-first scratch layout in the SLURM plumbing.
set -uo pipefail
cd "$(dirname "${BASH_SOURCE[0]}")/.."
fail=0
# submit_chain builds $BENCH_SCRATCH/$GREEN_VER/$SYSTEM/<phase> for logs
grep -q 'BENCH_SCRATCH/\$GREEN_VER/\$SYSTEM/init' tools/submit_chain.sh || { echo "submit_chain init log not version-first"; fail=1; }
grep -q 'BENCH_SCRATCH/\$GREEN_VER/\$SYSTEM/mbpt_gpu' tools/submit_chain.sh || { echo "submit_chain mbpt_gpu log not version-first"; fail=1; }
# templates build $BENCH_SCRATCH/$GREEN_VER/$SYSTEM/<phase>
grep -q 'BENCH_SCRATCH/\$GREEN_VER/\$SYSTEM/init' templates/init.sbatch || { echo "init.sbatch WORK not version-first"; fail=1; }
grep -q 'BENCH_SCRATCH/\$GREEN_VER/\$SYSTEM/\$MBPT_SUBDIR' templates/mbpt.sbatch || { echo "mbpt.sbatch WORK not version-first"; fail=1; }
grep -q 'BENCH_SCRATCH/\$GREEN_VER/\$SYSTEM' templates/ac.sbatch || { echo "ac.sbatch not version-first"; fail=1; }
# no OLD pattern (system before phase) remains in the plumbing
if grep -rEq 'BENCH_SCRATCH/\$SYSTEM/(init|mbpt|ac)' tools/submit_chain.sh templates/*.sbatch; then
  echo "OLD system-first path still present"; fail=1; fi
[[ $fail == 0 ]] && echo "layout OK" || exit 1
