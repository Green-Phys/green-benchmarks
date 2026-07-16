"""Tests for kernel-aware write_result / extract_results.

write_result real signature:
    write_result(system_name, mbpt_ver, mbtools_ver, methods, extras=None)
    writes to systems/<system_name>/results/<mbpt_ver>_<mbtools_ver>.json

For testing we monkeypatch _lib.results_dir so the output lands in tmp_path.
"""
import json
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "tools"))
import _lib
from _lib import write_result

_METHODS = {
    "gw": {
        "name": "gw",
        "energies": [{"iter": 1, "e1b": -1.0, "ehf": -0.5, "ecorr": -0.1}],
        "final_iter": 1,
        "timings": {},
    }
}


def test_write_result_cpu_default(tmp_path, monkeypatch):
    """CPU (default) path: filename unchanged, kernel field = 'cpu'."""
    monkeypatch.setattr(_lib, "results_dir", lambda name: tmp_path)
    out = write_result("sys", "v032", "0.3.0", _METHODS)
    assert out == tmp_path / "v032_0.3.0.json"
    data = json.loads(out.read_text())
    assert data["kernel"] == "cpu"
    assert data["schema"] == 3


def test_write_result_tags_kernel_gpu(tmp_path, monkeypatch):
    """GPU path: filename gets _gpu suffix, kernel field = 'gpu'."""
    monkeypatch.setattr(_lib, "results_dir", lambda name: tmp_path)
    out = write_result("sys", "v032", "0.3.0", _METHODS, kernel="gpu")
    assert out == tmp_path / "v032_0.3.0_gpu.json"
    data = json.loads(out.read_text())
    assert data["kernel"] == "gpu"
    assert data["schema"] == 3
