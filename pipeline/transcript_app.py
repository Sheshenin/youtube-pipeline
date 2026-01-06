from __future__ import annotations

import argparse
import logging
import os

from services.transcript import extract_video_id, fetch_transcript

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def run(url: str) -> str:
    video_id = extract_video_id(url)
    if not video_id:
        logger.error("Could not extract video id from: %s", url)
        return ""

    transcript = fetch_transcript(video_id)
    if not transcript:
        logger.warning("Transcript is empty for video: %s", video_id)
    return transcript


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Fetch and print transcript for a YouTube video."
    )
    parser.add_argument(
        "--url",
        help="YouTube video URL. If omitted, VIDEO_URL environment variable is used.",
        default=os.getenv("VIDEO_URL"),
    )
    args = parser.parse_args()

    if not args.url:
        parser.error("Provide --url or set VIDEO_URL.")

    transcript = run(args.url)
    if transcript:
        print(transcript)


if __name__ == "__main__":
    main()
