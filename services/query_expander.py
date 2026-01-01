from __future__ import annotations


def expand_queries(topic: str, language: str) -> list[str]:
    base = topic.strip()
    variants = [
        base,
        f"{base} shorts",
        f"{base} tips",
        f"{base} tutorial",
        f"{base} how to",
        f"{base} quick guide",
        f"{base} highlights",
        f"{base} examples",
    ]
    return _dedupe([v for v in variants if v])


def extend_queries(topic: str, existing: list[str], language: str) -> list[str]:
    base = topic.strip()
    extra = [
        f"{base} beginner",
        f"{base} advanced",
        f"{base} mistakes",
        f"{base} checklist",
        f"{base} 2024",
        f"{base} 2025",
    ]
    merged = existing + extra
    return _dedupe([v for v in merged if v])


def _dedupe(items: list[str]) -> list[str]:
    seen: set[str] = set()
    unique: list[str] = []
    for item in items:
        if item in seen:
            continue
        seen.add(item)
        unique.append(item)
    return unique
