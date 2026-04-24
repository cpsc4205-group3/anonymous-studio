from __future__ import annotations

import csv
import hashlib
import io
import json
import os
import sys
import tempfile
from collections import Counter
from pathlib import Path
from typing import Any

# Allow imports from the project root when this folder is copied into the main project.
PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from flask import Blueprint, Flask, Response, jsonify, render_template, request, send_file, send_from_directory

from store import get_store
from pii_engine import (
    ALL_ENTITIES,
    get_engine,
    get_spacy_model_options,
    get_spacy_model_status,
    set_spacy_model,
)
from services.synthetic import SyntheticConfig, synthesize_from_anonymized_text
from store.models import PIISession

store = get_store()

BASE_DIR = Path(__file__).resolve().parent
ALLOWED_EXTENSIONS = {".txt", ".csv", ".json", ".md", ".log"}
DEFAULT_THRESHOLD = 0.35
MAX_TEXT_CHARS = 150_000
DEFAULT_PREFIX = "/hybrid-analyze"
engine = get_engine()


def _confidence_band(score_pct: int) -> str:
    if score_pct >= 90:
        return "Very High"
    if score_pct >= 75:
        return "High"
    if score_pct >= 50:
        return "Medium"
    return "Low"


def _safe_int_percent(score: float | int | None) -> int:
    try:
        return int(round(float(score or 0) * 100))
    except Exception:
        return 0


def _normalize_entities(raw: Any) -> list[str]:
    if not isinstance(raw, list):
        return list(ALL_ENTITIES)
    selected = [str(item).strip() for item in raw if str(item).strip() in ALL_ENTITIES]
    return selected or list(ALL_ENTITIES)


def _parse_list_text(raw: str | None) -> list[str]:
    return [item.strip() for item in str(raw or "").split(",") if item.strip()]


def _mask_value(text: str) -> str:
    return "*" * max(4, len(text))


