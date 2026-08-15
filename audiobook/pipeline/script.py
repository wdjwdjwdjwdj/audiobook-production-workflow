"""Script annotation with an optional LLM and deterministic fallback."""

from __future__ import annotations

import re

from audiobook.domain.models import ScriptSegment


_SPLIT_RE = re.compile(r"(?<=[。！？!?；;])")
_DIALOGUE_RE = re.compile(r"[“\"「『].*?[”\"」』]", re.S)


def fallback_annotate(text: str, chapter_id: str = "chapter-01") -> list[ScriptSegment]:
    """Create a safe, reviewable script without an LLM key."""

    segments: list[ScriptSegment] = []
    counter = 1
    paragraphs = [paragraph.strip() for paragraph in re.split(r"\n\s*\n", text or "") if paragraph.strip()]
    for paragraph in paragraphs:
        raw_chunks = [chunk.strip() for chunk in _SPLIT_RE.split(paragraph) if chunk.strip()]
        chunks: list[str] = []
        for chunk in raw_chunks:
            if chunks and chunk in {"”", "」", "』", '"'}:
                chunks[-1] += chunk
            else:
                chunks.append(chunk)
        for chunk in chunks:
            is_dialogue = bool(_DIALOGUE_RE.search(chunk)) or chunk.startswith(("“", '"', "「", "『"))
            segments.append(
                ScriptSegment(
                    segment_id=f"{chapter_id}_{counter:03d}",
                    type="dialogue" if is_dialogue else "narration",
                    speaker="unknown" if is_dialogue else "旁白",
                    text=chunk,
                    emotion="unknown",
                    pace="medium",
                    review_required=is_dialogue,
                    review_reason="降级模式无法可靠判断说话人。" if is_dialogue else "",
                )
            )
            counter += 1
    return segments


def normalize_llm_segments(raw_segments: list[dict], chapter_id: str = "chapter-01") -> list[ScriptSegment]:
    result: list[ScriptSegment] = []
    for index, raw in enumerate(raw_segments, start=1):
        text = str(raw.get("text", "")).strip()
        if not text:
            continue
        segment_id = str(raw.get("segment_id") or f"{chapter_id}_{index:03d}")
        speaker = str(raw.get("speaker", "unknown"))
        requires_review = bool(raw.get("review_required", False)) or speaker in {"", "unknown"}
        result.append(
            ScriptSegment(
                segment_id=segment_id,
                type=str(raw.get("type", "narration")),
                speaker=speaker or "unknown",
                text=text,
                emotion=str(raw.get("emotion", "unknown")),
                pace=str(raw.get("pace", "medium")),
                pause_before_ms=int(raw.get("pause_before_ms", 0) or 0),
                pause_after_ms=int(raw.get("pause_after_ms", 0) or 0),
                emphasis=list(raw.get("emphasis", []) or []),
                pronunciation_notes=list(raw.get("pronunciation_notes", []) or []),
                scene_tags=list(raw.get("scene_tags", []) or []),
                sound_tags=list(raw.get("sound_tags", []) or []),
                review_required=requires_review,
                review_reason=str(raw.get("review_reason", ""))
                or ("说话人未能确定。" if requires_review and speaker in {"", "unknown"} else ""),
                suggestions=list(raw.get("suggestions", []) or []),
            )
        )
    if len({segment.segment_id for segment in result}) != len(result):
        raise ValueError("LLM returned duplicate segment_id values")
    return result
