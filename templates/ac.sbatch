#!/bin/bash
# templates/ac.sbatch — ANALYTIC CONTINUATION job.
#
# Pure-python phase (green-mbtools nevanlinna/caratheodory). Like init,
# this is single-task with multi-threaded BLAS via cpus-per-task.
#
# Contract (do not break):
#   In env :   BENCH_ROOT, BENCH_SCRATCH, SYSTEM, MANIFEST, GREEN_VER
#   In files:  $BENCH_SCRATCH/$SYSTEM/mbpt/$GREEN_VER/out.h5
#   Out:       $BENCH_SCRATCH/$SYSTEM/ac/$GREEN_VER/spectral.h5
#              + results JSON via tools/extract_results.py

#SBATCH --job-name=bench-ac
#SBATCH --output=%x-%j.out

set -euo pipefail
source "$BENCH_ROOT/env.sh"
source "$BENCH_ROOT/tools/activate_env.sh"

MBPT_OUT="$BENCH_SCRATCH/$SYSTEM/mbpt/$GREEN_VER/out.h5"
WORK="$BENCH_SCRATCH/$SYSTEM/ac/$GREEN_VER"
mkdir -p "$WORK"
cd "$WORK"

export OMP_NUM_THREADS=${SLURM_CPUS_PER_TASK:-1}
export MKL_NUM_THREADS=${SLURM_CPUS_PER_TASK:-1}

# TODO confirm exact AC entry-point. Nevanlinna is the default for
# green-mbtools (no external C++ deps beyond the in-tree extension).
python -m green_mbtools.ac \
    --input  "$MBPT_OUT" \
    --output "$WORK/spectral.h5" \
    --method nevanlinna

# Persist results JSON keyed by detected (mbpt-ver, mbtools-ver).
python "$BENCH_ROOT/tools/extract_results.py" \
    --system   "$SYSTEM" \
    --manifest "$MANIFEST" \
    --work-dir "$BENCH_SCRATCH/$SYSTEM"
