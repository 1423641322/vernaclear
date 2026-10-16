from __future__ import annotations

import sqlite3
from pathlib import Path

from vernaclear.core.models import GlossaryEntry, TranslationResult
from vernaclear.core.paths import data_dir


class Database:
    def __init__(self, path: Path | None = None) -> None:
        self.path = path or data_dir() / "vernaclear.db"
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self._initialize()

    def _connect(self) -> sqlite3.Connection:
        connection = sqlite3.connect(self.path)
        connection.row_factory = sqlite3.Row
        return connection

    def _initialize(self) -> None:
        with self._connect() as connection:
            connection.executescript(
                """
                CREATE TABLE IF NOT EXISTS history (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                    original TEXT NOT NULL,
                    translated TEXT NOT NULL,
                    provider TEXT NOT NULL,
                    mode TEXT NOT NULL
                );
                CREATE TABLE IF NOT EXISTS personal_glossary (
                    term TEXT PRIMARY KEY COLLATE NOCASE,
                    expansion TEXT NOT NULL,
                    language TEXT NOT NULL DEFAULT 'und',
                    category TEXT NOT NULL DEFAULT 'personal',
                    note TEXT NOT NULL DEFAULT ''
                );
                """
            )

    def add_history(self, result: TranslationResult) -> None:
        with self._connect() as connection:
            connection.execute(
                "INSERT INTO history(original, translated, provider, mode) VALUES (?, ?, ?, ?)",
                (result.original, result.translated, result.provider, result.mode_used.value),
            )
            connection.execute(
                "DELETE FROM history WHERE id NOT IN (SELECT id FROM history ORDER BY id DESC LIMIT 500)"
            )

    def recent_context(self, limit: int = 8) -> list[str]:
        with self._connect() as connection:
            rows = connection.execute(
                "SELECT original FROM history ORDER BY id DESC LIMIT ?", (max(0, limit),)
            ).fetchall()
        return [row["original"] for row in reversed(rows)]

    def recent_history(self, limit: int = 50) -> list[sqlite3.Row]:
        with self._connect() as connection:
            return connection.execute(
                "SELECT * FROM history ORDER BY id DESC LIMIT ?", (limit,)
            ).fetchall()

    def clear_history(self) -> None:
        with self._connect() as connection:
            connection.execute("DELETE FROM history")

    def glossary_entries(self) -> list[GlossaryEntry]:
        with self._connect() as connection:
            rows = connection.execute(
                "SELECT term, expansion, language, category, note FROM personal_glossary ORDER BY term"
            ).fetchall()
        return [GlossaryEntry(**dict(row)) for row in rows]

    def save_glossary_entry(self, entry: GlossaryEntry) -> None:
        with self._connect() as connection:
            connection.execute(
                """INSERT INTO personal_glossary(term, expansion, language, category, note)
                VALUES (?, ?, ?, ?, ?)
                ON CONFLICT(term) DO UPDATE SET expansion=excluded.expansion,
                    language=excluded.language, category=excluded.category, note=excluded.note""",
                (entry.term, entry.expansion, entry.language, entry.category, entry.note),
            )

    def delete_glossary_entry(self, term: str) -> None:
        with self._connect() as connection:
            connection.execute("DELETE FROM personal_glossary WHERE term = ?", (term,))

