#!/usr/bin/env python3
"""Parse a finished green-mbpt run and persist a results JSON.

Called at the end of templates/ac.sbatch. Reads:
  - the manifest (for the canonical observable id list + units)
  - whatever green-mbpt/green-ac wrote into $BENCH_SCRATCH/<ver>/<sys> (the
    mbpt out_*.h5, the ac ac_*.h5, and logs)

Writes systems/<sys>/results/<mbpt-ver>_<mbtools-ver>.json via
_lib.write_result (schema 3: one block per method under "methods", each
{name, energies, final_iter, timings, spectral?}).

NOTE: energies are per-iteration from each method's out_*.h5 (every iter,
plus final_iter); timings are the first-iteration value from the mbpt SLURM
log (later iters accumulate in 0.3.2/1.0.0a0); spectral observables (IP /
homo / lumo; band gap / vbm / cbm) come from the green-ac output. Versions: mbpt
from the $GREEN_ROOT install dir (no semver in the binary), mbtools from
its version.py / installed distribution metadata.
"""
from __future__ import annotations

import argparse
import os
import re
import sys
import time
from pathlib import Path

from _lib import load_manifest, write_result, methods_for_kernel


def _mbpt_version() -> str:
    """green-mbpt is a C++ binary with no Python module, and `mbpt.exe
    --help` prints only git hashes (no semver). Take the release from the
    versioned install dir, e.g. .../mbpt-cpu-install-v0.3.2 -> 0.3.2. Fall
    back to $GREEN_VER, then 'unknown'."""
    name = Path(os.environ.get("GREEN_ROOT", "")).name
    m = re.search(r"v(\d[\w.]*)$", name)
    if m:
        return m.group(1)
    return os.environ.get("GREEN_VER") or "unknown"


def _mbtools_version() -> str:
    """green-mbtools version: new releases expose green_mbtools.version
    .__version__; 0.3.x has no version.py, so fall back to the installed
    distribution metadata."""
    try:
        from green_mbtools.version import __version__
        return __version__
    except Exception:
        pass
    try:
        from importlib.metadata import version
        return version("green-mbtools")
    except Exception:
        return "unknown"


def _detect_versions() -> tuple[str, str]:
    """(mbpt, mbtools) version strings used for the results filename."""
    mbpt = _mbpt_version()
    if os.environ.get("GREEN_VER", "").endswith("_patched"):
        mbpt += "-patched"   # distinct tag so it doesn't collide with base
    return mbpt, _mbtools_version()


def _green_ver() -> str:
    """The version tag (v032 / v100a0) this run was launched with."""
    return os.environ.get("GREEN_VER", "")


def _mbpt_log(work_dir: Path, kernel: str = "cpu") -> Path | None:
    """Newest mbpt SLURM output (bench-mbpt-<jobid>.out) for this version."""
    subdir = "mbpt_gpu" if kernel == "gpu" else "mbpt"
    logs = sorted((work_dir / subdir).glob("bench-mbpt-*.out"))
    return logs[-1] if logs else None


def _ac_output(work_dir: Path, kernel: str = "cpu") -> Path:
    """green-ac output (spectral function) for this version."""
    subdir = "ac_gpu" if kernel == "gpu" else "ac"
    return work_dir / subdir / "ac_gw.h5"


# Number token: optional sign, decimal, exponent.
_NUM = r"[-+]?[0-9]+(?:\.[0-9]+)?(?:[eE][+-]?[0-9]+)?"

# Hartree -> eV, for the spectral observables (all reported in eV).
_AU2EV = 27.211


def _event_avg_all(text: str, event: str) -> list[float]:
    """The avg value for every occurrence of
    Event '<event>' took <max> <min> <avg>  in `text`. The three numbers
    are per-rank max/min/avg; we take avg (3rd). One entry per iteration."""
    return [
        float(x)
        for x in re.findall(
            rf"Event '{re.escape(event)}' took\s+{_NUM}\s+{_NUM}\s+({_NUM})",
            text,
        )
    ]


def _mbpt_out(work_dir: Path, method: str, kernel: str = "cpu") -> Path:
    """Path to a method's mbpt HDF5 output (out_hf.h5 / out_gf2.h5 / ...)."""
    subdir = "mbpt_gpu" if kernel == "gpu" else "mbpt"
    return work_dir / subdir / f"out_{method}.h5"


