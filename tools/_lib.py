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
) -> pathlib.Path:
    """Persist a results JSON, atomically.

    Schema 2: results are organized per method under "methods", each a dict
    {name, timings, observables}. Timings stay separate from observables so
    timing churn can't be mistaken for a physical regression.
    """
    payload = {
        "schema": 2,
        "mbpt_version": mbpt_ver,
        "mbtools_version": mbtools_ver,
        "methods": methods,
    }
    if extras:
        payload["extras"] = extras

    out = results_dir(system_name) / result_filename(mbpt_ver, mbtools_ver)
    tmp = out.with_suffix(out.suffix + ".tmp")
    with open(tmp, "w") as fh:
        json.dump(payload, fh, indent=2, sort_keys=True)
        fh.write("\n")
    tmp.replace(out)
    return out


def flatten_result(result: dict) -> tuple[dict[str, float], dict[str, float]]:
    """Flatten a schema-2 result into ('method/key' -> value) observable and
    timing dicts, for cross-version tabulation."""
    obs: dict[str, float] = {}
    timings: dict[str, float] = {}
    for mname, mblock in result.get("methods", {}).items():
        for k, v in mblock.get("observables", {}).items():
            obs[f"{mname}/{k}"] = v
        for k, v in mblock.get("timings", {}).items():
            timings[f"{mname}/{k}"] = v
    return obs, timings


def iter_systems() -> list[pathlib.Path]:
    return sorted((REPO_ROOT / "systems").glob("*/manifest.yaml"))
