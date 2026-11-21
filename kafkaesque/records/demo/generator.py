from __future__ import annotations

from datetime import datetime, timedelta
from random import Random


def generate_demo_records(
    start: datetime,
    end: datetime,
    subject: str = "test",
    rate_per_day: float = 2.0,
    seed: int = 7,
) -> list[dict]:
    rng = Random(seed)
    occurred_at = start
    records = []

    while True:
        occurred_at += timedelta(
            days=rng.expovariate(rate_per_day)
        )

        if occurred_at >= end:
            break

        records.append({
            "occurred_at": occurred_at.isoformat(
                sep=" ", timespec="seconds"
            ),
            "project": rng.choice(["GPP", None]),
            "context": rng.choice([
                "Meeting", "Call", "Email", "Message", "In-Person"
            ]),
            "ka_score": rng.randint(-5, 10),
            "subject": subject,
            "testimony": f"Synthetic observation {len(records) + 1:03d}",
        })

    return records