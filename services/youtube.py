from __future__ import annotations

import logging
import os
from typing import Iterable

import requests
from dotenv import load_dotenv

logger = logging.getLogger(__name__)
load_dotenv()

BASE_URL = "https://www.googleapis.com/youtube/v3"
DEFAULT_TIMEOUT = 20


class MissingYouTubeApiKeyError(RuntimeError):
    """Raised when the YouTube API key is not configured."""


def search_videos(
    query: str,
    region: str,
    language: str,
    published_after: str,
    max_results: int = 50,
) -> list[str]:
    api_key = _require_api_key()

    params = {
        "part": "snippet",
        "q": query,
        "type": "video",
        "maxResults": min(max_results, 50),
        "regionCode": region,
        "relevanceLanguage": language,
        "publishedAfter": published_after,
        "order": "viewCount",
        "videoDuration": "short",
        "key": api_key,
    }

    data = _request("search", params)
    items = data.get("items", []) if data else []
    video_ids = []
    for item in items:
        video_id = (item.get("id") or {}).get("videoId")
        if video_id:
            video_ids.append(video_id)
    return video_ids


def get_video_details(video_ids: Iterable[str]) -> list[dict]:
    ids = [video_id for video_id in video_ids if video_id]
    if not ids:
        return []

    api_key = _require_api_key()

    results: list[dict] = []
    for chunk in _chunked(ids, 50):
        params = {
            "part": "contentDetails,snippet,statistics",
            "id": ",".join(chunk),
            "key": api_key,
        }
        data = _request("videos", params)
        items = data.get("items", []) if data else []
        for item in items:
            snippet = item.get("snippet") or {}
            content = item.get("contentDetails") or {}
            stats = item.get("statistics") or {}
            video_id = item.get("id")
            results.append(
                {
                    "id": video_id,
                    "title": snippet.get("title"),
                    "channel_title": snippet.get("channelTitle"),
                    "channel_id": snippet.get("channelId"),
                    "published_at": snippet.get("publishedAt"),
                    "description": snippet.get("description"),
                    "view_count": stats.get("viewCount"),
                    "duration": content.get("duration"),
                    "url": f"https://www.youtube.com/watch?v={video_id}"
                    if video_id
                    else None,
                }
            )

    return results


def _require_api_key() -> str:
    api_key = os.getenv("YOUTUBE_API_KEY")
    if not api_key:
        message = "Set YOUTUBE_API_KEY in environment or .env"
        logger.error(message)
        raise MissingYouTubeApiKeyError(message)
    return api_key


def _request(endpoint: str, params: dict) -> dict:
    url = f"{BASE_URL}/{endpoint}"
    try:
        response = requests.get(url, params=params, timeout=DEFAULT_TIMEOUT)
        response.raise_for_status()
    except requests.RequestException as exc:
        logger.error("YouTube API error: %s", exc)
        return {}
    return response.json()


def _chunked(items: list[str], size: int) -> list[list[str]]:
    return [items[i : i + size] for i in range(0, len(items), size)]
