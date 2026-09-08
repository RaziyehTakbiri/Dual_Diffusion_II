# Factorized local pipeline qualification

Status: **implemented and tested local CPU scientific-amendment prototype; not production or real-data qualification.** Recorded 2026-09-08.

The factorized metadata/continuous-fiber reference, amended target and observation law now have an executable connection through real BASE learning, independent joint/product trajectories, conditional classifier learning, conditional initialization, learned hybrid sampling, and the unchanged F105 metric. This is no longer a frozen random BASE or a two-state-only sampling fixture. The tests remain deliberately small and use invented records only.

## Actual BASE objective

`src/heterodiff/experiments/factorized_base_training.py` implements the relative-Gaussian score and jump-flux objective in executable-method specification §4.2. The older `models/reference_training.py` fixed-grid denoiser trainer is not substituted for this objective and is unchanged.

For a corrupted configuration with scalar continuous coordinates `r_i`, potential `V`, and a reference-proposal edit `y -> y'`, the implemented population integrands are:

```text
L_C = gamma_C(s) * sum_i [0.5*(d_i V)^2 + d_ii V - r_i*d_i V]
L_J = gamma_J(s) * Lambda_0(y) * [exp(V(y')-V(y)) + V(y')-V(y)]
L   = E[L_C] + lambda_J * E[L_J]
```

Here the edit is sampled from the normalized unscaled reference proposal `q_0/Lambda_0`; the full exit rate and process jump schedule multiply the result exactly once. The linear jump term has a **positive** sign. The proposal weights are not normalized again within the loss. `lambda_J` is an explicit positive caller input, not inferred from a result.

Each training example starts from the amended TRAIN-target sampler and is corrupted by the exact-form OU plus complete capped birth/death reference construction. Physical forward time is sampled uniformly strictly inside the active interval. This estimates an expectation under that declared time law, without an additional inverse-density multiplier. Binary64/FP32 endpoint or resource failures stop rather than silently redraw or clip.

Only actual one-dimensional fibers receive coordinate derivatives. Zero-dimensional metadata atoms, including GCS/MechVent atomic values, never receive padded coordinates or Hessian terms. The scalar diagonal Hessian is computed with autograd, not a stochastic trace estimator. The implementation makes CPU placement explicit even under an ambient non-CPU default; FP32 derivatives and parameters are combined into FP64 objective terms. Its bounded neural class is not claimed to contain the exact population minimizer.

## End-to-end tests

The independent `tests/unit/test_factorized_conditional_pipeline.py` uses both PhysioNet and Retail structural record types and both G+R and DIR. Each domain performs three real BASE AdamW updates; each method then performs three real conditional AdamW updates with the trained BASE frozen. These are not the 4096-update cadence, a tuning run, or a learned-quality experiment.

| Boundary | Evidence exercised locally |
| --- | --- |
| Actual learning | Finite objective/backward/AdamW updates change BASE and conditional parameters; conditional updates leave the supplied BASE unchanged. |
| Classifier law | Two purpose-separated BASE trajectories share only the declared task, static context, and sampled reverse time. The latent comes from the first trajectory; joint and product observations come from the first and second terminal states respectively. |
| Full-interval time | Conditional steps draw strict interior reverse times over the whole interval. Each queried time is explicitly inserted into the numerical grid, and extra work/query refinement is reported. Fixed-time debug kernels remain separately identified. |
| Physical scalar | The same BASE plus guide plus once-gated residual drives coordinate gradients and birth/death likelihood ratios. The nuisance affects logits but cannot affect the physical potential, its gradient, or initialization. |
| Initialization | Both retained observations and overflow use the guide reference posterior plus bounded residual rejection; changing BASE does not change this initializer tilt. No BASE-energy or nuisance tilt is inserted into the initial reference law. |
| Hybrid paths | Complete birth/death activity and scalar continuous motion are exercised, including the zero-potential reference limit. Reference-order permutation preserves replayed paths. No silent cap clipping or one-jump replacement is used. |
| Clean hold | Held intervals preserve the same state object and consume no model calls or new random-stream requests; the BASE physical adapter extends its potential constantly across the hold. |
| Numerical check | A coupled 128-path OU known-law fixture compares step sizes `h` and `h/2` with common Brownian increments; the smaller-step RMS error is strictly lower and below 0.8 times the coarse error for the fixed test stream. This is not a general learned-model convergence proof. |
| Legal metric conversion | Generated exact metadata survives the semantic/F105 conversion. Scalar log/exp round-trip and binary64 conversion errors are explicitly checked finite; atomic round trips are exact. |
| Raw-truth metric seam | Two independently keyed generated conditional configurations are evaluated with the unchanged F105 configuration kernel and formal conditional CKS estimator against separate untouched raw decimal synthetic truth. This is a two-draw seam, not the 128-group ×64-draw production checkpoint contract. |

The raw synthetic truth used for that metric check is created directly through the existing decimal-token constructors. It is never passed through the target lift, forward corruption, or a rounding/projecting decoder. Generated scalar values remain the declared numerical log/exp output. No decoder silently repairs a discrete field, clinically filters GCS/MechVent, rounds a calendar/integer, or forces an arbitrary 112/10-vector into an F105 event.

## Recorded execution

Local environment: Python **3.11.5**, PyTorch **2.12.1**, CPU execution; CUDA unavailable. This is not the Databricks Python3.12 environment and does not replace its immutable installed-runtime receipt.

The combined owned qualification run completed:

```text
tests/unit/test_factorized_base_training.py
tests/unit/test_factorized_conditional_pipeline.py
25 passed in 6.29s
```

The 25 comprise eight focused BASE tests and seventeen independent pipeline tests. Static undefined/unused-name checks passed for the BASE module and both test files. The parent task records any broader regression separately; this note does not add historical test counts to this run.

## Remaining limits

- The metadata reference, TRAIN-key mixture, scalar target lift and positive observation law are the structurally adopted scientific amendment; its numeric production instance is not yet frozen. They do not preserve the old real-domain half-thinning identity observation law by assertion, nor alter any old frozen source or release binding.
- A finite-RNG numerical implementation is not the ideal full-support law. Entropy, event-count, metadata-byte, representation, thinning and initialization resource failures remain explicit failures, not successful conditioned samples.
- Uniform-query refinement creates a declared query-dependent numerical path family. It is not advertised as unchanged fixed-grid semantics, exact continuous-time learned dynamics, or a cost-free dense-output method.
- Exact metadata grammar and F105 structural conversion do not prove clinical validity, original raw decimal/binary64-origin eligibility, data admission, or scientific suitability of the amended priors and observation law.
- The caller-supplied TRAIN roster and context have not been authenticated against real splits. No study/test data, external downloads, paid jobs, GPU execution or production scientific run occurred.
- The tests establish executable equations and interfaces on small supplied configurations. They do not establish learned predictive quality, calibration, full production cadence, population convergence, certified full checkpoint validation, or project/blocker closure.

Next, specify the numerical sensitivity instance and larger-workload bounds, then prepare the explicit device-local successor and bounded CPU/GPU parity qualification. The structural model choice is already adopted, not awaiting another user decision. Real-data admission, the full workload/checkpoint contract and paid execution remain separate open steps; this local qualification does not grant that authority.
