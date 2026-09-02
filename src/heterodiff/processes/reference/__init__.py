"""Small exact corruption kernels for tests and independent reproduction.

These modules implement forward probability laws only. They intentionally make
no claim about a variational objective or a learned reverse model.
"""

from .continuous import GaussianPosterior, VPGaussianSchedule
from .discrete import (
    CategoricalSchedule,
    ImpossibleConditioningEvent,
    absorbing_d3pm_schedule,
    base_distribution_d3pm_schedule,
    cumulative_transitions,
    uniform_d3pm_schedule,
)

__all__ = [
    "CategoricalSchedule",
    "GaussianPosterior",
    "ImpossibleConditioningEvent",
    "VPGaussianSchedule",
    "absorbing_d3pm_schedule",
    "base_distribution_d3pm_schedule",
    "cumulative_transitions",
    "uniform_d3pm_schedule",
]
