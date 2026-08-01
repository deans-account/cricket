from __future__ import annotations

import sqlite3
from pathlib import Path


class Database:
    def __init__(self, path: str | Path):
        self.path = Path(path)

    def initialise(self) -> None:
        schema_path = Path(__file__).with_name("schema.sql")
        with sqlite3.connect(self.path) as connection:
            connection.executescript(schema_path.read_text(encoding="utf-8"))
            connection.commit()
