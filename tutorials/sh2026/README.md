# SH2026 Full-Day Colab Workshop

Working title: **AI and NLP for Spatial Humanities: From Text to Interpretable Spatial Narratives**

## Teaching philosophy

This is not a package walkthrough. Participants should understand what each methodological family can and cannot do, then use `spatio-textual` as the shared implementation environment.

The workshop follows one repeated pattern:

`source text -> method -> output -> error/disagreement -> validation -> interpretation`

Every notebook should run independently after the setup notebook and should contain precomputed fallback outputs for heavyweight/API-dependent sections.

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
4. identify the difference between entity recognition and entity resolution;
5. inspect ambiguity and model disagreement rather than hiding them;
6. compare rule, HF and LLM-capable affect pipelines critically;
7. understand schema-constrained LLM extraction and evidence requirements;
8. construct and inspect structured journey records;
9. export auditable annotations to JSONL/CSV/GeoJSON;
10. explain when human review is necessary in Spatial AI workflows.

## Notebook sequence

### `00_setup_and_orientation.ipynb`

**Duration:** 30 minutes

Contents:

- workshop goals;
- Spatial Humanities framing: location, locale, sense of place;
- clone/install lightweight requirements;
- import package;
- verify environment;
- load teaching examples;
- explain common schema;
- show final end-to-end output so participants know where the day is going.

No GPU/API key required.

### `01_manual_annotation.ipynb`

**Duration:** 35 minutes

Contents:

- one short Lake District passage;
- participant annotation of place names, geo-nouns, spatial relations, distance/time and subjective descriptors;
- compare participant decisions with an instructor reference;
- introduce inter-annotator disagreement and ontology design.

Key message: **human annotation is interpretive too.**

### `02_rules_and_gazetteers.ipynb`

**Duration:** 45 minutes

Contents:

- EntityRuler/project resources;
- deterministic matching;
- inspect successful cases;
- deliberately test spelling variation, unseen terms, ambiguous names and relational language;
- record latency and coverage.

Key message: **transparent and reproducible does not mean complete.**

### `03_contextual_ner.ipynb`

**Duration:** 55 minutes

Contents:

- spaCy small vs transformer model;
- optional HF NER comparison;
- place/entity label differences;
- precision/recall/F1 on a small reference set;
- inspect false positives/negatives;
- model telemetry.

Heavy models should have precomputed outputs available.

Key message: **context helps, but the model's training ontology still constrains what it can see.**

### `04_linking_and_ambiguity.ipynb`

**Duration:** 40 minutes

Contents:

- NER vs entity linking;
- offline GeoResolver;
- candidate ambiguity;
- examples such as common city names and historical polities;
- why original strings must be preserved;
- human review exercise.

Key message: **a coordinate is an interpretation, not simply an annotation.**

### `05_affect_and_events.ipynb`

**Duration:** 50 minutes

Contents:

- sentiment rule baseline;
- emotion rule baseline;
- HF classifiers;
- optional LLM comparison;
- narrator-centred actions/events;
- narrative sequence plot;
- disagreement/error analysis.

Explicitly discuss the limits of emotion taxonomies and avoid presenting labels as psychological ground truth.

Key message: **richer annotation creates richer questions and richer risks.**

### `06_llm_structured_extraction.ipynb`

**Duration:** 60 minutes

Contents:

- why unconstrained prompting is insufficient;
- JSON schema design;
- extract one structured spatial relation/journey;
- require evidence quote;
- validate evidence against source text;
- mark fields explicit vs contextual inference vs missing;
- retry/parse failures;
- optional live provider call plus precomputed outputs.

Key message: **the useful LLM pattern is constrained extraction + evidence + validation, not fluent generation.**

### `07_compare_and_adjudicate.ipynb`

**Duration:** 45 minutes

Contents:

- run rules/spaCy/HF/LLM outputs on matched examples;
- create a side-by-side comparison table;
- use existing adjudication for NER;
- surface disagreements;
- participant accepts/edits/rejects selected outputs;
- measure human correction burden.

Key message: **there is no single method winner across all dimensions.**

### `08_from_text_to_map.ipynb`

**Duration:** 45 minutes

Contents:

- GeoJSON export;
- interactive point map;
- co-occurrence network;
- simple route/journey visualisation;
- compare textual nearness with Euclidean proximity on Lake District examples;
- discuss non-cartographic place references that should not be forced onto a map.

Key message: **mapping is one possible representation of spatial evidence, not its endpoint.**

### `09_responsible_spatial_ai.ipynb`

**Duration:** 30 minutes

Contents:

- provenance;
- uncertainty;
- provider/model drift;
- reproducibility;
- privacy and controlled collections;
- cultural/geographic bias;
- cost/latency;
- human-in-the-loop design;
- final reusable checklist.

Key message: **the more interpretive power we delegate to AI, the stronger the audit trail must become.**

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

## Teaching datasets

### Primary

Lake District texts/examples that can be distributed under their source terms.

Use these for:

- place names;
- geo-nouns;
- `picturesque`/`wild` descriptors;
- nearness expressions;
- map comparison.

### Secondary

Instructor-created oral-history-style examples with Q/A structure, movement, ambiguity and affect.

### Research demonstration only

Controlled-access Holocaust testimony results should be represented through:

- aggregate statistics;
- diagrams;
- schemas;
- precomputed/cleared examples where permitted.

Do not bundle controlled transcripts in public notebooks.

## Colab reliability requirements

Every notebook must:

- run on CPU unless explicitly marked optional;
- have a `FAST_MODE = True` default;
- avoid requiring a participant API key;
- load precomputed results if optional models/providers are unavailable;
- include a `Reset`/re-run-safe workflow;
- avoid writing secrets to notebook output;
- use small examples for live heavy-model comparison;
- finish its default path in a predictable time.

## Shared outputs

Notebooks should write under:

```text
sh2026_outputs/
  annotations/
  comparisons/
  geojson/
  figures/
  human_review/
```

These outputs should use the schema in `docs/sh2026/COMMON_SCHEMA.md` so selected figures/tables can be reused directly in the Streamlit demo and keynote.

## Instructor package

Create before release:

- `INSTRUCTOR_GUIDE.md`;
- expected outputs/reference annotations;
- precomputed model outputs;
- troubleshooting guide;
- offline fallback zip;
- 5-minute and 15-minute contingency exercises if timings slip.

## Next implementation step

Build `00_setup_and_orientation.ipynb`, `01_manual_annotation.ipynb` and `02_rules_and_gazetteers.ipynb` first. They establish the vocabulary and guarantee a useful workshop even if every optional AI service fails.
