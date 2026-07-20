#!/bin/bash
# tools/submit.sh — queue the init -> mbpt -> ac chain for ONE system.
#
# Usage:
#   GREEN_VER=v100a0 bash tools/submit.sh <system>
#   GREEN_VER=v032_patched bash tools/submit.sh <system>   # patched diagnostic
#
# Per-system SLURM/behaviour overrides live in systems/<system>/overrides.sh
# (sourced if present); otherwise the per-phase defaults from env.sh apply.
# There is no per-system submit script — this one driver serves every system.
set -euo pipefail

SYSTEM="${1:?usage: [GREEN_VER=...] bash tools/submit.sh <system>}"
export SYSTEM
BENCH_ROOT="${BENCH_ROOT:-$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)}"

_overrides="$BENCH_ROOT/systems/$SYSTEM/overrides.sh"
[[ -f "$_overrides" ]] && source "$_overrides"

source "$BENCH_ROOT/tools/submit_chain.sh"
