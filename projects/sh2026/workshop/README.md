# SH2026 Full-Day Colab Workshop

Official title: **AI and NLP for Spatial Humanities: From Manual Annotation to LLM-Assisted Interpretation**

Keynote companion: **From Coordinates to Context: Rethinking Spatial Humanities in the Age of Large Language Models**

## Teaching philosophy

This is not a package walkthrough and not an argument that newer methods simply replace older ones. Participants should understand what each methodological family can and cannot represent, then use `spatio-textual` as the shared implementation environment.

The workshop follows one repeated pattern:

`source text -> method -> output -> error/disagreement -> validation -> interpretation`

Across the day, the methodological sequence is:

`manual annotation -> rules/gazetteers -> contextual NLP -> entity resolution -> affect/events -> evidence-first LLM extraction -> adjudication -> mapping -> responsible Spatial AI`

Every notebook should run independently after setup and should contain or point to a fallback path for heavyweight/API-dependent sections.

## Audience assumptions

- Spatial/Digital Humanities researchers;
- mixed coding experience;
- Python familiarity helpful but not required;
- no assumption of GPU access;
- no requirement for paid LLM API keys.

## Learning outcomes

By the end of the day, participants should be able to:

1. explain why spatial information in text extends beyond named mappable places;
2. manually define and annotate a small spatial-information task;
3. compare rule/gazetteer, spaCy and transformer NER approaches;
4. distinguish recognition, resolution, relation and interpretation;
5. inspect ambiguity and model disagreement rather than hiding them;
6. compare rule, HF and LLM-capable affect pipelines critically;
7. understand schema-constrained LLM extraction and evidence requirements;
8. construct and inspect structured journey records;
9. record human accept/edit/reject decisions in an auditable way;
10. export auditable annotations to JSONL/CSV/GeoJSON;
11. explain why some spatial evidence should not be forced onto a point map;
12. document provenance, uncertainty, model drift and data-governance constraints.

## Notebook status

| Notebook | Topic | Status |
|---|---|---|
| `00_setup_and_orientation.ipynb` | Setup, location/locale/sense of place, common schema | Implemented |
| `01_manual_annotation.ipynb` | Human reference annotation and disagreement | Implemented |
| `02_rules_and_gazetteers.ipynb` | Deterministic baseline and rule failure analysis | Implemented |
| `03_contextual_ner.ipynb` | spaCy/HF NER, ontology ceiling, representational reach | Implemented |
| `04_linking_and_ambiguity.ipynb` | Entity resolution, ambiguity, historical geography | Implemented |
| `05_affect_and_events.ipynb` | Sentiment, emotion and narrator-centred events | Implemented |
| `06_llm_structured_extraction.ipynb` | Evidence-first structured journey extraction | Implemented |
| `07_compare_and_adjudicate.ipynb` | Model disagreement, human review and correction burden | Implemented |
| `08_from_text_to_map.ipynb` | Entity/journey GeoJSON, route audit and mapping | Implemented |
| `09_responsible_spatial_ai.ipynb` | Provenance, uncertainty, governance and release audit | Implemented |

**Important:** “Implemented” means the notebook content and code path exist. It does not yet mean every notebook has passed a fresh Google Colab smoke test or has its final precomputed heavyweight-model outputs.

## Notebook sequence and teaching messages

### 00 · Setup and orientation — 30 min

- Spatial Humanities framing: location, locale and sense of place;
- install the SH2026 branch;
- load public-safe teaching examples;
- introduce the common audit schema;
- show the end-to-end destination.

**Message:** spatial information in text is broader than named coordinates.

### 01 · Manual annotation — 35 min

- annotate places, geo-nouns, relations, distance/time and subjective descriptors;
- compare participant judgements with a documented reference;
- expose span, ontology and selection disagreement.

**Message:** human annotation is interpretive too.

### 02 · Rules and gazetteers — 45 min

- bounded gazetteer/project resources;
- deterministic EntityRuler/regex baseline;
- inspect successful cases and brittle failures;
- record latency and coverage.

**Message:** transparent and reproducible does not mean complete.

### 03 · Contextual NER — 55 min

- separate contextual spaCy NER from spaCy + project resources;
- optional HF NER comparison;
- harmonise labels for evaluation;
- distinguish within-ontology accuracy from representational reach.

**Message:** context helps, but the training ontology still constrains what the model can see.

### 04 · Linking, ambiguity and historical geography — 40 min

- NER vs entity resolution;
- offline `GeoResolver`;
- candidate ambiguity;
- historical polities such as `Czechoslovakia` preserved rather than silently modernised;
- append-only review exercise.

**Message:** a coordinate is an interpretation, not simply an annotation.

### 05 · Affect and narrator-centred events — 50 min

