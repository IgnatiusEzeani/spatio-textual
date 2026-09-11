from __future__ import annotations

import json
from pathlib import Path


NOTEBOOK = Path("projects/sh2026/workshop/03_contextual_ner.ipynb")
FALLBACK = Path("projects/sh2026/demo/ner_transformer_teaching_fallback_v1.json")
MODEL = "dslim/bert-base-NER"
REVISION = "0b95561fd0c304538b5eb8a0ee532ca24dd009b9"


def _source_text(cell: dict) -> str:
    source = cell.get("source", "")
    return "".join(source) if isinstance(source, list) else str(source)


def _set_source(cell: dict, text: str) -> None:
    if isinstance(cell.get("source"), list):
        cell["source"] = text.splitlines(keepends=True)
    else:
        cell["source"] = text


def main() -> None:
    if not FALLBACK.exists():
        raise SystemExit(f"Missing required fallback: {FALLBACK}")

    notebook = json.loads(NOTEBOOK.read_text(encoding="utf-8"))
    changed = 0

    for cell in notebook.get("cells", []):
        text = _source_text(cell)

        if (
            cell.get("cell_type") == "markdown"
            and "## 7. Optional heavy comparison: Hugging Face NER" in text
            and "No fabricated/precomputed HF result is bundled here" in text
        ):
            _set_source(
                cell,
                "## 7. Optional heavy comparison: Hugging Face NER\n\n"
                "The repository includes `HFNERAnnotator` for transformer token-classification models. The live route below uses `dslim/bert-base-NER` at an **exact pinned Hugging Face revision**.\n\n"
                "For the default CPU-friendly workshop path, we bundle a **real precomputed run** over these same teaching references. The fallback records the model name, exact revision, generation commit, entity spans, harmonised spatial spans, exact-match scores and telemetry. It is a reliability asset for this notebook, **not** the frozen held-out benchmark result.\n\n"
                "Set `FAST_MODE = False` to download the pinned model and reproduce the comparison live."
            )
            changed += 1

        if (
            cell.get("cell_type") == "code"
            and "RUN_HF = not FAST_MODE" in text
            and "HFNERAnnotator(\"dslim/bert-base-NER\",link_places=False)" in text
        ):
            _set_source(
                cell,
                "RUN_HF = not FAST_MODE\n"
                "hf_results = []\n"
                "hf_fallback_path = repo_dir / \"projects\" / \"sh2026\" / \"demo\" / \"ner_transformer_teaching_fallback_v1.json\"\n"
                "\n"
                "if RUN_HF:\n"
                "    subprocess.run([sys.executable,\"-m\",\"pip\",\"install\",\"-q\",\"-r\",\"requirements-transformers.txt\"],check=True)\n"
                "    from spatio_textual.transformer_ner import HFNERAnnotator\n"
                f"    hf = HFNERAnnotator(\"{MODEL}\", revision=\"{REVISION}\", link_places=False)\n"
                "    for rec in records:\n"
                "        out = hf.annotate(rec[\"text\"])\n"
                "        pred = harmonize_ner_entities(out[\"entities\"])\n"
                "        ref = reference_spans_for_ner(rec)\n"
                "        score = score_span_annotations(pred, ref, match=\"exact\")\n"
                "        hf_results.append({\n"
                "            \"example_id\": rec[\"example_id\"],\n"
                "            \"method\": f\"HF {hf.model_identifier}\",\n"
                "            \"precision\": score[\"precision\"],\n"
                "            \"recall\": score[\"recall\"],\n"
                "            \"f1\": score[\"f1\"],\n"
                "            \"latency_ms\": out[\"telemetry\"][0][\"latency_ms\"],\n"
                "            \"error\": out.get(\"error\"),\n"
                "        })\n"
                "    hf_source = \"live revision-pinned Hugging Face run\"\n"
                "else:\n"
                "    fallback = json.loads(hf_fallback_path.read_text(encoding=\"utf-8\"))\n"
                "    assert [row[\"example_id\"] for row in fallback[\"records\"]] == [rec[\"example_id\"] for rec in records]\n"
                "    hf_results = [\n"
                "        {\n"
                "            \"example_id\": row[\"example_id\"],\n"
                "            \"method\": f\"HF {fallback['model']}@{fallback['revision'][:8]} (precomputed)\",\n"
                "            \"precision\": row[\"exact_score\"][\"precision\"],\n"
                "            \"recall\": row[\"exact_score\"][\"recall\"],\n"
                "            \"f1\": row[\"exact_score\"][\"f1\"],\n"
                "            \"latency_ms\": (row.get(\"telemetry\") or {}).get(\"latency_ms\"),\n"
                "            \"error\": None,\n"
                "        }\n"
                "        for row in fallback[\"records\"]\n"
                "    ]\n"
                "    hf_source = \"precomputed revision-pinned Hugging Face fallback\"\n"
                "\n"
                "display(pd.DataFrame(hf_results))\n"
                "print(\"HF source:\", hf_source)\n"
                "if not RUN_HF:\n"
                "    print(\"Pinned model:\", fallback[\"model\"], \"revision:\", fallback[\"revision\"])"
            )
            changed += 1

    if changed != 2:
        raise SystemExit(f"Expected to update 2 Notebook 03 cells, updated {changed}")

    NOTEBOOK.write_text(json.dumps(notebook, indent=1, ensure_ascii=False) + "\n", encoding="utf-8")
    print(f"Updated {NOTEBOOK}")


if __name__ == "__main__":
    main()
