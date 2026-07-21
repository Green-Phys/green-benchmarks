#!/usr/bin/env python3
"""Schema lint for systems/*/manifest.yaml.

Catches drift cheaply: adds and removes happen here, not in a wiki.
"""
from __future__ import annotations

import argparse
import sys
from typing import Any

from _lib import load_manifest


REQUIRED_TOP = ["system", "basis", "mesh", "methods"]
ALLOWED_KIND = {"molecular", "solid"}
ALLOWED_REL  = {"none", "sfx2c1e", "x2c1e"}
ALLOWED_METHOD = {"hf", "gf2", "gw"}


def _check(cond: bool, msg: str, errs: list[str]) -> None:
    if not cond:
        errs.append(msg)


def verify(path: str, manifest: dict[str, Any]) -> list[str]:
    errs: list[str] = []

    for k in REQUIRED_TOP:
        _check(k in manifest, f"missing top-level key: {k}", errs)
    if errs:
        return errs

    sys_ = manifest["system"]
    _check("name" in sys_, "system.name missing", errs)
    _check(sys_.get("kind") in ALLOWED_KIND,
           f"system.kind must be one of {ALLOWED_KIND}", errs)
    _check(sys_.get("relativistic", "none") in ALLOWED_REL,
           f"system.relativistic must be one of {ALLOWED_REL}", errs)

    if sys_.get("kind") == "solid":
        _check("k" in manifest["mesh"], "mesh.k required for solid systems", errs)
        _check("lattice" in sys_["geometry"],
               "geometry.lattice required for solid systems", errs)

    _verify_methods(manifest.get("methods"), "methods", required=True, errs=errs)
    # gpu_methods is the parallel GPU plan; optional (systems without it just
    # don't get a GPU job). Same per-entry rules as methods.
    if "gpu_methods" in manifest:
        _verify_methods(manifest["gpu_methods"], "gpu_methods", required=False, errs=errs)

    return errs


def _verify_methods(methods, section: str, *, required: bool, errs: list[str]) -> None:
    """Validate one method-plan list (`methods` or `gpu_methods`). output_tag
    uniqueness is per-section — the two plans write to separate files, so a CPU
    'gw' and a GPU 'gw' never collide."""
    if required:
        _check(isinstance(methods, list) and len(methods) >= 1,
               f"{section} must be a non-empty list", errs)
    else:
        _check(isinstance(methods, list) and len(methods) >= 1,
               f"{section}, if present, must be a non-empty list", errs)
    seen: set[str] = set()
    for m in methods if isinstance(methods, list) else []:
        t = m.get("type")
        tag = m.get("output_tag", t)
        _check(t in ALLOWED_METHOD,
               f"{section}[].type must be one of {ALLOWED_METHOD}, got {t!r}", errs)
        # A variant may reuse a type (e.g. two 'gw') under a distinct output_tag.
        if tag in seen:
            errs.append(f"duplicate {section}[].output_tag: {tag}")
        seen.add(tag)
        _check(isinstance(m.get("itermax"), int) and m["itermax"] > 0,
               f"{section}[{tag}].itermax must be a positive integer", errs)
        # threshold is required only for iterative methods
        if t == "gw":
            _check(isinstance(m.get("threshold"), float) and m["threshold"] > 0,
                   f"{section}[{tag}].threshold must be a positive float", errs)
        for cf in ("cuda_low_gpu_memory", "cuda_low_cpu_memory"):
            if cf in m:
                _check(isinstance(m[cf], bool),
                       f"{section}[{tag}].{cf} must be a boolean", errs)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("manifests", nargs="+")
    args = ap.parse_args()

    total = 0
    for path in args.manifests:
        try:
            m = load_manifest(path)
        except Exception as e:
            print(f"[FAIL] {path}: cannot load: {e}")
            total += 1
            continue
        errs = verify(path, m)
        if errs:
            total += len(errs)
            for e in errs:
                print(f"[FAIL] {path}: {e}")
        else:
            print(f"[ok]   {path}")
    return 1 if total else 0


if __name__ == "__main__":
    sys.exit(main())
