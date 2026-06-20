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


def write_result(
    system_name: str,
    mbpt_ver: str,
    mbtools_ver: str,
    observables: dict[str, float],
    timings: dict[str, float] | None = None,
    extras: dict[str, Any] | None = None,
) -> pathlib.Path:
    """Persist a results JSON, atomically.

    Observables and timings are kept in separate keys so timing churn
    cannot be mistaken for a physical regression in the cross-version
    table.
    """
    payload = {
        "schema": 1,
        "mbpt_version": mbpt_ver,
        "mbtools_version": mbtools_ver,
        "observables": observables,
        "timings": timings or {},
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


def iter_systems() -> list[pathlib.Path]:
    return sorted((REPO_ROOT / "systems").glob("*/manifest.yaml"))
