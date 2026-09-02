"""Bounded count-and-presence-aware atomic-grid Torch reference.

This module implements only the one-step wiring control preregistered in
``research/32_cross_domain_atomic_counting_reference_gate.md``.  It is not a
native configuration-process model, likelihood, ELBO, or cross-domain model.

The three public data boundaries are deliberately separate:

* :class:`AtomicCountingReferenceTarget` contains clean source state and is
  accepted only by the corruption function;
* :class:`AtomicCountingModelInput` contains the complete and only model-visible
  state; and
* :class:`AtomicCountingLossTarget` contains supervision and is accepted only
  by the loss.

All three store tensors as immutable CPU byte payloads.  Accessors return fresh
tensors, so caller mutation cannot alter a validated boundary after creation.
No event IDs, sample/group IDs, paths, split labels, or aligned source rows are
stored by these boundaries or admitted through a model/loss call signature.
"""

from __future__ import annotations

from dataclasses import dataclass, fields
import hashlib
import math
from numbers import Integral
from typing import Dict, Optional, Tuple

import numpy as np

try:
    import torch
    from torch import nn
    from torch.nn import functional as F
except ModuleNotFoundError as error:  # pragma: no cover - exercised without extra
    if error.name == "torch":
        raise ModuleNotFoundError(
            "heterodiff.cross_domain_gate.atomic_counting_reference_torch "
            "requires the pinned Torch extra"
        ) from error
    raise


_COUNT_MASK_STATE = 3
_PRESENCE_MASK_STATE = 2
_COUNT_CLEAN_CARDINALITY = 3
_PRESENCE_CLEAN_CARDINALITY = 2
_COUNT_NOISY_CARDINALITY = 4
_PRESENCE_NOISY_CARDINALITY = 3
_TYPE_EMBEDDING_WIDTH = 8
_FIRST_HIDDEN_WIDTH = 64
_SECOND_HIDDEN_WIDTH = 32
_MAX_REFERENCE_POSITIONS = 2_881
_MAX_EVENT_TYPES = 88
_MAX_SLOT_CAPACITY = 2
_MAX_PRESENCE_COORDINATES = 2
_MAX_CONTINUOUS_COORDINATES = 2
_MAX_BATCH_SIZE = 1
_MAX_TENSOR_ELEMENTS = 20_000_000
_HARD_PARAMETER_BUDGET = 250_000


