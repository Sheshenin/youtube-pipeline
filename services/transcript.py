from __future__ import annotations

import logging

logger = logging.getLogger(__name__)


def fetch_transcript(video_id: str | None) -> str:
    if not video_id:
        return ""
    logger.warning("fetch_transcript stub called for %s", video_id)
    return ""
