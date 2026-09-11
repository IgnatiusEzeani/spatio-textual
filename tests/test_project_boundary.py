from __future__ import annotations

from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
PACKAGE = ROOT / "spatio_textual"
PROJECT = ROOT / "projects" / "sh2026"


def test_reusable_package_does_not_import_sh2026_project_layer():
    forbidden = ("projects.sh2026", "projects/sh2026", "tutorials/sh2026", "docs/sh2026")
    offenders: list[str] = []
    for path in PACKAGE.rglob("*.py"):
        source = path.read_text(encoding="utf-8")
        if any(marker in source for marker in forbidden):
            offenders.append(str(path.relative_to(ROOT)))
    assert not offenders, "Reusable package depends on SH2026 project layer: " + ", ".join(offenders)


def test_sh2026_has_single_project_scoped_home():
    assert PROJECT.is_dir()
    for required in ("benchmarks", "demo", "docs", "scripts", "tests", "workshop"):
        assert (PROJECT / required).exists(), f"Missing project-scoped SH2026 path: {required}"


def test_legacy_sh2026_duplicate_locations_are_absent():
    legacy = [
        ROOT / "SH2026_ROADMAP.md",
        ROOT / "benchmarks" / "sh2026",
        ROOT / "docs" / "sh2026",
        ROOT / "tutorials" / "sh2026",
        ROOT / "sh2026_app.py",
    ]
    legacy.extend((ROOT / "scripts").glob("*sh2026*"))
    legacy.extend((ROOT / ".github").glob("sh2026_*_scope"))
    existing = [str(path.relative_to(ROOT)) for path in legacy if path.exists()]
    assert not existing, "Legacy SH2026 duplicates remain: " + ", ".join(existing)
