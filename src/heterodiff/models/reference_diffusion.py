"""Optional-Torch corruption and reverse sampling for the fixed-grid reference.

The probability laws are copied from validated NumPy schedule objects in
``heterodiff.processes.reference`` and checked against them in float64.  The
neural parameterization is frozen as categorical clean-``x0`` logits and
continuous Gaussian ``epsilon`` prediction.  This module deliberately contains
no Gumbel relaxation, classifier-free guidance, observed-value clamping, or
self-conditioning.

Clean categorical states use the contiguous indices ``0, ..., C_clean - 1``.
For the manuscript-facing absorbing process, the single diffusion-only mask is
the trailing index ``C_clean``.  NumPy schedules with an arbitrary mask index
remain valid forward oracles, but cannot be attached to this neural head without
an explicit state mapping and are therefore rejected here.

``elapsed_time_input`` passed to the model is a caller-supplied physical
inter-position duration.  It is not updated by the reverse diffusion clock and
is never confused with ``diffusion_progress``.
"""

from __future__ import annotations

from dataclasses import dataclass
import math
from numbers import Integral
from typing import Optional, Sequence, Tuple

import numpy as np

try:
    import torch
except ModuleNotFoundError as error:  # pragma: no cover - no-Torch boundary
    if error.name == "torch":
        raise ModuleNotFoundError(
            "heterodiff.models.reference_diffusion requires the optional "
            "PyTorch dependency; install the 'reference' extra"
        ) from error
    raise

from heterodiff.processes.reference import CategoricalSchedule, VPGaussianSchedule

from .fixed_grid import FixedGridReferenceDenoiser
from .reference_config import FixedGridReferenceConfig


_MAX_DIFFUSION_STEPS = 100_000
_MAX_REVERSE_WORK = 100_000_000
_MAX_REVERSE_MODEL_CALLS = 4_096
_MAX_REVERSE_MODEL_WORK = 1_000_000_000
_MAX_CATEGORICAL_SCHEDULES = 64
_MAX_GAUSSIAN_FEATURES = 4_096
_MAX_SINGLE_SCHEDULE_BYTES = 256 * 1024 * 1024
_MAX_BUNDLE_SCHEDULE_BYTES = 512 * 1024 * 1024
_SUPPORTED_STATE_DTYPES = frozenset(
    (torch.uint8, torch.int8, torch.int16, torch.int32, torch.int64)
)


def _plain_step(value: object, *, maximum: int, allow_zero: bool) -> int:
    if isinstance(value, bool) or not isinstance(value, Integral):
        raise TypeError("diffusion_step must be an integer")
    result = int(value)
    minimum = 0 if allow_zero else 1
    if result < minimum or result > maximum:
        raise ValueError(
            "diffusion_step must lie in [{}, {}]".format(minimum, maximum)
        )
    return result


def _cpu_generator(value: object) -> torch.Generator:
    if not isinstance(value, torch.Generator):
        raise TypeError("generator must be a torch.Generator")
    if str(value.device) != "cpu":
        raise ValueError("the frozen reference sampler requires a CPU generator")
    if value is torch.default_generator:
        raise ValueError(
            "generator must be a caller-created local generator, not Torch's "
            "global default generator"
        )
    return value


def _tensor(value: object, *, name: str) -> torch.Tensor:
    if not isinstance(value, torch.Tensor):
        raise TypeError("{} must be a torch.Tensor".format(name))
    if value.device.type != "cpu":
        raise ValueError("{} must be on CPU in the frozen reference".format(name))
    return value


def _integer_tensor(value: object, *, name: str) -> torch.Tensor:
    result = _tensor(value, name=name)
    if result.dtype not in _SUPPORTED_STATE_DTYPES:
        raise TypeError(
            "{} must use a supported 8/16/32/64-bit signed or uint8 integer dtype"
            .format(name)
        )
    return result


def _floating_tensor(value: object, *, name: str) -> torch.Tensor:
    result = _tensor(value, name=name)
    if not result.is_floating_point():
        raise TypeError("{} must have floating-point dtype".format(name))
    if result.dtype not in (torch.float32, torch.float64):
        raise TypeError("{} must use float32 or float64".format(name))
    return result


def _boolean_mask(
    value: object,
    *,
    name: str,
    shape: Tuple[int, ...],
) -> torch.Tensor:
    result = _tensor(value, name=name)
    if result.dtype != torch.bool:
        raise TypeError("{} must have boolean dtype".format(name))
    if tuple(result.shape) != shape:
        raise ValueError(
            "{} has shape {}; expected {}".format(name, tuple(result.shape), shape)
        )
    return result


