#!/bin/bash
set -uo pipefail
cd "$(dirname "${BASH_SOURCE[0]}")/.."
fail=0
grep -q 'AC_SUBDIR' templates/ac.sbatch || { echo "ac.sbatch not subdir-parametrized"; fail=1; }
grep -q 'AC_GPU_JID' tools/submit_chain.sh || { echo "submit_chain has no gpu-source AC job"; fail=1; }
grep -q 'AC_SUBDIR=ac_gpu' tools/submit_chain.sh || { echo "gpu-source AC not writing ac_gpu"; fail=1; }
grep -q 'MBPT_SUBDIR_FOR_AC=mbpt_gpu' tools/submit_chain.sh || { echo "gpu-source AC not reading mbpt_gpu"; fail=1; }
bash -n templates/ac.sbatch && bash -n tools/submit_chain.sh || { echo "syntax"; fail=1; }
[[ $fail == 0 ]] && echo "gpu-ac OK" || exit 1
