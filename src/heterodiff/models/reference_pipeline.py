"""Deterministic clean-to-corrupted batches for the fixed-grid reference.

This optional-PyTorch module is a narrow boundary between an already aligned,
clean fixed-grid tensor pool and :class:`FixedGridTrainingBatch`.  It does not
parse event records, choose a grid, impute missing values, sample a diffusion
step, or infer observation/loss masks.  Those choices remain explicit caller
responsibilities.

Categorical targets are clean ``x0`` states.  Continuous targets are the exact
``epsilon`` values drawn by the forward VP corruption.  Padding is required to
be canonical zero, remains exact zero, and consumes no local-generator draws.
"""

from __future__ import annotations

from numbers import Integral

try:
    import torch
except ModuleNotFoundError as error:  # pragma: no cover - no-Torch boundary
    if error.name == "torch":
        raise ModuleNotFoundError(
            "heterodiff.models.reference_pipeline requires the optional "
            "PyTorch dependency; install the 'reference' extra"
        ) from error
    raise

from .reference_config import FixedGridReferenceConfig
from .reference_diffusion import FixedGridDiffusionBundle
from .reference_training import FixedGridTrainingBatch, FixedGridTrainingConfig


_SUPPORTED_INTEGER_DTYPES = frozenset(
    (torch.uint8, torch.int8, torch.int16, torch.int32, torch.int64)
)
_MAX_CORRUPTED_BATCH_BYTES = 512 * 1024 * 1024
_MAX_CATEGORICAL_PROBABILITY_WORK = 100_000_000
_MAX_CATEGORICAL_TEMPORARY_BYTES = 512 * 1024 * 1024
# One categorical ``q_sample`` is evaluated at a time.  Its current dense path
# can have three site-by-state, eight-byte tables live together: the advanced-
# indexing result plus its clone; probabilities plus one-hot padding and the
# ``where`` result; or probabilities plus the boolean-indexed active table.
# Reserve a fourth table for ``multinomial`` workspace and allocator overlap.
# This multiplier must be re-audited if that implementation stops using dense
# float64 tables or adds another simultaneously live site-by-state table.
_CATEGORICAL_TEMPORARY_TABLE_COPIES = 4


def _dense_cpu_tensor(value: object, *, name: str) -> torch.Tensor:
    if type(value) is not torch.Tensor:
        raise TypeError("{} must be a torch.Tensor".format(name))
    if value.device.type != "cpu":
        raise ValueError("{} must be on CPU".format(name))
    if value.layout != torch.strided or value.is_quantized or value.is_complex():
        raise TypeError(
            "{} must be a dense, non-quantized, non-complex tensor".format(name)
        )
    return value


def _integer_tensor(value: object, *, name: str) -> torch.Tensor:
    result = _dense_cpu_tensor(value, name=name)
    if result.dtype not in _SUPPORTED_INTEGER_DTYPES:
        raise TypeError("{} must have a supported integer dtype".format(name))
    return result


def _float32_tensor(value: object, *, name: str) -> torch.Tensor:
    result = _dense_cpu_tensor(value, name=name)
    if result.dtype != torch.float32:
        raise TypeError("{} must use float32".format(name))
    return result


def _boolean_tensor(value: object, *, name: str) -> torch.Tensor:
    result = _dense_cpu_tensor(value, name=name)
    if result.dtype != torch.bool:
        raise TypeError("{} must have boolean dtype".format(name))
    return result


def _shape(value: torch.Tensor, expected: tuple, *, name: str) -> None:
    if tuple(value.shape) != expected:
        raise ValueError(
            "{} has shape {}; expected {}".format(name, tuple(value.shape), expected)
        )


def _local_cpu_generator(value: object) -> torch.Generator:
    if not isinstance(value, torch.Generator):
        raise TypeError("generator must be a torch.Generator")
    if str(value.device) != "cpu":
        raise ValueError("generator must be a CPU generator")
    if value is torch.default_generator:
        raise ValueError(
            "generator must be a caller-created local generator, not Torch's "
            "global default generator"
        )
    return value


def _diffusion_step(value: object, maximum: int) -> int:
    if isinstance(value, bool) or not isinstance(value, Integral):
        raise TypeError("diffusion_step must be an integer")
    result = int(value)
    if result < 1 or result > maximum:
        raise ValueError(
            "diffusion_step must lie in [1, {}] for a corrupted training batch"
            .format(maximum)
        )
    return result


def _validate_model_resources(
    config: FixedGridReferenceConfig, *, training_batch: int, positions: int
) -> None:
    if positions > config.max_sequence_length:
        raise ValueError("clean grid exceeds model max_sequence_length")
    if training_batch * positions > config.max_batch_tokens:
        raise ValueError("training slice exceeds model max_batch_tokens")
    if (
        config.backbone == "transformer"
        and training_batch
        * config.num_attention_heads
        * positions
        * positions
        > config.max_attention_elements
    ):
        raise ValueError("training slice exceeds model max_attention_elements")


