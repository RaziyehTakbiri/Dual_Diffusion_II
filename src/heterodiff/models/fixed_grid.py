"""Optional-PyTorch fixed-grid mixed-state reference model.

This module implements a compact clean-room baseline around the model-agnostic
D3PM and VP Gaussian kernels in :mod:`heterodiff.processes.reference`.  It is
not a reproduction of the supplied manuscript: the paper does not specify
enough architectural, optimization, coupling, or time-input details for that.

The forward API accepts only noisy/model-visible state.  In particular, clean
generated time is not a distinct argument.  For every backbone,
``elapsed_time_input`` means the nonnegative physical duration since the
preceding grid position; its first entry is the declared
origin-to-first-position duration.  It is never an absolute event timestamp.
Each duration must be declared observed context, a noisy duration coordinate,
or a provisional prediction supplied by the caller.  Scalar diffusion
progress is a separate input.  The aligned target tensors are accepted only by
:func:`hybrid_denoising_loss`.

Classifier-free guidance, self-conditioning, Gumbel coupling, and
straight-through estimators are deliberately absent because their semantics
are not frozen in the manuscript protocol.  The optional CfC control is the
canonical full cell equation from Hasani et al. and the author implementation,
not a reconstruction of the supplied manuscript's insertion point:

* https://www.nature.com/articles/s42256-022-00556-7
* https://github.com/raminmh/CfC/blob/main/torch_cfc.py

More precisely, it follows ``CfcCell`` on the repository's ``main`` branch as
accessed 2026-07-22 with ``minimal=False`` and ``no_gate=False`` (the repository
README's "full CfC" setting).  Its placement after this reference model's
shared mixed-state encoder is a clean-room engineering choice, not a manuscript
claim.

The loss below is an explicitly labeled hybrid denoising loss, not an ELBO.
"""

from __future__ import annotations

from dataclasses import dataclass
import math
from numbers import Real
from typing import Optional, Tuple

try:
    import torch
    from torch import nn
    from torch.nn import functional as F
except ModuleNotFoundError as error:  # pragma: no cover - exercised without extra
    if error.name == "torch":
        raise ModuleNotFoundError(
            "heterodiff.models.fixed_grid requires the optional PyTorch "
            "dependency; install the 'reference' extra"
        ) from error
    raise

from .reference_config import FixedGridReferenceConfig


_ELAPSED_TIME_CONTROLS = frozenset(
    ("true", "fixed", "zero", "shuffled", "rescaled")
)
_SUPPORTED_STATE_DTYPES = frozenset(
    (torch.uint8, torch.int8, torch.int16, torch.int32, torch.int64)
)


@dataclass(frozen=True)
class FixedGridDenoiserOutput:
    """Clean-``x0`` logits and Gaussian ``epsilon`` on a fixed grid.

    Padded positions are exact zeros.  ``continuous_prediction`` is forward
    Gaussian noise, not clean ``x0``, a score, velocity, posterior mean, or
    learned variance.
    """

    categorical_logits: Tuple[torch.Tensor, ...]
    continuous_prediction: torch.Tensor


@dataclass(frozen=True)
class HybridDenoisingLoss:
    """Auditable field-normalized CE plus feature-normalized squared error."""

    total: torch.Tensor
    categorical: torch.Tensor
    continuous: torch.Tensor
    categorical_by_field: torch.Tensor
    continuous_by_feature: torch.Tensor
    categorical_counts: torch.Tensor
    continuous_counts: torch.Tensor


def _is_true(value: torch.Tensor) -> bool:
    """Convert a scalar boolean tensor explicitly, including on accelerators."""

    return bool(value.detach().item())


def _require_tensor(value: object, name: str) -> torch.Tensor:
    if not isinstance(value, torch.Tensor):
        raise TypeError("{} must be a torch.Tensor".format(name))
    return value


def _require_bool_tensor(
    value: object,
    *,
    name: str,
    shape: Tuple[int, ...],
    device: torch.device,
) -> torch.Tensor:
    tensor = _require_tensor(value, name)
    if tensor.dtype != torch.bool:
        raise TypeError("{} must have boolean dtype".format(name))
    if tuple(tensor.shape) != shape:
        raise ValueError(
            "{} has shape {}; expected {}".format(name, tuple(tensor.shape), shape)
        )
    if tensor.device != device:
        raise ValueError("{} must be on the model/input device".format(name))
    return tensor


def _require_floating_tensor(
    value: object,
    *,
    name: str,
    shape: Tuple[int, ...],
    device: torch.device,
) -> torch.Tensor:
    tensor = _require_tensor(value, name)
    if not torch.is_floating_point(tensor):
        raise TypeError("{} must have a floating-point dtype".format(name))
    if tuple(tensor.shape) != shape:
        raise ValueError(
            "{} has shape {}; expected {}".format(name, tuple(tensor.shape), shape)
        )
    if tensor.device != device:
        raise ValueError("{} must be on the model/input device".format(name))
    return tensor


class _LeCunActivation(nn.Module):
    """Activation used by the canonical author CfC implementation."""

    def forward(self, value: torch.Tensor) -> torch.Tensor:
        return 1.7159 * torch.tanh(0.666 * value)


