from __future__ import annotations

import email
import imaplib
from datetime import datetime
from email.header import decode_header, make_header
from email.message import Message
from email.utils import parsedate_to_datetime

from maildrop.models import Attachment, MailMessage


class ImapClient:
    def __init__(
        self,
        host: str,
        port: int,
        username: str,
        password: str,
        mailbox: str,
    ) -> None:
        self.host = host
        self.port = port
        self.username = username
        self.password = password
        self.mailbox = mailbox

    def fetch_unseen_messages(self) -> list[MailMessage]:
        messages: list[MailMessage] = []

        try:
            with imaplib.IMAP4_SSL(self.host, self.port) as imap:
                imap.login(self.username, self.password)

                status, _ = imap.select(self.mailbox)
                if status != "OK":
                    raise RuntimeError(f"Failed to select mailbox: {self.mailbox}")

                status, data = imap.search(None, "UNSEEN")
                if status != "OK":
                    return messages

                for raw_message_id in data[0].split():
                    fetch_status, msg_data = imap.fetch(raw_message_id, "(BODY.PEEK[])")
                    if fetch_status != "OK" or not msg_data or not msg_data[0]:
                        continue

                    raw_email = msg_data[0][1]
                    if not isinstance(raw_email, (bytes, bytearray)):
                        continue

                    parsed_message = email.message_from_bytes(raw_email)
                    mail_message = self._convert_message(
                        parsed_message,
                        source_id=raw_message_id.decode(),
                    )
                    messages.append(mail_message)

        except imaplib.IMAP4.error as exc:
            raise RuntimeError(
                f"IMAP authentication or protocol error for {self.username} on "
                f"{self.host}:{self.port}: {exc}"
            ) from exc

        return messages

    def _convert_message(self, parsed_message: Message, source_id: str) -> MailMessage:
        subject = self._decode_mime_header(parsed_message.get("Subject", ""))
        sender = self._decode_mime_header(parsed_message.get("From", ""))
        received_at = self._parse_received_at(parsed_message.get("Date"))
        attachments = self._extract_attachments(parsed_message)

        return MailMessage(
            source_id=source_id,
            subject=subject,
            sender=sender,
            received_at=received_at,
            attachments=attachments,
        )

    def _decode_mime_header(self, raw_value: str) -> str:
        if not raw_value:
            return ""

        try:
            return str(make_header(decode_header(raw_value)))
        except Exception:
            return raw_value

    def _parse_received_at(self, raw_date: str | None) -> datetime:
        if raw_date:
            try:
                parsed = parsedate_to_datetime(raw_date)
                if parsed is not None:
                    return parsed.replace(tzinfo=None) if parsed.tzinfo else parsed
            except Exception:
                pass

        return datetime.now()

    def _extract_attachments(self, parsed_message: Message) -> list[Attachment]:
        attachments: list[Attachment] = []

        if not parsed_message.is_multipart():
            return attachments

        for part in parsed_message.walk():
            if part.get_content_maintype() == "multipart":
                continue

            filename = part.get_filename()
            if not filename:
                continue

            decoded_filename = self._decode_mime_header(filename)

            content = part.get_payload(decode=True)
            if not isinstance(content, (bytes, bytearray)):
                continue

            attachment = Attachment(
                filename=decoded_filename,
                content_type=part.get_content_type(),
                content=bytes(content),
                size=len(content),
            )
            attachments.append(attachment)

        return attachments