class TorchCategoricalSchedule:
    """Defensive Torch copy of one categorical NumPy schedule.

    ``clean_cardinality`` freezes the contiguous clean-logit support.  A
    terminal mask is optional for forward-only use.  When supplied, it must be
    the one trailing noisy state and be exactly absorbing at every step.
    """

    def __init__(
        self,
        schedule: CategoricalSchedule,
        *,
        clean_cardinality: int,
        terminal_state: Optional[int] = None,
    ) -> None:
        if not isinstance(schedule, CategoricalSchedule):
            raise TypeError("schedule must be a CategoricalSchedule")
        if isinstance(clean_cardinality, bool) or not isinstance(
            clean_cardinality, Integral
        ):
            raise TypeError("clean_cardinality must be an integer")
        clean = int(clean_cardinality)
        if clean < 2 or clean > schedule.num_states:
            raise ValueError("clean_cardinality must lie in [2, num_states]")
        if schedule.num_diffusion_steps > _MAX_DIFFUSION_STEPS:
            raise ValueError("categorical schedule exceeds the diffusion-step guard")
        storage_bytes = 8 * (
            int(schedule.transitions.size)
            + int(schedule.cumulative.size)
            + int(schedule.diffusion_progress.size)
        )
        if storage_bytes > _MAX_SINGLE_SCHEDULE_BYTES:
            raise ValueError(
                "categorical schedule exceeds the Torch-copy byte guard"
            )

        terminal = None
        if terminal_state is not None:
            if isinstance(terminal_state, bool) or not isinstance(terminal_state, Integral):
                raise TypeError("terminal_state must be an integer or None")
            terminal = int(terminal_state)
            if schedule.num_states != clean + 1 or terminal != clean:
                raise ValueError(
                    "the neural absorbing convention requires one trailing mask state"
                )
            expected = np.zeros(schedule.num_states, dtype=np.float64)
            expected[terminal] = 1.0
            if not np.array_equal(schedule.transitions[:, terminal, :], np.broadcast_to(
                expected, (schedule.num_diffusion_steps, schedule.num_states)
            )):
                raise ValueError("terminal_state must be exactly absorbing at every step")

        self._clean_cardinality = clean
        self._terminal_state = terminal
        self._storage_bytes = storage_bytes
        self._transitions = torch.from_numpy(
            np.array(schedule.transitions, dtype=np.float64, copy=True)
        )
        self._cumulative = torch.from_numpy(
            np.array(schedule.cumulative, dtype=np.float64, copy=True)
        )
        self._progress = torch.from_numpy(
            np.array(schedule.diffusion_progress, dtype=np.float64, copy=True)
        )

    @property
    def clean_cardinality(self) -> int:
        return self._clean_cardinality

    @property
    def num_states(self) -> int:
        return int(self._transitions.shape[1])

    @property
    def num_diffusion_steps(self) -> int:
        return int(self._transitions.shape[0])

    @property
    def terminal_state(self) -> Optional[int]:
        return self._terminal_state

    @property
    def transitions(self) -> torch.Tensor:
        return self._transitions.clone()

    @property
    def cumulative(self) -> torch.Tensor:
        return self._cumulative.clone()

    @property
    def diffusion_progress(self) -> torch.Tensor:
        return self._progress.clone()

    @property
    def has_exact_terminal_prior(self) -> bool:
        if self._terminal_state is None:
            return False
        terminal = self._terminal_state
        # A final transition whose every row is the terminal point mass is an
        # exact structural certificate, even if a long preceding matrix product
        # accumulated roundoff in its terminal entry (for example
        # 0.9999999999999998 instead of 1).  Preserve the copied NumPy
        # cumulative matrix for parity rather than rewriting that roundoff.
        terminal_row = torch.zeros(self.num_states, dtype=torch.float64)
        terminal_row[terminal] = 1.0
        if torch.equal(
            self._transitions[-1],
            terminal_row.expand(self.num_states, self.num_states),
        ):
            return True
        clean_rows = self._cumulative[-1, : self._clean_cardinality]
        expected = torch.zeros_like(clean_rows)
        expected[:, terminal] = 1.0
        return bool(torch.equal(clean_rows, expected))

    def marginal_probabilities(
        self,
        clean_states: torch.Tensor,
        diffusion_step: int,
        *,
        valid_mask: Optional[torch.Tensor] = None,
    ) -> torch.Tensor:
        clean = _integer_tensor(clean_states, name="clean_states")
        step = _plain_step(
            diffusion_step, maximum=self.num_diffusion_steps, allow_zero=True
        )
        mask = (
            torch.ones(tuple(clean.shape), dtype=torch.bool)
            if valid_mask is None
            else _boolean_mask(
                valid_mask, name="valid_mask", shape=tuple(clean.shape)
            )
        )
        if bool(torch.any((clean < 0) | (clean >= self.clean_cardinality)).item()):
            raise ValueError("clean_states contains a state outside clean support")
        indices = clean.to(dtype=torch.long)
        probabilities = self._cumulative[step][indices].clone()
        if bool(torch.any(~mask).item()):
            deterministic = torch.nn.functional.one_hot(
                indices, num_classes=self.num_states
            ).to(dtype=torch.float64)
            probabilities = torch.where(mask.unsqueeze(-1), probabilities, deterministic)
        return probabilities

    def exact_posterior(
        self,
        clean_states: torch.Tensor,
        noisy_states: torch.Tensor,
        diffusion_step: int,
        *,
        valid_mask: Optional[torch.Tensor] = None,
        impossible: str = "raise",
    ) -> torch.Tensor:
        step = _plain_step(
            diffusion_step, maximum=self.num_diffusion_steps, allow_zero=False
        )
        clean = _integer_tensor(clean_states, name="clean_states")
        noisy = _integer_tensor(noisy_states, name="noisy_states")
        try:
            clean, noisy = torch.broadcast_tensors(clean, noisy)
        except RuntimeError as error:
            raise ValueError("clean_states and noisy_states are not broadcastable") from error
        if impossible not in ("raise", "zeros"):
            raise ValueError("impossible must be 'raise' or 'zeros'")
        shape = tuple(clean.shape)
        mask = (
            torch.ones(shape, dtype=torch.bool)
            if valid_mask is None
            else _boolean_mask(valid_mask, name="valid_mask", shape=shape)
        )
        if bool(torch.any((clean < 0) | (clean >= self.clean_cardinality)).item()):
            raise ValueError("clean_states contains a state outside clean support")
        if bool(torch.any((noisy < 0) | (noisy >= self.num_states)).item()):
            raise ValueError("noisy_states contains a state outside noisy support")

        result = torch.zeros(shape + (self.num_states,), dtype=torch.float64)
        flat_clean = clean.to(dtype=torch.long).reshape(-1)
        flat_noisy = noisy.to(dtype=torch.long).reshape(-1)
        flat_mask = mask.reshape(-1)
        flat_result = result.reshape(-1, self.num_states)
        impossible_sites = []
        for site in range(flat_clean.numel()):
            clean_state = int(flat_clean[site].item())
            noisy_state = int(flat_noisy[site].item())
            if not bool(flat_mask[site].item()):
                flat_result[site, clean_state] = 1.0
                continue
            denominator = float(
                self._cumulative[step, clean_state, noisy_state].item()
            )
            if denominator == 0.0:
                impossible_sites.append(site)
                continue
            weights = (
                self._cumulative[step - 1, clean_state]
                * self._transitions[step - 1, :, noisy_state]
            )
            row = weights / denominator
            row_sum = float(row.sum().item())
            if not math.isfinite(row_sum) or row_sum <= 0.0:
                raise ArithmeticError("categorical posterior is not representable")
            row = row / row_sum
            if bool(torch.any(~torch.isfinite(row)).item()):
                raise ArithmeticError("categorical posterior is non-finite")
            flat_result[site] = row
        if impossible_sites and impossible == "raise":
            raise ValueError(
                "zero-probability conditioning event at flattened site(s) {}"
                .format(impossible_sites[:5])
            )
        return result

    def q_sample(
        self,
        clean_states: torch.Tensor,
        diffusion_step: int,
        *,
        generator: torch.Generator,
        valid_mask: Optional[torch.Tensor] = None,
    ) -> torch.Tensor:
        clean = _integer_tensor(clean_states, name="clean_states")
        active_generator = _cpu_generator(generator)
        mask = (
            torch.ones(tuple(clean.shape), dtype=torch.bool)
            if valid_mask is None
            else _boolean_mask(
                valid_mask, name="valid_mask", shape=tuple(clean.shape)
            )
        )
        probabilities = self.marginal_probabilities(
            clean, diffusion_step, valid_mask=mask
        )
        result = clean.to(dtype=torch.long).clone()
        active_probabilities = probabilities[mask]
        if active_probabilities.numel():
            samples = torch.multinomial(
                active_probabilities,
                num_samples=1,
                replacement=True,
                generator=active_generator,
            ).squeeze(-1)
            result[mask] = samples
        return result


