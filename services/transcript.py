from __future__ import annotations

import logging
import os

import requests
from dotenv import load_dotenv

logger = logging.getLogger(__name__)
load_dotenv()

BASE_URL = "https://api.supadata.ai/v1/transcript"
DEFAULT_TIMEOUT = 30


class MissingTranscriptApiKeyError(RuntimeError):
    """Raised when the transcript API key is not configured."""


def fetch_transcript(video_id: str | None) -> str:
    if not video_id:
        return ""

    api_key = _require_api_key()
    params = {"url": f"https://youtu.be/{video_id}"}
    headers = {"x-api-key": api_key}

    data = _request(params=params, headers=headers)
    transcript = _extract_transcript(data)
    if not transcript:
        logger.warning("No transcript returned for video %s", video_id)
    return transcript


def _require_api_key() -> str:
    api_key = os.getenv("SUPADATA_API_KEY")
    if not api_key:
        message = "Set SUPADATA_API_KEY in environment or .env"
        logger.error(message)
        raise MissingTranscriptApiKeyError(message)
    return api_key


def _request(params: dict, headers: dict) -> dict:
    try:
        response = requests.get(
            BASE_URL,
            params=params,
            headers=headers,
            timeout=DEFAULT_TIMEOUT,
        )
        response.raise_for_status()
    except requests.RequestException as exc:
        logger.error("Transcript API error: %s", exc)
        return {}
    return response.json()


def _extract_transcript(payload: dict) -> str:
    if not payload:
        return ""

    if isinstance(payload.get("text"), str):
        return payload["text"].strip()
    if isinstance(payload.get("transcript"), str):
        return payload["transcript"].strip()

    data = payload.get("data") or {}
    for key in ("text", "transcript", "content", "transcription"):
        value = data.get(key)
        if isinstance(value, str):
            return value.strip()

    segments = data.get("segments") or payload.get("segments")
    if isinstance(segments, list):
        parts = [
            segment.get("text")
            for segment in segments
            if isinstance(segment, dict) and segment.get("text")
        ]
        return " ".join(parts).strip()

    return ""
