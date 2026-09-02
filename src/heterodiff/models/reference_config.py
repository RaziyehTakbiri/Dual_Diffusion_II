"""Framework-free configuration for the fixed-grid neural reference.

This is a clean-room engineering configuration, not a reconstruction of
undocumented manuscript hyperparameters.  Its hard limits make accidental
multi-gigabyte models or batches fail before PyTorch allocates them.
"""

from __future__ import annotations

from dataclasses import dataclass
import math
from numbers import Integral, Real
from typing import Optional, Tuple


_BACKBONES = frozenset(("transformer", "grid_ffn", "gru", "cfc"))
_CFC_ACTIVATIONS = frozenset(("silu", "relu", "tanh", "gelu", "lecun"))
_MAX_CATEGORICAL_FIELDS = 64
_MAX_CATEGORY_CARDINALITY = 65_536
_MAX_EMBEDDING_ELEMENTS = 50_000_000
_MAX_CONTINUOUS_FEATURES = 4_096
_MAX_MODEL_WIDTH = 2_048
_MAX_LAYERS = 48
_MAX_FEEDFORWARD_WIDTH = 16_384
_MAX_SEQUENCE_LENGTH = 16_384
_MAX_BATCH_TOKENS = 10_000_000
_MAX_ATTENTION_ELEMENTS = 1_000_000_000
_MAX_PARAMETER_BUDGET = 250_000_000


def _integer(
    value: object,
    *,
    name: str,
    minimum: int,
    maximum: int,
) -> int:
    if isinstance(value, bool) or not isinstance(value, Integral):
        raise TypeError("{} must be an integer".format(name))
    result = int(value)
    if result < minimum or result > maximum:
        raise ValueError(
            "{} must lie in [{}, {}]".format(name, minimum, maximum)
        )
    return result


