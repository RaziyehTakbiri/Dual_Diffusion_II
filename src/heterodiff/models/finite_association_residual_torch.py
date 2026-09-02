"""Optional-PyTorch learner primitives for the frozen finite A1 experiment.

The NumPy theory core does not import this module.  Importing it explicitly
requires the optional PyTorch dependency and supplies only the architecture,
feature map, optimization helpers, and continuous correction certificate that
were frozen before the decision experiment.  It does not load data or execute
the decision fixture.

The continuous certificate is an operational certificate for the declared
binary64 evaluator.  Exact rational accumulation prevents the analytic
Lipschitz terms from being rounded downward.  Grid values themselves are
binary64 network evaluations rather than interval enclosures of an ideal
real-arithmetic MLP; a real-arithmetic theorem would require an additional
forward-error or interval analysis.
"""

from __future__ import annotations

from dataclasses import dataclass
from fractions import Fraction
import hashlib
import math
from numbers import Integral
from typing import Optional, Tuple

try:
    import torch
    from torch import nn
    from torch.nn import functional as F
except ModuleNotFoundError as error:  # pragma: no cover - tested in subprocess
    if error.name == "torch":
        raise ModuleNotFoundError(
            "heterodiff.models.finite_association_residual_torch requires "
            "the optional PyTorch dependency; install the 'reference' extra"
        ) from error
    raise


BASE_FEATURE_COUNT = 21
GUIDE_INPUT_FEATURE_COUNT = 22
PRIMARY_HIDDEN_WIDTH = 32
STRONG_DIRECT_HIDDEN_WIDTH = 40
CORRECTION_BOUND = 2048.0
CERTIFICATE_GRID_INTERVALS = 4096
CERTIFICATE_GRID_POINTS = CERTIFICATE_GRID_INTERVALS + 1
CERTIFICATE_TIME_CHUNK = 128
CERTIFICATE_CORRECTION_LIMIT = 20.0
ORDINARY_INPUT_TIME_LIPSCHITZ = math.nextafter(math.pi, math.inf)
GUIDE_INPUT_TIME_LIPSCHITZ = 165.0

_SILU_DERIVATIVE_BOUND_SQUARED = Fraction(121, 100)
_CERTIFICATE_PAIR_COUNT = 20 * 21
_CERTIFICATE_OUTPUT_COUNT = CERTIFICATE_GRID_POINTS * _CERTIFICATE_PAIR_COUNT
_VALID_MODES = frozenset(("direct", "guided", "mismatch", "input"))
_SUPPORTED_COUNT_DTYPES = frozenset(
    (torch.uint8, torch.int8, torch.int16, torch.int32, torch.int64)
)


class ContinuousCorrectionCertificateError(RuntimeError):
    """Raised when a fitted checkpoint cannot receive the frozen certificate."""


def _is_true(value: torch.Tensor) -> bool:
    return bool(value.detach().item())


def _bounded_integer(
    value: object, *, name: str, minimum: int, maximum: int
) -> int:
    if isinstance(value, (bool, torch.Tensor)) or not isinstance(value, Integral):
        raise TypeError("%s must be an integer non-boolean value" % name)
    result = int(value)
    if result < minimum or result > maximum:
        raise ValueError("%s must lie in [%d, %d]" % (name, minimum, maximum))
    return result


def _require_float64_cpu_tensor(
    value: object,
    *,
    name: str,
    shape: Optional[Tuple[int, ...]] = None,
) -> torch.Tensor:
    if not isinstance(value, torch.Tensor):
        raise TypeError("%s must be a torch.Tensor" % name)
    if value.dtype != torch.float64:
        raise TypeError("%s must have torch.float64 dtype" % name)
    if value.device.type != "cpu":
        raise ValueError("%s must be on the CPU" % name)
    if shape is not None and tuple(value.shape) != shape:
        raise ValueError("%s must have shape %r" % (name, shape))
    if _is_true(torch.any(~torch.isfinite(value))):
        raise ValueError("%s must contain only finite values" % name)
    return value


def _require_count_tensor(
    value: object,
    *,
    name: str,
    leading_shape: Tuple[int, ...],
) -> torch.Tensor:
    if not isinstance(value, torch.Tensor):
        raise TypeError("%s must be a torch.Tensor" % name)
    if value.device.type != "cpu":
        raise ValueError("%s must be on the CPU" % name)
    expected = leading_shape + (3,)
    if tuple(value.shape) != expected:
        raise ValueError("%s must have shape %r" % (name, expected))
    if value.dtype == torch.float64:
        if _is_true(torch.any(~torch.isfinite(value))):
            raise ValueError("%s must contain finite counts" % name)
        if _is_true(torch.any(value != torch.round(value))):
            raise ValueError("%s must contain integer-valued counts" % name)
        converted = value
    elif value.dtype in _SUPPORTED_COUNT_DTYPES:
        converted = value.to(dtype=torch.float64)
    else:
        raise TypeError(
            "%s must have an integer count dtype or torch.float64" % name
        )
    if _is_true(torch.any(converted < 0.0)) or _is_true(
        torch.any(converted > 3.0)
    ):
        raise ValueError("%s entries must lie in [0, 3]" % name)
    if _is_true(torch.any(converted.sum(dim=-1) > 3.0)):
        raise ValueError("%s total counts must not exceed three" % name)
    return converted


