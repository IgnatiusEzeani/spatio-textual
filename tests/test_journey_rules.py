from __future__ import annotations

import pytest

from spatio_textual.journey_rules import RuleDependencyJourneyExtractor


@pytest.fixture(scope="module")
def extractor():
    return RuleDependencyJourneyExtractor("en_core_web_sm")


def test_rule_dependency_extracts_explicit_journey(extractor):
    text = "On Tuesday, Mira travelled from Aberdeen to Inverness by train for an archive visit."
    result = extractor.extract(text, file_id="x1")
    assert len(result["journeys"]) == 1
    journey = result["journeys"][0]
    assert journey["start_location"] == "Aberdeen"
    assert journey["end_location"] == "Inverness"
    assert journey["transport_mode"] == "train"
    assert journey["date"] == "On Tuesday"
    assert journey["journey_reason"] == "for an archive visit"
    assert journey["evidence_quote"] == text
    assert text[journey["evidence_start_char"]:journey["evidence_end_char"]] == journey["evidence_quote"]


def test_rule_dependency_inherits_origin_only_when_bounded(extractor):
    text = "Mira stayed in Aberdeen for several days. The following morning, from there, Mira travelled to Inverness by coach."
    result = extractor.extract(text, file_id="x2")
    assert len(result["journeys"]) == 1
    journey = result["journeys"][0]
    assert journey["start_location"] == "Aberdeen"
    assert journey["end_location"] == "Inverness"
    assert journey["transport_mode"] == "bus"
    assert journey["date"] == "The following morning"
    assert journey["explicit_or_inferred"]["start_location"] == "contextual_inference"
    assert journey["requires_review"] is True
    assert journey["evidence_quote"] == text


def test_rule_dependency_rejects_cancelled_and_negated_travel(extractor):
    cancelled = "Mira planned to travel from Aberdeen to Inverness, but the trip was cancelled."
    negated = "Mira never went from Aberdeen to Inverness; the route appears only in a letter."
    assert extractor.extract(cancelled, file_id="n1")["journeys"] == []
    assert extractor.extract(negated, file_id="n2")["journeys"] == []


def test_rule_dependency_keeps_single_endpoint_boundaries_clean(extractor):
    arrival = "Late that evening, Mira arrived in Inverness and checked into a hostel."
    result = extractor.extract(arrival, file_id="x3")
    assert len(result["journeys"]) == 1
    journey = result["journeys"][0]
    assert journey["start_location"] is None
    assert journey["end_location"] == "Inverness"
    assert journey["date"] == "Late that evening"

    departure = "At sunrise, Mira left Aberdeen without recording the destination."
    result = extractor.extract(departure, file_id="x4")
    assert len(result["journeys"]) == 1
    journey = result["journeys"][0]
    assert journey["start_location"] == "Aberdeen"
    assert journey["end_location"] is None
    assert journey["date"] == "At sunrise"
    assert journey["explicit_or_inferred"]["end_location"] == "missing"
