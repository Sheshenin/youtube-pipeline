import pytest

from services import transcript


def test_extract_video_id_handles_variants():
    watch_url = "https://www.youtube.com/watch?v=abc123&t=10"
    shorts_url = "https://www.youtube.com/shorts/short987?feature=share"
    youtu_be_url = "https://youtu.be/qwerty"

    assert transcript.extract_video_id(watch_url) == "abc123"
    assert transcript.extract_video_id(shorts_url) == "short987"
    assert transcript.extract_video_id(youtu_be_url) == "qwerty"
    assert transcript.extract_video_id("https://example.com/video") == ""


@pytest.mark.skipif(
    not transcript._transcript_dependency_available,  # type: ignore[attr-defined]
    reason="youtube-transcript-api not installed",
)
def test_fetch_transcript_returns_text(monkeypatch):
    called = {}

    def fake_get_transcript(video_id, languages):
        called["video_id"] = video_id
        called["languages"] = languages
        return [
            {"text": "hello"},
            {"text": "world"},
        ]

    monkeypatch.setattr(
        transcript.YouTubeTranscriptApi, "get_transcript", fake_get_transcript
    )

    result = transcript.fetch_transcript("abc123")

    assert "hello" in result
    assert "world" in result
    assert called["video_id"] == "abc123"
    assert "en" in called["languages"]


@pytest.mark.skipif(
    not transcript._transcript_dependency_available,  # type: ignore[attr-defined]
    reason="youtube-transcript-api not installed",
)
def test_fetch_transcript_handles_errors(monkeypatch):
    def raise_error(video_id, languages):
        raise transcript.TranscriptsDisabled(video_id)

    monkeypatch.setattr(
        transcript.YouTubeTranscriptApi, "get_transcript", raise_error
    )

    assert transcript.fetch_transcript("abc123") == ""


@pytest.mark.skipif(
    not transcript._transcript_dependency_available,  # type: ignore[attr-defined]
    reason="youtube-transcript-api not installed",
)
def test_fetch_transcript_handles_network_issue(monkeypatch):
    def raise_error(video_id, languages):
        raise transcript.CouldNotRetrieveTranscript(video_id)

    monkeypatch.setattr(
        transcript.YouTubeTranscriptApi, "get_transcript", raise_error
    )

    assert transcript.fetch_transcript("abc123") == ""
