#!/bin/bash
# tools/submit_chain.sh — shared init -> mbpt -> ac SLURM submission chain.
#
# A system's submit.sh sets SYSTEM (and, optionally, per-system SLURM_*
# resource overrides), then sources this file. Job resources default from
# env.sh; override any of them by exporting the corresponding SLURM_{INIT,
# MBPT,AC}_* variable before sourcing this script.
#
# Usage (from systems/<sys>/submit.sh):
#     export SYSTEM=<sys>
#     # optional: export SLURM_MBPT_TIME=24:00:00   (etc.)
#     source "$(dirname "${BASH_SOURCE[0]}")/../../tools/submit_chain.sh"
#
# Required in env: GREEN_VER (e.g. v032, v100a0). BENCH_ROOT is derived from
# this script's location if not already set.
set -euo pipefail

: "${SYSTEM:?SYSTEM must be set by the calling submit.sh}"
: "${GREEN_VER:?GREEN_VER must be set (e.g. v032, v100a0)}"

# tools/ lives directly under the repo root.
export BENCH_ROOT="${BENCH_ROOT:-$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)}"
source "$BENCH_ROOT/env.sh"

# Safety net for a stale env.sh (it is gitignored / per-machine and may predate
# the per-phase resource variables): fill any that are still unset. Authoritative
# defaults + docs live in env.sh.template — tune there, not here.
: "${SLURM_INIT_CPUS:=16}";  : "${SLURM_INIT_TIME:=01:00:00}"
: "${SLURM_MBPT_NODES:=1}";  : "${SLURM_MBPT_NTASKS_PER_NODE:=32}"
: "${SLURM_MBPT_CPUS:=2}";   : "${SLURM_MBPT_TIME:=06:00:00}"
: "${SLURM_MBPT_EXTRA=--exclusive}"   # no ':' so an explicit empty is kept
: "${SLURM_AC_NODES:=1}";    : "${SLURM_AC_NTASKS_PER_NODE:=16}"
: "${SLURM_AC_CPUS:=2}";     : "${SLURM_AC_TIME:=02:00:00}"
: "${MBPT_GPU:=1}";          : "${SLURM_PARTITION_GPU:=blackwell}"
: "${SLURM_MBPT_GPU_NODES:=1}";          : "${SLURM_MBPT_GPU_NTASKS_PER_NODE:=1}"
: "${SLURM_MBPT_GPU_GPUS_PER_NODE:=1}";  : "${SLURM_MBPT_GPU_CPUS:=8}"
: "${SLURM_MBPT_GPU_TIME:=06:00:00}";    : "${SLURM_MBPT_GPU_EXTRA=}"

export MANIFEST="$BENCH_ROOT/systems/$SYSTEM/manifest.yaml"
EXPORTS="ALL,BENCH_ROOT,BENCH_SCRATCH,SYSTEM,MANIFEST,GREEN_VER"

LOG_INIT="$BENCH_SCRATCH/$GREEN_VER/$SYSTEM/init/bench-init-%j.out"
LOG_MBPT="$BENCH_SCRATCH/$GREEN_VER/$SYSTEM/mbpt/bench-mbpt-%j.out"
LOG_MBPT_GPU="$BENCH_SCRATCH/$GREEN_VER/$SYSTEM/mbpt_gpu/bench-mbpt-gpu-%j.out"
LOG_AC="$BENCH_SCRATCH/$GREEN_VER/$SYSTEM/ac/bench-ac-%j.out"
mkdir -p "$(dirname "$LOG_INIT")" "$(dirname "$LOG_MBPT")" \
         "$(dirname "$LOG_MBPT_GPU")" "$(dirname "$LOG_AC")"

# INIT — always single node / single task (multi-threaded via cpus-per-task).
INIT_JID=$(sbatch --parsable --export="$EXPORTS" \
    --nodes=1 --ntasks-per-node=1 \
    --cpus-per-task="$SLURM_INIT_CPUS" --time="$SLURM_INIT_TIME" \
    --partition="$SLURM_PARTITION_AUX" \
    --output="$LOG_INIT" \
    "$BENCH_ROOT/templates/init.sbatch")

