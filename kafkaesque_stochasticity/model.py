from __future__ import annotations

from collections.abc import Sequence
from inspect import isabstract
from typing import Self

from .core._types import RecordsInput
from .core.inputs import Inputs
from .core.outputs import Outputs
from .processes.base import StochasticProcess


class KafkaesqueModel:

    def __init__(
        self,
        records: RecordsInput,
        presence: RecordsInput | None = None,
    ) -> None:
        self.inputs = Inputs(records, presence)
        self._models: dict[str, StochasticProcess] = {}

    def fit(self, processes: str | Sequence[str]) -> Self:
        available = {
            cls.name: cls
            for cls in StochasticProcess.__subclasses__()
            if not isabstract(cls)
        }

        if processes == "all":
            selected = tuple(available)
        elif isinstance(processes, str):
            selected = (processes,)
        else:
            selected = tuple(dict.fromkeys(processes))

        if not selected:
            raise ValueError("No stochastic processes selected.")

        if unknown := set(selected) - available.keys():
            raise ValueError(f"Unknown processes: {sorted(unknown)}")

        self._models = {
            name: available[name]().fit(self.inputs)
            for name in selected
        }

        return self

    def predict(self, start: str, end: str) -> Outputs:
        if not self._models:
            raise RuntimeError("No fitted models available.")

        # TODO