def _h5_iteration_energies(path: Path) -> tuple[list[dict], int | None]:
    """Per-iteration energies and the final iteration index from an mbpt
    out_*.h5. Walks every iter<N> group and returns
    ([{iter, e1b, ehf, ecorr}, ...] sorted by N, final_iter), where
    e1b/ehf/ecorr = Energy_1b/HF/2b and final_iter is the file's 'iter'
    dataset. Returns ([], None) if the file is missing/unreadable."""
    if not path.exists():
        return [], None
    import h5py
    import numpy as np

    def _scalar(grp, name: str) -> float:
        v = np.asarray(grp[name][()]).ravel()[0]
        return float(v.real if np.iscomplexobj(v) else v)

    energies: list[dict] = []
    with h5py.File(path, "r") as f:
        final = (int(np.asarray(f["iter"][()]).ravel()[0])
                 if "iter" in f else None)
        iters = sorted(int(k[4:]) for k in f
                       if k.startswith("iter") and k[4:].isdigit())
        for n in iters:
            grp = f[f"iter{n}"]
            energies.append({
                "iter": n,
                "e1b": _scalar(grp, "Energy_1b"),
                "ehf": _scalar(grp, "Energy_HF"),
                "ecorr": _scalar(grp, "Energy_2b"),
            })
    return energies, final


def _peaks_from_A(A, freq):
    """Per (spin, k, orbital): the largest occupied (w<0) and smallest
    unoccupied (w>0) spectral peak. A: (n_omega, ns, nk, nao); freq (eV):
    (n_omega,). Returns (occ, unocc) dicts keyed by (s, k, a)."""
    from scipy.signal import find_peaks
    occ: dict[tuple[int, int, int], float] = {}
    unocc: dict[tuple[int, int, int], float] = {}
    _, ns, nk, nao = A.shape
    for s in range(ns):
        for k in range(nk):
            for a in range(nao):
                idx, _ = find_peaks(A[:, s, k, a], height=1e-3)
                w = freq[idx]
                below, above = w[w < 0], w[w > 0]
                if below.size:
                    occ[(s, k, a)] = float(below.max())
                if above.size:
                    unocc[(s, k, a)] = float(above.min())
    return occ, unocc


def _ac_spectral_peaks(ac_h5: Path):
    """Read the green-ac output's single iter<N>/G_tau group and return
    (occ, unocc) peak dicts (see _peaks_from_A). G and the frequency mesh
    are atomic-unit complex arrays;
    A = -Im(G)/pi, everything converted to eV. None if file missing."""
    if not ac_h5.exists():
        return None
    import h5py
    import numpy as np
    with h5py.File(ac_h5, "r") as f:
        grp = next(k for k in f if k.startswith("iter"))  # only one iter group
        G = f[f"{grp}/G_tau/data"][()]  # (n_omega,ns,nk,nao)
        mesh = f[f"{grp}/G_tau/mesh"][()]
    freq = mesh.real.reshape(-1) * _AU2EV  # drop tiny imag part
    A = -np.imag(G / _AU2EV) / np.pi
    return _peaks_from_A(A, freq)


def _method_sections(text: str) -> dict[str, str]:
    """Split the mbpt log into per-method chunks. mbpt.sbatch runs each
    method as its own srun and prints a banner first:
    '=== mbpt <ver> on <sys> :: <METHOD> ==='. Scoping events to the right
    chunk keeps a method's per-iteration timings from leaking into another
    (e.g. the HF build that GW redoes every iteration)."""
    sections: dict[str, str] = {}
    parts = re.split(r"=== mbpt .*? :: (\w+) ===", text)
    # parts = [preamble, METHOD1, body1, METHOD2, body2, ...]
    for i in range(1, len(parts), 2):
        method = parts[i].lower()
        sections[method] = sections.get(method, "") + parts[i + 1]
    return sections


# Solver "total" timing event per method (HF has only the HF build).
_SOLVER_EVENT = {"gf2": "GF2 total", "gw": "total"}


