# ADMIN.md — succession guide for green-benchmarks

If you are reading this you are (or are about to become) the person
running the Green-ecosystem HPC regression suite. This document is the
contract: every command needed to go from "fresh login on pauli" to
"new release's results committed" lives here.

If you discover tribal knowledge that is _not_ in this file, please
add it. The repo's bus factor is "whoever can run this." Make it bigger.

---

## 0. One-time pauli setup

Clone the repo and copy the env template:

```bash
ssh pauli
git clone <this repo> ~/green-benchmarks
cd ~/green-benchmarks
cp env.sh.template env.sh
$EDITOR env.sh         # fill in TBD entries — see comments inside
```

`env.sh` is gitignored. It must define, at minimum:

| Var                     | What                                                       |
|-------------------------|------------------------------------------------------------|
| `BENCH_ROOT`            | absolute path of this repo on pauli                        |
| `BENCH_SCRATCH`         | scratch root for heavy outputs (large/writable, e.g. `/pauli-storage`) |
| `SLURM_PARTITION_MBPT`  | fast pauli queue used for the heavy MBPT job               |
| `SLURM_PARTITION_AUX`   | regular pauli queue for init (MF + integrals) and AC       |
| `SLURM_ACCOUNT`         | optional, comment out if unused                            |
| `GREEN_ROOT_V032`       | install prefix for green-mbpt 0.3.2 binaries               |
| `GREEN_ROOT_V100A0`     | install prefix for green-mbpt 1.0.0a0 binaries             |
| `GREEN_AC`              | dir with `ac.exe` (green-ac build; same across versions)   |
| `MBTOOLS_V032_CONDA_ENV`| conda env name for green-mbtools 0.3.0 (e.g. `mbtools-v0.3.0`) |
| `MBTOOLS_V100A0_CONDA_ENV` | conda env name for green-mbtools 1.0.0a0               |
| `CONDA_BASE`            | conda installation root (`$HOME/miniconda3`, `/opt/conda`) |

Each conda env owns its python + green-mbtools install (including the
compiled C++ extensions). `activate_env.sh` runs `conda activate $env`
based on `$GREEN_VER`.

Confirm both Green installs are reachable:

```bash
source env.sh
for v in v032 v100a0; do
  GREEN_VER=$v bash -c 'source tools/activate_env.sh && \
      mbpt.exe --help && \
      python -c "from importlib.metadata import version; print(version(\"green-mbtools\"))"'
done
```

`mbpt.exe` has no `--version`; `--help` prints the build's git hashes,
which is enough to confirm the right install is on `PATH` for now.

If either fails: stop. Do not proceed until both versions are
loadable. The whole point of the suite is comparing across them.

---

## 1. SLURM job templates

The three job templates live under [`templates/`](templates):

| File                       | Purpose                                                       |
|----------------------------|---------------------------------------------------------------|
| `templates/init.sbatch`    | pyscf mean-field + green-mbtools integral dump → `input.h5`   |
| `templates/mbpt.sbatch`    | green-mbpt main calculation: HF, optionally GF2, then GW      |
| `templates/ac.sbatch`      | analytic continuation; finalizes the results JSON             |

**Drop your pauli-specific job content into these three files**.
The contract block at the top of each file lists which env vars are
set when it runs, which input files exist, and which output files
it must produce. Do not break those contracts.

Per-system `submit.sh` (under `systems/<sys>/`) chains the three
templates with `sbatch --dependency=afterok` and supplies per-system
resource flags (nodes / ntasks-per-node / time). Each system's
resource numbers were derived from `manifest.yaml#resources` plus
heuristics for the init and ac phases — adjust in the `submit.sh`
when you have real wallclock data.

---

## 2. Release procedure

For a new Green release `<mbpt-ver>` + `<mbtools-ver>`:

### 2.1 Verify manifests

```bash
python tools/verify_manifest.py systems/*/manifest.yaml
```

### 2.2 Submit the four-system suite, for each version

```bash
bash tools/run_all.sh
```

This loops every system × version and submits each as an init → mbpt →
ac chain (`sbatch --dependency=afterok`). Submit a subset with env vars:

```bash
SYSTEMS="si n2" VERSIONS="v032" bash tools/run_all.sh
```

Where the data goes:

- **Heavy outputs** (`input.h5`, `out_*.h5`, `ac_*.h5`) live under
  `$BENCH_SCRATCH` (e.g. `/pauli-storage`), never in the repo.
- The **`ac.sbatch`** step (last in the chain) extracts a small JSON
  summary into `systems/<sys>/results/<mbpt-ver>_<mbtools-ver>.json`
  **inside this repo checkout** — that JSON is the only thing committed.

Because the summary is written by the last job, a partial chain produces
no results JSON — by design.

### 2.3 Aggregate and report

Run this on pauli, in the same checkout the jobs wrote into:
`collect.py` walks `systems/*/results/*.json` (the committed summaries
the ac jobs populated) and regenerates `RESULTS.md`.

```bash
python tools/collect.py           > RESULTS.md
python tools/compare_versions.py \
    --old 0.3.2_0.3.0 \
    --new 1.0.0a0_1.0.0a0          > /tmp/cross_version_report.md
```

`compare_versions.py` emits two tables (values, timings) and a draft
one-paragraph summary keyed off `--obs-tol-percent`
(default 0.5%) and `--time-tol-percent` (default 20%). Tighten the
paragraph for the release notes.

### 2.4 Commit

```bash
git add systems/*/results/*.json RESULTS.md
git commit -m "Results for green-mbpt <mbpt-ver> + green-mbtools <mbtools-ver>"
git push
```

---

## 3. Adding a system

1. `mkdir -p systems/<new>/results`
2. Write `systems/<new>/manifest.yaml`. Run
   `python tools/verify_manifest.py systems/<new>/manifest.yaml`.
3. Inputs are generated from the manifest automatically by
   `init.sbatch` (via `tools/render_init_args.py` → Green's
   `init_data_(mol_)df.py`). If the manifest needs a new field, teach
   `render_init_args.py` to map it — there is no per-system generator.
4. Copy an existing `submit.sh` (closest workload size), adjust the
   `SYSTEM` name and the per-phase sbatch resource flags.
5. Add a row to the README's system table.

The four-systems pattern in this repo deliberately spans the
relativistic axis (none → pseudo → sfx2c1e → x2c1e). New systems
should justify their inclusion by exercising a code path that the
existing four do not.

---

## 4. When things go wrong

- **Chain breaks at init/mbpt**: the dependent jobs do not run. Look at
  the failed job's `bench-*.out`, fix, resubmit only the broken phase
  (no need to redo init if mbpt failed).
- **Manifest verification fails**: do not edit `verify_manifest.py`
  to make it pass. Fix the manifest, or extend the schema with
  explicit intent if the new field is real.
- **Cross-version diff shows huge regression**: do not paper over
  with tolerance bumps. File an issue on the source repo, link the
  benchmark run, and wait for triage.
- **HPC allocation lost**: out of scope for this repo. The suite stops
  running. This is the known bus factor.

---

## 5. Conventions

- Result filenames: `<mbpt-ver>_<mbtools-ver>.json` (e.g.
  `0.3.2_0.3.0.json`, `1.0.0a0_1.0.0a0.json`). Slightly clunky but
  unambiguous; can be made more friendly later.
- All JSON keys for observables match the manifest's `observables[].id`.
- Timing keys go under `timings:` in the JSON, separate from physical
  observables. They are tracked but never gate a release.
- Never edit `RESULTS.md` by hand. It is regenerated.
