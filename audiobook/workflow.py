"""End-to-end orchestration for the MVP review path."""

from __future__ import annotations

from pathlib import Path

from audiobook.domain.models import Transcript
from audiobook.pipeline.alignment import align_long_transcript, align_short_files
from audiobook.pipeline.review import build_review_issues, quality_events_for_files
from audiobook.providers.asr import ASRProvider, FasterWhisperProvider
from audiobook.providers.llm import LLMProvider, provider_from_env


def run_review(
    source_text: str,
    audio_files: list[str | Path],
    mode: str = "auto",
    chapter_id: str = "chapter-01",
    roles: str = "",
    scene_notes: str = "",
    llm: LLMProvider | None = None,
    asr: ASRProvider | None = None,
) -> dict:
    if not source_text.strip():
        raise ValueError("原文不能为空。")
    if not audio_files:
        raise ValueError("至少需要上传一个音频文件。")

    script = (llm or provider_from_env()).annotate_script(source_text, chapter_id, roles, scene_notes)
    if not script:
        raise ValueError("没有从原文生成可审听的片段。")

    selected_mode = mode
    if selected_mode == "auto":
        selected_mode = "short" if len(audio_files) == len(script) and len(audio_files) > 1 else "long"

    asr_provider = asr or FasterWhisperProvider()
    if selected_mode == "short":
        alignments = align_short_files(script, audio_files)
        transcript_segments = []
        for audio_file in audio_files:
            transcript_segments.extend(asr_provider.transcribe(audio_file).segments)
        transcript = Transcript(
            audio_file="multiple",
            language="zh",
            duration=None,
            segments=transcript_segments,
        )
    elif selected_mode == "long":
        if len(audio_files) != 1:
            raise ValueError("长音频模式只接受一个音频文件。")
        transcript = asr_provider.transcribe(audio_files[0])
        alignments = align_long_transcript(script, transcript.segments, str(audio_files[0]))
    else:
        raise ValueError(f"不支持的处理模式：{mode}")

    quality_events = quality_events_for_files([str(item) for item in audio_files])
    issues = build_review_issues(script, transcript, alignments, quality_events)
    return {
        "mode": selected_mode,
        "script": script,
        "transcript": transcript,
        "alignments": alignments,
        "issues": issues,
        "quality_events": quality_events,
    }