@dataclass(frozen=True)
class TorchGaussianCorruption:
    noisy: torch.Tensor
    epsilon: torch.Tensor


@dataclass(frozen=True)
class TorchGaussianPosterior:
    mean: torch.Tensor
    variance: torch.Tensor


class TorchVPGaussianSchedule:
    """Defensive Torch copy of a NumPy feature-wise VP schedule."""

    def __init__(self, schedule: VPGaussianSchedule) -> None:
        if not isinstance(schedule, VPGaussianSchedule):
            raise TypeError("schedule must be a VPGaussianSchedule")
        if schedule.num_diffusion_steps > _MAX_DIFFUSION_STEPS:
            raise ValueError("Gaussian schedule exceeds the diffusion-step guard")
        if schedule.num_scheduled_features > _MAX_GAUSSIAN_FEATURES:
            raise ValueError("Gaussian schedule exceeds the feature-count guard")
        storage_bytes = 8 * sum(
            int(array.size)
            for array in (
                schedule.betas,
                schedule.alphas,
                schedule.cumulative_alphas,
                schedule.cumulative_variances,
                schedule.log_cumulative_alphas,
                schedule.diffusion_progress,
            )
        )
        if storage_bytes > _MAX_SINGLE_SCHEDULE_BYTES:
            raise ValueError("Gaussian schedule exceeds the Torch-copy byte guard")
        self._storage_bytes = storage_bytes
        self._betas = torch.from_numpy(np.array(schedule.betas, copy=True))
        self._alphas = torch.from_numpy(np.array(schedule.alphas, copy=True))
        self._cumulative_alphas = torch.from_numpy(
            np.array(schedule.cumulative_alphas, copy=True)
        )
        self._cumulative_variances = torch.from_numpy(
            np.array(schedule.cumulative_variances, copy=True)
        )
        # Keep the log-domain signal coefficient.  ``alpha_bar`` itself can
        # underflow even when ``sqrt(alpha_bar)`` is still representable and
        # required by the forward, posterior, and DDIM equations.
        self._log_cumulative_alphas = torch.from_numpy(
            np.array(schedule.log_cumulative_alphas, copy=True)
        )
        self._progress = torch.from_numpy(
            np.array(schedule.diffusion_progress, copy=True)
        )

    @property
    def num_diffusion_steps(self) -> int:
        return int(self._betas.shape[0])

    @property
    def num_scheduled_features(self) -> int:
        return int(self._betas.shape[1])

    @property
    def betas(self) -> torch.Tensor:
        return self._betas.clone()

    @property
    def cumulative_alphas(self) -> torch.Tensor:
        return self._cumulative_alphas.clone()

    @property
    def diffusion_progress(self) -> torch.Tensor:
        return self._progress.clone()

    def _feature_vector(
        self, value: torch.Tensor, feature_count: int, dtype: torch.dtype
    ) -> torch.Tensor:
        if tuple(value.shape) == (1,):
            value = value.expand(feature_count)
        elif tuple(value.shape) != (feature_count,):
            raise ValueError(
                "Gaussian schedule has {} features; tensor has {}"
                .format(value.shape[0], feature_count)
            )
        converted = value.to(dtype=dtype)
        if bool(torch.any(~torch.isfinite(converted)).item()):
            raise FloatingPointError("Gaussian schedule cannot be represented in input dtype")
        return converted

    def q_moments(
        self, clean_values: torch.Tensor, diffusion_step: int
    ) -> Tuple[torch.Tensor, torch.Tensor]:
        clean = _floating_tensor(clean_values, name="clean_values")
        if clean.ndim == 0 or clean.shape[-1] == 0:
            raise ValueError("clean_values must have a non-empty feature axis")
        if bool(torch.any(~torch.isfinite(clean)).item()):
            raise ValueError("clean_values must be finite")
        step = _plain_step(
            diffusion_step, maximum=self.num_diffusion_steps, allow_zero=True
        )
        features = int(clean.shape[-1])
        log_cumulative = self._feature_vector(
            self._log_cumulative_alphas[step], features, clean.dtype
        )
        variance_feature = self._feature_vector(
            self._cumulative_variances[step], features, clean.dtype
        )
        if step > 0 and bool(torch.any(variance_feature <= 0.0).item()):
            raise FloatingPointError(
                "Gaussian variance is not representable in input dtype"
            )
        signal = torch.exp(0.5 * log_cumulative)
        if bool(torch.any((signal <= 0.0) | ~torch.isfinite(signal)).item()):
            raise FloatingPointError(
                "Gaussian signal coefficient is not representable in input dtype"
            )
        mean = signal * clean
        variance = variance_feature.expand_as(clean).clone()
        if bool(torch.any(~torch.isfinite(mean)).item()):
            raise FloatingPointError("Gaussian forward mean is non-finite")
        return mean, variance

    def q_sample(
        self,
        clean_values: torch.Tensor,
        diffusion_step: int,
        *,
        generator: Optional[torch.Generator] = None,
        noise: Optional[torch.Tensor] = None,
        valid_mask: Optional[torch.Tensor] = None,
    ) -> TorchGaussianCorruption:
        clean = _floating_tensor(clean_values, name="clean_values")
        if clean.ndim == 0:
            raise ValueError("clean_values must have a feature axis")
        mean, variance = self.q_moments(clean, diffusion_step)
        if valid_mask is None:
            mask = torch.ones(tuple(clean.shape), dtype=torch.bool)
        else:
            raw_mask = _tensor(valid_mask, name="valid_mask")
            if raw_mask.dtype != torch.bool:
                raise TypeError("valid_mask must have boolean dtype")
            if tuple(raw_mask.shape) == tuple(clean.shape[:-1]):
                raw_mask = raw_mask.unsqueeze(-1).expand_as(clean)
            mask = _boolean_mask(
                raw_mask, name="valid_mask", shape=tuple(clean.shape)
            )

        if noise is None:
            active_generator = _cpu_generator(generator)
            epsilon = torch.zeros_like(clean)
            count = int(mask.sum().item())
            if count:
                epsilon[mask] = torch.randn(
                    count, dtype=clean.dtype, generator=active_generator
                )
        else:
            epsilon = _floating_tensor(noise, name="noise")
            if tuple(epsilon.shape) != tuple(clean.shape):
                raise ValueError("noise must have the same shape as clean_values")
            if epsilon.dtype != clean.dtype:
                raise TypeError("noise and clean_values must have the same dtype")
            if bool(torch.any(~torch.isfinite(epsilon[mask])).item()):
                raise ValueError("noise must be finite at valid positions")
            epsilon = torch.where(mask, epsilon, torch.zeros_like(epsilon))
        noisy_candidate = mean + torch.sqrt(variance) * epsilon
        if bool(torch.any(~torch.isfinite(noisy_candidate[mask])).item()):
            raise FloatingPointError("Gaussian corruption is non-finite")
        noisy = torch.where(mask, noisy_candidate, clean)
        return TorchGaussianCorruption(noisy=noisy, epsilon=epsilon)

    def exact_posterior(
        self,
        noisy_values: torch.Tensor,
        clean_values: torch.Tensor,
        diffusion_step: int,
        *,
        valid_mask: Optional[torch.Tensor] = None,
    ) -> TorchGaussianPosterior:
        clean = _floating_tensor(clean_values, name="clean_values")
        noisy = _floating_tensor(noisy_values, name="noisy_values")
        if tuple(noisy.shape) != tuple(clean.shape) or noisy.dtype != clean.dtype:
            raise ValueError("noisy_values must match clean_values in shape and dtype")
        if clean.ndim == 0 or clean.shape[-1] == 0:
            raise ValueError("clean_values must have a non-empty feature axis")
        if bool(torch.any(~torch.isfinite(clean)).item()) or bool(
            torch.any(~torch.isfinite(noisy)).item()
        ):
            raise ValueError("clean_values and noisy_values must be finite")
        step = _plain_step(
            diffusion_step, maximum=self.num_diffusion_steps, allow_zero=False
        )
        features = int(clean.shape[-1])
        beta = self._feature_vector(self._betas[step - 1], features, clean.dtype)
        alpha = self._feature_vector(self._alphas[step - 1], features, clean.dtype)
        previous_log_cumulative = self._feature_vector(
            self._log_cumulative_alphas[step - 1], features, clean.dtype
        )
        cumulative_variance = self._feature_vector(
            self._cumulative_variances[step], features, clean.dtype
        )
        previous_variance = self._feature_vector(
            self._cumulative_variances[step - 1], features, clean.dtype
        )
        if bool(
            torch.any(
                (beta <= 0.0)
                | (cumulative_variance <= 0.0)
                | (previous_variance < 0.0)
            ).item()
        ) or (
            step > 1 and bool(torch.any(previous_variance <= 0.0).item())
        ):
            raise FloatingPointError(
                "Gaussian posterior clock is not representable in input dtype"
            )
        previous_signal = torch.exp(0.5 * previous_log_cumulative)
        if bool(
            torch.any((previous_signal <= 0.0) | ~torch.isfinite(previous_signal)).item()
        ):
            raise FloatingPointError(
                "Gaussian posterior signal is not representable in input dtype"
            )
        clean_coefficient = previous_signal * beta / cumulative_variance
        noisy_coefficient = torch.sqrt(alpha) * previous_variance / cumulative_variance
        mean = clean_coefficient * clean + noisy_coefficient * noisy
        feature_variance = previous_variance * beta / cumulative_variance
        variance = feature_variance.expand_as(clean).clone()
        if valid_mask is None:
            mask = torch.ones(tuple(clean.shape), dtype=torch.bool)
        else:
            raw_mask = _tensor(valid_mask, name="valid_mask")
            if raw_mask.dtype != torch.bool:
                raise TypeError("valid_mask must have boolean dtype")
            if tuple(raw_mask.shape) == tuple(clean.shape[:-1]):
                raw_mask = raw_mask.unsqueeze(-1).expand_as(clean)
            mask = _boolean_mask(raw_mask, name="valid_mask", shape=tuple(clean.shape))
        mean = torch.where(mask, mean, clean)
        variance = torch.where(mask, variance, torch.zeros_like(variance))
        if bool(torch.any(~torch.isfinite(mean[mask])).item()) or bool(
            torch.any(~torch.isfinite(variance[mask])).item()
        ):
            raise FloatingPointError("Gaussian posterior is non-finite")
        return TorchGaussianPosterior(mean=mean, variance=variance)


