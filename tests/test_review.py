from spatio_textual.review import apply_human_review, human_correction_burden


def _record():
    return {
        "journeyId": "ex-j-1",
        "end_location": "London",
        "requires_review": True,
        "human_status": "unreviewed",
        "human_edits": [],
    }


def test_apply_accept_preserves_record_and_audit_event():
    original = _record()
    reviewed = apply_human_review(
        original,
        action="accept",
        reason="human_flag",
        timestamp="2026-09-08T12:00:00+00:00",
    )
    assert original["human_status"] == "unreviewed"
    assert reviewed["human_status"] == "accepted"
    assert reviewed["requires_review"] is False
    assert reviewed["human_edits"][0]["action"] == "accept"


def test_apply_edit_records_old_and_new_values():
    reviewed = apply_human_review(
        _record(),
        action="edit",
        field="end_location",
        new_value="London, England",
        reason="disambiguation",
        timestamp="2026-09-08T12:00:00+00:00",
    )
    assert reviewed["end_location"] == "London, England"
    assert reviewed["human_status"] == "edited"
    event = reviewed["human_edits"][0]
    assert event["old_value"] == "London"
    assert event["new_value"] == "London, England"
    assert event["field"] == "end_location"


def test_apply_reject_sets_status():
    reviewed = apply_human_review(
        _record(),
        action="reject",
        reason="unsupported_llm_field",
        timestamp="2026-09-08T12:00:00+00:00",
    )
    assert reviewed["human_status"] == "rejected"
    assert reviewed["requires_review"] is False


def test_correction_burden_distinguishes_review_from_correction():
    accepted = apply_human_review(
        _record(), action="accept", reason="human_flag", timestamp="2026-09-08T12:00:00+00:00"
    )
    edited = apply_human_review(
        _record(), action="edit", field="end_location", new_value="London, England",
        reason="disambiguation", timestamp="2026-09-08T12:00:00+00:00"
    )
    rejected = apply_human_review(
        _record(), action="reject", reason="unsupported_llm_field", timestamp="2026-09-08T12:00:00+00:00"
    )
    unreviewed = _record()

    summary = human_correction_burden([accepted, edited, rejected, unreviewed])
    assert summary["records_total"] == 4
    assert summary["records_reviewed"] == 3
    assert summary["records_corrected"] == 2
    assert summary["review_rate"] == 0.75
    assert summary["correction_rate"] == 0.5
    assert summary["human_edit_events"] == 3
    assert summary["edited_fields"] == ["end_location"]
