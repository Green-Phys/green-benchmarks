#!/usr/bin/env python3
"""Parse a finished green-mbpt run and persist a results JSON.

Called at the end of every systems/<sys>/run.sh. Reads:
  - the manifest (for the canonical observable id list + units)
  - whatever green-mbpt wrote into $WORK (typically out.h5 + a log)

Writes systems/<sys>/results/<mbpt-ver>_<mbtools-ver>.json via
_lib.write_result so the schema stays consistent across systems.

NOTE: the actual extraction is system- and version-specific. The
manifest tells us what to look for; this script picks the right
green-mbtools accessor. The TODO blocks below are filled in once the
Green output format is locked.
"""
from __future__ import annotations

import argparse
import sys
import time
from pathlib import Path

from _lib import load_manifest, write_result


def _detect_versions(green_root: str | None) -> tuple[str, str]:
    """Resolve installed (mbpt, mbtools) version strings.

    Reads from the loaded python packages first (truth), falls back to
    inspecting $GREEN_VER for a CI environment that has no python deps.
    """
    mbpt_ver = mbtools_ver = "unknown"
    try:
        import green_mbpt  # type: ignore
        mbpt_ver = getattr(green_mbpt, "__version__", "unknown")
    except ImportError:
        pass
    try:
        import green_mbtools  # type: ignore
        mbtools_ver = getattr(green_mbtools, "__version__", "unknown")
    except ImportError:
        try:
            import mbtools  # 0.3.x layout
            mbtools_ver = getattr(mbtools, "__version__", "unknown")
        except ImportError:
            pass
    return mbpt_ver, mbtools_ver


def _extract_observables(work_dir: Path, manifest: dict) -> dict[str, float]:
    """Pull observables out of $WORK/out.h5 (or wherever Green writes).

    The right code here depends on the Green output format. Keep this
    function the *only* place that knows that format, so future format
    bumps land in one file.
    """
    observed: dict[str, float] = {}
    # TODO: open work_dir/'out.h5' (h5py) and populate observed keyed by
    # the manifest's observables[].id. Skip ids the run did not produce
    # — collect.py and compare_versions.py render those as '—'.
    return observed


def _extract_timings(work_dir: Path) -> dict[str, float]:
    """Pull per-section wallclocks from the run log."""
    timings: dict[str, float] = {}
    # TODO: parse the green-mbpt log lines that report per-section
    # wallclock and populate timings (key: section name, value: seconds).
    return timings


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--system",   required=True)
    ap.add_argument("--manifest", required=True)
    ap.add_argument("--work-dir", required=True, type=Path)
    args = ap.parse_args()

    manifest = load_manifest(args.manifest)
    mbpt_ver, mbtools_ver = _detect_versions(None)

    observables = _extract_observables(args.work_dir, manifest)
    timings = _extract_timings(args.work_dir)

    out_path = write_result(
        system_name=args.system,
        mbpt_ver=mbpt_ver,
        mbtools_ver=mbtools_ver,
        observables=observables,
        timings=timings,
        extras={"extracted_at": time.strftime("%Y-%m-%dT%H:%M:%S%z")},
    )
    print(f"wrote {out_path}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