def finite_association_features(
    direct_time: object,
    latent_counts: object,
    anchor_counts: object,
    overflow_indicator: object,
    *,
    guide_classifier_logit: Optional[object] = None,
) -> torch.Tensor:
    """Return the exact frozen 21 features and optional guide-input feature.

    The leading shape is arbitrary but must be shared by every input.  Count
    coordinates are divided by three before products are formed.  For the
    overflow outcome every anchor count must be exactly zero.
    """

    time = _require_float64_cpu_tensor(direct_time, name="direct_time")
    leading_shape = tuple(time.shape)
    if _is_true(torch.any(time < 0.0)) or _is_true(torch.any(time > 1.0)):
        raise ValueError("direct_time must lie in [0, 1]")
    latent = _require_count_tensor(
        latent_counts, name="latent_counts", leading_shape=leading_shape
    )
    anchors = _require_count_tensor(
        anchor_counts, name="anchor_counts", leading_shape=leading_shape
    )
    if not isinstance(overflow_indicator, torch.Tensor):
        raise TypeError("overflow_indicator must be a torch.Tensor")
    if overflow_indicator.dtype != torch.bool:
        raise TypeError("overflow_indicator must have boolean dtype")
    if overflow_indicator.device.type != "cpu":
        raise ValueError("overflow_indicator must be on the CPU")
    if tuple(overflow_indicator.shape) != leading_shape:
        raise ValueError(
            "overflow_indicator must have shape %r" % (leading_shape,)
        )
    if _is_true(
        torch.any(
            overflow_indicator.unsqueeze(-1) & (anchors != 0.0)
        )
    ):
        raise ValueError("overflow anchor-count coordinates must be exactly zero")

    one_minus_time = 1.0 - time
    latent_scaled = latent / 3.0
    anchor_scaled = anchors / 3.0
    latent_total = latent_scaled.sum(dim=-1)
    anchor_total = anchor_scaled.sum(dim=-1)
    values = (
        time,
        one_minus_time,
        torch.sin(math.pi * time),
        torch.cos(math.pi * time),
        latent_scaled[..., 0],
        latent_scaled[..., 1],
        latent_scaled[..., 2],
        latent_total,
        anchor_scaled[..., 0],
        anchor_scaled[..., 1],
        anchor_scaled[..., 2],
        anchor_total,
        overflow_indicator.to(dtype=torch.float64),
        latent_scaled[..., 0] * anchor_scaled[..., 0],
        latent_scaled[..., 1] * anchor_scaled[..., 1],
        latent_scaled[..., 2] * anchor_scaled[..., 2],
        latent_scaled[..., 0] * anchor_scaled[..., 1],
        latent_scaled[..., 1] * anchor_scaled[..., 2],
        latent_scaled[..., 2] * anchor_scaled[..., 0],
        latent_total * anchor_total,
        torch.ones_like(time),
    )
    features = torch.stack(values, dim=-1)
    if guide_classifier_logit is not None:
        guide = _require_float64_cpu_tensor(
            guide_classifier_logit,
            name="guide_classifier_logit",
            shape=leading_shape,
        )
        features = torch.cat((features, (guide / 4.0).unsqueeze(-1)), dim=-1)
    expected = (
        GUIDE_INPUT_FEATURE_COUNT
        if guide_classifier_logit is not None
        else BASE_FEATURE_COUNT
    )
    if tuple(features.shape) != leading_shape + (expected,) or _is_true(
        torch.any(~torch.isfinite(features))
    ):
        raise ArithmeticError("finite association features are invalid")
    return features


class _Linear64(nn.Module):
    def __init__(
        self,
        input_features: int,
        output_features: int,
        *,
        generator: torch.Generator,
    ) -> None:
        super().__init__()
        self.input_features = input_features
        self.output_features = output_features
        self.weight = nn.Parameter(
            torch.empty(
                (output_features, input_features),
                dtype=torch.float64,
                device="cpu",
            )
        )
        self.bias = nn.Parameter(
            torch.zeros(output_features, dtype=torch.float64, device="cpu")
        )
        nn.init.xavier_uniform_(self.weight, gain=1.0, generator=generator)

    def forward(self, inputs: torch.Tensor) -> torch.Tensor:
        return F.linear(inputs, self.weight, self.bias)


class FiniteAssociationCorrectionNetwork(nn.Module):
    """Frozen two-SiLU correction MLP in CPU binary64."""

    def __init__(
        self,
        *,
        generator: torch.Generator,
        input_features: int = BASE_FEATURE_COUNT,
        hidden_width: int = PRIMARY_HIDDEN_WIDTH,
    ) -> None:
        super().__init__()
        if not isinstance(generator, torch.Generator):
            raise TypeError("generator must be a torch.Generator")
        if generator.device.type != "cpu":
            raise ValueError("generator must be a CPU generator")
        inputs = _bounded_integer(
            input_features,
            name="input_features",
            minimum=BASE_FEATURE_COUNT,
            maximum=GUIDE_INPUT_FEATURE_COUNT,
        )
        width = _bounded_integer(
            hidden_width,
            name="hidden_width",
            minimum=PRIMARY_HIDDEN_WIDTH,
            maximum=STRONG_DIRECT_HIDDEN_WIDTH,
        )
        allowed = (
            (inputs == BASE_FEATURE_COUNT and width == PRIMARY_HIDDEN_WIDTH)
            or (
                inputs == BASE_FEATURE_COUNT
                and width == STRONG_DIRECT_HIDDEN_WIDTH
            )
            or (
                inputs == GUIDE_INPUT_FEATURE_COUNT
                and width == PRIMARY_HIDDEN_WIDTH
            )
        )
        if not allowed:
            raise ValueError(
                "architecture must be 21->32->32->1, 21->40->40->1, "
                "or 22->32->32->1"
            )
        self.input_features = inputs
        self.hidden_width = width
        self.linear1 = _Linear64(inputs, width, generator=generator)
        self.linear2 = _Linear64(width, width, generator=generator)
        self.linear3 = _Linear64(width, 1, generator=generator)

    @property
    def parameter_count(self) -> int:
        return sum(parameter.numel() for parameter in self.parameters())

    def _validate_parameters(self) -> None:
        for name, parameter in self.named_parameters():
            if parameter.dtype != torch.float64 or parameter.device.type != "cpu":
                raise TypeError("model parameter %s must be CPU float64" % name)
            if _is_true(torch.any(~torch.isfinite(parameter))):
                raise ArithmeticError("model parameter %s is non-finite" % name)

    def forward(self, features: object) -> torch.Tensor:
        self._validate_parameters()
        values = _require_float64_cpu_tensor(features, name="features")
        if values.ndim == 0 or values.shape[-1] != self.input_features:
            raise ValueError(
                "features must end in dimension %d" % self.input_features
            )
        hidden = F.silu(self.linear1(values))
        hidden = F.silu(self.linear2(hidden))
        output = self.linear3(hidden).squeeze(-1)
        if _is_true(torch.any(~torch.isfinite(output))):
            raise ArithmeticError("correction network output is non-finite")
        return output


