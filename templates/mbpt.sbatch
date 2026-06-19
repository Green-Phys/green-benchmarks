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

# Inputs are the init phase outputs (absolute paths so $WORK can move).
INIT_DIR="$BENCH_SCRATCH/$SYSTEM/init"
DF_INT="$INIT_DIR/df_int"
DF_HF_INT="$INIT_DIR/df_hf_int"

# Pull method list and grid file out of the manifest in one shot.
read -r METHODS GRID_FILE < <(python -c "
import yaml
m = yaml.safe_load(open('$MANIFEST'))
methods = ' '.join(x['type'].upper() for x in m['methods'])   # hf,mp2,gw -> HF,MP2,GW
grid    = m.get('mesh', {}).get('grid_file', 'ir/1e4.h5')
print(methods, grid)
")

for scf_type in $METHODS; do
    echo "=== mbpt $GREEN_VER on $SYSTEM :: $scf_type ==="
    OUT="$WORK/out_${scf_type,,}.h5"
    # Binary lives at $GREEN_ROOT/bin/mbpt.exe (on PATH via activate_env.sh).
    # Other params (mixing, diis, itermax, threshold, …) take mbpt.exe defaults.
    srun mbpt.exe \
        --verbose          4 \
        --scf_type         "$scf_type" \
        --input_file       "$INPUT" \
        --dfintegral_file  "$DF_INT" \
        --dfintegral_hf_file "$DF_HF_INT" \
        --grid_file        "$GRID_FILE" \
        --results_file     "$OUT" \
        --restart          false
done
