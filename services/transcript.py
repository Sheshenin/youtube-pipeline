from __future__ import annotations

import logging
import os

from dotenv import load_dotenv

logger = logging.getLogger(__name__)
load_dotenv()


class TranscriptNotConfiguredError(RuntimeError):
    """Raised when transcript fetching is not configured."""


def fetch_transcript(video_id: str | None) -> str:
    if not video_id:
        return ""

    provider = os.getenv("TRANSCRIPT_PROVIDER")
    if not provider:
        message = (
            "Transcript provider is not configured. "
            "Set TRANSCRIPT_PROVIDER and related credentials."
        )
        logger.error(message)
        raise TranscriptNotConfiguredError(message)

    logger.warning("Transcript provider '%s' is not implemented yet", provider)
    raise TranscriptNotConfiguredError(
        f"Transcript provider '{provider}' is not implemented yet."
    )
