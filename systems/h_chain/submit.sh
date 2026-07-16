#!/bin/bash
# Submit the init -> mbpt -> ac chain for the 1D H chain at $GREEN_VER.
# Usage: GREEN_VER=v100a0 bash systems/h_chain/submit.sh
# SLURM resources come from env.sh (per-phase SLURM_* defaults); overrides below preserve the tuned values (also GREEN_VER may be v032_patched).
set -euo pipefail

export SYSTEM=h_chain

# per-system resource overrides (else env.sh defaults apply)
export SLURM_INIT_TIME=00:20:00
export SLURM_MBPT_NODES=1
export SLURM_MBPT_NTASKS_PER_NODE=2
export SLURM_MBPT_EXTRA=""
export SLURM_MBPT_TIME=04:00:00
export SLURM_AC_NTASKS_PER_NODE=8
export SLURM_AC_TIME=02:00:00

source "$(dirname "${BASH_SOURCE[0]}")/../../tools/submit_chain.sh"
