import logging

import polars as pl
from supabase import Client

logger = logging.getLogger(__name__)


def submit_occurrences(
    client: Client,
    records: pl.DataFrame,
) -> None:
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
    records: pl.DataFrame,
) -> None:
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