def bounded_finite_association_correction(raw_output: object) -> torch.Tensor:
    """Apply the common near-identity ``2048*tanh(u/2048)`` safety map."""

    raw = _require_float64_cpu_tensor(raw_output, name="raw_output")
    result = CORRECTION_BOUND * torch.tanh(raw / CORRECTION_BOUND)
    if _is_true(torch.any(~torch.isfinite(result))):
        raise ArithmeticError("bounded correction is non-finite")
    return result


def _compose_finite_association_raw_logits(
    raw: torch.Tensor,
    feature_tensor: torch.Tensor,
    direct_time: object,
    terminal_classifier_logit: object,
    *,
    mode: str,
    guide_classifier_logit: Optional[object],
) -> torch.Tensor:
    time = _require_float64_cpu_tensor(
        direct_time, name="direct_time", shape=tuple(raw.shape)
    )
    if _is_true(torch.any(time < 0.0)) or _is_true(torch.any(time > 1.0)):
        raise ValueError("direct_time must lie in [0, 1]")
    terminal = _require_float64_cpu_tensor(
        terminal_classifier_logit,
        name="terminal_classifier_logit",
        shape=tuple(raw.shape),
    )
    guide = None
    if guide_classifier_logit is not None:
        guide = _require_float64_cpu_tensor(
            guide_classifier_logit,
            name="guide_classifier_logit",
            shape=tuple(raw.shape),
        )

    if mode == "direct":
        if guide is not None:
            raise ValueError("direct mode must not receive a guide logit")
        base = terminal
    elif mode in ("guided", "mismatch"):
        if guide is None:
            raise ValueError("guided and mismatch modes require a guide logit")
        base = guide
    else:
        if guide is None:
            raise ValueError("input mode requires the guide feature value")
        if feature_tensor.shape[-1] != GUIDE_INPUT_FEATURE_COUNT or not torch.equal(
            feature_tensor[..., -1], guide / 4.0
        ):
            raise ValueError("the twenty-second feature must equal guide_logit/4")
        base = terminal

    terminal_mask = time == 1.0
    if mode in ("guided", "mismatch") and _is_true(torch.any(terminal_mask)):
        if not torch.allclose(
            base[terminal_mask],
            terminal[terminal_mask],
            atol=1.0e-12,
            rtol=0.0,
        ):
            raise ValueError("terminal guide and terminal classifier logit disagree")
    correction = (1.0 - time) * bounded_finite_association_correction(raw)
    result = base + correction
    if _is_true(torch.any(~torch.isfinite(result))):
        raise ArithmeticError("composed classifier logit is non-finite")
    return result


def finite_association_logits(
    model: FiniteAssociationCorrectionNetwork,
    features: object,
    direct_time: object,
    terminal_classifier_logit: object,
    *,
    mode: str,
    guide_classifier_logit: Optional[object] = None,
) -> torch.Tensor:
    """Compose direct, guided, mismatched-guide, or guide-input logits."""

    if type(model) is not FiniteAssociationCorrectionNetwork:
        raise TypeError("model must be an exact FiniteAssociationCorrectionNetwork")
    if not isinstance(mode, str) or mode not in _VALID_MODES:
        raise ValueError("mode must be direct, guided, mismatch, or input")
    feature_tensor = _require_float64_cpu_tensor(features, name="features")
    expected_features = (
        GUIDE_INPUT_FEATURE_COUNT if mode == "input" else BASE_FEATURE_COUNT
    )
    if model.input_features != expected_features:
        raise ValueError("model input size does not match the selected mode")
    raw = model(feature_tensor)
    return _compose_finite_association_raw_logits(
        raw,
        feature_tensor,
        direct_time,
        terminal_classifier_logit,
        mode=mode,
        guide_classifier_logit=guide_classifier_logit,
    )


def cosine_adamw_learning_rate(update_index: object, total_updates: object) -> float:
    """Return the frozen endpoint-inclusive cosine learning rate."""

    updates = _bounded_integer(
        total_updates,
        name="total_updates",
        minimum=0,
        maximum=1_000_000,
    )
    if updates < 2:
        raise ValueError("total_updates must be at least two")
    index = _bounded_integer(
        update_index,
        name="update_index",
        minimum=0,
        maximum=updates - 1,
    )
    return 1.0e-5 + 0.5 * (1.0e-3 - 1.0e-5) * (
        1.0 + math.cos(math.pi * index / (updates - 1))
    )


def make_finite_association_adamw(
    model: FiniteAssociationCorrectionNetwork,
) -> torch.optim.AdamW:
    """Construct the exact deterministic CPU AdamW optimizer."""

    if type(model) is not FiniteAssociationCorrectionNetwork:
        raise TypeError("model must be an exact FiniteAssociationCorrectionNetwork")
    model._validate_parameters()
    return torch.optim.AdamW(
        tuple(model.parameters()),
        lr=1.0e-3,
        betas=(0.9, 0.999),
        eps=1.0e-8,
        weight_decay=1.0e-6,
        foreach=False,
        fused=False,
    )


@dataclass(frozen=True)
class FiniteAssociationAdamWUpdate:
    update_index: int
    learning_rate: float
    unclipped_gradient_norm: float


def _validate_optimizer_ownership(
    model: FiniteAssociationCorrectionNetwork,
    optimizer: object,
) -> torch.optim.AdamW:
    if not isinstance(optimizer, torch.optim.AdamW):
        raise TypeError("optimizer must be a torch.optim.AdamW")
    if len(optimizer.param_groups) != 1:
        raise ValueError("optimizer must contain exactly one parameter group")
    owned = tuple(optimizer.param_groups[0]["params"])
    expected = tuple(model.parameters())
    if len(owned) != len(expected) or any(
        actual is not wanted for actual, wanted in zip(owned, expected)
    ):
        raise ValueError("optimizer parameters do not exactly match the model")
    group = optimizer.param_groups[0]
    if (
        tuple(group["betas"]) != (0.9, 0.999)
        or float(group["eps"]) != 1.0e-8
        or float(group["weight_decay"]) != 1.0e-6
        or bool(group["amsgrad"])
        or bool(group["maximize"])
        or group["foreach"] is not False
        or bool(group["capturable"])
        or bool(group["differentiable"])
        or group["fused"] is not False
    ):
        raise ValueError("optimizer hyperparameters differ from the frozen AdamW")
    return optimizer


