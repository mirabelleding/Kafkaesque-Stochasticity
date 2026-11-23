from typing import Self

from kafkaesque_stochasticity.core.inputs import Inputs
from kafkaesque_stochasticity.core.outputs import Outputs

from .base import StochasticProcess


class CalendarHawkesProcess(StochasticProcess):
    name = "calendar_hawkes"

    def fit(self, inputs: Inputs) -> Self:
        ...

    def predict(self, start: datetime, end: datetime) -> Outputs:
        ...

    # TODO