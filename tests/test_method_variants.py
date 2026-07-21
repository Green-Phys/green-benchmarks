"""GPU runs use a parallel, self-contained `gpu_methods:` section (not the
CPU `methods:` list): a smaller plan (e.g. 1xHF + 2xGW) with its own itermax,
threshold and cuda flags. methods_for_kernel() reads `methods` for cpu and
`gpu_methods` for gpu — no per-method kernel filtering."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "tools"))
from _lib import methods_for_kernel, has_gpu_methods, load_manifest
import verify_manifest as vm

REPO = Path(__file__).resolve().parents[1]

_MANIFEST = {
    "methods": [
        {"type": "hf", "itermax": 1},
        {"type": "gf2", "itermax": 1},
        {"type": "gw", "itermax": 30, "threshold": 1e-7},
    ],
    "gpu_methods": [
        {"type": "hf", "itermax": 1},
        {"type": "gw", "itermax": 2, "threshold": 1e-7},
        {"type": "gw", "output_tag": "gw_fullmem", "itermax": 2, "threshold": 1e-7,
         "cuda_low_gpu_memory": False, "cuda_low_cpu_memory": False},
    ],
}


def test_cpu_reads_methods_section():
    plan = methods_for_kernel(_MANIFEST, "cpu")
    assert [(x["output_tag"], x["itermax"]) for x in plan] == [
        ("hf", 1), ("gf2", 1), ("gw", 30)]


def test_gpu_reads_gpu_methods_section():
    plan = methods_for_kernel(_MANIFEST, "gpu")
    assert [(x["output_tag"], x["type"], x["itermax"]) for x in plan] == [
        ("hf", "hf", 1), ("gw", "gw", 2), ("gw_fullmem", "gw", 2)]


def test_gpu_full_memory_variant_flags():
    full = methods_for_kernel(_MANIFEST, "gpu")[-1]
    assert full["cuda_low_gpu_memory"] is False
    assert full["cuda_low_cpu_memory"] is False


def test_gpu_defaults_cuda_true_and_output_tag_from_type():
    gw = methods_for_kernel(_MANIFEST, "gpu")[1]
    assert gw["output_tag"] == "gw"
    assert gw["cuda_low_gpu_memory"] is True and gw["cuda_low_cpu_memory"] is True


def test_no_gpu_methods_means_empty_gpu_plan():
    cpu_only = {"methods": [{"type": "hf", "itermax": 1}]}
    assert methods_for_kernel(cpu_only, "gpu") == []
    assert has_gpu_methods(cpu_only) is False
    assert has_gpu_methods(_MANIFEST) is True


def _wrap(methods=None, gpu_methods=None):
    m = {"system": {"name": "n2", "kind": "molecular"},
         "basis": {"name": "cc-pvdz"}, "mesh": {"beta": 100},
         "methods": methods if methods is not None else [{"type": "hf", "itermax": 1}]}
    if gpu_methods is not None:
        m["gpu_methods"] = gpu_methods
    return m


def test_verify_accepts_gpu_methods_section():
    assert vm.verify("x", _wrap(_MANIFEST["methods"], _MANIFEST["gpu_methods"])) == []


def test_verify_rejects_duplicate_output_tag_within_gpu_methods():
    errs = vm.verify("x", _wrap(gpu_methods=[
        {"type": "gw", "itermax": 2, "threshold": 1e-7},
        {"type": "gw", "itermax": 2, "threshold": 1e-7},
    ]))
    assert any("duplicate" in e for e in errs)


def test_verify_rejects_bad_gpu_method_type():
    errs = vm.verify("x", _wrap(gpu_methods=[{"type": "xyz", "itermax": 1}]))
    assert any("type" in e for e in errs)


def test_real_n2_manifest_lints_clean_and_has_gpu_plan():
    man = load_manifest(REPO / "systems" / "n2" / "manifest.yaml")
    assert vm.verify("n2", man) == []
    assert has_gpu_methods(man) is True
    assert [x["output_tag"] for x in methods_for_kernel(man, "gpu")] == [
        "hf", "gw", "gw_fullmem"]