def finite_association_adamw_update(
    model: FiniteAssociationCorrectionNetwork,
    optimizer: object,
    loss: object,
    *,
    update_index: object,
    total_updates: object,
) -> FiniteAssociationAdamWUpdate:
    """Apply one scheduled, norm-clipped deterministic AdamW update."""

    if type(model) is not FiniteAssociationCorrectionNetwork:
        raise TypeError("model must be an exact FiniteAssociationCorrectionNetwork")
    checked_optimizer = _validate_optimizer_ownership(model, optimizer)
    checked_loss = _require_float64_cpu_tensor(loss, name="loss", shape=())
    learning_rate = cosine_adamw_learning_rate(update_index, total_updates)
    index = int(update_index)  # validation above rejected booleans and non-integers
    checked_optimizer.param_groups[0]["lr"] = learning_rate
    checked_optimizer.zero_grad(set_to_none=True)
    checked_loss.backward()
    gradient_norm_tensor = torch.nn.utils.clip_grad_norm_(
        tuple(model.parameters()),
        max_norm=1.0,
        error_if_nonfinite=True,
    )
    gradient_norm = float(gradient_norm_tensor.detach().item())
    if not math.isfinite(gradient_norm) or gradient_norm < 0.0:
        raise ArithmeticError("gradient norm is invalid")
    checked_optimizer.step()
    model._validate_parameters()
    return FiniteAssociationAdamWUpdate(
        update_index=index,
        learning_rate=learning_rate,
        unclipped_gradient_norm=gradient_norm,
    )


def _fraction_from_float(value: float) -> Fraction:
    numerator, denominator = value.as_integer_ratio()
    return Fraction(numerator, denominator)


def _outward_float(value: Fraction, *, name: str) -> float:
    try:
        rounded = float(value)
    except OverflowError as error:
        raise ArithmeticError("%s exceeds binary64 range" % name) from error
    result = math.nextafter(rounded, math.inf)
    if not math.isfinite(result):
        raise ArithmeticError("%s has no finite outward binary64 bound" % name)
    return result


def outward_infinity_row_sum(weight: object) -> float:
    """Return an exact-accumulation outward upper infinity row-sum norm."""

    matrix = _require_float64_cpu_tensor(weight, name="weight")
    if matrix.ndim != 2 or min(matrix.shape) <= 0:
        raise ValueError("weight must be a nonempty two-dimensional matrix")
    maximum = Fraction(0)
    detached = matrix.detach()
    for row in detached:
        exact = Fraction(0)
        for entry in row:
            scalar = abs(float(entry.item()))
            exact += _fraction_from_float(scalar)
        if exact > maximum:
            maximum = exact
    return _outward_float(maximum, name="outward infinity row sum")


def _tensor_sha256_items(items: Tuple[Tuple[str, torch.Tensor], ...]) -> str:
    digest = hashlib.sha256()
    for name, tensor in items:
        detached = tensor.detach().to(device="cpu").contiguous()
        digest.update(name.encode("utf-8"))
        digest.update(str(detached.dtype).encode("ascii"))
        digest.update(repr(tuple(detached.shape)).encode("ascii"))
        digest.update(detached.numpy().tobytes(order="C"))
    return digest.hexdigest()


@dataclass(frozen=True)
class FiniteAssociationMLPSnapshot:
    input_features: int
    hidden_width: int
    weight1: torch.Tensor
    bias1: torch.Tensor
    weight2: torch.Tensor
    bias2: torch.Tensor
    weight3: torch.Tensor
    bias3: torch.Tensor
    parameter_sha256: str


def snapshot_finite_association_mlp(
    model: FiniteAssociationCorrectionNetwork,
) -> FiniteAssociationMLPSnapshot:
    """Clone and validate exactly the declared three-linear, two-SiLU graph."""

    if type(model) is not FiniteAssociationCorrectionNetwork:
        raise TypeError("model must be an exact FiniteAssociationCorrectionNetwork")
    model._validate_parameters()
    expected_modules = {
        "": model,
        "linear1": model.linear1,
        "linear2": model.linear2,
        "linear3": model.linear3,
    }
    actual_modules = dict(model.named_modules())
    if actual_modules != expected_modules:
        raise ValueError("model graph differs from the frozen three-linear MLP")
    expected_shapes = (
        (model.hidden_width, model.input_features),
        (model.hidden_width,),
        (model.hidden_width, model.hidden_width),
        (model.hidden_width,),
        (1, model.hidden_width),
        (1,),
    )
    source = (
        model.linear1.weight,
        model.linear1.bias,
        model.linear2.weight,
        model.linear2.bias,
        model.linear3.weight,
        model.linear3.bias,
    )
    if tuple(tuple(value.shape) for value in source) != expected_shapes:
        raise ValueError("model parameter shapes differ from the frozen architecture")
    names = ("weight1", "bias1", "weight2", "bias2", "weight3", "bias3")
    clones = tuple(value.detach().clone() for value in source)
    digest = _tensor_sha256_items(tuple(zip(names, clones)))
    return FiniteAssociationMLPSnapshot(
        input_features=model.input_features,
        hidden_width=model.hidden_width,
        weight1=clones[0],
        bias1=clones[1],
        weight2=clones[2],
        bias2=clones[3],
        weight3=clones[4],
        bias3=clones[5],
        parameter_sha256=digest,
    )


