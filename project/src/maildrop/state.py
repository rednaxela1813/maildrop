from __future__ import annotations

import sqlite3
from pathlib import Path


class StateStore:
    def __init__(self, db_path: Path) -> None:
        self.db_path = db_path

    def initialize(self) -> None:
        self.db_path.parent.mkdir(parents=True, exist_ok=True)

        with sqlite3.connect(self.db_path) as connection:
            connection.execute(
                """
                CREATE TABLE IF NOT EXISTS processed_messages (
                    source_id TEXT PRIMARY KEY,
                    processed_at TEXT NOT NULL
                )
                """
            )
            connection.execute(
                """
                CREATE TABLE IF NOT EXISTS delivered_attachments (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    message_id TEXT NOT NULL,
                    attachment_name TEXT NOT NULL,
                    checksum TEXT NOT NULL,
                    destination_path TEXT NOT NULL,
                    rule_name TEXT,
                    saved_at TEXT NOT NULL,
                    UNIQUE(checksum, destination_path)
                )
                """
            )
            connection.execute(
                """
                CREATE TABLE IF NOT EXISTS sender_last_seen (
                    sender TEXT PRIMARY KEY,
                    last_seen_at TEXT NOT NULL
                )
                """
            )
            connection.commit()

    def is_message_processed(self, source_id: str) -> bool:
        with sqlite3.connect(self.db_path) as connection:
            cursor = connection.execute(
                """
                SELECT 1
                FROM processed_messages
                WHERE source_id = ?
                LIMIT 1
                """,
                (source_id,),
            )
            row = cursor.fetchone()
            return row is not None

    def record_message_processed(self, source_id: str, processed_at: str) -> None:
        with sqlite3.connect(self.db_path) as connection:
            connection.execute(
                """
                INSERT OR IGNORE INTO processed_messages (source_id, processed_at)
                VALUES (?, ?)
                """,
                (source_id, processed_at),
            )
            connection.commit()

    def is_attachment_saved(self, checksum: str, destination_path: str) -> bool:
        with sqlite3.connect(self.db_path) as connection:
            cursor = connection.execute(
                """
                SELECT 1
                FROM delivered_attachments
                WHERE checksum = ? AND destination_path = ?
                LIMIT 1
                """,
                (checksum, destination_path),
            )
            row = cursor.fetchone()
            return row is not None

    def record_attachment_saved(
        self,
        message_id: str,
        attachment_name: str,
        checksum: str,
        destination_path: str,
        rule_name: str | None,
        saved_at: str,
    ) -> None:
        with sqlite3.connect(self.db_path) as connection:
            connection.execute(
                """
                INSERT OR IGNORE INTO delivered_attachments (
                    message_id,
                    attachment_name,
                    checksum,
                    destination_path,
                    rule_name,
                    saved_at
                )
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                (
                    message_id,
                    attachment_name,
                    checksum,
                    destination_path,
                    rule_name,
                    saved_at,
                ),
            )
            connection.commit()

    def record_sender_seen(self, sender: str, last_seen_at: str) -> None:
        with sqlite3.connect(self.db_path) as connection:
            connection.execute(
                """
                INSERT INTO sender_last_seen (sender, last_seen_at)
                VALUES (?, ?)
                ON CONFLICT(sender) DO UPDATE SET last_seen_at = excluded.last_seen_at
                """,
                (sender, last_seen_at),
            )
            connection.commit()

    def list_sender_last_seen(self) -> list[tuple[str, str]]:
        with sqlite3.connect(self.db_path) as connection:
            cursor = connection.execute(
                """
                SELECT sender, last_seen_at
                FROM sender_last_seen
                ORDER BY sender ASC
                """
            )
            rows = cursor.fetchall()
            return [(row[0], row[1]) for row in rows]