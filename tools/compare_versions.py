#!/usr/bin/env python3
"""Cross-version tabulation + draft of the one-paragraph release report.

Produces:
  - a value table (observables × release)
  - a timing table  (timings    × release)
  - a one-paragraph draft summarizing how 1.0.0a0 differs from 0.3.x

The paragraph is a *draft*: the admin tightens it for the release
notes. The numbers in it are computed from JSON, so they cannot be
copy-pasted incorrectly from the table.

Usage:
    python tools/compare_versions.py --old 0.3.2_0.3.0 --new 1.0.0a0_1.0.0a0
"""
from __future__ import annotations

import argparse
import json
import statistics
from pathlib import Path

from _lib import iter_systems, load_manifest


def _read(system_dir: Path, tag: str):
    p = system_dir / "results" / f"{tag}.json"
    if not p.exists():
        return None
    with open(p) as fh:
        return json.load(fh)


def _percent(old: float, new: float) -> float:
    denom = max(abs(old), 1e-30)
    return (new - old) / denom * 100.0


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--old", required=True, help="e.g. 0.3.2_0.3.0")
    ap.add_argument("--new", required=True, help="e.g. 1.0.0a0_1.0.0a0")
    ap.add_argument("--obs-tol-percent", type=float, default=0.5,
                    help="observable percent-change above which the report "
                         "calls out the row (default 0.5%)")
    ap.add_argument("--time-tol-percent", type=float, default=20.0,
                    help="timing percent-change above which the report "
                         "calls out a regression (default 20%)")
    args = ap.parse_args()

    out: list[str] = []
    out.append(f"# Cross-version report: {args.old} -> {args.new}")
    out.append("")

    obs_changes: list[tuple[str, str, float, float, float]] = []  # (sys,id,old,new,pct)
    time_changes: list[tuple[str, str, float, float, float]] = []
    obs_missing: list[tuple[str, str, str]] = []  # (sys,id,which-side)

    for manifest_path in iter_systems():
        manifest = load_manifest(manifest_path)
        sys_name = manifest["system"]["name"]
        sd = manifest_path.parent
        old = _read(sd, args.old)
        new = _read(sd, args.new)
        if old is None or new is None:
            out.append(f"## {sys_name}: _missing_ "
                       f"{'old' if old is None else 'new'} results")
            out.append("")
            continue

        out.append(f"## {sys_name}")
        out.append("")
        out.append(f"| observable | {args.old} | {args.new} | Δ% |")
        out.append("|---|---|---|---|")
        for obs in manifest["observables"]:
            ov = old["observables"].get(obs["id"])
            nv = new["observables"].get(obs["id"])
            if ov is None and nv is None:
                continue
            if ov is None:
                obs_missing.append((sys_name, obs["id"], args.old))
                out.append(f"| `{obs['id']}` | — | {nv:.6g} {obs['units']} | new |")
                continue
            if nv is None:
                obs_missing.append((sys_name, obs["id"], args.new))
                out.append(f"| `{obs['id']}` | {ov:.6g} {obs['units']} | — | dropped |")
                continue
            pct = _percent(ov, nv)
            out.append(f"| `{obs['id']}` | {ov:.6g} {obs['units']} "
                       f"| {nv:.6g} {obs['units']} | {pct:+.3f}% |")
            if abs(pct) > args.obs_tol_percent:
                obs_changes.append((sys_name, obs["id"], ov, nv, pct))
        out.append("")

        timing_keys = set(old.get("timings", {}).keys()) \
                    | set(new.get("timings", {}).keys())
        if timing_keys:
            out.append(f"| timing (s) | {args.old} | {args.new} | Δ% |")
            out.append("|---|---|---|---|")
            for tk in sorted(timing_keys):
                ov = old.get("timings", {}).get(tk)
                nv = new.get("timings", {}).get(tk)
                if ov is None or nv is None:
                    out.append(f"| `{tk}` | "
                               f"{'—' if ov is None else f'{ov:.3g}'} | "
                               f"{'—' if nv is None else f'{nv:.3g}'} | n/a |")
                    continue
                pct = _percent(ov, nv)
                out.append(f"| `{tk}` | {ov:.3g} | {nv:.3g} | {pct:+.1f}% |")
                if pct > args.time_tol_percent:
                    time_changes.append((sys_name, tk, ov, nv, pct))
            out.append("")

    # ---- one-paragraph draft ----
    out.append("## Draft summary paragraph")
    out.append("")
    parts: list[str] = []
    parts.append(
        f"Across the four-system benchmark suite, green-mbpt {args.new.split('_')[0]} "
        f"+ green-mbtools {args.new.split('_')[1]} was compared against "
        f"{args.old.split('_')[0]} / {args.old.split('_')[1]}."
    )
    if not obs_changes:
        parts.append(
            f"All physical observables agree within {args.obs_tol_percent}%; "
            "no regression flagged."
        )
    else:
        worst = max(obs_changes, key=lambda r: abs(r[4]))
        parts.append(
            f"{len(obs_changes)} observable(s) shifted by more than "
            f"{args.obs_tol_percent}%, with the largest being "
            f"`{worst[1]}` on {worst[0]} ({worst[4]:+.2f}%)."
        )
    if time_changes:
        worst = max(time_changes, key=lambda r: r[4])
        parts.append(
            f"Wallclock regressed in {len(time_changes)} case(s); "
            f"worst: `{worst[1]}` on {worst[0]} (+{worst[4]:.1f}%)."
        )
    else:
        parts.append("No timing regressions exceeded "
                     f"{args.time_tol_percent}%.")
    if obs_missing:
        new_only = sum(1 for _, _, w in obs_missing if w == args.old)
        if new_only:
            parts.append(
                f"{new_only} observable(s) are new in {args.new} and have "
                "no counterpart in the older release."
            )
    out.append(" ".join(parts))
    out.append("")

    print("\n".join(out))


if __name__ == "__main__":
    main()
