from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

import pandas as pd

from spatio_textual.benchmark import aggregate_comparison_rows, span_comparison_row
from spatio_textual.evaluation import (
    harmonize_ner_entities,
    reference_spans_for_ner,
    supported_reference_fraction,
)
from spatio_textual.gold import load_gold_jsonl
from spatio_textual.rules import RuleGazetteerAnnotator, filter_supported_gold_labels
from spatio_textual.utils import Annotator


def _parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(
        description="Run reproducible SH2026 span-method comparisons. Final keynote claims require a frozen holdout."
    )
    p.add_argument("input", type=Path, help="SH2026 reference JSONL")
    p.add_argument("--out-dir", type=Path, default=Path("sh2026_outputs/benchmark"))
    p.add_argument("--methods", default="rules", help="Comma-separated: rules,spacy")
    p.add_argument("--gazetteer", type=Path, default=Path("tutorials/sh2026/data/teaching_gazetteer.csv"))
    p.add_argument("--spacy-model", default="en_core_web_sm")
    p.add_argument(
        "--benchmark-mode",
        action="store_true",
        help="Refuse provisional/development records and require --frozen-at-commit.",
    )
    p.add_argument("--frozen-at-commit", default=None)
    return p.parse_args()


def _assert_benchmark_ready(records: list[dict[str, Any]], frozen_at_commit: str | None) -> None:
    if not frozen_at_commit:
        raise SystemExit("--benchmark-mode requires --frozen-at-commit so results remain tied to a frozen data revision.")
    bad = []
    for rec in records:
        status = str(rec.get("reference_status") or "").lower()
        distribution = str((rec.get("source") or {}).get("distribution_status") or "").lower()
        if "provisional" in status or "pending" in distribution:
            bad.append(rec.get("example_id"))
    if bad:
        raise SystemExit(
            "Benchmark mode refused provisional/pending records: " + ", ".join(str(x) for x in bad)
        )


def _strict_spacy_model(model_name: str):
    """Load the requested model without the package's tutorial fallback."""
    import spacy

    try:
        return spacy.load(model_name)
    except Exception as exc:
        raise SystemExit(
            f"Could not load spaCy model {model_name!r}. Benchmark mode must not silently fall back to a blank pipeline: {exc}"
        ) from exc


def run_rules(record: dict[str, Any], gazetteer: Path) -> dict[str, Any]:
    ann = RuleGazetteerAnnotator(gazetteer_path=gazetteer, link_places=False)
    result = ann.annotate(record["text"])
    reference = filter_supported_gold_labels(record.get("spans", []))
    reach = supported_reference_fraction(record, {span["label"] for span in reference})
    return span_comparison_row(
        example_id=record["example_id"],
        method="rule_gazetteer",
        backend="rules",
        model="entity_ruler+regex",
        predicted=result.get("spans", []),
        reference=reference,
        task="spatial_annotation_supported_labels",
        match="exact",
        supported_reference_total=reach["ontology_supported"],
        reference_total=reach["reference_total"],
        telemetry=result.get("telemetry", []),
        notes="Accuracy denominator contains only labels the deterministic baseline is designed to predict; coverage reports its broader ontology ceiling.",
    )


def build_spacy_runner(model_name: str):
    nlp = _strict_spacy_model(model_name)
    # Important experimental control: do not add project EntityRuler resources to
    # the contextual-only condition.
    return Annotator(nlp=nlp, model_name=model_name, link_places=False)


def run_spacy(record: dict[str, Any], annotator: Annotator, model_name: str) -> dict[str, Any]:
    result = annotator.annotate(record["text"], include_entities=True, include_verbs=False, include_events=False)
    predicted = harmonize_ner_entities(result.get("entities", []))
    reference = reference_spans_for_ner(record, include_geonouns=False, include_temporal=False)
    reach = supported_reference_fraction(record, {"TOPONYM"})
    return span_comparison_row(
        example_id=record["example_id"],
        method="contextual_ner",
        backend="spacy",
        model=model_name,
        predicted=predicted,
        reference=reference,
        task="toponym_recognition",
        match="exact",
        supported_reference_total=reach["ontology_supported"],
        reference_total=reach["reference_total"],
        telemetry=result.get("telemetry", []),
        notes="Contextual spaCy condition without project EntityRuler. Accuracy is TOPONYM-only; coverage is reported separately.",
    )


def main() -> None:
    args = _parse_args()
    records = load_gold_jsonl(args.input)
    if args.benchmark_mode:
        _assert_benchmark_ready(records, args.frozen_at_commit)

    methods = {item.strip().lower() for item in args.methods.split(",") if item.strip()}
    unknown = methods - {"rules", "spacy"}
    if unknown:
        raise SystemExit(f"Unsupported methods: {sorted(unknown)}")

    spacy_runner = build_spacy_runner(args.spacy_model) if "spacy" in methods else None
    rows: list[dict[str, Any]] = []
    for record in records:
        if "rules" in methods:
            rows.append(run_rules(record, args.gazetteer))
        if spacy_runner is not None:
            rows.append(run_spacy(record, spacy_runner, args.spacy_model))

    args.out_dir.mkdir(parents=True, exist_ok=True)
    per_example_jsonl = args.out_dir / "comparison_rows.jsonl"
    with per_example_jsonl.open("w", encoding="utf-8") as fh:
        for row in rows:
            fh.write(json.dumps(row, ensure_ascii=False) + "\n")

    # Tidy CSV intentionally drops nested telemetry_summary; the JSONL remains the
    # richer audit object.
    core_columns = [
        "example_id", "method", "backend", "model", "task", "precision", "recall", "f1",
        "coverage", "unsupported_rate", "ambiguous_rate", "human_edits_required", "latency_ms",
        "cost_usd_est", "notes",
    ]
    pd.DataFrame(rows).reindex(columns=core_columns).to_csv(args.out_dir / "comparison_rows.csv", index=False)

    summary = aggregate_comparison_rows(rows)
    (args.out_dir / "comparison_summary.json").write_text(
        json.dumps(
            {
                "run_mode": "benchmark" if args.benchmark_mode else "development",
                "frozen_at_commit": args.frozen_at_commit,
                "input": str(args.input),
                "methods": sorted(methods),
                "summary": summary,
            },
            ensure_ascii=False,
            indent=2,
        ),
        encoding="utf-8",
    )
    pd.DataFrame(summary).to_csv(args.out_dir / "comparison_summary.csv", index=False)

    print(f"Wrote {len(rows)} comparison rows to {args.out_dir}")
    if not args.benchmark_mode:
        print("DEVELOPMENT MODE: outputs are diagnostic and must not be reported as final SH2026 benchmark results.")


if __name__ == "__main__":
    main()
