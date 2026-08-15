"""Small FFmpeg/FFprobe wrappers used by the MVP."""

from __future__ import annotations

import json
import os
import re
import shutil
import subprocess
from pathlib import Path
from typing import Any


def _binary(name: str) -> str:
    value = shutil.which(name)
    if not value:
        raise RuntimeError(f"未找到 {name}，请安装 FFmpeg 并确保它在 PATH 中。")
    return value


def probe_duration(audio_file: str | Path) -> float | None:
    """Return duration in seconds, or None when probing fails."""

    try:
        result = subprocess.run(
            [
                _binary("ffprobe"),
                "-v",
                "error",
                "-show_entries",
                "format=duration",
                "-of",
                "json",
                str(audio_file),
            ],
            check=True,
            capture_output=True,
            text=True,
        )
        duration = json.loads(result.stdout)["format"]["duration"]
        return round(float(duration), 3)
    except (RuntimeError, subprocess.SubprocessError, KeyError, ValueError, json.JSONDecodeError):
        return None


def analyze_audio_quality(audio_file: str | Path) -> list[dict[str, Any]]:
    """Run conservative silence/clipping checks without changing the source file."""

    issues: list[dict[str, Any]] = []
    try:
        ffmpeg = _binary("ffmpeg")
    except RuntimeError as exc:
        return [{"issue_type": "tooling", "severity": "high", "message": str(exc)}]

    command = [
        ffmpeg,
        "-hide_banner",
        "-i",
        str(audio_file),
        "-af",
        "silencedetect=noise=-45dB:d=1,volumedetect",
        "-f",
        "null",
        "-",
    ]
    try:
        result = subprocess.run(command, capture_output=True, text=True, check=False)
    except OSError as exc:
        return [{"issue_type": "tooling", "severity": "high", "message": str(exc)}]

    output = f"{result.stdout}\n{result.stderr}"
    if result.returncode != 0:
        return [
            {
                "issue_type": "tooling",
                "severity": "high",
                "message": "FFmpeg 无法读取该音频或缺少所需音频滤镜；请检查音频格式和 FFmpeg 安装。",
            }
        ]
    silence_starts = re.findall(r"silence_start:\s*([0-9.]+)", output)
    silence_ends = re.findall(r"silence_end:\s*([0-9.]+)", output)
    for index, start in enumerate(silence_starts):
        end = silence_ends[index] if index < len(silence_ends) else None
        duration = float(end) - float(start) if end else None
        if duration is not None and duration >= 3.0:
            issues.append(
                {
                    "issue_type": "silence",
                    "severity": "medium",
                    "audio_start": float(start),
                    "audio_end": float(end),
                    "message": f"检测到约 {duration:.1f} 秒静音。",
                }
            )
    max_volume = re.search(r"max_volume:\s*(-?inf|[-0-9.]+) dB", output)
    if max_volume and max_volume.group(1) != "-inf" and float(max_volume.group(1)) >= -0.1:
        issues.append(
            {
                "issue_type": "clipping",
                "severity": "high",
                "message": "峰值接近 0 dB，可能存在削波风险。",
            }
        )
    return issues