def _cfc_activation(name: str) -> nn.Module:
    if name == "silu":
        return nn.SiLU()
    if name == "relu":
        return nn.ReLU()
    if name == "tanh":
        return nn.Tanh()
    if name == "gelu":
        return nn.GELU()
    if name == "lecun":
        return _LeCunActivation()
    raise ValueError("unsupported CfC activation")


class CanonicalFullCfcCell(nn.Module):
    """Canonical full gated CfC cell, isolated from the shared denoiser.

    For ``x = backbone(concat(input, hidden))``, this implements the author
    PyTorch full variant exactly at the equation level:

    ``ff1 = tanh(W1 x)``, ``ff2 = tanh(W2 x)``,
    ``gate = sigmoid(time_a(x) * dt + time_b(x))``, and
    ``hidden_new = ff1 * (1 - gate) + gate * ff2``.

    The author's ``no_gate`` and ``minimal`` variants are intentionally not
    aliases of this class.  Weight initialization is left at PyTorch defaults
    because the supplied manuscript does not report the author's optional
    initialization gain.
    """

    def __init__(
        self,
        input_size: int,
        hidden_size: int,
        *,
        backbone_width: int,
        backbone_layers: int,
        backbone_activation: str,
        dropout: float,
    ) -> None:
        super().__init__()
        self.input_size = input_size
        self.hidden_size = hidden_size
        layers = [
            nn.Linear(input_size + hidden_size, backbone_width),
            _cfc_activation(backbone_activation),
        ]
        for _ in range(1, backbone_layers):
            layers.extend(
                (nn.Linear(backbone_width, backbone_width), _cfc_activation(backbone_activation))
            )
        if dropout > 0.0:
            layers.append(nn.Dropout(dropout))
        self.backbone = nn.Sequential(*layers)
        self.ff1 = nn.Linear(backbone_width, hidden_size)
        self.ff2 = nn.Linear(backbone_width, hidden_size)
        self.time_a = nn.Linear(backbone_width, hidden_size)
        self.time_b = nn.Linear(backbone_width, hidden_size)

    def forward(
        self,
        inputs: torch.Tensor,
        hidden: torch.Tensor,
        elapsed_time: torch.Tensor,
    ) -> torch.Tensor:
        inputs = _require_tensor(inputs, "inputs")
        hidden = _require_tensor(hidden, "hidden")
        elapsed_time = _require_tensor(elapsed_time, "elapsed_time")
        if inputs.ndim != 2 or inputs.shape[1] != self.input_size:
            raise ValueError("inputs must have shape [batch, input_size]")
        if tuple(hidden.shape) != (inputs.shape[0], self.hidden_size):
            raise ValueError("hidden must have shape [batch, hidden_size]")
        if elapsed_time.ndim != 1 or elapsed_time.shape[0] != inputs.shape[0]:
            raise ValueError("elapsed_time must have shape [batch]")
        if not all(
            torch.is_floating_point(value)
            for value in (inputs, hidden, elapsed_time)
        ):
            raise TypeError("CfC inputs, hidden state, and elapsed time must be floating")
        parameter = self.ff1.weight
        if any(value.device != parameter.device for value in (inputs, hidden, elapsed_time)):
            raise ValueError("CfC inputs and parameters must share one device")
        if any(
            value.dtype != parameter.dtype
            for value in (inputs, hidden, elapsed_time)
        ):
            raise TypeError(
                "CfC inputs, hidden state, and elapsed time must match the parameter dtype"
            )
        if _is_true(torch.any(~torch.isfinite(inputs))) or _is_true(
            torch.any(~torch.isfinite(hidden))
        ):
            raise ValueError("CfC inputs and hidden state must be finite")
        if _is_true(torch.any(~torch.isfinite(elapsed_time))) or _is_true(
            torch.any(elapsed_time < 0.0)
        ):
            raise ValueError("elapsed_time must be finite and nonnegative")
        backbone_state = self.backbone(torch.cat((inputs, hidden), dim=-1))
        ff1 = torch.tanh(self.ff1(backbone_state))
        ff2 = torch.tanh(self.ff2(backbone_state))
        interpolation = torch.sigmoid(
            self.time_a(backbone_state) * elapsed_time.reshape(-1, 1)
            + self.time_b(backbone_state)
        )
        return ff1 * (1.0 - interpolation) + interpolation * ff2


