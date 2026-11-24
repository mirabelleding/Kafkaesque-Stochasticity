from __future__ import annotations

from dataclasses import dataclass

import xarray as xr


@dataclass(frozen=True)
class Outputs:
    probability_mass: xr.DataArray
    occurrences: xr.DataArray
    intensity: xr.DataArray