from __future__ import annotations

from datetime import datetime

import numpy as np
import xarray as xr
from scipy.stats import poisson

from kafkaesque_stochasticity.core.inputs import Inputs
from kafkaesque_stochasticity.core.outputs import Outputs

from .base import StochasticProcess


class PoissonProcess(StochasticProcess):
    name = "poisson"

    def __init__(self, inputs: Inputs) -> None:
        super().__init__(inputs)
        self._rates: dict[str, float] = {}
        self._marks: xr.DataArray | None = None

    def fit(self) -> None:
        exposure = self._observation_exposure()

        counts = dict(
            self._inputs.occurrences
            .group_by("subject")
            .len()
            .iter_rows()
        )

        self._rates = {
            subject: counts.get(subject, 0) / hours
            for subject, hours in exposure.items()
        } # instantaneous rate; i.e. occurrences/h

        self._marks = self._empirical_mark_distribution()

    def _max_count(
        self,
        start: datetime,
        end: datetime,
    ) -> int:
        rate = sum(self._rates.values())
        hours = (end - start).total_seconds() / 3600

        return max(
            1,
            int(poisson.ppf(1 - 1e-10, rate * hours)),
        )

    def _hourly_pmf(
        self,
        start: datetime,
        end: datetime,
    ) -> xr.DataArray:
        intervals = self._hourly_intervals(start, end)
        rate = sum(self._rates.values())

        durations = np.array([
            (b - a).total_seconds() / 3600
            for a, b in intervals
        ])

        counts = np.arange(self._max_count(start, end) + 1)
        means = rate * durations

        return xr.DataArray(
            poisson.pmf(counts, means[:, None]),
            dims=("hour", "count"),
            coords={
                "hour": [a for a, _ in intervals],
                "count": counts,
            },
        )

    def _cdf(
        self,
        start: datetime,
        end: datetime,
    ) -> xr.DataArray:
        times = [
            start,
            *(b for _, b in self._hourly_intervals(start, end)),
        ]

        rate = sum(self._rates.values())

        hours = np.array([
            (t - start).total_seconds() / 3600
            for t in times
        ])

        return xr.DataArray(
            -np.expm1(-rate * hours),
            dims=("time",),
            coords={"time": times},
        )

    def _forecast_mark_distribution(
        self,
        start: datetime,
        end: datetime,
    ) -> xr.DataArray:
        subjects = list(self._rates)

        marks = self._marks.reindex(
            subject=subjects,
            fill_value=0,
        )

        subject_probabilities = marks.sum("ka_score")

        rates = xr.DataArray(
            list(self._rates.values()),
            dims=("subject",),
            coords={"subject": subjects},
        )

        conditional_marks = marks / subject_probabilities.where(
            subject_probabilities > 0,
            other=1,
        )

        return (
            conditional_marks * (rates / rates.sum())
        ).expand_dims(
            occurrence=np.arange(1, self._max_count(start, end) + 1)
        )

    def _intensity(
        self,
        start: datetime,
        end: datetime,
    ) -> xr.DataArray:
        historical = [
            self._inputs.presence["start"].min(),
            self._inputs.presence["end"].max(),
        ]

        forecast = [
            start,
            *(b for _, b in self._hourly_intervals(start, end)),
        ]

        rates = xr.DataArray(
            list(self._rates.values()),
            dims=("subject",),
            coords={"subject": list(self._rates)},
        )

        return rates.expand_dims(
            time=[*historical, *forecast],
        ).assign_coords(
            phase=(
                "time",
                ["historical"] * len(historical)
                + ["forecast"] * len(forecast),
            )
        )