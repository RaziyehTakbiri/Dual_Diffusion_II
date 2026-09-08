# Mixed-key conditional learner: bounded local implementation

Date: 2026-09-08.

Status: **local CPU implementation and synthetic qualification; not scientific
training, a production certificate, or GPU qualification**. This additive code
implements the selected mixed-domain structural direction without changing any
old finite-type certificate, CPU-release file, numeric freeze or budget ceiling.

## Actual connections

`src/heterodiff/experiments/factorized_conditional_training.py` supplies:

- `FactorizedObservation(observed, domain_id, task_id, context_bytes)`: retained
  exact-key configurations, retained-empty and collapsed overflow (`None`) are
  distinct. Task/static-context bytes are explicit immutable inputs.
- A trainable shared-byte observation encoder to64 context channels. It consumes
  every canonical metadata/context byte and every retained occurrence, including
  duplicates, with separate0D activity and1D log-coordinate inputs. It pools in
  canonical order with1/(1+n); this is a learned representation, **not F105**.
  Compression is not asserted injective. Resource excess refuses without
  truncation, vocabulary substitution or retry.
- An independent observation-only encoder and64→32→1 nuisance. Its public input
  contains no latent state or time. Both encoders receive only immutable visible
  values; gradients train their parameters, not the observation data.
- `FactorizedConditionalModel` connects the real analytic association guide,
  the bounded shared-key conditioner and nuisance. G+R uses the propagated
  reference guide; DIR uses the terminal likelihood. Baselines remain CPU FP64
  and are not narrowed to FP32 or accepted as arbitrary supplied float arrays.

The sole residual gate is, for direct time s=S−u,

    gate(s) = [max(s−s_hold,0)/(S−s_hold)]³.

The paired risk is

    ½ mean(w_joint softplus(−logit_joint))
      + ½ mean(w_product softplus(logit_product)).

Each pair must share its first latent configuration, reverse time, exact
domain/task/static-context identity and declared sampling-law ID. Exact
class-conditional rational RN weights are retained, rounded to FP64 for the risk,
and never self-normalized. Unit factors are required for the declared-law route.
The API does not authenticate that supplied pairs actually came from independent
base trajectories or that a caller's context has the claimed semantics; the
sampler/population integration and real-data admission remain separate duties.

## Physical potential and initializer

`FactorizedPhysicalPotential` deep-copies the base and conditional modules,
switches them to evaluation mode and freezes their learned parameters. It
requires an explicit64D base context. The base-context mapping and supplied
remaining-clock callback are declared integration inputs, not authenticated
data laws. External edits to the original modules do not change the snapshot.

The physical potential is V+log(h)+gated residual for G+R and
V+log(g)+gated residual for DIR. Nuisance is never evaluated on this path.
The uniform upper bound is the base bound plus the analytic log-guide bound
plus the conditioner bound. `value_grad` returns aligned empty/one-element
coordinate-gradient rows; metadata remain discrete.

The adapter explicitly extends BASE through the clean hold by querying its
direct time at max(S−u,s_hold). This is an adapter-owned extension, not a
backbone certificate. The sampler's separately declared zero-clock intervals
must also hold the state fixed. The conditional gate uses the original time
and is exactly zero through the hold.

For initialization **after sampling the analytic reference-guide posterior**,
`initialization_residual_log_tilt(state)` supplies only the bounded residual
at u=0, with `initialization_residual_upper_bound`. It excludes BASE and nuisance
and does not charge the analytic guide twice. The separate
`initialization_log_tilt(u,state)` returns log-guide plus residual for auditing
the complete tilt, not the rejection factor for that already-guided proposal.

The learned energy uses CPU FP32 while guide, total scalar and logistic risk
use CPU FP64. Coordinate tensors retain autograd through the explicit cast;
overflow is refused. These are local numeric-graph derivatives, including
second-coordinate derivatives for the BASE objective helper, not transferred
old certified derivatives or global interval/path bounds.

## Exact architecture counts and bounded work accounting

| Component | Unique parameters |
|---|---:|
| Shared mixed-key conditioner energy |96,705|
| Visible encoder: byte recurrence +34→128→128 +162→128→64 |51,200|
| Independent nuisance encoder plus64→32→1 head |53,313|
| Conditional trainable total |201,218|
| Separate frozen BASE energy |96,705|
| BASE plus complete conditional model |297,923|

The internal energy context MLP is already included, not charged twice. These
are proposed implementation counts only; old F064/F065/F070/F071 values retain
their historical predecessor scope and no full-method successor is frozen here.

For one class of n examples the implementation executes n analytic guide calls,
one batched conditioner forward, two independent batched observation-encoder
forwards and n nuisance heads. A paired loss requires two such class forwards.
Each observation encoder executes one32-state recurrence per metadata/context
byte; the exposed workload reports exact affine MAC terms separately. Matching
complexity, activations, sorting/pooling, autodiff, optimizer, generated training
population and hardware measurements are not disguised as those MAC counts.
No F104 weights or ceilings are invented or lifted.

## Qualification boundary

Focused tests cover real guide-based paired risk and one AdamW update for both
methods, finite gradients to all three learned branches, same-graph physical
values/coordinate gradients, genuine0D rows, second-coordinate derivatives,
single cubic gate, clean-hold BASE constancy, snapshot isolation, nuisance
exclusion, residual-only initializer, exact parameter counts, visible
permutation/duplicate handling, complete-byte consumption and explicit numeric,
law, context, resource and time refusals. These are tiny invented CPU examples.

The focused learner suite contains25 passing cases. The joint learner, shared
energy and analytic-guide suite passes127 cases; no tests use admitted data or
paid/GPU execution. Static lint is clean. Independent sampler/pipeline tests
are additional evidence and are not included in that count.

The broader sampler/loss/F105 bridge, selected scientific numeric settings,
scalable countable-fiber numeric qualification, empirical data/splits/support,
GPU execution and all real outcomes require their separate evidence. Nothing
in this record authorizes a paid job, data acquisition or scientific run.
