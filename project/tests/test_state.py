from __future__ import annotations

from pathlib import Path

from maildrop.state import StateStore


def test_state_store_initializes_tables(tmp_path: Path) -> None:
    db_path = tmp_path / "maildrop.db"
    store = StateStore(db_path)

    store.initialize()

    assert db_path.exists()


def test_message_processed_roundtrip(tmp_path: Path) -> None:
    db_path = tmp_path / "maildrop.db"
    store = StateStore(db_path)
    store.initialize()

    assert store.is_message_processed("msg-1") is False

    store.record_message_processed("msg-1", "2026-04-15T10:00:00")

    assert store.is_message_processed("msg-1") is True


def test_attachment_saved_roundtrip(tmp_path: Path) -> None:
    db_path = tmp_path / "maildrop.db"
    store = StateStore(db_path)
    store.initialize()

    destination_path = "/tmp/example.pdf"
    checksum = "abc123"

    assert store.is_attachment_saved(checksum, destination_path) is False

    store.record_attachment_saved(
        message_id="msg-1",
        attachment_name="example.pdf",
        checksum=checksum,
        destination_path=destination_path,
        rule_name="test_rule",
        saved_at="2026-04-15T10:00:00",
    )

    assert store.is_attachment_saved(checksum, destination_path) is True


def test_record_attachment_saved_is_idempotent_for_same_checksum_and_path(
    tmp_path: Path,
) -> None:
    db_path = tmp_path / "maildrop.db"
    store = StateStore(db_path)
    store.initialize()

    destination_path = "/tmp/example.pdf"
    checksum = "abc123"

    store.record_attachment_saved(
        message_id="msg-1",
        attachment_name="example.pdf",
        checksum=checksum,
        destination_path=destination_path,
        rule_name="test_rule",
        saved_at="2026-04-15T10:00:00",
    )

    store.record_attachment_saved(
        message_id="msg-1",
        attachment_name="example.pdf",
        checksum=checksum,
        destination_path=destination_path,
        rule_name="test_rule",
        saved_at="2026-04-15T10:00:01",
    )

    assert store.is_attachment_saved(checksum, destination_path) is True