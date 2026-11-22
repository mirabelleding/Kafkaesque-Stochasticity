from __future__ import annotations

from collections.abc import Sequence
from datetime import datetime, timedelta
from random import Random
from string import ascii_letters


def generate_demo_records(
    start: datetime,
    end: datetime,
    subjects: Sequence[str] = ("annoyance_1", "annoyance_2", "annoyance_3"),
    environments: Sequence[str] = ("environ_1", "environ_2"),
    modalities: Sequence[str] = ("mode_1", "mode_2", "mode_3", "mode_4"),
    ka_scores: Sequence[int] = tuple(range(1, 11)),
    rate_per_day: float = 2.0,
    seed: int = 7,
) -> list[dict[str, str | int]]:
    if rate_per_day <= 0:
        raise ValueError("rate_per_day must be positive")

    if not all((subjects, environments, modalities, ka_scores)):
        raise ValueError("Input sequences must not be empty")

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
            "environment": rng.choice(environments),
            "modality": rng.choice(modalities),
            "subject": rng.choice(subjects),
            "ka_score": rng.choice(ka_scores),
            "testimony": "".join(rng.choices(ascii_letters, k=24)),
        })

    return records