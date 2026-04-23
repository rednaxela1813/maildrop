from __future__ import annotations

from pathlib import Path

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


PACKAGE_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_ENV_FILE = PACKAGE_ROOT / ".env"


class Settings(BaseSettings):
    imap_host: str = Field(..., alias="IMAP_HOST")
    imap_port: int = Field(993, alias="IMAP_PORT")
    imap_user: str = Field(..., alias="IMAP_USER")
    imap_password: str = Field(..., alias="IMAP_PASSWORD")
    imap_mailbox: str = Field("INBOX", alias="IMAP_MAILBOX")

    nextcloud_mount_path: Path = Field(..., alias="NEXTCLOUD_MOUNT_PATH")

    sqlite_path: Path = Field(PACKAGE_ROOT / "maildrop.db", alias="SQLITE_PATH")
    rules_file: Path = Field(PACKAGE_ROOT / "rules.yaml", alias="RULES_FILE")

    log_level: str = Field("INFO", alias="LOG_LEVEL")
    allowed_extensions: str = Field(".pdf,.csv,.xml", alias="ALLOWED_EXTENSIONS")
    monitored_senders: str = Field("", alias="MONITORED_SENDERS")

    model_config = SettingsConfigDict(
        env_file=DEFAULT_ENV_FILE,
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    def model_post_init(self, __context: object) -> None:
        self.sqlite_path = self._resolve_project_path(self.sqlite_path)
        self.rules_file = self._resolve_project_path(self.rules_file)

    def allowed_extensions_list(self) -> list[str]:
        return [
            item.strip().lower()
            for item in self.allowed_extensions.split(",")
            if item.strip()
        ]

    def monitored_senders_list(self) -> list[str]:
        return [
            item.strip()
            for item in self.monitored_senders.split(",")
            if item.strip()
        ]

    @staticmethod
    def _resolve_project_path(path: Path) -> Path:
        if path.is_absolute():
            return path
        return PACKAGE_ROOT / path


def get_settings() -> Settings:
    return Settings()
