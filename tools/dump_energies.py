#!/usr/bin/env python3
"""Dump per-iteration energies from a green-mbpt results h5 (out_*.h5 / sim_*.h5).

Why this exists: tools/extract_results.py reports a single iteration per
method, chosen by the file's `iter` dataset:

    grp = f[f"iter{int(f['iter'][()])}"]
    e1b, ecorr, ehf = grp["Energy_1b"], grp["Energy_2b"], grp["Energy_HF"]

If two versions store that `iter` pointer with different meaning (0- vs
1-based, "last completed" vs "next"), the benchmark ends up comparing
iteration i of one version against iteration j of another. This script prints
the pointer AND every iterN group so you can check that assumption directly.

Usage:
    python dump_energies.py sim_hf.h5
    python dump_energies.py v0.3.0/sim_hf.h5 v1.0.0/sim_hf.h5   # compare versions
    python dump_energies.py v0.3.0/sim_gw.h5 v1.0.0/sim_gw.h5

Compare the two versions row-by-row (iter1 vs iter1, ...) and separately look
at what each file's `iter` pointer selects (marked `<== extracted`). If the
per-iteration rows match but the extracted rows don't, the pointer semantics
differ across versions -- that's the bug, not the physics.
"""
import sys

import h5py
import numpy as np

FIELDS = ("Energy_1b", "Energy_2b", "Energy_HF")  # e1b, ecorr, ehf


def scalar(grp, name):
    """Same coercion extract_results.py uses: first element, real part."""
    if name not in grp:
        return None
    v = np.asarray(grp[name][()]).ravel()[0]
    return float(v.real if np.iscomplexobj(v) else v)


def iter_groups(f):
    """Names of iterN groups, sorted by N."""
    found = [(int(k[4:]), k) for k in f
             if k.startswith("iter") and k[4:].isdigit()]
    return [k for _, k in sorted(found)]


def dump(path):
    with h5py.File(path, "r") as f:
        pointer = (int(np.asarray(f["iter"][()]).ravel()[0])
                   if "iter" in f else None)
        print(f"\n=== {path} ===")
        print(f"  `iter` pointer -> {pointer}   "
              f"(extract_results.py would read iter{pointer})")
        header = f"  {'iter':>4}  {'Energy_1b':>24}  {'Energy_2b (ecorr)':>24}  {'Energy_HF':>24}"
        print(header)
        for gname in iter_groups(f):
            n = int(gname[4:])
            vals = [scalar(f[gname], x) for x in FIELDS]
            cells = "  ".join(f"{v:24.15e}" if v is not None else f"{'--':>24}"
                              for v in vals)
            mark = "   <== extracted" if n == pointer else ""
            print(f"  {n:>4}  {cells}{mark}")


def main():
    if len(sys.argv) < 2:
        print(__doc__)
        sys.exit(1)
    for p in sys.argv[1:]:
        try:
            dump(p)
        except Exception as e:  # keep going across files
            print(f"\n=== {p} ===\n  ERROR: {e}")


if __name__ == "__main__":
    main()
