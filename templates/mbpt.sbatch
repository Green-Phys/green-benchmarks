#!/bin/bash
# templates/mbpt.sbatch — MAIN MBPT job (the heavy one).
#
# MPI binary phase: green-mbpt runs hf, optionally mp2, then gw.
# Resources (nodes, ntasks-per-node) come from systems/<sys>/submit.sh.
#
# Contract (do not break):
#   In env :   BENCH_ROOT, BENCH_SCRATCH, SYSTEM, MANIFEST, GREEN_VER
#   In files:  $BENCH_SCRATCH/$GREEN_VER/$SYSTEM/init/input.h5
#   Out:       $BENCH_SCRATCH/$GREEN_VER/$SYSTEM/mbpt/out.h5
#              parseable log alongside, exit 0 on success

#SBATCH --job-name=bench-mbpt

set -euo pipefail
source "$BENCH_ROOT/env.sh"
source "$BENCH_ROOT/tools/activate_env.sh"

# Kernel + output subdir. Defaults reproduce the original CPU behaviour
# (subdir "mbpt", no --kernel flag). The GPU job sets MBPT_KERNEL=GPU and
# MBPT_SUBDIR=mbpt_gpu (see tools/submit_chain.sh) so it writes to a separate
# dir and does not clobber the CPU results.
MBPT_KERNEL="${MBPT_KERNEL:-CPU}"
MBPT_SUBDIR="${MBPT_SUBDIR:-mbpt}"
# cuda low-memory flags apply only to GPU runs; both move together via one
# knob (default true). n2's full-memory diagnostic run sets it false.
MBPT_CUDA_LOW_MEM="${MBPT_CUDA_LOW_MEM:-true}"
KERNEL_FLAG=""
if [[ "$MBPT_KERNEL" != "CPU" ]]; then
    KERNEL_FLAG="--kernel $MBPT_KERNEL"
    if [[ "$MBPT_KERNEL" == GPU ]]; then
        KERNEL_FLAG="$KERNEL_FLAG --cuda_low_gpu_memory $MBPT_CUDA_LOW_MEM --cuda_low_cpu_memory $MBPT_CUDA_LOW_MEM"
    fi
fi

INPUT="$BENCH_SCRATCH/$GREEN_VER/$SYSTEM/init/input.h5"
WORK="$BENCH_SCRATCH/$GREEN_VER/$SYSTEM/$MBPT_SUBDIR"
mkdir -p "$WORK"
cd "$WORK"

export OMP_NUM_THREADS=${SLURM_CPUS_PER_TASK:-1}
export MKL_NUM_THREADS=${SLURM_CPUS_PER_TASK:-1}
export HDF5_USE_FILE_LOCKING=FALSE

# Pull manifest values into separate vars (one python call per value
# so whitespace inside a value can't poison the others).
_yaml="import yaml,sys; m=yaml.safe_load(open('$MANIFEST'));"
KIND=$(python -c "$_yaml print(m['system']['kind'])")
METHODS=$(python -c "$_yaml print(' '.join(x['type'].upper() for x in m['methods']))")
GRID_FILE=$(python -c "$_yaml print(m.get('mesh',{}).get('grid_file','ir/1e4.h5'))")
BETA=$(python -c "$_yaml print(m.get('mesh',{}).get('beta',100))")

# Inputs are the init phase outputs (absolute paths so $WORK can move).
# Solids produce separate Coulomb / HF-exchange integral dirs; molecular
# init produces a single dir, so both point at the same df_hf_int.
INIT_DIR="$BENCH_SCRATCH/$GREEN_VER/$SYSTEM/init"
DF_HF_INT="$INIT_DIR/df_hf_int"
if [[ "$KIND" == solid ]]; then
    DF_INT="$INIT_DIR/df_int"
else
    DF_INT="$DF_HF_INT"
fi

for scf_type in $METHODS; do
    echo "=== mbpt $GREEN_VER on $SYSTEM :: $scf_type ==="
    OUT="$WORK/out_${scf_type,,}.h5"
    # itermax from the manifest's per-method spec; mbpt.exe defaults to 1,
    # which silently under-converges GW.
    ITERMAX=$(python -c "$_yaml print(next((x.get('itermax',1) for x in m['methods'] if x['type'].upper()=='$scf_type'),1))")
    # Binary lives at $GREEN_ROOT/bin/mbpt.exe (on PATH via activate_env.sh).
    # Full self-energy mixing (alpha=1.0 => take the full new sigma each
    # iteration, no damping). Other params (diis, threshold, …) take defaults.
    srun mbpt.exe \
        --verbose          4 \
        --scf_type         "$scf_type" \
        --itermax          "$ITERMAX" \
        --mixing_type      SIGMA_MIXING \
        --mixing_alpha     1.0 \
        --input_file       "$INPUT" \
        --dfintegral_file  "$DF_INT" \
        --dfintegral_hf_file "$DF_HF_INT" \
        --grid_file        "$GRID_FILE" \
        --BETA             "$BETA" \
        --results_file     "$OUT" \
        --restart          false \
        $KERNEL_FLAG
done

# When analytic continuation is skipped for this system (SKIP_AC=1, set in
# the system's submit.sh), ac.sbatch — which normally calls
# tools/extract_results.py — never runs. Do the energy-only extraction here
# instead. Spectral observables (vbm/cbm/gaps) need the AC output and are
# simply omitted; extract_results degrades gracefully when it's absent.
if [[ "${SKIP_AC:-0}" == 1 ]]; then
    echo "=== SKIP_AC=1: extracting energies (no analytic continuation) ==="
    python "$BENCH_ROOT/tools/extract_results.py" \
        --system   "$SYSTEM" \
        --manifest "$MANIFEST" \
        --work-dir "$BENCH_SCRATCH/$GREEN_VER/$SYSTEM" \
        --kernel   "$([[ "$MBPT_KERNEL" == GPU ]] && echo gpu || echo cpu)" \
        ${MBPT_VARIANT:+--variant "$MBPT_VARIANT"}
fi
