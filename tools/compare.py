#!/usr/bin/env python3
import json
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
SYSTEMS_DIR = REPO_ROOT / "systems"
OUTPUT = REPO_ROOT / "COMPARISON.md"

FILES = {
    "v032_cpu": "v032_0.3.0.json",
    "v032_gpu": "v032_0.3.0_gpu.json",
    "v100_cpu": "v100a1_1.0.0a2.json",
    "v100_gpu": "v100a1_1.0.0a2_gpu.json",
}

# Output precision for physical-result differences.
# Differences smaller than 1e-7 are displayed as zero.
DIFF_THRESHOLD = 1e-7
DIFF_DECIMALS = 7

# Units per observable family. Energies come from the per-iteration
# "energies" block and are in Hartree; band-structure/gap quantities
# come from the "spectral" block and are in electronvolts.
ENERGY_UNIT = "Ha"
SPECTRAL_UNIT = "eV"

SYSTEM_LABELS = {
    "n2": "n2 (Molecule)",
}

SYSTEM_NOTES = {
    "ge_x2c1e": (
        "> **Note:** This benchmark is currently failing; "
        "the results are included for reference."
    ),
}

def load_json(path):
    if not path.exists():
        return None
    with path.open() as f:
        return json.load(f)


def difference(a, b):
    """
    Calculate A - B.
    """
    if a is None or b is None:
        return None
    return a - b


def ratio(a, b):
    """
    Calculate A / B.
    """
    if a is None or b is None or b == 0:
        return None
    return a / b


def fmt_diff(value, unit):
    """
    Fixed absolute precision for physical-result differences. Values are
    rounded to DIFF_DECIMALS places and tagged with their unit.
    Differences below DIFF_THRESHOLD are shown as a plain "0".
    """
    if value is None:
        return "—"
    if abs(value) < DIFF_THRESHOLD:
        return "0"
    rounded = round(value, DIFF_DECIMALS)
    if rounded == 0:
        return "0"
    return f"{rounded:.{DIFF_DECIMALS}f} {unit}"


def fmt_time(value):
    if value is None:
        return "—"
    return f"{value:.6f}"


def fmt_ratio(value):
    if value is None:
        return "—"
    return f"{value:.4f}x"


def get_final_energy(method_data, observable):
    """
    Read observable from the final iteration of the energies list.
    """
    energies = method_data.get("energies", [])
    if not energies:
        return None
    final_iter = method_data.get("final_iter")
    if final_iter is not None:
        for entry in energies:
            if entry.get("iter") == final_iter:
                return entry.get(observable)
    # Fallback: use the last stored iteration.
    return energies[-1].get(observable)


def extract_results(data):
    """
    Flatten physical results into (value, unit) pairs keyed by names
    such as:
        gw/e1b            -> (value, "Ha")
        gw/ecorr          -> (value, "Ha")
        gw/ehf            -> (value, "Ha")
        gw/cbm            -> (value, "eV")
        gw/vbm            -> (value, "eV")
        gw/indirect_gap   -> (value, "eV")
        ...
    """
    results = {}
    if data is None:
        return results
    methods = data.get("methods", {})
    for method_name, method_data in methods.items():
        # Energies from final iteration (Hartree)
        energies = method_data.get("energies", [])
        if energies:
            keys = set()
            for entry in energies:
                keys.update(entry.keys())
            keys.discard("iter")
            for key in sorted(keys):
                value = get_final_energy(method_data, key)
                if value is not None:
                    results[f"{method_name}/{key}"] = (value, ENERGY_UNIT)

        # Spectral quantities (electronvolt)
        spectral = method_data.get("spectral", {})
        for key, value in spectral.items():
            if value is not None:
                results[f"{method_name}/{key}"] = (value, SPECTRAL_UNIT)
    return results


def extract_timings(data):
    """
    Flatten timings into names such as:
        gw/hf
        gw/total
        gf2/total
        ...
    """
    timings = {}
    if data is None:
        return timings
    methods = data.get("methods", {})
    for method_name, method_data in methods.items():
        method_timings = method_data.get("timings", {})
        for key, value in method_timings.items():
            if value is not None:
                timings[f"{method_name}/{key}"] = value
    return timings


def load_system(system_dir):
    datasets = {}
    for label, filename in FILES.items():
        datasets[label] = load_json(
            system_dir / "results" / filename
        )
    return datasets


