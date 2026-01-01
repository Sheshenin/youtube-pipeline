from __future__ import annotations


def is_short_duration(duration: str | None) -> bool:
    """
    YouTube API returns ISO 8601 durations (e.g., PT45S, PT1M05S).
    Business rule: if no 'M' is present, treat it as a Short.
    """
    if not duration:
        return False
    return "M" not in duration