class FixedGridDiffusionBundle:
    """One synchronized categorical/Gaussian clock for a fixed-grid model."""

    def __init__(
        self,
        categorical: Sequence[TorchCategoricalSchedule],
        continuous: TorchVPGaussianSchedule,
    ) -> None:
        schedules = tuple(categorical)
        if not schedules or not all(
            isinstance(item, TorchCategoricalSchedule) for item in schedules
        ):
            raise TypeError("categorical must contain TorchCategoricalSchedule objects")
        if len(schedules) > _MAX_CATEGORICAL_SCHEDULES:
            raise ValueError("categorical schedule count exceeds the hard guard")
        if not isinstance(continuous, TorchVPGaussianSchedule):
            raise TypeError("continuous must be a TorchVPGaussianSchedule")
        if (
            sum(schedule._storage_bytes for schedule in schedules)
            + continuous._storage_bytes
            > _MAX_BUNDLE_SCHEDULE_BYTES
        ):
            raise ValueError("diffusion bundle exceeds the schedule byte guard")
        step_count = schedules[0].num_diffusion_steps
        progress = schedules[0]._progress
        for schedule in schedules[1:]:
            if schedule.num_diffusion_steps != step_count or not torch.equal(
                schedule._progress, progress
            ):
                raise ValueError("all categorical schedules must share one exact clock")
        if continuous.num_diffusion_steps != step_count or not torch.equal(
            continuous._progress, progress
        ):
            raise ValueError("categorical and continuous schedules must share one exact clock")
        model_progress = progress.to(dtype=torch.float32)
        if bool(torch.any(~torch.isfinite(model_progress)).item()) or not bool(
            torch.all(model_progress[1:] > model_progress[:-1]).item()
        ):
            raise ValueError(
                "diffusion_progress must remain finite and strictly increasing "
                "in the model's float32 dtype"
            )
        self._categorical = schedules
        self._continuous = continuous
        self._progress = progress.clone()

    @property
    def categorical(self) -> Tuple[TorchCategoricalSchedule, ...]:
        return self._categorical

    @property
    def continuous(self) -> TorchVPGaussianSchedule:
        return self._continuous

    @property
    def num_diffusion_steps(self) -> int:
        return int(self._progress.numel() - 1)

    @property
    def diffusion_progress(self) -> torch.Tensor:
        return self._progress.clone()

    def validate_model_config(
        self, config: FixedGridReferenceConfig, *, require_exact_terminal: bool
    ) -> None:
        if not isinstance(config, FixedGridReferenceConfig):
            raise TypeError("config must be a FixedGridReferenceConfig")
        if not isinstance(require_exact_terminal, bool):
            raise TypeError("require_exact_terminal must be a boolean")
        if len(self._categorical) != config.num_categorical_fields:
            raise ValueError("schedule field count does not match model configuration")
        for field, schedule in enumerate(self._categorical):
            if schedule.num_states != config.categorical_cardinalities[field]:
                raise ValueError("categorical noisy support does not match model")
            if schedule.clean_cardinality != config.categorical_output_cardinalities[field]:
                raise ValueError("categorical clean support does not match model")
            if require_exact_terminal:
                if schedule.terminal_state != schedule.clean_cardinality:
                    raise ValueError(
                        "full reverse sampling requires one trailing mask state"
                    )
                if not schedule.has_exact_terminal_prior:
                    raise ValueError(
                        "categorical schedule does not end at the exact mask prior"
                    )
        scheduled_features = self._continuous.num_scheduled_features
        if scheduled_features not in (1, config.num_continuous_features):
            raise ValueError("Gaussian feature clock does not match model")


