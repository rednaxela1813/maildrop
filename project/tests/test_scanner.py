from __future__ import annotations

from datetime import datetime
from pathlib import Path

from maildrop.config import Settings
from maildrop.models import Attachment, MailMessage
from maildrop.scanner import run_scan


class DummySettings(Settings):
    pass


def test_run_scan_saves_supported_attachment_and_returns_summary(
    tmp_path: Path,
    monkeypatch,
) -> None:
    rules_file = tmp_path / "rules.yaml"
    rules_file.write_text(
        """
rules:
  - name: metro_csv_documents
    priority: 10
    enabled: true
    sender_contains:
      - "deilmann.sro@gmail.com"
    subject_contains:
      - "dodaci list"
    filename_contains:
      - "inv_"
    allowed_extensions:
      - ".csv"
    destination: "Mail/Documents/Metro/{yyyy}/{mm}"

fallback:
  destination: "Mail/Unsorted/{yyyy}/{mm}"
""".strip(),
        encoding="utf-8",
    )

    settings = DummySettings(
        IMAP_HOST="mail.example.com",
        IMAP_PORT=993,
        IMAP_USER="user@example.com",
        IMAP_PASSWORD="secret",
        IMAP_MAILBOX="INBOX",
        NEXTCLOUD_MOUNT_PATH=tmp_path / "nextcloud",
        SQLITE_PATH=tmp_path / "maildrop.db",
        RULES_FILE=rules_file,
        LOG_LEVEL="INFO",
        ALLOWED_EXTENSIONS=".pdf,.csv,.xml",
    )

    fake_messages = [
        MailMessage(
            source_id="msg-1",
            subject="Fwd: Elektronicky dodaci list",
            sender="Alexander Kiselev <deilmann.sro@gmail.com>",
            received_at=datetime(2026, 3, 2, 10, 0, 0),
            attachments=[
                Attachment(
                    filename="INV_23201092_2304007430.CSV",
                    content_type="text/csv",
                    content=b"csv-data",
                    size=8,
                )
            ],
        )
    ]

    def fake_fetch_unseen_messages(self):
        return fake_messages

    monkeypatch.setattr(
        "maildrop.imap_client.ImapClient.fetch_unseen_messages",
        fake_fetch_unseen_messages,
    )

    result = run_scan(settings=settings, dry_run=False)

    assert result.messages_seen == 1
    assert result.messages_already_processed == 0
    assert result.messages_marked_processed == 1
    assert result.attachments_total == 1
    assert result.attachments_skipped_unsupported == 0
    assert result.attachments_already_saved == 0
    assert result.attachments_saved == 1

    saved_file = (
        tmp_path
        / "nextcloud"
        / "Mail"
        / "Documents"
        / "Metro"
        / "2026"
        / "03"
        / "2026-03-02_INV_23201092_2304007430.CSV"
    )
    assert saved_file.exists()
    assert saved_file.read_bytes() == b"csv-data"