from __future__ import annotations

from abc import ABC, abstractmethod
from typing import ClassVar, Self

from kafkaesque_stochasticity.core.inputs import Inputs
from kafkaesque_stochasticity.core.outputs import Outputs


class StochasticProcess(ABC):
    name: ClassVar[str]

    @abstractmethod
    def fit(self, inputs: Inputs) -> Self:
        ...

    @abstractmethod
    def predict(
        self,
        start: str,
        end: str,
    ) -> Outputs:
        ...