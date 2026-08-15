from audiobook.pipeline.text import classify_difference, normalize_text, similarity


def test_normalize_text_removes_chinese_punctuation_and_spaces():
    assert normalize_text(" 你终于来了。 ") == "你终于来了"


def test_exact_text_has_no_issue():
    issue_type, confidence, _ = classify_difference("你终于来了。", "你终于来了")
    assert issue_type is None
    assert confidence == 1.0


def test_missing_text_is_omission():
    issue_type, confidence, _ = classify_difference("他没有回答。", "")
    assert issue_type == "omission"
    assert confidence > 0.9


def test_replacement_is_detected():
    issue_type, _, _ = classify_difference("你终于来了。", "你总算来了。")
    assert issue_type == "replacement"


def test_similarity_is_bounded():
    assert 0.0 <= similarity("甲", "乙") <= 1.0
