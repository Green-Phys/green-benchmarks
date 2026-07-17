import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "tools"))
import kernel_report as kr
from test_kernel_report_engine import _cls


def test_rollup_line_reports_verdict():
    classes = {"old": _cls({1: -10.0}, "cpu"), "old_gpu": _cls({1: -10.0}, "gpu"),
               "new": _cls({1: -10.0}, "cpu"), "new_gpu": _cls({1: -10.0 + 1e-3}, "gpu")}
    line = kr.rollup_line("demo", classes, tol_kernel_energy=1e-6)
    assert line.startswith("| demo |")
    assert "FAIL" in line


def test_labels_from_tag_strips_version_suffix():
    # display label = the mbpt version tag (prefix before first '_'),
    # which is exactly VERSION_OLD / VERSION_NEW from env.sh
    assert kr.label_from_tag("v032_0.3.0") == "v032"
    assert kr.label_from_tag("v100a0_1.0.0a1") == "v100a0"
