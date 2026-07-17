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
  si/           PBC + pseudopotential (reference solid)
  ge_sfx2c1e/   all-electron + scalar relativistic (sfx2c1e)
  ge_x2c1e/     all-electron + full X2C (spinor path)
  h_chain/      1D periodic correlation
  <13 solids>/  GW symmetry-coverage set — see "Solid-state coverage" below
tools/          collection, diff, manifest lint, version comparison
RESULTS.md      generated comparison table (do not hand-edit)
```

Each system has `manifest.yaml` (the run contract), `submit.sh` (chains
the init → mbpt → ac SLURM jobs), and `results/` (one JSON summary per
Green release). Heavy run outputs live in scratch (`$BENCH_SCRATCH`,
e.g. `/pauli-storage`) — only the extracted JSON summaries are committed
here.

## Solid-state coverage

A set of solids chosen to span distinct space groups, to exercise the k-point
symmetry machinery (symmorphic vs non-symmorphic, centrosymmetric vs polar,
insulators vs metals). Each runs **GW** on a **3×3×3** k-mesh with
`gth-dzvp-molopt-sr` / `gth-pbe` (`auxbasis: none`, `etb_beta: 2.5`), PBE
mean-field. Geometries use experimental equilibrium lattice parameters
(space group verified with spglib).

| System | Formula | SG # | Symbol | Crystal system | Atoms/cell | Notes |
|--------|---------|------|--------|----------------|-----------:|-------|
| lih     | LiH   | 225 | Fm-3m    | Cubic        | 2  | Rock-salt, symmorphic |
| si      | Si    | 227 | Fd-3m    | Cubic        | 2  | Diamond (reference, pre-existing) |
| gaas    | GaAs  | 216 | F-43m    | Cubic        | 2  | Zinc-blende, non-centrosymmetric |
| diamond | C     | 227 | Fd-3m    | Cubic        | 2  | Diamond, light atoms |
| c_bn    | BN    | 216 | F-43m    | Cubic        | 2  | Zinc-blende, non-centrosymmetric |
| na      | Na    | 229 | Im-3m    | Cubic        | 1  | BCC metal, symmorphic |
| hbn     | BN    | 194 | P6₃/mmc  | Hexagonal    | 4  | Layered, non-symmorphic, centrosymmetric |
| aln     | AlN   | 186 | P6₃mc    | Hexagonal    | 4  | Wurtzite, polar, non-centrosymmetric |
| mg      | Mg    | 194 | P6₃/mmc  | Hexagonal    | 2  | HCP metal |
| mgf2    | MgF₂  | 136 | P4₂/mnm  | Tetragonal   | 6  | Rutile-type, non-symmorphic |
| mgh2    | MgH₂  | 136 | P4₂/mnm  | Tetragonal   | 6  | Rutile-type, lightest |
| tio2    | TiO₂  | 141 | I4₁/amd  | Tetragonal   | 12 | Anatase, conventional cell, non-symmorphic |
| black_p | P     | 64  | Cmce     | Orthorhombic | 8  | Black phosphorus, conventional cell |
| al2o3   | Al₂O₃ | 167 | R-3c     | Trigonal     | 10 | Corundum, rhombohedral primitive |

Symmetry spread:
- Symmorphic: Na (229), c-BN / GaAs (216), LiH (225); all others non-symmorphic.
- Non-centrosymmetric: c-BN (216), GaAs (216), AlN (186).
- Metals: Na (229), Mg (194).
- **10 distinct space groups**: 225, 227, 216, 229, 194, 186, 136, 141, 64, 167.

TiO₂ (anatase) and black P use their **conventional** cells — PySCF detects the
full space group more reliably from conventional than from reduced primitive
cells.

## Active comparison

Initial round:

| Component     | Versions under test |
|---------------|---------------------|
| green-mbpt    | `0.3.2`, `1.0.0-alpha` |
| green-mbtools | `0.3.0`, `1.0.0-alpha` |

Results land in `systems/<sys>/results/<mbpt-version>_<mbtools-version>.json`
and aggregate to [`RESULTS.md`](RESULTS.md).

## Quick links

- Add a new release: see [`ADMIN.md`](ADMIN.md#release-procedure)
- Add a new system: see [`ADMIN.md`](ADMIN.md#adding-a-system)
- Manifest schema: [`tools/verify_manifest.py`](tools/verify_manifest.py)
