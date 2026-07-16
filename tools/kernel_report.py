#!/usr/bin/env python3
"""Cross-version + cpu/gpu kernel report for a system. Engine only here;
rendering + CLI in later tasks."""
from __future__ import annotations
import json
from pathlib import Path

ENERGY_OBS = ("e1b", "ehf", "ecorr")
GAP_OBS = ("direct_gap_gamma", "indirect_gap")
# display label -> (version tag chooser, kernel)
LABELS = ("v032", "v032_gpu", "v100", "v100_gpu")


def _read(system_dir: Path, tag: str, gpu: bool):
    name = f"{tag}_gpu.json" if gpu else f"{tag}.json"
    p = Path(system_dir) / "results" / name
    return json.loads(p.read_text()) if p.exists() else None


def load_classes(system_dir, old_tag, new_tag):
    return {
        "v032":     _read(system_dir, old_tag, False),
        "v032_gpu": _read(system_dir, old_tag, True),
        "v100":     _read(system_dir, new_tag, False),
        "v100_gpu": _read(system_dir, new_tag, True),
    }


def _energies(cls, method):
    if not cls:
        return {}
    m = cls.get("methods", {}).get(method)
    if not m or "energies" not in m:
        return {}
    return {rec["iter"]: rec for rec in m["energies"]}


def _sub(a, b):
    return None if a is None or b is None else a - b


def energy_diffs(classes, method):
    per = {lab: _energies(classes.get(lab), method) for lab in LABELS}
    iters = sorted({i for d in per.values() for i in d})
    rows = []
    for obs in ENERGY_OBS:
        for it in iters:
            v = {lab: (per[lab].get(it, {}) or {}).get(obs) for lab in LABELS}
            rows.append({
                "obs": obs, "iter": it,
                **v,
                "d_ver_cpu": _sub(v["v100"], v["v032"]),
                "d_ver_gpu": _sub(v["v100_gpu"], v["v032_gpu"]),
                "d_cpu_gpu_old": _sub(v["v032"], v["v032_gpu"]),
                "d_cpu_gpu_new": _sub(v["v100"], v["v100_gpu"]),
            })
    return rows


def verdict(classes, tol_kernel_energy):
    worst_ctrl = worst_test = 0.0
    for method in ("hf", "gf2", "gw"):
        for r in energy_diffs(classes, method):
            if r["d_cpu_gpu_old"] is not None:
                worst_ctrl = max(worst_ctrl, abs(r["d_cpu_gpu_old"]))
            if r["d_cpu_gpu_new"] is not None:
                worst_test = max(worst_test, abs(r["d_cpu_gpu_new"]))
    if worst_ctrl > tol_kernel_energy:
        return "SUSPECT", worst_ctrl
    if worst_test > tol_kernel_energy:
        return "FAIL", worst_test
    return "PASS", worst_test


def _fmt(x):
    return "" if x is None else f"{x:.8g}"


def _gaps(cls, obs):
    m = (cls or {}).get("methods", {}).get("gw", {})
    return (m.get("spectral") or {}).get(obs)


