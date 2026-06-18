"""Mean-field initialization helpers shared by all systems' generate.py.

Reads the manifest and produces a converged mean-field object that the
per-system script then hands to green-mbtools to dump integrals + a
green-mbpt-shaped input.h5.

Kept in /tools so the per-system scripts stay short and the
manifest -> pyscf mapping has exactly one definition.
"""
from __future__ import annotations

from typing import Any


def build_molecular(manifest: dict[str, Any]):
    from pyscf import gto, scf

    sys_ = manifest["system"]
    atom_lines = [
        f"{a['element']} {a['xyz'][0]} {a['xyz'][1]} {a['xyz'][2]}"
        for a in sys_["geometry"]["atoms"]
    ]
    mol = gto.M(
        atom="; ".join(atom_lines),
        basis=manifest["basis"]["name"],
        charge=sys_.get("charge", 0),
        spin=sys_.get("spin", 0),
        unit=sys_["geometry"].get("units", "angstrom"),
        verbose=4,
    )

    mf = scf.RHF(mol)
    if sys_["relativistic"] == "sfx2c1e":
        mf = mf.sfx2c1e()
    elif sys_["relativistic"] == "x2c1e":
        # full one-electron X2C; spinor wavefunction
        mf = scf.X2C(mol)

    mf.conv_tol = 1e-10
    mf.kernel()
    return mol, mf


def build_pbc(manifest: dict[str, Any]):
    from pyscf.pbc import gto as pgto, scf as pscf
    import numpy as np

    sys_ = manifest["system"]
    geom = sys_["geometry"]
    a = float(geom["lattice"]["a"])
    vectors = np.asarray(geom["lattice"]["vectors"], dtype=float) * a

    atom_lines = []
    for atm in geom["atoms"]:
        frac = np.asarray(atm["frac"], dtype=float)
        cart = frac @ vectors
        atom_lines.append(f"{atm['element']} {cart[0]} {cart[1]} {cart[2]}")

    cell = pgto.Cell()
    cell.atom = "; ".join(atom_lines)
    cell.a = vectors
    cell.basis = manifest["basis"]["name"]
    pseudo = sys_.get("pseudo", "none")
    if pseudo and pseudo != "none":
        cell.pseudo = pseudo
    cell.verbose = 4
    cell.build()

    kmesh = manifest["mesh"]["k"]
    kpts = cell.make_kpts(kmesh)

    mf = pscf.KRHF(cell, kpts=kpts).density_fit()
    if sys_["relativistic"] == "sfx2c1e":
        mf = mf.sfx2c1e()
    elif sys_["relativistic"] == "x2c1e":
        mf = pscf.KGHF(cell, kpts=kpts).density_fit().x2c1e()

    mf.conv_tol = 1e-9
    mf.kernel()
    return cell, mf, kpts


def dump_green_input(manifest: dict[str, Any], mf, output_path: str) -> None:
    """Dump a green-mbpt-shaped input.h5 from a converged mf.

    This is intentionally thin: the per-version green-mbtools API
    handles the heavy lifting. If green-mbtools renames `mio` or its
    dump routine, fix it here and the four generate.py scripts pick up
    the change for free.
    """
    try:
        from green_mbtools.mint import dump as _dump
    except ImportError:
        from mbtools.mint import dump as _dump  # 0.3.x layout fallback
    _dump(mf, manifest=manifest, output=output_path)
