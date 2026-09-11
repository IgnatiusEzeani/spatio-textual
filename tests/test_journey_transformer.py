from __future__ import annotations

from collections import Counter

from benchmarks.sh2026.build_journey_dev_v1 import build_records
from spatio_textual.journey_transformer import (
    ID2LABEL,
    LABEL2ID,
    align_token_labels,
    development_record_splits,
    journey_training_instances,
    spans_from_bio_predictions,
)


def test_transformer_journey_split_is_record_level_and_stratified():
    records = build_records()
    splits = development_record_splits(records)
    assert Counter(splits.values()) == {"train": 144, "dev": 36}

    by_category = {}
    for record in records:
        category = record["source"]["development_category"]
        by_category.setdefault(category, Counter())[splits[record["example_id"]]] += 1
    assert all(counts == {"train": 12, "dev": 3} for counts in by_category.values())


def test_transformer_training_instances_are_separate_from_formal_holdout():
    records = build_records()
    rows = journey_training_instances(records)
    assert len(rows) == 195  # 135 positive journey instances + 60 hard negatives
    assert Counter(row["split"] for row in rows) == {"train": 156, "dev": 39}
    assert all(row["record_id"].startswith("journey_dev_") for row in rows)

    positives = [row for row in rows if row["roles"]]
    assert len(positives) == 135
    assert all(any(role["role"] == "TRIGGER" for role in row["roles"]) for row in positives)


def test_token_alignment_and_bio_collapse_round_trip():
    text = "Mira travelled from Aberdeen to Inverness"
    roles = [
        {"role": "TRIGGER", "start_char": 5, "end_char": 14, "text": "travelled"},
        {"role": "SOURCE", "start_char": 20, "end_char": 28, "text": "Aberdeen"},
        {"role": "DESTINATION", "start_char": 32, "end_char": 41, "text": "Inverness"},
    ]
    offsets = [(0, 0), (0, 4), (5, 14), (15, 19), (20, 28), (29, 31), (32, 41), (0, 0)]
    labels = align_token_labels(offsets, roles)
    assert ID2LABEL[labels[2]] == "B-TRIGGER"
    assert ID2LABEL[labels[4]] == "B-SOURCE"
    assert ID2LABEL[labels[6]] == "B-DESTINATION"

    predicted = spans_from_bio_predictions(text, offsets, [LABEL2ID["O"] if value == -100 else value for value in labels])
    assert [(item["role"], item["text"]) for item in predicted] == [
        ("TRIGGER", "travelled"),
        ("SOURCE", "Aberdeen"),
        ("DESTINATION", "Inverness"),
    ]
