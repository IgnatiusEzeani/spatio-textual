from __future__ import annotations

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
from spatio_textual.journeys import JourneyExtractor
from spatio_textual.llm import LLMClient
from spatio_textual.provenance import build_run_manifest
from spatio_textual.review import apply_human_review
from spatio_textual.rules import RuleGazetteerAnnotator
from spatio_textual.sentiment import SentimentAnalyzer
from spatio_textual.utils import Annotator, load_spacy_model
from spatio_textual.viz import build_cooccurrence, journeys_to_geojson, to_geojson

DEMO_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = DEMO_DIR.parent
REPO_ROOT = PROJECT_ROOT.parents[1]
WORKSHOP_DATA = PROJECT_ROOT / "workshop" / "data"
EXAMPLES_PATH = WORKSHOP_DATA / "examples.json"
TEACHING_GAZETTEER = WORKSHOP_DATA / "teaching_gazetteer.csv"
PACKAGE_RESOURCES = REPO_ROOT / "spatio_textual" / "resources"

st.set_page_config(
    page_title="Spatial Humanities 2026 | spatio-textual",
    page_icon="🗺️",
    layout="wide",
    initial_sidebar_state="expanded",
)


@st.cache_data
def load_examples() -> list[dict[str, Any]]:
    if not EXAMPLES_PATH.exists():
        return []
    return json.loads(EXAMPLES_PATH.read_text(encoding="utf-8"))


@st.cache_resource
def load_contextual_model():
    return load_spacy_model(
        "en_core_web_sm",
        resources_dir=PACKAGE_RESOURCES,
        add_entity_ruler=False,
    )


def git_commit() -> str | None:
    try:
        result = subprocess.run(
            ["git", "rev-parse", "HEAD"],
            cwd=REPO_ROOT,
            capture_output=True,
            text=True,
            check=True,
            timeout=5,
        )
        return result.stdout.strip() or None
    except Exception:
        return None


