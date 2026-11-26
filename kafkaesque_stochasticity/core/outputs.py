from __future__ import annotations

from dataclasses import dataclass

import xarray as xr


@dataclass(frozen=True)
class Outputs:
    hourly_pmf: xr.DataArray
    cdf: xr.DataArray
    mark_distribution: xr.DataArray
    intensity: xr.DataArray