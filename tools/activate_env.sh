#!/bin/bash
# tools/activate_env.sh — resolve $GREEN_VER to the right green-mbpt
# install + green-mbtools conda env, using env.sh.
#
# Sourced (not exec'd) from every templates/*.sbatch *after* env.sh.
#
# Version-agnostic: for a tag $GREEN_VER it looks up GREEN_ROOT_<tag> and
# MBTOOLS_<tag> from env.sh by shell indirection — no per-version case arms
# here. Adding a release is purely an env.sh change (define its two vars).
#
# Requires set (in env.sh):
#   GREEN_VER            the version tag, e.g. v032 | v100a0 (optionally with a
#                        "_patched" suffix — a diagnostic run that reuses the
#                        base version's install/env while init.sbatch swaps in
#                        the other version's symmetric Fock)
#   GREEN_ROOT_<tag>     install prefix for green-mbpt <tag>, e.g. GREEN_ROOT_v032
#   MBTOOLS_<tag>        conda env name for green-mbtools <tag>, e.g. MBTOOLS_v032
#   CONDA_BASE           conda installation root

set -u

# A "_patched" diagnostic run reuses the base version's install + conda env.
BASE_VER="${GREEN_VER:-}"
BASE_VER="${BASE_VER%_patched}"

if [[ -z "$BASE_VER" ]]; then
  echo "activate_env.sh: GREEN_VER must be set (e.g. v032, v100a0)" >&2
  return 2 2>/dev/null || exit 2
fi

# Indirect lookup: GREEN_ROOT_<tag> / MBTOOLS_<tag>. Needs a tag with only
# valid variable-name characters (no dots) — see env.sh VERSION_OLD/NEW note.
_root_var="GREEN_ROOT_${BASE_VER}"
_env_var="MBTOOLS_${BASE_VER}"
GREEN_ROOT="${!_root_var:-}"
CONDA_ENV="${!_env_var:-}"

if [[ -z "$GREEN_ROOT" || -z "$CONDA_ENV" ]]; then
  echo "activate_env.sh: no install/env for GREEN_VER='${GREEN_VER:-}' — set $_root_var and $_env_var in env.sh" >&2
  return 2 2>/dev/null || exit 2
fi

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