def _spectral_observables(work_dir: Path, kind: str,
                           kernel: str = "cpu") -> dict[str, float]:
    """IP/homo/lumo (molecular) or band gap/vbm/cbm/direct_gap_gamma (solid)
    from the green-ac output. Empty if the AC output is unavailable.
    homo/vbm = largest occupied peak; lumo/cbm = smallest unoccupied peak."""
    out: dict[str, float] = {}
    peaks = _ac_spectral_peaks(_ac_output(work_dir, kernel))
    if peaks is None:
        return out
    occ, unocc = peaks
    homo = max(occ.values()) if occ else None
    lumo = min(unocc.values()) if unocc else None
    if kind == "molecular":
        if homo is not None:
            out["homo"] = homo
            out["ip_koopmans"] = -homo
        if lumo is not None:
            out["lumo"] = lumo
    elif kind == "solid":
        if homo is not None:
            out["vbm"] = homo
        if lumo is not None:
            out["cbm"] = lumo
        if homo is not None and lumo is not None:
            out["indirect_gap"] = lumo - homo
        # Direct gap at Gamma — ASSUMES k-index 0 is Gamma (confirm!).
        g_occ = [v for (s, k, a), v in occ.items() if k == 0]
        g_unocc = [v for (s, k, a), v in unocc.items() if k == 0]
        if g_occ and g_unocc:
            out["direct_gap_gamma"] = min(g_unocc) - max(g_occ)
    return out


def _method_result(name: str, scf_type: str, work_dir: Path, kind: str,
                   sections: dict[str, str], kernel: str = "cpu") -> dict:
    """Build one method's {name, energies, final_iter, timings, spectral?}
    block (schema 3).

    name is the output/report key (out_<name>.h5, log section); scf_type is the
    underlying hf/gf2/gw used for the solver-timing event, so a variant like
    'gw_fullmem' still gets its GW timing. Spectral attaches only to the method
    literally named 'gw' — the one the AC job continues (out_gw.h5).

    timings (from the mbpt log section): 'hf' = the Hartree-Fock build,
    'total' = the method's solver (GF2/GW). Each line reports per-rank
    max/min/avg; we take avg of the FIRST iteration only. GW prints these
    per iteration, but 0.3.2/1.0.0a0 accumulate the wallclock across
    iterations, so only iter 1 is reliable (and first-iter stays correct
    for future versions that fix the accumulation).
    energies: every iteration of out_<name>.h5 as {iter, e1b, ehf, ecorr}
    (Energy_1b/HF/2b), with final_iter the converged index. GW additionally
    carries a 'spectral' block (vbm/cbm/gaps) from the analytic continuation.
    """
    block: dict = {"name": name, "timings": {}}

    hf_t = _event_avg_all(sections.get(name, ""), "Hartree-Fock")
    if hf_t:
        block["timings"]["hf"] = hf_t[0]          # first iteration only
    ev = _SOLVER_EVENT.get(scf_type)
    if ev:
        tot = _event_avg_all(sections.get(name, ""), ev)
        if tot:
            block["timings"]["total"] = tot[0]    # first iteration only

    energies, final_iter = _h5_iteration_energies(_mbpt_out(work_dir, name, kernel))
    block["energies"] = energies
    if final_iter is not None:
        block["final_iter"] = final_iter

    if name == "gw":
        spectral = _spectral_observables(work_dir, kind, kernel)
        if spectral:
            block["spectral"] = spectral

    return block


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--system",   required=True)
    ap.add_argument("--manifest", required=True)
    ap.add_argument("--work-dir", required=True, type=Path)
    ap.add_argument("--kernel",   choices=["cpu", "gpu"], default="cpu",
                    help="Compute kernel used for mbpt (cpu or gpu). "
                         "GPU runs read mbpt_gpu/ac_gpu dirs and write a _gpu.json.")
    args = ap.parse_args()

    manifest = load_manifest(args.manifest)
    kind = manifest["system"]["kind"]
    mbpt_ver, mbtools_ver = _detect_versions()

    log = _mbpt_log(args.work_dir, args.kernel)
    sections = _method_sections(log.read_text(errors="replace")) if log else {}

    # Only the methods that ran on this kernel (a GPU-only variant like n2's
    # 'gw_fullmem' is absent from the CPU results), keyed by output name.
    methods = {
        x["name"].lower(): _method_result(x["name"].lower(), x["type"].lower(),
                                           args.work_dir, kind, sections, args.kernel)
        for x in methods_for_kernel(manifest, args.kernel)
    }

    out_path = write_result(
        system_name=args.system,
        mbpt_ver=mbpt_ver,
        mbtools_ver=mbtools_ver,
        methods=methods,
        extras={"extracted_at": time.strftime("%Y-%m-%dT%H:%M:%S%z")},
        kernel=args.kernel,
    )
    print(f"wrote {out_path}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
