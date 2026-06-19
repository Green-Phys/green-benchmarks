#!/bin/bash
# templates/mbpt.sbatch — MAIN MBPT job (the heavy one).
#
# MPI binary phase: green-mbpt runs hf, optionally mp2, then gw.
# Resources (nodes, ntasks-per-node) come from systems/<sys>/submit.sh.
#
# Contract (do not break):
#   In env :   BENCH_ROOT, BENCH_SCRATCH, SYSTEM, MANIFEST, GREEN_VER
#   In files:  $BENCH_SCRATCH/$SYSTEM/init/input.h5
#   Out:       $BENCH_SCRATCH/$SYSTEM/mbpt/$GREEN_VER/out.h5
#              parseable log alongside, exit 0 on success

#SBATCH --job-name=bench-mbpt
#SBATCH --output=%x-%j.out

set -euo pipefail
source "$BENCH_ROOT/env.sh"
source "$BENCH_ROOT/tools/activate_env.sh"

INPUT="$BENCH_SCRATCH/$SYSTEM/init/input.h5"
WORK="$BENCH_SCRATCH/$SYSTEM/mbpt/$GREEN_VER"
mkdir -p "$WORK"
cd "$WORK"

export OMP_NUM_THREADS=${SLURM_CPUS_PER_TASK:-1}
export MKL_NUM_THREADS=${SLURM_CPUS_PER_TASK:-1}

# Drive method list out of the manifest. Each method is one mbpt invocation;
# they share $INPUT and append into $WORK/out.h5 under a per-method group.
methods=$(python -c "
import yaml, sys
with open('$MANIFEST') as f: m = yaml.safe_load(f)
print(' '.join(x['type'] for x in m['methods']))
")
for method in $methods; do
    echo "=== mbpt $GREEN_VER on $SYSTEM :: $method ==="
    # Binary lives at $GREEN_ROOT/bin/mbpt.exe (already on PATH).
    # TODO confirm CLI flags via `mbpt.exe --help` on pauli.
    srun mbpt.exe \
        --scf_type   "$method" \
        --input    "$INPUT" \
        --manifest "$MANIFEST" \
        --out      "$WORK/out.h5"
done
