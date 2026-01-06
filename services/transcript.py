from __future__ import annotations

import logging
import os
from typing import Any

import requests
from dotenv import load_dotenv

logger = logging.getLogger(__name__)
load_dotenv()

BASE_URL = "https://www.googleapis.com/youtube/v3"
DEFAULT_TIMEOUT = 20


def fetch_transcript(video_id: str | None, language: str | None = None) -> str:
    if not video_id:
        return ""

    token = os.getenv("YOUTUBE_OAUTH_TOKEN")
    if not token:
        logger.warning("YOUTUBE_OAUTH_TOKEN not set; skipping transcript fetch")
        return ""

    caption_id = _find_caption_id(video_id, token=token, language=language)
    if not caption_id:
        logger.info("No captions found for %s", video_id)
        return ""

    text = _download_caption(caption_id, token=token)
    if text:
        logger.info("Fetched captions for %s", video_id)
    return text


def _find_caption_id(video_id: str, token: str, language: str | None) -> str | None:
    params = {
        "part": "snippet",
        "videoId": video_id,
    }
    headers = {"Authorization": f"Bearer {token}"}
    try:
        response = requests.get(
            f"{BASE_URL}/captions", params=params, headers=headers, timeout=DEFAULT_TIMEOUT
        )
        response.raise_for_status()
    except requests.RequestException as exc:
        logger.error("YouTube captions.list error for %s: %s", video_id, exc)
        return None

    items: list[dict[str, Any]] = response.json().get("items", [])
    if not items:
        return None

    if language:
        for item in items:
            snippet = item.get("snippet") or {}
            if snippet.get("language") == language:
                return item.get("id")

    return items[0].get("id")


def _download_caption(caption_id: str, token: str) -> str:
    if not caption_id:
        return ""
    headers = {
        "Authorization": f"Bearer {token}",
        "Accept": "text/plain",
    }
    params = {"tfmt": "ttml", "alt": "media"}
    try:
        response = requests.get(
            f"{BASE_URL}/captions/{caption_id}", params=params, headers=headers, timeout=DEFAULT_TIMEOUT
        )
        response.raise_for_status()
    except requests.RequestException as exc:
        logger.error("YouTube captions.download error for %s: %s", caption_id, exc)
        return ""

    return response.text or ""