def categorical_x0_reverse_probabilities(
    schedule: TorchCategoricalSchedule,
    noisy_states: torch.Tensor,
    x0_logits: torch.Tensor,
    diffusion_step: int,
    *,
    valid_mask: torch.Tensor,
) -> torch.Tensor:
    """Mix exact categorical posteriors using compatible clean-``x0`` logits."""

    if not isinstance(schedule, TorchCategoricalSchedule):
        raise TypeError("schedule must be a TorchCategoricalSchedule")
    noisy = _integer_tensor(noisy_states, name="noisy_states")
    logits = _floating_tensor(x0_logits, name="x0_logits")
    if tuple(logits.shape) != tuple(noisy.shape) + (schedule.clean_cardinality,):
        raise ValueError("x0_logits does not match noisy state and clean support")
    mask = _boolean_mask(valid_mask, name="valid_mask", shape=tuple(noisy.shape))
    if bool(torch.any((noisy < 0) | (noisy >= schedule.num_states)).item()):
        raise ValueError("noisy_states contains a state outside noisy support")
    if bool(torch.any(~torch.isfinite(logits[mask])).item()):
        raise ValueError("x0_logits must be finite at valid positions")
    step = _plain_step(
        diffusion_step, maximum=schedule.num_diffusion_steps, allow_zero=False
    )
    result = torch.zeros(tuple(noisy.shape) + (schedule.num_states,), dtype=torch.float64)
    flat_noisy = noisy.to(dtype=torch.long).reshape(-1)
    flat_logits = logits.to(dtype=torch.float64).reshape(-1, schedule.clean_cardinality)
    flat_mask = mask.reshape(-1)
    flat_result = result.reshape(-1, schedule.num_states)
    for site in range(flat_noisy.numel()):
        observed = int(flat_noisy[site].item())
        if not bool(flat_mask[site].item()):
            flat_result[site, observed] = 1.0
            continue
        denominators = schedule._cumulative[
            step, : schedule.clean_cardinality, observed
        ]
        compatible = denominators > 0.0
        if not bool(torch.any(compatible).item()):
            raise ValueError("no clean x0 state is compatible with a noisy state")
        compatible_logits = flat_logits[site, compatible]
        log_weights = compatible_logits - torch.logsumexp(compatible_logits, dim=0)
        weights = torch.exp(log_weights)
        if bool(torch.any(weights == 0.0).item()) or bool(
            torch.any(~torch.isfinite(weights)).item()
        ):
            raise FloatingPointError("a positive compatible x0 weight underflowed")
        clean_indices = torch.nonzero(compatible, as_tuple=False).reshape(-1)
        mixture = torch.zeros(schedule.num_states, dtype=torch.float64)
        for weight, clean_index in zip(weights, clean_indices):
            clean_state = int(clean_index.item())
            numerator = (
                schedule._cumulative[step - 1, clean_state]
                * schedule._transitions[step - 1, :, observed]
            )
            posterior = numerator / denominators[clean_state]
            mixture = mixture + weight * posterior
        total = float(mixture.sum().item())
        if not math.isfinite(total) or total <= 0.0:
            raise FloatingPointError("categorical reverse mixture is not representable")
        mixture = mixture / total
        if bool(torch.any(mixture < 0.0).item()) or bool(
            torch.any(~torch.isfinite(mixture)).item()
        ):
            raise FloatingPointError("categorical reverse mixture is invalid")
        flat_result[site] = mixture
    return result


