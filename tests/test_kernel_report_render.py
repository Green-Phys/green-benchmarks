import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "tools"))
import kernel_report as kr
from test_kernel_report_engine import _cls  # reuse builder

def test_render_has_sections_and_flags_fail():
    classes = {"v032": _cls({1: -10.0}, "cpu"), "v032_gpu": _cls({1: -10.0}, "gpu"),
               "v100": _cls({1: -10.0}, "cpu"), "v100_gpu": _cls({1: -10.0 + 1e-3}, "gpu")}
    md = kr.render_system_report("demo", classes, tol_kernel_energy=1e-6, tol_ver_pct=0.1)
    assert "## gw" in md
    assert "e1b" in md
    assert "v032_gpu" in md and "Δcpu/gpu@v100" in md
    assert "⚠" in md              # the 1e-3 cpu/gpu disagreement is flagged
    assert "FAIL" in md
