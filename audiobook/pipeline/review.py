"""Review report generation for short and long audio inputs."""

from __future__ import annotations

from itertools import count
from typing import Any

from audiobook.audio.ffmpeg import analyze_audio_quality
from audiobook.domain.models import AlignmentItem, ReviewIssue, ScriptSegment, Transcript
from audiobook.pipeline.text import classify_difference


def _severity(issue_type: str, confidence: float) -> str:
    if issue_type in {"omission", "cutoff"}:
        return "high"
    if issue_type in {"replacement", "insertion", "reorder"}:
        return "medium" if confidence < 0.8 else "high"
    return "medium"


def build_review_issues(
    script_segments: list[ScriptSegment],
    transcript: Transcript,
    alignments: list[AlignmentItem],
    quality_events: list[dict[str, Any]] | None = None,
) -> list[ReviewIssue]:
    script_by_id = {segment.segment_id: segment for segment in script_segments}
    transcript_by_id: dict[str, str] = {}
    for alignment in alignments:
        if alignment.audio_file:
            transcript_by_id[alignment.segment_id] = transcript.text if len(alignments) == 1 else ""

    issues: list[ReviewIssue] = []
    ids = count(1)
    for alignment in alignments:
        script_segment = script_by_id.get(alignment.segment_id)
        if not script_segment:
            continue
        if len(alignments) == 1:
            heard = transcript.text
        else:
            matching = [
                item
                for item in transcript.segments
                if item.audio_file == alignment.audio_file
                and (
                    alignment.start is None
                    or alignment.end is None
                    or item.end > alignment.start
                    and item.start < alignment.end
                )
            ]
            heard = "".join(item.text for item in matching).strip()
        issue_type, confidence, suggestion = classify_difference(script_segment.text, heard)
        if issue_type:
            issues.append(
                ReviewIssue(
                    issue_id=f"issue_{next(ids):03d}",
                    segment_id=alignment.segment_id,
                    issue_type=issue_type,
                    severity=_severity(issue_type, confidence),
                    confidence=confidence,
                    expected_text=script_segment.text,
                    heard_text=heard,
                    suggestion=suggestion,
                    audio_start=alignment.start,
                    audio_end=alignment.end,
                    audio_file=alignment.audio_file,
                    timecode_status="available" if alignment.start is not None and alignment.end is not None else "unavailable",
                    needs_human_relisten=True,
                )
            )
        if alignment.status in {"missing", "review_required"}:
            issues.append(
                ReviewIssue(
                    issue_id=f"issue_{next(ids):03d}",
                    segment_id=alignment.segment_id,
                    issue_type="segmentation",
                    severity="high" if alignment.status == "missing" else "medium",
                    confidence=round(1.0 - alignment.confidence, 4),
                    expected_text=script_segment.text,
                    heard_text=heard,
                    suggestion=alignment.notes or "请人工确认文本与音频的对应关系。",
                    audio_start=alignment.start,
                    audio_end=alignment.end,
                    audio_file=alignment.audio_file,
                    timecode_status="available" if alignment.start is not None and alignment.end is not None else "unavailable",
                    needs_human_relisten=True,
                )
            )

    for event in quality_events or []:
        issues.append(
            ReviewIssue(
                issue_id=f"issue_{next(ids):03d}",
                segment_id="audio_quality",
                issue_type=str(event.get("issue_type", "other")),
                severity=str(event.get("severity", "medium")),
                confidence=0.8,
                expected_text="",
                heard_text="",
                suggestion=str(event.get("message", "请人工检查音频质量。")),
                audio_start=event.get("audio_start"),
                audio_end=event.get("audio_end"),
                timecode_status="available" if event.get("audio_start") is not None else "unavailable",
                needs_human_relisten=True,
            )
        )
    return issues


def quality_events_for_files(files: list[str]) -> list[dict[str, Any]]:
    events: list[dict[str, Any]] = []
    for file in files:
        for event in analyze_audio_quality(file):
            event["audio_file"] = file
            events.append(event)
    return events
