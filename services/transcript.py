from __future__ import annotations

import logging
import os

from dotenv import load_dotenv
from youtube_transcript_api import (
    NoTranscriptAvailable,
    NoTranscriptFound,
    TranscriptsDisabled,
    YouTubeTranscriptApi,
)

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

    provider = (os.getenv("TRANSCRIPT_PROVIDER") or DEFAULT_PROVIDER).lower()
    transcript_language = language or os.getenv("TRANSCRIPT_LANGUAGE") or DEFAULT_LANGUAGE

    if provider != "youtube":
        message = (
            f"Transcript provider '{provider}' is not supported. "
            "Use TRANSCRIPT_PROVIDER=youtube."
        )
        logger.error(message)
        raise TranscriptNotConfiguredError(message)

    try:
        segments = YouTubeTranscriptApi.get_transcript(
            video_id, languages=[transcript_language]
        )
    except (NoTranscriptFound, NoTranscriptAvailable, TranscriptsDisabled) as exc:
        logger.warning("Transcript not available for %s: %s", video_id, exc)
        return ""
    except Exception as exc:  # noqa: BLE001
        logger.error("Transcript fetch failed for %s: %s", video_id, exc)
        raise

    text = " ".join(segment.get("text", "") for segment in segments).strip()
    return text
