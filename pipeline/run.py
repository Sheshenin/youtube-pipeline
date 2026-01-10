from __future__ import annotations

import argparse
import datetime as dt
import logging
from typing import Iterable

from pipeline.config import (
    DEFAULT_DAYS,
    DEFAULT_LANGUAGE,
    DEFAULT_MIN_RESULTS,
    DEFAULT_REGION,
    MAX_SELECTED_SHORTS,
)
from pipeline.shorts import is_short_duration
from services.query_expander import expand_queries, extend_queries
from services.sheets import write_rows
from services.transcript import fetch_transcript
from services.translation import translate_text
from services.youtube import get_video_details, search_videos

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def _published_after(days: int) -> str:
    return (dt.datetime.utcnow() - dt.timedelta(days=days)).isoformat("T") + "Z"


def _dedupe(items: Iterable[dict], key: str) -> list[dict]:
    seen: set[str] = set()
    unique: list[dict] = []
    for item in items:
        value = item.get(key)
        if not value or value in seen:
            continue
        seen.add(value)
        unique.append(item)
    return unique


def _view_count(value: str | None) -> int:
    try:
        return int(value or 0)
    except (TypeError, ValueError):
        return 0


def run_pipeline(
    topic: str,
    language: str = DEFAULT_LANGUAGE,
    region: str = DEFAULT_REGION,
    days: int = DEFAULT_DAYS,
    min_results: int = DEFAULT_MIN_RESULTS,
) -> dict:
    logger.info("Starting pipeline for topic: %s", topic)

    target_count = min(min_results, MAX_SELECTED_SHORTS)
    published_after = _published_after(days)
    queries = expand_queries(topic, language=language)
    results: list[dict] = []
    seen_ids: set[str] = set()

    query_index = 0
    while len(results) < target_count and query_index < len(queries):
        query = queries[query_index]
        query_index += 1

        video_ids = search_videos(
            query=query,
            region=region,
            language=language,
            published_after=published_after,
            max_results=50,
        )
        if not video_ids:
            continue

        details = get_video_details(video_ids)
        for video in details:
            video_id = video.get("id")
            duration = video.get("duration")
            if not video_id or video_id in seen_ids:
                continue
            if not is_short_duration(duration):
                continue
            seen_ids.add(video_id)
            results.append(video)
            if len(results) >= target_count:
                break

        if len(results) >= target_count:
            break

        if len(results) < target_count and query_index >= len(queries):
            queries = extend_queries(topic, existing=queries, language=language)

    results = _dedupe(results, key="id")
    results.sort(key=lambda item: _view_count(item.get("view_count")), reverse=True)
    results = results[:target_count]

    logger.info("Found %d shorts", len(results))

    rows = []
    for video in results:
        transcript = fetch_transcript(video.get("id"))
        translation = translate_text(transcript, target_language="ru")
        row = {
            **video,
            "transcript": transcript,
            "translation": translation,
        }
        rows.append(row)

    write_rows(rows)

    return {
        "topic": topic,
        "query_count": len(queries),
        "shorts_count": len(results),
        "rows_written": len(rows),
        "items": [
            {"url": row.get("url"), "transcript": row.get("transcript")}
            for row in rows
        ],
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="Run the Shorts pipeline.")
    parser.add_argument("--topic", required=True)
    parser.add_argument("--language", default=DEFAULT_LANGUAGE)
    parser.add_argument("--region", default=DEFAULT_REGION)
    parser.add_argument("--days", type=int, default=DEFAULT_DAYS)
    parser.add_argument("--min-results", type=int, default=DEFAULT_MIN_RESULTS)
    args = parser.parse_args()

    result = run_pipeline(
        topic=args.topic,
        language=args.language,
        region=args.region,
        days=args.days,
        min_results=args.min_results,
    )
    logger.info("Pipeline finished: %s", result)


if __name__ == "__main__":
    main()
