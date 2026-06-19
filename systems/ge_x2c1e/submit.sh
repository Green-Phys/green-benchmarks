#!/bin/bash
# Submit the init -> mbpt -> ac chain for Ge x2c1e (spinor) at $GREEN_VER.
# Usage: GREEN_VER=v032 bash systems/ge_x2c1e/submit.sh
set -euo pipefail

export SYSTEM=ge_x2c1e
: "${GREEN_VER:?GREEN_VER must be v032 or v100a0}"

THIS_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
export BENCH_ROOT="${BENCH_ROOT:-$(cd "$THIS_DIR/../.." && pwd)}"
source "$BENCH_ROOT/env.sh"

export MANIFEST="$BENCH_ROOT/systems/$SYSTEM/manifest.yaml"
EXPORTS="ALL,BENCH_ROOT,BENCH_SCRATCH,SYSTEM,MANIFEST,GREEN_VER"

# x2c1e spinor: roughly 1.5x the work of sfx2c1e.
INIT_JID=$(sbatch --parsable --export="$EXPORTS" \
    --nodes=1 --ntasks-per-node=1 --cpus-per-task=16 --time=01:30:00 \
    --partition="$SLURM_PARTITION_AUX" \
    "$BENCH_ROOT/templates/init.sbatch")
MBPT_JID=$(sbatch --parsable --export="$EXPORTS" \
    --dependency=afterok:$INIT_JID \
    --nodes=4 --ntasks-per-node=32 --time=18:00:00 \
    --partition="$SLURM_PARTITION_MBPT" \
    "$BENCH_ROOT/templates/mbpt.sbatch")
AC_JID=$(sbatch --parsable --export="$EXPORTS" \
    --dependency=afterok:$MBPT_JID \
    --nodes=1 --ntasks-per-node=1 --cpus-per-task=16 --time=03:00:00 \
    --partition="$SLURM_PARTITION_AUX" \
    "$BENCH_ROOT/templates/ac.sbatch")

echo "queued: init=$INIT_JID  mbpt=$MBPT_JID  ac=$AC_JID  (system=$SYSTEM ver=$GREEN_VER)"