def _plain_int(
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


def _shape_size(shape: Tuple[int, ...]) -> int:
    result = 1
    for dimension in shape:
        result *= dimension
    return result


_DTYPES = {
    "bool": (torch.bool, np.dtype(np.bool_)),
    "int64": (torch.int64, np.dtype(np.int64)),
    "float32": (torch.float32, np.dtype(np.float32)),
}
_TORCH_DTYPE_NAMES = {value[0]: key for key, value in _DTYPES.items()}


@dataclass(frozen=True)
class _FrozenTensor:
    """Exact immutable C-order bytes for one bounded dense CPU tensor."""

    dtype_name: str
    shape: Tuple[int, ...]
    data: bytes

    def __post_init__(self) -> None:
        if self.dtype_name not in _DTYPES:
            raise ValueError("unsupported frozen tensor dtype")
        if not isinstance(self.shape, tuple) or not self.shape:
            raise TypeError("frozen tensor shape must be a nonempty tuple")
        shape = tuple(
            _plain_int(
                item,
                name="frozen tensor dimension",
                minimum=1,
                maximum=_MAX_TENSOR_ELEMENTS,
            )
            for item in self.shape
        )
        if _shape_size(shape) > _MAX_TENSOR_ELEMENTS:
            raise ValueError("frozen tensor exceeds the element guard")
        if not isinstance(self.data, bytes):
            raise TypeError("frozen tensor payload must be bytes")
        expected = _shape_size(shape) * _DTYPES[self.dtype_name][1].itemsize
        if len(self.data) != expected:
            raise ValueError("frozen tensor byte length disagrees with its shape")
        if self.dtype_name == "float32" and not bool(
            np.all(np.isfinite(np.frombuffer(self.data, dtype=np.float32)))
        ):
            raise ValueError("frozen float tensor payload must be finite")
        object.__setattr__(self, "shape", shape)

    @classmethod
    def freeze(
        cls,
        value: object,
        *,
        name: str,
        dtype: torch.dtype,
        shape: Tuple[int, ...],
    ) -> "_FrozenTensor":
        if type(value) is not torch.Tensor:
            raise TypeError("{} must be an exact torch.Tensor".format(name))
        tensor = value
        if tensor.device.type != "cpu" or tensor.layout != torch.strided:
            raise ValueError("{} must be a dense CPU tensor".format(name))
        if tensor.dtype != dtype:
            raise TypeError(
                "{} must have dtype {}; got {}".format(name, dtype, tensor.dtype)
            )
        if tuple(tensor.shape) != shape:
            raise ValueError(
                "{} has shape {}; expected {}".format(
                    name, tuple(tensor.shape), shape
                )
            )
        if tensor.requires_grad:
            raise ValueError("{} must not require gradients".format(name))
        if tensor.is_floating_point() and bool(
            torch.any(~torch.isfinite(tensor)).item()
        ):
            raise ValueError("{} must contain only finite values".format(name))
        contiguous = tensor.detach().clone().contiguous()
        return cls(
            dtype_name=_TORCH_DTYPE_NAMES[dtype],
            shape=shape,
            data=contiguous.numpy().tobytes(order="C"),
        )

    def thaw(self) -> torch.Tensor:
        torch_dtype, numpy_dtype = _DTYPES[self.dtype_name]
        array = np.frombuffer(self.data, dtype=numpy_dtype).copy().reshape(self.shape)
        result = torch.from_numpy(array)
        if result.dtype != torch_dtype:  # pragma: no cover - defensive version guard
            result = result.to(dtype=torch_dtype)
        return result.contiguous()

    def validate(self) -> None:
        """Re-run constructor validation after pickle or unsafe mutation."""

        _FrozenTensor(self.dtype_name, self.shape, self.data)


@dataclass(frozen=True)
class AtomicCountingReferenceConfig:
    """Exact bounded shape and architecture contract for one domain model."""

    reference_positions: int
    number_of_event_types: int
    number_of_presence_coordinates: int
    number_of_continuous_coordinates: int
    continuous_presence_indices: Tuple[int, ...]
    slot_capacity: int = 2
    parameter_budget: int = _HARD_PARAMETER_BUDGET

    def __post_init__(self) -> None:
        object.__setattr__(
            self,
            "reference_positions",
            _plain_int(
                self.reference_positions,
                name="reference_positions",
                minimum=2,
                maximum=_MAX_REFERENCE_POSITIONS,
            ),
        )
        object.__setattr__(
            self,
            "number_of_event_types",
            _plain_int(
                self.number_of_event_types,
                name="number_of_event_types",
                minimum=1,
                maximum=_MAX_EVENT_TYPES,
            ),
        )
        object.__setattr__(
            self,
            "number_of_presence_coordinates",
            _plain_int(
                self.number_of_presence_coordinates,
                name="number_of_presence_coordinates",
                minimum=1,
                maximum=_MAX_PRESENCE_COORDINATES,
            ),
        )
        object.__setattr__(
            self,
            "number_of_continuous_coordinates",
            _plain_int(
                self.number_of_continuous_coordinates,
                name="number_of_continuous_coordinates",
                minimum=1,
                maximum=_MAX_CONTINUOUS_COORDINATES,
            ),
        )
        object.__setattr__(
            self,
            "slot_capacity",
            _plain_int(
                self.slot_capacity,
                name="slot_capacity",
                minimum=_MAX_SLOT_CAPACITY,
                maximum=_MAX_SLOT_CAPACITY,
            ),
        )
        try:
            indices = tuple(self.continuous_presence_indices)
        except TypeError as error:
            raise TypeError(
                "continuous_presence_indices must be a tuple of integers"
            ) from error
        if len(indices) != self.number_of_continuous_coordinates:
            raise ValueError(
                "continuous_presence_indices must have one entry per continuous "
                "coordinate"
            )
        validated = tuple(
            _plain_int(
                value,
                name="continuous_presence_indices[{}]".format(index),
                minimum=0,
                maximum=self.number_of_presence_coordinates - 1,
            )
            for index, value in enumerate(indices)
        )
        object.__setattr__(self, "continuous_presence_indices", validated)
        object.__setattr__(
            self,
            "parameter_budget",
            _plain_int(
                self.parameter_budget,
                name="parameter_budget",
                minimum=1,
                maximum=_HARD_PARAMETER_BUDGET,
            ),
        )
        if self.estimated_parameter_count > self.parameter_budget:
            raise ValueError(
                "model requires {} parameters, exceeding parameter_budget={}".format(
                    self.estimated_parameter_count, self.parameter_budget
                )
            )

    @property
    def input_width(self) -> int:
        slots = self.slot_capacity
        presence = self.number_of_presence_coordinates
        continuous = self.number_of_continuous_coordinates
        # count one-hot; presence one-hots; numeric marks; applicability;
        # valid-time bit; noisy-count-derived slot activity; reference position;
        # fixed step; type embedding; anchor-count one-hot and observed bit.
        return (
            4
            + 3 * slots * presence
            + slots * continuous
            + slots * presence
            + 1
            + slots
            + 1
            + 1
            + _TYPE_EMBEDDING_WIDTH
            + 3
            + 1
        )

    @property
    def estimated_parameter_count(self) -> int:
        presence_heads = self.slot_capacity * self.number_of_presence_coordinates
        epsilon_heads = self.slot_capacity * self.number_of_continuous_coordinates
        return (
            self.number_of_event_types * _TYPE_EMBEDDING_WIDTH
            + self.input_width * _FIRST_HIDDEN_WIDTH
            + _FIRST_HIDDEN_WIDTH
            + _FIRST_HIDDEN_WIDTH * _SECOND_HIDDEN_WIDTH
            + _SECOND_HIDDEN_WIDTH
            + _SECOND_HIDDEN_WIDTH * _COUNT_CLEAN_CARDINALITY
            + _COUNT_CLEAN_CARDINALITY
            + presence_heads
            * (_SECOND_HIDDEN_WIDTH * _PRESENCE_CLEAN_CARDINALITY + 2)
            + epsilon_heads * (_SECOND_HIDDEN_WIDTH + 1)
        )

    @property
    def shape_signature(self) -> Tuple[object, ...]:
        return (
            self.reference_positions,
            self.number_of_event_types,
            self.slot_capacity,
            self.number_of_presence_coordinates,
            self.number_of_continuous_coordinates,
            self.continuous_presence_indices,
        )


def _require_valid_config(value: object) -> AtomicCountingReferenceConfig:
    """Revalidate an exact config after any persistence boundary."""

    if type(value) is not AtomicCountingReferenceConfig:
        raise TypeError("config must be an exact AtomicCountingReferenceConfig")
    integer_names = (
        "reference_positions",
        "number_of_event_types",
        "number_of_presence_coordinates",
        "number_of_continuous_coordinates",
        "slot_capacity",
        "parameter_budget",
    )
    if any(type(getattr(value, name)) is not int for name in integer_names):
        raise TypeError("config integer fields must remain canonical integers")
    if type(value.continuous_presence_indices) is not tuple or any(
        type(item) is not int for item in value.continuous_presence_indices
    ):
        raise TypeError(
            "continuous_presence_indices must remain a canonical integer tuple"
        )
    rebuilt = AtomicCountingReferenceConfig(
        reference_positions=value.reference_positions,
        number_of_event_types=value.number_of_event_types,
        number_of_presence_coordinates=value.number_of_presence_coordinates,
        number_of_continuous_coordinates=value.number_of_continuous_coordinates,
        continuous_presence_indices=value.continuous_presence_indices,
        slot_capacity=value.slot_capacity,
        parameter_budget=value.parameter_budget,
    )
    if rebuilt != value:
        raise ValueError("config is not in canonical validated state")
    return value


def _require_digest(value: object, *, name: str) -> str:
    if (
        type(value) is not str
        or len(value) != 64
        or value.lower() != value
        or any(character not in "0123456789abcdef" for character in value)
    ):
        raise ValueError("{} must be a lowercase SHA-256 digest".format(name))
    return value


def _frozen_boundary_digest(
    domain: str,
    config: AtomicCountingReferenceConfig,
    values: Tuple[Tuple[str, _FrozenTensor], ...],
) -> str:
    _require_valid_config(config)
    digest = hashlib.sha256()
    digest.update(domain.encode("ascii"))
    digest.update(b"\x00")
    config_values = (
        config.reference_positions,
        config.number_of_event_types,
        config.number_of_presence_coordinates,
        config.number_of_continuous_coordinates,
        config.slot_capacity,
        config.parameter_budget,
        len(config.continuous_presence_indices),
        *config.continuous_presence_indices,
    )
    for value in config_values:
        digest.update(int(value).to_bytes(8, byteorder="big", signed=False))
    for name, value in values:
        if type(value) is not _FrozenTensor:
            raise TypeError("digest payloads must be exact frozen tensors")
        value.validate()
        name_bytes = name.encode("ascii")
        dtype_bytes = value.dtype_name.encode("ascii")
        digest.update(len(name_bytes).to_bytes(2, "big"))
        digest.update(name_bytes)
        digest.update(len(dtype_bytes).to_bytes(1, "big"))
        digest.update(dtype_bytes)
        digest.update(len(value.shape).to_bytes(1, "big"))
        for dimension in value.shape:
            digest.update(int(dimension).to_bytes(8, "big"))
        digest.update(len(value.data).to_bytes(8, "big"))
        digest.update(value.data)
    return digest.hexdigest()


def _loss_target_integrity_digest(
    config: AtomicCountingReferenceConfig,
    model_input_digest: str,
    values: Tuple[Tuple[str, _FrozenTensor], ...],
) -> str:
    input_digest = _require_digest(
        model_input_digest, name="model_input_digest"
    )
    payload_digest = _frozen_boundary_digest(
        "heterodiff.atomic-counting.loss-target-payload.v1",
        config,
        values,
    )
    digest = hashlib.sha256()
    digest.update(b"heterodiff.atomic-counting.loss-target-binding.v1\x00")
    digest.update(bytes.fromhex(input_digest))
    digest.update(bytes.fromhex(payload_digest))
    return digest.hexdigest()


def _target_shapes(
    config: AtomicCountingReferenceConfig, batch_size: int
) -> Dict[str, Tuple[int, ...]]:
    batch = _plain_int(
        batch_size,
        name="batch_size",
        minimum=1,
        maximum=_MAX_BATCH_SIZE,
    )
    b_r_k = (
        batch,
        config.reference_positions,
        config.number_of_event_types,
    )
    b_r_k_s = b_r_k + (config.slot_capacity,)
    return {
        "count": b_r_k,
        "presence": b_r_k_s + (config.number_of_presence_coordinates,),
        "continuous": b_r_k_s + (config.number_of_continuous_coordinates,),
        "valid": (batch, config.reference_positions),
    }


def _require_prefix_valid_time(value: torch.Tensor, *, name: str) -> None:
    if bool(torch.any(~torch.any(value, dim=1)).item()):
        raise ValueError("{} requires at least one real position per row".format(name))
    if value.shape[1] > 1 and bool(
        torch.any((~value[:, :-1]) & value[:, 1:]).item()
    ):
        raise ValueError("{} must be a left-aligned prefix mask".format(name))


def _validate_structural_applicability(
    structural: torch.Tensor,
    valid_time: torch.Tensor,
    *,
    name: str,
) -> None:
    # Applicability is schema state.  It cannot vary with clean occupancy or
    # occurrence slot, and every batch row using one config has one template.
    templates = []
    for batch_index in range(structural.shape[0]):
        length = int(valid_time[batch_index].sum().item())
        template = structural[batch_index, 0]
        if not torch.equal(
            structural[batch_index, :length],
            template.unsqueeze(0).expand_as(structural[batch_index, :length]),
        ):
            raise ValueError(
                "{} varies across real positions and could reveal target state".format(
                    name
                )
            )
        if not torch.equal(
            template,
            template[:, :1, :].expand_as(template),
        ):
            raise ValueError(
                "{} varies across serialization slots and could reveal occupancy".format(
                    name
                )
            )
        if bool(torch.any(structural[batch_index, length:]).item()):
            raise ValueError("{} must be false on padding".format(name))
        templates.append(template)
    for template in templates[1:]:
        if not torch.equal(template, templates[0]):
            raise ValueError("{} differs across batch rows".format(name))


def _presence_to_continuous(
    value: torch.Tensor, config: AtomicCountingReferenceConfig
) -> torch.Tensor:
    indices = torch.tensor(
        config.continuous_presence_indices,
        dtype=torch.int64,
        device=value.device,
    )
    return value.index_select(-1, indices)


def _validate_anchor_arrays(
    anchor_count: torch.Tensor,
    anchor_observed: torch.Tensor,
    valid_time: torch.Tensor,
    *,
    clean_count: Optional[torch.Tensor] = None,
) -> None:
    if bool(torch.any((anchor_count < 0) | (anchor_count > 2)).item()):
        raise ValueError("anchor_count must lie in clean support 0, 1, 2")
    if bool(torch.any(anchor_count[~anchor_observed] != 0).item()):
        raise ValueError("unobserved anchor counts must be canonical zero")
    if bool(torch.any(anchor_count[anchor_observed] != 1).item()):
        raise ValueError("the frozen anchored task requires a unique count-one cell")
    valid_cells = valid_time.unsqueeze(-1).expand_as(anchor_observed)
    if bool(torch.any(anchor_observed & ~valid_cells).item()):
        raise ValueError("an anchor cannot expose padding")
    if bool(torch.any(anchor_observed.sum(dim=(1, 2)) > 1).item()):
        raise ValueError("the frozen task permits at most one anchored cell")
    if clean_count is not None and bool(
        torch.any(clean_count[anchor_observed] != 1).item()
    ):
        raise ValueError("the anchored cell must have clean count exactly one")


@dataclass(frozen=True)
class AtomicCountingReferenceTarget:
    """Immutable clean layout accepted only by the corruption kernel."""

    config: AtomicCountingReferenceConfig
    _clean_count: _FrozenTensor
    _clean_presence: _FrozenTensor
    _transformed_mark: _FrozenTensor
    _structural_applicable: _FrozenTensor
    _source_observed: _FrozenTensor
    _valid_time: _FrozenTensor
    _anchor_count: _FrozenTensor
    _anchor_count_observed: _FrozenTensor

    def __post_init__(self) -> None:
        if type(self.config) is not AtomicCountingReferenceConfig:
            raise TypeError("config must be an exact AtomicCountingReferenceConfig")
        if any(
            type(getattr(self, item.name)) is not _FrozenTensor
            for item in fields(self)
            if item.name != "config"
        ):
            raise TypeError("target tensor payloads must be exact frozen tensors")
        self._validate()

    @classmethod
    def from_tensors(
        cls,
        config: AtomicCountingReferenceConfig,
        *,
        clean_count: torch.Tensor,
        clean_presence: torch.Tensor,
        transformed_mark: torch.Tensor,
        structural_applicable: torch.Tensor,
        source_observed: torch.Tensor,
        valid_time: torch.Tensor,
        anchor_count: torch.Tensor,
        anchor_count_observed: torch.Tensor,
    ) -> "AtomicCountingReferenceTarget":
        if type(config) is not AtomicCountingReferenceConfig:
            raise TypeError("config must be an exact AtomicCountingReferenceConfig")
        if type(clean_count) is not torch.Tensor or clean_count.ndim != 3:
            raise TypeError("clean_count must be a rank-three exact torch.Tensor")
        batch = int(clean_count.shape[0])
        shapes = _target_shapes(config, batch)
        return cls(
            config=config,
            _clean_count=_FrozenTensor.freeze(
                clean_count, name="clean_count", dtype=torch.int64, shape=shapes["count"]
            ),
            _clean_presence=_FrozenTensor.freeze(
                clean_presence,
                name="clean_presence",
                dtype=torch.bool,
                shape=shapes["presence"],
            ),
            _transformed_mark=_FrozenTensor.freeze(
                transformed_mark,
                name="transformed_mark",
                dtype=torch.float32,
                shape=shapes["continuous"],
            ),
            _structural_applicable=_FrozenTensor.freeze(
                structural_applicable,
                name="structural_applicable",
                dtype=torch.bool,
                shape=shapes["presence"],
            ),
            _source_observed=_FrozenTensor.freeze(
                source_observed,
                name="source_observed",
                dtype=torch.bool,
                shape=shapes["presence"],
            ),
            _valid_time=_FrozenTensor.freeze(
                valid_time,
                name="valid_time",
                dtype=torch.bool,
                shape=shapes["valid"],
            ),
            _anchor_count=_FrozenTensor.freeze(
                anchor_count,
                name="anchor_count",
                dtype=torch.int64,
                shape=shapes["count"],
            ),
            _anchor_count_observed=_FrozenTensor.freeze(
                anchor_count_observed,
                name="anchor_count_observed",
                dtype=torch.bool,
                shape=shapes["count"],
            ),
        )

    @classmethod
    def from_encoded_reference(
        cls,
        encoded: object,
        *,
        anchor_count: Optional[torch.Tensor] = None,
        anchor_count_observed: Optional[torch.Tensor] = None,
        parameter_budget: int = _HARD_PARAMETER_BUDGET,
    ) -> "AtomicCountingReferenceTarget":
        """Build one ID-free target from the lossless NumPy layout boundary.

        Provenance sidecars are intentionally not copied.  Model-visible
        structural applicability is rebuilt from the frozen schema, rather
        than copied from occurrence-aligned arrays whose activity would reveal
        clean cardinality.
        """

        from heterodiff.data.atomic_counting_reference import (
            EncodedCountingReference,
        )
        from heterodiff.events.schema import SupportKind

        if type(encoded) is not EncodedCountingReference:
            raise TypeError(
                "encoded must be an exact EncodedCountingReference instance"
            )
        # Re-run the complete public representation validation and round trip
        # before consuming its arrays.
        encoded.to_atomic_counting_grid_tensor()
        layout = encoded.layout
        for event_type in layout.schema.event_types:
            for field in event_type.fields:
                if field.support not in (SupportKind.REAL, SupportKind.POSITIVE):
                    raise ValueError(
                        "the frozen gate admits only REAL and POSITIVE fields"
                    )
        field_coordinates = layout.field_coordinates
        transformed_coordinates = layout.transformed_coordinates
        field_index = {
            coordinate: index for index, coordinate in enumerate(field_coordinates)
        }
        try:
            continuous_presence_indices = tuple(
                field_index[coordinate] for coordinate in transformed_coordinates
            )
        except KeyError as error:
            raise ValueError(
                "the bounded gate supports only coordinate-aligned transforms"
            ) from error

        config = AtomicCountingReferenceConfig(
            reference_positions=layout.reference_length,
            number_of_event_types=layout.number_of_types,
            number_of_presence_coordinates=len(field_coordinates),
            number_of_continuous_coordinates=len(transformed_coordinates),
            continuous_presence_indices=continuous_presence_indices,
            slot_capacity=layout.slot_capacity,
            parameter_budget=parameter_budget,
        )

        mapped_clean_presence = encoded.clean_presence[
            ..., continuous_presence_indices
        ]
        mapped_structural = encoded.structural_applicability[
            ..., continuous_presence_indices
        ]
        mapped_source_observed = encoded.source_observed[
            ..., continuous_presence_indices
        ]
        if not np.array_equal(
            mapped_clean_presence, encoded.transformed_clean_presence
        ):
            raise ValueError(
                "native and transformed physical-presence axes disagree"
            )
        if not np.array_equal(
            mapped_structural, encoded.transformed_structural_applicability
        ):
            raise ValueError(
                "native and transformed applicability axes disagree"
            )
        if not np.array_equal(
            mapped_source_observed, encoded.transformed_source_observed
        ):
            raise ValueError(
                "native and transformed source-observation axes disagree"
            )

        r = layout.reference_length
        k = layout.number_of_types
        s = layout.slot_capacity
        f = len(field_coordinates)
        schema_template = np.zeros((k, s, f), dtype=np.bool_)
        for type_index, event_type in enumerate(layout.schema.event_types):
            for field in event_type.fields:
                for coordinate in range(field.dimension):
                    schema_template[
                        type_index, :, field_index[(field.name, coordinate)]
                    ] = True
        structural = np.zeros((r, k, s, f), dtype=np.bool_)
        structural[encoded.valid_time_mask] = schema_template

        if (anchor_count is None) != (anchor_count_observed is None):
            raise ValueError(
                "anchor_count and anchor_count_observed must be supplied together"
            )
        if anchor_count is None:
            anchor_count_value = torch.zeros((r, k), dtype=torch.int64)
            anchor_observed_value = torch.zeros((r, k), dtype=torch.bool)
        else:
            if type(anchor_count) is not torch.Tensor or tuple(
                anchor_count.shape
            ) != (r, k):
                raise TypeError("anchor_count must be an exact rank-two grid tensor")
            if type(anchor_count_observed) is not torch.Tensor or tuple(
                anchor_count_observed.shape
            ) != (r, k):
                raise TypeError(
                    "anchor_count_observed must be an exact rank-two grid tensor"
                )
            anchor_count_value = anchor_count
            anchor_observed_value = anchor_count_observed

        def tensor_from_array(value: np.ndarray) -> torch.Tensor:
            return torch.from_numpy(np.array(value, copy=True, order="C"))

        return cls.from_tensors(
            config,
            clean_count=tensor_from_array(encoded.exact_counts).unsqueeze(0),
            clean_presence=tensor_from_array(encoded.clean_presence).unsqueeze(0),
            transformed_mark=tensor_from_array(
                encoded.transformed_mark_values
            ).to(dtype=torch.float32).unsqueeze(0),
            structural_applicable=tensor_from_array(structural).unsqueeze(0),
            source_observed=tensor_from_array(encoded.source_observed).unsqueeze(0),
            valid_time=tensor_from_array(encoded.valid_time_mask).unsqueeze(0),
            anchor_count=anchor_count_value.unsqueeze(0),
            anchor_count_observed=anchor_observed_value.unsqueeze(0),
        )

    @property
    def batch_size(self) -> int:
        return self._clean_count.shape[0]

    @property
    def clean_count(self) -> torch.Tensor:
        return self._clean_count.thaw()

    @property
    def clean_presence(self) -> torch.Tensor:
        return self._clean_presence.thaw()

    @property
    def transformed_mark(self) -> torch.Tensor:
        return self._transformed_mark.thaw()

    @property
    def structural_applicable(self) -> torch.Tensor:
        return self._structural_applicable.thaw()

    @property
    def source_observed(self) -> torch.Tensor:
        return self._source_observed.thaw()

    @property
    def valid_time(self) -> torch.Tensor:
        return self._valid_time.thaw()

    @property
    def anchor_count(self) -> torch.Tensor:
        return self._anchor_count.thaw()

    @property
    def anchor_count_observed(self) -> torch.Tensor:
        return self._anchor_count_observed.thaw()

    def _validate(self) -> None:
        _require_valid_config(self.config)
        shapes = _target_shapes(self.config, self.batch_size)
        expected = {
            "_clean_count": ("int64", shapes["count"]),
            "_clean_presence": ("bool", shapes["presence"]),
            "_transformed_mark": ("float32", shapes["continuous"]),
            "_structural_applicable": ("bool", shapes["presence"]),
            "_source_observed": ("bool", shapes["presence"]),
            "_valid_time": ("bool", shapes["valid"]),
            "_anchor_count": ("int64", shapes["count"]),
            "_anchor_count_observed": ("bool", shapes["count"]),
        }
        for name, (dtype_name, shape) in expected.items():
            value = getattr(self, name)
            value.validate()
            if value.dtype_name != dtype_name or value.shape != shape:
                raise ValueError("{} disagrees with the target config".format(name))

        count = self.clean_count
        presence = self.clean_presence
        mark = self.transformed_mark
        structural = self.structural_applicable
        source_observed = self.source_observed
        valid = self.valid_time
        _require_prefix_valid_time(valid, name="valid_time")
        _validate_structural_applicability(
            structural, valid, name="structural_applicable"
        )
        valid_cells = valid.unsqueeze(-1).expand_as(count)
        if bool(torch.any((count < 0) | (count > self.config.slot_capacity)).item()):
            raise ValueError("clean_count exceeds the frozen count support")
        if bool(torch.any(count[~valid_cells] != 0).item()):
            raise ValueError("clean_count padding must be canonical zero")
        slots = torch.arange(self.config.slot_capacity).reshape(1, 1, 1, -1)
        active = slots < count.unsqueeze(-1)
        allowed_presence = (
            valid[:, :, None, None, None] & structural & active.unsqueeze(-1)
        )
        if bool(torch.any(presence & ~allowed_presence).item()):
            raise ValueError(
                "clean_presence includes padding, an inactive slot, or an "
                "inapplicable coordinate"
            )
        if bool(torch.any(source_observed & ~presence).item()):
            raise ValueError("source_observed must be a subset of clean_presence")
        continuous_present = _presence_to_continuous(presence, self.config)
        if bool(torch.any(mark[~continuous_present] != 0.0).item()):
            raise ValueError("transformed marks must be zero where physically absent")
        _validate_anchor_arrays(
            self.anchor_count,
            self.anchor_count_observed,
            valid,
            clean_count=count,
        )


@dataclass(frozen=True)
class AtomicCountingModelInput:
    """Immutable complete model-visible input, with no aligned clean state."""

    config: AtomicCountingReferenceConfig
    _noisy_count: _FrozenTensor
    _noisy_presence: _FrozenTensor
    _noisy_mark: _FrozenTensor
    _structural_applicable: _FrozenTensor
    _valid_time: _FrozenTensor
    _slot_active: _FrozenTensor
    _anchor_count: _FrozenTensor
    _anchor_count_observed: _FrozenTensor

    def __post_init__(self) -> None:
        if type(self.config) is not AtomicCountingReferenceConfig:
            raise TypeError("config must be an exact AtomicCountingReferenceConfig")
        if any(
            type(getattr(self, item.name)) is not _FrozenTensor
            for item in fields(self)
            if item.name != "config"
        ):
            raise TypeError("model-input payloads must be exact frozen tensors")
        self._validate()

    @classmethod
    def from_tensors(
        cls,
        config: AtomicCountingReferenceConfig,
        *,
        noisy_count: torch.Tensor,
        noisy_presence: torch.Tensor,
        noisy_mark: torch.Tensor,
        structural_applicable: torch.Tensor,
        valid_time: torch.Tensor,
        slot_active: torch.Tensor,
        anchor_count: torch.Tensor,
        anchor_count_observed: torch.Tensor,
    ) -> "AtomicCountingModelInput":
        if type(config) is not AtomicCountingReferenceConfig:
            raise TypeError("config must be an exact AtomicCountingReferenceConfig")
        if type(noisy_count) is not torch.Tensor or noisy_count.ndim != 3:
            raise TypeError("noisy_count must be a rank-three exact torch.Tensor")
        batch = int(noisy_count.shape[0])
        shapes = _target_shapes(config, batch)
        slot_shape = shapes["count"] + (config.slot_capacity,)
        return cls(
            config=config,
            _noisy_count=_FrozenTensor.freeze(
                noisy_count,
                name="noisy_count",
                dtype=torch.int64,
                shape=shapes["count"],
            ),
            _noisy_presence=_FrozenTensor.freeze(
                noisy_presence,
                name="noisy_presence",
                dtype=torch.int64,
                shape=shapes["presence"],
            ),
            _noisy_mark=_FrozenTensor.freeze(
                noisy_mark,
                name="noisy_mark",
                dtype=torch.float32,
                shape=shapes["continuous"],
            ),
            _structural_applicable=_FrozenTensor.freeze(
                structural_applicable,
                name="structural_applicable",
                dtype=torch.bool,
                shape=shapes["presence"],
            ),
            _valid_time=_FrozenTensor.freeze(
                valid_time,
                name="valid_time",
                dtype=torch.bool,
                shape=shapes["valid"],
            ),
            _slot_active=_FrozenTensor.freeze(
                slot_active,
                name="slot_active",
                dtype=torch.bool,
                shape=slot_shape,
            ),
            _anchor_count=_FrozenTensor.freeze(
                anchor_count,
                name="anchor_count",
                dtype=torch.int64,
                shape=shapes["count"],
            ),
            _anchor_count_observed=_FrozenTensor.freeze(
                anchor_count_observed,
                name="anchor_count_observed",
                dtype=torch.bool,
                shape=shapes["count"],
            ),
        )

    @property
    def batch_size(self) -> int:
        return self._noisy_count.shape[0]

    @property
    def noisy_count(self) -> torch.Tensor:
        return self._noisy_count.thaw()

    @property
    def noisy_presence(self) -> torch.Tensor:
        return self._noisy_presence.thaw()

    @property
    def noisy_mark(self) -> torch.Tensor:
        return self._noisy_mark.thaw()

    @property
    def structural_applicable(self) -> torch.Tensor:
        return self._structural_applicable.thaw()

    @property
    def valid_time(self) -> torch.Tensor:
        return self._valid_time.thaw()

    @property
    def slot_active(self) -> torch.Tensor:
        return self._slot_active.thaw()

    @property
    def anchor_count(self) -> torch.Tensor:
        return self._anchor_count.thaw()

    @property
    def anchor_count_observed(self) -> torch.Tensor:
        return self._anchor_count_observed.thaw()

    @property
    def model_input_digest(self) -> str:
        """Bind supervision and outputs to these exact model-visible bytes."""

        return _frozen_boundary_digest(
            "heterodiff.atomic-counting.model-input.v1",
            self.config,
            tuple(
                (item.name, getattr(self, item.name))
                for item in fields(self)
                if item.name != "config"
            ),
        )

    def _validate(self) -> None:
        _require_valid_config(self.config)
        shapes = _target_shapes(self.config, self.batch_size)
        slot_shape = shapes["count"] + (self.config.slot_capacity,)
        expected = {
            "_noisy_count": ("int64", shapes["count"]),
            "_noisy_presence": ("int64", shapes["presence"]),
            "_noisy_mark": ("float32", shapes["continuous"]),
            "_structural_applicable": ("bool", shapes["presence"]),
            "_valid_time": ("bool", shapes["valid"]),
            "_slot_active": ("bool", slot_shape),
            "_anchor_count": ("int64", shapes["count"]),
            "_anchor_count_observed": ("bool", shapes["count"]),
        }
        for name, (dtype_name, shape) in expected.items():
            value = getattr(self, name)
            value.validate()
            if value.dtype_name != dtype_name or value.shape != shape:
                raise ValueError("{} disagrees with the model-input config".format(name))

        count = self.noisy_count
        presence = self.noisy_presence
        mark = self.noisy_mark
        structural = self.structural_applicable
        valid = self.valid_time
        slot_active = self.slot_active
        _require_prefix_valid_time(valid, name="model valid_time")
        _validate_structural_applicability(
            structural, valid, name="model structural_applicable"
        )
        valid_cells = valid.unsqueeze(-1).expand_as(count)
        if bool(torch.any((count < 0) | (count > _COUNT_MASK_STATE)).item()):
            raise ValueError("noisy_count contains an unsupported state")
        if bool(torch.any(count[~valid_cells] != 0).item()):
            raise ValueError("noisy_count padding must be canonical zero")
        if bool(
            torch.any(
                (presence < 0) | (presence > _PRESENCE_MASK_STATE)
            ).item()
        ):
            raise ValueError("noisy_presence contains an unsupported state")
        valid_structural = valid[:, :, None, None, None] & structural
        if bool(torch.any(presence[~valid_structural] != 0).item()):
            raise ValueError(
                "noisy_presence must be zero on padding and inapplicable coordinates"
            )

        slots = torch.arange(self.config.slot_capacity).reshape(1, 1, 1, -1)
        numeric_count = count != _COUNT_MASK_STATE
        expected_active = (
            numeric_count.unsqueeze(-1) & (slots < count.unsqueeze(-1))
        )
        expected_active &= valid[:, :, None, None]
        if not torch.equal(slot_active, expected_active):
            raise ValueError(
                "slot_active must be derived only from the numeric noisy count"
            )
        masked_cells = (count == _COUNT_MASK_STATE).unsqueeze(-1).unsqueeze(-1)
        if bool(
            torch.any(
                presence[masked_cells.expand_as(presence) & valid_structural]
                != _PRESENCE_MASK_STATE
            ).item()
        ):
            raise ValueError(
                "a masked count requires masked presence at every applicable slot"
            )
        inactive_numeric = (
            numeric_count.unsqueeze(-1).unsqueeze(-1)
            & ~slot_active.unsqueeze(-1)
            & valid_structural
        )
        if bool(torch.any(presence[inactive_numeric] != 0).item()):
            raise ValueError("numeric-count inactive slots require presence zero")

        continuous_structural = _presence_to_continuous(structural, self.config)
        valid_continuous = valid[:, :, None, None, None] & continuous_structural
        if bool(torch.any(mark[~valid_continuous] != 0.0).item()):
            raise ValueError(
                "noisy marks must be zero on padding and inapplicable coordinates"
            )
        _validate_anchor_arrays(
            self.anchor_count,
            self.anchor_count_observed,
            valid,
        )


@dataclass(frozen=True)
class AtomicCountingLossTarget:
    """Immutable supervision accepted only by the hybrid loss."""

    config: AtomicCountingReferenceConfig
    model_input_digest: str
    integrity_digest: str
    _clean_count: _FrozenTensor
    _clean_presence: _FrozenTensor
    _clean_transformed_mark: _FrozenTensor
    _epsilon: _FrozenTensor
    _count_loss_mask: _FrozenTensor
    _presence_loss_mask: _FrozenTensor
    _continuous_loss_mask: _FrozenTensor

    def __post_init__(self) -> None:
        if type(self.config) is not AtomicCountingReferenceConfig:
            raise TypeError("config must be an exact AtomicCountingReferenceConfig")
        if any(
            type(getattr(self, item.name)) is not _FrozenTensor
            for item in fields(self)
            if item.name
            not in ("config", "model_input_digest", "integrity_digest")
        ):
            raise TypeError("loss-target payloads must be exact frozen tensors")
        self._validate()

    @classmethod
    def from_tensors(
        cls,
        config: AtomicCountingReferenceConfig,
        *,
        model_input_digest: str,
        clean_count: torch.Tensor,
        clean_presence: torch.Tensor,
        clean_transformed_mark: torch.Tensor,
        epsilon: torch.Tensor,
        count_loss_mask: torch.Tensor,
        presence_loss_mask: torch.Tensor,
        continuous_loss_mask: torch.Tensor,
    ) -> "AtomicCountingLossTarget":
        if type(config) is not AtomicCountingReferenceConfig:
            raise TypeError("config must be an exact AtomicCountingReferenceConfig")
        if type(clean_count) is not torch.Tensor or clean_count.ndim != 3:
            raise TypeError("clean_count must be a rank-three exact torch.Tensor")
        batch = int(clean_count.shape[0])
        shapes = _target_shapes(config, batch)
        frozen_values = (
            (
                "_clean_count",
                _FrozenTensor.freeze(
                    clean_count,
                    name="clean_count",
                    dtype=torch.int64,
                    shape=shapes["count"],
                ),
            ),
            (
                "_clean_presence",
                _FrozenTensor.freeze(
                    clean_presence,
                    name="clean_presence",
                    dtype=torch.bool,
                    shape=shapes["presence"],
                ),
            ),
            (
                "_clean_transformed_mark",
                _FrozenTensor.freeze(
                    clean_transformed_mark,
                    name="clean_transformed_mark",
                    dtype=torch.float32,
                    shape=shapes["continuous"],
                ),
            ),
            (
                "_epsilon",
                _FrozenTensor.freeze(
                    epsilon,
                    name="epsilon",
                    dtype=torch.float32,
                    shape=shapes["continuous"],
                ),
            ),
            (
                "_count_loss_mask",
                _FrozenTensor.freeze(
                    count_loss_mask,
                    name="count_loss_mask",
                    dtype=torch.bool,
                    shape=shapes["count"],
                ),
            ),
            (
                "_presence_loss_mask",
                _FrozenTensor.freeze(
                    presence_loss_mask,
                    name="presence_loss_mask",
                    dtype=torch.bool,
                    shape=shapes["presence"],
                ),
            ),
            (
                "_continuous_loss_mask",
                _FrozenTensor.freeze(
                    continuous_loss_mask,
                    name="continuous_loss_mask",
                    dtype=torch.bool,
                    shape=shapes["continuous"],
                ),
            ),
        )
        payloads = dict(frozen_values)
        return cls(
            config=config,
            model_input_digest=_require_digest(
                model_input_digest, name="model_input_digest"
            ),
            integrity_digest=_loss_target_integrity_digest(
                config, model_input_digest, frozen_values
            ),
            **payloads,
        )

    @property
    def batch_size(self) -> int:
        return self._clean_count.shape[0]

    @property
    def clean_count(self) -> torch.Tensor:
        return self._clean_count.thaw()

    @property
    def clean_presence(self) -> torch.Tensor:
        return self._clean_presence.thaw()

    @property
    def clean_transformed_mark(self) -> torch.Tensor:
        return self._clean_transformed_mark.thaw()

    @property
    def epsilon(self) -> torch.Tensor:
        return self._epsilon.thaw()

    @property
    def count_loss_mask(self) -> torch.Tensor:
        return self._count_loss_mask.thaw()

    @property
    def presence_loss_mask(self) -> torch.Tensor:
        return self._presence_loss_mask.thaw()

    @property
    def continuous_loss_mask(self) -> torch.Tensor:
        return self._continuous_loss_mask.thaw()

    def _validate(self) -> None:
        _require_valid_config(self.config)
        _require_digest(self.model_input_digest, name="model_input_digest")
        _require_digest(self.integrity_digest, name="integrity_digest")
        shapes = _target_shapes(self.config, self.batch_size)
        expected = {
            "_clean_count": ("int64", shapes["count"]),
            "_clean_presence": ("bool", shapes["presence"]),
            "_clean_transformed_mark": ("float32", shapes["continuous"]),
            "_epsilon": ("float32", shapes["continuous"]),
            "_count_loss_mask": ("bool", shapes["count"]),
            "_presence_loss_mask": ("bool", shapes["presence"]),
            "_continuous_loss_mask": ("bool", shapes["continuous"]),
        }
        for name, (dtype_name, shape) in expected.items():
            value = getattr(self, name)
            value.validate()
            if value.dtype_name != dtype_name or value.shape != shape:
                raise ValueError("{} disagrees with the loss-target config".format(name))
        expected_integrity = _loss_target_integrity_digest(
            self.config,
            self.model_input_digest,
            tuple((name, getattr(self, name)) for name in expected),
        )
        if self.integrity_digest != expected_integrity:
            raise ValueError(
                "loss target integrity digest disagrees with its payload"
            )
        count = self.clean_count
        presence = self.clean_presence
        clean_mark = self.clean_transformed_mark
        count_mask = self.count_loss_mask
        presence_mask = self.presence_loss_mask
        continuous_mask = self.continuous_loss_mask
        if bool(torch.any((count < 0) | (count > 2)).item()):
            raise ValueError("clean count target is outside support 0, 1, 2")
        if bool(
            torch.any(
                continuous_mask
                & ~_presence_to_continuous(presence, self.config)
            ).item()
        ):
            raise ValueError(
                "continuous supervision requires a physically present clean mark"
            )
        # The count mask defines valid cells and must include every type at a
        # real position, never an arbitrary target-dependent subset.
        valid = count_mask[:, :, :1]
        if not torch.equal(count_mask, valid.expand_as(count_mask)):
            raise ValueError("count_loss_mask must cover all types at each real time")
        valid_time = valid[:, :, 0]
        _require_prefix_valid_time(valid_time, name="loss valid_time")
        _validate_structural_applicability(
            presence_mask,
            valid_time,
            name="presence_loss_mask structural template",
        )
        if bool(torch.any(count[~count_mask] != 0).item()):
            raise ValueError("clean count padding must be canonical zero")
        valid_presence = valid_time[:, :, None, None, None]
        if bool(torch.any(presence & ~valid_presence).item()):
            raise ValueError("clean presence cannot include padding")
        if bool(torch.any(presence_mask & ~valid_presence).item()):
            raise ValueError("presence_loss_mask cannot include padding")
        valid_continuous = valid_time[:, :, None, None, None]
        if bool(torch.any(continuous_mask & ~valid_continuous).item()):
            raise ValueError("continuous_loss_mask cannot include padding")
        slots = torch.arange(self.config.slot_capacity).reshape(1, 1, 1, -1)
        active_slots = slots < count.unsqueeze(-1)
        if bool(torch.any(presence & ~active_slots.unsqueeze(-1)).item()):
            raise ValueError("clean presence requires an active clean-count slot")
        if bool(torch.any(presence & ~presence_mask).item()):
            raise ValueError(
                "clean presence cannot occupy an inapplicable loss coordinate"
            )
        continuous_applicable = _presence_to_continuous(
            presence_mask, self.config
        )
        if bool(torch.any(continuous_mask & ~continuous_applicable).item()):
            raise ValueError(
                "continuous supervision cannot enable an inapplicable coordinate"
            )
        epsilon = self.epsilon
        continuous_present = _presence_to_continuous(presence, self.config)
        if bool(torch.any(clean_mark[~continuous_present] != 0.0).item()):
            raise ValueError(
                "clean transformed marks must be zero where physically absent"
            )
        if bool(torch.any(epsilon[~valid_continuous.expand_as(epsilon)] != 0.0).item()):
            raise ValueError("epsilon padding must be canonical zero")
        if bool(torch.any(epsilon[~continuous_applicable] != 0.0).item()):
            raise ValueError("epsilon must be zero on inapplicable coordinates")


@dataclass(frozen=True)
class AtomicCountingCorruptionBatch:
    """Separated immutable model input and supervision for one corruption draw."""

    model_input: AtomicCountingModelInput
    loss_target: AtomicCountingLossTarget

    def __post_init__(self) -> None:
        if type(self.model_input) is not AtomicCountingModelInput:
            raise TypeError("model_input must be an exact AtomicCountingModelInput")
        if type(self.loss_target) is not AtomicCountingLossTarget:
            raise TypeError("loss_target must be an exact AtomicCountingLossTarget")
        if self.model_input.config != self.loss_target.config:
            raise ValueError("model input and loss target configs differ")
        if self.model_input.batch_size != self.loss_target.batch_size:
            raise ValueError("model input and loss target batch sizes differ")
        self.model_input._validate()
        self.loss_target._validate()
        expected_valid_time = self.loss_target.count_loss_mask[:, :, 0]
        if not torch.equal(self.model_input.valid_time, expected_valid_time):
            raise ValueError(
                "model input and loss target valid-time masks differ"
            )
        if not torch.equal(
            self.model_input.structural_applicable,
            self.loss_target.presence_loss_mask,
        ):
            raise ValueError(
                "model input and loss target applicability templates differ"
            )
        anchored = self.model_input.anchor_count_observed
        if bool(
            torch.any(self.loss_target.clean_count[anchored] != 1).item()
        ):
            raise ValueError(
                "model input anchors disagree with the clean count target"
            )
        noisy_count = self.model_input.noisy_count
        clean_count = self.loss_target.clean_count
        numeric_count = noisy_count != _COUNT_MASK_STATE
        if bool(torch.any(noisy_count[numeric_count] != clean_count[numeric_count]).item()):
            raise ValueError(
                "numeric noisy counts disagree with the clean count target"
            )
        noisy_presence = self.model_input.noisy_presence
        clean_presence = self.loss_target.clean_presence
        applicable = self.model_input.structural_applicable
        valid_presence = (
            self.model_input.valid_time[:, :, None, None, None] & applicable
        )
        exposed_presence = (
            valid_presence & (noisy_presence != _PRESENCE_MASK_STATE)
        )
        if bool(
            torch.any(
                noisy_presence[exposed_presence]
                != clean_presence.to(dtype=torch.int64)[exposed_presence]
            ).item()
        ):
            raise ValueError(
                "exposed noisy presence disagrees with the clean presence target"
            )
        continuous_applicable = _presence_to_continuous(
            applicable, self.model_input.config
        )
        continuous_valid = (
            self.model_input.valid_time[:, :, None, None, None]
            & continuous_applicable
        )
        continuous_presence = _presence_to_continuous(
            noisy_presence, self.model_input.config
        )
        exposed_continuous = (
            continuous_valid
            & numeric_count.unsqueeze(-1).unsqueeze(-1)
            & self.model_input.slot_active.unsqueeze(-1)
            & (continuous_presence == 1)
        )
        if bool(
            torch.any(
                self.loss_target.continuous_loss_mask & ~exposed_continuous
            ).item()
        ):
            raise ValueError(
                "continuous supervision is not an exposed-present corruption branch"
            )
        reference_noise_branch = continuous_valid & ~exposed_continuous
        if not torch.equal(
            self.model_input.noisy_mark[reference_noise_branch],
            self.loss_target.epsilon[reference_noise_branch],
        ):
            raise ValueError(
                "model reference noise and epsilon target disagree"
            )
        expected_exposed_mark = (
            math.sqrt(0.8) * self.loss_target.clean_transformed_mark
            + math.sqrt(0.2) * self.loss_target.epsilon
        )
        if not torch.equal(
            self.model_input.noisy_mark[exposed_continuous],
            expected_exposed_mark[exposed_continuous],
        ):
            raise ValueError(
                "exposed noisy marks and epsilon target disagree"
            )
        if self.loss_target.model_input_digest != self.model_input.model_input_digest:
            raise ValueError(
                "model input and loss target integrity bindings differ"
            )


def _require_cpu_generator(value: object, *, name: str) -> torch.Generator:
    if not isinstance(value, torch.Generator):
        raise TypeError("{} must be a torch.Generator".format(name))
    if value.device.type != "cpu":
        raise ValueError("{} must be a CPU generator".format(name))
    if value is torch.default_generator:
        raise ValueError("{} must not be torch.default_generator".format(name))
    return value


def corrupt_atomic_counting_reference(
    target: AtomicCountingReferenceTarget,
    *,
    generator: torch.Generator,
) -> AtomicCountingCorruptionBatch:
    """Apply the preregistered full-shape, one-step joint corruption.

    Validation occurs before the first draw.  The explicit generator is rolled
    back if any later operation fails, while the global CPU RNG is required to
    remain bitwise unchanged on both success and failure.
    """

    if type(target) is not AtomicCountingReferenceTarget:
        raise TypeError("target must be an exact AtomicCountingReferenceTarget")
    local_generator = _require_cpu_generator(generator, name="generator")

    # Re-run validation before recording the transactional generator state or
    # drawing.  This also detects hand-constructed/pickle-mutated boundaries.
    target._validate()
    local_state = local_generator.get_state().clone()
    global_state = torch.random.get_rng_state().clone()

    config = target.config
    shapes = _target_shapes(config, target.batch_size)
    count_shape = shapes["count"]
    presence_shape = shapes["presence"]
    continuous_shape = shapes["continuous"]
    # The frozen gate is batch-one.  Its preregistered draw stream is therefore
    # defined on the unbatched reference shapes, then lifted to the boundary.
    count_draw_shape = count_shape[1:]
    presence_draw_shape = presence_shape[1:]
    continuous_draw_shape = continuous_shape[1:]
    try:
        # Frozen order: full count uniforms, full presence uniforms, full
        # Gaussian reference.  Padding and hidden cardinality are ignored until
        # every draw has completed.
        u_count = torch.rand(
            count_draw_shape,
            dtype=torch.float32,
            device="cpu",
            generator=local_generator,
        ).unsqueeze(0)
        u_presence = torch.rand(
            presence_draw_shape,
            dtype=torch.float32,
            device="cpu",
            generator=local_generator,
        ).unsqueeze(0)
        z = torch.randn(
            continuous_draw_shape,
            dtype=torch.float32,
            device="cpu",
            generator=local_generator,
        ).unsqueeze(0)

        clean_count = target.clean_count
        clean_presence = target.clean_presence
        clean_mark = target.transformed_mark
        structural = target.structural_applicable
        source_observed = target.source_observed
        valid_time = target.valid_time

        valid_cells = valid_time[:, :, None].expand_as(clean_count)
        count_masked = (u_count < 0.5) & valid_cells
        noisy_count = torch.where(
            count_masked,
            torch.full_like(clean_count, _COUNT_MASK_STATE),
            clean_count,
        )
        noisy_count = torch.where(valid_cells, noisy_count, torch.zeros_like(noisy_count))

        slots = torch.arange(
            config.slot_capacity, dtype=torch.int64, device="cpu"
        ).reshape(1, 1, 1, -1)
        numeric_count = valid_cells & ~count_masked
        slot_active = (
            numeric_count.unsqueeze(-1) & (slots < noisy_count.unsqueeze(-1))
        )

        valid_structural = valid_time[:, :, None, None, None] & structural
        active_structural = slot_active.unsqueeze(-1) & valid_structural
        count_masked_fields = (
            count_masked.unsqueeze(-1).unsqueeze(-1) & valid_structural
        )
        presence_masked = (u_presence < 0.5) & active_structural
        noisy_presence = torch.zeros(presence_shape, dtype=torch.int64)
        noisy_presence = torch.where(
            count_masked_fields | presence_masked,
            torch.full_like(noisy_presence, _PRESENCE_MASK_STATE),
            noisy_presence,
        )
        exposed_presence = active_structural & ~presence_masked
        noisy_presence = torch.where(
            exposed_presence & clean_presence,
            torch.ones_like(noisy_presence),
            noisy_presence,
        )

        continuous_structural = _presence_to_continuous(structural, config)
        continuous_valid = (
            valid_time[:, :, None, None, None] & continuous_structural
        )
        continuous_clean_presence = _presence_to_continuous(
            clean_presence, config
        )
        continuous_source_observed = _presence_to_continuous(
            source_observed, config
        )
        continuous_presence_masked = _presence_to_continuous(
            presence_masked, config
        )
        continuous_slot_active = slot_active.unsqueeze(-1).expand_as(z)
        continuous_count_numeric = (
            numeric_count.unsqueeze(-1).unsqueeze(-1).expand_as(z)
        )
        exposed_clean_mark = (
            continuous_valid
            & continuous_count_numeric
            & continuous_slot_active
            & ~continuous_presence_masked
            & continuous_clean_presence
        )
        noisy_mark = torch.where(
            continuous_valid,
            z,
            torch.zeros_like(z),
        )
        corrupted_present_mark = (
            math.sqrt(0.8) * clean_mark + math.sqrt(0.2) * z
        )
        noisy_mark = torch.where(
            exposed_clean_mark,
            corrupted_present_mark,
            noisy_mark,
        )

        count_loss_mask = valid_cells
        presence_loss_mask = valid_structural
        continuous_loss_mask = exposed_clean_mark & continuous_source_observed
        epsilon = torch.where(continuous_valid, z, torch.zeros_like(z))

        model_input = AtomicCountingModelInput.from_tensors(
            config,
            noisy_count=noisy_count,
            noisy_presence=noisy_presence,
            noisy_mark=noisy_mark,
            structural_applicable=structural,
            valid_time=valid_time,
            slot_active=slot_active,
            anchor_count=target.anchor_count,
            anchor_count_observed=target.anchor_count_observed,
        )
        loss_target = AtomicCountingLossTarget.from_tensors(
            config,
            model_input_digest=model_input.model_input_digest,
            clean_count=clean_count,
            clean_presence=clean_presence,
            clean_transformed_mark=clean_mark,
            epsilon=epsilon,
            count_loss_mask=count_loss_mask,
            presence_loss_mask=presence_loss_mask,
            continuous_loss_mask=continuous_loss_mask,
        )
        result = AtomicCountingCorruptionBatch(model_input, loss_target)
    except BaseException:
        local_generator.set_state(local_state)
        if not torch.equal(torch.random.get_rng_state(), global_state):
            torch.random.set_rng_state(global_state)
        raise

    if not torch.equal(torch.random.get_rng_state(), global_state):
        torch.random.set_rng_state(global_state)
        local_generator.set_state(local_state)
        raise RuntimeError("corruption unexpectedly changed the global CPU RNG")
    return result


@dataclass(frozen=True)
class AtomicCountingReferenceOutput:
    """Differentiable per-cell model outputs in canonical grid shapes."""

    config: AtomicCountingReferenceConfig
    model_input_digest: str
    count_logits: torch.Tensor
    presence_logits: torch.Tensor
    epsilon_prediction: torch.Tensor

    def __post_init__(self) -> None:
        self._validate()

    def _validate(self) -> None:
        _require_valid_config(self.config)
        _require_digest(self.model_input_digest, name="model_input_digest")
        tensors = (
            ("count_logits", self.count_logits, torch.float32, 4),
            ("presence_logits", self.presence_logits, torch.float32, 6),
            ("epsilon_prediction", self.epsilon_prediction, torch.float32, 5),
        )
        for name, value, dtype, rank in tensors:
            if type(value) is not torch.Tensor:
                raise TypeError("{} must be an exact torch.Tensor".format(name))
            if value.device.type != "cpu" or value.layout != torch.strided:
                raise ValueError("{} must be a dense CPU tensor".format(name))
            if value.dtype != dtype or value.ndim != rank:
                raise TypeError(
                    "{} must be a rank-{} float32 tensor".format(name, rank)
                )
        batch = int(self.count_logits.shape[0])
        shapes = _target_shapes(self.config, batch)
        if tuple(self.count_logits.shape) != shapes["count"] + (
            _COUNT_CLEAN_CARDINALITY,
        ):
            raise ValueError("count_logits shape disagrees with config")
        if tuple(self.presence_logits.shape) != shapes["presence"] + (
            _PRESENCE_CLEAN_CARDINALITY,
        ):
            raise ValueError("presence_logits shape disagrees with config")
        if tuple(self.epsilon_prediction.shape) != shapes["continuous"]:
            raise ValueError("epsilon_prediction shape disagrees with config")

    @property
    def batch_size(self) -> int:
        return int(self.count_logits.shape[0])


class AtomicCountingReferenceFFN(nn.Module):
    """The exact bounded positionwise FFN preregistered for this gate."""

    def __init__(
        self,
        config: AtomicCountingReferenceConfig,
        *,
        initialization_generator: torch.Generator,
    ) -> None:
        super().__init__()
        _require_valid_config(config)
        init_generator = _require_cpu_generator(
            initialization_generator, name="initialization_generator"
        )
        if config.estimated_parameter_count > config.parameter_budget:
            # This check deliberately precedes every parameter allocation.
            raise ValueError("parameter preflight failed")

        global_state = torch.random.get_rng_state().clone()
        local_state = init_generator.get_state().clone()
        try:
            # Module constructors perform default initialization, so isolate all
            # constructor-side draws before replacing every parameter below.
            with torch.random.fork_rng(devices=[], enabled=True):
                self.type_embedding = nn.Embedding(
                    config.number_of_event_types,
                    _TYPE_EMBEDDING_WIDTH,
                    device="cpu",
                    dtype=torch.float32,
                )
                self.first_linear = nn.Linear(
                    config.input_width,
                    _FIRST_HIDDEN_WIDTH,
                    device="cpu",
                    dtype=torch.float32,
                )
                self.second_linear = nn.Linear(
                    _FIRST_HIDDEN_WIDTH,
                    _SECOND_HIDDEN_WIDTH,
                    device="cpu",
                    dtype=torch.float32,
                )
                self.count_head = nn.Linear(
                    _SECOND_HIDDEN_WIDTH,
                    _COUNT_CLEAN_CARDINALITY,
                    device="cpu",
                    dtype=torch.float32,
                )
                self.presence_heads = nn.ModuleList(
                    [
                        nn.Linear(
                            _SECOND_HIDDEN_WIDTH,
                            _PRESENCE_CLEAN_CARDINALITY,
                            device="cpu",
                            dtype=torch.float32,
                        )
                        for _field in range(
                            config.number_of_presence_coordinates
                        )
                        for _slot in range(config.slot_capacity)
                    ]
                )
                epsilon_order = sorted(
                    (
                        config.continuous_presence_indices[coordinate],
                        slot,
                        coordinate,
                    )
                    for coordinate in range(
                        config.number_of_continuous_coordinates
                    )
                    for slot in range(config.slot_capacity)
                )
                self.epsilon_heads = nn.ModuleList(
                    [
                        nn.Linear(
                            _SECOND_HIDDEN_WIDTH,
                            1,
                            device="cpu",
                            dtype=torch.float32,
                        )
                        for _item in epsilon_order
                    ]
                )
                self._epsilon_head_order = tuple(epsilon_order)

                nn.init.normal_(
                    self.type_embedding.weight,
                    mean=0.0,
                    std=0.02,
                    generator=init_generator,
                )
                linear_modules = (
                    self.first_linear,
                    self.second_linear,
                    self.count_head,
                    *tuple(self.presence_heads),
                    *tuple(self.epsilon_heads),
                )
                for module in linear_modules:
                    nn.init.xavier_uniform_(
                        module.weight,
                        gain=1.0,
                        generator=init_generator,
                    )
                    nn.init.zeros_(module.bias)
        except BaseException:
            init_generator.set_state(local_state)
            if not torch.equal(torch.random.get_rng_state(), global_state):
                torch.random.set_rng_state(global_state)
            raise
        if not torch.equal(torch.random.get_rng_state(), global_state):
            torch.random.set_rng_state(global_state)
            init_generator.set_state(local_state)
            raise RuntimeError("model construction unexpectedly changed global RNG")

        self.config = config
        parameter_count = sum(parameter.numel() for parameter in self.parameters())
        if parameter_count != config.estimated_parameter_count:
            init_generator.set_state(local_state)
            raise RuntimeError(
                "allocated parameter count {} disagrees with preflight {}".format(
                    parameter_count, config.estimated_parameter_count
                )
            )

    @property
    def parameter_count(self) -> int:
        return sum(parameter.numel() for parameter in self.parameters())

    def _require_cpu_float32_parameters(self) -> None:
        for name, parameter in self.named_parameters():
            if parameter.device.type != "cpu" or parameter.dtype != torch.float32:
                raise ValueError(
                    "model parameter {} must remain CPU float32".format(name)
                )

    def forward(
        self, model_input: AtomicCountingModelInput
    ) -> AtomicCountingReferenceOutput:
        if type(model_input) is not AtomicCountingModelInput:
            raise TypeError(
                "model_input must be an exact AtomicCountingModelInput"
            )
        if model_input.config != self.config:
            raise ValueError("model input config differs from model config")
        _require_valid_config(self.config)
        model_input._validate()
        self._require_cpu_float32_parameters()

        noisy_count = model_input.noisy_count
        noisy_presence = model_input.noisy_presence
        noisy_mark = model_input.noisy_mark
        structural = model_input.structural_applicable
        valid_time = model_input.valid_time
        slot_active = model_input.slot_active
        anchor_count = model_input.anchor_count
        anchor_observed = model_input.anchor_count_observed

        batch = model_input.batch_size
        r = self.config.reference_positions
        k = self.config.number_of_event_types
        count_features = F.one_hot(
            noisy_count, num_classes=_COUNT_NOISY_CARDINALITY
        ).to(dtype=torch.float32)
        presence_features = F.one_hot(
            noisy_presence, num_classes=_PRESENCE_NOISY_CARDINALITY
        ).to(dtype=torch.float32)
        presence_features = presence_features.reshape(batch, r, k, -1)
        mark_features = noisy_mark.reshape(batch, r, k, -1)
        structural_features = structural.to(dtype=torch.float32).reshape(
            batch, r, k, -1
        )
        valid_features = valid_time[:, :, None, None].expand(
            batch, r, k, 1
        ).to(dtype=torch.float32)
        slot_features = slot_active.to(dtype=torch.float32)
        position = (
            2.0 * torch.arange(r, dtype=torch.float32, device="cpu")
            / float(r - 1)
            - 1.0
        ).reshape(1, r, 1, 1).expand(batch, r, k, 1)
        step = torch.ones((batch, r, k, 1), dtype=torch.float32)
        type_index = torch.arange(k, dtype=torch.int64).reshape(1, 1, k)
        type_index = type_index.expand(batch, r, k)
        type_features = self.type_embedding(type_index)
        anchor_features = F.one_hot(
            anchor_count, num_classes=_COUNT_CLEAN_CARDINALITY
        ).to(dtype=torch.float32)
        anchor_observed_features = anchor_observed.unsqueeze(-1).to(
            dtype=torch.float32
        )

        features = torch.cat(
            (
                count_features,
                presence_features,
                mark_features,
                structural_features,
                valid_features,
                slot_features,
                position,
                step,
                type_features,
                anchor_features,
                anchor_observed_features,
            ),
            dim=-1,
        )
        if features.shape[-1] != self.config.input_width:
            raise RuntimeError("constructed feature width disagrees with config")
        hidden = F.gelu(self.first_linear(features), approximate="none")
        hidden = F.gelu(self.second_linear(hidden), approximate="none")

        count_logits = self.count_head(hidden)
        presence_logits = torch.empty(
            (
                batch,
                r,
                k,
                self.config.slot_capacity,
                self.config.number_of_presence_coordinates,
                _PRESENCE_CLEAN_CARDINALITY,
            ),
            dtype=torch.float32,
            device="cpu",
        )
        head_index = 0
        for field_index in range(
            self.config.number_of_presence_coordinates
        ):
            for slot_index in range(self.config.slot_capacity):
                presence_logits[:, :, :, slot_index, field_index, :] = (
                    self.presence_heads[head_index](hidden)
                )
                head_index += 1

        epsilon_prediction = torch.empty(
            (
                batch,
                r,
                k,
                self.config.slot_capacity,
                self.config.number_of_continuous_coordinates,
            ),
            dtype=torch.float32,
            device="cpu",
        )
        for head, (_field, slot_index, coordinate) in zip(
            self.epsilon_heads, self._epsilon_head_order
        ):
            epsilon_prediction[:, :, :, slot_index, coordinate] = head(
                hidden
            ).squeeze(-1)

        valid_cells = valid_time[:, :, None].expand(batch, r, k)
        count_logits = torch.where(
            valid_cells.unsqueeze(-1),
            count_logits,
            torch.zeros_like(count_logits),
        )
        valid_presence = valid_time[:, :, None, None, None] & structural
        presence_logits = torch.where(
            valid_presence.unsqueeze(-1),
            presence_logits,
            torch.zeros_like(presence_logits),
        )
        continuous_structural = _presence_to_continuous(structural, self.config)
        valid_continuous = (
            valid_time[:, :, None, None, None] & continuous_structural
        )
        epsilon_prediction = torch.where(
            valid_continuous,
            epsilon_prediction,
            torch.zeros_like(epsilon_prediction),
        )
        return AtomicCountingReferenceOutput(
            config=self.config,
            model_input_digest=model_input.model_input_digest,
            count_logits=count_logits,
            presence_logits=presence_logits,
            epsilon_prediction=epsilon_prediction,
        )


@dataclass(frozen=True)
class AtomicCountingHybridLoss:
    """The three unit-weight loss terms and their exact sum."""

    total: torch.Tensor
    count: torch.Tensor
    presence: torch.Tensor
    continuous: torch.Tensor
    occupied_count: int
    empty_count: int
    present_count: int
    absent_count: int
    continuous_count: int


def _zero_scalar(reference: torch.Tensor) -> torch.Tensor:
    return torch.zeros((), dtype=reference.dtype, device=reference.device)


def _balanced_cross_entropy(
    logits: torch.Tensor,
    labels: torch.Tensor,
    mask: torch.Tensor,
) -> Tuple[torch.Tensor, int, int]:
    # Select before any finite check or cross-entropy arithmetic, so a poisoned
    # padded/inapplicable storage cell cannot affect the objective.
    selected_logits = logits[mask]
    selected_labels = labels[mask]
    if selected_logits.numel() == 0:
        return _zero_scalar(logits), 0, 0
    if bool(torch.any(~torch.isfinite(selected_logits)).item()):
        raise ValueError("active categorical logits must be finite")
    per_item = F.cross_entropy(selected_logits, selected_labels, reduction="none")
    positive = selected_labels != 0
    negative = ~positive
    positive_count = int(positive.sum().item())
    negative_count = int(negative.sum().item())
    positive_mean = (
        per_item[positive].mean()
        if positive_count
        else _zero_scalar(per_item)
    )
    negative_mean = (
        per_item[negative].mean()
        if negative_count
        else _zero_scalar(per_item)
    )
    return 0.5 * positive_mean + 0.5 * negative_mean, positive_count, negative_count


def atomic_counting_hybrid_loss(
    output: AtomicCountingReferenceOutput,
    target: AtomicCountingLossTarget,
) -> AtomicCountingHybridLoss:
    """Compute the exact balanced categorical plus conditional-epsilon loss."""

    if type(output) is not AtomicCountingReferenceOutput:
        raise TypeError("output must be an exact AtomicCountingReferenceOutput")
    if type(target) is not AtomicCountingLossTarget:
        raise TypeError("target must be an exact AtomicCountingLossTarget")
    output._validate()
    target._validate()
    if output.config != target.config or output.batch_size != target.batch_size:
        raise ValueError("output and loss target boundaries disagree")
    if output.model_input_digest != target.model_input_digest:
        raise ValueError("output and loss target integrity bindings differ")

    clean_count = target.clean_count
    clean_presence = target.clean_presence.to(dtype=torch.int64)
    count_term, occupied_count, empty_count = _balanced_cross_entropy(
        output.count_logits,
        clean_count,
        target.count_loss_mask,
    )
    presence_term, present_count, absent_count = _balanced_cross_entropy(
        output.presence_logits,
        clean_presence,
        target.presence_loss_mask,
    )

    continuous_mask = target.continuous_loss_mask
    prediction = output.epsilon_prediction[continuous_mask]
    epsilon = target.epsilon[continuous_mask]
    continuous_count = int(prediction.numel())
    if continuous_count:
        if bool(torch.any(~torch.isfinite(prediction)).item()):
            raise ValueError("active epsilon predictions must be finite")
        continuous_term = torch.mean(torch.square(prediction - epsilon))
    else:
        continuous_term = _zero_scalar(output.epsilon_prediction)
    total = count_term + presence_term + continuous_term
    return AtomicCountingHybridLoss(
        total=total,
        count=count_term,
        presence=presence_term,
        continuous=continuous_term,
        occupied_count=occupied_count,
        empty_count=empty_count,
        present_count=present_count,
        absent_count=absent_count,
        continuous_count=continuous_count,
    )


__all__ = [
    "AtomicCountingCorruptionBatch",
    "AtomicCountingHybridLoss",
    "AtomicCountingLossTarget",
    "AtomicCountingModelInput",
    "AtomicCountingReferenceConfig",
    "AtomicCountingReferenceFFN",
    "AtomicCountingReferenceOutput",
    "AtomicCountingReferenceTarget",
    "atomic_counting_hybrid_loss",
    "corrupt_atomic_counting_reference",
]
