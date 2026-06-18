# green-benchmarks

Release-time HPC regression suite for the Green ecosystem
(`green-mbpt`, `green-mbtools`, …). Complements the per-PR unit tests
in the source repos by running calculations that genuinely need a
supercomputer allocation.

See [`DESIGN_BRIEF.md`](DESIGN_BRIEF.md) for the rationale and design
discussion. See [`ADMIN.md`](ADMIN.md) for the operational guide.

## What's in here

```
systems/
  n2/           molecular, basic correlation sanity
  si/           PBC + pseudopotential
  ge_sfx2c1e/   all-electron + scalar relativistic (sfx2c1e)
  ge_x2c1e/     all-electron + full X2C (spinor path)
tools/          collection, diff, manifest lint, version comparison
RESULTS.md      generated comparison table (do not hand-edit)
```

Each system has `manifest.yaml` (the run contract), `generate.py`
(produces inputs), `run.sh` (SLURM template), and `results/` (one
JSON file per Green release).

## Active comparison

Initial round:

| Component     | Versions under test |
|---------------|---------------------|
| green-mbpt    | `0.3.2`, `1.0.0a0`  |
| green-mbtools | `0.3.0`, `1.0.0a0`  |

Results land in `systems/<sys>/results/<mbpt-version>_<mbtools-version>.json`
and aggregate to [`RESULTS.md`](RESULTS.md).

## Quick links

- Add a new release: see [`ADMIN.md`](ADMIN.md#release-procedure)
- Add a new system: see [`ADMIN.md`](ADMIN.md#adding-a-system)
- Manifest schema: [`tools/verify_manifest.py`](tools/verify_manifest.py)
