# Explicit-device factorized neural graphs

Date: 2026-09-08. Additive local implementation only. The existing CPU energy,
observation encoder, nuisance, source identities, and historical runtime
evidence are untouched. No CUDA execution or speedup is claimed here.

## Interfaces and preservation

`src/heterodiff/models/factorized_device_energy_torch.py` provides:

- `DeviceFactorizedEnergy.from_cpu(cpu_model, device)`;
- `DeviceFactorizedObservationEncoder.from_cpu(cpu_encoder, device)`;
- `DeviceFactorizedObservationNuisance.from_cpu(cpu_nuisance, device)`;
- `device_configuration_batch(states, reverse_times, contexts, architecture,
  device=..., coordinates=..., coordinate_gradients=...)`.

Each wrapper copies the original parameter values, names, state-dictionary
keys, gradient flags, and training/evaluation mode into independent storage.
Copying does not initialize random weights or alter global RNG state. The
energy retains its unchanged architecture identity and 96,705 parameters;
the observation encoder and independent nuisance retain 51,200 and 53,313.

Accepted devices are CPU or CUDA; bare `cuda` is normalized explicitly to
`cuda:0`, not the ambient current CUDA device. The qualification harness may
require the stricter indexed spelling. Other device families are refused.
All tensor creation specifies a device, and transferred coordinates/context
retain their autograd connection. New requested coordinate-gradient rows are
FP32 leaves on the target device; zero-dimensional atoms remain empty rows.

## Graph and host/device boundary

Exact event and context bytes remain CPU metadata. The unchanged recurrent
byte graph consumes every byte on the selected device; no vocabulary,
hash-index substitution, truncation, or discrete-coordinate rounding occurs.
There is no device scalar read inside the per-byte recurrence.

Energy pooling retains the CPU graph's canonical metadata/FP32-coordinate
ordering. It performs one batched detached coordinate transfer to CPU for
sorting, instead of a separate scalar transfer per event. This does not
detach the coordinates used by the differentiable graph. Observation
pooling retains the original exact host-event ordering and keeps ordinary
empty observations, overflow, and static context distinct.

This is deliberately a parity-first implementation, not a fused GPU kernel:
the recurrence still launches serial per-byte operations and graph validation
requires bounded synchronization. No throughput improvement, completely
GPU-resident sampler, asynchronous pipeline, or end-to-end acceleration is
inferred from CUDA-capable tensor placement. Analytic float64 guide/risk and
CPU sampling/metric boundaries belong to the separate device trainer.

## Local verification

The focused wrapper suite passes **27 CPU-only tests**. It checks unchanged
names/weights and independent storage, no global RNG mutation, exact CPU
forward values, coordinate first/second derivatives, context/parameter
gradients, an actual AdamW step and moments, repeated-event pooling, full
metadata/context bytes, zero-dimensional fibers, overflow, explicit allocation
under an ambient meta-device context, malformed inputs, and finite/resource
refusals. The CUDA-name test parses a device string only; it does not access
hardware or count as a CUDA test.

Any later CUDA qualification must independently report device/runtime facts,
numerical tolerances, actual timings, and failures. These wrappers alone do
not adopt scientific numerical settings, amend the frozen production budget,
authorize paid jobs, or complete model/scientific execution.
