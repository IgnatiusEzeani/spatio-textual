# Spatial Humanities 2026: Keynote, Tutorial and Demo Roadmap

Working branch: `spatial-humanities-2026`

## Goal

Turn `spatio-textual` into one coherent Spatial Humanities 2026 package with three public-facing outputs:

1. a full-day Google Colab tutorial/workshop;
2. a hosted interactive demo;
3. a keynote lecture comparing manual annotation, rule-based NLP, statistical/transformer NLP and LLM-assisted workflows.

The three outputs should share the same examples, data schema, evaluation language and visual identity rather than becoming separate projects.

## Core principle

Use one end-to-end research story:

`text -> segmentation -> annotation -> entity linking -> affect/event extraction -> validation/review -> spatial analysis -> visualisation -> interpretation`

At each stage, expose at least two methodological choices and their trade-offs. Preserve source evidence and provenance throughout.

## Deliverables

### A. Full-day Colab tutorial

- Landing notebook with setup, learning goals and schedule.
- Notebook 1: text, spatial humanities and baseline/manual annotation.
- Notebook 2: rule-based and spaCy entity extraction.
- Notebook 3: transformer NER and model comparison.
- Notebook 4: sentiment/emotion and narrator-centred events.
- Notebook 5: LLM-assisted structured extraction and prompt/schema design.
- Notebook 6: entity linking, ambiguity, human review and adjudication.
- Notebook 7: GeoJSON, co-occurrence, maps and interpretation.
- Instructor notebook / answer key.
- Precomputed outputs so the workshop remains usable without API keys or GPU availability.

### B. Hosted demo

Build from the existing `app.py`, retaining the current model selection, review queue, telemetry and export functionality.

Priority additions:

- clear Home / Annotate / Compare / Explore / About workflow;
- side-by-side source text and extracted annotations;
- visible method comparison for rule/spaCy/HF/LLM outputs;
- interactive map rather than raw GeoJSON only;
- per-segment affect plots and narrative sequence views;
- evidence/provenance display for every interpretive output;
- human correction/adjudication controls;
- curated public-safe example texts and presets;
- hosted deployment with cached models, graceful API-key handling and a lightweight default mode.

Stretch goal: add schema-constrained journey extraction with origin, destination, transport, date/reason and evidence quote.

### C. Keynote lecture

Provisional thesis:

> AI does not make traditional Spatial Humanities methods obsolete. It changes where the bottlenecks lie: from finding explicit spatial signals to validating, interpreting and governing increasingly rich machine-generated representations of human experience.

Proposed comparative spine:

1. Manual annotation: interpretively rich, transparent, expensive and difficult to scale.
2. Rule/gazetteer methods: deterministic, fast, reproducible and excellent on bounded tasks, but brittle outside the anticipated vocabulary and forms.
3. Statistical/transformer NLP: contextual and scalable, but dependent on training domains, label inventories and benchmark assumptions.
4. LLMs: flexible structured extraction, implicit relations and rapid adaptation, but with hallucination, opacity, cost, non-determinism and governance risks.
5. Hybrid/human-in-the-loop workflows: use each method where it is strongest and retain evidence, disagreement and provenance.

Anchor case studies:

- Lake District writing: named places, geo-nouns, picturesque/wild descriptions and textual proximity.
- Holocaust survivor testimonies: Q/A-aware segmentation, journeys, affect and evidence-grounded extraction.
- Curatorial/archival workflow: AI as review and discovery support rather than automated historical authority.

## One-week sprint

### Day 1: Audit, scope and freeze the teaching schema

- Verify current v0.3 installation and tests.
- Freeze a common annotation schema for notebooks, app and keynote.
- Select 3-4 public-safe teaching texts.
- Define the comparison matrix and evaluation measures.
- Create notebook skeletons and demo information architecture.

Exit criterion: every later deliverable uses the same fields, examples and terminology.

### Day 2: Build tutorial core

- Implement setup/landing notebook.
- Implement manual/rule/spaCy notebooks.
- Add exercises and expected outputs.
- Add lightweight install path and precomputed fallback results.

Exit criterion: morning half of workshop runs end-to-end in a fresh Colab runtime.

### Day 3: Build advanced tutorial

- Add HF model comparison.
- Add sentiment/emotion/events.
- Add LLM structured extraction with optional API-key cells.
- Add adjudication and telemetry exercises.

Exit criterion: full workshop can run without forcing every participant to call a paid API.

### Day 4: Upgrade hosted demo

- Refactor app into user-facing sections/pages.
- Add highlighted annotation view, comparison table and proper map.
- Add affect/narrative visualisation and review UI.
- Add public-safe examples and explanatory text.

Exit criterion: a non-technical humanities researcher can understand what happened to their text without opening JSON.

### Day 5: Deployment and robustness

- Run tests and add smoke tests for tutorial/demo paths.
- Test Docker/Hugging Face Space and/or Streamlit deployment.
- Cache models and handle unavailable heavyweight/LLM backends cleanly.
- Test on desktop and projector-sized displays.

Exit criterion: stable public URL plus a fully offline/lightweight fallback.

### Day 6: Keynote deck architecture

- Create a 45-55 minute slide storyboard.
- Reuse outputs generated by the tutorial and demo as keynote evidence.
- Build the central comparison graphic and 3-4 signature visualisations.
- Draft opening, transitions and conclusion.

Exit criterion: complete slide-by-slide narrative before visual polishing.

### Day 7: Integration and rehearsal package

- Run the workshop as a participant from a clean environment.
- Run the public demo from a fresh browser/session.
- Rehearse the talk against the live demo/screenshots.
- Freeze release candidate, links and QR codes.
- Produce a facilitator checklist and failure-mode backup plan.

Exit criterion: tutorial, demo and keynote tell one coherent story and can survive network/API/model failure.

## Evaluation matrix for the keynote and tutorial

Compare methods on:

- annotation effort;
- precision/recall where gold labels exist;
- ability to capture explicit vs implicit spatial information;
- robustness to spelling, ambiguity and historical language;
- portability across corpora;
- reproducibility/determinism;
- latency and computational requirements;
- financial/API cost;
- explainability and evidence traceability;
- ease of correction;
- privacy/data-governance risk;
- suitability for sensitive collections.

Avoid presenting the methods as a simple linear progression from 'old' to 'better'. The strongest argument is methodological complementarity.

## Scope guardrails

For the one-week sprint, do not attempt to build a general-purpose GIS platform, full RAG copilot, multimodal audio/video pipeline or archive-scale production system. The target is a polished research/teaching demonstrator with clear provenance and defensible comparisons.

Controlled-access Holocaust testimony text must not be bundled into the public repository or Colab notebooks. Use public-safe excerpts where permissions allow, synthetic structurally realistic examples, or precomputed aggregate outputs.

## Release target

Tag the integrated release only after tutorial and demo smoke tests pass. Suggested milestone name: `sh2026-rc1`.
