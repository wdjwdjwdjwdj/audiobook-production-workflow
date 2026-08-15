"""Order-preserving sentence-level alignment for the MVP."""

from __future__ import annotations

from pathlib import Path
from typing import Iterable

from audiobook.audio.ffmpeg import probe_duration
from audiobook.domain.models import AlignmentItem, ScriptSegment, TranscriptSegment
from audiobook.pipeline.text import similarity


def _best_window(expected: str, transcript: list[TranscriptSegment], start_index: int, max_window: int = 5):
    if start_index >= len(transcript):
        return None
    best = None
    for width in range(1, min(max_window, len(transcript) - start_index) + 1):
        window = transcript[start_index : start_index + width]
        heard = "".join(item.text for item in window)
        score = similarity(expected, heard)
        candidate = (score, width, window)
        if best is None or candidate[0] > best[0]:
            best = candidate
    return best


def align_long_transcript(
    script_segments: Iterable[ScriptSegment], transcript_segments: list[TranscriptSegment], audio_file: str
) -> list[AlignmentItem]:
    """Map ordered script segments to contiguous ASR windows."""

    result: list[AlignmentItem] = []
    cursor = 0
    for script_segment in script_segments:
        candidate = _best_window(script_segment.text, transcript_segments, cursor)
        if candidate is None:
            result.append(
                AlignmentItem(
                    segment_id=script_segment.segment_id,
                    audio_file=audio_file,
                    start=None,
                    end=None,
                    match_type="asr_alignment",
                    confidence=0.0,
                    status="missing",
                    notes="没有剩余 ASR 片段可供匹配。",
                )
            )
            continue

        score, width, window = candidate
        cursor += width
        status = "matched" if score >= 0.65 else "review_required"
        result.append(
            AlignmentItem(
                segment_id=script_segment.segment_id,
                audio_file=audio_file,
                start=window[0].start,
                end=window[-1].end,
                match_type="asr_alignment",
                confidence=score,
                status=status,
                notes="句子级顺序匹配；低分结果必须人工复核。" if status != "matched" else "",
            )
        )
    return result


def align_short_files(
    script_segments: list[ScriptSegment], audio_files: list[str | Path]
) -> list[AlignmentItem]:
    """Map one-file-per-segment audio using stable IDs, then deterministic order."""

    paths = [Path(path) for path in audio_files]
    by_id = {path.stem: path for path in paths}
    result: list[AlignmentItem] = []
    for index, segment in enumerate(script_segments):
        path = by_id.get(segment.segment_id)
        match_type = "metadata"
        if path is None and index < len(paths):
            path = paths[index]
            match_type = "manual"
        if path is None:
            result.append(
                AlignmentItem(
                    segment_id=segment.segment_id,
                    audio_file=None,
                    start=None,
                    end=None,
                    match_type="metadata",
                    confidence=0.0,
                    status="missing",
                    notes="没有找到对应音频文件。",
                )
            )
            continue
        duration = probe_duration(path)
        result.append(
            AlignmentItem(
                segment_id=segment.segment_id,
                audio_file=str(path),
                start=0.0 if duration is not None else None,
                end=duration,
                match_type=match_type,
                confidence=0.99 if match_type == "metadata" else 0.75,
                status="matched" if duration is not None else "review_required",
                notes="按上传顺序匹配，请确认文件名与原文顺序。" if match_type == "manual" else "",
            )
        )
    return result
