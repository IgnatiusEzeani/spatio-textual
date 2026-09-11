from __future__ import annotations

from typing import Any, Protocol

SENTIMENT_LABELS = ("positive", "negative", "neutral", "mixed")
EMOTION_LABELS = (
    "fear",
    "sadness",
    "anger",
    "joy",
    "anxiety",
    "despair",
    "gratitude",
    "surprise",
)


class StructuredAffectClient(Protocol):
    provider: str
    model: str

    def complete_json(self, task: str, prompt: str, *, input_text: str | None = None) -> dict[str, Any]: ...


def affect_response_schema() -> dict[str, Any]:
    return {
        "type": "object",
        "additionalProperties": False,
        "properties": {
            "sentiment": {"type": "string", "enum": list(SENTIMENT_LABELS)},
            "emotion_labels": {
                "type": "array",
                "items": {"type": "string", "enum": list(EMOTION_LABELS)},
                "uniqueItems": True,
            },
            "evidence_quote": {
                "anyOf": [{"type": "string"}, {"type": "null"}],
            },
            "explicit_or_inferred": {
                "type": "string",
                "enum": ["explicit", "contextual_inference", "none"],
            },
            "confidence": {
                "anyOf": [
                    {"type": "number", "minimum": 0.0, "maximum": 1.0},
                    {"type": "null"},
                ]
            },
            "notes": {"type": "array", "items": {"type": "string"}},
        },
        "required": [
            "sentiment",
            "emotion_labels",
            "evidence_quote",
            "explicit_or_inferred",
            "confidence",
            "notes",
        ],
    }


def build_affect_prompt(text: str) -> str:
    labels = ", ".join(EMOTION_LABELS)
    return f"""You are annotating textual affect for a Spatial Humanities research benchmark.

Classify only what the supplied passage supports. A model label is an interpretation of textual evidence, not a direct measurement of a person's hidden psychological state.

Return exactly one JSON object matching the supplied schema.

Sentiment labels:
- positive
- negative
- neutral
- mixed

Emotion labels are multi-label and restricted to:
{labels}

Rules:
1. Keep sentiment and emotion separate. Surprise can be sentiment-neutral, and a passage can be mixed in sentiment.
2. Use an empty emotion_labels array when none of the permitted emotions is sufficiently supported.
3. Do not infer emotion merely from historical or domain terms such as place names, camp, ghetto, war, journey, or archive.
4. Respect negation and questions. A word such as 'fear' mentioned as a title, quotation label, or unanswered question is not automatically evidence that the passage expresses fear.
5. Reported affect counts only when the passage actually attributes the affect to a person or textual source, not when an emotion word is merely mentioned.
6. If affect is explicit, set explicit_or_inferred to 'explicit'. If it depends on contextual behaviour or implication, use 'contextual_inference'. If no emotion is assigned and the passage is affectively neutral, use 'none'.
7. evidence_quote must be a verbatim quotation from the passage that grounds the assigned affect. It may span the whole passage when multiple clauses are needed. Use null only when sentiment is neutral and emotion_labels is empty.
8. Do not invent text, events, motives, or feelings not supported by the passage.
9. confidence is a value from 0 to 1 reflecting confidence in this textual classification, not confidence about historical truth.
10. Keep notes short and use an empty list when no note is needed.

Passage:
{text}
"""


def _ground_quote(text: str, quote: str | None) -> tuple[int | None, int | None, str, list[str]]:
    if quote is None:
        return None, None, "missing", []
    if not isinstance(quote, str) or not quote:
        return None, None, "unsupported", ["Evidence quote is empty or invalid."]
    starts: list[int] = []
    offset = 0
    while True:
        idx = text.find(quote, offset)
        if idx < 0:
            break
        starts.append(idx)
        offset = idx + 1
    if len(starts) == 1:
        start = starts[0]
        return start, start + len(quote), "grounded", []
    if not starts:
        return None, None, "unsupported", ["Evidence quote was not found verbatim in the source text."]
    return None, None, "ambiguous", ["Evidence quote occurs multiple times in the source text."]


def extract_audited_affect(
    client: StructuredAffectClient,
    text: str,
    *,
    example_id: str,
) -> dict[str, Any]:
    prompt = build_affect_prompt(text)
    data = client.complete_json("affect_classification", prompt, input_text=text)
    telemetry = data.pop("telemetry", None)
    raw_response_text = data.pop("_raw_response_text", None)
    response_metadata = data.pop("_response_metadata", None)

    sentiment = str(data.get("sentiment") or "neutral").lower()
    emotions = [str(x).lower() for x in (data.get("emotion_labels") or [])]
    quote = data.get("evidence_quote")
    status = str(data.get("explicit_or_inferred") or "none")
    confidence = data.get("confidence")
    notes = [str(x) for x in (data.get("notes") or [])]

    start, end, grounding_status, review_notes = _ground_quote(text, quote)
    if (sentiment != "neutral" or emotions) and quote is None:
        review_notes.append("Non-neutral affect classification has no evidence quote.")
    if not emotions and status == "contextual_inference":
        review_notes.append("Contextual inference status was supplied without an emotion label.")
    if emotions and status == "none":
        review_notes.append("Emotion labels were supplied with explicit_or_inferred='none'.")
    if status == "contextual_inference":
        review_notes.append("Contextual affect inference requires scholarly review.")

    return {
        "example_id": example_id,
        "sentiment_label": sentiment,
        "emotion_labels": sorted(dict.fromkeys(emotions)),
        "evidence_quote": quote,
        "evidence_start_char": start,
        "evidence_end_char": end,
        "evidence_grounding_status": grounding_status,
        "explicit_or_inferred": status,
        "confidence": confidence,
        "notes": notes,
        "requires_review": bool(review_notes),
        "review_notes": review_notes,
        "telemetry": [] if telemetry is None else [telemetry],
        "raw_structured_response": data,
        "raw_response_text": raw_response_text,
        "response_metadata": response_metadata,
        "prompt": prompt,
    }
