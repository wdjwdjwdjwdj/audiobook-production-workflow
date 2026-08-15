"""Export helpers for JSON, CSV and Markdown artifacts."""

from __future__ import annotations

import csv
import io
import json
import zipfile
from typing import Any

from audiobook.domain.models import AlignmentItem, ReviewIssue, ScriptSegment, Transcript


def json_bytes(value: Any) -> bytes:
    return json.dumps(value, ensure_ascii=False, indent=2).encode("utf-8")


def markdown_report(issues: list[ReviewIssue], project_title: str = "有声书审听报告") -> str:
    lines = [f"# {project_title}", "", f"问题数量：{len(issues)}", ""]
    if not issues:
        lines.append("未发现文本差异或音频质量问题；仍建议人工抽听确认。")
        return "\n".join(lines) + "\n"
    lines.extend(["| ID | 片段 | 类型 | 严重程度 | 时间码 | 原文 | ASR | 建议 |", "|---|---|---|---|---|---|---|---|"])
    for issue in issues:
        timecode = "-"
        if issue.audio_start is not None and issue.audio_end is not None:
            timecode = f"{issue.audio_start:.2f}s - {issue.audio_end:.2f}s"
        cells = [
            issue.issue_id,
            issue.segment_id,
            issue.issue_type,
            issue.severity,
            timecode,
            issue.expected_text.replace("|", "\\|"),
            issue.heard_text.replace("|", "\\|"),
            issue.suggestion.replace("|", "\\|"),
        ]
        lines.append("| " + " | ".join(cells) + " |")
    return "\n".join(lines) + "\n"


def timeline_csv(alignments: list[AlignmentItem]) -> bytes:
    buffer = io.StringIO()
    writer = csv.DictWriter(buffer, fieldnames=["segment_id", "audio_file", "start", "end", "match_type", "confidence", "status", "notes"])
    writer.writeheader()
    for item in alignments:
        writer.writerow(item.to_dict())
    return buffer.getvalue().encode("utf-8-sig")


def project_zip(
    script: list[ScriptSegment],
    transcript: Transcript,
    alignments: list[AlignmentItem],
    issues: list[ReviewIssue],
    project_title: str = "audiobook-project",
) -> bytes:
    files = {
        "script.json": json_bytes({"title": project_title, "segments": [item.to_dict() for item in script]}),
        "transcript.json": json_bytes(transcript.to_dict()),
        "alignment.json": json_bytes({"items": [item.to_dict() for item in alignments]}),
        "review.json": json_bytes({"issues": [item.to_dict() for item in issues]}),
        "timeline.csv": timeline_csv(alignments),
        "review.md": markdown_report(issues, project_title).encode("utf-8"),
    }
    buffer = io.BytesIO()
    with zipfile.ZipFile(buffer, "w", compression=zipfile.ZIP_DEFLATED) as archive:
        for name, content in files.items():
            archive.writestr(name, content)
    return buffer.getvalue()
