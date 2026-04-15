from __future__ import annotations

from pathlib import Path

import yaml

from maildrop.models import Attachment, FallbackRule, MailMessage, RoutingRule


def load_rules(rules_file: Path) -> tuple[list[RoutingRule], FallbackRule]:
    with rules_file.open("r", encoding="utf-8") as file:
        raw_data = yaml.safe_load(file) or {}

    raw_rules = raw_data.get("rules", [])
    raw_fallback = raw_data.get("fallback", {})

    rules: list[RoutingRule] = []
    for item in raw_rules:
        rule = RoutingRule(
            name=item["name"],
            priority=item.get("priority", 100),
            enabled=item.get("enabled", True),
            sender_contains=item.get("sender_contains", []),
            subject_contains=item.get("subject_contains", []),
            filename_contains=item.get("filename_contains", []),
            allowed_extensions=item.get("allowed_extensions", []),
            destination=item["destination"],
        )
        rules.append(rule)

    rules.sort(key=lambda rule: rule.priority)

    fallback = FallbackRule(
        destination=raw_fallback.get("destination", "Mail/Unsorted/{yyyy}/{mm}")
    )

    return rules, fallback


def match_rule(
    message: MailMessage,
    attachment: Attachment,
    rules: list[RoutingRule],
) -> RoutingRule | None:
    sender = message.sender.lower()
    subject = message.subject.lower()
    filename = attachment.filename.lower()
    extension = Path(attachment.filename).suffix.lower()

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

        if rule.allowed_extensions:
            normalized_extensions = [ext.lower() for ext in rule.allowed_extensions]
            if extension not in normalized_extensions:
                continue

        return rule

    return None


def render_destination(template: str, message: MailMessage) -> str:
    return (
        template.replace("{yyyy}", message.received_at.strftime("%Y"))
        .replace("{mm}", message.received_at.strftime("%m"))
        .replace("{dd}", message.received_at.strftime("%d"))
    )