def sample_categorical_reverse(
    probabilities: torch.Tensor,
    *,
    generator: torch.Generator,
    valid_mask: torch.Tensor,
) -> torch.Tensor:
    probabilities = _floating_tensor(probabilities, name="probabilities")
    if probabilities.ndim < 2 or probabilities.shape[-1] < 2:
        raise ValueError("probabilities must have a nontrivial state axis")
    mask = _boolean_mask(
        valid_mask, name="valid_mask", shape=tuple(probabilities.shape[:-1])
    )
    active_generator = _cpu_generator(generator)
    if bool(torch.any(~torch.isfinite(probabilities[mask])).item()) or bool(
        torch.any(probabilities[mask] < 0.0).item()
    ):
        raise ValueError("probabilities must be finite and nonnegative")
    row_tolerance = max(
        1.0e-11, 64.0 * float(torch.finfo(probabilities.dtype).eps)
    )
    if bool(
        torch.any(
            torch.abs(probabilities[mask].sum(dim=-1) - 1.0)
            > row_tolerance
        ).item()
    ):
        raise ValueError("probability rows must sum to one")
    result = torch.zeros(tuple(mask.shape), dtype=torch.long)
    if bool(torch.any(mask).item()):
        result[mask] = torch.multinomial(
            probabilities[mask],
            num_samples=1,
            replacement=True,
            generator=active_generator,
        ).squeeze(-1)
    return result


