from __future__ import annotations

from datetime import datetime
from inspect import isabstract
from typing import Self

from . import processes
from .core._types import RecordsInput
from .core.inputs import Inputs
from .core.outputs import Outputs
from .processes.base import StochasticProcess


class KafkaesqueModel:

    def __init__(
        self,
        records: RecordsInput,
        presence: RecordsInput | None = None,
        *,
        process: str,
    ) -> None:
        cls = next(
            (
                cls
                for cls in StochasticProcess.__subclasses__()
                if not isabstract(cls) and cls.name == process
            ),
            None,
        )

        if cls is None:
            raise ValueError(f"Unknown process: {process}")

        self.inputs = Inputs(records, presence)
        self.process = cls()

    def fit(self) -> Self:
        self.process.fit(self.inputs)
        return self

    def predict(
        self,
        start:  str | datetime,
        end:  str | datetime,
    ) -> Outputs:
        start, end = (
            datetime.fromisoformat(value) if isinstance(value, str) else value
            for value in (start, end)
        )

        if start >= end:
            raise ValueError("Forecast start must precede end.")

        return self.process.predict(start, end)
