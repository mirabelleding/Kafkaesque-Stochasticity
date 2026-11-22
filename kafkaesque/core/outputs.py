from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass

import polars as pl


@dataclass(frozen=True)
class OccurrenceForecast:
    instantaneous_rates: pl.DataFrame
    cumulative_probabilities: pl.DataFrame
    hourly_probabilities: pl.DataFrame
    subjects: Mapping[str, float] | None

    @property
    def probability_of_happenstance(self) -> float:
        return float(
            self.cumulative_probabilities["probability"][-1]
        )


@dataclass(frozen=True)
class KaScoreForecast:
    probability_distribution: Mapping[int, float]

    @property
    def expected_score(self) -> float:
        return sum(
            score * probability
            for score, probability in self.probability_distribution.items()
        )


@dataclass(frozen=True)
class Outputs:
    occurrences: OccurrenceForecast
    ka_scores: KaScoreForecast | None