def _hash_value(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()[:12]


def _replacement_for(entity: dict[str, Any], operator: str) -> str:
    raw_text = str(entity.get("text", ""))
    entity_type = str(entity.get("entity_type", "PII"))
    if operator == "redact":
        return "[REDACTED]"
    if operator == "mask":
        return _mask_value(raw_text)
    if operator == "hash":
        return _hash_value(raw_text)
    return f"<{entity_type}>"


def _merge_entities(entities: list[dict[str, Any]]) -> list[dict[str, Any]]:
    merged: list[dict[str, Any]] = []
    for ent in sorted(entities, key=lambda e: (int(e.get("start", 0)), -float(e.get("score", 0) or 0))):
        if merged and int(ent.get("start", 0)) < int(merged[-1].get("end", 0)):
            if float(ent.get("score", 0) or 0) > float(merged[-1].get("score", 0) or 0):
                merged[-1] = ent
        else:
            merged.append(ent)
    return merged


def _build_linked_segments(
    source_text: str,
    entities: list[dict[str, Any]],
    operator: str,
    synthesized_text: str | None = None,
) -> tuple[list[dict[str, Any]], list[dict[str, Any]], str, str]:
    """Create linked original/result preview segments.

    Returns original_segments, result_segments, plain_result, final_display_text.
    For synthesize, linked result uses placeholders while final_display_text is the
    synthesized output shown in the plain output box.
    """
    original_segments: list[dict[str, Any]] = []
    result_segments: list[dict[str, Any]] = []
    merged = _merge_entities(entities)
    cursor = 0
    rebuilt_result: list[str] = []

    for index, ent in enumerate(merged, start=1):
        start = int(ent.get("start", 0))
        end = int(ent.get("end", 0))
        if start > cursor:
            plain_text = source_text[cursor:start]
            original_segments.append({"text": plain_text, "entityId": None, "kind": "plain"})
            result_segments.append({"text": plain_text, "entityId": None, "kind": "plain"})
            rebuilt_result.append(plain_text)

        entity_id = f"ent-{index}"
        original_value = source_text[start:end]
        replacement_value = _replacement_for(ent, operator if operator != "synthesize" else "replace")
        score_pct = _safe_int_percent(ent.get("score"))
        label = str(ent.get("entity_type", "PII")).replace("_", " ").title()

        original_segments.append(
            {
                "text": original_value,
                "entityId": entity_id,
                "kind": "entity",
                "entityType": ent.get("entity_type", "PII"),
                "label": label,
                "confidence": score_pct,
            }
        )
        result_segments.append(
            {
                "text": replacement_value,
                "entityId": entity_id,
                "kind": "entity",
                "entityType": ent.get("entity_type", "PII"),
                "label": label,
                "confidence": score_pct,
            }
        )
        rebuilt_result.append(replacement_value)
        cursor = end

    if cursor < len(source_text):
        tail = source_text[cursor:]
        original_segments.append({"text": tail, "entityId": None, "kind": "plain"})
        result_segments.append({"text": tail, "entityId": None, "kind": "plain"})
        rebuilt_result.append(tail)

    placeholder_result = "".join(rebuilt_result)
    final_text = synthesized_text if operator == "synthesize" and synthesized_text else placeholder_result
    return original_segments, result_segments, placeholder_result, final_text


def _extract_text_from_upload(upload) -> str:
    if upload is None or not getattr(upload, "filename", ""):
        return ""

    suffix = Path(upload.filename).suffix.lower()
    if suffix not in ALLOWED_EXTENSIONS:
        raise ValueError(
            f"Unsupported file type: {suffix or 'unknown'}. Use .txt, .csv, .json, .md, or .log."
        )

    raw = upload.read()
    if not raw:
        return ""

    text = raw.decode("utf-8", errors="replace")
    if suffix == ".json":
        try:
            obj = json.loads(text)
            text = json.dumps(obj, indent=2)
        except Exception:
            pass
    elif suffix == ".csv":
        try:
            import pandas as pd
            df = pd.read_csv(io.StringIO(text))
            text = df.to_csv(index=False)
        except Exception:
            pass
    return text[:MAX_TEXT_CHARS]


def _build_summary(entities: list[dict[str, Any]]) -> dict[str, Any]:
    counts = Counter(str(ent.get("entity_type", "UNKNOWN")) for ent in entities)
    conf_values = [_safe_int_percent(ent.get("score")) for ent in entities]
    band_counts = Counter(_confidence_band(score) for score in conf_values)
    dominant_entity = counts.most_common(1)[0][0] if counts else "None"
    dominant_band = band_counts.most_common(1)[0][0] if band_counts else "N/A"
    avg_conf = round(sum(conf_values) / len(conf_values), 1) if conf_values else 0.0
    low_conf = sum(1 for score in conf_values if score < 50)

    return {
        "totalEntities": len(entities),
        "entityCounts": dict(sorted(counts.items(), key=lambda item: (-item[1], item[0]))),
        "dominantEntity": dominant_entity,
        "dominantBand": dominant_band,
        "averageConfidence": avg_conf,
        "lowConfidenceCount": low_conf,
        "bandCounts": {
            "Very High": band_counts.get("Very High", 0),
            "High": band_counts.get("High", 0),
            "Medium": band_counts.get("Medium", 0),
            "Low": band_counts.get("Low", 0),
        },
    }


def _serialize_entity_rows(entities: list[dict[str, Any]]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for ent in entities:
        score_pct = _safe_int_percent(ent.get("score"))
        rows.append(
            {
                "entityType": ent.get("entity_type", ""),
                "text": ent.get("text", ""),
                "confidence": score_pct,
                "confidenceBand": _confidence_band(score_pct),
                "start": ent.get("start", 0),
                "end": ent.get("end", 0),
                "recognizer": ent.get("recognizer", ""),
                "rationale": ent.get("rationale", ""),
            }
        )
    return rows


def _pipeline_cards() -> list[dict[str, str]]:
    try:
        cards = store.list_cards()
    except Exception:
        cards = []
    return [
        {"id": str(getattr(card, "id", "")), "title": str(getattr(card, "title", "Untitled"))}
        for card in cards
        if getattr(card, "id", None)
    ]


def _serialize_session(session: PIISession) -> dict[str, Any]:
    return {
        "id": session.id,
        "title": session.title,
        "operator": session.operator,
        "entities": len(session.entities or []),
        "createdAt": session.created_at,
        "pipelineCardId": session.pipeline_card_id or "",
        "entityCounts": session.entity_counts or {},
        "originalText": session.original_text,
        "anonymizedText": session.anonymized_text,
        "entityRows": _serialize_entity_rows(list(session.entities or [])),
    }


def _list_sessions() -> list[dict[str, Any]]:
    try:
        sessions = store.list_sessions()
    except Exception:
        sessions = []
    return [_serialize_session(session) for session in sessions]


def _save_session(payload: dict[str, Any]) -> PIISession:
    entity_rows = payload.get("entityRows") or []
    entity_counts = payload.get("summary", {}).get("entityCounts") or {}
    if not entity_counts and entity_rows:
        counts = Counter(str(row.get("entityType", "UNKNOWN")) for row in entity_rows)
        entity_counts = dict(counts)
    session = PIISession(
        title=str(payload.get("title") or "Hybrid Analyze Session").strip() or "Hybrid Analyze Session",
        original_text=str(payload.get("sourceText") or ""),
        anonymized_text=str(payload.get("resultText") or ""),
        entities=[
            {
                "entity_type": row.get("entityType", ""),
                "text": row.get("text", ""),
                "score": round(float(row.get("confidence", 0) or 0) / 100.0, 3),
                "start": int(row.get("start", 0) or 0),
                "end": int(row.get("end", 0) or 0),
                "recognizer": row.get("recognizer", ""),
                "rationale": row.get("rationale", ""),
            }
            for row in entity_rows
        ],
        entity_counts=entity_counts,
        operator=str(payload.get("operator") or "replace"),
        source_type="text",
        file_name=str(payload.get("fileName") or "") or None,
        pipeline_card_id=str(payload.get("pipelineCardId") or "") or None,
        processing_ms=float(payload.get("processingMs") or 0.0),
    )
    saved = store.add_session(session)
    card_id = str(payload.get("pipelineCardId") or "").strip()
    if card_id:
        try:
            store.update_card(card_id, session_id=saved.id)
        except Exception:
            pass
    return saved


def _csv_bytes(rows: list[dict[str, Any]]) -> bytes:
    output = io.StringIO()
    writer = csv.DictWriter(
        output,
        fieldnames=["entityType", "text", "confidence", "confidenceBand", "start", "end", "recognizer", "rationale"],
    )
    writer.writeheader()
    for row in rows:
        writer.writerow(row)
    return output.getvalue().encode("utf-8")


def _apply_model_choice(raw_choice: str) -> dict[str, Any]:
    requested = str(raw_choice or "auto").strip() or "auto"
    resolved_model, has_ner, status_text = set_spacy_model(requested)
    return {
        "requested": requested,
        "resolved": resolved_model,
        "hasNer": bool(has_ner),
        "status": status_text,
    }


def _run_detection(form, files, action: str) -> dict[str, Any]:
    text = str(form.get("text", "") or "").strip()
    uploaded_text = _extract_text_from_upload(files.get("file"))
    effective_text = text or uploaded_text
    if not effective_text.strip():
        raise ValueError("Enter text or upload a supported file first.")

    operator = str(form.get("operator", "replace") or "replace").strip().lower()
    if operator not in {"replace", "redact", "mask", "hash", "synthesize"}:
        operator = "replace"

    threshold_raw = form.get("threshold", DEFAULT_THRESHOLD)
    try:
        threshold = float(threshold_raw)
    except Exception:
        threshold = DEFAULT_THRESHOLD
    threshold = min(max(threshold, 0.1), 1.0)

    selected_entities = _normalize_entities(form.getlist("entities"))
    allowlist = _parse_list_text(form.get("allowlist"))
    denylist = _parse_list_text(form.get("denylist"))
    show_rationale = str(form.get("show_rationale", "true")).lower() != "false"
    model_choice = str(form.get("ner_model", "auto") or "auto").strip() or "auto"
    model_result = _apply_model_choice(model_choice)

    if action == "analyze":
        detected = engine.analyze(
            effective_text,
            entities=selected_entities,
            threshold=threshold,
            allowlist=allowlist or None,
            denylist=denylist or None,
        )
        original_segments, result_segments, placeholder_result, final_display_text = _build_linked_segments(
            effective_text, detected, operator
        )
        result_text = placeholder_result
        synth_note = ""
    else:
        op_for_engine = "replace" if operator == "synthesize" else operator
        analysis_result = engine.anonymize(
            effective_text,
            entities=selected_entities,
            operator=op_for_engine,
            threshold=threshold,
            allowlist=allowlist or None,
            denylist=denylist or None,
        )
        detected = list(analysis_result.entities or [])
        synth_note = ""
        final_output = analysis_result.anonymized_text
        if operator == "synthesize":
            synth_cfg = SyntheticConfig(
                provider=str(form.get("synth_provider", "faker") or "faker"),
                model=str(form.get("synth_model", "gpt-4o-mini") or "gpt-4o-mini"),
                api_key=str(form.get("synth_api_key", "") or ""),
                api_base=str(form.get("synth_api_base", "") or ""),
                deployment_id=str(form.get("synth_deployment", "") or ""),
                api_version=str(form.get("synth_api_version", os.environ.get("ANON_SYNTH_API_VERSION", "2024-08-01-preview")) or "2024-08-01-preview"),
                temperature=float(form.get("synth_temperature", 0.2) or 0.2),
                max_tokens=max(128, int(form.get("synth_max_tokens", 800) or 800)),
            )
            synth = synthesize_from_anonymized_text(final_output, synth_cfg)
            final_output = synth.text
            synth_note = synth.message
        original_segments, result_segments, placeholder_result, final_display_text = _build_linked_segments(
            effective_text,
            detected,
            operator,
            synthesized_text=final_output if operator == "synthesize" else None,
        )
        result_text = final_output

    summary = _build_summary(detected)
    entity_rows = _serialize_entity_rows(detected)
    if not show_rationale:
        for row in entity_rows:
            row.pop("recognizer", None)
            row.pop("rationale", None)

    return {
        "ok": True,
        "action": action,
        "sourceText": effective_text,
        "usedUpload": bool(uploaded_text and not text),
        "selectedEntities": selected_entities,
        "operator": operator,
        "summary": summary,
        "entities": entity_rows,
        "originalSegments": original_segments,
        "resultSegments": result_segments,
        "linkedResultText": placeholder_result,
        "resultText": result_text,
        "displayResultText": final_display_text,
        "showRationale": show_rationale,
        "allowlist": allowlist,
        "denylist": denylist,
        "threshold": threshold,
        "model": model_result,
        "synthNote": synth_note,
    }


def create_blueprint(url_prefix: str = DEFAULT_PREFIX) -> Blueprint:
    bp = Blueprint(
        "hybrid_redaction",
        __name__,
        template_folder=str(BASE_DIR / "templates"),
        static_folder=str(BASE_DIR / "static"),
        static_url_path=f"{url_prefix}/static" if url_prefix else "/static",
        url_prefix=url_prefix,
    )


    @bp.get("/main-images/<path:filename>")
    def main_image(filename: str):
        images_dir = PROJECT_ROOT / "images"
        return send_from_directory(images_dir, filename)

    @bp.get("/")
    def home():
        return render_template(
            "hybrid_redaction.html",
            all_entities=list(ALL_ENTITIES),
            default_threshold=DEFAULT_THRESHOLD,
            spacy_model_options=get_spacy_model_options(),
            spacy_status=get_spacy_model_status(),
            synth_provider_options=["faker", "openai", "azure_openai"],
            cards=_pipeline_cards(),
            sessions=_list_sessions(),
            route_prefix=url_prefix,
            main_app_base=(os.environ.get("ANON_MAIN_APP_BASE", "http://127.0.0.1:5000") or "http://127.0.0.1:5000").rstrip("/"),
            hybrid_home=(url_prefix or "") + "/",
        )

    @bp.post("/api/analyze")
    def api_analyze():
        try:
            return jsonify(_run_detection(request.form, request.files, action="analyze"))
        except ValueError as exc:
            return jsonify({"ok": False, "error": str(exc)}), 400
        except Exception as exc:  # pragma: no cover
            return jsonify({"ok": False, "error": f"Analyze failed: {type(exc).__name__}: {exc}"}), 500

    @bp.post("/api/anonymize")
    def api_anonymize():
        try:
            return jsonify(_run_detection(request.form, request.files, action="anonymize"))
        except ValueError as exc:
            return jsonify({"ok": False, "error": str(exc)}), 400
        except Exception as exc:  # pragma: no cover
            return jsonify({"ok": False, "error": f"Anonymize failed: {type(exc).__name__}: {exc}"}), 500

    @bp.get("/api/cards")
    def api_cards():
        return jsonify({"ok": True, "cards": _pipeline_cards()})

    @bp.get("/api/sessions")
    def api_sessions():
        return jsonify({"ok": True, "sessions": _list_sessions()})

    @bp.post("/api/sessions")
    def api_save_session():
        try:
            payload = request.get_json(force=True) or {}
            session = _save_session(payload)
            return jsonify({"ok": True, "session": _serialize_session(session), "sessions": _list_sessions()})
        except Exception as exc:  # pragma: no cover
            return jsonify({"ok": False, "error": f"Save failed: {type(exc).__name__}: {exc}"}), 500

    @bp.get("/api/sessions/<session_id>")
    def api_get_session(session_id: str):
        try:
            session = store.get_session(session_id)
        except Exception:
            session = None
        if not session:
            return jsonify({"ok": False, "error": "Session not found."}), 404
        return jsonify({"ok": True, "session": _serialize_session(session)})

    @bp.get("/api/sessions/<session_id>/download")
    def api_download_session(session_id: str):
        try:
            session = store.get_session(session_id)
        except Exception:
            session = None
        if not session:
            return jsonify({"ok": False, "error": "Session not found."}), 404
        payload = json.dumps(_serialize_session(session), indent=2).encode("utf-8")
        return send_file(
            io.BytesIO(payload),
            mimetype="application/json",
            as_attachment=True,
            download_name=f"session_{session_id}.json",
        )

    @bp.post("/api/download/text")
    def api_download_text():
        data = request.get_json(force=True) or {}
        text = str(data.get("text") or "")
        filename = str(data.get("filename") or "hybrid_anonymized_output.txt")
        return send_file(io.BytesIO(text.encode("utf-8")), mimetype="text/plain", as_attachment=True, download_name=filename)

    @bp.post("/api/download/entities")
    def api_download_entities():
        data = request.get_json(force=True) or {}
        rows = data.get("rows") or []
        payload = _csv_bytes(rows)
        return send_file(io.BytesIO(payload), mimetype="text/csv", as_attachment=True, download_name="hybrid_entity_evidence.csv")

    @bp.post("/api/model")
    def api_set_model():
        payload = request.get_json(force=True) or {}
        choice = str(payload.get("choice") or "auto")
        try:
            return jsonify({"ok": True, "model": _apply_model_choice(choice), "options": get_spacy_model_options()})
        except Exception as exc:  # pragma: no cover
            return jsonify({"ok": False, "error": f"Model change failed: {type(exc).__name__}: {exc}"}), 500

    return bp


def create_app(url_prefix: str = "") -> Flask:
    app = Flask(
        __name__,
        template_folder=str(BASE_DIR / "templates"),
        static_folder=str(BASE_DIR / "static"),
    )
    app.register_blueprint(create_blueprint(url_prefix=url_prefix))
    return app


if __name__ == "__main__":
    app = create_app(url_prefix="")
    app.run(host="127.0.0.1", port=5052, debug=True)
