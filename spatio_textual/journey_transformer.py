from __future__ import annotations

import re
import time
from collections import Counter
from typing import Any, Sequence

import spacy

ROLE_NAMES = ("TRIGGER", "SOURCE", "DESTINATION", "TRANSPORT", "TIME", "REASON")
LABELS = ("O",) + tuple(label for role in ROLE_NAMES for label in (f"B-{role}", f"I-{role}"))
LABEL2ID = {label: idx for idx, label in enumerate(LABELS)}
ID2LABEL = {idx: label for label, idx in LABEL2ID.items()}

FIELD_TO_ROLE = {
    "start_location": "SOURCE",
    "end_location": "DESTINATION",
    "transport_mode": "TRANSPORT",
    "date": "TIME",
    "journey_reason": "REASON",
}

TRIGGER_RE = re.compile(
    r"\b(?:arrived|arrive|continued|continue|crossed|cross|cycled|cycle|departed|depart|drove|drive|"
    r"escaped|escape|fled|flee|flew|fly|went|go|journeyed|journey|left|leave|moved|move|reached|reach|"
    r"relocated|relocate|returned|return|rode|ride|sailed|sail|settled|settle|took|take|travelled|traveled|"
    r"travel|walked|walk)\b",
    re.I,
)
TRANSPORT_SURFACES = {
    "train": ("train", "rail"),
    "bus": ("bus", "coach"),
    "car": ("car", "taxi"),
    "ferry": ("ferry",),
    "boat": ("boat",),
    "ship": ("ship",),
    "air": ("plane", "flight", "air"),
    "bicycle": ("bicycle", "bike"),
    "foot": ("foot",),
    "lorry": ("lorry", "truck"),
}
TRANSPORT_ALIASES = {
    surface.casefold(): normalized
    for normalized, surfaces in TRANSPORT_SURFACES.items()
    for surface in surfaces
}
IMPLIED_TRANSPORT = {
    "walked": "foot", "walk": "foot",
    "cycled": "bicycle", "cycle": "bicycle",
    "drove": "car", "drive": "car",
    "flew": "air", "fly": "air",
    "sailed": "ship", "sail": "ship",
}


def development_record_splits(records: Sequence[dict[str, Any]]) -> dict[str, str]:
    """Return a deterministic 80/20 split stratified by development category.

    Every fifth item within each category is held out for development evaluation.
    Splitting happens at source-record level, so multi-journey passages cannot
    leak one journey into train and another into development evaluation.
    """
    counts: Counter[str] = Counter()
    out: dict[str, str] = {}
    for record in records:
        category = str((record.get("source") or {}).get("development_category") or "uncategorized")
        ordinal = counts[category]
        counts[category] += 1
        out[str(record["example_id"])] = "dev" if ordinal % 5 == 4 else "train"
    return out


def _find_literal(text: str, value: str) -> tuple[int, int] | None:
    start = text.find(value)
    if start >= 0:
        return start, start + len(value)
    start = text.casefold().find(value.casefold())
    if start >= 0:
        return start, start + len(value)
    return None


def _find_transport(text: str, normalized: str) -> tuple[int, int] | None:
    for surface in TRANSPORT_SURFACES.get(normalized.casefold(), (normalized,)):
        match = re.search(rf"\b{re.escape(surface)}\b", text, re.I)
        if match:
            return match.start(), match.end()
    return None


def _find_trigger(text: str) -> tuple[int, int] | None:
    matches = list(TRIGGER_RE.finditer(text))
    if not matches:
        return None
    match = matches[-1]
    return match.start(), match.end()


