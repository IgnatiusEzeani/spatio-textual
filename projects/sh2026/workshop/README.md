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

All ten default CPU notebook paths have passed automated execution during SH2026 development. The release workflow now executes the checked-out PR/release candidate rather than cloning a previously published branch. A fresh current-head automated run plus a manual Google Colab rehearsal remain release gates.

## Notebook sequence and teaching messages

### 00 · Setup and orientation — 30 min

Location, locale and sense of place; install the SH2026 release; load public-safe examples; introduce the common schema.

**Message:** spatial information in text is broader than named coordinates.

### 01 · Manual annotation — 35 min

Annotate places, geo-nouns, relations, distance/time and subjective descriptors; compare judgements and expose span/ontology disagreement.

**Message:** human annotation is interpretive too.

### 02 · Rules and gazetteers — 45 min

Run deterministic EntityRuler/regex/gazetteer baselines and inspect both successful cases and brittle failures.

**Message:** transparent and reproducible does not mean complete.

### 03 · Contextual NER — 55 min

Compare contextual spaCy/HF recognition and distinguish within-ontology accuracy from representational reach.

**Message:** context helps, but the training ontology still constrains what the model can see.

### 04 · Linking, ambiguity and historical geography — 40 min

Separate recognition from resolution; inspect candidate ambiguity and preserve historical place identities rather than silently modernising them.

**Message:** a coordinate is an interpretation, not simply an annotation.

### 05 · Affect and narrator-centred events — 50 min

Compare sentiment/emotion signals and narrator-centred movement/action events while exposing lexical and domain assumptions.

**Message:** model-labelled affect is an analytical signal, not psychological ground truth.

### 06 · Evidence-first LLM structured extraction — 60 min

Use a constrained journey schema, require literal evidence, compute offsets locally and preserve `explicit`, `contextual_inference` and `missing` provenance.

**Message:** the useful LLM pattern is constrained extraction + evidence + validation, not fluent generation.

### 07 · Compare, disagree and adjudicate — 45 min

Compare methods without erasing disagreement; record accept/edit/reject review events and correction burden.

**Message:** there is no single method winner across all dimensions.

### 08 · From text to map — 35–45 min

Create point and journey GeoJSON, inspect unresolved-route audits, map where appropriate and retain non-map spatial representations such as co-occurrence.

**Message:** mapping is one possible representation of spatial evidence, not its endpoint.

### 09 · Responsible Spatial AI — 20–30 min

Inspect provenance, uncertainty, data governance, model/provider drift and the release checklist.

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

**Primary:** Lake District examples that can be distributed under their source terms, for named places, geo-nouns, landscape descriptors, textual nearness and map comparison.

**Secondary:** instructor-created public-safe oral-history/travel examples with Q/A structure, movement, ambiguity, affect and missing fields.

**Research demonstration only:** controlled-access Holocaust testimony results should be represented through aggregate statistics, diagrams, schemas and cleared/precomputed material where permitted. Do **not** bundle controlled transcripts in the public notebooks or repository.

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

## Reliability and release gates

Every release candidate must:

- execute all ten default notebook paths on CPU without participant API keys;
- provide a documented fallback for heavyweight/API-dependent sections;
- be safe to re-run from the top without leaking credentials;
- record model/backend/version information for empirical outputs;
- preserve public-safe data boundaries;
- pass the current-head automated smoke suite;
- pass at least one fresh manual Google Colab rehearsal.

The operational go/no-go checklist is `projects/sh2026/docs/RELEASE_CHECKLIST.md`.

## Instructor package

`INSTRUCTOR_GUIDE.md` now provides the delivery sequence, troubleshooting guidance, no-network/no-API routes and 5-minute/15-minute contingencies. Before `sh2026-rc1`, the remaining packaging work is to freeze provenance-complete precomputed transformer/LLM fallbacks, record a fresh manual Colab run, and assemble the lightweight/offline teaching fallback.

## Current implementation block

1. Keep current-head CI green after project disaggregation and notebook-path hardening.
2. Use `projects/sh2026/benchmarks/results_snapshot_v1.json` as the single reportable metric feed for the conference demo/keynote, rather than hard-coded UI numbers.
3. Complete provenance-complete fallback outputs for optional heavyweight/API sections.
4. Rehearse the hosted Streamlit demo from a clean browser with no API key, then with optional live LLM access.
5. Run the final manual Google Colab rehearsal and record it in the release checklist.

The workshop core is structurally complete. The remaining work is release validation, fallback packaging and presentation rehearsal rather than notebook construction.