def _snapshot_items(
    snapshot: FiniteAssociationMLPSnapshot,
) -> Tuple[Tuple[str, torch.Tensor], ...]:
    return (
        ("weight1", snapshot.weight1),
        ("bias1", snapshot.bias1),
        ("weight2", snapshot.weight2),
        ("bias2", snapshot.bias2),
        ("weight3", snapshot.weight3),
        ("bias3", snapshot.bias3),
    )


def _validate_snapshot(snapshot: object) -> FiniteAssociationMLPSnapshot:
    if type(snapshot) is not FiniteAssociationMLPSnapshot:
        raise TypeError("snapshot must be an exact FiniteAssociationMLPSnapshot")
    for name, tensor in _snapshot_items(snapshot):
        _require_float64_cpu_tensor(tensor, name="snapshot.%s" % name)
    expected_shapes = (
        (snapshot.hidden_width, snapshot.input_features),
        (snapshot.hidden_width,),
        (snapshot.hidden_width, snapshot.hidden_width),
        (snapshot.hidden_width,),
        (1, snapshot.hidden_width),
        (1,),
    )
    if tuple(tuple(tensor.shape) for _, tensor in _snapshot_items(snapshot)) != (
        expected_shapes
    ):
        raise ValueError("snapshot tensor shapes are inconsistent")
    digest = _tensor_sha256_items(_snapshot_items(snapshot))
    if digest != snapshot.parameter_sha256:
        raise ValueError("snapshot tensors do not match their parameter digest")
    return snapshot


@dataclass(frozen=True)
class FiniteAssociationLipschitzWitness:
    input_time_lipschitz: float
    layer_outward_row_sums: Tuple[float, float, float]
    network_time_lipschitz: float
    _network_time_lipschitz_fraction: Fraction


def finite_association_network_lipschitz(
    snapshot: FiniteAssociationMLPSnapshot,
) -> FiniteAssociationLipschitzWitness:
    """Return the exact-composition time-Lipschitz witness for one snapshot."""

    checked = _validate_snapshot(snapshot)
    norms = (
        outward_infinity_row_sum(checked.weight1),
        outward_infinity_row_sum(checked.weight2),
        outward_infinity_row_sum(checked.weight3),
    )
    if checked.input_features == BASE_FEATURE_COUNT:
        input_lipschitz = ORDINARY_INPUT_TIME_LIPSCHITZ
    elif checked.input_features == GUIDE_INPUT_FEATURE_COUNT:
        input_lipschitz = GUIDE_INPUT_TIME_LIPSCHITZ
    else:
        raise ValueError("snapshot has an unsupported input feature count")
    exact = _SILU_DERIVATIVE_BOUND_SQUARED
    for norm in norms:
        exact *= _fraction_from_float(norm)
    exact *= _fraction_from_float(input_lipschitz)
    reported = _outward_float(exact, name="network time-Lipschitz bound")
    return FiniteAssociationLipschitzWitness(
        input_time_lipschitz=input_lipschitz,
        layer_outward_row_sums=norms,
        network_time_lipschitz=reported,
        _network_time_lipschitz_fraction=exact,
    )


def _canonical_count_vectors() -> Tuple[Tuple[int, int, int], ...]:
    return tuple(
        (first, second, total - first - second)
        for total in range(4)
        for first in range(total + 1)
        for second in range(total - first + 1)
    )


_CANONICAL_COUNTS = _canonical_count_vectors()


def _snapshot_forward(
    snapshot: FiniteAssociationMLPSnapshot, features: torch.Tensor
) -> torch.Tensor:
    hidden = F.silu(F.linear(features, snapshot.weight1, snapshot.bias1))
    hidden = F.silu(F.linear(hidden, snapshot.weight2, snapshot.bias2))
    return F.linear(hidden, snapshot.weight3, snapshot.bias3).squeeze(-1)


def _finite_association_validated_snapshot_logits(
    snapshot: FiniteAssociationMLPSnapshot,
    features: object,
    direct_time: object,
    terminal_classifier_logit: object,
    *,
    mode: str,
    guide_classifier_logit: Optional[object] = None,
) -> torch.Tensor:
    """Evaluate a snapshot that was already validated at a custody boundary."""

    checked = snapshot
    if not isinstance(mode, str) or mode not in _VALID_MODES:
        raise ValueError("mode must be direct, guided, mismatch, or input")
    feature_tensor = _require_float64_cpu_tensor(features, name="features")
    expected_features = (
        GUIDE_INPUT_FEATURE_COUNT if mode == "input" else BASE_FEATURE_COUNT
    )
    if checked.input_features != expected_features:
        raise ValueError("snapshot input size does not match the selected mode")
    if feature_tensor.ndim == 0 or feature_tensor.shape[-1] != expected_features:
        raise ValueError(
            "features must end in dimension %d" % expected_features
        )
    raw = _snapshot_forward(checked, feature_tensor)
    if _is_true(torch.any(~torch.isfinite(raw))):
        raise ArithmeticError("snapshot correction output is non-finite")
    return _compose_finite_association_raw_logits(
        raw,
        feature_tensor,
        direct_time,
        terminal_classifier_logit,
        mode=mode,
        guide_classifier_logit=guide_classifier_logit,
    )


def finite_association_snapshot_logits(
    snapshot: FiniteAssociationMLPSnapshot,
    features: object,
    direct_time: object,
    terminal_classifier_logit: object,
    *,
    mode: str,
    guide_classifier_logit: Optional[object] = None,
) -> torch.Tensor:
    """Compose logits through the immutable, fixed functional MLP graph.

    This public boundary rehashes the snapshot before evaluation.  A fitted
    production evaluator may instead call the private validated helper after
    it has cloned and certified an owned snapshot; that avoids repeated
    hashing inside adaptive path integrators while retaining boundary checks.
    """

    checked = _validate_snapshot(snapshot)
    return _finite_association_validated_snapshot_logits(
        checked,
        features,
        direct_time,
        terminal_classifier_logit,
        mode=mode,
        guide_classifier_logit=guide_classifier_logit,
    )