class PositionwiseGridFeedForwardCore(nn.Module):
    """Bounded grid-FFN control with no cross-position communication.

    Each layer applies ``LayerNorm(x + W2(GELU(W1(x))))`` independently at
    every grid position.  Dropout modules are retained so the declared
    configuration controls training stochasticity, but no attention,
    recurrence, convolution, or time mixing is hidden in this baseline.

    The surrounding :class:`FixedGridReferenceDenoiser` owns the common
    mixed-state encoder (including its ordinary physical-duration and
    diffusion-progress features) and prediction heads.  This core has no
    dedicated time modulation.  It is therefore not an implementation of the
    manuscript's separately named time-conditioned FFN, whose mechanism is
    still unidentified.  This module's input and output both have shape
    ``[batch, positions, d_model]`` and form an explicit common-core comparison
    boundary.
    """

    def __init__(
        self,
        d_model: int,
        feedforward_width: int,
        *,
        num_layers: int,
        dropout: float,
    ) -> None:
        super().__init__()
        self.d_model = d_model
        self.layers = nn.ModuleList()
        for _ in range(num_layers):
            self.layers.append(
                nn.ModuleDict(
                    {
                        "linear1": nn.Linear(d_model, feedforward_width),
                        "linear2": nn.Linear(feedforward_width, d_model),
                        "dropout1": nn.Dropout(dropout),
                        "dropout2": nn.Dropout(dropout),
                        "norm": nn.LayerNorm(d_model),
                    }
                )
            )

    def forward(self, inputs: torch.Tensor) -> torch.Tensor:
        inputs = _require_tensor(inputs, "inputs")
        if inputs.ndim != 3 or inputs.shape[-1] != self.d_model:
            raise ValueError(
                "grid-FFN inputs must have shape [batch, positions, d_model]"
            )
        parameter = self.layers[0]["linear1"].weight
        if inputs.device != parameter.device:
            raise ValueError("grid-FFN inputs and parameters must share one device")
        if inputs.dtype != parameter.dtype:
            raise TypeError("grid-FFN inputs must match the parameter dtype")
        if _is_true(torch.any(~torch.isfinite(inputs))):
            raise ValueError("grid-FFN inputs must be finite")
        hidden = inputs
        for layer in self.layers:
            residual = layer["linear2"](
                layer["dropout1"](F.gelu(layer["linear1"](hidden)))
            )
            hidden = layer["norm"](hidden + layer["dropout2"](residual))
        return hidden


def controlled_elapsed_time(
    elapsed_time: torch.Tensor,
    sequence_mask: torch.Tensor,
    *,
    control: str,
    fixed_value: float = 1.0,
    rescale_factor: float = 1.0,
    shuffle_indices: Optional[torch.Tensor] = None,
) -> torch.Tensor:
    """Apply a weight-preserving physical-duration intervention.

    ``elapsed_time`` contains inter-position durations, not absolute event
    timestamps.  Its first valid entry is the origin-to-first-position
    duration.  The historical argument name is retained to avoid a breaking
    API change.

    ``shuffled`` requires an explicit per-row permutation.  For each sample its
    first ``sequence_mask.sum()`` indices must be a permutation of that valid
    prefix; padded indices are ignored.  Requiring the permutation as data
    avoids hidden global RNG state and makes the intervention auditable.
    """

    elapsed = _require_tensor(elapsed_time, "elapsed_time")
    sequence = _require_tensor(sequence_mask, "sequence_mask")
    if elapsed.ndim != 2 or tuple(sequence.shape) != tuple(elapsed.shape):
        raise ValueError("elapsed_time and sequence_mask must share shape [batch, positions]")
    if elapsed.shape[0] == 0 or elapsed.shape[1] == 0:
        raise ValueError("elapsed_time must contain a non-empty batch and grid")
    if not torch.is_floating_point(elapsed):
        raise TypeError("elapsed_time must have floating-point dtype")
    if sequence.dtype != torch.bool:
        raise TypeError("sequence_mask must have boolean dtype")
    if elapsed.device != sequence.device:
        raise ValueError("elapsed_time and sequence_mask must share one device")
    if elapsed.shape[1] > 1 and _is_true(
        torch.any(torch.logical_and(~sequence[:, :-1], sequence[:, 1:]))
    ):
        raise ValueError("sequence_mask must be a left-aligned prefix mask")
    if not isinstance(control, str) or control not in _ELAPSED_TIME_CONTROLS:
        raise ValueError(
            "elapsed-time control must be one of {}"
            .format(sorted(_ELAPSED_TIME_CONTROLS))
        )
    valid_values = elapsed[sequence]
    if _is_true(torch.any(~torch.isfinite(valid_values))):
        raise ValueError("elapsed_time must be finite at valid positions")
    if _is_true(torch.any(valid_values < 0.0)):
        raise ValueError("elapsed_time must be nonnegative at valid positions")

    fixed = _loss_weight(fixed_value, "fixed_value")
    factor = _loss_weight(rescale_factor, "rescale_factor")
    fixed_scalar = torch.as_tensor(fixed, dtype=elapsed.dtype, device=elapsed.device)
    factor_scalar = torch.as_tensor(factor, dtype=elapsed.dtype, device=elapsed.device)
    if not _is_true(torch.isfinite(fixed_scalar)):
        raise ValueError("fixed_value is not representable in the elapsed_time dtype")
    if not _is_true(torch.isfinite(factor_scalar)):
        raise ValueError("rescale_factor is not representable in the elapsed_time dtype")
    if control == "rescaled" and factor == 0.0:
        raise ValueError("rescale_factor must be positive for rescaled control")
    safe = torch.where(sequence, elapsed, torch.zeros_like(elapsed))
    if control == "true":
        result = safe
    elif control == "fixed":
        result = torch.where(sequence, torch.full_like(safe, fixed), safe)
    elif control == "zero":
        result = torch.zeros_like(safe)
    elif control == "rescaled":
        result = safe * factor_scalar
    else:
        indices = _require_tensor(shuffle_indices, "shuffle_indices")
        if (
            indices.dtype == torch.bool
            or torch.is_floating_point(indices)
            or torch.is_complex(indices)
        ):
            raise TypeError("shuffle_indices must have integer dtype")
        if tuple(indices.shape) != tuple(elapsed.shape) or indices.device != elapsed.device:
            raise ValueError("shuffle_indices must align with elapsed_time on the same device")
        indices = indices.to(dtype=torch.long)
        result = torch.zeros_like(safe)
        for row in range(elapsed.shape[0]):
            length = int(sequence[row].sum().detach().item())
            row_indices = indices[row, :length]
            if length and not torch.equal(
                torch.sort(row_indices).values,
                torch.arange(length, device=elapsed.device),
            ):
                raise ValueError(
                    "shuffle_indices row {} is not a permutation of its valid prefix"
                    .format(row)
                )
            if length:
                result[row, :length] = safe[row, row_indices]
    if _is_true(torch.any(~torch.isfinite(result[sequence]))):
        raise ValueError("elapsed-time control produced a non-finite valid value")
    return result


