#!/bin/bash
# Submit the init -> mbpt -> ac chain for Al2O3 at $GREEN_VER.
# Usage: GREEN_VER=v100a0 bash systems/al2o3/submit.sh
# SLURM resources come from env.sh (per-phase SLURM_* defaults); tune there for your cluster.
set -euo pipefail

export SYSTEM=al2o3

source "$(dirname "${BASH_SOURCE[0]}")/../../tools/submit_chain.sh"
