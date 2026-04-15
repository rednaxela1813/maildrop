from __future__ import annotations

import hashlib
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path

from maildrop.config import Settings
from maildrop.imap_client import ImapClient
from maildrop.rules import load_rules, match_rule, render_destination
from maildrop.state import StateStore
from maildrop.storage import save_attachment


@dataclass(frozen=True)
class ScanResult:
    messages_seen: int
    messages_already_processed: int
    messages_marked_processed: int
    attachments_total: int
    attachments_skipped_unsupported: int
    attachments_already_saved: int
    attachments_saved: int


def run_scan(settings: Settings, dry_run: bool = False) -> ScanResult:
    state_store = StateStore(settings.sqlite_path)
    state_store.initialize()

    rules, fallback = load_rules(settings.rules_file)

    client = ImapClient(
        host=settings.imap_host,
        port=settings.imap_port,
        username=settings.imap_user,
        password=settings.imap_password,
        mailbox=settings.imap_mailbox,
    )

    print("Connecting to IMAP...")
    messages = client.fetch_unseen_messages()
    print(f"Unseen messages found: {len(messages)}")
    print(f"Loaded rules: {len(rules)}")
    print(f"Nextcloud mount path: {settings.nextcloud_mount_path}")
    print(f"SQLite path: {settings.sqlite_path}")

    allowed_extensions = settings.allowed_extensions_list()
    print(f"Allowed extensions: {', '.join(allowed_extensions)}")

    messages_already_processed = 0
    messages_marked_processed = 0
    attachments_total = 0
    attachments_skipped_unsupported = 0
    attachments_already_saved = 0
    attachments_saved = 0

    for message in messages:
        print("-" * 60)
        print(f"Message ID: {message.source_id}")
        print(f"From: {message.sender}")
        print(f"Subject: {message.subject}")
        print(f"Attachments found: {len(message.attachments)}")

        if state_store.is_message_processed(message.source_id):
            print(f"Message already processed locally: {message.source_id}")
            messages_already_processed += 1
            continue

        message_was_handled = False

        for attachment in message.attachments:
            attachments_total += 1

            extension = Path(attachment.filename).suffix.lower()

            if extension not in allowed_extensions:
                print(
                    f"Skipped unsupported attachment: {attachment.filename} "
                    f"({extension or 'no extension'})"
                )
                attachments_skipped_unsupported += 1
                message_was_handled = True
                continue

            checksum = hashlib.sha256(attachment.content).hexdigest()

            matched_rule = match_rule(message, attachment, rules)

            if matched_rule is not None:
                rendered_destination = render_destination(matched_rule.destination, message)
                matched_rule_name = matched_rule.name
                print(
                    f"Matched rule for {attachment.filename}: {matched_rule_name} -> "
                    f"{rendered_destination}"
                )
            else:
                rendered_destination = render_destination(fallback.destination, message)
                matched_rule_name = None
                print(
                    f"No rule matched for {attachment.filename}. Using fallback -> "
                    f"{rendered_destination}"
                )

            prospective_filename = (
                f"{message.received_at.strftime('%Y-%m-%d')}_{attachment.filename}"
            )
            prospective_full_path = (
                settings.nextcloud_mount_path / rendered_destination / prospective_filename
            )

            if state_store.is_attachment_saved(checksum, str(prospective_full_path)):
                print(f"Attachment already saved: {prospective_full_path}")
                attachments_already_saved += 1
                
                message_was_handled = True
                continue

            if dry_run:
                print(f"[DRY-RUN] Would save: {prospective_full_path}")
                message_was_handled = True
                continue

            saved_path = save_attachment(
                base_path=settings.nextcloud_mount_path,
                rendered_destination=rendered_destination,
                message=message,
                attachment=attachment,
            )

            saved_at = datetime.now().isoformat()

            state_store.record_attachment_saved(
                message_id=message.source_id,
                attachment_name=attachment.filename,
                checksum=checksum,
                destination_path=str(saved_path),
                rule_name=matched_rule_name,
                saved_at=saved_at,
            )

            print(f"Saved file to: {saved_path}")
            attachments_saved += 1
            message_was_handled = True

        if not dry_run and message_was_handled:
            state_store.record_message_processed(
                source_id=message.source_id,
                processed_at=datetime.now().isoformat(),
            )
            print(f"Recorded message as processed locally: {message.source_id}")
            messages_marked_processed += 1

    result = ScanResult(
        messages_seen=len(messages),
        messages_already_processed=messages_already_processed,
        messages_marked_processed=messages_marked_processed,
        attachments_total=attachments_total,
        attachments_skipped_unsupported=attachments_skipped_unsupported,
        attachments_already_saved=attachments_already_saved,
        attachments_saved=attachments_saved,
    )

    print("-" * 60)
    print("Summary:")
    print(f"  Messages seen: {result.messages_seen}")
    print(f"  Messages already processed: {result.messages_already_processed}")
    print(f"  Messages marked processed locally: {result.messages_marked_processed}")
    print(f"  Attachments total: {result.attachments_total}")
    print(f"  Attachments skipped unsupported: {result.attachments_skipped_unsupported}")
    print(f"  Attachments already saved: {result.attachments_already_saved}")
    print(f"  Attachments saved: {result.attachments_saved}")

    if dry_run:
        print("Dry-run finished.")
        return result

    if result.attachments_saved > 0:
        print("Scan finished successfully.")
    else:
        print("Scan finished. No new files were saved.")

    return result