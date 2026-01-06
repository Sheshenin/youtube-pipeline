from __future__ import annotations

import logging
import re
from urllib.parse import parse_qs, urlparse

try:
    from youtube_transcript_api import (
        CouldNotRetrieveTranscript,
        NoTranscriptFound,
        TranscriptsDisabled,
        YouTubeTranscriptApi,
    )

    _transcript_dependency_available = True
except ImportError:  # pragma: no cover - allow degraded mode without dependency
    _transcript_dependency_available = False

    class TranscriptsDisabled(Exception):
        pass

    class NoTranscriptFound(Exception):
        pass

    class CouldNotRetrieveTranscript(Exception):
        pass

    class _MissingTranscriptApi:
        def __getattr__(self, _name):
            raise ImportError("youtube-transcript-api is not installed")

    YouTubeTranscriptApi = _MissingTranscriptApi()  # type: ignore[assignment]

logger = logging.getLogger(__name__)
load_dotenv()

DEFAULT_PROVIDER = "youtube"
DEFAULT_LANGUAGE = "en"


class TranscriptNotConfiguredError(RuntimeError):
    """Raised when transcript fetching is not configured."""


def fetch_transcript(video_id: str | None, language: str | None = None) -> str:
    """
    Fetch a transcript for the given video.

    Provider selection is driven by TRANSCRIPT_PROVIDER env var (default: youtube).
    Language defaults to TRANSCRIPT_LANGUAGE or 'en'.
    """
    if not video_id:
        return ""

    if not _transcript_dependency_available:
        logger.error(
            "youtube-transcript-api is not installed; cannot fetch transcript."
        )
        return ""

    try:
        transcript_data = YouTubeTranscriptApi.get_transcript(
            video_id, languages=["en", "en-US", "ru", "uk"]
        )
    except (TranscriptsDisabled, NoTranscriptFound, CouldNotRetrieveTranscript) as exc:
        logger.warning("Transcript unavailable for %s: %s", video_id, exc)
        return ""
    except Exception as exc:  # pragma: no cover - defensive logging
        logger.error("Unexpected transcript error for %s: %s", video_id, exc)
        return ""

    parts = [item.get("text", "").strip() for item in transcript_data]
    return "\n".join(part for part in parts if part)


def extract_video_id(video_url: str | None) -> str:
    if not video_url:
        return ""

    parsed = urlparse(video_url)
    if parsed.netloc.endswith("youtu.be"):
        return parsed.path.lstrip("/").split("/")[0]

    if "youtube.com" in parsed.netloc:
        query = parse_qs(parsed.query)
        video_id = query.get("v", [""])[0]
        if video_id:
            return video_id

        path_match = re.search(r"/shorts/([^/?]+)", parsed.path)
        if path_match:
            return path_match.group(1)

    return ""
