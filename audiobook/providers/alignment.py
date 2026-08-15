"""Optional forced-alignment boundary for future Qwen3/Charsiu adapters."""

from __future__ import annotations

from pathlib import Path
from typing import Any


class ForcedAligner:
    def align(self, audio_file: str | Path, text: str, language: str = "zh") -> list[dict[str, Any]]:
        raise NotImplementedError


class UnavailableForcedAligner(ForcedAligner):
    """Explicit placeholder so the MVP never silently claims word-level alignment."""

    def align(self, audio_file: str | Path, text: str, language: str = "zh") -> list[dict[str, Any]]:
        raise RuntimeError(
            "MVP 未启用 forced alignment。当前只提供 faster-whisper 的句子级时间定位；"
            "需要更细粒度对轨时，请接入 Qwen3 ForcedAligner 或 Charsiu。"
        )