def _guide_grid(
    value: Optional[object], *, required: bool
) -> Optional[torch.Tensor]:
    if value is None:
        if required:
            raise ValueError(
                "guide_classifier_logit_grid is required for the 22-input control"
            )
        return None
    if not required:
        raise ValueError("a 21-input certificate must not receive a guide grid")
    return _require_float64_cpu_tensor(
        value,
        name="guide_classifier_logit_grid",
        shape=(CERTIFICATE_GRID_POINTS, 20, 21),
    )


def _require_fixture_sha256(value: object) -> str:
    if type(value) is not str:
        raise TypeError("frozen_fixture_sha256 must be a string")
    if len(value) != 64 or any(
        character not in "0123456789abcdef" for character in value
    ):
        raise ValueError(
            "frozen_fixture_sha256 must be a lowercase 64-hex SHA-256 digest"
        )
    return value


def _certificate_feature_sha256(
    guide_grid: Optional[torch.Tensor], frozen_fixture_sha256: str
) -> str:
    digest = hashlib.sha256()
    digest.update(b"finite-association-certificate-grid-v2")
    digest.update(frozen_fixture_sha256.encode("ascii"))
    digest.update(repr(_CANONICAL_COUNTS).encode("ascii"))
    if guide_grid is None:
        digest.update(b"ordinary-21-input")
    else:
        digest.update(b"guide-input-22")
        digest.update(guide_grid.detach().contiguous().numpy().tobytes(order="C"))
    return digest.hexdigest()


def _certificate_witness_sha256(
    *,
    parameter_sha256: str,
    frozen_fixture_sha256: str,
    feature_sha256: str,
    input_features: int,
    hidden_width: int,
    grid_intervals: int,
    grid_points: int,
    time_chunk_size: int,
    pair_count: int,
    evaluated_output_count: int,
    layer_outward_row_sums: Tuple[float, float, float],
    input_time_lipschitz: float,
    network_time_lipschitz: float,
    maximum_grid_absolute_correction: float,
    outward_grid_maximum: float,
    half_cell_allowance: float,
    certified_maximum_absolute_correction: float,
    correction_limit: float,
    passed: bool,
) -> str:
    digest = hashlib.sha256()
    digest.update(b"finite-association-continuous-certificate-v1\0")
    values = (
        parameter_sha256,
        frozen_fixture_sha256,
        feature_sha256,
        str(input_features),
        str(hidden_width),
        str(grid_intervals),
        str(grid_points),
        str(time_chunk_size),
        str(pair_count),
        str(evaluated_output_count),
        *(float(value).hex() for value in layer_outward_row_sums),
        float(input_time_lipschitz).hex(),
        float(network_time_lipschitz).hex(),
        float(maximum_grid_absolute_correction).hex(),
        float(outward_grid_maximum).hex(),
        float(half_cell_allowance).hex(),
        float(certified_maximum_absolute_correction).hex(),
        float(correction_limit).hex(),
        "PASS" if passed else "HOLD",
    )
    for value in values:
        encoded = value.encode("ascii")
        digest.update(len(encoded).to_bytes(4, "big"))
        digest.update(encoded)
    return digest.hexdigest()


@dataclass(frozen=True)
class ContinuousCorrectionCertificate:
    parameter_sha256: str
    frozen_fixture_sha256: str
    feature_sha256: str
    input_features: int
    hidden_width: int
    grid_intervals: int
    grid_points: int
    time_chunk_size: int
    pair_count: int
    evaluated_output_count: int
    layer_outward_row_sums: Tuple[float, float, float]
    input_time_lipschitz: float
    network_time_lipschitz: float
    maximum_grid_absolute_correction: float
    outward_grid_maximum: float
    half_cell_allowance: float
    certified_maximum_absolute_correction: float
    correction_limit: float
    passed: bool
    certificate_sha256: str

    def __post_init__(self) -> None:
        for name in (
            "parameter_sha256",
            "frozen_fixture_sha256",
            "feature_sha256",
            "certificate_sha256",
        ):
            value = getattr(self, name)
            if type(value) is not str or len(value) != 64 or any(
                character not in "0123456789abcdef" for character in value
            ):
                raise ValueError("%s must be lowercase SHA-256" % name)
        if (self.input_features, self.hidden_width) not in (
            (BASE_FEATURE_COUNT, PRIMARY_HIDDEN_WIDTH),
            (BASE_FEATURE_COUNT, STRONG_DIRECT_HIDDEN_WIDTH),
            (GUIDE_INPUT_FEATURE_COUNT, PRIMARY_HIDDEN_WIDTH),
        ):
            raise ValueError("certificate architecture is not frozen")
        if (
            self.grid_intervals != CERTIFICATE_GRID_INTERVALS
            or self.grid_points != CERTIFICATE_GRID_POINTS
            or self.time_chunk_size != CERTIFICATE_TIME_CHUNK
            or self.pair_count != _CERTIFICATE_PAIR_COUNT
            or self.evaluated_output_count != _CERTIFICATE_OUTPUT_COUNT
        ):
            raise ValueError("certificate grid coverage is not frozen")
        floats = (
            *self.layer_outward_row_sums,
            self.input_time_lipschitz,
            self.network_time_lipschitz,
            self.maximum_grid_absolute_correction,
            self.outward_grid_maximum,
            self.half_cell_allowance,
            self.certified_maximum_absolute_correction,
            self.correction_limit,
        )
        if len(self.layer_outward_row_sums) != 3 or any(
            not math.isfinite(float(value)) or float(value) < 0.0
            for value in floats
        ):
            raise ValueError("certificate numerical witnesses are invalid")
        if self.correction_limit != CERTIFICATE_CORRECTION_LIMIT:
            raise ValueError("certificate correction limit is not frozen")
        if self.outward_grid_maximum != math.nextafter(
            self.maximum_grid_absolute_correction, math.inf
        ):
            raise ValueError("certificate grid maximum is not outward rounded")
        if (
            self.certified_maximum_absolute_correction
            > self.correction_limit
            or self.half_cell_allowance > self.correction_limit
            or self.passed is not True
        ):
            raise ValueError("certificate is not a valid PASS witness")
        expected = _certificate_witness_sha256(
            parameter_sha256=self.parameter_sha256,
            frozen_fixture_sha256=self.frozen_fixture_sha256,
            feature_sha256=self.feature_sha256,
            input_features=self.input_features,
            hidden_width=self.hidden_width,
            grid_intervals=self.grid_intervals,
            grid_points=self.grid_points,
            time_chunk_size=self.time_chunk_size,
            pair_count=self.pair_count,
            evaluated_output_count=self.evaluated_output_count,
            layer_outward_row_sums=self.layer_outward_row_sums,
            input_time_lipschitz=self.input_time_lipschitz,
            network_time_lipschitz=self.network_time_lipschitz,
            maximum_grid_absolute_correction=(
                self.maximum_grid_absolute_correction
            ),
            outward_grid_maximum=self.outward_grid_maximum,
            half_cell_allowance=self.half_cell_allowance,
            certified_maximum_absolute_correction=(
                self.certified_maximum_absolute_correction
            ),
            correction_limit=self.correction_limit,
            passed=self.passed,
        )
        if expected != self.certificate_sha256:
            raise ValueError("certificate witness digest is inconsistent")


