"""Small serializable domain models shared by the MVP pipeline."""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any, Optional


@dataclass
class ScriptSegment:
    segment_id: str
    type: str
    speaker: str
    text: str
    emotion: str = "unknown"
    pace: str = "medium"
    pause_before_ms: int = 0
    pause_after_ms: int = 0
    emphasis: list[str] = field(default_factory=list)
    pronunciation_notes: list[str] = field(default_factory=list)
    scene_tags: list[str] = field(default_factory=list)
    sound_tags: list[str] = field(default_factory=list)
    review_required: bool = False
    review_reason: str = ""
    suggestions: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class TranscriptSegment:
    start: float
    end: float
    text: str
    confidence: float = 0.0
    words: list[dict[str, Any]] = field(default_factory=list)
    audio_file: Optional[str] = None

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class Transcript:
    audio_file: str
    language: str
    duration: Optional[float]
    segments: list[TranscriptSegment]

    @property
    def text(self) -> str:
        return "".join(segment.text for segment in self.segments).strip()

    def to_dict(self) -> dict[str, Any]:
        return {
            "audio_file": self.audio_file,
            "language": self.language,
            "duration": self.duration,
            "text": self.text,
            "segments": [segment.to_dict() for segment in self.segments],
        }


@dataclass
class AlignmentItem:
    segment_id: str
    audio_file: Optional[str]
    start: Optional[float]
    end: Optional[float]
    match_type: str
    confidence: float
    status: str
    notes: str = ""

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class ReviewIssue:
    issue_id: str
    segment_id: str
    issue_type: str
    severity: str
    confidence: float
    expected_text: str
    heard_text: str
    suggestion: str
    audio_start: Optional[float] = None
    audio_end: Optional[float] = None
    audio_file: Optional[str] = None
    timecode_status: str = "unavailable"
    needs_human_relisten: bool = True

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)
