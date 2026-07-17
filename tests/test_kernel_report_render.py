import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "tools"))
import kernel_report as kr
from test_kernel_report_engine import _cls  # reuse builder

def test_render_has_sections_and_flags_fail():
    classes = {"old": _cls({1: -10.0}, "cpu"), "old_gpu": _cls({1: -10.0}, "gpu"),
               "new": _cls({1: -10.0}, "cpu"), "new_gpu": _cls({1: -10.0 + 1e-3}, "gpu")}
    md = kr.render_system_report("demo", classes, old_label="v032", new_label="v100a0",
                                 tol_kernel_energy=1e-6, tol_ver_pct=0.1)
    assert "## gw" in md
    assert "e1b" in md
    # column headers carry the injected version labels, not hardwired tags
    assert "v032_gpu" in md and "v100a0_gpu" in md
    assert "Δcpu/gpu@v100a0" in md
    assert "⚠" in md              # the 1e-3 cpu/gpu disagreement is flagged
    assert "FAIL" in md
