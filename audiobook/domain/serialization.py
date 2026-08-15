"""Serialization helpers for the existing JSON contracts."""

from __future__ import annotations

from typing import Any

from .models import ScriptSegment, Transcript, TranscriptSegment


def script_segments_from_payload(payload: dict[str, Any] | list[dict[str, Any]]) -> list[ScriptSegment]:
    raw_segments = payload if isinstance(payload, list) else payload.get("segments", [])
    if not isinstance(raw_segments, list):
        raise ValueError("script payload must contain a segments list")

    result: list[ScriptSegment] = []
    for raw in raw_segments:
        if not isinstance(raw, dict):
            raise ValueError("each script segment must be an object")
        text = str(raw.get("text", "")).strip()
        segment_id = str(raw.get("segment_id", "")).strip()
        if not segment_id or not text:
            raise ValueError("every script segment requires segment_id and text")
        result.append(
            ScriptSegment(
                segment_id=segment_id,
                type=str(raw.get("type", "narration")),
                speaker=str(raw.get("speaker", "旁白")),
                text=text,
                emotion=str(raw.get("emotion", "unknown")),
                pace=str(raw.get("pace", "medium")),
                pause_before_ms=int(raw.get("pause_before_ms", 0) or 0),
                pause_after_ms=int(raw.get("pause_after_ms", 0) or 0),
                emphasis=list(raw.get("emphasis", []) or []),
                pronunciation_notes=list(raw.get("pronunciation_notes", []) or []),
                scene_tags=list(raw.get("scene_tags", []) or []),
                sound_tags=list(raw.get("sound_tags", []) or []),
                review_required=bool(raw.get("review_required", False)),
                review_reason=str(raw.get("review_reason", "")),
                suggestions=list(raw.get("suggestions", []) or []),
            )
        )
    if len({segment.segment_id for segment in result}) != len(result):
        raise ValueError("segment_id values must be unique")
    return result


def transcript_from_payload(payload: dict[str, Any]) -> Transcript:
    segments = []
    for raw in payload.get("segments", []):
        segments.append(
            TranscriptSegment(
                start=float(raw.get("start", 0.0)),
                end=float(raw.get("end", 0.0)),
                text=str(raw.get("text", "")),
                confidence=float(raw.get("confidence", 0.0)),
                words=list(raw.get("words", []) or []),
                audio_file=raw.get("audio_file"),
            )
        )
    return Transcript(
        audio_file=str(payload.get("audio_file", "")),
        language=str(payload.get("language", "zh")),
        duration=payload.get("duration"),
        segments=segments,
    )
