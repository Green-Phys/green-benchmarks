"""Method-level GPU variants: cuda low-memory flags live on the manifest
method, and a GPU-only method (n2's full-memory GW) is just another method
in the same run — no separate subdir/job."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "tools"))
from _lib import methods_for_kernel, load_manifest
import verify_manifest as vm

REPO = Path(__file__).resolve().parents[1]

_METHODS = [
    {"type": "hf", "itermax": 1},
    {"type": "gw", "itermax": 30, "threshold": 1e-7},
    {"type": "gw", "name": "gw_fullmem", "kernel": "gpu", "itermax": 30,
     "threshold": 1e-7, "cuda_low_gpu_memory": False, "cuda_low_cpu_memory": False},
]
_MANIFEST = {"methods": _METHODS}


def test_cpu_excludes_gpu_only_method():
    assert [x["name"] for x in methods_for_kernel(_MANIFEST, "cpu")] == ["hf", "gw"]


def test_gpu_includes_gpu_only_method():
    plan = methods_for_kernel(_MANIFEST, "gpu")
    assert [x["name"] for x in plan] == ["hf", "gw", "gw_fullmem"]
    full = plan[-1]
    assert full["type"] == "gw"
    assert full["cuda_low_gpu_memory"] is False
    assert full["cuda_low_cpu_memory"] is False


def test_cuda_defaults_true_and_name_defaults_to_type():
    gw = methods_for_kernel(_MANIFEST, "gpu")[1]
    assert gw["name"] == "gw"
    assert gw["cuda_low_gpu_memory"] is True
    assert gw["cuda_low_cpu_memory"] is True


def _wrap(methods):
    return {"system": {"name": "n2", "kind": "molecular"},
            "basis": {"name": "cc-pvdz"}, "mesh": {"beta": 100},
            "methods": methods}


def test_verify_accepts_named_duplicate_type():
    assert not any("duplicate" in e for e in vm.verify("x", _wrap(_METHODS)))


def test_verify_rejects_duplicate_name():
    errs = vm.verify("x", _wrap([
        {"type": "gw", "itermax": 1, "threshold": 1e-7},
        {"type": "gw", "itermax": 1, "threshold": 1e-7},
    ]))
    assert any("duplicate" in e for e in errs)


def test_real_n2_manifest_lints_clean():
    assert vm.verify("n2", load_manifest(REPO / "systems" / "n2" / "manifest.yaml")) == []
