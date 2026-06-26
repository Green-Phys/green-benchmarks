#!/usr/bin/env python3
"""Patch an mbpt input.h5: keep one file's grid/symmetry structure but
transplant HF/{S-k, Fock-k, H-k} from another.

Diagnostic for the cross-version (v032 vs v100a0) disagreement on the
relativistic Ge systems. HF/* lives on the *full* k-mesh, which is the same
across versions, while only the irreducible reduction under symmetry/*
differs — so the HF group transplants index-for-index. Dropping a
symmetry-adapted (symmetric-Fock) HF/* from v100a0 onto v032's grid, then
running mbpt, isolates whether the Fock asymmetry (not the grid or the
solver) drives the disagreement.

Usage:
    python tools/patch_input.py --base   <v032   input.h5> \\
                                --hf-from <v100a0 input.h5> \\
                                --out     <patched input.h5>
"""
from __future__ import annotations

import argparse
import shutil
import sys
from pathlib import Path

import h5py
import numpy as np

# Datasets transplanted from --hf-from onto --base's grid. They live on the
# full k-mesh (same across versions), so they copy index-for-index.
_DATASETS = ("S-k", "Fock-k", "H-k")


def _fock(f: h5py.File) -> np.ndarray:
    """HF/Fock-k as complex (ns, nk, nao, nao). Stored as float64 real-pairs
    (last axis 2) per the green h5pp layout."""
    raw = f["HF/Fock-k"][()]
    return raw.view(complex).reshape(raw.shape[:-1])


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--base", required=True, type=Path,
                    help="input.h5 whose grid/symmetry structure is kept")
    ap.add_argument("--hf-from", required=True, type=Path,
                    help="input.h5 whose HF/* group is transplanted")
    ap.add_argument("--out", required=True, type=Path,
                    help="output patched input.h5")
    args = ap.parse_args()

    # --- sanity checks: the kept grid must be the same full k-mesh ---
    with h5py.File(args.base, "r") as b, h5py.File(args.hf_from, "r") as s:
        fb, fs = _fock(b), _fock(s)
        if fb.shape != fs.shape:
            sys.exit(f"HF/Fock-k shape mismatch (full k-mesh must match): "
                     f"base {fb.shape} vs hf-from {fs.shape}")
        mb, ms = b["symmetry/k/mesh"][()], s["symmetry/k/mesh"][()]
        same = mb.shape == ms.shape and np.allclose(mb, ms)
        print(f"full k-mesh identical : {same}  (nk={fb.shape[1]})")
        if not same:
            sys.exit("symmetry/k/mesh differs between files — full k-mesh "
                     "must be identical to transplant HF/* by index.")
        print(f"max|Fock(hf-from) - Fock(base)| = {np.max(np.abs(fs - fb)):.3e}")

    # --- copy base, then overwrite only the transplanted HF datasets ---
    shutil.copyfile(args.base, args.out)
    with h5py.File(args.hf_from, "r") as s, h5py.File(args.out, "r+") as o:
        for name in _DATASETS:
            if f"HF/{name}" in o:
                del o[f"HF/{name}"]
            s.copy(f"HF/{name}", o["HF"], name)

    print(f"transplanted HF/{{{', '.join(_DATASETS)}}} -> {args.out}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
