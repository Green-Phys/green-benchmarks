#!/usr/bin/env python3
"""Render manifest -> CLI args for Green's init_data_(mol_)df.py.

These init scripts ship with green-mbpt at
$GREEN_ROOT/python/init_data_df.py       (solids)
$GREEN_ROOT/python/init_data_mol_df.py   (molecules)

They take CLI flags; this helper emits a shell-quoted argv based on
the manifest. The flag set is the intersection of what's documented
across versions; new manifest fields → new flags can be added here
without touching init.sbatch.

NOTE flag names assumed (run `python init_data_df.py --help` and adjust):
  --a, --atom, --basis, --auxbasis, --pseudo, --xc, --x2c,
  --nk (k-mesh), --beta, --grid_file, --output

Mapping:
  system.relativistic   -> --x2c
    none      -> 0
    sfx2c1e   -> 1
    x2c1e     -> 2
"""
from __future__ import annotations

import argparse
import shlex
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from _lib import load_manifest

X2C_MAP = {"none": 0, "sfx2c1e": 1, "x2c1e": 2}


def _atom_lines_solid(geom: dict) -> str:
    """Cartesian "Elem x y z\\n ..." string from frac coords + lattice."""
    import numpy as np
    a = float(geom["lattice"]["a"])
    vectors = np.asarray(geom["lattice"]["vectors"], dtype=float) * a
    lines = []
    for atm in geom["atoms"]:
        cart = np.asarray(atm["frac"], dtype=float) @ vectors
        lines.append(f"{atm['element']} {cart[0]:.10f} {cart[1]:.10f} {cart[2]:.10f}")
    return "\n".join(lines)


def _lattice_vectors(geom: dict) -> str:
    """Real-space lattice translation vectors (a * unit vectors) in the
    form green_mbtools' --a expects: comma-separated values, one vector per
    line (parse_geometry passes the string through to pyscf's cell.a).
    Note --a is the translation vectors, not the scalar lattice constant."""
    import numpy as np
    a = float(geom["lattice"]["a"])
    vectors = np.asarray(geom["lattice"]["vectors"], dtype=float) * a
    return "\n".join(f"{v[0]:.10f}, {v[1]:.10f}, {v[2]:.10f}" for v in vectors)


def _atom_lines_molecular(geom: dict) -> str:
    lines = []
    for atm in geom["atoms"]:
        x, y, z = atm["xyz"]
        lines.append(f"{atm['element']} {x} {y} {z}")
    return "\n".join(lines)


def render(manifest: dict) -> list[str]:
    sys_ = manifest["system"]
    init = manifest.get("init", {})
    basis = manifest["basis"]
    mesh = manifest.get("mesh", {})

    args: list[str] = []
    args += ["--basis", basis["name"]]
    aux = basis.get("auxbasis")
    if aux and aux != "none":
        args += ["--auxbasis", aux]

    pseudo = sys_.get("pseudo", "none")
    if pseudo and pseudo != "none":
        args += ["--pseudo", pseudo]

    if "xc" in init:
        args += ["--xc", init["xc"]]

    args += ["--x2c", str(X2C_MAP[sys_.get("relativistic", "none")])]

    if sys_["kind"] == "solid":
        args += ["--a", _lattice_vectors(sys_["geometry"])]
        args += ["--atom", _atom_lines_solid(sys_["geometry"])]
        if "k" in mesh:
            # --nk takes a single int (cubic NxNxN). The 3-value form is
            # v100-only, so emit just the scalar for cross-version support.
            k = mesh["k"]
            kk = k if isinstance(k, (list, tuple)) else [k]
            if len(set(kk)) != 1:
                sys.exit(f"render_init_args: non-cubic k-mesh {k} needs the "
                         "3-value --nk (v100-only); not supported here.")
            args += ["--nk", str(kk[0])]
    else:
        args += ["--atom", _atom_lines_molecular(sys_["geometry"])]
        if "spin" in sys_:
            args += ["--spin", str(sys_["spin"])]

    if "beta" in mesh:
        args += ["--beta", str(mesh["beta"])]

    args += ["--df_int", "1"]
    return args


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--manifest", required=True)
    ap.add_argument("--script", action="store_true",
                    help="also print the script basename "
                         "(init_data_df.py / init_data_mol_df.py) on stderr")
    args = ap.parse_args()

    m = load_manifest(args.manifest)
    rendered = render(m)
    if args.script:
        script = ("init_data_df.py" if m["system"]["kind"] == "solid"
                  else "init_data_mol_df.py")
        print(script, file=sys.stderr)
    # shell-quoted; init.sbatch consumes via `eval` or `xargs`
    print(" ".join(shlex.quote(a) for a in rendered))


if __name__ == "__main__":
    main()
