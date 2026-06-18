#!/bin/bash
# templates/init.sbatch — INITIALIZATION job.
#
# Pure-python phase: pyscf mean-field + green-mbtools integral dump.
# Single-task SLURM allocation, multi-threaded BLAS/OpenMP via cpus-per-task.
#
# Contract (do not break):
#   In env :  BENCH_ROOT, BENCH_SCRATCH, SYSTEM, MANIFEST, GREEN_VER
#             (set by systems/<sys>/submit.sh before sbatch)
#   Out:      $BENCH_SCRATCH/$SYSTEM/init/input.h5
#             exit 0 on success; non-zero aborts the chain

#SBATCH --job-name=bench-init
#SBATCH --output=%x-%j.out

set -euo pipefail
source "$BENCH_ROOT/env.sh"
source "$BENCH_ROOT/tools/activate_env.sh"

WORK="$BENCH_SCRATCH/$SYSTEM/init"
mkdir -p "$WORK"
cd "$WORK"

# Match BLAS thread count to the SLURM allocation
export OMP_NUM_THREADS=${SLURM_CPUS_PER_TASK:-1}
export MKL_NUM_THREADS=${SLURM_CPUS_PER_TASK:-1}

python "$BENCH_ROOT/systems/$SYSTEM/generate.py" \
    --manifest "$MANIFEST" \
    --out      "$WORK/input.h5"