# MBPT — the heavy MPI job. $SLURM_MBPT_EXTRA is intentionally unquoted so an
# empty value expands to nothing and e.g. "--exclusive" expands to a flag.
MBPT_JID=$(sbatch --parsable --export="$EXPORTS" \
    --dependency=afterok:$INIT_JID \
    --nodes="$SLURM_MBPT_NODES" --ntasks-per-node="$SLURM_MBPT_NTASKS_PER_NODE" \
    --cpus-per-task="$SLURM_MBPT_CPUS" --time="$SLURM_MBPT_TIME" $SLURM_MBPT_EXTRA \
    --partition="$SLURM_PARTITION_MBPT" \
    --output="$LOG_MBPT" \
    "$BENCH_ROOT/templates/mbpt.sbatch")

# MBPT on GPU (mbpt.exe --kernel GPU) — extra MBPT-only job on the GPU
# partition, depends on the same init, writes to a separate mbpt_gpu/ dir.
# Skipped when MBPT_GPU=0.
MBPT_GPU_JID=""
if [[ "$MBPT_GPU" != 0 ]]; then
    MBPT_GPU_JID=$(sbatch --parsable \
        --export="$EXPORTS,MBPT_KERNEL=GPU,MBPT_SUBDIR=mbpt_gpu" \
        --dependency=afterok:$INIT_JID \
        --nodes="$SLURM_MBPT_GPU_NODES" --ntasks-per-node="$SLURM_MBPT_GPU_NTASKS_PER_NODE" \
        --gpus-per-node="$SLURM_MBPT_GPU_GPUS_PER_NODE" \
        --cpus-per-task="$SLURM_MBPT_GPU_CPUS" --time="$SLURM_MBPT_GPU_TIME" $SLURM_MBPT_GPU_EXTRA \
        --partition="$SLURM_PARTITION_GPU" \
        --output="$LOG_MBPT_GPU" \
        "$BENCH_ROOT/templates/mbpt.sbatch")
fi

: "${AC_GPU:=$MBPT_GPU}"
LOG_AC_GPU="$BENCH_SCRATCH/$GREEN_VER/$SYSTEM/ac_gpu/bench-ac-gpu-%j.out"
mkdir -p "$(dirname "$LOG_AC_GPU")"
AC_GPU_JID=""
if [[ "$MBPT_GPU" != 0 && "$AC_GPU" != 0 ]]; then
    # Identical to the CPU AC job (same ac.exe, same SLURM_AC_* resources, same
    # AUX partition) — only the source mbpt dir and the output dir differ.
    AC_GPU_JID=$(sbatch --parsable \
        --export="$EXPORTS,AC_SUBDIR=ac_gpu,MBPT_SUBDIR_FOR_AC=mbpt_gpu" \
        --dependency=afterok:$MBPT_GPU_JID \
        --nodes="$SLURM_AC_NODES" --ntasks-per-node="$SLURM_AC_NTASKS_PER_NODE" \
        --cpus-per-task="$SLURM_AC_CPUS" --time="$SLURM_AC_TIME" \
        --partition="$SLURM_PARTITION_AUX" \
        --output="$LOG_AC_GPU" \
        "$BENCH_ROOT/templates/ac.sbatch")
fi

# AC — analytic continuation (on the CPU MBPT output).
AC_JID=$(sbatch --parsable --export="$EXPORTS" \
    --dependency=afterok:$MBPT_JID \
    --nodes="$SLURM_AC_NODES" --ntasks-per-node="$SLURM_AC_NTASKS_PER_NODE" \
    --cpus-per-task="$SLURM_AC_CPUS" --time="$SLURM_AC_TIME" \
    --partition="$SLURM_PARTITION_AUX" \
    --output="$LOG_AC" \
    "$BENCH_ROOT/templates/ac.sbatch")

echo "queued: init=$INIT_JID  mbpt=$MBPT_JID  mbpt_gpu=${MBPT_GPU_JID:-skipped}  ac=$AC_JID  ac_gpu=${AC_GPU_JID:-skipped}  (system=$SYSTEM ver=$GREEN_VER)"
