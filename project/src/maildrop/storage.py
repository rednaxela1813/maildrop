from __future__ import annotations

from pathlib import Path

from maildrop.models import Attachment, MailMessage


def build_destination_dir(base_path: Path, rendered_destination: str) -> Path:
    return base_path / rendered_destination


def build_destination_filename(message: MailMessage, attachment: Attachment) -> str:
    date_prefix = message.received_at.strftime("%Y-%m-%d")
    original_name = Path(attachment.filename).name
    return f"{date_prefix}_{original_name}"


def ensure_directory(path: Path) -> None:
    path.mkdir(parents=True, exist_ok=True)


def save_attachment(
    base_path: Path,
    rendered_destination: str,
    message: MailMessage,
    attachment: Attachment,
) -> Path:
    destination_dir = build_destination_dir(base_path, rendered_destination)
    ensure_directory(destination_dir)

    filename = build_destination_filename(message, attachment)
    destination_file = destination_dir / filename

    destination_file.write_bytes(attachment.content)
    return destination_file