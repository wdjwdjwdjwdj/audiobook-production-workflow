from audiobook.domain.models import AlignmentItem, ScriptSegment, Transcript, TranscriptSegment
from audiobook.pipeline.review import build_review_issues


def test_review_reports_omission_with_timecode():
    script = [ScriptSegment("s1", "narration", "旁白", "他没有回答。")]
    transcript = Transcript("chapter.mp3", "zh", 2.0, [TranscriptSegment(0.5, 1.5, "")])
    alignment = [AlignmentItem("s1", "chapter.mp3", 0.5, 1.5, "asr_alignment", 0.9, "matched")]
    issues = build_review_issues(script, transcript, alignment)
    assert issues[0].issue_type == "omission"
    assert issues[0].audio_start == 0.5
