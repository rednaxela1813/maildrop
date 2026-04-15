from __future__ import annotations

import typer

from maildrop.config import get_settings
from maildrop.imap_client import ImapClient
from maildrop.scanner import run_scan

app = typer.Typer(
    help="Maildrop CLI for sorting email attachments into local folders.",
    no_args_is_help=True,
)


@app.callback()
def callback() -> None:
    """
    Root command group.
    """
    pass


@app.command("scan")
def scan(
    dry_run: bool = typer.Option(
        False,
        "--dry-run",
        help="Show actions without saving files.",
    ),
) -> None:
    """
    Scan mailbox and process real email attachments.
    """
    settings = get_settings()
    run_scan(settings=settings, dry_run=dry_run)


@app.command("debug-imap")
def debug_imap() -> None:
    """
    Connect to IMAP and print unseen messages with attachment info.
    """
    settings = get_settings()

    client = ImapClient(
        host=settings.imap_host,
        port=settings.imap_port,
        username=settings.imap_user,
        password=settings.imap_password,
        mailbox=settings.imap_mailbox,
    )

    typer.echo("Connecting to IMAP...")
    messages = client.fetch_unseen_messages()
    typer.echo(f"Unseen messages found: {len(messages)}")

    for index, message in enumerate(messages, start=1):
        typer.echo("-" * 60)
        typer.echo(f"Message #{index}")
        typer.echo(f"ID: {message.source_id}")
        typer.echo(f"From: {message.sender}")
        typer.echo(f"Subject: {message.subject}")
        typer.echo(f"Received at: {message.received_at.isoformat()}")
        typer.echo(f"Attachments: {len(message.attachments)}")

        for attachment in message.attachments:
            typer.echo(
                f"  - {attachment.filename} | {attachment.content_type} | {attachment.size} bytes"
            )