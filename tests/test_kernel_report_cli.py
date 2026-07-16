import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "tools"))
import kernel_report as kr
from test_kernel_report_engine import _cls


def test_rollup_line_reports_verdict():
    classes = {"v032": _cls({1: -10.0}, "cpu"), "v032_gpu": _cls({1: -10.0}, "gpu"),
               "v100": _cls({1: -10.0}, "cpu"), "v100_gpu": _cls({1: -10.0 + 1e-3}, "gpu")}
    line = kr.rollup_line("demo", classes, tol_kernel_energy=1e-6)
    assert line.startswith("| demo |")
    assert "FAIL" in line
