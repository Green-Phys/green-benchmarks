#!/bin/bash
# tools/run_all.sh — submit the whole benchmark matrix (systems × versions).
#
# tools/submit.sh queues one init -> mbpt -> ac chain for a single system at a
# single GREEN_VER; this driver just loops the matrix and submits them all.
#
# Where things land:
#   - Heavy run outputs (input.h5, mbpt out_*.h5, ac_*.h5) live under
#     $BENCH_SCRATCH (e.g. /pauli-storage) — NOT in this repo.
#   - The ac job extracts a small JSON summary into
#     systems/<sys>/results/<mbpt-ver>_<mbtools-ver>.json in this repo.
#   - After every chain finishes, run tools/collect.py to tabulate those
#     JSONs into RESULTS.md, then commit (see ADMIN.md §2).
#
# Usage:
#   bash tools/run_all.sh                          # ALL systems, both versions
#   SYSTEMS="si n2" VERSIONS="v032" bash tools/run_all.sh
set -euo pipefail

THIS_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
BENCH_ROOT="$(cd "$THIS_DIR/.." && pwd)"

# Pull VERSION_OLD / VERSION_NEW (the pair under comparison) from env.sh.
# env.sh is per-machine + gitignored; tolerate its absence and fall back to
# the same defaults env.sh.template ships.
[[ -f "$BENCH_ROOT/env.sh" ]] && source "$BENCH_ROOT/env.sh"
: "${VERSION_OLD:=v032}"
: "${VERSION_NEW:=v100a0}"

# Default: every system with a manifest (mirrors tools/_lib.iter_systems()).
# Override with SYSTEMS="si n2" to run a subset.
if [[ -z "${SYSTEMS:-}" ]]; then
  SYSTEMS=""
  for _m in "$BENCH_ROOT"/systems/*/manifest.yaml; do
    [[ -e "$_m" ]] || continue
    SYSTEMS+=" $(basename "$(dirname "$_m")")"
  done
fi
VERSIONS="${VERSIONS:-$VERSION_OLD $VERSION_NEW}"

# RUN_ALL_DRY=1 previews the resolved matrix without submitting anything.
if [[ "${RUN_ALL_DRY:-0}" == 1 ]]; then
  echo "systems: $SYSTEMS"
  echo "versions: $VERSIONS"
  exit 0
fi

for s in $SYSTEMS; do
  for v in $VERSIONS; do
    echo "=== submitting $s @ $v ==="
    GREEN_VER="$v" bash "$BENCH_ROOT/tools/submit.sh" "$s"
  done
done

echo
echo "All chains submitted. When they finish (check 'squeue'), tabulate with:"
echo "    python tools/collect.py > RESULTS.md"
