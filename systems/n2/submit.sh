#!/bin/bash
# Submit the init -> mbpt -> ac chain for N2 (molecular) at $GREEN_VER.
# Usage: GREEN_VER=v100a0 bash systems/n2/submit.sh
# SLURM resources come from env.sh (per-phase SLURM_* defaults); overrides below preserve the tuned values.
set -euo pipefail

export SYSTEM=n2

# per-system resource overrides (else env.sh defaults apply)
export SLURM_INIT_TIME=00:15:00
export SLURM_MBPT_NODES=2
export SLURM_MBPT_NTASKS_PER_NODE=48
export SLURM_MBPT_TIME=00:30:00
export SLURM_AC_NTASKS_PER_NODE=1
export SLURM_AC_TIME=00:15:00

source "$(dirname "${BASH_SOURCE[0]}")/../../tools/submit_chain.sh"
