from audiobook.domain.models import ScriptSegment, TranscriptSegment
from audiobook.pipeline.alignment import align_long_transcript


def test_long_alignment_preserves_order_and_returns_timecodes():
    script = [
        ScriptSegment("s1", "narration", "旁白", "雨下了一整夜。"),
        ScriptSegment("s2", "dialogue", "林默", "你终于来了。"),
    ]
    transcript = [
        TranscriptSegment(0.0, 2.0, "雨下了一整夜。", 0.95),
        TranscriptSegment(2.1, 4.5, "你终于来了。", 0.95),
    ]
    aligned = align_long_transcript(script, transcript, "chapter.mp3")
    assert [item.segment_id for item in aligned] == ["s1", "s2"]
    assert aligned[0].start == 0.0
    assert aligned[1].end == 4.5
    assert all(item.status == "matched" for item in aligned)
