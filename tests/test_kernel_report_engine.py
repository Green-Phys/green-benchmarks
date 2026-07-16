import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "tools"))
import kernel_report as kr

def _cls(e1b_by_iter, kernel):
    return {"kernel": kernel, "methods": {"gw": {
        "energies": [{"iter": i, "e1b": v, "ehf": 0.0, "ecorr": 0.0}
                     for i, v in e1b_by_iter.items()],
        "final_iter": max(e1b_by_iter)}}}

def test_energy_diffs_align_by_iter():
    classes = {"v032": _cls({1: -10.0, 2: -12.0}, "cpu"),
               "v032_gpu": _cls({1: -10.0, 2: -12.0}, "gpu"),
               "v100": _cls({1: -10.0, 2: -12.0}, "cpu"),
               "v100_gpu": _cls({1: -10.0, 2: -12.0 + 5e-7}, "gpu")}
    rows = kr.energy_diffs(classes, "gw")
    r = next(x for x in rows if x["obs"] == "e1b" and x["iter"] == 2)
    assert abs(r["d_cpu_gpu_new"] - (-12.0 - (-12.0 + 5e-7))) < 1e-12
    assert r["d_ver_cpu"] == 0.0

def test_verdict_pass_when_cpu_gpu_agree():
    classes = {"v032": _cls({1: -10.0}, "cpu"), "v032_gpu": _cls({1: -10.0}, "gpu"),
               "v100": _cls({1: -10.0}, "cpu"), "v100_gpu": _cls({1: -10.0 + 1e-9}, "gpu")}
    assert kr.verdict(classes, 1e-6)[0] == "PASS"

def test_verdict_fail_when_new_cpu_gpu_disagree():
    classes = {"v032": _cls({1: -10.0}, "cpu"), "v032_gpu": _cls({1: -10.0}, "gpu"),
               "v100": _cls({1: -10.0}, "cpu"), "v100_gpu": _cls({1: -10.0 + 1e-3}, "gpu")}
    assert kr.verdict(classes, 1e-6)[0] == "FAIL"

def test_verdict_suspect_when_control_breaks():
    classes = {"v032": _cls({1: -10.0}, "cpu"), "v032_gpu": _cls({1: -10.0 + 1e-3}, "gpu"),
               "v100": _cls({1: -10.0}, "cpu"), "v100_gpu": _cls({1: -10.0}, "gpu")}
    assert kr.verdict(classes, 1e-6)[0] == "SUSPECT"
