from __future__ import annotations

from pathlib import Path

from maildrop.config import Settings
from maildrop.health import check_sender_health
from maildrop.state import StateStore


class DummySettings(Settings):
    pass


def test_check_sender_health_filters_monitored_senders_and_marks_stale(tmp_path: Path) -> None:
    db_path = tmp_path / "maildrop.db"
    store = StateStore(db_path)
    store.initialize()

    store.record_sender_seen(
        sender="Alexander Kiselev <deilmann.sro@gmail.com>",
        last_seen_at="2026-04-15T10:00:00",
    )
    store.record_sender_seen(
        sender="Alexander Kiselev <rednaxela1813@gmail.com>",
        last_seen_at="2026-03-01T10:00:00",
    )
    store.record_sender_seen(
        sender='"cPanel on deilmann.sk" <cpanel@deilmann.sk>',
        last_seen_at="2026-04-15T10:00:00",
    )

    settings = DummySettings(
        IMAP_HOST="mail.example.com",
        IMAP_PORT=993,
        IMAP_USER="user@example.com",
        IMAP_PASSWORD="secret",
        IMAP_MAILBOX="INBOX",
        NEXTCLOUD_MOUNT_PATH=tmp_path / "nextcloud",
        SQLITE_PATH=db_path,
        RULES_FILE=tmp_path / "rules.yaml",
        LOG_LEVEL="INFO",
        ALLOWED_EXTENSIONS=".pdf,.csv,.xml",
        MONITORED_SENDERS=(
            "Alexander Kiselev <deilmann.sro@gmail.com>,"
            "Alexander Kiselev <rednaxela1813@gmail.com>"
        ),
    )

    result = check_sender_health(settings=settings, max_age_days=7)

    assert len(result) == 2
    assert result[0].sender == "Alexander Kiselev <deilmann.sro@gmail.com>"
    assert result[1].sender == "Alexander Kiselev <rednaxela1813@gmail.com>"

    # rednaxela sender should definitely be stale relative to current date
    assert result[1].is_stale is True