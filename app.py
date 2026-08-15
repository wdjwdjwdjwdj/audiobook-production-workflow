"""Streamlit entry point for the audiobook production MVP."""

from __future__ import annotations

import json
import os
from pathlib import Path


def _read_uploaded_text(uploaded_file) -> str:
    raw = uploaded_file.getvalue()
    for encoding in ("utf-8-sig", "utf-8", "gb18030"):
        try:
            return raw.decode(encoding)
        except UnicodeDecodeError:
            continue
    raise ValueError("原文文件无法按 UTF-8 或 GB18030 解码。")


def _result_json(result: dict) -> dict:
    return {
        "mode": result["mode"],
        "script": {"segments": [item.to_dict() for item in result["script"]]},
        "transcript": result["transcript"].to_dict(),
        "alignment": {"items": [item.to_dict() for item in result["alignments"]]},
        "review": {"issues": [item.to_dict() for item in result["issues"]]},
    }


def main() -> None:
    import streamlit as st

    from audiobook.report import json_bytes, markdown_report, project_zip, timeline_csv
    from audiobook.storage.session import JobStorage
    from audiobook.workflow import run_review

    st.set_page_config(page_title="有声书生产工作流", page_icon="🎧", layout="wide")
    st.title("有声书生产工作流 MVP")
    st.caption("当前主链路：画本 → 审听 → 对轨结果与审听报告")

    if "job_storage" not in st.session_state:
        st.session_state.job_storage = JobStorage()
    if st.button("清理当前任务"):
        st.session_state.job_storage.clear()
        st.session_state.job_storage = JobStorage()
        st.session_state.pop("result", None)
        st.rerun()

    with st.sidebar:
        st.header("项目设置")
        chapter_id = st.text_input("章节 ID", value="chapter-01")
        mode_label = st.selectbox("音频组织方式", ["自动判断", "一段一个音频", "一章长音频"])
        mode = {"自动判断": "auto", "一段一个音频": "short", "一章长音频": "long"}[mode_label]
        roles = st.text_area("已知角色（可选）", placeholder="林默\n苏晚")
        scene_notes = st.text_area("场景说明（可选）", placeholder="夜晚、雨天、室内")
        st.divider()
        st.caption(f"ASR 模型：{os.getenv('ASR_MODEL', 'small')}")
        st.caption(f"设备：{os.getenv('ASR_DEVICE', 'cpu')}")
        if not os.getenv("LLM_API_KEY"):
            st.info("未配置 LLM_API_KEY，将使用降级画本模式。")

    source = st.file_uploader("上传原文（TXT/Markdown）", type=["txt", "md"])
    audio_files = st.file_uploader(
        "上传音频（MP3/WAV/M4A/FLAC）",
        type=["mp3", "wav", "m4a", "flac"],
        accept_multiple_files=True,
    )

    if st.button("运行画本与审听", type="primary", disabled=not source or not audio_files):
        from audiobook.providers.asr import FasterWhisperProvider

        try:
            source_text = _read_uploaded_text(source)
            saved_audio = [
                st.session_state.job_storage.save_bytes(uploaded.name, uploaded.getvalue())
                for uploaded in audio_files
            ]
            with st.status("正在处理有声书项目…", expanded=True) as status:
                st.write("生成结构化画本…")
                st.write("运行 ASR 和文本比对…")
                result = run_review(
                    source_text=source_text,
                    audio_files=saved_audio,
                    mode=mode,
                    chapter_id=chapter_id,
                    roles=roles,
                    scene_notes=scene_notes,
                    asr=FasterWhisperProvider(
                        model_size=os.getenv("ASR_MODEL", "small"),
                        device=os.getenv("ASR_DEVICE", "cpu"),
                        compute_type=os.getenv("ASR_COMPUTE_TYPE"),
                    ),
                )
                status.update(label="处理完成", state="complete")
            st.session_state.result = result
        except Exception as exc:
            st.error(str(exc))

    result = st.session_state.get("result")
    if not result:
        st.info("上传原文和音频后开始处理。首次运行 ASR 可能需要下载模型。")
        return

    script = result["script"]
    transcript = result["transcript"]
    alignments = result["alignments"]
    issues = result["issues"]
    tabs = st.tabs(["画本结果", "审听结果", "对轨结果", "导出"])

    with tabs[0]:
        st.metric("片段数", len(script))
        st.dataframe([item.to_dict() for item in script], use_container_width=True)

    with tabs[1]:
        st.metric("问题数", len(issues))
        if not issues:
            st.success("未发现自动检测问题；仍建议人工抽听。")
        for issue in issues:
            with st.expander(f"{issue.issue_id} · {issue.severity} · {issue.issue_type} · {issue.segment_id}"):
                st.write(f"原文：{issue.expected_text}")
                st.write(f"ASR：{issue.heard_text or '(未识别到文本)'}")
                st.write(f"建议：{issue.suggestion}")
                if issue.audio_start is not None and issue.audio_end is not None:
                    st.caption(f"时间码：{issue.audio_start:.2f}s - {issue.audio_end:.2f}s")
                if issue.audio_file and Path(issue.audio_file).exists():
                    st.audio(Path(issue.audio_file).read_bytes())

    with tabs[2]:
        st.dataframe([item.to_dict() for item in alignments], use_container_width=True)

    with tabs[3]:
        payload = _result_json(result)
        st.download_button("下载 script.json", json_bytes(payload["script"]), "script.json", "application/json")
        st.download_button("下载 transcript.json", json_bytes(payload["transcript"]), "transcript.json", "application/json")
        st.download_button("下载 alignment.json", json_bytes(payload["alignment"]), "alignment.json", "application/json")
        st.download_button("下载 review.json", json_bytes(payload["review"]), "review.json", "application/json")
        st.download_button("下载 timeline.csv", timeline_csv(alignments), "timeline.csv", "text/csv")
        st.download_button("下载审听报告", markdown_report(issues).encode("utf-8"), "review.md", "text/markdown")
        st.download_button(
            "下载完整项目 ZIP",
            project_zip(script, transcript, alignments, issues),
            "audiobook-project.zip",
            "application/zip",
        )


if __name__ == "__main__":
    main()
