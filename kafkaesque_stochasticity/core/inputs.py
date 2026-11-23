from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass

import pandas as pd
import polars as pl

from ._types import RecordsInput

OCCURRENCE_COLUMNS = (
    "occurred_at", "environment", "modality", "subject", "ka_score"
)
PRESENCE_COLUMNS = ("subject", "start", "end")


@dataclass(frozen=True)
class Inputs:
    occurrences: RecordsInput
    presence: RecordsInput | None = None

    def __post_init__(self) -> None:
        occurrences = validate_occurrences(
            to_polars(self.occurrences)
        )
        presence = (
            validate_presence(to_polars(self.presence))
            if self.presence is not None
            else None
        )

        if presence is not None:
            validate_occurrence_presence(occurrences, presence)

        object.__setattr__(self, "occurrences", occurrences)
        object.__setattr__(self, "presence", presence)


def to_polars(data: RecordsInput) -> pl.DataFrame:
    if isinstance(data, pl.DataFrame):
        return data.clone()
    if isinstance(data, pd.DataFrame):
        return pl.from_pandas(data)
    if isinstance(data, Mapping):
        return pl.DataFrame(dict(data))
    return pl.from_dicts(data)


def _validate_columns(data: pl.DataFrame, required: tuple[str, ...]) -> None:
    missing = set(required) - set(data.columns)

    if missing:
        raise ValueError(f"Input schema missing required columns: {sorted(missing)}.")

    null_columns = [
        column for column in required
        if data[column].null_count()
    ]

    if null_columns:
        raise ValueError(f"Null values in: {null_columns}")


def _datetime_column(data: pl.DataFrame, column: str) -> pl.DataFrame:
    dtype = data.schema[column]

    if dtype == pl.String:
        if not data[column].str.contains(r"[ T]\d{2}:\d{2}").all():
            raise ValueError(f"{column!r} must contain valid timestamps")

        try:
            data = data.with_columns(pl.col(column).str.to_datetime(strict=True))
        except pl.exceptions.PolarsError as exc:
            raise ValueError(f"Invalid datetime values in {column!r}") from exc

    elif dtype.base_type() != pl.Datetime:
        raise TypeError(f"{column!r} must contain datetime values")

    return data


def validate_occurrences(data: pl.DataFrame) -> pl.DataFrame:
    _validate_columns(data, OCCURRENCE_COLUMNS)

    data = _datetime_column(data, "occurred_at")

    if (
        not data["ka_score"].dtype.is_integer()
        or not data["ka_score"].is_between(1, 10).all()
    ):
        raise ValueError("'ka_score' must be an integer between 1 and 10.")

    return data


def validate_presence(
    data: pl.DataFrame,
) -> pl.DataFrame:
    _validate_columns(data, PRESENCE_COLUMNS)

    for column in ("start", "end"):
        data = _datetime_column(data, column)

    if (data["start"] >= data["end"]).any():
        raise ValueError("Presence interval start must precede end.")

    return data



def validate_occurrence_presence(
    occurrences: pl.DataFrame,
    presence: pl.DataFrame,
) -> None:
    invalid = (
        occurrences.with_row_index("_occurrence_index")
        .join(presence, on="subject", how="left")
        .group_by("_occurrence_index")
        .agg(
            (
                (pl.col("occurred_at") >= pl.col("start"))
                & (pl.col("occurred_at") < pl.col("end"))
            )
            .fill_null(False)
            .any()
            .alias("within_presence")
        )
        .filter(~pl.col("within_presence"))
    )

    if not invalid.is_empty():
        raise ValueError(
            "Occurrences outside subject presence intervals."
        )