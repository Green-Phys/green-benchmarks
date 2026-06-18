#!/usr/bin/env python3
"""Pairwise diff between two releases.

Useful as a pre-release sanity check: compare the candidate release
against the previous one before committing.

Usage:
    python tools/diff.py 0.3.2_0.3.0 1.0.0a0_1.0.0a0
"""
from __future__ import annotations

import argparse
import json
import sys

from _lib import iter_systems, load_manifest


def _read(system_dir, tag: str):
    p = system_dir / "results" / f"{tag}.json"
    if not p.exists():
        return None
    with open(p) as fh:
        return json.load(fh)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("old_tag", help='e.g. "0.3.2_0.3.0"')
    ap.add_argument("new_tag", help='e.g. "1.0.0a0_1.0.0a0"')
    ap.add_argument("--rtol", type=float, default=1e-4,
                    help="relative tolerance to flag")
    ap.add_argument("--atol", type=float, default=1e-6,
                    help="absolute tolerance to flag")
    args = ap.parse_args()

    any_flagged = False
    for manifest_path in iter_systems():
        manifest = load_manifest(manifest_path)
        sd = manifest_path.parent
        old = _read(sd, args.old_tag)
        new = _read(sd, args.new_tag)
        if old is None or new is None:
            print(f"[skip] {manifest['system']['name']}: "
                  f"missing {args.old_tag if old is None else args.new_tag}")
            continue

        print(f"\n## {manifest['system']['name']}")
        for obs in manifest["observables"]:
            ov = old["observables"].get(obs["id"])
            nv = new["observables"].get(obs["id"])
            if ov is None or nv is None:
                print(f"  {obs['id']}: "
                      f"{'—' if ov is None else ov} -> "
                      f"{'—' if nv is None else nv}")
                continue
            delta = nv - ov
            denom = max(abs(ov), abs(nv), 1e-30)
            rel = abs(delta) / denom
            flag = " *FLAG*" if (abs(delta) > args.atol and rel > args.rtol) else ""
            any_flagged = any_flagged or bool(flag)
            print(f"  {obs['id']}: {ov:.6g} -> {nv:.6g}  "
                  f"Δ={delta:+.3e} ({rel:.2%}){flag}")

    return 1 if any_flagged else 0


if __name__ == "__main__":
    sys.exit(main())
