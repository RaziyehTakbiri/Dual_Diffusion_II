"""Leakage-resistant evaluation utilities.

The metric-floor routines estimate finite-sample variation between two
group-disjoint subsets of real data.  They are descriptive diagnostics, not
hypothesis tests or model scores.  They are imported lazily so independent
stdlib-only analytic submodules do not acquire NumPy or SciPy merely by being
imported through this package.
"""

from __future__ import annotations

from typing import Any

__all__ = [
    "BIASED_ENERGY",
    "WASSERSTEIN_1D",
    "GroupMetricFloor",
    "GroupSplitDistance",
    "biased_energy_distance",
    "estimate_group_metric_floor",
    "wasserstein_distance_1d",
]


def __getattr__(name: str) -> Any:
    """Load the legacy metric-floor surface only when it is requested."""

    if type(name) is not str or name not in __all__:
        raise AttributeError("module %r has no attribute %r" % (__name__, name))
    from . import metric_floor

    value = getattr(metric_floor, name)
    globals()[name] = value
    return value


def __dir__() -> list[str]:
    return sorted(set(globals()) | set(__all__))