def journey_training_instances(records: Sequence[dict[str, Any]]) -> list[dict[str, Any]]:
    """Project structured development references into token-role instances."""
    splits = development_record_splits(records)
    instances: list[dict[str, Any]] = []
    for record in records:
        example_id = str(record["example_id"])
        category = str((record.get("source") or {}).get("development_category") or "uncategorized")
        journeys = record.get("journeys", []) or []
        if not journeys:
            instances.append({
                "instance_id": f"{example_id}_negative",
                "record_id": example_id,
                "category": category,
                "split": splits[example_id],
                "text": str(record["text"]),
                "roles": [],
            })
            continue

        for journey in journeys:
            evidence = str(journey["evidence_quote"])
            roles: list[dict[str, Any]] = []
            trigger = _find_trigger(evidence)
            if trigger:
                roles.append({"role": "TRIGGER", "start_char": trigger[0], "end_char": trigger[1], "text": evidence[trigger[0]:trigger[1]]})

            statuses = journey.get("explicit_or_inferred") or {}
            for field, role in FIELD_TO_ROLE.items():
                value = journey.get(field)
                if value in (None, ""):
                    continue
                span = None
                if field == "transport_mode":
                    if statuses.get(field) == "explicit":
                        span = _find_transport(evidence, str(value))
                else:
                    span = _find_literal(evidence, str(value))
                if span:
                    roles.append({"role": role, "start_char": span[0], "end_char": span[1], "text": evidence[span[0]:span[1]]})

            roles.sort(key=lambda item: (item["start_char"], item["end_char"], item["role"]))
            instances.append({
                "instance_id": str(journey["journeyId"]),
                "record_id": example_id,
                "category": category,
                "split": splits[example_id],
                "text": evidence,
                "roles": roles,
            })
    return instances


def align_token_labels(offsets: Sequence[Sequence[int]], roles: Sequence[dict[str, Any]]) -> list[int]:
    """Align character-role annotations to a fast-tokenizer offset mapping."""
    labels: list[int] = []
    for start, end in offsets:
        if start == end == 0:
            labels.append(-100)
            continue
        assigned = "O"
        for role in roles:
            a = int(role["start_char"])
            b = int(role["end_char"])
            if end <= a or start >= b:
                continue
            prefix = "B" if start <= a < end or start == a else "I"
            assigned = f"{prefix}-{role['role']}"
            break
        labels.append(LABEL2ID[assigned])
    return labels


def spans_from_bio_predictions(
    text: str,
    offsets: Sequence[Sequence[int]],
    label_ids: Sequence[int],
) -> list[dict[str, Any]]:
    """Collapse token BIO predictions into grounded character spans."""
    spans: list[dict[str, Any]] = []
    current: dict[str, Any] | None = None
    for (start, end), label_id in zip(offsets, label_ids):
        if start == end == 0:
            continue
        label = ID2LABEL.get(int(label_id), "O")
        if label == "O":
            if current is not None:
                current["text"] = text[current["start_char"]:current["end_char"]]
                spans.append(current)
                current = None
            continue
        prefix, role = label.split("-", 1)
        if current is None or prefix == "B" or current["role"] != role or start > current["end_char"] + 1:
            if current is not None:
                current["text"] = text[current["start_char"]:current["end_char"]]
                spans.append(current)
            current = {"role": role, "start_char": int(start), "end_char": int(end)}
        else:
            current["end_char"] = int(end)
    if current is not None:
        current["text"] = text[current["start_char"]:current["end_char"]]
        spans.append(current)
    return spans


def _pick_role(spans: Sequence[dict[str, Any]], role: str, trigger: dict[str, Any], *, prefer_after: bool = False) -> dict[str, Any] | None:
    candidates = [span for span in spans if span.get("role") == role]
    if not candidates:
        return None
    t = (int(trigger["start_char"]) + int(trigger["end_char"])) / 2.0
    if prefer_after:
        after = [span for span in candidates if int(span["start_char"]) >= int(trigger["end_char"])]
        if after:
            candidates = after
    return min(candidates, key=lambda span: abs(((int(span["start_char"]) + int(span["end_char"])) / 2.0) - t))


