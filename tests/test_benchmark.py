from spatio_textual.benchmark import (
    aggregate_comparison_rows,
    journey_audit_metrics,
    journey_comparison_row,
    span_comparison_row,
    summarize_telemetry,
)


def test_summarize_telemetry_preserves_missing_cost():
    summary = summarize_telemetry([
        {"latency_ms": 10.0, "input_tokens_est": 4, "output_tokens_est": 2, "cost_usd_est": None, "success": True},
        {"latency_ms": 20.0, "input_tokens_est": 5, "output_tokens_est": 3, "cost_usd_est": None, "success": True},
    ])
    assert summary["latency_ms_total"] == 30.0
    assert summary["latency_ms_mean"] == 15.0
    assert summary["cost_usd_est_total"] is None
    assert summary["success_rate"] == 1.0


def test_span_comparison_row_keeps_accuracy_and_coverage_distinct():
    reference = [
        {"text": "London", "label": "TOPONYM", "start_char": 0, "end_char": 6},
        {"text": "near", "label": "SPATIAL_RELATION", "start_char": 7, "end_char": 11},
    ]
    predicted = [{"text": "London", "label": "TOPONYM", "start_char": 0, "end_char": 6}]
    row = span_comparison_row(
        example_id="ex1",
        method="ner",
        backend="spacy",
        model="demo",
        predicted=predicted,
        reference=[reference[0]],
        supported_reference_total=1,
        reference_total=2,
    )
    assert row["precision"] == 1.0
    assert row["recall"] == 1.0
    assert row["f1"] == 1.0
    assert row["coverage"] == 0.5


def test_journey_audit_metrics_count_grounding_inference_and_review():
    journeys = [
        {
            "evidence_grounded": True,
            "requires_review": True,
            "explicit_or_inferred": {
                "start_location": "contextual_inference",
                "end_location": "explicit",
                "transport_mode": "missing",
            },
        },
        {
            "evidence_grounded": False,
            "requires_review": True,
            "explicit_or_inferred": {
                "start_location": "explicit",
                "end_location": "explicit",
            },
        },
    ]
    result = journey_audit_metrics(journeys)
    assert result["evidence_grounded_rate"] == 0.5
    assert result["unsupported_rate"] == 0.5
    assert result["requires_review_rate"] == 1.0
    assert result["contextual_inference_rate"] == 0.5


def test_journey_comparison_row_does_not_invent_precision_recall():
    row = journey_comparison_row(
        example_id="ex1",
        method="llm",
        backend="llm",
        model="demo",
        journeys=[{
            "evidence_grounded": True,
            "requires_review": False,
            "explicit_or_inferred": {"start_location": "explicit", "end_location": "explicit"},
        }],
        telemetry=[{"latency_ms": 12.0, "cost_usd_est": 0.001, "success": True}],
    )
    assert row["precision"] is None
    assert row["recall"] is None
    assert row["f1"] is None
    assert row["unsupported_rate"] == 0.0
    assert row["latency_ms"] == 12.0


def test_aggregate_comparison_rows_ignores_null_numeric_values():
    rows = [
        {"method": "rules", "task": "spatial", "backend": "rules", "model": "r1", "f1": 0.8, "coverage": 0.5},
        {"method": "rules", "task": "spatial", "backend": "rules", "model": "r1", "f1": 1.0, "coverage": None},
    ]
    agg = aggregate_comparison_rows(rows)[0]
    assert agg["examples"] == 2
    assert agg["f1"] == 0.9
    assert agg["coverage"] == 0.5
