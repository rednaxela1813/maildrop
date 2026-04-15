from __future__ import annotations

from datetime import datetime
from pathlib import Path

from maildrop.models import Attachment, MailMessage, RoutingRule
from maildrop.rules import match_rule, render_destination


def test_match_rule_returns_matching_rule() -> None:
    message = MailMessage(
        source_id="msg-1",
        subject="Fwd: Elektronicky dodaci list",
        sender="Alexander Kiselev <deilmann.sro@gmail.com>",
        received_at=datetime(2026, 3, 2, 10, 0, 0),
        attachments=[],
    )
    attachment = Attachment(
        filename="INV_23201092_2304007430.CSV",
        content_type="text/csv",
        content=b"csv-data",
        size=8,
    )

    rules = [
        RoutingRule(
            name="metro_csv_documents",
            priority=10,
            enabled=True,
            sender_contains=["deilmann.sro@gmail.com"],
            subject_contains=["dodaci list"],
            filename_contains=["inv_"],
            allowed_extensions=[".csv"],
            destination="Mail/Documents/Metro/{yyyy}/{mm}",
        )
    ]

    matched = match_rule(message, attachment, rules)

    assert matched is not None
    assert matched.name == "metro_csv_documents"


def test_match_rule_returns_none_when_nothing_matches() -> None:
    message = MailMessage(
        source_id="msg-2",
        subject="Hello world",
        sender="someone@example.com",
        received_at=datetime(2026, 3, 2, 10, 0, 0),
        attachments=[],
    )
    attachment = Attachment(
        filename="document.pdf",
        content_type="application/pdf",
        content=b"pdf-data",
        size=8,
    )

    rules = [
        RoutingRule(
            name="bank_xml_exports",
            priority=10,
            enabled=True,
            sender_contains=["deilmann.sro@gmail.com"],
            subject_contains=["pravidelný export z účtu"],
            filename_contains=["export_"],
            allowed_extensions=[".xml"],
            destination="Mail/Bank/Exports/{yyyy}/{mm}",
        )
    ]

    matched = match_rule(message, attachment, rules)

    assert matched is None


def test_render_destination_replaces_date_placeholders() -> None:
    message = MailMessage(
        source_id="msg-3",
        subject="Anything",
        sender="someone@example.com",
        received_at=datetime(2026, 4, 15, 9, 30, 0),
        attachments=[],
    )

    result = render_destination("Mail/Documents/Websupport/{yyyy}/{mm}/{dd}", message)

    assert result == "Mail/Documents/Websupport/2026/04/15"