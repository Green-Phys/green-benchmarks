# green-benchmarks — design brief

A heavy-compute benchmark suite for the Green ecosystem (green-mbpt,
green-mbtools, green-impurity, …), intended as the **release-time HPC
regression tier**, kept separate from the fast PR-gated unit tests in
the source repos.

This document is the brief for a fresh session; it captures the design
discussion that led to this repo so a new agent (or human contributor)
can pick it up without re-deriving the choices.

---

## Scope (what belongs here, what doesn't)

| | Stays in source repos (unit tests) | Lives here (benchmarks) |
|---|---|---|
| Cadence | Per-PR, free CI | Per-release, manual / scheduled on HPC |
| Hardware | Laptop / CI runner | Supercomputer allocation |
| Examples | Orth basis-invariance on H2/cc-pVDZ (mbpt#53) | Si bands; Ge IP; α-Sn band structure |
| Trigger | `pytest` / `ctest` | Admin runs `make` / SLURM driver |

**Rule of thumb:** if a check is fast enough to gate a PR, it is a unit
test by definition and belongs in the source repo's `test/` directory.
This repo only hosts checks that genuinely need HPC.

---

## Suggested initial system list

The four-system rationale spans the relativistic axis cleanly:

| System | Type | Coverage purpose |
|---|---|---|
| N2 | molecular | basic correlation sanity (consider F2 / C6H6 instead — N2/HF is trivial) |
| Si | PBC + pseudopotential | the canonical PBC test |
| Ge | all-electron + sfx2c1e | scalar relativistic correction (the X2C-scalar code path) |
| α-Sn | all-electron + x2c1e | full relativistic via X2C (the spinor code path) |

The Ge / α-Sn pair is the one that justifies this repo most — they're
exactly where green-mbtools' X2C work and the orth refactor's spinor
path land. They were also the systems whose physics depend on correctly
implemented features that the unit tests can only partially exercise.

Possible per-system observables to track (each becomes a "comparable"
in the versioning sense — see below):

- Total energy at a fixed (method, basis, k-mesh, β, …) tuple
- Band gap / IP / EA
- Band structure along high-symmetry path
- Timing breakdowns (wall, MPI ranks, memory footprint) — these are
  perf regressions, but the same harness can record them

---

## Repo structure (proposed)

```
green-benchmarks/
├── README.md            # human-facing: what this repo is, how to run
├── ADMIN.md             # succession doc for whoever runs the suite
├── systems/
│   ├── n2/
│   │   ├── manifest.yaml        # machine-readable run spec
│   │   ├── generate.py          # produces input.h5 + fixtures
│   │   ├── run.sh               # SLURM template
│   │   └── results/
│   │       ├── 0.3.0.json       # one file per Green release
│   │       ├── 0.4.0.json
│   │       └── …
│   ├── si/                      # same shape
│   ├── ge/                      # same shape
│   └── alpha_sn/                # same shape
├── tools/
│   ├── collect.py               # aggregate results/*.json into RESULTS.md
│   ├── compare_versions.py      # compare two releases (tables + draft note)
│   └── verify_manifest.py       # CI lint for manifest schema
└── RESULTS.md                   # generated comparison table, NOT in README
```

**Why two docs (`README.md` + `ADMIN.md`)?** README is for users
("what's in this repo, what do the numbers mean"); ADMIN is the
succession doc ("you are the new admin, here's how to run a release
batch"). Mixing them risks the README rotting whenever a new admin
finds the run instructions need updating.

**Why `results/<version>.json` not in README?** The README diff churn
from per-release number updates is high enough to flood git history.
Generate a `RESULTS.md` aggregate table (committed) and link the README
to it.

---

## manifest.yaml — the contract for "what is comparable"

A central concern from the design discussion: **cross-version
comparison needs a stable observable identifier.** If v0.3 computed
"N2 IP" at HF/cc-pVDZ and v0.4 computed it at GW/cc-pVTZ, the numbers
aren't comparable. Each observable needs a fingerprint of
`(system, method, basis, grid, …)`.

Suggested schema:

```yaml
system:
  name: ge
  kind: solid       # molecular | solid
  geometry: ge.xyz  # or atoms+lattice inline
  pseudo: none      # all-electron
  relativistic: sfx2c1e
basis:
  name: tzp-dkh
  auxbasis: tzp-dkh-jkfit
mesh:
  k: [4, 4, 4]
  beta: 1000
  grid_file: ir/1e4.h5
method:
  type: gw
  itermax: 50
  threshold: 1e-9
observables:
  - id: total_energy
    units: Ha
  - id: indirect_gap
    units: eV
  - id: ip_at_gamma
    units: eV
resources:
  nodes: 4
  walltime: "6:00:00"
  partition: standard
```

The (system.name, basis.name, mesh, method.type, method.itermax)
tuple defines the comparable. Two releases' results are comparable
iff their manifests are bit-equal in those fields.

**Why YAML, not JSON?** Human-readable / editable; YAML schemas
support comments. Admins will edit these.

**Why a separate manifest per system?** Each benchmark has its own
physical parameters. Sharing the manifest across systems forces an
artificial common subset.

---

## Versioning / comparison strategy

- Each release of the upstream Green ecosystem (e.g., `green-mbpt
  0.4.0`) gets one `results/<version>.json` per system.
- `tools/collect.py` walks `systems/*/results/*.json` and writes
  `RESULTS.md` with a table per observable across versions.
- `tools/compare_versions.py --old <v_old> --new <v_new>` highlights
  deltas (value + timing tables, flagged past tolerance) — useful as a
  pre-release sanity check.
- When a new observable is added (e.g., a method that didn't exist
  in older versions), older `results/*.json` simply lack that key.
  `RESULTS.md` should render "—" rather than fail. This is the
  "graceful new-feature" case.
- When a manifest changes incompatibly (e.g., basis upgrade),
  consider it a new comparable: rename the observable id or bump a
  per-observable `comparable_version` field so the diff tool doesn't
  show a spurious regression.

---

## Admin succession (key design constraint)

The original ask was that this repo be runnable by **any future admin
or AI agent** — not just whoever set it up. That means:

1. **ADMIN.md must be self-contained.** No tribal knowledge about
   "ask Harsha for the Greatlakes module setup." Every command needed
   to go from "fresh login on HPC" to "results committed" lives in
   that file.

2. **manifest.yaml is the source of truth for run parameters.** An
   automation harness (Claude, a Slurm orchestrator, anything) can
   read `systems/<sys>/manifest.yaml`, generate the SLURM script
   from `run.sh` + manifest, submit, and on completion populate
   `results/<version>.json`.

3. **No hidden dependencies on personal infrastructure.** All scripts
   should accept paths via environment variables or CLI args; the
   default values should be "wherever the canonical Green install
   lives on the target system."

4. **The HPC allocation itself is not in this repo's scope.** ADMIN.md
   names the project / partition / nodes the suite expects but doesn't
   try to manage allocations. If the admin loses HPC access, the suite
   stops running — that's the project's known bus factor.

---

## What was deliberately rejected during design

- **Per-PR HPC runs.** Detection latency would still be too high for
  the kinds of bugs HPC tests catch (they're the long ones; mid-PR is
  the wrong feedback loop). Per-PR fast checks already live in source
  repos.
- **A README that auto-updates with results.** README diff churn,
  merge-conflict noise. Use generated `RESULTS.md`.
- **"Documentation for Claude" as a first-class concept.** The right
  framing is "machine-readable manifest" — any automation can consume
  it, AI or otherwise. Don't bake a specific AI into the design.
- **Folding the orth basis-invariance test into this repo.** That's
  fast enough to PR-gate on H2/cc-pVDZ; it lives in
  `green-mbpt/test/solvers_test.cpp` (committed in mbpt#53).

---

## Concrete next steps for the fresh session

1. **Draft `manifest.yaml` schema.** Pick a concrete example
   system (Ge is a good first one — it exercises the sfx2c1e path
   we just touched) and write its full manifest. Iterate the schema
   based on what feels right.
2. **Stand up `tools/verify_manifest.py`** as a schema lint — even
   a `jsonschema`-backed YAML check. Catches drift cheaply.
3. **Write `ADMIN.md`** before writing any system. The doc forces
   the design to confront its succession story up front.
4. **Decide on a results store format.** Plain JSON is fine; HDF5
   if the observable list grows. Start with JSON, escalate later.
5. **First real benchmark: Ge sfx2c1e GW.** Reasons:
   - exercises the X2C-scalar code path
   - all-electron so it's not pseudopotential-dependent
   - well-known reference numbers in the literature
   - one of the four systems on the design list

Defer Si and α-Sn until after Ge has proven the harness.

---

## Connections to the work that just landed

The orth refactor (green-mbtools#42, green-mbpt#53) cleaned up the
orthogonalization layer and added an HF/GW/GF2 basis-invariance
regression test on H2/cc-pVDZ at the unit-test level. Those PRs:

- demonstrated that the X2C-spinor path in `build_X_kspace_from_ao_reps`
  works end-to-end (`spinor=True` for `lowdin` and `symmetric_lowdin`).
- closed bug 2 in `natural_per_k` (S^{-1/2}·dm·S^{-1/2} formulation).
- added `symmetric_lowdin_per_k` as a distinct Hermitian variant of
  Löwdin.

The benchmark suite picks up where unit tests stop: it verifies these
features actually produce sensible physics on real systems at scale.
Ge sfx2c1e in particular is where the scalar-relativistic +
orth-rotation pipeline gets stressed.

The companion green-mbpt PR (#54) fixes a μ double-counting bug in
`inchworm_utils.get_inchworm_selfenergy`. Inchworm impurity solver
runs are themselves heavy and would be natural benchmark candidates
once a SLURM-driven impurity-solver workflow exists in the harness.
