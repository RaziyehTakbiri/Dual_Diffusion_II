# Residual likelihood/score diagnosis: fixed local protocol

Declared 2026-09-13, after the completed 22-route outcome and before the
diagnostic fit replays. This is an explanatory, post-outcome diagnosis, not a
new confirmatory test or a change to the scientific objective.

## Fixed work

Reconstruct all twelve existing fits: the same two joint scenarios, three seeds
1201/1202/1203 and two methods. Use the original 32 updates, two joint/product
pairs per update, optimizer, initialization, observation channel, common grid,
32 held-out pairs and checkpoints 0/8/16/32. Verify the original initial/final
parameter digests, population identity, every update record and every held-out
loss. Failure to match stops interpretation as an original-fit diagnosis.
No conditional endpoint draws, model selection, new hyperparameters, retries,
GPU work, remote jobs, real data or package downloads.

At each checkpoint query every original macro node 0,1/8,...,1. At each node
query EMPTY, the atomic OTHER key (3,HR,ZERO), the selected continuous key
(3,HR,POSITIVE), and another continuous OTHER key (4,HR,POSITIVE). Both
continuous keys use coordinates -3,-1.5,0,1.5,3. These 108 rows per checkpoint
are fixed, unweighted probes, not posterior-weighted risk estimates. There are
48 checkpoint inspections and 5,184 query rows in total. Midpoint stages are
not silently identified with macro-node conditional laws.

Compare learned physical log-potentials after subtracting their EMPTY value,
latent-coordinate scores and Hessians against (a) the independent continuous
capped-reference likelihood and (b) an independent analytic likelihood for the
zero-BASE numerical grid kernel. Retain the zero-residual baseline and actual
randomly initialized network separately. Also report raw classifier errors with
the correct observation evidence and RN convention, and observation-only
nuisance movement. Report finite-query maxima/RMS, not a global norm or a
sampling-law error bound. Do not select checkpoints by these measurements.

At each time, compare the diameter of the target-minus-baseline correction on
the fixed query roster with twice the available gated residual amplitude.
Positive excess proves a finite-query representation obstruction; it does not
give an endpoint-distribution error or a derivative bound.

The exact existing population sampler is delegated without additional RNG calls
to record observation/time coverage of its existing training and validation
pairs. Selected-observation proximity means the fixed interval y +/- 0.5 (one
declared observation-noise standard deviation), not a retrospectively selected
band. The observation tally is descriptive; it is not an admission or support
audit of real data.

## Bounds and reporting

One CPU process, one intra-op thread, deterministic algorithms, a 1,200-second
parent-enforced deadline. New diagnostic work includes 384 replayed optimizer
updates and the original 2,304 training/validation BASE paths; these are not
zero-cost checkpoint reads. Save each completed diagnostic route separately
and a final combined report only after all twelve exact replays match. Preserve
all older results and partial runs. The output directory must be new. CPU
kernel/RNG finite-precision effects and resource-refusal conditioning are not
made exact by the analytic numerical-kernel oracle.

No model fix is authorized by this diagnostic protocol. A capacity or
regularization amendment, if indicated, is a separately reviewed next step.