def certify_finite_association_continuous_correction(
    model: FiniteAssociationCorrectionNetwork,
    *,
    frozen_fixture_sha256: object,
    guide_classifier_logit_grid: Optional[object] = None,
) -> ContinuousCorrectionCertificate:
    """Certify the fitted correction on all 4097 x 20 x 21 frozen cells.

    No grid size, correction limit, or Lipschitz constant is caller-adjustable.
    A failed checkpoint raises and produces no reusable PASS certificate.
    """

    chunk_size = CERTIFICATE_TIME_CHUNK
    fixture_sha256 = _require_fixture_sha256(frozen_fixture_sha256)
    snapshot = snapshot_finite_association_mlp(model)
    guide_grid = _guide_grid(
        guide_classifier_logit_grid,
        required=snapshot.input_features == GUIDE_INPUT_FEATURE_COUNT,
    )
    feature_digest = _certificate_feature_sha256(guide_grid, fixture_sha256)
    lipschitz = finite_association_network_lipschitz(snapshot)
    derivative_exact = Fraction(int(CORRECTION_BOUND), 1) + (
        lipschitz._network_time_lipschitz_fraction
    )
    half_cell_exact = derivative_exact / (2 * CERTIFICATE_GRID_INTERVALS)
    if half_cell_exact > Fraction(int(CERTIFICATE_CORRECTION_LIMIT), 1):
        raise ContinuousCorrectionCertificateError(
            "continuous correction half-cell allowance already exceeds 20"
        )

    latent_base = torch.tensor(_CANONICAL_COUNTS, dtype=torch.int64)
    anchor_base = torch.tensor(
        _CANONICAL_COUNTS + ((0, 0, 0),), dtype=torch.int64
    )
    overflow_base = torch.zeros(21, dtype=torch.bool)
    overflow_base[-1] = True
    maximum = 0.0
    evaluated = 0
    terminal_checked = False
    with torch.no_grad():
        for start in range(0, CERTIFICATE_GRID_POINTS, chunk_size):
            stop = min(start + chunk_size, CERTIFICATE_GRID_POINTS)
            time_values = (
                torch.arange(start, stop, dtype=torch.float64)
                / CERTIFICATE_GRID_INTERVALS
            )
            shape = (stop - start, 20, 21)
            times = time_values[:, None, None].expand(shape)
            latent = latent_base[None, :, None, :].expand(shape + (3,))
            anchors = anchor_base[None, None, :, :].expand(shape + (3,))
            overflow = overflow_base[None, None, :].expand(shape)
            guide_slice = None if guide_grid is None else guide_grid[start:stop]
            features = finite_association_features(
                times,
                latent,
                anchors,
                overflow,
                guide_classifier_logit=guide_slice,
            )
            raw = _snapshot_forward(
                snapshot, features.reshape(-1, snapshot.input_features)
            ).reshape(shape)
            correction = (1.0 - times) * (
                CORRECTION_BOUND * torch.tanh(raw / CORRECTION_BOUND)
            )
            if _is_true(torch.any(~torch.isfinite(correction))):
                raise ContinuousCorrectionCertificateError(
                    "non-finite correction occurred on the certificate grid"
                )
            if stop == CERTIFICATE_GRID_POINTS:
                terminal_checked = bool(
                    torch.equal(correction[-1], torch.zeros_like(correction[-1]))
                )
            maximum = max(
                maximum, float(torch.max(torch.abs(correction)).item())
            )
            evaluated += correction.numel()
    if evaluated != _CERTIFICATE_OUTPUT_COUNT or not terminal_checked:
        raise ContinuousCorrectionCertificateError(
            "certificate grid coverage or terminal-zero check failed"
        )

    outward_maximum = math.nextafter(maximum, math.inf)
    if not math.isfinite(outward_maximum):
        raise ContinuousCorrectionCertificateError(
            "grid maximum has no finite outward bound"
        )
    certified_exact = _fraction_from_float(outward_maximum) + half_cell_exact
    if certified_exact > Fraction(int(CERTIFICATE_CORRECTION_LIMIT), 1):
        try:
            failed_bound = float(certified_exact)
        except OverflowError:
            failed_bound = math.inf
        raise ContinuousCorrectionCertificateError(
            "continuous correction certificate exceeds 20 (bound=%r)"
            % failed_bound
        )
    half_cell = _outward_float(half_cell_exact, name="half-cell allowance")
    certified = _outward_float(
        certified_exact, name="certified correction maximum"
    )
    if certified > CERTIFICATE_CORRECTION_LIMIT:
        raise ContinuousCorrectionCertificateError(
            "outward continuous correction certificate exceeds 20"
        )
    ending_snapshot = snapshot_finite_association_mlp(model)
    if ending_snapshot.parameter_sha256 != snapshot.parameter_sha256:
        raise ContinuousCorrectionCertificateError(
            "model parameters changed during certification"
        )
    witness_values = dict(
        parameter_sha256=snapshot.parameter_sha256,
        frozen_fixture_sha256=fixture_sha256,
        feature_sha256=feature_digest,
        input_features=snapshot.input_features,
        hidden_width=snapshot.hidden_width,
        grid_intervals=CERTIFICATE_GRID_INTERVALS,
        grid_points=CERTIFICATE_GRID_POINTS,
        time_chunk_size=chunk_size,
        pair_count=_CERTIFICATE_PAIR_COUNT,
        evaluated_output_count=evaluated,
        layer_outward_row_sums=lipschitz.layer_outward_row_sums,
        input_time_lipschitz=lipschitz.input_time_lipschitz,
        network_time_lipschitz=lipschitz.network_time_lipschitz,
        maximum_grid_absolute_correction=maximum,
        outward_grid_maximum=outward_maximum,
        half_cell_allowance=half_cell,
        certified_maximum_absolute_correction=certified,
        correction_limit=CERTIFICATE_CORRECTION_LIMIT,
        passed=True,
    )
    return ContinuousCorrectionCertificate(
        **witness_values,
        certificate_sha256=_certificate_witness_sha256(**witness_values),
    )


