#!/bin/bash
# tools/run_all.sh — submit the whole benchmark matrix (systems × versions).
#
# Each systems/<sys>/submit.sh queues one init -> mbpt -> ac chain for a
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
#   bash tools/run_all.sh                          # all systems, both versions
#   SYSTEMS="si n2" VERSIONS="v032" bash tools/run_all.sh
set -euo pipefail

THIS_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
BENCH_ROOT="$(cd "$THIS_DIR/.." && pwd)"

SYSTEMS="${SYSTEMS:-n2 si ge_sfx2c1e ge_x2c1e}"
VERSIONS="${VERSIONS:-v032 v100a0}"

for s in $SYSTEMS; do
  for v in $VERSIONS; do
    echo "=== submitting $s @ $v ==="
    GREEN_VER="$v" bash "$BENCH_ROOT/systems/$s/submit.sh"
  done
done

echo
echo "All chains submitted. When they finish (check 'squeue'), tabulate with:"
echo "    python tools/collect.py > RESULTS.md"
