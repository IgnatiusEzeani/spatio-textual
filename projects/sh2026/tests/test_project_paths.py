from __future__ import annotations

from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
REPO_ROOT = PROJECT_ROOT.parents[1]
FROZEN_SPECS = {
    PROJECT_ROOT / "benchmarks" / "holdout_spec_v1.py",
    PROJECT_ROOT / "benchmarks" / "affect_spec_v1.py",
}
FORBIDDEN = (
    "tutorials/sh2026/",
    "docs/sh2026/",
    "benchmarks/sh2026/",
    "scripts/run_sh2026_",
    "scripts/generate_sh2026_",
    "scripts/train_sh2026_",
    "sh2026_app.py",
)


def test_live_project_code_uses_project_scoped_paths():
    offenders: list[str] = []
    candidates = list(PROJECT_ROOT.rglob("*.py")) + list(PROJECT_ROOT.rglob("*.ipynb"))
    for path in candidates:
        if path in FROZEN_SPECS:
            continue
        text = path.read_text(encoding="utf-8")
        hits = [marker for marker in FORBIDDEN if marker in text]
        if hits:
            offenders.append(f"{path.relative_to(REPO_ROOT)}: {', '.join(hits)}")
    assert not offenders, "Legacy SH2026 paths remain in live project code:\n" + "\n".join(offenders)
