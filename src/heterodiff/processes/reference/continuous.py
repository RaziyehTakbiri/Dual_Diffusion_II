"""Reference feature-wise variance-preserving Gaussian corruption.

The schedule index is numerical diffusion progress, never physical event time.
These routines define forward Gaussian laws and their exact conditionals only;
they do not define or make claims about a training objective.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Optional, Tuple

import numpy as np
from numpy.typing import NDArray


FloatArray = NDArray[np.float64]


def _validate_diffusion_progress(
    progress: Optional[FloatArray], num_diffusion_steps: int
) -> FloatArray:
    if progress is None:
        values = np.linspace(0.0, 1.0, num_diffusion_steps + 1, dtype=np.float64)
    else:
        values = np.array(progress, dtype=np.float64, copy=True)
        if values.shape != (num_diffusion_steps + 1,):
            raise ValueError(
                "diffusion_progress must have one entry for step zero and each "
                "corruption step"
            )
        if not np.all(np.isfinite(values)):
            raise ValueError("diffusion_progress must be finite")
        if values[0] != 0.0 or values[-1] != 1.0:
            raise ValueError("diffusion_progress must start at zero and end at one")
        if np.any(np.diff(values) <= 0.0):
            raise ValueError("diffusion_progress must be strictly increasing")
    values.setflags(write=False)
    return values


def _broadcast_valid_mask(mask: Optional[object], clean_shape: tuple) -> NDArray[np.bool_]:
    if mask is None:
        return np.ones(clean_shape, dtype=bool)
    values = np.asarray(mask)
    if values.dtype != np.bool_:
        raise TypeError("valid_mask must contain booleans")
    # An event/position mask conventionally omits the final feature axis.
    if values.shape == clean_shape[:-1]:
        values = values[..., None]
    try:
        return np.broadcast_to(values, clean_shape)
    except ValueError as error:
        raise ValueError("valid_mask cannot be broadcast to continuous values") from error


@dataclass(frozen=True)
class GaussianPosterior:
    """Elementwise parameters of ``q(z_{n-1} | z_n, z_0)``."""

    mean: FloatArray
    variance: FloatArray


@dataclass(frozen=True)
class VPGaussianSchedule:
    """A shared or feature-wise finite VP Gaussian schedule.

    ``betas`` may have shape ``[steps]`` for a shared feature clock or
    ``[steps, features]`` for explicitly feature-wise clocks.
    """

    betas: FloatArray
    diffusion_progress: Optional[FloatArray] = None
    alphas: FloatArray = field(init=False, repr=False)
    cumulative_alphas: FloatArray = field(init=False, repr=False)
    cumulative_variances: FloatArray = field(init=False, repr=False)
    log_cumulative_alphas: FloatArray = field(init=False, repr=False)

    def __post_init__(self) -> None:
        betas = np.array(self.betas, dtype=np.float64, copy=True)
        if betas.ndim == 1:
            betas = betas[:, None]
        if betas.ndim != 2 or betas.shape[0] == 0 or betas.shape[1] == 0:
            raise ValueError("betas must have shape [steps] or [steps, features]")
        if not np.all(np.isfinite(betas)) or np.any(betas <= 0.0) or np.any(betas >= 1.0):
            raise ValueError("VP Gaussian betas must lie strictly between zero and one")
        log_alphas = np.log1p(-betas)
        alphas = np.exp(log_alphas)
        log_cumulative = np.empty(
            (betas.shape[0] + 1, betas.shape[1]), dtype=np.float64
        )
        log_cumulative[0] = 0.0
        log_cumulative[1:] = np.cumsum(log_alphas, axis=0)
        cumulative = np.empty((betas.shape[0] + 1, betas.shape[1]), dtype=np.float64)
        cumulative[:] = np.exp(log_cumulative)
        cumulative_variances = -np.expm1(log_cumulative)
        progress = _validate_diffusion_progress(
            self.diffusion_progress, betas.shape[0]
        )
        for array in (
            betas,
            alphas,
            cumulative,
            cumulative_variances,
            log_cumulative,
        ):
            array.setflags(write=False)
        object.__setattr__(self, "betas", betas)
        object.__setattr__(self, "alphas", alphas)
        object.__setattr__(self, "cumulative_alphas", cumulative)
        object.__setattr__(self, "cumulative_variances", cumulative_variances)
        object.__setattr__(self, "log_cumulative_alphas", log_cumulative)
        object.__setattr__(self, "diffusion_progress", progress)

    @property
    def num_diffusion_steps(self) -> int:
        return self.betas.shape[0]

    @property
    def num_scheduled_features(self) -> int:
        return self.betas.shape[1]

    def _validate_step(self, diffusion_step: int, allow_zero: bool = True) -> int:
        if isinstance(diffusion_step, bool) or not isinstance(diffusion_step, (int, np.integer)):
            raise TypeError("diffusion_step must be an integer")
        minimum = 0 if allow_zero else 1
        if diffusion_step < minimum or diffusion_step > self.num_diffusion_steps:
            raise ValueError(
                "diffusion_step must lie in [%d, %d]"
                % (minimum, self.num_diffusion_steps)
            )
        return int(diffusion_step)

    def _feature_vector(self, values: FloatArray, num_features: int) -> FloatArray:
        if values.shape == (1,):
            return np.broadcast_to(values, (num_features,))
        if values.shape != (num_features,):
            raise ValueError(
                "schedule has %d features but clean values have %d"
                % (values.shape[0], num_features)
            )
        return values

    def _validate_clean(self, clean_values: object) -> FloatArray:
        clean = np.asarray(clean_values, dtype=np.float64)
        if clean.ndim == 0:
            clean = clean.reshape((1,))
        if not np.all(np.isfinite(clean)):
            raise ValueError("clean_values must be finite")
        return clean

    def q_moments(
        self, clean_values: object, diffusion_step: int
    ) -> Tuple[FloatArray, FloatArray]:
        """Return the exact mean and variance of ``q(z_n | z_0)``."""

        step = self._validate_step(diffusion_step)
        clean = self._validate_clean(clean_values)
        log_cumulative_alpha = self._feature_vector(
            self.log_cumulative_alphas[step], clean.shape[-1]
        )
        cumulative_variance = self._feature_vector(
            self.cumulative_variances[step], clean.shape[-1]
        )
        mean = np.exp(0.5 * log_cumulative_alpha) * clean
        variance = np.broadcast_to(cumulative_variance, clean.shape).copy()
        return mean, variance

    def q_sample(
        self,
        clean_values: object,
        diffusion_step: int,
        rng: Optional[np.random.Generator] = None,
        noise: Optional[object] = None,
        valid_mask: Optional[object] = None,
    ) -> FloatArray:
        """Sample ``q(z_n | z_0)`` while leaving invalid sites untouched."""

        clean = self._validate_clean(clean_values)
        mean, variance = self.q_moments(clean, diffusion_step)
        if noise is None:
            if not isinstance(rng, np.random.Generator):
                raise TypeError("rng must be a numpy.random.Generator when noise is omitted")
            epsilon = rng.standard_normal(clean.shape)
        else:
            epsilon = np.asarray(noise, dtype=np.float64)
            if epsilon.ndim == 0 and clean.shape == (1,):
                epsilon = epsilon.reshape((1,))
            if epsilon.shape != clean.shape or not np.all(np.isfinite(epsilon)):
                raise ValueError("noise must be finite and have the same shape as clean_values")
        noisy = mean + np.sqrt(variance) * epsilon
        mask = _broadcast_valid_mask(valid_mask, clean.shape)
        return np.where(mask, noisy, clean)

    def exact_posterior(
        self,
        noisy_values: object,
        clean_values: object,
        diffusion_step: int,
        valid_mask: Optional[object] = None,
    ) -> GaussianPosterior:
        """Return exact ``q(z_{n-1} | z_n, z_0)`` mean and variance."""

        step = self._validate_step(diffusion_step, allow_zero=False)
        clean = self._validate_clean(clean_values)
        noisy = self._validate_clean(noisy_values)
        if noisy.shape != clean.shape:
            raise ValueError("noisy_values must be finite and match clean_values")
        num_features = clean.shape[-1]
        beta = self._feature_vector(self.betas[step - 1], num_features)
        alpha = self._feature_vector(self.alphas[step - 1], num_features)
        log_cumulative_previous = self._feature_vector(
            self.log_cumulative_alphas[step - 1], num_features
        )
        cumulative_variance = self._feature_vector(
            self.cumulative_variances[step], num_features
        )
        cumulative_variance_previous = self._feature_vector(
            self.cumulative_variances[step - 1], num_features
        )
        denominator = cumulative_variance
        clean_coefficient = (
            np.exp(0.5 * log_cumulative_previous) * beta / denominator
        )
        noisy_coefficient = (
            np.sqrt(alpha) * cumulative_variance_previous / denominator
        )
        mean = clean_coefficient * clean + noisy_coefficient * noisy
        feature_variance = cumulative_variance_previous * beta / denominator
        variance = np.broadcast_to(feature_variance, clean.shape).copy()

        mask = _broadcast_valid_mask(valid_mask, clean.shape)
        mean = np.where(mask, mean, clean)
        variance = np.where(mask, variance, 0.0)
        return GaussianPosterior(mean=mean, variance=variance)
