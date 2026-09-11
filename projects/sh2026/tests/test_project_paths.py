from __future__ import annotations

from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
REPO_ROOT = PROJECT_ROOT.parents[1]

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
    for path in PROJECT_ROOT.rglob("*.py"):
        if path == Path(__file__).resolve():
            continue
        text = path.read_text(encoding="utf-8")
        hits = [marker for marker in FORBIDDEN_RUNTIME_SNIPPETS if marker in text]
        if hits:
            offenders.append(f"{path.relative_to(REPO_ROOT)}: {', '.join(hits)}")
    assert not offenders, "Legacy SH2026 runtime paths remain:\n" + "\n".join(offenders)
