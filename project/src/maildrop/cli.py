from __future__ import annotations

import typer

from maildrop.config import get_settings
from maildrop.health import check_sender_health
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


@app.command("check-health")
def check_health(
    max_age_days: int = typer.Option(
        7,
        "--max-age-days",
        help="Warn if a sender has not been seen for more than this number of days.",
    ),
    strict: bool = typer.Option(
        False,
        "--strict",
        help="Exit with code 1 if any monitored sender is stale.",
    ),
) -> None:
    """
    Check sender freshness based on local state.
    """
    settings = get_settings()
    results = check_sender_health(settings=settings, max_age_days=max_age_days)

    if not results:
        typer.echo("No sender history found yet.")
        return

    typer.echo(f"Checking sender freshness (threshold: {max_age_days} days)")
    stale_found = False

    for item in results:
        status = "STALE" if item.is_stale else "OK"
        typer.echo(
            f"[{status}] {item.sender} | last seen: {item.last_seen_at.isoformat()} | "
            f"age: {item.age_days} days"
        )
        if item.is_stale:
            stale_found = True

    if stale_found and strict:
        raise typer.Exit(code=1)