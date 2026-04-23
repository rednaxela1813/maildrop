from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta

from maildrop.config import Settings
from maildrop.state import StateStore


@dataclass(frozen=True)
class SenderHealthStatus:
    sender: str
    last_seen_at: datetime
    age_days: int
    is_stale: bool


def check_sender_health(settings: Settings, max_age_days: int = 7) -> list[SenderHealthStatus]:
    store = StateStore(settings.sqlite_path)
    store.initialize()

    now = datetime.now()
    threshold = timedelta(days=max_age_days)

    monitored_senders = settings.monitored_senders_list()
    monitored_set = set(monitored_senders)

    results: list[SenderHealthStatus] = []

    for sender, raw_last_seen_at in store.list_sender_last_seen():
        if monitored_set and sender not in monitored_set:
            continue

        last_seen_at = datetime.fromisoformat(raw_last_seen_at)
        age = now - last_seen_at

        results.append(
            SenderHealthStatus(
                sender=sender,
                last_seen_at=last_seen_at,
                age_days=age.days,
                is_stale=age > threshold,
            )
        )

    return results