class FixedGridReferenceDenoiser(nn.Module):
    """Shared denoiser with Transformer, grid-FFN, GRU, or full-CfC core.

    Input shapes are ``[batch, positions, fields]`` for categorical state,
    ``[batch, positions, features]`` for continuous state, and
    ``[batch, positions]`` for elapsed time and the prefix sequence mask.
    ``elapsed_time_input`` contains nonnegative physical inter-position
    durations (including the origin-to-first duration at position zero), never
    absolute timestamps.  ``diffusion_progress`` has shape ``[batch]`` and
    must lie in ``[0, 1]``; it is a separate diffusion-clock input.

    Every categorical head predicts clean ``x0`` logits on its configured
    clean support.  The continuous head predicts forward Gaussian noise
    ``epsilon``.  Reverse-kernel mixing and deterministic DDIM conversion are
    sampler responsibilities, not hidden behaviors of this module.

    Observation masks are model-visible task information.  They are distinct
    from loss masks and must be false outside ``sequence_mask``.  The sequence
    mask is required to be a prefix mask because this fixed-grid reference
    treats length/padding as known batching context; it is not an interface for
    hidden-cardinality conditioning.
    """

    def __init__(self, config: FixedGridReferenceConfig) -> None:
        super().__init__()
        if not isinstance(config, FixedGridReferenceConfig):
            raise TypeError("config must be a FixedGridReferenceConfig")
        self.config = config

        # The framework-free estimate is checked while constructing the
        # config, before any potentially large PyTorch tensors are allocated.
        if config.estimated_parameter_count > config.parameter_budget:
            raise ValueError("estimated model size exceeds parameter_budget")

        self.categorical_embeddings = nn.ModuleList(
            nn.Embedding(cardinality, config.d_model)
            for cardinality in config.categorical_cardinalities
        )
        self.continuous_input = nn.Linear(
            2 * config.num_continuous_features, config.d_model
        )
        self.categorical_observation_input = nn.Linear(
            config.num_categorical_fields, config.d_model
        )
        self.elapsed_time_value_feature = (
            None if config.backbone == "cfc" else nn.Linear(1, config.d_model)
        )
        self.elapsed_time_observation_feature = nn.Linear(1, config.d_model)
        self.diffusion_time_input = nn.Linear(1, config.d_model)
        self.position_embedding = nn.Embedding(
            config.max_sequence_length, config.d_model
        )
        self.input_norm = nn.LayerNorm(config.d_model)

        if config.backbone == "transformer":
            layer = nn.TransformerEncoderLayer(
                d_model=config.d_model,
                nhead=config.num_attention_heads,
                dim_feedforward=config.feedforward_width,
                dropout=config.dropout,
                activation="gelu",
                batch_first=True,
                norm_first=False,
            )
            self.core = nn.TransformerEncoder(
                layer,
                num_layers=config.num_layers,
                norm=nn.LayerNorm(config.d_model),
                # The frozen CPU path uses ordinary dense tensors.  Disabling
                # the prototype nested-tensor fast path avoids a version-
                # dependent representation switch (and warning) between
                # gradient-enabled training and no-grad reverse sampling.
                enable_nested_tensor=False,
            )
        elif config.backbone == "grid_ffn":
            self.core = PositionwiseGridFeedForwardCore(
                config.d_model,
                config.feedforward_width,
                num_layers=config.num_layers,
                dropout=config.dropout,
            )
        elif config.backbone == "gru":
            self.core = nn.GRU(
                input_size=config.d_model,
                hidden_size=config.d_model,
                num_layers=config.num_layers,
                batch_first=True,
                dropout=config.dropout if config.num_layers > 1 else 0.0,
                bidirectional=False,
            )
        else:
            self.core = CanonicalFullCfcCell(
                config.d_model,
                config.d_model,
                backbone_width=config.feedforward_width,
                backbone_layers=config.cfc_backbone_layers,
                backbone_activation=config.cfc_activation,
                dropout=config.dropout,
            )

        self.categorical_heads = nn.ModuleList(
            nn.Linear(config.d_model, cardinality)
            for cardinality in config.categorical_output_cardinalities
        )
        self.continuous_head = nn.Linear(
            config.d_model, config.num_continuous_features
        )

        parameter_count = sum(parameter.numel() for parameter in self.parameters())
        if parameter_count != config.estimated_parameter_count:
            raise RuntimeError(
                "parameter-count contract mismatch: estimated {}, constructed {}"
                .format(config.estimated_parameter_count, parameter_count)
            )

    @property
    def parameter_count(self) -> int:
        """Return the exact number of trainable and frozen scalar parameters."""

        return sum(parameter.numel() for parameter in self.parameters())

    def forward(
        self,
        discrete_noisy_state: torch.Tensor,
        continuous_noisy_state: torch.Tensor,
        *,
        elapsed_time_input: torch.Tensor,
        diffusion_progress: torch.Tensor,
        sequence_mask: torch.Tensor,
        discrete_observed_mask: torch.Tensor,
        continuous_observed_mask: torch.Tensor,
        elapsed_time_observed_mask: torch.Tensor,
        elapsed_time_control: str = "true",
        fixed_elapsed_time: float = 1.0,
        elapsed_time_rescale_factor: float = 1.0,
        elapsed_time_shuffle_indices: Optional[torch.Tensor] = None,
    ) -> FixedGridDenoiserOutput:
        discrete = _require_tensor(discrete_noisy_state, "discrete_noisy_state")
        if discrete.dtype not in _SUPPORTED_STATE_DTYPES:
            raise TypeError(
                "discrete_noisy_state must use a supported 8/16/32/64-bit "
                "signed or uint8 integer dtype"
            )
        if discrete.ndim != 3:
            raise ValueError(
                "discrete_noisy_state must have shape [batch, positions, fields]"
            )
        batch, positions, categorical_fields = discrete.shape
        if batch == 0:
            raise ValueError("the fixed-grid batch must contain at least one sample")
        if categorical_fields != self.config.num_categorical_fields:
            raise ValueError(
                "discrete_noisy_state has {} fields; expected {}"
                .format(categorical_fields, self.config.num_categorical_fields)
            )
        if positions == 0:
            raise ValueError("the fixed grid must contain at least one position")
        if positions > self.config.max_sequence_length:
            raise ValueError(
                "sequence length {} exceeds max_sequence_length={}"
                .format(positions, self.config.max_sequence_length)
            )
        if batch * positions > self.config.max_batch_tokens:
            raise ValueError(
                "batch contains {} tokens, exceeding max_batch_tokens={}"
                .format(batch * positions, self.config.max_batch_tokens)
            )
        if (
            self.config.backbone == "transformer"
            and batch
            * self.config.num_attention_heads
            * positions
            * positions
            > self.config.max_attention_elements
        ):
            raise ValueError(
                "attention score footprint exceeds max_attention_elements={}"
                .format(self.config.max_attention_elements)
            )

        model_parameter = self.position_embedding.weight
        device = model_parameter.device
        if discrete.device != device:
            raise ValueError("all inputs must be on the model device")
        sequence = _require_bool_tensor(
            sequence_mask,
            name="sequence_mask",
            shape=(batch, positions),
            device=device,
        )
        if positions > 1 and _is_true(
            torch.any(torch.logical_and(torch.logical_not(sequence[:, :-1]), sequence[:, 1:]))
        ):
            raise ValueError("sequence_mask must be a left-aligned prefix mask")

        discrete_observed = _require_bool_tensor(
            discrete_observed_mask,
            name="discrete_observed_mask",
            shape=(batch, positions, categorical_fields),
            device=device,
        )
        continuous_observed = _require_bool_tensor(
            continuous_observed_mask,
            name="continuous_observed_mask",
            shape=(batch, positions, self.config.num_continuous_features),
            device=device,
        )
        time_observed = _require_bool_tensor(
            elapsed_time_observed_mask,
            name="elapsed_time_observed_mask",
            shape=(batch, positions),
            device=device,
        )
        if _is_true(torch.any(discrete_observed & ~sequence.unsqueeze(-1))):
            raise ValueError("discrete_observed_mask exposes a padded position")
        if _is_true(torch.any(continuous_observed & ~sequence.unsqueeze(-1))):
            raise ValueError("continuous_observed_mask exposes a padded position")
        if _is_true(torch.any(time_observed & ~sequence)):
            raise ValueError("elapsed_time_observed_mask exposes a padded position")

        continuous = _require_floating_tensor(
            continuous_noisy_state,
            name="continuous_noisy_state",
            shape=(batch, positions, self.config.num_continuous_features),
            device=device,
        )
        elapsed_time = _require_floating_tensor(
            elapsed_time_input,
            name="elapsed_time_input",
            shape=(batch, positions),
            device=device,
        )
        diffusion = _require_floating_tensor(
            diffusion_progress,
            name="diffusion_progress",
            shape=(batch,),
            device=device,
        )
        if _is_true(torch.any(~torch.isfinite(continuous[sequence]))):
            raise ValueError("continuous_noisy_state must be finite at valid positions")
        if _is_true(torch.any(~torch.isfinite(diffusion))):
            raise ValueError("diffusion_progress must be finite")
        if _is_true(torch.any((diffusion < 0.0) | (diffusion > 1.0))):
            raise ValueError("diffusion_progress must lie in [0, 1]")

        safe_discrete = torch.where(
            sequence.unsqueeze(-1), discrete, torch.zeros_like(discrete)
        ).to(dtype=torch.long)
        for field, cardinality in enumerate(self.config.categorical_cardinalities):
            active_values = safe_discrete[:, :, field][sequence]
            if _is_true(torch.any((active_values < 0) | (active_values >= cardinality))):
                raise ValueError(
                    "discrete_noisy_state field {} contains a valid-position state "
                    "outside [0, {})".format(field, cardinality)
                )

        dtype = model_parameter.dtype
        safe_continuous = torch.where(
            sequence.unsqueeze(-1), continuous, torch.zeros_like(continuous)
        ).to(dtype=dtype)
        if _is_true(torch.any(~torch.isfinite(safe_continuous[sequence]))):
            raise ValueError(
                "continuous_noisy_state is not representable in the model dtype"
            )
        controlled_time = controlled_elapsed_time(
            elapsed_time,
            sequence,
            control=elapsed_time_control,
            fixed_value=fixed_elapsed_time,
            rescale_factor=elapsed_time_rescale_factor,
            shuffle_indices=elapsed_time_shuffle_indices,
        )
        safe_elapsed_time = controlled_time.to(dtype=dtype)
        if _is_true(torch.any(~torch.isfinite(safe_elapsed_time[sequence]))):
            raise ValueError(
                "elapsed_time_input is not representable in the model dtype"
            )
        safe_diffusion = diffusion.to(dtype=dtype)
        if _is_true(torch.any(~torch.isfinite(safe_diffusion))):
            raise ValueError(
                "diffusion_progress is not representable in the model dtype"
            )

        hidden = torch.zeros(
            (batch, positions, self.config.d_model),
            dtype=dtype,
            device=device,
        )
        for field, embedding in enumerate(self.categorical_embeddings):
            hidden = hidden + embedding(safe_discrete[:, :, field])
        hidden = hidden + self.continuous_input(
            torch.cat(
                (safe_continuous, continuous_observed.to(dtype=dtype)), dim=-1
            )
        )
        hidden = hidden + self.categorical_observation_input(
            discrete_observed.to(dtype=dtype)
        )
        hidden = hidden + self.elapsed_time_observation_feature(
            time_observed.to(dtype=dtype).unsqueeze(-1)
        )
        # In the canonical CfC control, elapsed time enters only through the
        # cell's explicit ``time_a(x) * dt + time_b(x)`` gate.  Injecting it a
        # second time as an ordinary input feature would no longer isolate that
        # equation. Transformer and GRU controls receive the same value through
        # an ordinary linear feature because they have no separate time gate.
        if self.config.backbone != "cfc":
            assert self.elapsed_time_value_feature is not None
            hidden = hidden + self.elapsed_time_value_feature(
                safe_elapsed_time.unsqueeze(-1)
            )
        hidden = hidden + self.diffusion_time_input(
            safe_diffusion.reshape(batch, 1, 1)
        )
        positions_index = torch.arange(positions, device=device)
        hidden = hidden + self.position_embedding(positions_index).unsqueeze(0)
        hidden = self.input_norm(hidden)
        hidden = torch.where(
            sequence.unsqueeze(-1), hidden, torch.zeros_like(hidden)
        )

        if self.config.backbone == "transformer":
            effective_valid = sequence.clone()
            empty_rows = ~torch.any(effective_valid, dim=1)
            if _is_true(torch.any(empty_rows)):
                effective_valid[empty_rows, 0] = True
            encoded = self.core(
                hidden, src_key_padding_mask=torch.logical_not(effective_valid)
            )
        elif self.config.backbone == "grid_ffn":
            encoded = self.core(hidden)
        elif self.config.backbone == "gru":
            encoded, _ = self.core(hidden)
        else:
            recurrent_state = torch.zeros(
                (batch, self.config.d_model), dtype=hidden.dtype, device=hidden.device
            )
            recurrent_outputs = []
            for position in range(positions):
                candidate = self.core(
                    hidden[:, position],
                    recurrent_state,
                    safe_elapsed_time[:, position],
                )
                valid = sequence[:, position].unsqueeze(-1)
                recurrent_state = torch.where(valid, candidate, recurrent_state)
                recurrent_outputs.append(
                    torch.where(valid, recurrent_state, torch.zeros_like(recurrent_state))
                )
            encoded = torch.stack(recurrent_outputs, dim=1)
        encoded = torch.where(
            sequence.unsqueeze(-1), encoded, torch.zeros_like(encoded)
        )

        categorical_logits = tuple(
            torch.where(
                sequence.unsqueeze(-1), head(encoded), torch.zeros(
                    (batch, positions, head.out_features),
                    dtype=encoded.dtype,
                    device=encoded.device,
                )
            )
            for head in self.categorical_heads
        )
        continuous_prediction = torch.where(
            sequence.unsqueeze(-1),
            self.continuous_head(encoded),
            torch.zeros(
                (batch, positions, self.config.num_continuous_features),
                dtype=encoded.dtype,
                device=encoded.device,
            ),
        )
        if _is_true(
            torch.any(
                ~torch.isfinite(continuous_prediction[sequence])
            )
        ):
            raise FloatingPointError("continuous prediction is non-finite")
        for field, logits in enumerate(categorical_logits):
            if _is_true(torch.any(~torch.isfinite(logits[sequence]))):
                raise FloatingPointError(
                    "categorical logits for field {} are non-finite".format(field)
                )
        return FixedGridDenoiserOutput(
            categorical_logits=categorical_logits,
            continuous_prediction=continuous_prediction,
        )


