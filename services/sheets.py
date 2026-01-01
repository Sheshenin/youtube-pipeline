from __future__ import annotations

import logging

logger = logging.getLogger(__name__)


def write_rows(rows: list[dict]) -> None:
    logger.warning("write_rows stub called; rows=%d", len(rows))
