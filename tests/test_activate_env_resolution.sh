#!/bin/bash
# tests/test_activate_env_resolution.sh — activate_env resolves GREEN_ROOT /
# conda env by indirection on the version tag (GREEN_ROOT_<tag> / MBTOOLS_<tag>),
# with no hardwired per-version case arms. Stubs conda so the source succeeds.
set -u
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
fail=0

# No literal version case arms should remain in the resolver.
grep -Eq '^\s*v(032|100a0)[^=]*\)' "$ROOT/tools/activate_env.sh" \
  && { echo "activate_env.sh still has a hardwired version case arm"; fail=1; }

tmp="$(mktemp -d)"
trap 'rm -rf "$tmp"' EXIT
# Minimal conda stub: profile.d/conda.sh defines a no-op `conda`.
mkdir -p "$tmp/etc/profile.d"
printf 'conda() { :; }\n' > "$tmp/etc/profile.d/conda.sh"

# Arbitrary tag proves the lookup is data-driven, not hardcoded.
run() {  # run <GREEN_VER>  -> prints "GREEN_ROOT|CONDA_ENV" (last line), or nothing on failure
  GREEN_VER="$1" \
  CONDA_BASE="$tmp" \
  GREEN_ROOT_zzz9="/opt/green/zzz9" MBTOOLS_zzz9="mbtools-zzz9" \
  bash -c 'source "'"$ROOT"'/tools/activate_env.sh" 2>/dev/null && echo "RESOLVED=$GREEN_ROOT|$CONDA_ENV"' \
  | sed -n 's/^RESOLVED=//p'
}

got="$(run zzz9)"
[[ "$got" == "/opt/green/zzz9|mbtools-zzz9" ]] || { echo "indirect resolve failed: got '$got'"; fail=1; }

# _patched reuses the base tag's install/env.
gotp="$(run zzz9_patched)"
[[ "$gotp" == "/opt/green/zzz9|mbtools-zzz9" ]] || { echo "_patched resolve failed: got '$gotp'"; fail=1; }

# Unknown tag (no vars defined) must not resolve.
[[ -z "$(run nope)" ]] || { echo "unknown tag should not resolve"; fail=1; }

[[ $fail == 0 ]] && echo "test_activate_env_resolution: PASS" || echo "test_activate_env_resolution: FAIL"
exit $fail
