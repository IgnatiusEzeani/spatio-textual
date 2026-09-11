# Spatial Humanities 2026 project resources

This directory contains the conference-specific research, teaching, benchmarking and demonstration resources for Spatial Humanities 2026.

The reusable Python library remains independent in [`spatio_textual/`](../../spatio_textual), with its package metadata, tests and general application at repository level. SH2026 resources consume the public package API; the package must not import from `projects/sh2026`.

## Project boundary

Use a simple rule when deciding where new code belongs:

> If the SH2026 project disappeared tomorrow, would this code still belong in `spatio-textual`?

If yes, it belongs in the reusable package. If no, it belongs here.

Package-level capabilities include generic spatial annotation, NER, journey extraction, affect analysis, model clients, evidence grounding, evaluation primitives, provenance, review, telemetry and visualisation.

SH2026-specific assets include frozen benchmark corpora and checksums, experiment runners/configuration, workshop notebooks, keynote evidence and results, and the conference Streamlit demo.

## Structure

```text
projects/sh2026/
├── README.md
├── ROADMAP.md
├── benchmarks/        # frozen and development research corpora/builders
├── docs/              # protocols, result records and keynote evidence
├── scripts/           # SH2026 experiment runners and training scripts
├── workshop/          # tutorial notebooks, data and instructor material
└── demo/
    └── app.py          # conference-specific Streamlit experience
```

GitHub Actions workflow definitions remain under `.github/workflows/`, because GitHub requires workflows there, but SH2026 workflows should reference resources under this project directory and should be guarded so routine package changes do not trigger paid or heavyweight conference experiments.

## Release relationship

The intended release relationship is:

- **spatio-textual**: reusable Python package, independently versioned and documented.
- **SH2026 resources**: reproducible research/teaching layer pinned to a known package release or commit.

The SH2026 benchmark results are not package guarantees. They are project-specific empirical results with explicit provenance and claim boundaries.
