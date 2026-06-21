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

    methods = manifest["methods"]
    _check(isinstance(methods, list) and len(methods) >= 1,
           "methods must be a non-empty list", errs)
    seen_methods: set[str] = set()
    for m in methods if isinstance(methods, list) else []:
        t = m.get("type")
        _check(t in ALLOWED_METHOD,
               f"methods[].type must be one of {ALLOWED_METHOD}, got {t!r}", errs)
        if t in seen_methods:
            errs.append(f"duplicate methods[].type: {t}")
        seen_methods.add(t)
        _check(isinstance(m.get("itermax"), int) and m["itermax"] > 0,
               f"methods[{t}].itermax must be a positive integer", errs)
        # threshold is required only for iterative methods
        if t == "gw":
            _check(isinstance(m.get("threshold"), float) and m["threshold"] > 0,
                   "methods[gw].threshold must be a positive float", errs)

    return errs


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