def entity_rows(records: list[dict[str, Any]]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for record in records:
        for entity in record.get("entities") or []:
            rows.append({
                "segment": record.get("segId", 1),
                "text": entity.get("text"),
                "label": entity.get("label"),
                "resolved_name": entity.get("resolved_name"),
                "resolution_status": entity.get("resolution_status"),
                "ambiguous": entity.get("ambiguous"),
                "lat": entity.get("lat"),
                "lon": entity.get("lon"),
                "source": entity.get("source"),
            })
    return rows


def telemetry_rows(records: list[dict[str, Any]]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for record in records:
        rows.extend(row for row in (record.get("telemetry") or []) if isinstance(row, dict))
    return rows


def analyse(text: str, *, link_places: bool = True) -> dict[str, Any]:
    nlp = load_contextual_model()
    annotator = Annotator(
        nlp,
        resources_dir=PACKAGE_RESOURCES,
        model_name="en_core_web_sm",
        link_places=link_places,
    )
    contextual = annotator.annotate(
        text,
        include_text=True,
        include_entities=True,
        include_events=True,
    )
    contextual["fileId"] = "demo"
    contextual["segId"] = 1

    rules = RuleGazetteerAnnotator(
        gazetteer_path=TEACHING_GAZETTEER,
        link_places=False,
    ).annotate(text)

    sentiment = SentimentAnalyzer("rule").predict([text])[0]
    emotion = EmotionAnalyzer("rule").predict([text])[0]

    contextual["sentiment_label"] = sentiment.get("label")
    contextual["sentiment_distribution"] = sentiment.get("distribution")
    contextual["emotion_label"] = emotion.get("label")
    contextual["emotion_dist"] = emotion.get("distribution")
    contextual.setdefault("telemetry", []).extend(
        [row for row in (sentiment.get("telemetry"), emotion.get("telemetry")) if row]
    )

    return {"records": [contextual], "rules": rules}


def maybe_extract_journeys(text: str) -> dict[str, Any] | None:
    if not os.getenv("OPENAI_API_KEY"):
        return None
    client = LLMClient(provider="openai")
    return JourneyExtractor(client=client).extract(text, file_id="demo", seg_id=1)


def render_map(records: list[dict[str, Any]], journeys: list[dict[str, Any]]) -> None:
    try:
        import folium
        import streamlit.components.v1 as components
    except Exception as exc:
        st.info(f"Interactive map unavailable in this environment: {exc}")
        return

    point_geo = to_geojson(records)
    route_geo = journeys_to_geojson(journeys) if journeys else {"features": [], "audit": []}
    features = list(point_geo.get("features", [])) + list(route_geo.get("features", []))
    if not features:
        st.info("No currently resolved geometry is available. Unresolved spatial evidence remains visible in the tables.")
        return

    coordinates: list[tuple[float, float]] = []
    for feature in features:
        geometry = feature.get("geometry") or {}
        if geometry.get("type") == "Point":
            lon, lat = geometry.get("coordinates", [None, None])[:2]
            if lon is not None and lat is not None:
                coordinates.append((float(lat), float(lon)))
        elif geometry.get("type") == "LineString":
            for pair in geometry.get("coordinates") or []:
                if len(pair) >= 2:
                    coordinates.append((float(pair[1]), float(pair[0])))

    center = [52.0, 0.0]
    if coordinates:
        center = [
            sum(lat for lat, _ in coordinates) / len(coordinates),
            sum(lon for _, lon in coordinates) / len(coordinates),
        ]
    fmap = folium.Map(location=center, zoom_start=4)
    folium.GeoJson({"type": "FeatureCollection", "features": features}).add_to(fmap)
    components.html(fmap._repr_html_(), height=520)
    if route_geo.get("audit"):
        st.caption("Some journey records could not be mapped without further resolution.")
        st.dataframe(pd.DataFrame(route_geo["audit"]), use_container_width=True, hide_index=True)


def benchmark_snapshot() -> None:
    st.markdown("### Frozen SH2026 benchmark snapshot")
    st.caption("These are project-specific empirical results, not package performance guarantees.")
    st.dataframe(
        pd.DataFrame(
            [
                {"Task": "TOPONYM", "Method": "Rules", "Precision": 1.000, "Recall": 0.073, "F1": 0.136},
                {"Task": "TOPONYM", "Method": "spaCy", "Precision": 0.962, "Recall": 0.610, "F1": 0.746},
                {"Task": "TOPONYM", "Method": "HF BERT", "Precision": 0.952, "Recall": 0.976, "F1": 0.964},
                {"Task": "TOPONYM", "Method": "GPT-5.6 Sol", "Precision": 0.976, "Recall": 1.000, "F1": 0.988},
                {"Task": "Journey", "Method": "Rules", "Precision": 0.944, "Recall": 0.944, "F1": 0.944},
                {"Task": "Journey", "Method": "Transformer", "Precision": 0.882, "Recall": 0.833, "F1": 0.857},
                {"Task": "Journey", "Method": "GPT-5.6 Sol", "Precision": 0.750, "Recall": 1.000, "F1": 0.857},
            ]
        ),
        use_container_width=True,
        hide_index=True,
    )
    st.info(
        "Read the table as a trade-off, not a leaderboard: representational reach, evidence, inference and review burden change with the method."
    )


if "analysis" not in st.session_state:
    st.session_state.analysis = None
if "journeys" not in st.session_state:
    st.session_state.journeys = []
if "journey_notes" not in st.session_state:
    st.session_state.journey_notes = []

examples = load_examples()

with st.sidebar:
    st.markdown("## Spatial Humanities 2026")
    page = st.radio("Navigate", ["Home", "Analyse", "Compare", "Explore", "Review", "About"])
    st.divider()
    st.caption("Conference demonstrator built on the reusable `spatio-textual` package.")

st.title("From Coordinates to Context")
st.caption("Auditable spatial-text analysis: recognition → event reconstruction → interpretation")

if page == "Home":
    st.markdown(
        "This demonstrator compares computational methods without assuming that newer models simply replace older ones. "
        "The central question is what each method can represent, what evidence supports its output, and what a scholar still needs to validate."
    )
    a, b, c = st.columns(3)
    a.metric("Recognition", "Spatial entities")
    b.metric("Reconstruction", "Journeys")
    c.metric("Interpretation", "Affect")
    benchmark_snapshot()
    st.markdown("### Methodological progression")
    st.markdown("**Rules / resources → contextual transformers → structured LLMs → human adjudication**")

elif page == "Analyse":
    st.subheader("Analyse a public-safe example")
    titles = [example["title"] for example in examples]
    chosen = st.selectbox("Example", titles) if titles else None
    default_text = examples[titles.index(chosen)]["text"] if chosen else ""
    text = st.text_area("Source text", value=default_text, height=220)
    link_places = st.checkbox("Resolve named places where possible", value=True)
    run_llm = st.checkbox("Also run live evidence-first LLM journey extraction", value=False)
    if run_llm and not os.getenv("OPENAI_API_KEY"):
        st.warning("No server-side OpenAI key is configured. The core demonstration remains fully usable without a live LLM call.")

    if st.button("Run analysis", type="primary", use_container_width=True):
        if not text.strip():
            st.error("Enter source text first.")
        else:
            result = analyse(text, link_places=link_places)
            st.session_state.analysis = {"text": text, **result}
            st.session_state.journeys = []
            st.session_state.journey_notes = []
            if run_llm and os.getenv("OPENAI_API_KEY"):
                try:
                    journey_result = maybe_extract_journeys(text)
                    if journey_result:
                        st.session_state.journeys = journey_result.get("journeys") or []
                        st.session_state.journey_notes = journey_result.get("review_notes") or []
                except Exception as exc:
                    st.session_state.journey_notes = [f"Live journey extraction failed: {exc}"]

    analysis = st.session_state.analysis
    if analysis:
        records = analysis["records"]
        entities = entity_rows(records)
        m1, m2, m3 = st.columns(3)
        m1.metric("Contextual entities", len(entities))
        m2.metric("Rule spans", len(analysis["rules"].get("spans") or []))
        m3.metric("Journeys", len(st.session_state.journeys))
        st.markdown("### Contextual NLP output")
        st.dataframe(pd.DataFrame(entities), use_container_width=True, hide_index=True)
        st.markdown("### Affect signals")
        rec = records[0]
        c1, c2 = st.columns(2)
        c1.write("**Sentiment**")
        c1.json(rec.get("sentiment_distribution") or {})
        c2.write("**Emotion**")
        c2.json(rec.get("emotion_dist") or {})
        if st.session_state.journeys:
            st.markdown("### Evidence-first structured journeys")
            st.dataframe(pd.DataFrame(st.session_state.journeys), use_container_width=True, hide_index=True)
        if st.session_state.journey_notes:
            st.warning("; ".join(map(str, st.session_state.journey_notes)))

elif page == "Compare":
    st.subheader("Compare what the methods can represent")
    analysis = st.session_state.analysis
    if not analysis:
        st.info("Run an analysis first.")
    else:
        source = analysis["text"]
        rules = analysis["rules"].get("spans") or []
        contextual = harmonize_ner_entities(analysis["records"][0].get("entities") or [])
        left, right = st.columns(2)
        with left:
            st.markdown("#### Rules / gazetteer")
            st.dataframe(pd.DataFrame(rules), use_container_width=True, hide_index=True)
            st.caption("Transparent and deterministic, but bounded by encoded resources and patterns.")
        with right:
            st.markdown("#### Contextual NER")
            st.dataframe(pd.DataFrame(contextual), use_container_width=True, hide_index=True)
            st.caption("Context-sensitive recognition, but still bounded by its entity ontology.")
        st.markdown("#### Richer structured layer")
        if st.session_state.journeys:
            st.dataframe(pd.DataFrame(st.session_state.journeys), use_container_width=True, hide_index=True)
        else:
            st.caption("Live structured journey extraction has not been run for this passage.")
        st.info(
            "Better recognition within a narrow ontology is not the same as richer spatial understanding. Richer representation also increases the audit burden."
        )
        st.code(source, language=None)

elif page == "Explore":
    st.subheader("Explore spatial representations")
    analysis = st.session_state.analysis
    if not analysis:
        st.info("Run an analysis first.")
    else:
        records = analysis["records"]
        journeys = st.session_state.journeys
        render_map(records, journeys)
        st.markdown("### Co-occurrence as a non-route representation")
        edges = build_cooccurrence(records)
        if edges:
            st.dataframe(pd.DataFrame(edges, columns=["source", "target", "weight"]), use_container_width=True, hide_index=True)
        else:
            st.caption("No co-occurrence edges in the current one-segment example.")

elif page == "Review":
    st.subheader("Human review remains part of the method")
    analysis = st.session_state.analysis
    if not analysis:
        st.info("Run an analysis first.")
    else:
        records = analysis["records"]
        flagged = [
            (i, entity)
            for i, entity in enumerate(records[0].get("entities") or [])
            if entity.get("ambiguous") or entity.get("resolution_status") == "unresolved" or entity.get("requires_review")
        ]
        st.metric("Flagged place records", len(flagged))
        if not flagged:
            st.caption("No place-resolution records are currently flagged.")
        for index, entity in flagged:
            with st.container(border=True):
                st.write({k: entity.get(k) for k in ("text", "resolved_name", "resolution_status", "ambiguous", "candidates")})
                decision = st.selectbox("Decision", ["accept", "reject"], key=f"place_decision_{index}")
                if st.button("Record review", key=f"place_review_{index}"):
                    records[0]["entities"][index] = apply_human_review(entity, action=decision, reason="conference_demo_review")
                    st.session_state.analysis["records"] = records
                    st.success("Review appended to the audit trail.")

        st.markdown("### Journey review")
        if not st.session_state.journeys:
            st.caption("No live journey records to review.")
        for index, journey in enumerate(st.session_state.journeys):
            if not journey.get("requires_review"):
                continue
            with st.container(border=True):
                st.write(f"{journey.get('start_location') or '∅'} → {journey.get('end_location') or '∅'}")
                st.caption(journey.get("evidence_quote") or "No grounded evidence")
                st.write("Field provenance:", journey.get("explicit_or_inferred"))

elif page == "About":
    st.subheader("About the SH2026 demonstrator")
    st.markdown("**Workshop:** *AI and NLP for Spatial Humanities: From Manual Annotation to LLM-Assisted Interpretation*")
    st.markdown("**Keynote:** *From Coordinates to Context: Rethinking Spatial Humanities in the Age of Large Language Models*")
    st.write(
        "The demo is a project-specific presentation layer over the reusable `spatio-textual` package. "
        "It uses public-safe or synthetic material and does not bundle controlled-access testimony transcripts."
    )
    st.markdown("### Provenance")
    records = (st.session_state.analysis or {}).get("records", []) if st.session_state.analysis else []
    manifest = build_run_manifest(
        input_text=(st.session_state.analysis or {}).get("text", "") if st.session_state.analysis else "",
        config={"demo": "SH2026", "live_llm_available": bool(os.getenv("OPENAI_API_KEY"))},
        git_commit=git_commit(),
    )
    st.json({
        "manifest": manifest,
        "telemetry_summary": summarize_telemetry(telemetry_rows(records)) if records else {},
        "common_schema": "projects/sh2026/docs/COMMON_SCHEMA.md",
        "benchmark_protocol": "projects/sh2026/docs/BENCHMARK_PROTOCOL.md",
    })