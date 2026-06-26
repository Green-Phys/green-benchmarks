#!/bin/bash
# tools/activate_env.sh — resolve $GREEN_VER to the right green-mbpt
# install + green-mbtools conda env, using env.sh.
#
# Sourced (not exec'd) from every templates/*.sbatch *after* env.sh.
#
# Requires set:
#   GREEN_VER                 v032 | v100a0 | v032_patched
#   GREEN_ROOT_V032           install prefix for green-mbpt 0.3.2
#   GREEN_ROOT_V100A0         install prefix for green-mbpt 1.0.0a0
#   MBTOOLS_V032_CONDA_ENV    e.g. mbtools-v0.3.0
#   MBTOOLS_V100A0_CONDA_ENV  e.g. mbtools-v1.0.0
#   CONDA_BASE                conda installation root

set -u

case "${GREEN_VER:-}" in
  v032)
    GREEN_ROOT="$GREEN_ROOT_V032"
    CONDA_ENV="$MBTOOLS_V032_CONDA_ENV"
    ;;
  v100a0)
    GREEN_ROOT="$GREEN_ROOT_V100A0"
    CONDA_ENV="$MBTOOLS_V100A0_CONDA_ENV"
    ;;
  v032_patched)
    # patched diagnostic run: v032 solver/env + v032 grid, with v100a0's
    # (symmetric) Fock swapped into input.h5 by templates/init.sbatch.
    GREEN_ROOT="$GREEN_ROOT_V032"
    CONDA_ENV="$MBTOOLS_V032_CONDA_ENV"
    ;;
  *)
    echo "activate_env.sh: GREEN_VER must be v032, v100a0 or v032_patched, got '${GREEN_VER:-}'" >&2
    return 2 2>/dev/null || exit 2
    ;;
esac

# green-mbpt binary
export PATH="$GREEN_ROOT/bin:$PATH"
export LD_LIBRARY_PATH="$GREEN_ROOT/lib:${LD_LIBRARY_PATH:-}"

# green-mbtools conda env
[[ -f "$CONDA_BASE/etc/profile.d/conda.sh" ]] || {
  echo "conda.sh not found at $CONDA_BASE/etc/profile.d/conda.sh" >&2
  return 3 2>/dev/null || exit 3
}
# shellcheck disable=SC1091
source "$CONDA_BASE/etc/profile.d/conda.sh"
conda activate "$CONDA_ENV" || {
  echo "conda activate failed for env: $CONDA_ENV" >&2
  return 4 2>/dev/null || exit 4
}

echo "activate_env: GREEN_VER=$GREEN_VER  GREEN_ROOT=$GREEN_ROOT  conda=$CONDA_ENV"
