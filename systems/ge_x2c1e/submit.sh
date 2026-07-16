#!/bin/bash
# Submit the init -> mbpt -> ac chain for ge x2c1e at $GREEN_VER.
# Usage: GREEN_VER=v100a0 bash systems/ge_x2c1e/submit.sh
# SLURM resources come from env.sh (per-phase SLURM_* defaults); overrides below preserve the tuned values.
set -euo pipefail

export SYSTEM=ge_x2c1e

# per-system resource overrides (else env.sh defaults apply)
export SLURM_INIT_TIME=12:00:00
export SLURM_MBPT_NODES=2
export SLURM_MBPT_NTASKS_PER_NODE=48
export SLURM_MBPT_TIME=24:00:00
export SLURM_AC_NTASKS_PER_NODE=32
export SLURM_AC_TIME=12:00:00

source "$(dirname "${BASH_SOURCE[0]}")/../../tools/submit_chain.sh"
