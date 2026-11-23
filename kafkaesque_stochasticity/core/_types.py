from __future__ import annotations

from collections.abc import Mapping, Sequence
from typing import Any, TypeAlias

import pandas as pd
import polars as pl

RecordsInput: TypeAlias = (
    pd.DataFrame
    | pl.DataFrame
    | Mapping[str, Sequence[Any]]
    | Sequence[Mapping[str, Any]]
)