@dataclass(frozen=True)
class FixedGridReferenceConfig:
    """Validated architecture contract for a compact mixed-state denoiser.

    ``categorical_cardinalities`` describes the *noisy* state spaces accepted
    by the model, so an absorbing D3PM mask state must be included.
    ``categorical_output_cardinalities`` independently freezes the clean
    ``x0`` logit support.  A diffusion-only absorbing mask must therefore be
    excluded from this output support.  ``None`` is valid only when clean and
    noisy supports coincide; it conservatively uses the noisy-state support
    because the framework-free record cannot infer mask identity.  The
    continuous head has the separately frozen Gaussian-noise ``epsilon``
    parameterization.  The GRU is a
    bounded, unidirectional recurrent control.  ``backbone='grid_ffn'`` is a
    strictly positionwise residual feed-forward control: it uses the same
    mixed-state encoder, time inputs, positional embedding, and prediction
    heads as the Transformer, but it cannot exchange information between grid
    positions.  It receives time only through the shared encoder and has no
    dedicated time modulation inside its core; it is not the separately
    reported time-conditioned FFN whose mechanism remains unspecified.
    ``backbone='cfc'`` selects a
    separately identified single-cell implementation of the canonical full
    CfC equation; it is never inferred from the manuscript's undocumented
    insertion point.  All backbones use the same input and prediction heads.

    At the model boundary, ``elapsed_time_input`` (defined by the concrete
    PyTorch module) means a nonnegative physical *inter-position duration*.
    Entry zero is the declared origin-to-first-position duration.  It is never
    an absolute timestamp and is separate from scalar diffusion progress.
    """

    categorical_cardinalities: Tuple[int, ...]
    num_continuous_features: int
    categorical_output_cardinalities: Optional[Tuple[int, ...]] = None
    backbone: str = "transformer"
    d_model: int = 128
    num_layers: int = 2
    num_attention_heads: int = 4
    feedforward_width: int = 512
    cfc_backbone_layers: int = 1
    cfc_activation: str = "lecun"
    dropout: float = 0.0
    max_sequence_length: int = 256
    max_batch_tokens: int = 32_768
    max_attention_elements: int = 16_777_216
    parameter_budget: int = 50_000_000

    def __post_init__(self) -> None:
        try:
            cardinalities = tuple(self.categorical_cardinalities)
        except TypeError as error:
            raise TypeError(
                "categorical_cardinalities must be a finite iterable"
            ) from error
        if not cardinalities:
            raise ValueError("at least one categorical field is required")
        if len(cardinalities) > _MAX_CATEGORICAL_FIELDS:
            raise ValueError(
                "categorical_cardinalities exceeds the field-count guard of {}"
                .format(_MAX_CATEGORICAL_FIELDS)
            )
        validated_cardinalities = tuple(
            _integer(
                value,
                name="categorical_cardinalities[{}]".format(index),
                minimum=2,
                maximum=_MAX_CATEGORY_CARDINALITY,
            )
            for index, value in enumerate(cardinalities)
        )
        if self.categorical_output_cardinalities is None:
            output_cardinalities = validated_cardinalities
        else:
            try:
                output_values = tuple(self.categorical_output_cardinalities)
            except TypeError as error:
                raise TypeError(
                    "categorical_output_cardinalities must be a finite iterable or None"
                ) from error
            if len(output_values) != len(validated_cardinalities):
                raise ValueError(
                    "categorical_output_cardinalities must have one entry per field"
                )
            output_cardinalities = tuple(
                _integer(
                    value,
                    name="categorical_output_cardinalities[{}]".format(index),
                    minimum=2,
                    maximum=_MAX_CATEGORY_CARDINALITY,
                )
                for index, value in enumerate(output_values)
            )
            for index, (clean_cardinality, noisy_cardinality) in enumerate(
                zip(output_cardinalities, validated_cardinalities)
            ):
                if clean_cardinality > noisy_cardinality:
                    raise ValueError(
                        "categorical_output_cardinalities[{}] cannot exceed "
                        "categorical_cardinalities[{}]".format(index, index)
                    )

        if not isinstance(self.backbone, str):
            raise TypeError("backbone must be a string")
        if self.backbone not in _BACKBONES:
            raise ValueError(
                "backbone must be 'transformer', 'grid_ffn', 'gru', or 'cfc'"
            )

        continuous = _integer(
            self.num_continuous_features,
            name="num_continuous_features",
            minimum=1,
            maximum=_MAX_CONTINUOUS_FEATURES,
        )
        width = _integer(
            self.d_model,
            name="d_model",
            minimum=4,
            maximum=_MAX_MODEL_WIDTH,
        )
        layers = _integer(
            self.num_layers,
            name="num_layers",
            minimum=1,
            maximum=_MAX_LAYERS,
        )
        heads = _integer(
            self.num_attention_heads,
            name="num_attention_heads",
            minimum=1,
            maximum=_MAX_MODEL_WIDTH,
        )
        if width % heads != 0:
            raise ValueError("d_model must be divisible by num_attention_heads")
        feedforward = _integer(
            self.feedforward_width,
            name="feedforward_width",
            minimum=width,
            maximum=_MAX_FEEDFORWARD_WIDTH,
        )
        cfc_layers = _integer(
            self.cfc_backbone_layers,
            name="cfc_backbone_layers",
            minimum=1,
            maximum=16,
        )
        if not isinstance(self.cfc_activation, str):
            raise TypeError("cfc_activation must be a string")
        if self.cfc_activation not in _CFC_ACTIVATIONS:
            raise ValueError(
                "cfc_activation must be one of {}"
                .format(sorted(_CFC_ACTIVATIONS))
            )
        if self.backbone == "cfc" and layers != 1:
            raise ValueError(
                "the isolated canonical CfC control uses exactly one recurrent cell; "
                "set num_layers=1"
            )
        maximum_length = _integer(
            self.max_sequence_length,
            name="max_sequence_length",
            minimum=1,
            maximum=_MAX_SEQUENCE_LENGTH,
        )
        maximum_tokens = _integer(
            self.max_batch_tokens,
            name="max_batch_tokens",
            minimum=1,
            maximum=_MAX_BATCH_TOKENS,
        )
        if maximum_tokens < maximum_length:
            raise ValueError(
                "max_batch_tokens must accommodate at least one maximum-length sample"
            )
        maximum_attention = _integer(
            self.max_attention_elements,
            name="max_attention_elements",
            minimum=1,
            maximum=_MAX_ATTENTION_ELEMENTS,
        )
        if (
            self.backbone == "transformer"
            and heads * maximum_length * maximum_length > maximum_attention
        ):
            raise ValueError(
                "max_attention_elements must accommodate one maximum-length "
                "Transformer sample"
            )
        budget = _integer(
            self.parameter_budget,
            name="parameter_budget",
            minimum=1,
            maximum=_MAX_PARAMETER_BUDGET,
        )

        if isinstance(self.dropout, bool) or not isinstance(self.dropout, Real):
            raise TypeError("dropout must be a real number")
        dropout = float(self.dropout)
        if not math.isfinite(dropout) or dropout < 0.0 or dropout >= 1.0:
            raise ValueError("dropout must be finite and lie in [0, 1)")

        embedding_elements = (
            sum(validated_cardinalities) * width + maximum_length * width
        )
        if embedding_elements > _MAX_EMBEDDING_ELEMENTS:
            raise ValueError(
                "categorical plus positional embeddings exceed the {}-element guard"
                .format(_MAX_EMBEDDING_ELEMENTS)
            )

        object.__setattr__(self, "categorical_cardinalities", validated_cardinalities)
        object.__setattr__(
            self, "categorical_output_cardinalities", output_cardinalities
        )
        object.__setattr__(self, "num_continuous_features", continuous)
        object.__setattr__(self, "d_model", width)
        object.__setattr__(self, "num_layers", layers)
        object.__setattr__(self, "num_attention_heads", heads)
        object.__setattr__(self, "feedforward_width", feedforward)
        object.__setattr__(self, "cfc_backbone_layers", cfc_layers)
        object.__setattr__(self, "dropout", dropout)
        object.__setattr__(self, "max_sequence_length", maximum_length)
        object.__setattr__(self, "max_batch_tokens", maximum_tokens)
        object.__setattr__(self, "max_attention_elements", maximum_attention)
        object.__setattr__(self, "parameter_budget", budget)

        estimate = self.estimated_parameter_count
        if estimate > budget:
            raise ValueError(
                "model requires {} parameters, exceeding parameter_budget={}"
                .format(estimate, budget)
            )

    @property
    def num_categorical_fields(self) -> int:
        """Number of independent categorical sites at each grid position."""

        return len(self.categorical_cardinalities)

    @property
    def estimated_parameter_count(self) -> int:
        """Exact scalar-parameter count for the implemented PyTorch module.

        Computing this without importing PyTorch lets the resource budget fail
        before any embedding, recurrent, or attention tensor is allocated.
        """

        width = self.d_model
        continuous = self.num_continuous_features
        fields = self.num_categorical_fields
        feedforward = self.feedforward_width

        # Shared noisy-state encoder and prediction heads.
        total = sum(self.categorical_cardinalities) * width
        total += (2 * continuous + 1) * width
        total += (fields + 1) * width
        if self.backbone != "cfc":
            total += 2 * width  # ordinary elapsed-time value feature
        total += 2 * width  # elapsed-time observation-mask feature
        total += 2 * width  # diffusion-progress feature
        total += self.max_sequence_length * width
        total += 2 * width  # input LayerNorm

        if self.backbone == "transformer":
            # Multi-head attention, two feed-forward linears, and two norms.
            per_layer = (
                4 * width * width
                + 2 * width * feedforward
                + feedforward
                + 9 * width
            )
            total += self.num_layers * per_layer
            total += 2 * width  # final TransformerEncoder LayerNorm
        elif self.backbone == "grid_ffn":
            # Positionwise residual FFN: two linears and one LayerNorm.
            per_layer = 2 * width * feedforward + feedforward + 3 * width
            total += self.num_layers * per_layer
        elif self.backbone == "gru":
            # PyTorch GRU has input/hidden weights and two biases per gate.
            total += self.num_layers * (6 * width * width + 6 * width)
        else:
            # Canonical full CfC: backbone plus ff1/ff2/time_a/time_b heads.
            total += 2 * width * feedforward + feedforward
            total += (self.cfc_backbone_layers - 1) * (
                feedforward * feedforward + feedforward
            )
            total += 4 * (feedforward * width + width)

        total += sum(
            cardinality * (width + 1)
            for cardinality in self.categorical_output_cardinalities
        )
        total += continuous * (width + 1)
        return total


__all__ = ["FixedGridReferenceConfig"]
