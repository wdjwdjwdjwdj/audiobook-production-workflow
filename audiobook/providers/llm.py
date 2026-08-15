"""Minimal OpenAI-compatible chat adapter with no vendor lock-in."""

from __future__ import annotations

import json
import os
import re
import urllib.error
import urllib.request
from typing import Any

from dotenv import load_dotenv

from audiobook.pipeline.script import fallback_annotate, normalize_llm_segments


class LLMProvider:
    def annotate_script(self, text: str, chapter_id: str = "chapter-01", roles: str = "", scene_notes: str = ""):
        raise NotImplementedError


class OpenAICompatibleLLM(LLMProvider):
    def __init__(self, base_url: str, api_key: str, model: str, timeout: int = 120):
        self.base_url = base_url.rstrip("/")
        self.api_key = api_key
        self.model = model
        self.timeout = timeout

    @property
    def enabled(self) -> bool:
        return bool(self.api_key and self.base_url and self.model)

    def annotate_script(self, text: str, chapter_id: str = "chapter-01", roles: str = "", scene_notes: str = ""):
        if not self.enabled:
            return fallback_annotate(text, chapter_id)

        system_prompt = (
            "你是有声书画本编辑。只输出 JSON，不要 Markdown。"
            "将原文拆成配音片段，区分旁白和角色，保留原文，不改写内容。"
            "无法确定的说话人必须使用 unknown 并设置 review_required=true。"
            "JSON 格式为 {segments:[{segment_id,type,speaker,text,emotion,pace,"
            "pause_before_ms,pause_after_ms,review_required,review_reason}]}。"
        )
        user_prompt = f"章节 ID：{chapter_id}\n已知角色：{roles or '无'}\n场景说明：{scene_notes or '无'}\n原文：\n{text}"
        payload = {
            "model": self.model,
            "temperature": 0.1,
            "response_format": {"type": "json_object"},
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
        }
        request = urllib.request.Request(
            f"{self.base_url}/chat/completions",
            data=json.dumps(payload, ensure_ascii=False).encode("utf-8"),
            headers={
                "Content-Type": "application/json",
                "Authorization": f"Bearer {self.api_key}",
            },
            method="POST",
        )
        try:
            with urllib.request.urlopen(request, timeout=self.timeout) as response:
                body = json.loads(response.read().decode("utf-8"))
            content = body["choices"][0]["message"]["content"]
            return normalize_llm_segments(_extract_json(content).get("segments", []), chapter_id)
        except (urllib.error.URLError, TimeoutError, KeyError, IndexError, json.JSONDecodeError, ValueError) as exc:
            raise RuntimeError(f"LLM 画本失败：{exc}") from exc


def _extract_json(content: str) -> dict[str, Any]:
    cleaned = content.strip()
    cleaned = re.sub(r"^```(?:json)?\s*", "", cleaned, flags=re.I)
    cleaned = re.sub(r"\s*```$", "", cleaned)
    parsed = json.loads(cleaned)
    if not isinstance(parsed, dict):
        raise ValueError("LLM response must be a JSON object")
    return parsed


def provider_from_env() -> OpenAICompatibleLLM:
    load_dotenv()
    return OpenAICompatibleLLM(
        base_url=os.getenv("LLM_BASE_URL", "https://api.openai.com/v1"),
        api_key=os.getenv("LLM_API_KEY", ""),
        model=os.getenv("LLM_MODEL", "gpt-4o-mini"),
    )
