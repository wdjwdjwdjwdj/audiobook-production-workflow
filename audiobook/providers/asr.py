"""Lazy faster-whisper adapter and a deterministic mock adapter for tests."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from audiobook.domain.models import Transcript, TranscriptSegment


class ASRProvider:
    def transcribe(self, audio_file: str | Path, language: str = "zh", word_timestamps: bool = True) -> Transcript:
        raise NotImplementedError


class FasterWhisperProvider(ASRProvider):
    def __init__(self, model_size: str = "small", device: str = "cpu", compute_type: str | None = None):
        self.model_size = model_size
        self.device = device
        self.compute_type = compute_type or ("int8" if device == "cpu" else "float16")
        self._model = None

    def _load_model(self):
        if self._model is None:
            try:
                from faster_whisper import WhisperModel
            except ImportError as exc:
                raise RuntimeError("未安装 faster-whisper，请先安装项目依赖。") from exc
            self._model = WhisperModel(self.model_size, device=self.device, compute_type=self.compute_type)
        return self._model

    def transcribe(self, audio_file: str | Path, language: str = "zh", word_timestamps: bool = True) -> Transcript:
        model = self._load_model()
        segments, info = model.transcribe(
            str(audio_file),
            language=language,
            word_timestamps=word_timestamps,
            vad_filter=True,
            beam_size=5,
        )
        output: list[TranscriptSegment] = []
        for segment in segments:
            words: list[dict[str, Any]] = []
            for word in segment.words or []:
                words.append(
                    {
                        "start": float(word.start),
                        "end": float(word.end),
                        "word": word.word,
                        "probability": float(getattr(word, "probability", 0.0) or 0.0),
                    }
                )
            avg_logprob = float(getattr(segment, "avg_logprob", -1.0) or -1.0)
            confidence = max(0.0, min(1.0, 1.0 + avg_logprob / 2.0))
            output.append(
                TranscriptSegment(
                    start=float(segment.start),
                    end=float(segment.end),
                    text=str(segment.text).strip(),
                    confidence=round(confidence, 4),
                    words=words,
                    audio_file=str(audio_file),
                )
            )
        return Transcript(
            audio_file=str(audio_file),
            language=str(getattr(info, "language", language) or language),
            duration=float(getattr(info, "duration", 0.0) or 0.0),
            segments=output,
        )


class MockASRProvider(ASRProvider):
    """Load a transcript fixture keyed by file name for tests and demos."""

    def __init__(self, fixture: dict[str, Any] | str | Path):
        if isinstance(fixture, (str, Path)):
            fixture = json.loads(Path(fixture).read_text(encoding="utf-8"))
        self.fixture = fixture

    def transcribe(self, audio_file: str | Path, language: str = "zh", word_timestamps: bool = True) -> Transcript:
        name = Path(audio_file).name
        payload = self.fixture.get(name, self.fixture.get("default", {}))
        segments = [
            TranscriptSegment(
                start=float(raw.get("start", 0.0)),
                end=float(raw.get("end", 0.0)),
                text=str(raw.get("text", "")),
                confidence=float(raw.get("confidence", 0.95)),
                words=list(raw.get("words", []) or []),
                audio_file=str(audio_file),
            )
            for raw in payload.get("segments", [])
        ]
        return Transcript(
            audio_file=str(audio_file),
            language=payload.get("language", language),
            duration=payload.get("duration"),
            segments=segments,
        )
