from __future__ import annotations

import html
import json
import os
import subprocess
from pathlib import Path
from typing import Any

import pandas as pd
import streamlit as st

from spatio_textual.benchmark import summarize_telemetry
from spatio_textual.emotion import EmotionAnalyzer
from spatio_textual.evaluation import harmonize_ner_entities
from spatio_textual.formats import entities_to_conll
from spatio_textual.journeys import JourneyExtractor
from spatio_textual.llm import LLMClient
from spatio_textual.model_registry import EMOTION_MODELS, LLM_PROVIDERS, NER_MODELS, SENTIMENT_MODELS, parse_ner_model
from spatio_textual.provenance import build_run_manifest
from spatio_textual.qa import segment_testimony
from spatio_textual.review import apply_human_review
from spatio_textual.rules import RuleGazetteerAnnotator
from spatio_textual.sentiment import SentimentAnalyzer
from spatio_textual.transformer_ner import HFNERAnnotator
from spatio_textual.utils import Annotator, load_spacy_model, split_into_segments
from spatio_textual.viz import build_cooccurrence, journeys_to_geojson, to_geojson

st.set_page_config(
    page_title="spatio-textual | Spatial Humanities 2026",
    page_icon="🗺️",
    layout="wide",
    initial_sidebar_state="expanded",
)

ROOT = Path(__file__).resolve().parent
EXAMPLES_PATH = ROOT / "tutorials" / "sh2026" / "data" / "examples.json"
TEACHING_GAZETTEER = ROOT / "tutorials" / "sh2026" / "data" / "teaching_gazetteer.csv"


@st.cache_data
def load_examples() -> list[dict[str, Any]]:
    if not EXAMPLES_PATH.exists():
        return []
    return json.loads(EXAMPLES_PATH.read_text(encoding="utf-8"))


@st.cache_resource
def cached_spacy(model_name: str, resources_dir: str, add_project_resources: bool = True):
    return load_spacy_model(model_name, resources_dir=resources_dir, add_entity_ruler=add_project_resources)


def current_git_commit() -> str | None:
    try:
        proc = subprocess.run(
            ["git", "rev-parse", "HEAD"], cwd=ROOT, capture_output=True, text=True, check=True, timeout=5
        )
        return proc.stdout.strip() or None
    except Exception:
        return None


def _init_state() -> None:
    defaults = {
        "sh_source_text": "",
        "sh_source_id": "pasted_text",
        "sh_source_note": None,
        "sh_records": [],
        "sh_journeys": [],
        "sh_journey_audit": [],
        "sh_source_items": [],
        "sh_last_config": {},
        "sh_compare": None,
    }
    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value


_init_state()
EXAMPLES = load_examples()


def _safe_example_options() -> list[dict[str, Any]]:
    # The CLDW teaching item remains available but is visibly marked as pending
    # exact citation verification. Synthetic items are immediately distributable.
    return EXAMPLES


def _use_example(example: dict[str, Any]) -> None:
    st.session_state["sh_source_text"] = example.get("text", "")
    st.session_state["sh_source_id"] = example.get("id", "example")
    st.session_state["sh_source_note"] = example.get("source_note")


