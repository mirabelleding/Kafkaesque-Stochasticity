from __future__ import annotations

from abc import ABC, abstractmethod
from datetime import datetime, timedelta
from typing import ClassVar, Self

import numpy as np
import polars as pl
import xarray as xr

from kafkaesque_stochasticity.core.inputs import Inputs
from kafkaesque_stochasticity.core.outputs import Outputs


class StochasticProcess(ABC):
    name: ClassVar[str]

    def __init__(self, inputs: Inputs) -> None:
        self._inputs = inputs

    @abstractmethod
    def fit(self) -> Self:
        ...

    def predict(
        self,
        start: datetime,
        end: datetime,
    ) -> Outputs:
        return Outputs(
            hourly_pmf=self._hourly_pmf(start, end),
            cdf=self._cdf(start, end),
            mark_distribution=self._forecast_mark_distribution(start, end),
            intensity=self._intensity(start, end),
        )

    @abstractmethod
    def _hourly_pmf(
        self,
        start: datetime,
        end: datetime,
    ) -> xr.DataArray:
        ...

    @abstractmethod
    def _cdf(
        self,
        start: datetime,
        end: datetime,
    ) -> xr.DataArray:
        ...

    @abstractmethod
    def _forecast_mark_distribution(
        self,
        start: datetime,
        end: datetime,
    ) -> xr.DataArray:
        ...

    @abstractmethod
    def _intensity(
        self,
        start: datetime,
        end: datetime,
    ) -> xr.DataArray:
        ...

    @staticmethod
    def _hourly_intervals(
        start: datetime,
        end: datetime,
    ) -> tuple[tuple[datetime, datetime], ...]:
        intervals = []
        current = start

        while current < end:
            next_hour = current.replace(
                minute=0,
                second=0,
                microsecond=0,
            ) + timedelta(hours=1)

            boundary = min(next_hour, end)
            intervals.append((current, boundary))
            current = boundary

        return tuple(intervals)

    def _observation_exposure(self) -> dict[str, float]:
        return dict(
            self._inputs.presence
            .group_by("subject")
            .agg(
                (
                    (pl.col("end") - pl.col("start"))
                    .dt.total_seconds() / 3600
                ).sum().alias("hours")
            )
            .select("subject", "hours")
            .iter_rows()
        )

    def _empirical_mark_distribution(self) -> xr.DataArray:
        records = self._inputs.occurrences

        subjects = sorted(records["subject"].unique().to_list())
        scores = [*map(str, range(1, 11)), "inf"]

        subject_index = {
            subject: i for i, subject in enumerate(subjects)
        }
        score_index = {
            score: i for i, score in enumerate(scores)
        }

        probabilities = np.zeros((len(subjects), len(scores)))

        frequencies = records.group_by(
            "subject", "ka_score"
        ).len()

        for subject, score, count in frequencies.iter_rows():
            probabilities[
                subject_index[subject],
                score_index[str(score)],
            ] = count

        probabilities /= probabilities.sum()

        return xr.DataArray(
            probabilities,
            dims=("subject", "ka_score"),
            coords={
                "subject": subjects,
                "ka_score": scores,
            },
        )

    @staticmethod
    def _build_outputs(
        hourly_probability_mass: xr.DataArray,
        cumulative_probability: xr.DataArray,
        mark_distribution: xr.DataArray,
        intensity: xr.DataArray,
    ) -> Outputs:
        return Outputs(
            hourly_probability_mass=hourly_probability_mass,
            cumulative_probability=cumulative_probability,
            mark_distribution=mark_distribution,
            intensity=intensity,
        )