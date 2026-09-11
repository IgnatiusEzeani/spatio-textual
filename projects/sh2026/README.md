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
├── config/            # guarded experiment trigger/config files
├── demo/              # conference-specific Streamlit experience
├── docs/              # protocols, result records and keynote evidence
├── scripts/           # SH2026 experiment runners and training scripts
├── tests/             # project-boundary and SH2026 regression tests
└── workshop/          # tutorial notebooks, data and instructor material
```

GitHub Actions workflow definitions remain under `.github/workflows/`, because GitHub requires workflows there, but SH2026 workflows reference resources under this project directory and are guarded so routine package changes do not repeat paid conference experiments.

## Run the conference demo locally

From the repository root:

```bash
python -m pip install -r requirements-lite.txt
streamlit run projects/sh2026/demo/streamlit_app.py
```

The public-safe guided path does not require an API key. Live LLM journey extraction is optional and uses a server-side `OPENAI_API_KEY` when configured.

## Release relationship

The intended release relationship is:

- **spatio-textual**: reusable Python package, independently versioned and documented.
- **SH2026 resources**: reproducible research/teaching layer pinned to a known package release or commit.

The SH2026 benchmark results are not package guarantees. They are project-specific empirical results with explicit provenance and claim boundaries.

## SH2026 completion gate

Before the conference release is considered ready, the project should have: the NER, journey and affect comparison rows frozen; the package/project boundary regression-tested; all ten workshop notebooks passing in a clean CPU environment; the project-scoped Streamlit health check passing without an API key; package tests and compatibility checks green; and the deployed demo rehearsed using only public-safe material.
