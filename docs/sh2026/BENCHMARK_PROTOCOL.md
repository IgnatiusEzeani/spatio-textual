# SH2026 Comparative Benchmark Protocol

Status: **protocol frozen; benchmark examples/results not yet frozen**

Purpose: generate defensible empirical evidence for the workshop, hosted demo and keynote without turning the comparison into a simplistic model leaderboard.

## 1. Research question

The benchmark asks two related but distinct questions:

1. **Within-task performance:** how accurately does each method perform the task it is designed to perform?
2. **Representational reach and audit burden:** what kinds of spatial information can the method represent, and what validation/review work does that representation create?

A high NER F1 and a high-capability structured LLM answer different questions. They must not be collapsed into one score.

## 2. Methods to compare

Target methodological families:

1. human reference/manual annotation;
2. deterministic rules/gazetteers;
3. contextual spaCy NER without project rules;
4. contextual spaCy + project resources (hybrid);
5. optional Hugging Face transformer NER;
6. schema-constrained LLM journey extraction;
7. hybrid/adjudicated workflows where relevant.

Record exact backend/model/version at runtime. Do not use labels such as simply `AI` or `LLM` in benchmark tables when a specific model was used.

## 3. Data separation

### Teaching/development set

The existing `gold_reference_v0.1.jsonl` is a **development/teaching reference**. It has already influenced rules, examples, notebook design and validation utilities. It must therefore **not be reported as an unbiased final benchmark**.

This includes the current examples such as:

- Penrith / Pooley Bridge;
- synthetic Q/A journey;
- ambiguous Cambridge;
- historical polity;
- relational/non-cartographic space.

### Held-out benchmark

Create a separate `benchmark_holdout_v1.jsonl` only after:

- source/distribution rights are verified;
- the annotation policy is frozen;
- examples are selected before final model/rule/prompt tuning;
- the benchmark file is committed with a `frozen_at_commit` field;
- any later change increments the benchmark version and is documented.

Do not repeatedly inspect holdout errors and then tune the tested system while continuing to call the same set held-out.

## 4. Target composition

A practical conference benchmark should contain **30–50 short passages** rather than an artificially large weakly controlled set.

Suggested strata:

| Stratum | Purpose | Approx. share |
|---|---|---:|
| explicit named places | bounded recognition baseline | 20% |
| geo-nouns / locale expressions | beyond named entities | 15% |
| spatial relations / distance / direction | relation representation | 15% |
| ambiguity / duplicate place names | entity resolution | 10% |
| historical geography / spelling | temporal validity and normalization | 10% |
| explicit journeys | structured movement | 10% |
| context-dependent journeys / Q-A | inference and discourse context | 10% |
| non-cartographic/deictic/sense-of-place cases | representational ceiling | 10% |

These percentages are targets, not claims about the distribution of any source corpus.

## 5. Source policy

Prefer:

- public-domain historical texts with exact bibliographic/source citation;
- appropriately licensed public texts;
- instructor-authored synthetic examples for controlled stress tests.

Keep synthetic and source-derived results distinguishable in analysis. Do not present synthetic benchmark behaviour as evidence about a historical corpus.

Controlled-access Holocaust testimony transcripts must **not** be copied into the public benchmark. Research findings from controlled data can be discussed separately using permitted aggregate or cleared material.

## 6. Annotation and adjudication

Each held-out example should be annotated using `docs/sh2026/GOLD_ANNOTATION_GUIDE.md`.

Minimum process:

1. primary human annotation;
2. second-pass review against the written policy;
3. record unresolved scholarly disagreement rather than forcing consensus;
4. validate offsets/schema automatically;
5. freeze the adjudicated record before final system runs.

The term **reference annotation** is preferred to language implying interpretation-free ground truth.

## 7. Metrics

### 7.1 Span/recognition tasks

Report where applicable:

- precision;
- recall;
- F1;
- exact-span and, where analytically useful, overlap-span scores;
- per-label counts;
- error examples.

