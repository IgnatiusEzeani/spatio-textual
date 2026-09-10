# SH2026 source-derived external validation protocol

## Purpose

The primary SH2026 holdout is synthetic by design: it gives us controlled coverage of named places, geo-nouns, vague and relational space, historical geography, journeys, temporal context and contextual inference without distributing controlled testimony text.

A synthetic benchmark alone, however, cannot establish that a method generalises to historical writing. This protocol therefore defines a deliberately narrower **external validation check** using the public Corpus of Lake District Writing (CLDW).

The external check answers one question only:

> Do the named-place recognition findings from the synthetic benchmark remain plausible on independently sourced historical Lake District writing?

It is not a second development set and must not be used to tune the gazetteer, rule patterns, label mappings or model prompts before reporting the external result.

## Upstream source and provenance

The source is `UCREL/LakeDistrictCorpus` at commit:

`9042811cf590f694f9b635c4bc656ed4f81ca422`

The CLDW repository describes 80 manually digitised/annotated texts (more than 1.5 million tokens) and a 28-text hand-checked gold-standard subcorpus of approximately 242,000 tokens. Gold place names are marked with `<cdplace>`.

The upstream repository states a **CC BY-NC-SA 4.0** licence. Any distributed derivative excerpt must therefore preserve appropriate attribution/licensing. To minimise unnecessary redistribution, the preferred SH2026 workflow reconstructs the validation passages from the pinned upstream repository at run time and stores them as benchmark artefacts with provenance.

Dataset reference:

Rayson, P., Reinhold, A., Butler, J., Donaldson, C. E., Gregory, I. N., & Taylor, J. E. (2017). *A deeply annotated testbed for geographical text analysis: The Corpus of Lake District Writing*. GeoHumanities'17, ACM SIGSPATIAL.

## Source selection frozen before model execution

The exact ten source files are recorded in:

`benchmarks/sh2026/cldw_external_manifest_v1.json`

They provide a chronological spread within the already curated CLDW gold-standard subcorpus. This is a purposive source-derived validation sample, not a claim of random sampling or statistical representativeness of all historical writing.

The file selection was frozen before running the SH2026 methods on these passages. Selection must not be changed because a method performs badly on a chosen text.

## Deterministic passage selection

For each fixed source file:

1. Read paragraphs in source order.
2. Select the first paragraph containing at least two gold `<cdplace>` annotations and between 80 and 1200 normalized plain-text characters.
3. If no paragraph meets that condition, select the first paragraph in the same length range containing at least one `<cdplace>` annotation.
4. Preserve the paragraph's normalized plain text and derive exact character offsets for every `<cdplace>` mention from the markup.
5. Record upstream repository, commit, path, blob SHA, passage ordinal and extraction-rule version.

The builder must fail loudly if a pinned file is absent, a source blob differs from the manifest, no eligible passage exists, or a derived gold span does not reproduce the exact source substring.

## Evaluation scope

This external check is deliberately **TOPONYM recognition only**. It may compare:

- contextual spaCy NER;
- the same spaCy model plus frozen project resources;
- the revision-pinned Hugging Face NER condition;
- the deterministic/gazetteer condition only where its declared toponym support makes the comparison interpretable.

Precision, recall and F1 must use the same CLDW `<cdplace>`-derived reference denominator for methods presented side by side as named-place recognition systems.

This check must **not** be used to claim external validation for geo-nouns, qualitative relations, affect, journey extraction or LLM interpretation. Those require different annotations and evidence.

## Separation from the synthetic holdout

The two evaluation layers serve different purposes:

- **Synthetic frozen holdout:** controlled representational breadth and auditability across the richer SH2026 ontology.
- **CLDW external validation:** source-derived historical-language check for named-place recognition.

Results must be reported separately before any combined interpretation. A strong result on one cannot erase limitations on the other.

## Anti-contamination rules

After the external passages are generated:

- do not add their missed names to the teaching gazetteer before the reported run;
- do not edit rule patterns in response to their errors;
- do not change label harmonisation because of their predictions;
- do not replace difficult passages;
- do not select only the best-performing source files;
- preserve the exact generated dataset checksum with every result artefact.

Any later tuning creates a **post-validation development condition** and must be labelled as such.

## Reporting language

Appropriate:

> On a ten-passage source-derived CLDW check frozen before model execution, the named-place recognition pattern was ...

Avoid:

> The model is validated on historical texts.

The latter is too broad for this sample and task.

## Release gate

The external-validation result becomes keynote-ready only when all of the following are true: the builder is deterministic; upstream provenance and licence are included; generated gold offsets validate; a checksum is frozen; all compared NER conditions use a clearly stated denominator; environment/model revisions are recorded; and no post-hoc tuning has occurred.