def _entity_rows(records: list[dict[str, Any]]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for rec_index, record in enumerate(records):
        for ent_index, entity in enumerate(record.get("entities") or []):
            rows.append({
                "record_index": rec_index,
                "entity_index": ent_index,
                "fileId": record.get("fileId"),
                "segId": record.get("segId"),
                **entity,
            })
    return rows


def _telemetry_rows(records: list[dict[str, Any]]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for record in records:
        for tel in record.get("telemetry") or []:
            if isinstance(tel, dict):
                rows.append({"fileId": record.get("fileId"), "segId": record.get("segId"), **tel})
    return rows


def _highlight_text(text: str, spans: list[dict[str, Any]]) -> str:
    """Render non-overlapping source-grounded spans without altering source text."""
    valid = []
    for span in spans:
        start, end = span.get("start_char"), span.get("end_char")
        if not isinstance(start, int) or not isinstance(end, int) or not (0 <= start < end <= len(text)):
            continue
        if text[start:end] != span.get("text"):
            continue
        valid.append(span)
    valid.sort(key=lambda row: (row["start_char"], -(row["end_char"] - row["start_char"])))

    chosen = []
    cursor = -1
    for span in valid:
        if span["start_char"] < cursor:
            continue
        chosen.append(span)
        cursor = span["end_char"]

    parts = []
    pos = 0
    for span in chosen:
        start, end = span["start_char"], span["end_char"]
        parts.append(html.escape(text[pos:start]))
        label = html.escape(str(span.get("label") or span.get("place_type") or "entity"))
        title = html.escape(str(span.get("source") or "annotation"))
        parts.append(
            f'<mark title="{title}" style="padding:0.12rem 0.2rem;border-radius:0.25rem;">'
            f'{html.escape(text[start:end])}<sup style="font-size:0.68em;margin-left:0.15rem;">{label}</sup></mark>'
        )
        pos = end
    parts.append(html.escape(text[pos:]))
    return '<div style="line-height:1.9;font-size:1.02rem;white-space:pre-wrap;">' + "".join(parts) + "</div>"


def _make_segments(content: str, *, testimony: bool, nlp=None, max_chars: int = 14000) -> tuple[list[dict], list[dict] | None]:
    if testimony:
        turns = segment_testimony(content, nlp=nlp)
        segments = [
            {
                "text": turn.text,
                "segStartChar": turn.seg_start_char,
                "segEndChar": turn.seg_end_char,
                "segTextCharLength": len(turn.text),
            }
            for turn in turns
        ]
        metadata = [
            {
                "role": turn.role,
                "turnId": turn.turn_id,
                "qaPairId": turn.qa_pair_id,
                "isQuestion": turn.is_question,
                "isAnswer": turn.is_answer,
            }
            for turn in turns
        ]
        return segments, metadata
    return split_into_segments(
        content, max_chars=max_chars, overlap_chars=0, nlp=nlp, as_records=True
    ), None


def _annotate_content(
    file_id: str,
    content: str,
    *,
    ner_model: str,
    resources_dir: str,
    link_places: bool,
    include_events: bool,
    testimony: bool,
    max_chars: int,
) -> list[dict[str, Any]]:
    spec = parse_ner_model(ner_model)
    if spec.backend == "hf":
        segments, metadata = _make_segments(content, testimony=testimony, nlp=None, max_chars=max_chars)
        annotator = HFNERAnnotator(spec.model, link_places=link_places)
        rows = []
        for i, seg in enumerate(segments, start=1):
            rec = annotator.annotate(seg["text"], include_text=True)
            rec.update({
                "file": file_id,
                "fileId": file_id,
                "segId": i,
                "segCount": len(segments),
                "segStartChar": seg.get("segStartChar"),
                "segEndChar": seg.get("segEndChar"),
                "segTextCharLength": seg.get("segTextCharLength"),
            })
            if metadata:
                rec.update(metadata[i - 1])
            rows.append(rec)
        return rows

    nlp = cached_spacy(spec.model, resources_dir, True)
    segments, metadata = _make_segments(content, testimony=testimony, nlp=nlp, max_chars=max_chars)
    annotator = Annotator(nlp, resources_dir=resources_dir, model_name=spec.model, link_places=link_places)
    return annotator.annotate_texts(
        segments,
        file_id=file_id,
        include_text=True,
        include_verbs=False,
        include_events=include_events,
        metadata=metadata,
    )


def _add_affect(
    records: list[dict[str, Any]],
    *,
    sentiment_key: str,
    emotion_key: str,
    llm_provider: str,
) -> None:
    texts = [row.get("text", "") for row in records]
    if sentiment_key != "none":
        backend = sentiment_key.split(":", 1)[0]
        model = sentiment_key.split(":", 1)[1] if sentiment_key.startswith("hf:") else None
        sent = SentimentAnalyzer(backend, model_name=model, provider=llm_provider)
        for row, pred in zip(records, sent.predict(texts)):
            row["sentiment_label"] = pred.get("label")
            row["sentiment_score"] = pred.get("score")
            row["sentiment_distribution"] = pred.get("distribution")
            if pred.get("telemetry"):
                row.setdefault("telemetry", []).append(pred["telemetry"])
    if emotion_key != "none":
        backend = emotion_key.split(":", 1)[0]
        model = emotion_key.split(":", 1)[1] if emotion_key.startswith("hf:") else None
        emo = EmotionAnalyzer(backend, model_name=model, provider=llm_provider)
        for row, pred in zip(records, emo.predict(texts)):
            row["emotion_label"] = pred.get("label")
            row["emotion_score"] = pred.get("score")
            row["emotion_dist"] = pred.get("distribution")
            if pred.get("telemetry"):
                row.setdefault("telemetry", []).append(pred["telemetry"])


def _run_live_journeys(content: str, file_id: str, provider: str, model: str | None) -> dict[str, Any]:
    client = LLMClient(provider=provider, model=model)
    return JourneyExtractor(client=client).extract(content, file_id=file_id, seg_id=0)


def _combined_geojson(records: list[dict[str, Any]], journeys: list[dict[str, Any]], allow_ambiguous: bool) -> dict[str, Any]:
    points = to_geojson(records)
    routes = journeys_to_geojson(journeys, allow_ambiguous=allow_ambiguous) if journeys else {"features": [], "audit": []}
    return {
        "type": "FeatureCollection",
        "features": list(points.get("features", [])) + list(routes.get("features", [])),
        "audit": routes.get("audit", []),
    }


def _render_map(geojson: dict[str, Any]) -> None:
    try:
        import folium
        import streamlit.components.v1 as components
    except Exception as exc:
        st.warning(f"Interactive map unavailable: {exc}")
        return

    coords = []
    for feature in geojson.get("features", []):
        geometry = feature.get("geometry") or {}
        if geometry.get("type") == "Point":
            lon, lat = geometry.get("coordinates", [None, None])[:2]
            if lon is not None and lat is not None:
                coords.append((float(lat), float(lon)))
        elif geometry.get("type") == "LineString":
            for pair in geometry.get("coordinates") or []:
                if len(pair) >= 2:
                    coords.append((float(pair[1]), float(pair[0])))
    center = [52.0, 0.0] if not coords else [sum(x[0] for x in coords) / len(coords), sum(x[1] for x in coords) / len(coords)]
    fmap = folium.Map(location=center, zoom_start=4)
    folium.GeoJson(geojson, name="spatial evidence").add_to(fmap)
    components.html(fmap._repr_html_(), height=560)


def _method_chain() -> None:
    st.markdown(
        "**Manual annotation → Rules/gazetteers → Contextual NLP → Resolution → "
        "Affect/events → LLM structured extraction → Human review → Spatial representation**"
    )


with st.sidebar:
    st.markdown("### 🗺️ Spatial Humanities 2026")
    page = st.radio("Navigate", ["Home", "Annotate", "Compare", "Explore", "Review", "About"])
    st.divider()
    mode = st.radio("Interface mode", ["Guided", "Expert"], horizontal=True)
    st.caption("Guided mode keeps the demonstration lightweight. Expert mode exposes model choices and optional provider-backed features.")

    resources_dir = str(ROOT / "spatio_textual" / "resources")
    if mode == "Guided":
        ner_model = "spacy:en_core_web_sm"
        link_places = True
        include_events = True
        testimony = True
        max_chars = 14000
        sentiment_key = "rule"
        emotion_key = "rule"
        llm_provider = "openai"
        llm_model = None
        run_journeys = False
    else:
        ner_model = st.selectbox("Primary spatial NER", list(NER_MODELS.keys()), index=list(NER_MODELS.keys()).index("spacy:en_core_web_sm") if "spacy:en_core_web_sm" in NER_MODELS else 0)
        st.caption(parse_ner_model(ner_model).description)
        link_places = st.checkbox("Resolve named places", value=True)
        include_events = st.checkbox("Narrator-centred events", value=True)
        testimony = st.checkbox("Q/A-aware segmentation", value=True)
        max_chars = int(st.number_input("Max chars/segment", min_value=500, value=14000, step=500))
        sentiment_key = st.selectbox("Sentiment", list(SENTIMENT_MODELS.keys()), index=list(SENTIMENT_MODELS.keys()).index("rule") if "rule" in SENTIMENT_MODELS else 0)
        emotion_key = st.selectbox("Emotion", list(EMOTION_MODELS.keys()), index=list(EMOTION_MODELS.keys()).index("rule") if "rule" in EMOTION_MODELS else 0)
        llm_provider = st.selectbox("LLM provider", LLM_PROVIDERS, index=0)
        llm_model = st.text_input("LLM model (blank = provider default)", value="").strip() or None
        run_journeys = st.checkbox("Run live evidence-first journey extraction", value=False)
        if run_journeys:
            st.warning("Live LLM mode uses provider credentials configured in the server environment. Do not paste keys into the source text.")


st.title("From text to auditable spatial evidence")
st.caption("SH2026 research demonstrator · uncertainty, provenance and human review remain visible")


if page == "Home":
    st.subheader("What this demonstrator is for")
    st.write(
        "Explore how manual/rule-based, contextual NLP and LLM-assisted methods expose different layers of spatial meaning. "
        "The aim is not to produce an authoritative map automatically, but to keep source evidence, ambiguity and human judgement connected to computational outputs."
    )
    _method_chain()

    c1, c2, c3 = st.columns(3)
    c1.metric("Core distinction", "Accuracy ≠ reach")
    c2.metric("Evidence principle", "Ground before trust")
    c3.metric("Review principle", "Uncertainty survives export")

    st.markdown("### Curated examples")
    for i, example in enumerate(_safe_example_options()):
        with st.container(border=True):
            left, right = st.columns([4, 1])
            with left:
                st.markdown(f"**{example.get('title')}**")
                st.caption(f"{example.get('genre')} · {', '.join(example.get('teaching_targets') or [])}")
                st.write(example.get("text"))
                if "pending" in str(example.get("distribution_status")):
                    st.warning("Teaching source citation still requires final verification before release.")
                else:
                    st.caption(example.get("source_note"))
            with right:
                if st.button("Use example", key=f"use_example_{i}"):
                    _use_example(example)
                    st.success("Loaded. Open Annotate.")

    st.markdown("### Two conference outputs, one research argument")
    st.markdown("**Workshop:** *AI and NLP for Spatial Humanities: From Manual Annotation to LLM-Assisted Interpretation*")
    st.markdown("**Keynote:** *From Coordinates to Context: Rethinking Spatial Humanities in the Age of Large Language Models*")


elif page == "Annotate":
    st.subheader("Annotate a source")
    uploaded = st.file_uploader("Optional .txt files", type=["txt"], accept_multiple_files=True)
    source_text = st.text_area("Or paste / edit text", key="sh_source_text", height=260)
    if st.session_state.get("sh_source_note"):
        st.caption(st.session_state["sh_source_note"])

    with st.expander("Active configuration", expanded=False):
        st.json({
            "mode": mode,
            "ner_model": ner_model,
            "link_places": link_places,
            "include_events": include_events,
            "qa_aware_segmentation": testimony,
            "max_chars": max_chars,
            "sentiment": sentiment_key,
            "emotion": emotion_key,
            "live_journey_extraction": run_journeys,
            "llm_provider": llm_provider if run_journeys else None,
            "llm_model": llm_model if run_journeys else None,
        })

    if st.button("Analyse text", type="primary", use_container_width=True):
        source_items = []
        if uploaded:
            for file in uploaded:
                source_items.append((Path(file.name).stem, file.read().decode("utf-8", errors="ignore")))
        elif source_text.strip():
            source_items.append((st.session_state.get("sh_source_id") or "pasted_text", source_text))

        if not source_items:
            st.error("Paste text or upload at least one .txt file.")
        else:
            all_records = []
            all_journeys = []
            journey_audit = []
            for file_id, content in source_items:
                rows = _annotate_content(
                    file_id,
                    content,
                    ner_model=ner_model,
                    resources_dir=resources_dir,
                    link_places=link_places,
                    include_events=include_events,
                    testimony=testimony,
                    max_chars=max_chars,
                )
                _add_affect(rows, sentiment_key=sentiment_key, emotion_key=emotion_key, llm_provider=llm_provider)
                all_records.extend(rows)
                if run_journeys:
                    try:
                        jr = _run_live_journeys(content, file_id, llm_provider, llm_model)
                        all_journeys.extend(jr.get("journeys") or [])
                        journey_audit.extend(jr.get("review_notes") or [])
                    except Exception as exc:
                        journey_audit.append(f"{file_id}: live journey extraction failed: {exc}")

            config = {
                "mode": mode,
                "ner_model": ner_model,
                "link_places": link_places,
                "include_events": include_events,
                "qa_aware_segmentation": testimony,
                "max_chars": max_chars,
                "sentiment": sentiment_key,
                "emotion": emotion_key,
                "llm_provider": llm_provider if run_journeys else None,
                "llm_model": llm_model if run_journeys else None,
            }
            st.session_state["sh_records"] = all_records
            st.session_state["sh_journeys"] = all_journeys
            st.session_state["sh_journey_audit"] = journey_audit
            st.session_state["sh_source_items"] = source_items
            st.session_state["sh_last_config"] = config
            st.success(f"Created {len(all_records)} segment record(s).")

    records = st.session_state.get("sh_records", [])
    journeys = st.session_state.get("sh_journeys", [])
    if records:
        entities = _entity_rows(records)
        telemetry = _telemetry_rows(records)
        tel_summary = summarize_telemetry(telemetry)
        m1, m2, m3, m4 = st.columns(4)
        m1.metric("Segments", len(records))
        m2.metric("Entities", len(entities))
        m3.metric("Review flags", sum(bool(r.get("requires_review")) for r in records) + sum(bool(j.get("requires_review")) for j in journeys))
        m4.metric("Journeys", len(journeys))

        st.markdown("### Source-grounded annotations")
        for record in records:
            title = f"{record.get('fileId')} · segment {record.get('segId')}"
            with st.expander(title, expanded=len(records) <= 3):
                st.markdown(_highlight_text(record.get("text", ""), record.get("entities") or []), unsafe_allow_html=True)
                small = [{k: ent.get(k) for k in ("text", "label", "place_type", "resolved_name", "resolution_status", "geo_confidence", "ambiguous", "source")} for ent in record.get("entities") or []]
                if small:
                    st.dataframe(pd.DataFrame(small), use_container_width=True, hide_index=True)
                if record.get("sentiment_label") or record.get("emotion_label"):
                    st.caption(
                        f"Model-labelled affect · sentiment: {record.get('sentiment_label', '—')} · emotion: {record.get('emotion_label', '—')}"
                    )
                if record.get("event_data"):
                    st.write("Narrator-centred event cues")
                    st.dataframe(pd.DataFrame(record.get("event_data")), use_container_width=True, hide_index=True)

        if journeys:
            st.markdown("### Evidence-first journeys")
            st.dataframe(pd.DataFrame(journeys), use_container_width=True, hide_index=True)

        with st.expander("Telemetry and provenance", expanded=False):
            st.json(tel_summary)
            manifest = build_run_manifest(
                input_text="\n".join(text for _, text in st.session_state.get("sh_source_items", [])),
                config=st.session_state.get("sh_last_config", {}),
                git_commit=current_git_commit(),
            )
            st.json(manifest)

        with st.expander("Export", expanded=False):
            payload = {"records": records, "journeys": journeys}
            st.download_button(
                "Download auditable JSON",
                json.dumps(payload, ensure_ascii=False, indent=2).encode("utf-8"),
                "sh2026_spatial_annotations.json",
                "application/json",
            )
            st.download_button(
                "Download segment JSONL",
                "".join(json.dumps(row, ensure_ascii=False) + "\n" for row in records).encode("utf-8"),
                "sh2026_segments.jsonl",
                "application/x-ndjson",
            )
            csv_df = pd.DataFrame(records)
            st.download_button("Download segment CSV", csv_df.to_csv(index=False).encode("utf-8"), "sh2026_segments.csv", "text/csv")
            conll_docs = []
            for row in records:
                tokens = (row.get("text") or "").split()
                conll_docs.append(entities_to_conll(tokens, row.get("entities") or [], doc_id=f"{row.get('fileId')}_{row.get('segId')}"))
            st.download_button("Download CoNLL/BIO", "\n".join(conll_docs).encode("utf-8"), "sh2026_entities.conll", "text/plain")


elif page == "Compare":
    st.subheader("Compare methodological outputs")
    source = st.session_state.get("sh_source_text", "").strip()
    if not source:
        st.info("Load or paste an example on Home/Annotate first.")
    else:
        st.write("This view compares what methods *represent*, not only how many strings they return.")
        if st.button("Run lightweight comparison", type="primary"):
            rule = RuleGazetteerAnnotator(gazetteer_path=TEACHING_GAZETTEER, link_places=False)
            rule_result = rule.annotate(source)

            spec = parse_ner_model(ner_model)
            if spec.backend == "spacy":
                # contextual-only condition: no project EntityRuler resources
                nlp = cached_spacy(spec.model, resources_dir, False)
                ann = Annotator(nlp=nlp, model_name=spec.model, link_places=False)
                contextual = ann.annotate(source, include_entities=True, include_events=False, include_text=True)
                contextual_spans = harmonize_ner_entities(contextual.get("entities") or [])
            else:
                ann = HFNERAnnotator(spec.model, link_places=False)
                contextual = ann.annotate(source, include_text=True)
                contextual_spans = harmonize_ner_entities(contextual.get("entities") or [])

            st.session_state["sh_compare"] = {
                "rules": rule_result,
                "contextual": contextual,
                "contextual_spans": contextual_spans,
            }

        compare = st.session_state.get("sh_compare")
        if compare:
            left, right = st.columns(2)
            with left:
                st.markdown("#### Rules / gazetteer")
                st.markdown(_highlight_text(source, compare["rules"].get("spans") or []), unsafe_allow_html=True)
                st.dataframe(pd.DataFrame(compare["rules"].get("spans") or []), use_container_width=True, hide_index=True)
                st.caption("Deterministic and inspectable; limited to encoded forms and resources.")
            with right:
                st.markdown("#### Contextual NER")
                st.markdown(_highlight_text(source, compare.get("contextual_spans") or []), unsafe_allow_html=True)
                st.dataframe(pd.DataFrame(compare.get("contextual_spans") or []), use_container_width=True, hide_index=True)
                st.caption("Contextual named-entity recognition; output ontology still constrains representational reach.")

            st.markdown("#### Questions for interpretation")
            st.write(
                "Which spatial evidence is visible to both methods? Which is visible only to the rule ontology? "
                "Which spatial relations, journey fields, deictic references or experiential descriptions are outside both output schemas?"
            )
            if st.session_state.get("sh_journeys"):
                st.markdown("#### Structured journey layer")
                st.dataframe(pd.DataFrame(st.session_state["sh_journeys"]), use_container_width=True, hide_index=True)
                st.caption("Journey extraction is a richer structured task and should not be treated as directly equivalent to NER F1.")


elif page == "Explore":
    st.subheader("Explore spatial representations")
    records = st.session_state.get("sh_records", [])
    journeys = st.session_state.get("sh_journeys", [])
    if not records and not journeys:
        st.info("Analyse a source first.")
    else:
        allow_ambiguous = st.checkbox("Show routes with ambiguous endpoints", value=False)
        geojson = _combined_geojson(records, journeys, allow_ambiguous)
        st.caption(f"Mapped features: {len(geojson.get('features', []))}. Unmapped/route-audit entries remain available below.")
        _render_map(geojson)

        if geojson.get("audit"):
            st.markdown("### Route audit: what did *not* become a line?")
            st.dataframe(pd.DataFrame(geojson["audit"]), use_container_width=True, hide_index=True)

        st.markdown("### Co-occurrence")
        edges = build_cooccurrence(records)
        if edges:
            st.dataframe(pd.DataFrame(edges, columns=["source", "target", "weight"]), use_container_width=True, hide_index=True)
        else:
            st.caption("No co-occurrence edges for the current records.")

        affect_rows = [
            {"segment": f"{row.get('fileId')}:{row.get('segId')}", "negative": (row.get("sentiment_distribution") or {}).get("negative")}
            for row in records
            if isinstance((row.get("sentiment_distribution") or {}).get("negative"), (int, float))
        ]
        if affect_rows:
            st.markdown("### Narrative sequence: model-labelled negative probability")
            affect_df = pd.DataFrame(affect_rows).set_index("segment")
            st.line_chart(affect_df)
            st.caption("This is a computational affect signal, not a measurement of a narrator's psychological state.")

        with st.expander("Raw auditable GeoJSON", expanded=False):
            st.json(geojson)


elif page == "Review":
    st.subheader("Human review")
    st.write("Machine suggestions remain in the record; human accept/edit/reject actions are appended rather than silently replacing provenance.")
    records = st.session_state.get("sh_records", [])
    journeys = st.session_state.get("sh_journeys", [])
    flagged_entities = [row for row in _entity_rows(records) if row.get("ambiguous") or row.get("resolution_status") == "unresolved" or row.get("requires_review")]
    flagged_journeys = [(i, row) for i, row in enumerate(journeys) if row.get("requires_review") or row.get("human_status") == "unreviewed"]

    st.metric("Items needing attention", len(flagged_entities) + len(flagged_journeys))

    st.markdown("### Place-resolution review")
    if not flagged_entities:
        st.caption("No ambiguous/unresolved entities are currently flagged.")
    for item in flagged_entities:
        rec_i, ent_i = item["record_index"], item["entity_index"]
        key_base = f"entity_{rec_i}_{ent_i}"
        with st.container(border=True):
            st.markdown(f"**{item.get('text')}** · {item.get('resolution_status', 'unresolved')}")
            st.write({k: item.get(k) for k in ("resolved_name", "lat", "lon", "geo_source", "geo_confidence", "ambiguous", "candidates")})
            c1, c2 = st.columns(2)
            new_name = c1.text_input("Resolved name / note", value=str(item.get("resolved_name") or item.get("text") or ""), key=f"{key_base}_name")
            action = c2.selectbox("Decision", ["accept", "edit", "reject"], key=f"{key_base}_action")
            if st.button("Save entity review", key=f"{key_base}_save"):
                current = records[rec_i]["entities"][ent_i]
                if action == "edit":
                    reviewed = apply_human_review(current, action="edit", field="resolved_name", new_value=new_name, reason="disambiguation")
                elif action == "accept":
                    reviewed = apply_human_review(current, action="accept", reason="human_flag")
                else:
                    reviewed = apply_human_review(current, action="reject", reason="human_flag")
                records[rec_i]["entities"][ent_i] = reviewed
                st.session_state["sh_records"] = records
                st.success("Review saved with audit trail.")

    st.markdown("### Journey review")
    if not flagged_journeys:
        st.caption("No journey records currently require review.")
    for index, journey in flagged_journeys:
        key_base = f"journey_{index}"
        with st.container(border=True):
            st.markdown(f"**{journey.get('start_location') or '∅'} → {journey.get('end_location') or '∅'}**")
            st.caption(journey.get("evidence_quote") or "No grounded evidence quote")
            st.write("Field status:", journey.get("explicit_or_inferred"))
            st.write("Review notes:", journey.get("review_notes"))
            field = st.selectbox("Field to edit (if needed)", ["start_location", "end_location", "transport_mode", "date", "journey_reason"], key=f"{key_base}_field")
            new_value = st.text_input("Replacement value", key=f"{key_base}_value")
            action = st.selectbox("Decision", ["accept", "edit", "reject"], key=f"{key_base}_action")
            if st.button("Save journey review", key=f"{key_base}_save"):
                if action == "edit":
                    reviewed = apply_human_review(journey, action="edit", field=field, new_value=new_value or None, reason="correction")
                    statuses = dict(reviewed.get("explicit_or_inferred") or {})
                    statuses[field] = "human_supplied" if new_value else "missing"
                    reviewed["explicit_or_inferred"] = statuses
                elif action == "accept":
                    reviewed = apply_human_review(journey, action="accept", reason="human_flag")
                else:
                    reviewed = apply_human_review(journey, action="reject", reason="unsupported_llm_field")
                journeys[index] = reviewed
                st.session_state["sh_journeys"] = journeys
                st.success("Journey review saved with audit trail.")


elif page == "About":
    st.subheader("About this demonstrator")
    _method_chain()
    st.markdown(
        "The demo is designed around a simple proposition: **increasing representational capability shifts the bottleneck from extraction toward validation, provenance, interpretation and governance.**"
    )
    st.markdown("### What it does not claim")
    st.write(
        "Outputs are not historical ground truth, psychological diagnoses or automatically authoritative maps. "
        "Named-entity models are evaluated within their output ontology; richer LLM structures require stronger evidence and review."
    )
    st.markdown("### Data boundary")
    st.write(
        "The public demonstrator uses public-safe or synthetic material. Controlled-access testimony transcripts and private archival data are not bundled into the repository or demo."
    )
    st.markdown("### Provenance")
    st.json({
        "git_commit": current_git_commit(),
        "branch_target": "spatial-humanities-2026",
        "common_schema": "docs/sh2026/COMMON_SCHEMA.md",
        "benchmark_protocol": "docs/sh2026/BENCHMARK_PROTOCOL.md",
    })
    st.markdown("### Conference titles")
    st.markdown("**Workshop:** *AI and NLP for Spatial Humanities: From Manual Annotation to LLM-Assisted Interpretation*")
    st.markdown("**Keynote:** *From Coordinates to Context: Rethinking Spatial Humanities in the Age of Large Language Models*")