class TransformerJourneyExtractor:
    """Non-generative token-classification journey event extractor."""

    def __init__(self, model_path: str, *, max_length: int = 256) -> None:
        try:
            import torch
            from transformers import AutoModelForTokenClassification, AutoTokenizer
        except Exception as exc:  # pragma: no cover
            raise RuntimeError("Transformer journey extraction requires the `transformers` optional dependency") from exc
        self.torch = torch
        self.tokenizer = AutoTokenizer.from_pretrained(model_path, use_fast=True)
        self.model = AutoModelForTokenClassification.from_pretrained(model_path)
        self.model.eval()
        self.max_length = max_length
        self.model_identifier = str(model_path)
        self.sentencizer = spacy.blank("en")
        self.sentencizer.add_pipe("sentencizer")

    def _predict_spans(self, text: str) -> list[dict[str, Any]]:
        encoded = self.tokenizer(
            text,
            return_offsets_mapping=True,
            truncation=True,
            max_length=self.max_length,
            return_tensors="pt",
        )
        offsets = encoded.pop("offset_mapping")[0].tolist()
        with self.torch.no_grad():
            logits = self.model(**encoded).logits[0]
        label_ids = logits.argmax(dim=-1).tolist()
        return spans_from_bio_predictions(text, offsets, label_ids)

    def extract(self, text: str, *, file_id: str = "document") -> dict[str, Any]:
        started = time.perf_counter()
        source = text or ""
        doc = self.sentencizer(source)
        sentences = list(doc.sents)
        journeys: list[dict[str, Any]] = []

        for index, sent in enumerate(sentences):
            window_start = sentences[index - 1].start_char if index > 0 else sent.start_char
            window_end = sent.end_char
            window = source[window_start:window_end]
            current_start = sent.start_char - window_start
            current_end = sent.end_char - window_start
            spans = self._predict_spans(window)
            triggers = [
                span for span in spans
                if span.get("role") == "TRIGGER" and int(span["start_char"]) >= current_start and int(span["end_char"]) <= current_end
            ]
            for trigger in triggers:
                source_span = _pick_role(spans, "SOURCE", trigger)
                destination_span = _pick_role(spans, "DESTINATION", trigger, prefer_after=True)
                transport_span = _pick_role(spans, "TRANSPORT", trigger)
                time_span = _pick_role(spans, "TIME", trigger)
                reason_span = _pick_role(spans, "REASON", trigger)
                if source_span is None and destination_span is None:
                    continue

                def value(span: dict[str, Any] | None) -> str | None:
                    return str(span["text"]) if span is not None else None

                transport = value(transport_span)
                transport_status = "explicit" if transport else "missing"
                if transport:
                    transport = TRANSPORT_ALIASES.get(transport.casefold(), transport.casefold())
                else:
                    implied = IMPLIED_TRANSPORT.get(str(trigger["text"]).casefold())
                    if implied:
                        transport = implied
                        transport_status = "contextual_inference"

                def span_status(span: dict[str, Any] | None) -> str:
                    if span is None:
                        return "missing"
                    return "explicit" if int(span["start_char"]) >= current_start else "contextual_inference"

                statuses = {
                    "start_location": span_status(source_span),
                    "end_location": span_status(destination_span),
                    "transport_mode": transport_status,
                    "date": span_status(time_span),
                    "journey_reason": span_status(reason_span),
                }
                contextual = any(status == "contextual_inference" for status in statuses.values())
                uses_previous = any(
                    span is not None and int(span["start_char"]) < current_start
                    for span in (source_span, destination_span, transport_span, time_span, reason_span)
                )
                evidence_start = window_start if uses_previous else sent.start_char
                evidence_end = sent.end_char
                evidence = source[evidence_start:evidence_end]

                journeys.append({
                    "journeyId": f"{file_id}_transformer_j{len(journeys) + 1}",
                    "fileId": file_id,
                    "start_location": value(source_span),
                    "end_location": value(destination_span),
                    "transport_mode": transport,
                    "date": value(time_span),
                    "journey_reason": value(reason_span),
                    "trigger": str(trigger["text"]),
                    "evidence_quote": evidence,
                    "evidence_start_char": evidence_start,
                    "evidence_end_char": evidence_end,
                    "evidence_grounded": source[evidence_start:evidence_end] == evidence,
                    "explicit_or_inferred": statuses,
                    "requires_review": contextual,
                    "review_notes": ["Contains transformer-derived contextual inference."] if contextual else [],
                    "source": "transformer_token_event_v1",
                })

        latency_ms = round((time.perf_counter() - started) * 1000, 3)
        return {
            "journeys": journeys,
            "requires_review": any(item.get("requires_review") for item in journeys),
            "review_notes": ["At least one journey contains contextual inference."] if any(item.get("requires_review") for item in journeys) else [],
            "telemetry": [{
                "task": "journey_extraction",
                "backend": "transformer_token_classification",
                "provider": "local",
                "model": self.model_identifier,
                "latency_ms": latency_ms,
                "input_chars": len(source),
                "input_tokens_est": None,
                "output_tokens_est": None,
                "cost_usd_est": 0.0,
                "success": True,
                "error": None,
            }],
        }