def build_corrupted_fixed_grid_training_batch(
    bundle: FixedGridDiffusionBundle,
    model_config: FixedGridReferenceConfig,
    training_config: FixedGridTrainingConfig,
    *,
    clean_discrete_state: torch.Tensor,
    clean_continuous_state: torch.Tensor,
    elapsed_time_input: torch.Tensor,
    diffusion_step: int,
    sequence_mask: torch.Tensor,
    discrete_observed_mask: torch.Tensor,
    continuous_observed_mask: torch.Tensor,
    elapsed_time_observed_mask: torch.Tensor,
    discrete_loss_mask: torch.Tensor,
    continuous_loss_mask: torch.Tensor,
    generator: torch.Generator,
) -> FixedGridTrainingBatch:
    """Corrupt one explicit diffusion step and build a trainer-ready pool.

    ``diffusion_step`` is a single caller-selected numerical corruption index
    shared by every row and modality.  ``elapsed_time_input`` remains physical
    inter-position duration and is copied unchanged.  All observation and loss
    masks are caller supplied; this function does not infer task semantics.

    The successful call advances only ``generator``.  Validation failures do
    not advance it, and an unexpected sampling failure transactionally restores
    it.  Process-global CPU Torch RNG state is a checked postcondition.
    """

    if not isinstance(bundle, FixedGridDiffusionBundle):
        raise TypeError("bundle must be a FixedGridDiffusionBundle")
    if not isinstance(model_config, FixedGridReferenceConfig):
        raise TypeError("model_config must be a FixedGridReferenceConfig")
    if not isinstance(training_config, FixedGridTrainingConfig):
        raise TypeError("training_config must be a FixedGridTrainingConfig")
    active_generator = _local_cpu_generator(generator)
    step = _diffusion_step(diffusion_step, bundle.num_diffusion_steps)
    bundle.validate_model_config(model_config, require_exact_terminal=False)

    clean_discrete = _integer_tensor(
        clean_discrete_state, name="clean_discrete_state"
    )
    if clean_discrete.dtype != torch.int64:
        raise TypeError("clean_discrete_state must use int64")
    if clean_discrete.ndim != 3:
        raise ValueError(
            "clean_discrete_state must have shape [samples, positions, fields]"
        )
    batch, positions, fields = clean_discrete.shape
    if batch == 0 or positions == 0:
        raise ValueError("clean fixed-grid pool must be non-empty")
    if fields != model_config.num_categorical_fields:
        raise ValueError("clean categorical field count does not match model")
    if batch != training_config.dataset_size:
        raise ValueError("clean pool size does not match training_config.dataset_size")
    _validate_model_resources(
        model_config,
        training_batch=training_config.batch_size,
        positions=positions,
    )

    # The model sees only one training slice at a time, but this helper builds
    # and retains the complete corrupted pool.  Bound that distinct allocation
    # and the temporary dense categorical probability tables before the
    # shape-wide validation temporaries below, any random draw, or any output
    # copy.  Larger datasets require a future streaming corruption/data-loader
    # path rather than silently expanding this CPU smoke API.
    output_bytes_per_position = (
        18 * fields
        + 10 * model_config.num_continuous_features
        + 6
    )
    estimated_output_bytes = (
        batch * positions * output_bytes_per_position + 4 * batch
    )
    if estimated_output_bytes > _MAX_CORRUPTED_BATCH_BYTES:
        raise ValueError("corrupted training pool exceeds the output-byte guard")
    grid_sites = batch * positions
    categorical_probability_work = grid_sites * sum(
        schedule.num_states for schedule in bundle.categorical
    )
    if categorical_probability_work > _MAX_CATEGORICAL_PROBABILITY_WORK:
        raise ValueError("categorical corruption exceeds the probability-work guard")
    categorical_temporary_bytes = (
        _CATEGORICAL_TEMPORARY_TABLE_COPIES
        * 8
        * grid_sites
        * max(schedule.num_states for schedule in bundle.categorical)
    )
    if categorical_temporary_bytes > _MAX_CATEGORICAL_TEMPORARY_BYTES:
        raise ValueError(
            "categorical corruption exceeds the temporary-byte guard"
        )

    clean_continuous = _float32_tensor(
        clean_continuous_state, name="clean_continuous_state"
    )
    elapsed_time = _float32_tensor(
        elapsed_time_input, name="elapsed_time_input"
    )
    sequence = _boolean_tensor(sequence_mask, name="sequence_mask")
    discrete_observed = _boolean_tensor(
        discrete_observed_mask, name="discrete_observed_mask"
    )
    continuous_observed = _boolean_tensor(
        continuous_observed_mask, name="continuous_observed_mask"
    )
    time_observed = _boolean_tensor(
        elapsed_time_observed_mask, name="elapsed_time_observed_mask"
    )
    discrete_loss = _boolean_tensor(
        discrete_loss_mask, name="discrete_loss_mask"
    )
    continuous_loss = _boolean_tensor(
        continuous_loss_mask, name="continuous_loss_mask"
    )

    continuous_shape = (
        batch,
        positions,
        model_config.num_continuous_features,
    )
    discrete_shape = (batch, positions, fields)
    _shape(clean_continuous, continuous_shape, name="clean_continuous_state")
    _shape(elapsed_time, (batch, positions), name="elapsed_time_input")
    _shape(sequence, (batch, positions), name="sequence_mask")
    _shape(discrete_observed, discrete_shape, name="discrete_observed_mask")
    _shape(
        continuous_observed,
        continuous_shape,
        name="continuous_observed_mask",
    )
    _shape(time_observed, (batch, positions), name="elapsed_time_observed_mask")
    _shape(discrete_loss, discrete_shape, name="discrete_loss_mask")
    _shape(continuous_loss, continuous_shape, name="continuous_loss_mask")

    if bool(torch.any(~torch.any(sequence, dim=1)).item()):
        raise ValueError("every clean fixed-grid row must contain a valid position")
    if positions > 1 and bool(
        torch.any((~sequence[:, :-1]) & sequence[:, 1:]).item()
    ):
        raise ValueError("sequence_mask must be a left-aligned prefix mask")
    sequence_discrete = sequence.unsqueeze(-1).expand_as(clean_discrete)
    sequence_continuous = sequence.unsqueeze(-1).expand_as(clean_continuous)
    if bool(torch.any(discrete_observed & ~sequence_discrete).item()):
        raise ValueError("discrete_observed_mask exposes padding")
    if bool(torch.any(continuous_observed & ~sequence_continuous).item()):
        raise ValueError("continuous_observed_mask exposes padding")
    if bool(torch.any(time_observed & ~sequence).item()):
        raise ValueError("elapsed_time_observed_mask exposes padding")
    if bool(torch.any(discrete_loss & ~sequence_discrete).item()):
        raise ValueError("discrete_loss_mask includes padding")
    if bool(torch.any(continuous_loss & ~sequence_continuous).item()):
        raise ValueError("continuous_loss_mask includes padding")

    for field, cardinality in enumerate(
        model_config.categorical_output_cardinalities
    ):
        active = clean_discrete[:, :, field][sequence]
        if bool(torch.any((active < 0) | (active >= cardinality)).item()):
            raise ValueError(
                "clean_discrete_state field {} lies outside clean x0 support"
                .format(field)
            )
    if bool(torch.any(clean_discrete[~sequence_discrete] != 0).item()):
        raise ValueError("clean_discrete_state padding must be canonical zero")
    if bool(torch.any(~torch.isfinite(clean_continuous[sequence_continuous])).item()):
        raise ValueError("clean_continuous_state must be finite at valid positions")
    if bool(torch.any(clean_continuous[~sequence_continuous] != 0.0).item()):
        raise ValueError("clean_continuous_state padding must be canonical zero")
    if bool(torch.any(~torch.isfinite(elapsed_time[sequence])).item()):
        raise ValueError("elapsed_time_input must be finite at valid positions")
    if bool(torch.any(elapsed_time[sequence] < 0.0).item()):
        raise ValueError("elapsed_time_input must be nonnegative at valid positions")
    if bool(torch.any(elapsed_time[~sequence] != 0.0).item()):
        raise ValueError("elapsed_time_input padding must be canonical zero")

    local_before = active_generator.get_state().clone()
    global_before = torch.get_rng_state().clone()
    try:
        noisy_fields = []
        for field, schedule in enumerate(bundle.categorical):
            noisy_fields.append(
                schedule.q_sample(
                    clean_discrete[:, :, field],
                    step,
                    generator=active_generator,
                    valid_mask=sequence,
                )
            )
        discrete_noisy = torch.stack(noisy_fields, dim=-1)
        gaussian = bundle.continuous.q_sample(
            clean_continuous,
            step,
            generator=active_generator,
            valid_mask=sequence,
        )
        progress_value = float(bundle.diffusion_progress[step].item())
        progress = torch.full((batch,), progress_value, dtype=torch.float32)
        result = FixedGridTrainingBatch(
            discrete_noisy_state=discrete_noisy.contiguous(),
            continuous_noisy_state=gaussian.noisy.contiguous(),
            elapsed_time_input=elapsed_time.clone().contiguous(),
            diffusion_progress=progress,
            sequence_mask=sequence.clone().contiguous(),
            discrete_observed_mask=discrete_observed.clone().contiguous(),
            continuous_observed_mask=continuous_observed.clone().contiguous(),
            elapsed_time_observed_mask=time_observed.clone().contiguous(),
            discrete_target=clean_discrete.clone().contiguous(),
            continuous_target=gaussian.epsilon.contiguous(),
            discrete_loss_mask=discrete_loss.clone().contiguous(),
            continuous_loss_mask=continuous_loss.clone().contiguous(),
        )
    except Exception:
        active_generator.set_state(local_before)
        if not torch.equal(torch.get_rng_state(), global_before):
            torch.set_rng_state(global_before)
        raise

    if not torch.equal(torch.get_rng_state(), global_before):
        active_generator.set_state(local_before)
        torch.set_rng_state(global_before)
        raise RuntimeError("forward corruption changed process-global Torch RNG state")
    return result


__all__ = ["build_corrupted_fixed_grid_training_batch"]
