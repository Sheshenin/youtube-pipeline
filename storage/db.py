from __future__ import annotations

import sqlite3
from pathlib import Path

DB_PATH = Path("storage/data.db")


def connect() -> sqlite3.Connection:
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    return sqlite3.connect(DB_PATH)
