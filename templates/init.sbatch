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
#   Out:      $BENCH_SCRATCH/$SYSTEM/init/$GREEN_VER/{input.h5, df_hf_int/, df_int/}
#             exit 0 on success; non-zero aborts the chain

#SBATCH --job-name=bench-init

set -euo pipefail
source "$BENCH_ROOT/env.sh"
source "$BENCH_ROOT/tools/activate_env.sh"

WORK="$BENCH_SCRATCH/$SYSTEM/init/$GREEN_VER"
mkdir -p "$WORK"
cd "$WORK"

export OMP_NUM_THREADS=${SLURM_CPUS_PER_TASK:-16}
export MKL_NUM_THREADS=${SLURM_CPUS_PER_TASK:-16}

# Patched diagnostic run (GREEN_VER=<base>_patched): skip the fresh pyscf
# init; take the base version's grid + integrals and swap in the other
# version's (symmetric) HF Fock/S/H. Currently v032 grid + v100a0 Fock.
# Requires the base and HF-source inits to already exist (runs a and b).
if [[ "$GREEN_VER" == *_patched ]]; then
    BASE_VER="${GREEN_VER%_patched}"     # e.g. v032
    HF_VER="v100a0"                      # symmetric-Fock source
    BASE_DIR="$BENCH_SCRATCH/$SYSTEM/init/$BASE_VER"
    HF_DIR="$BENCH_SCRATCH/$SYSTEM/init/$HF_VER"
    for d in "$BASE_DIR" "$HF_DIR"; do
        [[ -f "$d/input.h5" ]] || {
            echo "patched init needs $d/input.h5 (run $BASE_VER and $HF_VER first)" >&2
            exit 2; }
    done
    echo "=== patched init for $SYSTEM: $BASE_VER grid + $HF_VER Fock ==="
    python "$BENCH_ROOT/tools/patch_input.py" \
        --base    "$BASE_DIR/input.h5" \
        --hf-from "$HF_DIR/input.h5" \
        --out     "$WORK/input.h5"
    # reuse the base version's integrals + grid (same full k-mesh)
    ln -sfn "$BASE_DIR/df_int"    "$WORK/df_int"
    ln -sfn "$BASE_DIR/df_hf_int" "$WORK/df_hf_int"
    exit 0
fi

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