### 7.2 Representational reach

Before model inference, calculate the proportion of the broader reference ontology the method's output schema could represent.

This is an **ontology ceiling**, not empirical recall.

For example, an NER model may achieve high TOPONYM F1 while having no output category for distance, movement, deictic reference or sense-of-place description.

### 7.3 Entity resolution

Report:

- resolved rate;
- ambiguous rate;
- unresolved rate;
- candidate-list availability;
- anachronistic/unsafe-normalization errors found during human review.

Do not score a resolver as correct merely because it returned coordinates.

### 7.4 Structured journeys / LLM outputs

Before implementing journey precision/recall, freeze a journey-matching policy for origin/destination/evidence and partial field agreement.

Metrics already safe to report from the runtime schema include:

- evidence-grounded rate;
- unsupported evidence rate;
- contextual-inference rate;
- field-level inference rate;
- requires-review rate;
- schema/parse failure rate;
- missing-field rate;
- latency/token telemetry;
- estimated cost where a dated and reproducible cost calculation is available.

Do **not** infer or invent precision/recall values before the matching policy is frozen.

### 7.5 Human work

Distinguish:

- **review burden:** proportion of suggestions inspected;
- **correction burden:** proportion edited or rejected;
- number of edit events;
- fields most frequently corrected;
- optional review time if measured under a consistent protocol.

Accepting a model suggestion still consumes review effort but is not a correction.

## 8. Telemetry and cost

For every empirical run preserve, where available:

- task;
- backend;
- provider;
- exact model identifier;
- latency;
- input/output token estimates;
- success/error;
- estimated monetary cost;
- timestamp;
- package/Git commit;
- prompt/schema version for generative models.

If price data are incomplete or model billing cannot be reconstructed, leave cost `null`. Do not coerce missing cost to zero.

## 9. Repetition and non-determinism

Deterministic rules should normally be run once per frozen environment.

For stochastic/generative APIs, the final protocol should specify:

- temperature/decoding settings;
- number of repeated runs;
- whether results are scored per-run or after a defined adjudication rule.

If only one API run is feasible for the conference sprint, state that limitation explicitly and do not generalize stability claims beyond the observed run.

## 10. Benchmark output

Write tidy per-example rows compatible with `docs/sh2026/COMMON_SCHEMA.md` and `spatio_textual.benchmark`.

Core columns:

```text
example_id
method
backend
model
task
precision
recall
f1
coverage
unsupported_rate
ambiguous_rate
human_edits_required
latency_ms
cost_usd_est
notes
```

Additional audit fields may be included, but core fields should not change between the demo and keynote export.

Missing/not-applicable measures remain `null`, not zero.

## 11. Planned keynote figures

Only generate final figures after the holdout is frozen and the corresponding methods have actually been run.

Priority figures:

1. **Accuracy vs representational reach** — show that within-ontology accuracy and breadth are different quantities.
2. **Capability vs audit burden** — grounded evidence, inference and review rate alongside representational richness.
3. **Human work** — review burden vs correction burden by method/workflow.
4. **Latency/cost vs task richness** — only with measured values.
5. **Error taxonomy** — transparent rule failure, ontology ceiling, resolution ambiguity, unsupported generative inference.

Avoid a single overall winner score.

## 12. Release gates for benchmark claims

A result may be labelled **SH2026 benchmark result** only when:

- [ ] holdout examples are frozen;
- [ ] source rights/citations are verified;
- [ ] annotation validation passes;
- [ ] method configuration is recorded;
- [ ] run manifest is stored;
- [ ] output evidence/offset validation passes where applicable;
- [ ] results were not manually altered outside the recorded review mechanism;
- [ ] missing metrics remain null;
- [ ] figures can be regenerated from committed tidy result data;
- [ ] synthetic and historical/source-derived strata are distinguishable.

Until then, notebook outputs are **teaching/development demonstrations**, not final empirical claims.
