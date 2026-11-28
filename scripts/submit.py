import logging

import polars as pl
from supabase import Client

from ..kafkaesque_stochasticity.core._types import RecordsInput
from ..kafkaesque_stochasticity.core.inputs import to_polars

logger = logging.getLogger(__name__)


def submit_occurrences(
    client: Client,
    records: RecordsInput,
) -> None:
    """
    Submit occurrence records and their associated testimonies.
    Associated environments, modalities, and subjects must already
    exist in the reference tables.
    """
    records = to_polars(records)

    payload = records.select(
        "occurred_at",
        "environment",
        "modality",
        "subject",
        pl.col("ka_score").cast(pl.Float64),
        "testimony",
    ).to_dicts()

    for record in payload:
        if record["ka_score"] == float("inf"):
            record["ka_score"] = "inf"

    uuids = client.rpc(
        "submit_occurrences",
        {"p_records": payload},
    ).execute().data

    logger.info("%d occurrence records inserted successfully.", len(uuids))


def submit_presence(
    client: Client,
    records: RecordsInput,
) -> None:
    """
    Submit subject presence intervals. Associated subjects must
    already exist in the reference tables.
    A null end timestamp represents an ongoing presence interval.
    """
    records = to_polars(records)

    count = client.rpc(
        "submit_presence",
        {
            "p_records": records.select(
                "subject",
                pl.col("start", "end").cast(pl.String),
            ).to_dicts()
        },
    ).execute().data

    logger.info("%d presence records inserted successfully.", count)


def submit_reference_data(
    client: Client,
    records: RecordsInput,
) -> None:
    """
    Extract and submit unique environments, modalities, and subjects
    from reference data, occurrence records, or presence records.
    Existing reference records are ignored.
    """
    records = to_polars(records)

    for column, table in (
        ("environment", "environments"),
        ("modality", "modalities"),
        ("subject", "subjects"),
    ):
        if column not in records.columns:
            continue

        values = [
            {"name": value}
            for value in records[column].drop_nulls().unique().sort()
        ]

        if values:
            inserted = client.table(table).upsert(
                values,
                on_conflict="name",
                ignore_duplicates=True,
                returning="representation",
            ).execute().data

            logger.info(
                "%s: %d inserted, %d existing records ignored.",
                table,
                len(inserted),
                len(values) - len(inserted),
            )