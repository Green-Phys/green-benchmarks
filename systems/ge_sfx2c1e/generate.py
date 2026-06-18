#!/usr/bin/env python3
"""Generate input.h5 for Ge (all-electron, sfx2c1e scalar relativistic)."""
import argparse
import sys
import pathlib

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[2] / "tools"))
from _lib import load_manifest             # noqa: E402
from _pyscf_init import build_pbc, dump_green_input  # noqa: E402


def main() -> None:
    p = argparse.ArgumentParser()
    p.add_argument("--manifest", required=True)
    p.add_argument("--out", required=True, help="path to write input.h5")
    args = p.parse_args()

    manifest = load_manifest(args.manifest)
    assert manifest["system"]["kind"] == "solid"
    assert manifest["system"]["relativistic"] == "sfx2c1e"

    _, mf, _ = build_pbc(manifest)
    dump_green_input(manifest, mf, args.out)


if __name__ == "__main__":
    main()
