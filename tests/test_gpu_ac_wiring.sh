#!/bin/bash
set -uo pipefail
cd "$(dirname "${BASH_SOURCE[0]}")/.."
fail=0
grep -q 'AC_SUBDIR' templates/ac.sbatch || { echo "ac.sbatch not subdir-parametrized"; fail=1; }
grep -q 'AC_GPU_JID' tools/submit_chain.sh || { echo "submit_chain has no gpu-source AC job"; fail=1; }
grep -q 'AC_SUBDIR=ac_gpu' tools/submit_chain.sh || { echo "gpu-source AC not writing ac_gpu"; fail=1; }
grep -q 'MBPT_SUBDIR_FOR_AC=mbpt_gpu' tools/submit_chain.sh || { echo "gpu-source AC not reading mbpt_gpu"; fail=1; }
# GPU resource request is a configurable pass-through, not a hardwired gpu gres:
# pauli schedules blackwell as whole CPU nodes (no gpu gres), so the default
# must emit no --gres/--gpus-* at all. Clusters that DO schedule GPUs set
# SLURM_MBPT_GPU_GRES="--gres=gpu:N".
grep -q 'SLURM_MBPT_GPU_GRES' tools/submit_chain.sh || { echo "GPU job gres not configurable via SLURM_MBPT_GPU_GRES"; fail=1; }
grep -q 'gpus-per-node' tools/submit_chain.sh && { echo "GPU job still hardwires --gpus-per-node gres"; fail=1; }
bash -n templates/ac.sbatch && bash -n tools/submit_chain.sh || { echo "syntax"; fail=1; }
[[ $fail == 0 ]] && echo "gpu-ac OK" || exit 1
