#!/usr/bin/env python3
"""Generate input.h5 for Ge (all-electron, full X2C / spinor path).

This script is the spinor-path entry point. If `build_pbc` does not
return a spinor-aware mf for `relativistic: x2c1e`, the assertion
below fires before any downstream dump runs.
"""
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
    assert manifest["system"]["relativistic"] == "x2c1e"

    _, mf, _ = build_pbc(manifest)
    # spinor signature: the orth layer must run its spinor branch
    # downstream. We assert intent here; the actual flag is consumed
    # by green-mbtools.dump via the manifest.
    gw = next((m for m in manifest["methods"] if m["type"] == "gw"), {})
    assert gw.get("orth_spinor") is True, "ge_x2c1e gw method must set orth_spinor: true"
    dump_green_input(manifest, mf, args.out)


if __name__ == "__main__":
    main()