def main():
    lines = [
        "# Comparison",
        "",
        "Generated directly from JSON result files.",
        "",
        "Result differences are calculated as:",
        "",
        "- `v032 CPU-GPU` = v032 CPU - v032 GPU",
        "- `v100 CPU-GPU` = v100 CPU - v100 GPU",
        "- `CPU v032-v100` = v032 CPU - v100 CPU",
        "- `GPU v032-v100` = v032 GPU - v100 GPU",
        "",
       f"Differences are rounded to {DIFF_DECIMALS} decimal places "
        f"(~{DIFF_THRESHOLD:g}). Anything smaller is shown as `0`. "
        "The input DFT calculation is performed without symmetry and "
        "has an asymmetry of ~1e-6. "
        "Energies (`e1b`, `ecorr`, `ehf`) are in Hartree; "
        "band/gap quantities (`cbm`, `vbm`, `*_gap*`, `homo`, `lumo`, "
        "`ip_koopmans`) are in electronvolts.",
        "",
        "Timing ratios are calculated as:",
        "",
        "- `CPU v032/v100` = v032 CPU time / v100 CPU time",
        "- `GPU v032/v100` = v032 GPU time / v100 GPU time",
        "",
        "For timing ratios, values > 1 mean that v100 is faster than v032.",
        "",
    ]

    for system_dir in sorted(SYSTEMS_DIR.iterdir()):
        if not system_dir.is_dir():
            continue
        results_dir = system_dir / "results"
        if not results_dir.exists():
            continue

        datasets = load_system(system_dir)
        if not any(datasets.values()):
            continue

        system = system_dir.name
        result_sets = {
            name: extract_results(data)
            for name, data in datasets.items()
        }
        timing_sets = {
            name: extract_timings(data)
            for name, data in datasets.items()
        }

        system_label = SYSTEM_LABELS.get(system, system)

        lines.append(f"## {system_label}")
        lines.append("")
        if system in SYSTEM_NOTES:
            lines.append(SYSTEM_NOTES[system])
            lines.append("")
        # ==========================================================
        # PHYSICAL RESULTS
        # ==========================================================
        lines.append("### Results differences")
        lines.append("")
        lines.append(
            "| observable | v032 CPU-GPU | v100 CPU-GPU | "
            "CPU v032-v100 | GPU v032-v100 |"
        )
        lines.append(
            "|---|---:|---:|---:|---:|"
        )

        result_keys = set()
        for result_set in result_sets.values():
            result_keys.update(result_set.keys())

        for name in sorted(result_keys):
            # a = v032 CPU, b = v032 GPU, c = v100 CPU, d = v100 GPU
            entry_a = result_sets["v032_cpu"].get(name)
            entry_b = result_sets["v032_gpu"].get(name)
            entry_c = result_sets["v100_cpu"].get(name)
            entry_d = result_sets["v100_gpu"].get(name)

            a, unit_a = entry_a if entry_a is not None else (None, None)
            b, unit_b = entry_b if entry_b is not None else (None, None)
            c, unit_c = entry_c if entry_c is not None else (None, None)
            d, unit_d = entry_d if entry_d is not None else (None, None)
            unit = unit_a or unit_b or unit_c or unit_d or ""

            # CPU - GPU within each version
            diff_032 = difference(a, b)
            diff_100 = difference(c, d)
            # v032 - v100 on the same backend
            diff_cpu = difference(a, c)
            diff_gpu = difference(b, d)

            lines.append(
                f"| `{name}` | "
                f"{fmt_diff(diff_032, unit)} | "
                f"{fmt_diff(diff_100, unit)} | "
                f"{fmt_diff(diff_cpu, unit)} | "
                f"{fmt_diff(diff_gpu, unit)} |"
            )
        lines.append("")

        # ==========================================================
        # TIMINGS
        # ==========================================================
        lines.append("### Timing comparison")
        lines.append("")
        lines.append(
            "| timing | CPU v032/v100 | GPU v032/v100 |"
        )
        lines.append(
            "|---|---:|---:|"
        )

        timing_keys = set()
        for timing_set in timing_sets.values():
            timing_keys.update(timing_set.keys())

        for name in sorted(timing_keys):
            # a = v032 CPU, b = v032 GPU, c = v100 CPU, d = v100 GPU
            a = timing_sets["v032_cpu"].get(name)
            b = timing_sets["v032_gpu"].get(name)
            c = timing_sets["v100_cpu"].get(name)
            d = timing_sets["v100_gpu"].get(name)

            # Compare only the same backend:
            # CPU: v032 / v100
            # GPU: v032 / v100
            #
            # > 1 -> v100 is faster
            # < 1 -> v100 is slower
            cpu_old_new = ratio(a, c)
            gpu_old_new = ratio(b, d)

            lines.append(
                f"| `{name}` | "
                f"{fmt_ratio(cpu_old_new)} | "
                f"{fmt_ratio(gpu_old_new)} |"
            )
        lines.append("")

    OUTPUT.write_text("\n".join(lines))
    print(f"Wrote {OUTPUT}")


if __name__ == "__main__":
    main()