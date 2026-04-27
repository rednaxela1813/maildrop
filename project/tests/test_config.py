from __future__ import annotations

from maildrop.config import DEFAULT_ENV_FILE, PACKAGE_ROOT, Settings


def test_settings_default_paths_are_resolved_from_project_root() -> None:
    settings = Settings(
        IMAP_HOST="mail.example.com",
        IMAP_USER="user@example.com",
        IMAP_PASSWORD="secret",
        NEXTCLOUD_MOUNT_PATH="/tmp/nextcloud",
    )

    assert PACKAGE_ROOT.name == "project"
    assert DEFAULT_ENV_FILE == PACKAGE_ROOT / ".env"
    assert settings.sqlite_path == PACKAGE_ROOT / "maildrop.db"
    assert settings.rules_file == PACKAGE_ROOT / "rules.yaml"


def test_settings_exposes_rule_variables() -> None:
    settings = Settings(
        IMAP_HOST="mail.example.com",
        IMAP_USER="user@example.com",
        IMAP_PASSWORD="secret",
        NEXTCLOUD_MOUNT_PATH="/tmp/nextcloud",
        MAILDROP_SENDER_DEILMANN="sender@example.com",
        MAILDROP_SENDER_VUB="bank@example.com",
        MAILDROP_SENDER_FORWARDER="forwarder@example.com",
    )

    assert settings.rule_variables() == {
        "MAILDROP_SENDER_DEILMANN": "sender@example.com",
        "MAILDROP_SENDER_VUB": "bank@example.com",
        "MAILDROP_SENDER_FORWARDER": "forwarder@example.com",
    }
