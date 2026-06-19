#!/bin/bash
# templates/init.sbatch — INITIALIZATION job.
#
# Runs Green's own pyscf-based init script that produces input.h5 +
# df integral directories. Solid systems use init_data_df.py; molecular
# systems use init_data_mol_df.py.
#
# Single-task, multi-threaded BLAS via cpus-per-task. Resources set
# by systems/<sys>/submit.sh.
#
# Contract (do not break):
#   In env :  BENCH_ROOT, BENCH_SCRATCH, SYSTEM, MANIFEST, GREEN_VER
#   Out:      $BENCH_SCRATCH/$SYSTEM/init/{input.h5, df_hf_int/, df_int/}
#             exit 0 on success; non-zero aborts the chain

#SBATCH --job-name=bench-init

set -euo pipefail
source "$BENCH_ROOT/env.sh"
source "$BENCH_ROOT/tools/activate_env.sh"

WORK="$BENCH_SCRATCH/$SYSTEM/init"
mkdir -p "$WORK"
cd "$WORK"

export OMP_NUM_THREADS=${SLURM_CPUS_PER_TASK:-16}
export MKL_NUM_THREADS=${SLURM_CPUS_PER_TASK:-16}

# Pick init script based on system.kind (solid -> df, molecular -> mol_df)
KIND=$(python -c "import yaml; print(yaml.safe_load(open('$MANIFEST'))['system']['kind'])")
case "$KIND" in
  solid)     INIT_SCRIPT="$GREEN_ROOT/python/init_data_df.py"     ;;
  molecular) INIT_SCRIPT="$GREEN_ROOT/python/init_data_mol_df.py" ;;
  *) echo "unknown system.kind: $KIND" >&2; exit 2 ;;
esac

# render manifest -> CLI args via the shared helper
INIT_ARGS=$(python "$BENCH_ROOT/tools/render_init_args.py" --manifest "$MANIFEST")

echo "=== init for $SYSTEM ($GREEN_VER): $(basename "$INIT_SCRIPT") ==="
echo "$INIT_SCRIPT $INIT_ARGS"
eval "python \"$INIT_SCRIPT\" $INIT_ARGS"
