from __future__ import annotations

from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
REPO_ROOT = PROJECT_ROOT.parents[1]
FROZEN_SPECS = {
    PROJECT_ROOT / "benchmarks" / "holdout_spec_v1.py",
    PROJECT_ROOT / "benchmarks" / "affect_spec_v1.py",
}

# These patterns represent executable path construction into locations that were
# removed during project scoping. Historical/frozen provenance strings are not
# treated as runtime dependencies and may intentionally preserve their original
# text for checksum stability.
FORBIDDEN_RUNTIME_SNIPPETS = (
    'Path("tutorials/sh2026/',
    "Path('tutorials/sh2026/",
    'Path("benchmarks/sh2026/',
    "Path('benchmarks/sh2026/",
    'Path("docs/sh2026/',
    "Path('docs/sh2026/",
    'ROOT / "tutorials" / "sh2026"',
    "ROOT / 'tutorials' / 'sh2026'",
)


def test_live_project_python_uses_project_scoped_runtime_paths():
    offenders: list[str] = []
    this_file = Path(__file__).resolve()
    for path in PROJECT_ROOT.rglob("*.py"):
        resolved = path.resolve()
        if resolved == this_file or resolved in {p.resolve() for p in FROZEN_SPECS}:
            continue
        text = path.read_text(encoding="utf-8")
        hits = [marker for marker in FORBIDDEN_RUNTIME_SNIPPETS if marker in text]
        if hits:
            offenders.append(f"{path.relative_to(REPO_ROOT)}: {', '.join(hits)}")
    assert not offenders, "Legacy SH2026 runtime paths remain:\n" + "\n".join(offenders)
