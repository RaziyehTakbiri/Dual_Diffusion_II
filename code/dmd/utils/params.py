"""Parameter matching across ladder rungs (MODEL_SPEC [R12]).

The paper's "matched capacity" claim must be auditable: given a reference
parameter count (rung B0 at hidden = 4*d_model by convention), every other
rung's hidden width is solved so its count lands within RTOL of the target.
Matched counts are logged with every run.
"""

from __future__ import annotations

from typing import Callable

import torch.nn as nn

RTOL = 0.01


def count_params(module: nn.Module) -> int:
    return sum(p.numel() for p in module.parameters() if p.requires_grad)


def match_width(
    build: Callable[[int], nn.Module],
    target: int,
    lo: int = 1,
    hi: int = 65536,
) -> int:
    """Binary-search the integer hidden width whose parameter count is closest
    to `target`. Counts are monotone in width for all ladder rungs."""
    if count_params(build(lo)) > target:
        return lo
    while hi - lo > 1:
        mid = (lo + hi) // 2
        if count_params(build(mid)) <= target:
            lo = mid
        else:
            hi = mid
    n_lo, n_hi = count_params(build(lo)), count_params(build(hi))
    best = lo if abs(n_lo - target) <= abs(n_hi - target) else hi
    achieved = count_params(build(best))
    if abs(achieved - target) / target > RTOL:
        raise ValueError(
            f"cannot match target={target} within {RTOL:.0%}; "
            f"closest width {best} gives {achieved}"
        )
    return best
