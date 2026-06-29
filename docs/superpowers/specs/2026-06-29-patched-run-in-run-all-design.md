# Opt-in `v032_patched` diagnostic in `run_all` — design

**Date:** 2026-06-29

## Context & goal

The `v032_patched` diagnostic run (v0.3.2 grid/integrals/solver, with v1.0.0a0's
symmetric HF `Fock`/`S`/`H` swapped into `input.h5`) isolates whether the
asymmetric init Fock — not the solver — drives the v032↔v100a0 disagreement on the
relativistic Ge systems. Today it runs only as a manual
`GREEN_VER=v032_patched bash systems/<sys>/submit.sh`, *after* that system's `v032`
and `v100a0` inits already exist on disk.

**Goal:** let `tools/run_all.sh` optionally submit the patched chains for the Ge
systems in the same one-command invocation, with SLURM ordering handled
automatically — while keeping it **opt-in, off by default, and trivially removable**
next release. The patched diagnostic is temporary: it exists only for the
0.3.2-vs-1.0.0a0 round; future releases won't have a "patched" version, so the design
must not leave cruft in the permanent driver.

## Key structural fact

A system's patched run depends **only on that system's `v032` and `v100a0` `init`
jobs** — it reads their `input.h5` and symlinks v032's `df_int`/`df_hf_int`. It does
*not* need their `mbpt`/`ac` chains. So the coordination is just "wait for two init
jobs," not "wait for two whole chains."

## Design

### 1. `submit.sh` — two small, general capabilities (all 5 system `submit.sh`)

Both are general (not patched-specific) and harmless, so they can stay after the
diagnostic is retired.

1. **Emit the init job id.** After the init `sbatch`:
   ```sh
   echo "$INIT_JID" > "$BENCH_SCRATCH/$SYSTEM/init/$GREEN_VER/.init_jid"
   ```
2. **Accept an optional incoming init dependency.** If `$INIT_DEPENDENCY` is set, add
   `--dependency=$INIT_DEPENDENCY` to the **init** `sbatch` (the init job currently has
   no dependency). `mbpt`/`ac` keep their existing internal `afterok` deps unchanged.

### 2. `run_all.sh` — opt-in patched pass (default off)

After the existing system × version matrix loop, append:
```sh
for s in ${PATCHED:-}; do          # e.g. PATCHED="ge_sfx2c1e ge_x2c1e"; empty = no-op
    j032=$(cat "$BENCH_SCRATCH/$s/init/v032/.init_jid"   2>/dev/null) \
        || { echo "skip patched $s: no v032 init this run"; continue; }
    j100=$(cat "$BENCH_SCRATCH/$s/init/v100a0/.init_jid" 2>/dev/null) \
        || { echo "skip patched $s: no v100a0 init this run"; continue; }
    INIT_DEPENDENCY="afterok:$j032:$j100" GREEN_VER=v032_patched \
        bash "$BENCH_ROOT/systems/$s/submit.sh"
done
```
The patched **init (patch) job waits on both Ge inits**; `mbpt`/`ac` then proceed
normally; `extract_results` already tags the result `0.3.2-patched` so it doesn't
collide with pure v032.

### 3. `collect.py` — unchanged, manual

No change. `run_all` only submits; `collect.py` is run manually after jobs finish.
It globs all `systems/*/results/*.json`, so the patched
`0.3.2-patched_0.3.0.json` is picked up as an extra column automatically.

## Invocation

```sh
PATCHED="ge_sfx2c1e ge_x2c1e" bash tools/run_all.sh   # matrix + patched diagnostic
bash tools/run_all.sh                                  # unchanged behavior
```

## Edge cases / guards

- A `PATCHED` system not run at **both** `v032` and `v100a0` in this invocation has no
  `.init_jid` files → skip with a warning (no patched submission).
- `INIT_DEPENDENCY` is applied **only** to the init job; the chain's own
  `afterok` deps are untouched.
- `afterok:<v032_init>:<v100a0_init>` → the patched init runs only if **both** inits
  succeed; if either fails, the patched chain is cancelled by SLURM (correct).

## Retire next release

Delete the `PATCHED` loop (~6 lines) from `run_all.sh`. The two `submit.sh` additions
are general; keep them or revert. `v032_patched` in `activate_env.sh`/`init.sbatch`
can be removed separately when the diagnostic is fully retired.

## Testing

- `bash -n` on every edited script.
- `run_all` with `PATCHED` set but no `.init_jid` present → prints skip warnings, makes
  no patched submission (and no errors under `set -euo pipefail`).
- On pauli, one Ge system end-to-end: `PATCHED` run produces
  `0.3.2-patched_0.3.0.json`, and `squeue` shows the patched init held until both
  inits finish.

## Noted, not addressed now

The 5 system `submit.sh` files are near-identical copies; applying the same two-line
change to each highlights that duplication. Not refactoring it here (out of scope, and
the patched diagnostic is temporary) — flagged for a possible future consolidation into
a shared submit driver.
