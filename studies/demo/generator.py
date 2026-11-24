from __future__ import annotations

from collections.abc import Sequence
from datetime import datetime, timedelta
from random import Random
from string import ascii_letters


def generate_demo_presence(
    start: datetime,
    end: datetime,
    subjects: Sequence[str],
    intervals_per_subject: int,
    seed: int,
) -> list[dict]:
    rng = Random(seed)
    duration = (end - start).total_seconds()
    records = []

    for subject in subjects:
        boundaries = sorted(
            start + timedelta(seconds=rng.uniform(0, duration))
            for _ in range(2 * intervals_per_subject)
        )

        records.extend(
            {"subject": subject, "start": a, "end": b}
            for a, b in zip(boundaries[::2], boundaries[1::2])
        )

    return records


def generate_demo_records(
    start: datetime,
    end: datetime,
    subjects: Sequence[str],
    environments: Sequence[str],
    modalities: Sequence[str],
    ka_scores: Sequence[int | str],
    rate_per_day: float,
    seed: int,
    presence: list[dict] | None,
    inf_probability: float,
) -> list[dict]:
    if not 0 <= inf_probability <= 1:
        raise ValueError("'inf_probability' must be between 0 and 1.")

    finite_scores = tuple(score for score in ka_scores if score != "inf")

    if not finite_scores and ("inf" not in ka_scores or inf_probability < 1):
        raise ValueError("'ka_scores' must contain finite scores.")

    rng = Random(seed)
    current = start
    records = []
    intervals = {}

    for record in presence or ():
        intervals.setdefault(record["subject"], []).append(
            (record["start"], record["end"])
        )

    while current < end:
        current += timedelta(days=rng.expovariate(rate_per_day))

        if current >= end:
            break

        subject = rng.choice(subjects)

        if presence is not None and not any(
            a <= current < b
            for a, b in intervals.get(subject, ())
        ):
            continue

        records.append({
            "occurred_at": current,
            "environment": rng.choice(environments),
            "modality": rng.choice(modalities),
            "subject": subject,
            "ka_score": (
                "inf"
                if "inf" in ka_scores and rng.random() < inf_probability
                else rng.choice(finite_scores)
            ),
            "testimony": "".join(rng.choices(ascii_letters, k=24)),
        })

    return records


def generate_demo_data(
    start: datetime = datetime(2026, 1, 1),
    end: datetime = datetime(2026, 12, 31),
    subjects: Sequence[str] = ("annoyance_1", "annoyance_2", "annoyance_3"),
    environments: Sequence[str] = ("environ_1", "environ_2"),
    modalities: Sequence[str] = ("mode_1", "mode_2", "mode_3", "mode_4"),
    ka_scores: Sequence[int | str] = (*range(1, 11), "inf"),
    rate_per_day: float = 2.0,
    inf_probability: float = 0.05,
    intervals_per_subject: int = 3,
    incl_presence: bool = True,
    seed: int = 7,
) -> dict:
    presence = (
        generate_demo_presence(
            start=start,
            end=end,
            subjects=subjects,
            intervals_per_subject=intervals_per_subject,
            seed=seed,
        )
        if incl_presence else None
    )

    records = generate_demo_records(
        start=start,
        end=end,
        subjects=subjects,
        environments=environments,
        modalities=modalities,
        ka_scores=ka_scores,
        rate_per_day=rate_per_day,
        inf_probability=inf_probability,
        presence=presence,
        seed=seed,
    )

    return {"records": records, "presence": presence}