def ddim_epsilon_step(
    schedule: TorchVPGaussianSchedule,
    noisy_values: torch.Tensor,
    epsilon_prediction: torch.Tensor,
    diffusion_step: int,
    *,
    valid_mask: torch.Tensor,
) -> torch.Tensor:
    """Apply the deterministic ``eta=0`` DDIM update from step n to n-1."""

    if not isinstance(schedule, TorchVPGaussianSchedule):
        raise TypeError("schedule must be a TorchVPGaussianSchedule")
    noisy = _floating_tensor(noisy_values, name="noisy_values")
    epsilon = _floating_tensor(epsilon_prediction, name="epsilon_prediction")
    if tuple(epsilon.shape) != tuple(noisy.shape) or epsilon.dtype != noisy.dtype:
        raise ValueError("epsilon_prediction must match noisy_values")
    if noisy.ndim == 0 or noisy.shape[-1] == 0:
        raise ValueError("noisy_values must have a non-empty feature axis")
    mask = _boolean_mask(valid_mask, name="valid_mask", shape=tuple(noisy.shape))
    if bool(torch.any(~torch.isfinite(noisy[mask])).item()) or bool(
        torch.any(~torch.isfinite(epsilon[mask])).item()
    ):
        raise ValueError("DDIM inputs must be finite at valid positions")
    step = _plain_step(
        diffusion_step, maximum=schedule.num_diffusion_steps, allow_zero=False
    )
    features = int(noisy.shape[-1])
    current_log = schedule._feature_vector(
        schedule._log_cumulative_alphas[step], features, noisy.dtype
    )
    previous_log = schedule._feature_vector(
        schedule._log_cumulative_alphas[step - 1], features, noisy.dtype
    )
    current_variance = schedule._feature_vector(
        schedule._cumulative_variances[step], features, noisy.dtype
    )
    previous_variance = schedule._feature_vector(
        schedule._cumulative_variances[step - 1], features, noisy.dtype
    )
    current_signal = torch.exp(0.5 * current_log)
    previous_signal = torch.exp(0.5 * previous_log)
    if bool(
        torch.any(
            (current_signal <= 0.0)
            | (previous_signal <= 0.0)
            | ~torch.isfinite(current_signal)
            | ~torch.isfinite(previous_signal)
        ).item()
    ):
        raise FloatingPointError(
            "DDIM signal coefficient is not representable in input dtype"
        )
    if bool(
        torch.any(
            (current_variance <= 0.0)
            | (previous_variance < 0.0)
            | ((step > 1) & (previous_variance <= 0.0))
        ).item()
    ):
        raise FloatingPointError(
            "DDIM variance coefficient is not representable in input dtype"
        )
    clean_prediction = (
        noisy - torch.sqrt(current_variance) * epsilon
    ) / current_signal
    candidate = (
        previous_signal * clean_prediction
        + torch.sqrt(previous_variance) * epsilon
    )
    if bool(torch.any(~torch.isfinite(candidate[mask])).item()):
        raise FloatingPointError("DDIM update is non-finite")
    return torch.where(mask, candidate, noisy)


@dataclass(frozen=True)
class FixedGridReverseSample:
    discrete_state: torch.Tensor
    continuous_state: torch.Tensor


