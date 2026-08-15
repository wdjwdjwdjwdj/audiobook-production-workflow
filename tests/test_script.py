from audiobook.pipeline.script import fallback_annotate


def test_fallback_script_has_stable_ids_and_marks_unknown_dialogue():
    segments = fallback_annotate("雨下了一整夜。\n\n“你终于来了。”", "chapter-02")
    assert [segment.segment_id for segment in segments] == ["chapter-02_001", "chapter-02_002"]
    assert segments[0].speaker == "旁白"
    assert segments[1].review_required is True
