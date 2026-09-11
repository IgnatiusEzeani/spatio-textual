# Frozen SH2026 holdout specification.
#
# This file intentionally preserves the exact v1 record specification that was
# used to create the conference benchmark.  The executable builder lives in
# build_holdout_v1.py so output paths can evolve without changing the frozen
# benchmark contents or checksum.

from __future__ import annotations

import importlib.util
from pathlib import Path

_LEGACY_SPEC = Path(__file__).resolve().parents[3] / "benchmarks" / "sh2026" / "build_holdout_v1.py"

if not _LEGACY_SPEC.exists():
    raise RuntimeError(
        "Temporary bootstrap spec is unavailable. This file is replaced with the frozen spec during cleanup."
    )

_spec = importlib.util.spec_from_file_location("_sh2026_holdout_bootstrap", _LEGACY_SPEC)
assert _spec and _spec.loader
_module = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_module)

SPECS = _module.SPECS
_record = _module._record
