from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass

import pandas as pd
import polars as pl

from ._types import RecordsInput


def to_polars(data: RecordsInput) -> pl.DataFrame:
    if isinstance(data, pl.DataFrame):
        return data.clone()

    if isinstance(data, pd.DataFrame):
        return pl.from_pandas(data)

    if isinstance(data, Mapping):
        return pl.DataFrame(dict(data))

    return pl.from_dicts([dict(record) for record in data])


@dataclass(frozen=True)
class Inputs:
    occurrences: pl.DataFrame
    presence: pl.DataFrame | None = None