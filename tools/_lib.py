"""Shared utilities for the benchmark scripts.

Kept deliberately small. Per-system submit.sh scripts are the source of
truth for any system-specific behavior; this module only holds plumbing
that would otherwise be copy-pasted four times.
"""
from __future__ import annotations

import json
import pathlib
import sys
from typing import Any

try:
    import yaml
except ImportError:
    sys.exit(
        "PyYAML is required. Install with `pip install pyyaml` "
        "or load the Green env that ships it."
    )


REPO_ROOT = pathlib.Path(__file__).resolve().parents[1]


def load_manifest(path: str | pathlib.Path) -> dict[str, Any]:
    with open(path) as fh:
        return yaml.safe_load(fh)


def system_dir(system_name: str) -> pathlib.Path:
    return REPO_ROOT / "systems" / system_name


def results_dir(system_name: str) -> pathlib.Path:
    d = system_dir(system_name) / "results"
    d.mkdir(parents=True, exist_ok=True)
    return d


def result_filename(mbpt_ver: str, mbtools_ver: str) -> str:
    return f"{mbpt_ver}_{mbtools_ver}.json"


# Units for the per-method observable keys (used by the report tools).
OBSERVABLE_UNITS = {
    "e1b": "Ha", "ehf": "Ha", "ecorr": "Ha", "etot": "Ha",
    "ip_koopmans": "eV", "homo": "eV", "lumo": "eV",
    "indirect_gap": "eV", "direct_gap_gamma": "eV", "vbm": "eV", "cbm": "eV",
}


def observable_units(key: str) -> str:
    """Units for an observable key (the bare key, not 'method/key')."""
    return OBSERVABLE_UNITS.get(key, "")


def write_result(
    system_name: str,
    mbpt_ver: str,
    mbtools_ver: str,
    methods: dict[str, dict[str, Any]],
    extras: dict[str, Any] | None = None,
    kernel: str = "cpu",
) -> pathlib.Path:
    """Persist a results JSON, atomically.

    Schema 3: results are organized per method under "methods", each a dict
    {name, energies, final_iter, timings, spectral?}:
      - energies: list of per-iteration {iter, e1b, ehf, ecorr} records
      - final_iter: the run's last/converged iteration index (h5 `iter`)
      - timings: first-iteration wallclock (hf build, solver total)
      - spectral: AC observables (vbm/cbm/gaps), gw only, when AC ran
    Timings and spectral stay separate from the per-iteration energies so
    timing/AC churn can't be mistaken for a physical energy regression.

    kernel: "cpu" (default) or "gpu". GPU runs get a `_gpu` filename suffix
    and a "kernel" field in the payload so results stay distinct.
    """
    payload = {
        "schema": 3,
        "mbpt_version": mbpt_ver,
        "mbtools_version": mbtools_ver,
        "kernel": kernel,
        "methods": methods,
    }
    if extras:
        payload["extras"] = extras

    base = result_filename(mbpt_ver, mbtools_ver)
    if kernel == "gpu":
        base = base.replace(".json", "_gpu.json")
    out = results_dir(system_name) / base
    tmp = out.with_suffix(out.suffix + ".tmp")
    with open(tmp, "w") as fh:
        json.dump(payload, fh, indent=2, sort_keys=True)
        fh.write("\n")
    tmp.replace(out)
    return out


def flatten_result(result: dict) -> tuple[dict[str, float], dict[str, float]]:
    """Flatten a result into ('method/key' -> value) observable and timing
    dicts, for cross-version tabulation.

    schema 3: the headline observable per method is the energy record at
    'final_iter' (fallback: last iteration); 'spectral' (vbm/cbm/gaps) is
    merged in as-is. Per-iteration detail is intentionally not flattened here
    — it lives in the JSON for tools that need it. schema 2 ('observables')
    is still accepted so older result files keep tabulating.
    """
    obs: dict[str, float] = {}
    timings: dict[str, float] = {}
    for mname, mblock in result.get("methods", {}).items():
        energies = mblock.get("energies")
        if energies is not None:                              # schema 3
            final = mblock.get("final_iter")
            rec = next((e for e in energies if e.get("iter") == final), None)
            if rec is None and energies:
                rec = energies[-1]
            for k in ("e1b", "ehf", "ecorr"):
                if rec and k in rec:
                    obs[f"{mname}/{k}"] = rec[k]
            for k, v in mblock.get("spectral", {}).items():
                obs[f"{mname}/{k}"] = v
        else:                                                 # schema 2
            for k, v in mblock.get("observables", {}).items():
                obs[f"{mname}/{k}"] = v
        for k, v in mblock.get("timings", {}).items():
            timings[f"{mname}/{k}"] = v
    return obs, timings


def iter_systems() -> list[pathlib.Path]:
    return sorted((REPO_ROOT / "systems").glob("*/manifest.yaml"))


def _methods_section(kernel: str) -> str:
    """The manifest key holding the plan for `kernel`: `methods` (cpu) or the
    parallel, self-contained `gpu_methods` (gpu)."""
    return "gpu_methods" if kernel == "gpu" else "methods"


def methods_for_kernel(manifest: dict[str, Any], kernel: str) -> list[dict[str, Any]]:
    """Normalized method plan for `kernel` ("cpu" | "gpu").

    CPU reads the `methods:` list; GPU reads the parallel `gpu_methods:` list
    (each fully self-contained — its own itermax/threshold/cuda flags, a smaller
    plan such as 1xHF + 2xGW). A system with no `gpu_methods:` has an empty GPU
    plan (see has_gpu_methods). Shared source of truth for templates/mbpt.sbatch
    (which methods to RUN) and tools/extract_results.py (which to REPORT).

    Each returned dict has the resolved:
      output_tag — names the output file (out_<tag>.h5) and the report key;
                   defaults to type; must be unique within its section
      type       — mbpt.exe --scf_type (hf/gf2/gw)
      itermax
      cuda_low_gpu_memory / cuda_low_cpu_memory — bool, default True; passed to
        mbpt.exe only on GPU runs (both default true per the GPU convention).
    """
    plan: list[dict[str, Any]] = []
    for x in manifest.get(_methods_section(kernel), []):
        plan.append({
            "output_tag": str(x.get("output_tag", x["type"])),
            "type": x["type"],
            "itermax": x.get("itermax", 1),
            "cuda_low_gpu_memory": bool(x.get("cuda_low_gpu_memory", True)),
            "cuda_low_cpu_memory": bool(x.get("cuda_low_cpu_memory", True)),
        })
    return plan


def has_gpu_methods(manifest: dict[str, Any]) -> bool:
    """True if the manifest defines a non-empty `gpu_methods:` plan. The GPU
    MBPT job is submitted only for such systems (gated in submit_chain.sh)."""
    return bool(manifest.get("gpu_methods"))