def render_system_report(system, classes, *, tol_kernel_energy, tol_ver_pct):
    v, worst = verdict(classes, tol_kernel_energy)
    out = [f"# {system} — cpu/gpu × version report", "",
           f"**Verdict:** {v} (worst cpu/gpu energy Δ = {worst:.2e} Ha)", ""]
    for method in ("hf", "gf2", "gw"):
        if not any((classes.get(l) or {}).get("methods", {}).get(method) for l in LABELS):
            continue
        out.append(f"## {method}")
        rows = energy_diffs(classes, method)
        is_gw = method == "gw"
        for obs in ENERGY_OBS:
            sub = [r for r in rows if r["obs"] == obs]
            if not sub:
                continue
            out.append(f"### {obs} (Ha)")
            if is_gw:
                out.append("| iter | v032 | v032_gpu | v100 | v100_gpu | Δver_cpu | Δver_gpu | Δcpu/gpu@v032 | Δcpu/gpu@v100 |")
                out.append("|--|--|--|--|--|--|--|--|--|")
                for r in sub:
                    flag = " ⚠" if (r["d_cpu_gpu_new"] is not None and abs(r["d_cpu_gpu_new"]) > tol_kernel_energy) else ""
                    out.append("| {iter} | {v032} | {v032_gpu} | {v100} | {v100_gpu} | {dvc} | {dvg} | {dco} | {dcn}{f} |".format(
                        iter=r["iter"], v032=_fmt(r["v032"]), v032_gpu=_fmt(r["v032_gpu"]),
                        v100=_fmt(r["v100"]), v100_gpu=_fmt(r["v100_gpu"]),
                        dvc=_fmt(r["d_ver_cpu"]), dvg=_fmt(r["d_ver_gpu"]),
                        dco=_fmt(r["d_cpu_gpu_old"]), dcn=_fmt(r["d_cpu_gpu_new"]), f=flag))
            else:
                out.append("| iter | v032 | v100 | Δver |")
                out.append("|--|--|--|--|")
                for r in sub:
                    out.append(f"| {r['iter']} | {_fmt(r['v032'])} | {_fmt(r['v100'])} | {_fmt(r['d_ver_cpu'])} |")
            out.append("")
        if is_gw:
            gap_lines = []
            for obs in GAP_OBS:
                vals = {l: _gaps(classes.get(l), obs) for l in LABELS}
                if all(x is None for x in vals.values()):
                    continue  # metal / no gap
                gap_lines.append("| {o} | {a} | {b} | {c} | {d} | {e} | {f} |".format(
                    o=obs, a=_fmt(vals["v032"]), b=_fmt(vals["v032_gpu"]),
                    c=_fmt(vals["v100"]), d=_fmt(vals["v100_gpu"]),
                    e=_fmt(_sub(vals["v100"], vals["v032"])),
                    f=_fmt(_sub(vals["v100"], vals["v100_gpu"]))))
            if gap_lines:
                out.append("### band gaps (eV, final iter — visual guide, no verdict)")
                out.append("| gap | v032 | v032_gpu | v100 | v100_gpu | Δver_cpu | Δcpu/gpu@v100 |")
                out.append("|--|--|--|--|--|--|--|")
                out += gap_lines + [""]
    return "\n".join(out)


import argparse

ROLL_START = "<!-- kernel-report:start -->"
ROLL_END = "<!-- kernel-report:end -->"


def rollup_line(system, classes, *, tol_kernel_energy):
    v, worst = verdict(classes, tol_kernel_energy)
    return f"| {system} | {v} | {worst:.2e} |"


def _write_rollup(results_md: Path, lines):
    header = ("## cpu/gpu kernel agreement\n\n"
              "| system | verdict | worst cpu/gpu energy Δ (Ha) |\n|--|--|--|\n")
    block = f"{ROLL_START}\n{header}" + "\n".join(lines) + f"\n{ROLL_END}\n"
    text = results_md.read_text() if results_md.exists() else "# RESULTS\n"
    if ROLL_START in text and ROLL_END in text:
        pre = text.split(ROLL_START)[0]
        post = text.split(ROLL_END)[1]
        text = pre + block + post
    else:
        text = text.rstrip() + "\n\n" + block
    results_md.write_text(text)


def main():
    import _lib
    from _lib import iter_systems
    ap = argparse.ArgumentParser()
    ap.add_argument("--old", required=True, help="e.g. v032_0.3.0")
    ap.add_argument("--new", required=True, help="e.g. v100a0_1.0.0a1")
    ap.add_argument("--tol-kernel-energy", type=float, default=1e-6)
    ap.add_argument("--tol-ver-pct", type=float, default=0.1)
    args = ap.parse_args()
    lines = []
    for manifest_path in iter_systems():
        system_dir = manifest_path.parent
        system_name = system_dir.name
        classes = load_classes(system_dir, args.old, args.new)
        if not any(classes.values()):
            continue
        md = render_system_report(system_name, classes,
                                  tol_kernel_energy=args.tol_kernel_energy,
                                  tol_ver_pct=args.tol_ver_pct)
        (system_dir / "results").mkdir(exist_ok=True)
        (system_dir / "results" / "report.md").write_text(md)
        lines.append(rollup_line(system_name, classes,
                                 tol_kernel_energy=args.tol_kernel_energy))
    _write_rollup(_lib.REPO_ROOT / "RESULTS.md", lines)
    print(f"wrote {len(lines)} system reports + RESULTS.md roll-up")


if __name__ == "__main__":
    main()
