#!/bin/bash
# Submit the init -> mbpt -> ac chain for Ge sfx2c1e at $GREEN_VER.
# Usage: GREEN_VER=v032 bash systems/ge_sfx2c1e/submit.sh
set -euo pipefail

export SYSTEM=ge_sfx2c1e
: "${GREEN_VER:?GREEN_VER must be v032 or v100a0}"

THIS_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
export BENCH_ROOT="${BENCH_ROOT:-$(cd "$THIS_DIR/../.." && pwd)}"
source "$BENCH_ROOT/env.sh"

export MANIFEST="$BENCH_ROOT/systems/$SYSTEM/manifest.yaml"
EXPORTS="ALL,BENCH_ROOT,BENCH_SCRATCH,SYSTEM,MANIFEST,GREEN_VER"

LOG_INIT="$BENCH_SCRATCH/$SYSTEM/init/$GREEN_VER/bench-init-%j.out"
LOG_MBPT="$BENCH_SCRATCH/$SYSTEM/mbpt/$GREEN_VER/bench-mbpt-%j.out"
LOG_AC="$BENCH_SCRATCH/$SYSTEM/ac/$GREEN_VER/bench-ac-%j.out"
mkdir -p "$(dirname "$LOG_INIT")" "$(dirname "$LOG_MBPT")" "$(dirname "$LOG_AC")"

INIT_JID=$(sbatch --parsable --export="$EXPORTS" \
    --nodes=1 --ntasks-per-node=1 --cpus-per-task=16 --time=01:00:00 \
    --partition="$SLURM_PARTITION_AUX" \
    --output="$LOG_INIT" \
    "$BENCH_ROOT/templates/init.sbatch")
MBPT_JID=$(sbatch --parsable --export="$EXPORTS" \
    --dependency=afterok:$INIT_JID \
    --nodes=2 --ntasks-per-node=48 --cpus-per-task=2 --exclusive --time=48:00:00 \
    --partition="$SLURM_PARTITION_MBPT" \
    --output="$LOG_MBPT" \
    "$BENCH_ROOT/templates/mbpt.sbatch")
AC_JID=$(sbatch --parsable --export="$EXPORTS" \
    --dependency=afterok:$MBPT_JID \
    --nodes=1 --ntasks-per-node=32 --cpus-per-task=2 --time=12:00:00 \
    --partition="$SLURM_PARTITION_AUX" \
    --output="$LOG_AC" \
    "$BENCH_ROOT/templates/ac.sbatch")

echo "queued: init=$INIT_JID  mbpt=$MBPT_JID  ac=$AC_JID  (system=$SYSTEM ver=$GREEN_VER)"
