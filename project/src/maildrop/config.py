from __future__ import annotations

from pathlib import Path

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    imap_host: str = Field(..., alias="IMAP_HOST")
    imap_port: int = Field(993, alias="IMAP_PORT")
    imap_user: str = Field(..., alias="IMAP_USER")
    imap_password: str = Field(..., alias="IMAP_PASSWORD")
    imap_mailbox: str = Field("INBOX", alias="IMAP_MAILBOX")

    nextcloud_mount_path: Path = Field(..., alias="NEXTCLOUD_MOUNT_PATH")

    sqlite_path: Path = Field(Path("./maildrop.db"), alias="SQLITE_PATH")
    rules_file: Path = Field(Path("./rules.yaml"), alias="RULES_FILE")

    log_level: str = Field("INFO", alias="LOG_LEVEL")
    allowed_extensions: str = Field(".pdf,.csv,.xml", alias="ALLOWED_EXTENSIONS")

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    def allowed_extensions_list(self) -> list[str]:
        return [
            item.strip().lower()
            for item in self.allowed_extensions.split(",")
            if item.strip()
        ]

def get_settings() -> Settings:
    return Settings()