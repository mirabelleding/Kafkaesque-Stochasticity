from __future__ import annotations

from dataclasses import dataclass
from datetime import timedelta, datetime

import pandas as pd
import polars as pl

from ._types import KA_SCORE, RecordsInput

OCCURRENCE_COLUMNS = (
    "occurred_at", "environment", "modality", "subject", "ka_score"
)
PRESENCE_COLUMNS = ("subject", "start", "end")


@dataclass(frozen=True)
class Inputs:
    occurrences: pl.DataFrame
    presence: pl.DataFrame | None

    def __init__(
        self,
        occurrences: RecordsInput,
        presence: RecordsInput | None = None,
    ) -> None:
        occurrences = validate_occurrences(to_polars(occurrences))
        presence = (
            validate_presence(to_polars(presence))
            if presence is not None
            else None
        )

        if presence is not None:
            validate_occurrence_presence(occurrences, presence)

        else:
            start = occurrences["occurred_at"].min()
            end = occurrences["occurred_at"].max()

            if start == end:
                raise ValueError(
                    "Cannot infer observation exposure from a single timestamp."
                )

            subjects = occurrences["subject"].unique().to_list()

            presence = pl.DataFrame({
                "subject": subjects,
                "start": [start] * len(subjects),
                "end": [end + timedelta(seconds=1)] * len(subjects),
            })

        object.__setattr__(self, "occurrences", occurrences)
        object.__setattr__(self, "presence", presence)


def to_polars(data: RecordsInput) -> pl.DataFrame:
    if isinstance(data, pl.DataFrame):
        return data.clone()

    if isinstance(data, pd.DataFrame):
        return pl.from_pandas(data)

    return pl.DataFrame(
        data,
        schema_overrides={"ka_score": pl.String},
        strict=False,
    )


def _validate_dataframe(
    data: pl.DataFrame,
    required: tuple[str, ...],
    *,
    nullable: tuple[str, ...] = (),
) -> None:
    if data.is_empty():
        raise ValueError("Input DataFrame cannot be empty.")

    missing = set(required) - set(data.columns)

    if missing:
        raise ValueError(f"Input schema missing required columns: {sorted(missing)}.")

    null_columns = [
        column for column in required
        if column not in nullable and data[column].null_count()
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


def _impute_end_timestamp(data: pl.DataFrame) -> pl.DataFrame:
    return data.with_columns(
        pl.col("end").fill_null(datetime.now())
    )


def validate_occurrences(data: pl.DataFrame) -> pl.DataFrame:
    _validate_dataframe(data, OCCURRENCE_COLUMNS)
    data = _datetime_column(data, "occurred_at")

    try:
        return data.with_columns(
            pl.col("ka_score")
            .cast(pl.String)
            .str.replace(r"\.0+$", "")
            .cast(KA_SCORE, strict=True)
        )
    except pl.exceptions.PolarsError as exc:
        raise ValueError(
            "'ka_score' must be an integer from 1 to 10, "
            'its string representation, or "inf".'
        ) from exc


def validate_presence(data: pl.DataFrame) -> pl.DataFrame:
    _validate_dataframe(data, PRESENCE_COLUMNS, nullable=("end",))

    data = (
        data
        .pipe(_datetime_column, "start")
        .pipe(_datetime_column, "end")
        .pipe(_impute_end_timestamp)
    )

    if (data["start"] >= data["end"]).any():
        raise ValueError("Presence interval start must precede end.")

    overlaps = (
        data.sort("subject", "start")
        .with_columns(
            previous_end=pl.col("end").shift().over("subject")
        )
        .filter(pl.col("start") < pl.col("previous_end"))
    )

    if not overlaps.is_empty():
        raise ValueError("Overlapping presence intervals for the same subject.")

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