def _loss_weight(value: object, name: str) -> float:
    if isinstance(value, bool) or not isinstance(value, Real):
        raise TypeError("{} must be a real number".format(name))
    result = float(value)
    if not math.isfinite(result) or result < 0.0:
        raise ValueError("{} must be finite and nonnegative".format(name))
    return result


def hybrid_denoising_loss(
    output: FixedGridDenoiserOutput,
    *,
    discrete_target: torch.Tensor,
    continuous_target: torch.Tensor,
    sequence_mask: torch.Tensor,
    discrete_loss_mask: torch.Tensor,
    continuous_loss_mask: torch.Tensor,
    categorical_weight: float = 1.0,
    continuous_weight: float = 1.0,
) -> HybridDenoisingLoss:
    """Assemble clean-``x0`` CE plus Gaussian-``epsilon`` MSE.

    Each categorical field and continuous feature is normalized independently
    by ``max(1, active_count)`` and the normalized field/feature losses are then
    summed.  Consequently frequent fields cannot dominate merely by having
    more observed sites.  A field with no active target contributes exactly
    zero.  Masked target/logit entries are replaced before arithmetic, so a
    sentinel (including a non-finite continuous sentinel) cannot contaminate
    the result.

    ``discrete_target`` contains clean categorical ``x0`` states and
    ``continuous_target`` contains the exact forward Gaussian noise used to
    construct the noisy input.  ``discrete_loss_mask`` and
    ``continuous_loss_mask`` are supervision masks,
    not the model-visible observation masks used by the denoiser.  They must be
    explicit subsets of ``sequence_mask``.  No focal, SNR, or modality-specific
    timestep weighting is silently applied.
    """

    if not isinstance(output, FixedGridDenoiserOutput):
        raise TypeError("output must be a FixedGridDenoiserOutput")
    if not output.categorical_logits:
        raise ValueError("output must contain at least one categorical field")
    continuous_prediction = _require_tensor(
        output.continuous_prediction, "output.continuous_prediction"
    )
    if continuous_prediction.ndim != 3 or not torch.is_floating_point(
        continuous_prediction
    ):
        raise ValueError(
            "continuous_prediction must be floating with shape [batch, positions, features]"
        )
    batch, positions, continuous_features = continuous_prediction.shape
    if batch == 0 or positions == 0 or continuous_features == 0:
        raise ValueError(
            "continuous_prediction must contain a non-empty batch, grid, and feature axis"
        )
    device = continuous_prediction.device
    categorical_fields = len(output.categorical_logits)

    categorical_scale = _loss_weight(categorical_weight, "categorical_weight")
    continuous_scale = _loss_weight(continuous_weight, "continuous_weight")
    if categorical_scale == 0.0 and continuous_scale == 0.0:
        raise ValueError("at least one modality weight must be positive")

    sequence = _require_bool_tensor(
        sequence_mask,
        name="sequence_mask",
        shape=(batch, positions),
        device=device,
    )
    discrete_mask = _require_bool_tensor(
        discrete_loss_mask,
        name="discrete_loss_mask",
        shape=(batch, positions, categorical_fields),
        device=device,
    )
    continuous_mask = _require_bool_tensor(
        continuous_loss_mask,
        name="continuous_loss_mask",
        shape=(batch, positions, continuous_features),
        device=device,
    )
    if _is_true(torch.any(discrete_mask & ~sequence.unsqueeze(-1))):
        raise ValueError("discrete_loss_mask includes a padded position")
    if _is_true(torch.any(continuous_mask & ~sequence.unsqueeze(-1))):
        raise ValueError("continuous_loss_mask includes a padded position")

    discrete_targets = _require_tensor(discrete_target, "discrete_target")
    if discrete_targets.dtype not in _SUPPORTED_STATE_DTYPES:
        raise TypeError(
            "discrete_target must use a supported 8/16/32/64-bit signed or "
            "uint8 integer dtype"
        )
    if tuple(discrete_targets.shape) != (batch, positions, categorical_fields):
        raise ValueError("discrete_target has the wrong shape")
    if discrete_targets.device != device:
        raise ValueError("all loss inputs must be on the output device")
    continuous_targets = _require_floating_tensor(
        continuous_target,
        name="continuous_target",
        shape=(batch, positions, continuous_features),
        device=device,
    )

    categorical_losses = []
    categorical_counts = []
    for field, logits in enumerate(output.categorical_logits):
        logits = _require_tensor(logits, "categorical_logits[{}]".format(field))
        if logits.ndim != 3 or not torch.is_floating_point(logits):
            raise ValueError("categorical logits must be floating rank-three tensors")
        if tuple(logits.shape[:2]) != (batch, positions):
            raise ValueError("categorical logits do not align with continuous prediction")
        if logits.shape[-1] < 2:
            raise ValueError("every categorical field must have at least two states")
        if logits.device != device:
            raise ValueError("all output tensors must share one device")

        field_mask = discrete_mask[:, :, field] & sequence
        active_targets = discrete_targets[:, :, field][field_mask]
        if _is_true(
            torch.any((active_targets < 0) | (active_targets >= logits.shape[-1]))
        ):
            raise ValueError(
                "discrete_target field {} contains an active state outside [0, {})"
                .format(field, logits.shape[-1])
            )
        if _is_true(torch.any(~torch.isfinite(logits[field_mask]))):
            raise FloatingPointError(
                "categorical logits are non-finite at an active loss site"
            )
        safe_logits = torch.where(
            field_mask.unsqueeze(-1), logits, torch.zeros_like(logits)
        )
        safe_target = torch.where(
            field_mask,
            discrete_targets[:, :, field],
            torch.zeros_like(discrete_targets[:, :, field]),
        ).to(dtype=torch.long)
        per_site = F.cross_entropy(
            safe_logits.reshape(-1, logits.shape[-1]),
            safe_target.reshape(-1),
            reduction="none",
        ).reshape(batch, positions)
        if _is_true(torch.any(~torch.isfinite(per_site[field_mask]))):
            raise FloatingPointError(
                "categorical cross entropy is non-finite at an active loss site"
            )
        count = field_mask.sum()
        field_loss = (per_site * field_mask.to(dtype=per_site.dtype)).sum()
        field_loss = field_loss / count.clamp(min=1).to(dtype=per_site.dtype)
        categorical_losses.append(field_loss)
        categorical_counts.append(count)

    categorical_by_field = torch.stack(categorical_losses)
    categorical_count_tensor = torch.stack(categorical_counts)
    categorical_loss = categorical_by_field.sum()

    if _is_true(
        torch.any(
            ~torch.isfinite(continuous_targets[continuous_mask & sequence.unsqueeze(-1)])
        )
    ):
        raise ValueError("continuous_target is non-finite at an active loss site")
    if _is_true(
        torch.any(
            ~torch.isfinite(
                continuous_prediction[continuous_mask & sequence.unsqueeze(-1)]
            )
        )
    ):
        raise FloatingPointError(
            "continuous prediction is non-finite at an active loss site"
        )
    active_continuous = continuous_mask & sequence.unsqueeze(-1)
    safe_prediction = torch.where(
        active_continuous,
        continuous_prediction,
        torch.zeros_like(continuous_prediction),
    )
    safe_continuous_target = torch.where(
        active_continuous,
        continuous_targets,
        torch.zeros_like(continuous_targets),
    ).to(dtype=continuous_prediction.dtype)
    if _is_true(
        torch.any(~torch.isfinite(safe_continuous_target[active_continuous]))
    ):
        raise ValueError(
            "continuous_target is not representable in the prediction dtype"
        )
    squared_error = (safe_prediction - safe_continuous_target).square()
    if _is_true(torch.any(~torch.isfinite(squared_error[active_continuous]))):
        raise FloatingPointError(
            "continuous squared error is non-finite at an active loss site"
        )
    continuous_counts = active_continuous.sum(dim=(0, 1))
    continuous_by_feature = squared_error.sum(dim=(0, 1)) / continuous_counts.clamp(
        min=1
    ).to(dtype=squared_error.dtype)
    continuous_loss = continuous_by_feature.sum()

    total = (
        categorical_scale * categorical_loss
        + continuous_scale * continuous_loss
    )
    if _is_true(~torch.isfinite(total)):
        raise FloatingPointError(
            "weighted hybrid denoising loss is non-finite"
        )
    return HybridDenoisingLoss(
        total=total,
        categorical=categorical_loss,
        continuous=continuous_loss,
        categorical_by_field=categorical_by_field,
        continuous_by_feature=continuous_by_feature,
        categorical_counts=categorical_count_tensor,
        continuous_counts=continuous_counts,
    )


__all__ = [
    "CanonicalFullCfcCell",
    "FixedGridDenoiserOutput",
    "FixedGridReferenceConfig",
    "FixedGridReferenceDenoiser",
    "HybridDenoisingLoss",
    "PositionwiseGridFeedForwardCore",
    "controlled_elapsed_time",
    "hybrid_denoising_loss",
]
