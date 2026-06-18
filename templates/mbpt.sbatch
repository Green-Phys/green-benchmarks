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

export OMP_NUM_THREADS=1   # MPI-bound; threading off for predictable scaling

# Drive method list out of the manifest. Each method is one mbpt invocation;
# they share $INPUT and append into $WORK/out.h5 under a per-method group.
methods=$(python -c "
import yaml, sys
with open('$MANIFEST') as f: m = yaml.safe_load(f)
print(' '.join(x['type'] for x in m['methods']))
")
for method in $methods; do
    echo "=== mbpt $GREEN_VER on $SYSTEM :: $method ==="
    # TODO confirm exact mbpt CLI on pauli; this assumes
    # `mbpt --method <hf|mp2|gw> --input <h5> --manifest <yaml> --out <h5>`
    srun --mpi=pmi2 mbpt \
        --method   "$method" \
        --input    "$INPUT" \
        --manifest "$MANIFEST" \
        --out      "$WORK/out.h5"
done