@torch.no_grad()
def sample_fixed_grid_reverse(
    model: FixedGridReferenceDenoiser,
    bundle: FixedGridDiffusionBundle,
    *,
    elapsed_time_input: torch.Tensor,
    sequence_mask: torch.Tensor,
    discrete_observed_mask: torch.Tensor,
    continuous_observed_mask: torch.Tensor,
    elapsed_time_observed_mask: torch.Tensor,
    generator: torch.Generator,
    max_reverse_work: int = _MAX_REVERSE_WORK,
) -> FixedGridReverseSample:
    """Run one bounded full reverse clock from declared terminal noise.

    Sequence length, every observation mask, and physical inter-position
    duration are caller supplied.  Observation masks inform the denoiser but do
    not clamp state.  The function refuses a model in training mode and never
    changes its mode or weights.
    """

    if not isinstance(model, FixedGridReferenceDenoiser):
        raise TypeError("model must be a FixedGridReferenceDenoiser")
    if model.training:
        raise ValueError("reverse sampling requires model.eval()")
    if not isinstance(bundle, FixedGridDiffusionBundle):
        raise TypeError("bundle must be a FixedGridDiffusionBundle")
    active_generator = _cpu_generator(generator)
    if isinstance(max_reverse_work, bool) or not isinstance(max_reverse_work, Integral):
        raise TypeError("max_reverse_work must be an integer")
    work_limit = int(max_reverse_work)
    if work_limit < 1 or work_limit > _MAX_REVERSE_WORK:
        raise ValueError("max_reverse_work is outside the hard guard")
    bundle.validate_model_config(model.config, require_exact_terminal=True)

    duration = _floating_tensor(elapsed_time_input, name="elapsed_time_input")
    if duration.dtype != torch.float32 or duration.ndim != 2:
        raise TypeError("elapsed_time_input must be a CPU float32 [batch, positions] tensor")
    batch, positions = duration.shape
    if batch == 0 or positions == 0:
        raise ValueError("reverse sampler requires a non-empty batch and grid")
    sequence = _boolean_mask(
        sequence_mask, name="sequence_mask", shape=(batch, positions)
    )
    discrete_observed = _boolean_mask(
        discrete_observed_mask,
        name="discrete_observed_mask",
        shape=(batch, positions, model.config.num_categorical_fields),
    )
    continuous_observed = _boolean_mask(
        continuous_observed_mask,
        name="continuous_observed_mask",
        shape=(batch, positions, model.config.num_continuous_features),
    )
    time_observed = _boolean_mask(
        elapsed_time_observed_mask,
        name="elapsed_time_observed_mask",
        shape=(batch, positions),
    )
    if positions > model.config.max_sequence_length:
        raise ValueError("reverse grid exceeds model max_sequence_length")
    if batch * positions > model.config.max_batch_tokens:
        raise ValueError("reverse batch exceeds model max_batch_tokens")
    if (
        model.config.backbone == "transformer"
        and batch
        * model.config.num_attention_heads
        * positions
        * positions
        > model.config.max_attention_elements
    ):
        raise ValueError("reverse attention footprint exceeds model resource guard")
    if positions > 1 and bool(
        torch.any((~sequence[:, :-1]) & sequence[:, 1:]).item()
    ):
        raise ValueError("sequence_mask must be a left-aligned prefix mask")
    if bool(torch.any(discrete_observed & ~sequence.unsqueeze(-1)).item()):
        raise ValueError("discrete_observed_mask exposes a padded position")
    if bool(torch.any(continuous_observed & ~sequence.unsqueeze(-1)).item()):
        raise ValueError("continuous_observed_mask exposes a padded position")
    if bool(torch.any(time_observed & ~sequence).item()):
        raise ValueError("elapsed_time_observed_mask exposes a padded position")
    if bool(torch.any(~torch.isfinite(duration[sequence])).item()):
        raise ValueError("elapsed_time_input must be finite at valid positions")
    if bool(torch.any(duration[sequence] < 0.0).item()):
        raise ValueError("elapsed_time_input must be nonnegative at valid positions")
    if bundle.num_diffusion_steps > _MAX_REVERSE_MODEL_CALLS:
        raise ValueError(
            "reverse clock exceeds the hard model-invocation guard"
        )
    categorical_kernel_width = sum(
        schedule.clean_cardinality * schedule.num_states
        for schedule in bundle.categorical
    )
    probability_work = (
        batch
        * positions
        * bundle.num_diffusion_steps
        * (categorical_kernel_width + model.config.num_continuous_features)
    )
    if probability_work > work_limit:
        raise ValueError(
            "reverse probability work exceeds max_reverse_work"
        )
    model_work = (
        batch
        * positions
        * bundle.num_diffusion_steps
        * model.parameter_count
    )
    if model.config.backbone == "transformer":
        model_work += (
            batch
            * model.config.num_attention_heads
            * positions
            * positions
            * model.config.d_model
            * bundle.num_diffusion_steps
        )
    if model_work > _MAX_REVERSE_MODEL_WORK:
        raise ValueError("reverse denoiser work exceeds the hard CPU guard")
    if any(
        parameter.device.type != "cpu" or parameter.dtype != torch.float32
        for parameter in model.parameters()
    ):
        raise ValueError("the frozen reverse sampler requires a CPU float32 model")
    if any(
        bool(torch.any(~torch.isfinite(parameter.detach())).item())
        for parameter in model.parameters()
    ):
        raise ValueError("the frozen reverse sampler requires finite model parameters")
    float32_log_signal = bundle.continuous._log_cumulative_alphas.to(
        dtype=torch.float32
    )
    float32_signal = torch.exp(0.5 * float32_log_signal)
    float32_variance = bundle.continuous._cumulative_variances.to(
        dtype=torch.float32
    )
    invalid_signal = bool(
        torch.any(
            (float32_signal <= 0.0)
            | ~torch.isfinite(float32_signal)
            | ~torch.isfinite(torch.reciprocal(float32_signal))
        ).item()
    )
    invalid_variance = (
        bool(torch.any(~torch.isfinite(float32_variance)).item())
        or bool(torch.any(float32_variance[0] != 0.0).item())
        or bool(torch.any(float32_variance[1:] <= 0.0).item())
    )
    if invalid_signal or invalid_variance:
        raise ValueError(
            "Gaussian reverse clock is not representable for CPU float32 DDIM"
        )

    # Validation above is deliberately RNG-free.  Once sampling begins, make
    # the explicit generator transactional so a rejected/non-finite model call
    # cannot silently consume a prefix of the declared random stream.
    generator_before = active_generator.get_state().clone()
    try:
        discrete = torch.zeros(
            (batch, positions, model.config.num_categorical_fields), dtype=torch.long
        )
        for field, schedule in enumerate(bundle.categorical):
            assert schedule.terminal_state is not None
            discrete[:, :, field] = torch.where(
                sequence,
                torch.full(
                    (batch, positions), schedule.terminal_state, dtype=torch.long
                ),
                torch.zeros((batch, positions), dtype=torch.long),
            )
        continuous = torch.zeros(
            (batch, positions, model.config.num_continuous_features),
            dtype=torch.float32,
        )
        continuous_mask = sequence.unsqueeze(-1).expand_as(continuous)
        count = int(continuous_mask.sum().item())
        if count:
            continuous[continuous_mask] = torch.randn(
                count, dtype=torch.float32, generator=active_generator
            )

        for step in range(bundle.num_diffusion_steps, 0, -1):
            progress = torch.full(
                (batch,), float(bundle._progress[step].item()), dtype=torch.float32
            )
            output = model(
                discrete,
                continuous,
                elapsed_time_input=duration,
                diffusion_progress=progress,
                sequence_mask=sequence,
                discrete_observed_mask=discrete_observed,
                continuous_observed_mask=continuous_observed,
                elapsed_time_observed_mask=time_observed,
            )
            next_fields = []
            for field, schedule in enumerate(bundle.categorical):
                probabilities = categorical_x0_reverse_probabilities(
                    schedule,
                    discrete[:, :, field],
                    output.categorical_logits[field],
                    step,
                    valid_mask=sequence,
                )
                next_fields.append(
                    sample_categorical_reverse(
                        probabilities,
                        generator=active_generator,
                        valid_mask=sequence,
                    )
                )
            discrete = torch.stack(next_fields, dim=-1)
            continuous = ddim_epsilon_step(
                bundle.continuous,
                continuous,
                output.continuous_prediction,
                step,
                valid_mask=continuous_mask,
            )

        for field, schedule in enumerate(bundle.categorical):
            if bool(
                torch.any(
                    discrete[:, :, field][sequence] >= schedule.clean_cardinality
                ).item()
            ):
                raise RuntimeError(
                    "reverse sampler retained a diffusion-only state at step zero"
                )
        return FixedGridReverseSample(
            discrete_state=discrete.clone(), continuous_state=continuous.clone()
        )
    except Exception:
        active_generator.set_state(generator_before)
        raise


__all__ = [
    "FixedGridDiffusionBundle",
    "FixedGridReverseSample",
    "TorchCategoricalSchedule",
    "TorchGaussianCorruption",
    "TorchGaussianPosterior",
    "TorchVPGaussianSchedule",
    "categorical_x0_reverse_probabilities",
    "ddim_epsilon_step",
    "sample_categorical_reverse",
    "sample_fixed_grid_reverse",
]
