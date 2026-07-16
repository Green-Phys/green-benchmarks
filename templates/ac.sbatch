#!/bin/bash
# templates/ac.sbatch — ANALYTIC CONTINUATION job.
#
# MPI C++ binary (green-ac/ac.exe) — continues the mbpt GW Green's
# function G_tau to real frequency. ac.exe is version-independent, so
# its build dir is on PATH via $GREEN_AC in env.sh (not activate_env.sh,
# which is per-version). Solids run under MPI; molecular uses 1 task.
#
# Contract (do not break):
#   In env :   BENCH_ROOT, BENCH_SCRATCH, SYSTEM, MANIFEST, GREEN_VER
#   In files:  $BENCH_SCRATCH/$GREEN_VER/$SYSTEM/mbpt/out_gw.h5
#   Out:       $BENCH_SCRATCH/$GREEN_VER/$SYSTEM/ac/ac_gw.h5
#              + results JSON via tools/extract_results.py

#SBATCH --job-name=bench-ac

set -euo pipefail
source "$BENCH_ROOT/env.sh"
source "$BENCH_ROOT/tools/activate_env.sh"

AC_SUBDIR="${AC_SUBDIR:-ac}"                       # ac | ac_gpu
MBPT_SUBDIR_FOR_AC="${MBPT_SUBDIR_FOR_AC:-mbpt}"   # mbpt | mbpt_gpu
AC_INPUT="$BENCH_SCRATCH/$GREEN_VER/$SYSTEM/$MBPT_SUBDIR_FOR_AC/out_gw.h5"
WORK="$BENCH_SCRATCH/$GREEN_VER/$SYSTEM/$AC_SUBDIR"
AC_OUTPUT="$WORK/ac_gw.h5"

# ac.exe is resolved via PATH ($GREEN_AC is prepended in env.sh), same as
# mbpt.exe. Sanity-check it exists up front so a missing/unset $GREEN_AC
# fails with a clear message instead of a cryptic srun execve error.
AC_BIN="${GREEN_AC:?GREEN_AC must point to the green-ac build dir in env.sh}/ac.exe"
[[ -x "$AC_BIN" ]] || { echo "ac.exe not found or not executable at $AC_BIN" >&2; exit 1; }

mkdir -p "$WORK"
cd "$WORK"

export OMP_NUM_THREADS=${SLURM_CPUS_PER_TASK:-1}
export MKL_NUM_THREADS=${SLURM_CPUS_PER_TASK:-1}

# grid + beta are the same values mbpt ran with (from the manifest).
_yaml="import yaml; m=yaml.safe_load(open('$MANIFEST'));"
GRID_FILE=$(python -c "$_yaml print(m.get('mesh',{}).get('grid_file','ir/1e4.h5'))")
BETA=$(python -c "$_yaml print(m.get('mesh',{}).get('beta',100))")

# The 'iter' dataset records the final iteration; its G_tau lives under
# iter<N>/G_tau. (AC can run on any method's output; GW for now.)
LAST_ITER=$(python -c "
import h5py
with h5py.File('$AC_INPUT', 'r') as f:
    print(int(f['iter'][()]))
")

srun ac.exe \
    --grid_file   "$GRID_FILE" \
    --BETA        "$BETA" \
    --input_file  "$AC_INPUT" \
    --output_file "$AC_OUTPUT" \
    --group       "iter${LAST_ITER}/G_tau" \
    --e_min       -1 \
    --e_max       0.5 \
    --n_omega     1501 \
    --eta         0.005 \
    --kind        Nevanlinna

# Persist results JSON keyed by detected (mbpt-ver, mbtools-ver).
python "$BENCH_ROOT/tools/extract_results.py" \
    --system   "$SYSTEM" \
    --manifest "$MANIFEST" \
    --work-dir "$BENCH_SCRATCH/$GREEN_VER/$SYSTEM"
