from __future__ import annotations

from datetime import datetime
from pathlib import Path

from maildrop.models import Attachment, MailMessage, RoutingRule
from maildrop.rules import load_rules, match_rule, render_destination


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
            attachment_text_contains=[],
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
            attachment_text_contains=[],
            allowed_extensions=[".xml"],
            destination="Mail/Bank/Exports/{yyyy}/{mm}",
        )
    ]

    matched = match_rule(message, attachment, rules)

    assert matched is None


def test_project_rules_match_vub_xml_exports_without_subject_dependency() -> None:
    message = MailMessage(
        source_id="msg-3",
        subject="Denný výpis",
        sender="VÚB <nonstopbanking@vub.sk>",
        received_at=datetime(2026, 4, 27, 1, 9, 3),
        attachments=[],
    )
    attachment = Attachment(
        filename="export_SK2902000000003936478451_26-04-2026-26-04-2026.XML",
        content_type="application/xml",
        content=b"<?xml version=\"1.0\"?><Document />",
        size=36,
    )
    rules_file = Path(__file__).resolve().parents[1] / "rules.yaml"
    rules, _ = load_rules(
        rules_file,
        variables={
            "MAILDROP_SENDER_DEILMANN": "deilmann.sro@gmail.com",
            "MAILDROP_SENDER_VUB": "nonstopbanking@vub.sk",
            "MAILDROP_SENDER_FORWARDER": "rednaxela1813@gmail.com",
        },
    )

    matched = match_rule(message, attachment, rules)

    assert matched is not None
    assert matched.name == "vub_bank_xml_exports"


def test_match_rule_can_match_pdf_attachment_text(monkeypatch) -> None:
    message = MailMessage(
        source_id="msg-4",
        subject="Document",
        sender="someone@example.com",
        received_at=datetime(2026, 4, 29, 11, 30, 0),
        attachments=[],
    )
    attachment = Attachment(
        filename="01_dok_5146203610013700.pdf",
        content_type="application/pdf",
        content=b"pdf-data",
        size=8,
    )
    rules = [
        RoutingRule(
            name="government_business_registry_documents",
            priority=10,
            enabled=True,
            sender_contains=[],
            subject_contains=[],
            filename_contains=["01_dok_"],
            attachment_text_contains=["Okresny urad Banska Bystrica"],
            allowed_extensions=[".pdf"],
            destination="Mail/Documents/Government/{yyyy}/{mm}",
        )
    ]

    monkeypatch.setattr(
        "maildrop.rules.extract_pdf_text",
        lambda content: "Okresny urad Banska Bystrica",
    )

    matched = match_rule(message, attachment, rules)

    assert matched is not None
    assert matched.name == "government_business_registry_documents"


def test_project_rules_match_spp_pdf_by_filename_and_text(monkeypatch) -> None:
    message = MailMessage(
        source_id="msg-5",
        subject="Zmluva",
        sender="no-reply@example.com",
        received_at=datetime(2026, 4, 29, 12, 30, 0),
        attachments=[],
    )
    attachment = Attachment(
        filename="SPP_14449363000001_5151255244.pdf",
        content_type="application/pdf",
        content=b"pdf-data",
        size=8,
    )
    rules_file = Path(__file__).resolve().parents[1] / "rules.yaml"
    rules, _ = load_rules(
        rules_file,
        variables={
            "MAILDROP_SENDER_DEILMANN": "deilmann.sro@gmail.com",
            "MAILDROP_SENDER_VUB": "nonstopbanking@vub.sk",
            "MAILDROP_SENDER_FORWARDER": "rednaxela1813@gmail.com",
        },
    )

    monkeypatch.setattr(
        "maildrop.rules.extract_pdf_text",
        lambda content: "Slovensky plynarensky priemysel",
    )

    matched = match_rule(message, attachment, rules)

    assert matched is not None
    assert matched.name == "spp_energy_contracts"


def test_load_rules_resolves_variables(tmp_path: Path) -> None:
    rules_file = tmp_path / "rules.yaml"
    rules_file.write_text(
        """
rules:
  - name: variable_sender_rule
    priority: 10
    enabled: true
    sender_contains:
      - "${SENDER_ADDRESS}"
    subject_contains: []
    filename_contains: []
    allowed_extensions:
      - ".pdf"
    destination: "Mail/Documents/${DESTINATION_BUCKET}/{yyyy}/{mm}"

fallback:
  destination: "Mail/Unsorted/{yyyy}/{mm}"
""".strip(),
        encoding="utf-8",
    )

    rules, _ = load_rules(
        rules_file,
        variables={
            "SENDER_ADDRESS": "sender@example.com",
            "DESTINATION_BUCKET": "Invoices",
        },
    )

    assert rules[0].sender_contains == ["sender@example.com"]
    assert rules[0].destination == "Mail/Documents/Invoices/{yyyy}/{mm}"


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