- sentiment and emotion rule baselines;
- inspect the lexical cues driving classifications;
- demonstrate domain-assumption leakage;
- optional HF comparison;
- narrator-centred movement/action events;
- narrative-sequence plot.

**Message:** model-labelled affect is an analytical signal, not psychological ground truth.

### 06 · Evidence-first LLM structured extraction — 60 min

- inspect the journey JSON contract;
- require verbatim source evidence;
- compute offsets locally rather than trusting model-generated offsets;
- distinguish `explicit`, `contextual_inference` and `missing`;
- demonstrate unsupported evidence and invalid-schema handling;
- optional live provider call;
- preserve `null` when the source is silent.

**Message:** the useful LLM pattern is constrained extraction + evidence + validation, not fluent generation.

### 07 · Compare, disagree and adjudicate — 45 min

- model voting without erasing disagreement;
- accept/edit/reject review events;
- review burden vs correction burden;
- tidy comparison-table skeleton for benchmark/keynote use.

**Message:** there is no single method winner across all dimensions.

### 08 · From text to map — 35–45 min

- point GeoJSON;
- auditable journey route GeoJSON;
- ambiguous/unresolved route audit;
- interactive Folium map;
- textual nearness vs Euclidean distance;
- co-occurrence as a non-route representation;
- spatial evidence that should not be forced onto a point map.

**Message:** mapping is one possible representation of spatial evidence, not its endpoint.

### 09 · Responsible Spatial AI — 20–30 min

- secret-safe run manifests and input hashes;
- uncertainty in exported data;
- public vs restricted material;
- model/provider drift;
- human-review triggers;
- multidimensional benchmark criteria;
- final release checklist.

**Message:** the more interpretive power delegated to AI, the stronger the audit trail must become.

## Proposed day schedule

| Time | Activity |
|---|---|
| 09:30-10:00 | Setup and conceptual framing |
| 10:00-10:35 | Manual annotation |
| 10:35-11:20 | Rules and gazetteers |
| 11:20-11:35 | Break |
| 11:35-12:30 | Contextual NER |
| 12:30-13:10 | Linking and ambiguity |
| 13:10-14:00 | Lunch |
| 14:00-14:50 | Affect and events |
| 14:50-15:50 | LLM structured extraction |
| 15:50-16:05 | Break |
| 16:05-16:50 | Compare and adjudicate |
| 16:50-17:25 | Text to map |
| 17:25-17:45 | Responsible Spatial AI + wrap-up |

The schedule is deliberately modular. If earlier discussion runs long, Notebook 09 can be used as a concise closing checklist and parts of Notebook 08 can be demonstrated rather than completed hands-on.

## Teaching datasets

### Primary

Lake District examples that can be distributed under their source terms. Use these for named places, geo-nouns, landscape descriptors, textual nearness and map comparison.

### Secondary

Instructor-created public-safe oral-history/travel examples with Q/A structure, movement, ambiguity, affect and missing fields.

### Research demonstration only

Controlled-access Holocaust testimony results should be represented through aggregate statistics, diagrams, schemas and cleared/precomputed material where permitted. Do **not** bundle controlled transcripts in the public notebooks or repository.

## Shared outputs

Notebooks write under:

```text
sh2026_outputs/
  annotations/
  comparisons/
  geojson/
  figures/
  human_review/
```

Outputs should follow `projects/sh2026/docs/COMMON_SCHEMA.md` so selected tables and figures can be reused directly in the hosted demo and keynote.

## Colab reliability requirements

Before release, every notebook must:

- run on CPU on its default path unless clearly marked optional;
- avoid requiring a participant API key;
- skip or use documented precomputed outputs when optional models/providers are unavailable;
- be safe to re-run from the top;
- avoid printing or persisting secrets;
- record model/backend/version information for empirical outputs;
- use small examples for live heavyweight comparison;
- finish its default path in a predictable time.

## Instructor package still required

Before the workshop release candidate, create:

- `INSTRUCTOR_GUIDE.md`;
- expected outputs/reference annotations;
- precomputed transformer/LLM outputs with provenance manifests;
- troubleshooting guide;
- offline/lightweight fallback package;
- 5-minute and 15-minute contingency exercises;
- clean-Colab smoke-test record.

## Immediate next implementation block

1. Run CI after the new review/provenance/journey-mapping utilities.
2. Smoke-test notebooks `00`–`09` from clean environments, prioritising their CPU/default paths.
3. Freeze a held-out benchmark set before further method/prompt tuning.
4. Build the benchmark runner and first empirical keynote figures.
5. Refactor the Streamlit app around **Home / Annotate / Compare / Explore / Review / About** using the same review, provenance and journey-mapping utilities.

The workshop core is now structurally complete; the next phase is **validation, benchmarking, fallback generation and demo integration**.
