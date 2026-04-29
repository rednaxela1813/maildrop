from __future__ import annotations

import os
import re
from pathlib import Path

import yaml

from maildrop.models import Attachment, FallbackRule, MailMessage, RoutingRule
from maildrop.pdf_text import extract_pdf_text

VARIABLE_PATTERN = re.compile(r"\$\{([A-Z0-9_]+)\}")


def load_rules(
    rules_file: Path,
    variables: dict[str, str] | None = None,
) -> tuple[list[RoutingRule], FallbackRule]:
    with rules_file.open("r", encoding="utf-8") as file:
        raw_data = yaml.safe_load(file) or {}

    substitution_variables = {**os.environ, **(variables or {})}
    raw_rules = raw_data.get("rules", [])
    raw_fallback = raw_data.get("fallback", {})

    rules: list[RoutingRule] = []
    for item in raw_rules:
        rule = RoutingRule(
            name=item["name"],
            priority=item.get("priority", 100),
            enabled=item.get("enabled", True),
            sender_contains=_resolve_string_list(
                item.get("sender_contains", []),
                substitution_variables,
            ),
            subject_contains=_resolve_string_list(
                item.get("subject_contains", []),
                substitution_variables,
            ),
            filename_contains=_resolve_string_list(
                item.get("filename_contains", []),
                substitution_variables,
            ),
            attachment_text_contains=_resolve_string_list(
                item.get("attachment_text_contains", []),
                substitution_variables,
            ),
            allowed_extensions=_resolve_string_list(
                item.get("allowed_extensions", []),
                substitution_variables,
            ),
            destination=_resolve_string(item["destination"], substitution_variables),
        )
        rules.append(rule)

    rules.sort(key=lambda rule: rule.priority)

    fallback = FallbackRule(
        destination=_resolve_string(
            raw_fallback.get("destination", "Mail/Unsorted/{yyyy}/{mm}"),
            substitution_variables,
        )
    )

    return rules, fallback


def _resolve_string_list(items: list[str], variables: dict[str, str]) -> list[str]:
    return [_resolve_string(item, variables) for item in items]


def _resolve_string(value: str, variables: dict[str, str]) -> str:
    def replace(match: re.Match[str]) -> str:
        variable_name = match.group(1)
        if variable_name not in variables:
            raise ValueError(f"Rule variable is not defined: {variable_name}")
        return variables[variable_name]

    return VARIABLE_PATTERN.sub(replace, value)


def match_rule(
    message: MailMessage,
    attachment: Attachment,
    rules: list[RoutingRule],
) -> RoutingRule | None:
    sender = message.sender.lower()
    subject = message.subject.lower()
    filename = attachment.filename.lower()
    extension = Path(attachment.filename).suffix.lower()
    attachment_text: str | None = None

    for rule in rules:
        if not rule.enabled:
            continue

        if rule.sender_contains:
            if not any(fragment.lower() in sender for fragment in rule.sender_contains):
                continue

        if rule.subject_contains:
            if not any(fragment.lower() in subject for fragment in rule.subject_contains):
                continue

        if rule.filename_contains:
            if not any(fragment.lower() in filename for fragment in rule.filename_contains):
                continue

        if rule.attachment_text_contains:
            if attachment_text is None:
                attachment_text = _extract_attachment_text(attachment)

            if not any(
                fragment.lower() in attachment_text
                for fragment in rule.attachment_text_contains
            ):
                continue

        if rule.allowed_extensions:
            normalized_extensions = [ext.lower() for ext in rule.allowed_extensions]
            if extension not in normalized_extensions:
                continue

        return rule

    return None


def _extract_attachment_text(attachment: Attachment) -> str:
    extension = Path(attachment.filename).suffix.lower()
    if extension != ".pdf":
        return ""

    return extract_pdf_text(attachment.content).lower()


def render_destination(template: str, message: MailMessage) -> str:
    return (
        template.replace("{yyyy}", message.received_at.strftime("%Y"))
        .replace("{mm}", message.received_at.strftime("%m"))
        .replace("{dd}", message.received_at.strftime("%d"))
    )
