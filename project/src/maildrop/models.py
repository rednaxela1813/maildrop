from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path


@dataclass(frozen=True)
class Attachment:
    filename: str
    content_type: str
    content: bytes
    size: int


@dataclass(frozen=True)
class MailMessage:
    source_id: str
    subject: str
    sender: str
    received_at: datetime
    attachments: list[Attachment] = field(default_factory=list)


@dataclass(frozen=True)
class RoutingRule:
    name: str
    priority: int
    enabled: bool
    sender_contains: list[str]
    subject_contains: list[str]
    filename_contains: list[str]
    allowed_extensions: list[str]
    destination: str


@dataclass(frozen=True)
class FallbackRule:
    destination: str


@dataclass(frozen=True)
class DeliveryRecord:
    message_id: str
    attachment_name: str
    checksum: str
    destination_path: Path
    rule_name: str | None
    saved_at: datetime