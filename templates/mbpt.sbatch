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
KERNEL_FLAG=""
[[ "$MBPT_KERNEL" != "CPU" ]] && KERNEL_FLAG="--kernel $MBPT_KERNEL"

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
GRID_FILE=$(python -c "$_yaml print(m.get('mesh',{}).get('grid_file','ir/1e4.h5'))")
BETA=$(python -c "$_yaml print(m.get('mesh',{}).get('beta',100))")

# Per-method plan for THIS kernel, from the shared planner (so it matches what
# extract_results later reports). Tab-separated: output_tag / scf_type / itermax
# / cuda_low_gpu_memory / cuda_low_cpu_memory. A GPU-only method (n2's
# full-memory gw_fullmem) appears only when MBPT_KERNEL=GPU.
KERNEL_LC=$([[ "$MBPT_KERNEL" == GPU ]] && echo gpu || echo cpu)
METHOD_TABLE=$(python -c "
import sys; sys.path.insert(0, '$BENCH_ROOT/tools')
from _lib import load_manifest, methods_for_kernel
for x in methods_for_kernel(load_manifest('$MANIFEST'), '$KERNEL_LC'):
    print('\t'.join([x['output_tag'], x['type'], str(x['itermax']),
                     str(x['cuda_low_gpu_memory']).lower(),
                     str(x['cuda_low_cpu_memory']).lower()]))
")

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

# One srun per method. OUTPUT_TAG names the output (out_<tag>.h5) and report
# key; a variant reuses an scf_type under a distinct tag (e.g. gw_fullmem -> gw).
# The method table is fed to the loop on stdin (via `done <<<`), and srun reads
# stdin — so without `srun ... </dev/null` below, the first method's srun would
# swallow the remaining rows and only that method would run.
while IFS=$'\t' read -r OUTPUT_TAG SCF_TYPE ITERMAX CUDA_GPU CUDA_CPU; do
    [[ -z "$OUTPUT_TAG" ]] && continue
    echo "=== mbpt $GREEN_VER on $SYSTEM :: $OUTPUT_TAG ==="
    OUT="$WORK/out_${OUTPUT_TAG,,}.h5"
    # cuda low-memory flags apply only to GPU runs (both from the manifest
    # method; default true). n2's gw_fullmem sets them false.
    CUDA_FLAGS=""
    [[ "$MBPT_KERNEL" == GPU ]] && CUDA_FLAGS="--cuda_low_gpu_memory $CUDA_GPU --cuda_low_cpu_memory $CUDA_CPU"
    # Binary lives at $GREEN_ROOT/bin/mbpt.exe (on PATH via activate_env.sh).
    # Full self-energy mixing (alpha=1.0 => take the full new sigma each
    # iteration, no damping). Other params (diis, threshold, …) take defaults.
    srun mbpt.exe \
        --verbose          4 \
        --scf_type         "${SCF_TYPE^^}" \
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
        $KERNEL_FLAG $CUDA_FLAGS </dev/null
done <<< "$METHOD_TABLE"

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
        --kernel   "$([[ "$MBPT_KERNEL" == GPU ]] && echo gpu || echo cpu)"
fi