def require_matching_snapshot_continuous_certificate(
    snapshot: FiniteAssociationMLPSnapshot,
    certificate: object,
    *,
    frozen_fixture_sha256: object,
    guide_classifier_logit_grid: Optional[object] = None,
) -> ContinuousCorrectionCertificate:
    """Fail unless every analytic witness matches an immutable snapshot."""

    if type(certificate) is not ContinuousCorrectionCertificate:
        raise TypeError("certificate must be an exact ContinuousCorrectionCertificate")
    checked = _validate_snapshot(snapshot)
    fixture_sha256 = _require_fixture_sha256(frozen_fixture_sha256)
    if fixture_sha256 != certificate.frozen_fixture_sha256:
        raise ContinuousCorrectionCertificateError(
            "frozen fixture token no longer matches the PASS certificate"
        )
    if checked.parameter_sha256 != certificate.parameter_sha256:
        raise ContinuousCorrectionCertificateError(
            "model checkpoint no longer matches the PASS certificate"
        )
    guide_grid = _guide_grid(
        guide_classifier_logit_grid,
        required=checked.input_features == GUIDE_INPUT_FEATURE_COUNT,
    )
    if (
        _certificate_feature_sha256(guide_grid, fixture_sha256)
        != certificate.feature_sha256
    ):
        raise ContinuousCorrectionCertificateError(
            "certificate guide/feature digest no longer matches"
        )
    if (
        certificate.input_features != checked.input_features
        or certificate.hidden_width != checked.hidden_width
    ):
        raise ContinuousCorrectionCertificateError(
            "certificate architecture no longer matches the snapshot"
        )
    lipschitz = finite_association_network_lipschitz(checked)
    if (
        certificate.layer_outward_row_sums
        != lipschitz.layer_outward_row_sums
        or certificate.input_time_lipschitz
        != lipschitz.input_time_lipschitz
        or certificate.network_time_lipschitz
        != lipschitz.network_time_lipschitz
    ):
        raise ContinuousCorrectionCertificateError(
            "certificate Lipschitz witness no longer matches the snapshot"
        )
    derivative_exact = Fraction(int(CORRECTION_BOUND), 1) + (
        lipschitz._network_time_lipschitz_fraction
    )
    half_cell_exact = derivative_exact / (2 * CERTIFICATE_GRID_INTERVALS)
    expected_half_cell = _outward_float(
        half_cell_exact, name="matching half-cell allowance"
    )
    certified_exact = (
        _fraction_from_float(certificate.outward_grid_maximum)
        + half_cell_exact
    )
    expected_certified = _outward_float(
        certified_exact, name="matching certified correction maximum"
    )
    if (
        certificate.half_cell_allowance != expected_half_cell
        or certificate.certified_maximum_absolute_correction
        != expected_certified
    ):
        raise ContinuousCorrectionCertificateError(
            "certificate continuous bound is inconsistent with its witness"
        )
    return certificate


def require_matching_continuous_certificate(
    model: FiniteAssociationCorrectionNetwork,
    certificate: object,
    *,
    frozen_fixture_sha256: object,
    guide_classifier_logit_grid: Optional[object] = None,
) -> ContinuousCorrectionCertificate:
    """Fail unless a PASS certificate still matches model and guide inputs."""

    if type(model) is not FiniteAssociationCorrectionNetwork:
        raise TypeError("model must be an exact FiniteAssociationCorrectionNetwork")
    return require_matching_snapshot_continuous_certificate(
        snapshot_finite_association_mlp(model),
        certificate,
        frozen_fixture_sha256=frozen_fixture_sha256,
        guide_classifier_logit_grid=guide_classifier_logit_grid,
    )


__all__ = [
    "BASE_FEATURE_COUNT",
    "CERTIFICATE_CORRECTION_LIMIT",
    "CERTIFICATE_GRID_INTERVALS",
    "CERTIFICATE_GRID_POINTS",
    "CERTIFICATE_TIME_CHUNK",
    "CORRECTION_BOUND",
    "ContinuousCorrectionCertificate",
    "ContinuousCorrectionCertificateError",
    "FiniteAssociationAdamWUpdate",
    "FiniteAssociationCorrectionNetwork",
    "FiniteAssociationLipschitzWitness",
    "FiniteAssociationMLPSnapshot",
    "GUIDE_INPUT_FEATURE_COUNT",
    "GUIDE_INPUT_TIME_LIPSCHITZ",
    "ORDINARY_INPUT_TIME_LIPSCHITZ",
    "PRIMARY_HIDDEN_WIDTH",
    "STRONG_DIRECT_HIDDEN_WIDTH",
    "bounded_finite_association_correction",
    "certify_finite_association_continuous_correction",
    "cosine_adamw_learning_rate",
    "finite_association_adamw_update",
    "finite_association_features",
    "finite_association_logits",
    "finite_association_network_lipschitz",
    "finite_association_snapshot_logits",
    "make_finite_association_adamw",
    "outward_infinity_row_sum",
    "require_matching_continuous_certificate",
    "require_matching_snapshot_continuous_certificate",
    "snapshot_finite_association_mlp",
]
