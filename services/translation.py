from __future__ import annotations

import logging

logger = logging.getLogger(__name__)


def translate_text(text: str, target_language: str) -> str:
    if not text:
        return ""
    logger.warning("translate_text stub called for target=%s", target_language)
    return ""
