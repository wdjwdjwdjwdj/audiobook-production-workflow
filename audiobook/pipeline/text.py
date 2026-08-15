"""Chinese-friendly text normalization and conservative diffing."""

from __future__ import annotations

import re
import unicodedata
from difflib import SequenceMatcher


_PUNCTUATION = re.compile(r"[\s\u200b\u3000，。！？、：；“”‘’（）【】《》〈〉「」『』—…,.!?;:'\"()\[\]{}<>_~`@#$%^&*+=|\\/\-]+")


def normalize_text(text: str) -> str:
    """Normalize text for comparison while preserving Chinese characters."""

    normalized = unicodedata.normalize("NFKC", text or "").lower()
    return _PUNCTUATION.sub("", normalized)


def similarity(expected: str, heard: str) -> float:
    left = normalize_text(expected)
    right = normalize_text(heard)
    if left == right:
        return 1.0
    if not left and not right:
        return 1.0
    return round(SequenceMatcher(None, left, right).ratio(), 4)


def classify_difference(expected: str, heard: str) -> tuple[str | None, float, str]:
    """Return issue type, issue confidence and a short reviewer suggestion."""

    left = normalize_text(expected)
    right = normalize_text(heard)
    if left == right:
        return None, 1.0, ""
    if left and not right:
        return "omission", 0.99, "音频中没有识别到原文内容，请人工复听并确认是否漏读。"
    if right and not left:
        return "insertion", 0.99, "音频中出现原文之外的内容，请人工确认是否为多读。"

    matcher = SequenceMatcher(None, left, right)
    opcodes = [tag for tag, *_ in matcher.get_opcodes() if tag != "equal"]
    if opcodes and all(tag == "delete" for tag in opcodes):
        issue_type = "omission"
    elif opcodes and all(tag == "insert" for tag in opcodes):
        issue_type = "insertion"
    else:
        issue_type = "replacement"
    confidence = round(max(0.0, min(1.0, 1.0 - matcher.ratio())), 4)
    return issue_type, confidence, "请复听时间码，确认是错读、同义替换还是录音内容需要返工。"
