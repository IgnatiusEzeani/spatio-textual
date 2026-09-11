from __future__ import annotations

import hashlib
from collections import Counter

from benchmarks.sh2026.build_journey_dev_v1 import EXPECTED_SHA256, build_records, serialize
from spatio_textual.gold import assert_valid_gold


def test_journey_dev_v1_is_deterministic_and_valid():
    records = build_records()
    assert len(records) == 180
    assert sum(len(record.get("journeys", [])) for record in records) == 135
    assert_valid_gold(records)

    digest = hashlib.sha256(serialize(records)).hexdigest()
    assert digest == EXPECTED_SHA256

    categories = Counter(record["source"]["development_category"] for record in records)
    assert len(categories) == 12
    assert set(categories.values()) == {15}


def test_journey_dev_v1_keeps_holdout_separate():
    records = build_records()
    assert all(record["source"]["distribution_status"] == "public_safe_synthetic_development" for record in records)
    assert all(record["example_id"].startswith("journey_dev_") for record in records)
