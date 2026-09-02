# Manuscript v3 Working Package

**Status:** scientifically result-pending method skeleton; one bounded
nonconfirmatory engineering diagnostic completed  
**Created:** 2026-08-03  
**Target quality:** ICML/ICLR/NeurIPS; venue template intentionally deferred  
**Authoritative strategy:**
`research/85_general_framework_manuscript_revision_blueprint.md`

## Files

- `manuscript_v3.md` — venue-neutral manuscript prose and equations.
- `manuscript_v3.tex` — compile-verified, venue-neutral LaTeX counterpart of
  the cohesive manuscript, with all equations, algorithms, tables, status
  markers, companion-file references, appendix roadmap, and source inventory.
- `../output/pdf/manuscript_v3_venue_neutral.pdf` — rendered validation copy of
  `manuscript_v3.tex`; this is a working manuscript artifact, not a
  venue-formatted submission.
- `executable_method_spec.md` — internally cross-audited mathematical candidate
  for the capped reference, reverse objective, normalized association law,
  analytic preconditioner, initializer, and sampler; implementation is partial.
- `executable_method_audit.md` — internal algebra/implementability audit,
  dispositions, unresolved blockers, and post-implementation re-audit rule.
- `configuration_reference_code_audit.md` — equation-to-code audit of the
  first general implementation layer, including numerical and test boundaries.
- `reversible_hybrid_reference_code_audit.md` — equation-to-code audit of the
  second implementation layer: reversible forward corruption and exact
  event-driven simulation for the declared piecewise process.
- `reverse_energy_objective_code_audit.md` — equation-to-code audit of the
  third implementation layer: NumPy reference-relative reverse targets,
  continuous and jump population-objective oracles, structured importance
  arithmetic, and their explicit evidence limits.
- `association_observation_code_audit.md` — equation-to-code audit of the
  fourth implementation layer: the bound normalized unordered observation
  row, exact association/orbit oracles, overflow, positive mixing, and source
  gradients.
- `association_preconditioner_code_audit.md` — equation-to-code audit of the
  fifth implementation layer: analytic reverse-to-terminal propagation, the
  literal capped restriction, exact blocked-birth defect, guide derivatives,
  edit ratios, and unnormalized proposal diagnostics.
- `configuration_energy_code_audit.md` — equation-to-code audit of the sixth
  implementation layer: bounded typed DeepSets energy, global snapshot
  certificate, exact/Hutchinson derivatives, objectives, output gauges, and
  certificate-checked supplied-rate operational guards.
- `plugin_bridge_sampler_code_audit.md` — equation-to-code audit of the
  seventh implementation layer: the process-owned normalized reference-edit
  composer and its certified base-energy candidate projection. This is not a
  reverse path sampler.
- `mixed_hybrid_oracle_code_audit.md` — equation-to-code audit of the eighth
  implementation layer: a scoped cap-one, two-type mixed CTMC--OU forward
  known law and backward-information/Doob oracle, with a separate cap-two
  multiplicity companion. This is not a general conditional path sampler.
- `mixed_hybrid_conditional_sampler_code_audit.md` — equation-to-code and
  path-law audit of the ninth implementation layer: a finite-resolution-
  checked exact compact conditional-path sampler obtained by right-endpoint
  sampling, exact forward-reference simulation, and deterministic time
  reversal. It is restricted to the eighth layer's known-law scope and is not
  the general learned plug-in sampler.
- `plugin_bridge_intensity_code_audit.md` — equation-to-code audit of the
  tenth implementation checkpoint: a sealed deterministic no-RNG query of the
  state-dependent reference candidate intensity, exact clean-hold versus
  active structural-zero records, route-resolution preflight, and candidate
  sampling from the revalidated record. It is not the controlled envelope,
  waiting/acceptance RNG, or a path sampler.
- `analytic_guide_range_certificate_code_audit.md` — equation-to-code audit of
  the eleventh implementation checkpoint: a sealed, fixed-observation global
  range, edit-oscillation, and coordinate-regularity certificate for the
  real-arithmetic conjugate guide under normalized probability-simplex and
  Markov-kernel semantics. It is not a floating-point evaluator-error
  enclosure or operational sampler admission.
- `range_gated_guide_code_audit.md` — equation-to-code audit of the twelfth
  implementation checkpoint: a sealed, fixed-observation, successful-only
  bridge that preserves exact finite raw binary64 log-guide values inside the
  directed model interval, certifies a coarse range-derived discrepancy and
  direct represented edit envelope, and refuses every other result. It is not
  a small forward-error analysis, liveness theorem, derivative certificate,
  controlled clock, or sampler admission.
- `configuration_residual_code_audit.md` — equation-to-code audit of the
  thirteenth implementation checkpoint: a distinct domain-neutral
  boundary-gated conditional residual with residual-specific
  schema/provenance custody, active-row-only neural evaluation, global
  value/state-pair and physical-coordinate derivative bounds, and exact
  clean-hold zeros. Its finite-vector conditioner is procedurally bound but
  not runtime-authenticated; it is not a conditional trainer, combined
  potential, controlled clock, or sampler admission.
- `configuration_potential_composer_code_audit.md` — equation-to-code audit of
  the fourteenth implementation checkpoint: successful-only, provenance-bound
  log-space composition of the certified base edge, represented guide edit,
  and certified residual edge for one already sampled process-valid
  candidate. It supplies an exact-rational one-round represented sum and
  separate time-specific mathematical/operational aggregate log witnesses;
  it is not a rate-space envelope, total exit, waiting/acceptance decision,
  drift certificate, path, or sampler admission.
- `totalized_jump_guide_code_audit.md` — equation-to-code audit of the
  fifteenth implementation checkpoint: a fixed-observation, factory-
  preflighted operational-surrogate jump guide that preserves successful raw
  values and maps only typed numerical/range point failures to one certified
  midpoint. It stores runtime-specific streaming-digest records and exact-
  rational endpoint coboundaries with \(W_m\), fallback-specific, and
  \(2W_m\) witnesses; it is not the analytic target, a derivative/drift
  certificate, rate envelope, clock, RNG, path, or sampler admission.
- `totalized_residual_jump_code_audit.md` — equation-to-code audit of the
  sixteenth implementation checkpoint: a detached, checkpoint-private,
  jump-only conditional residual that preserves checkpoint-thirteen successes
  bitwise and maps only its exact typed active tiny-cubic-gate refusal to an
  exact-rational gate times the represented bounded core, rounded once. It is
  not an exact real neural residual or conditional/posterior target, derivative
  or drift certificate, rate envelope, clock, RNG, path, or sampler admission.
- `totalized_jump_potential_composer_code_audit.md` — equation-to-code audit
  of the seventeenth implementation checkpoint: a target-explicit operational-
  surrogate composer that combines the checkpoint-private base, fixed-
  observation totalized guide, and totalized residual on one active process-
  valid birth, death, or replacement candidate. It composes exact rational
  represented endpoint differences and rounds the aggregate once; it does not
  exponentiate, construct a rate envelope or total exit, draw clock/RNG
  decisions, certify drift, initialize or construct a path, or admit a sampler.
- `totalized_jump_rate_envelope_code_audit.md` — equation-to-code audit of the
  eighteenth implementation checkpoint: exact-edge adaptive Decimal
  exponentiation for checkpoint seventeen's operational target, a correctly
  rounded finite normal candidate-measure integrand on success, and no-RNG
  instantaneous/global controlled-total-exit upper bounds. It preserves
  structural zero but does not compute the active total exit, admit the route
  draw, preserve rounded detailed balance, draw waiting/acceptance randomness,
  certify drift, construct a path, or admit a sampler.
- `plugin_bridge_operational_thinning_code_audit.md` — equation-to-code audit
  of the nineteenth implementation checkpoint: one successful-return local
  operational wait/route/accept sequence for checkpoint seventeen's explicit
  surrogate under checkpoint eighteen's local envelope. It resolves an ideal
  Philox raw-word prefix with directed inverse-exponential arithmetic, returns
  only a uniquely rounded binary64 interior `proposal_time`, delegates the
  inherited finite-resolution normalized-reference route, and draws an exact
  Bernoulli for the represented rate ratio
  \(I_{64}^{\mathrm{op}}/E_{64}^{\mathrm{op}}\). It is not a repeated loop,
  counter-keyed lineage contract, continuous-route validation, path, or full
  sampler.
- `plugin_bridge_operational_thinning_loop_code_audit.md` — equation-to-code
  audit of the twentieth implementation checkpoint: bounded successful-return
  coordination of checkpoint nineteen's local operation at one fixed
  generative time. Rejections advance the represented local clock and reuse
  the exact state/intensity/envelope objects; acceptances immediately
  preflight a fresh intensity and envelope before continuation. A result is
  returned only after certified structural-zero or right-endpoint exhaustion;
  the caller's 0--64 proposal budget is a fail-closed resource cap, not a
  successful stop. It remains a sequential-Philox operational transcript, not
  an exact real-time Poisson/CTMC law, counter-keyed or lineage-aware path,
  drift/Strang step, initializer, or full sampler. Focused route evidence is
  still all-atomic; continuous-destination operational evidence is absent.
- `plugin_bridge_continuous_route_evidence_code_audit.md` — equation-to-code
  audit of the twenty-first implementation checkpoint: a successor evidence
  owner that retains reconstructable canonical Philox states around one
  checkpoint-nineteen route, replays the frozen process-owned composer on a
  fresh local generator, and requires the candidate digest and exact
  post-state to agree. Its focused fixture covers continuous birth, both
  2D-to-3D and 3D-to-2D replacements, and death without hidden resampling. It
  is same-runtime finite-resolution evidence, not an exact categorical,
  integer, or Gaussian law, Test-29 distribution recovery, liveness, a path,
  or the full sampler.
- `plugin_bridge_operational_thinning_loop_route_evidence_code_audit.md` —
  equation-to-code audit of the twenty-second implementation checkpoint: an
  additive successor around the frozen checkpoint-twenty loop that snapshots
  its complete Philox entry and exit states, reconstructs every waiting,
  route, acceptance, and terminal prefix on a fresh local stream, and binds
  one checkpoint-twenty-one route-evidence record to each completed proposal.
  It is bounded, successful-return, same-runtime procedural custody—not an
  ideal route law, unconditional completion or liveness theorem, path, or
  full sampler.
- `plugin_bridge_counter_keyed_lineage_contract_code_audit.md` — equation-to-
  code audit of the twenty-third implementation checkpoint: a direct, unhashed
  NumPy Philox address namespace and a persistent duplicate-safe lineage
  sidecar over one fully revalidated checkpoint-twenty-two result. It does not
  assert that checkpoint twenty-two consumed the issued streams, implement
  Brownian coupling or drift, construct a path, or admit the full sampler.
- `plugin_bridge_counter_keyed_operational_epoch_loop_code_audit.md` —
  equation-to-code audit of the twenty-fourth implementation checkpoint: a
  bounded successful-return loop whose active epochs use a new direct
  `operational_epoch` Philox domain, tag 6, and whose candidate epochs bind the
  checkpoint-twenty iteration, checkpoint-twenty-one route evidence, and
  checkpoint-twenty-three lineage transition. It accepts no caller RNG and is
  hardened by exact tag and parent-certificate types, canonical context and
  per-proposal digest custody, bounded pre-hash candidate/event/lineage
  resources, deep child-record validation, and event-identity projection
  checks. It is not an exact jump law, path, initializer, Brownian coupling,
  drift/Strang step, liveness theorem, or full sampler.
- `plugin_bridge_counter_keyed_initializer_stream_consumption_code_audit.md`
  — equation-to-code audit of the twenty-fifth implementation checkpoint: a
  bootstrap-only successor that consumes one bounded uninterpreted `raw64`
  prefix from each existing occurrence's direct tag-3, step-zero initializer
  receipt. It binds the exact checkpoint-twenty-four and checkpoint-twenty-
  three owners, accepts no caller RNG, and returns the exact input lineage
  state unchanged. It is prefix custody, not an initializer or output law,
  and supplies no Brownian coupling, drift, path, or full sampler.
- `plugin_bridge_counter_keyed_global_initializer_control_code_audit.md`
  — equation-to-code audit of the twenty-sixth implementation checkpoint: a
  law-neutral successor that consumes bounded uninterpreted `raw64` prefixes
  from a direct pre-cardinality tag-7 namespace with key `(run_id, 7)` and
  counter `(0, initialization_index, stage_index, attempt_index)`. It freezes
  address and replay custody, not stage/retry semantics, output transforms, an
  initializer distribution, tag-3 payload coordination, or a sampler.
- `plugin_bridge_counter_keyed_initializer_protocol_code_audit.md`
  — equation-to-code audit of the twenty-seventh implementation checkpoint:
  a fixed, nonadaptive successor that assigns disjoint tag-7 stages and
  canonical multiblock work-item coordinates to enumeration, bounded
  rejection, SIR, and a branch-free reference candidate. It allocates and
  replays prefixes but performs no transform, branch decision, resampling,
  configuration generation, or initializer law.
- `plugin_bridge_counter_keyed_reference_initializer_code_audit.md`
  — equation-to-code and law-boundary audit of the twenty-eighth
  implementation checkpoint: an ancestry-bound, fixed-word-budget, no-retry
  finite
  transformer for only checkpoint twenty-seven's reference strategy. It
  records exact binary64-induced count/type targets, positive Hamilton dyadic
  quotas and their TV errors, a complete fixed raw-slot layout, a symmetric
  top-53 midpoint normal-quantile codebook, and duplicate-stable canonical
  configuration maps. Its output law is defined only under a hypothetical
  product-uniform word source; actual Philox use is deterministic procedural
  replay, not certified randomness or an exact continuous reference law.
- [`plugin_bridge_counter_keyed_reference_initializer_diagnostic_preregistration.md`](plugin_bridge_counter_keyed_reference_initializer_diagnostic_preregistration.md)
  — sealed checkpoint-29 protocol for one fixed, no-search, no-retry
  deterministic-grid diagnostic of the checkpoint-28 reference transformer.
- `plugin_bridge_counter_keyed_reference_initializer_diagnostic_execution_audit.md`
  — post-execution audit of the sole checkpoint-29 attempt. All five exact
  discrepancies passed their frozen counterfactual product-uniform envelopes;
  the evidence is explicitly nonconfirmatory and does not certify Philox,
  \(Q_{\mathrm{fin}}\), the continuous reference, or initializer admission.
- `configuration_initial_tilt_composer_code_audit.md`
  — equation-to-code audit of the thirtieth implementation checkpoint: a
  sealed, replayable, deterministic point evaluation of the time-zero
  operational initial log factor for the selected capped-Poisson base law. It
  composes the totalized guide at reverse time zero with the totalized residual
  at direct time \(S\), excludes the learned base energy, and stops before
  exponentiation, normalization, support enumeration, selection, RNG,
  initialization, path construction, or sampler admission.
- `configuration_initial_tilt_atomic_enumerator_code_audit.md`
  — equation-to-code audit of the thirty-first implementation checkpoint: a
  sealed, replayable enumeration of the complete bounded all-atomic support
  for the selected represented-parameter capped-Poisson base. It records exact
  multiplicity-corrected unnormalized base coefficients and their completeness
  normalizer, and attaches one checkpoint-thirty point record to every state.
  It refuses any positive-dimensional type and stops before factor
  exponentiation, tilted normalization, selection, RNG, initializer admission,
  path construction, or sampler admission.
- `configuration_initial_tilt_atomic_selector_code_audit.md`
  — equation-to-code audit of the thirty-second implementation checkpoint: a
  sealed deterministic preparation of a positive \(2^{64}\)-quota
  approximation to the resource-admitted all-atomic operational tilted law,
  with directed mass enclosures, exact proxy normalization, rigorous TV
  bounds, and exact lookup from one explicit uint64 word. Checkpoint thirty-two
  itself neither acquires nor certifies the word nor binds checkpoint twenty-
  seven stage 0, and does not admit an initializer, continuous/mixed support,
  a path, or a sampler.
- `configuration_initial_tilt_atomic_protocol_binding_code_audit.md`
  — equation-to-code audit of the thirty-third implementation checkpoint: a
  sealed bridge that materializes checkpoint twenty-seven's exact one-word
  enumeration-stage tag-7 prefix and forwards its sole uint64 value unchanged
  to a matching checkpoint-thirty-two preparation and selector. For a fixed
  preparation \(p\), replacing that live word by a separate abstract
  \(U\sim\operatorname{Uniform}(\{0,\ldots,2^{64}-1\})\) makes the lookup
  output follow checkpoint thirty-two's dyadic law
  \(Q_p^{\mathrm{dyadic}}\); \(U\) is not identified with the
  live word source, whose value and output at a fixed address are deterministic. It
  certifies no actual Philox law, initializer admission, mixed/continuous
  support, lineage, path, or sampler.
- `configuration_initial_tilt_atomic_initializer_admission_code_audit.md`
  — equation-to-code and law-boundary audit of the thirty-fourth implementation
  checkpoint: a factory-owned live all-atomic initial-state configuration
  constructor with exact checkpoint-thirty-one through checkpoint-thirty-three
  custody and no per-call caller context, preparation, RNG, or word. Its
  positive output/pushforward-law theorem is only the same counterfactual
  replacement-\(U\) pushforward to \(Q_p^{\mathrm{dyadic}}\). Separately, the
  fixed preparation inherits
  \(\operatorname{TV}(P_p^{\mathrm{operational}},
  Q_p^{\mathrm{dyadic}})\le2^{-48}\). It does not
  certify a live initializer distribution or admission, actual word
  uniformity/independence, general or mixed/continuous initialization, a path,
  or a sampler. The filename retains `admission` as the historical checkpoint
  label, not as a positive admission claim.
- `plugin_bridge_counter_keyed_mixed_reference_constructor_code_audit.md`
  — equation-to-code and law-boundary audit of the thirty-fifth implementation
  checkpoint: a fixed-index finite mixed reference constructor that composes
  checkpoint twenty-eight's tag-7 transform, a reverse-time-zero intensity,
  checkpoint twenty-three bootstrap lineage, and checkpoint twenty-five
  dimension-shaped tag-3 prefixes. Its exact finite-pushforward theorem uses a
  separate abstract iid-uniform uint64 vector and concerns only the CP28
  configuration component \(Q_{\mathrm{fin}}\), not the live Philox words,
  tag-3 transcript, or full result. It is not a conditional/tilted initializer,
  initializer admission, path, or sampler.
- `plugin_bridge_counter_keyed_initial_tilt_rejection_preparation_code_audit.md`
  — equation-to-code and law-boundary audit of the thirty-sixth implementation
  checkpoint: fixed-budget checkpoint-twenty-seven rejection-stage preparation
  using the exact checkpoint-twenty-eight proposal transform, one reserved
  uninterpreted word per attempt, and the checkpoint-thirty exact point score
  with reduced rational witness \(q-U\le0\). It makes no acceptance decision,
  selects no attempt, and admits no initializer. Its only distributional
  statement is conditional on a separate abstract iid-uniform uint64 family
  over distinct full logical coordinates and uses a total map into an abstract
  success batch disjoint-unioned with one failure symbol.
- `plugin_bridge_counter_keyed_initial_tilt_rejection_decision_code_audit.md`
  — equation-to-code and law-boundary audit of the thirty-seventh
  implementation checkpoint: exact conservative quotas
  \(K_a=\lfloor2^{64}e^{q_a-U}\rfloor\), certified for every CP36 attempt
  before any reserved word is decision-compared, followed by exact half-open
  prefix comparisons and either first-selected output or bounded exhaustion.
  Its product law requires fixed proposal/score data and a separate abstract
  iid-uniform word family. Separately, a fixed-data common-uniform coupling of
  independent-coordinate ideal and dyadic Bernoulli sequences gives the strict
  \(A/2^{64}\) finite-outcome discrepancy bound. It certifies no live Philox
  law, exact ideal rejection, initializer
  admission, lineage/tag-3 coordination, path, or sampler.
- `plugin_bridge_counter_keyed_initial_tilt_rejection_finite_batch_law_code_audit.md`
  — equation-to-code and law-boundary audit of the thirty-eighth
  implementation checkpoint: the complete exact counterfactual first-success
  and exhaustion law conditional on a direct word-free projection \(B\) of
  CP36 candidates, score gaps, and CP37 quotas. It stably aggregates duplicate
  configurations and defines the selected-configuration law only when
  selection has positive mass. A separate common-uniform comparison gives the
  strict \(A/2^{64}\) augmented dyadic-versus-ideal TV bound before selection
  conditioning. It certifies no live Philox law, success-conditioned reuse of
  that bound, generic initializer admission, lineage/tag-3 coordination, path,
  or sampler. The no-cache, warnings-as-errors focused suite passed 45/45 and
  its CP37 direct-parent regression passed 44/44; the disposition is **PASS
  WITH EXPLICIT SCOPE LIMITS**.
- `plugin_bridge_counter_keyed_initial_tilt_rejection_lineage_tag3_coordination_code_audit.md`
  — equation-to-code and custody-boundary audit of the thirty-ninth
  implementation checkpoint: one exact CP38 resolution followed, only on the
  selected branch, by reverse-time-zero reference intensity, duplicate-safe
  CP23 positional bootstrap lineage, and bounded CP39-local tag-3 prefixes at
  key `(run_id, 3)` and counter
  `(0, initialization_index, occurrence_serial, selected_attempt_index + 1)`.
  Prefix length is `max(1, manifest_dimension)`. Selected-empty remains a
  present state with intensity and empty lineage; exhaustion remains an exact
  no-state result with no selected-branch child construction. The positive
  suffix is disjoint only from valid legacy suffix-zero tag-3 addresses; no
  global, one-shot, cross-bootstrap, merge, or fork guarantee follows. The
  words are uninterpreted and do not generate coordinates. The final
  disposition is **PASS WITH EXPLICIT SCOPE LIMITS**.
- `plugin_bridge_counter_keyed_initial_tilt_rejection_admission_code_audit.md`
  — equation-to-code, admission-boundary, and custody audit of the fortieth
  implementation checkpoint. It names CP38's exact augmented dyadic law
  conditional on the direct word-free successful batch \(B\) as the finite-
  resolution target, defines its selected-state target only for \(Z_B>0\), and
  records the correctly selection-mass-scaled ideal/dyadic comparison. One
  exact CP39 selected state, including selected-empty, crosses a narrow
  downstream structural state boundary; exhaustion retains the target but no
  state. This is not a live distribution, global normalized tilt, exact ideal
  rejection, all-strategy initializer admission, path, or sampler. Source and
  tests are frozen, the focused suite passed 45/45, and inherited exact-hash
  CP39 parent evidence remains applicable; the disposition is **PASS WITH
  EXPLICIT SCOPE LIMITS**.
- [`plugin_bridge_counter_keyed_initial_tilt_rejection_failure_aware_source_law_code_audit.md`](plugin_bridge_counter_keyed_initial_tilt_rejection_failure_aware_source_law_code_audit.md)
  — equation-to-code and law-boundary audit of the forty-first implementation
  checkpoint: an abstract product-uniform failure-aware source law conditional
  on an explicit unproved factorization hypothesis. It partitions CP36's
  normalized words into proposal/scoring coordinates \(V\) and reserved
  decision coordinates \(W\), distinguishes preparation failure, quota
  failure, exhaustion, and configuration atoms, and records only symbolic
  fiber mixtures and their exact normalization. No numeric fiber or mass is
  materialized, and no live Philox, source, or initializer law follows. The
  no-cache, warnings-as-errors focused suite passed **28/28**; the disposition
  is **PASS WITH EXPLICIT SCOPE LIMITS**.
- [`plugin_bridge_counter_keyed_initial_tilt_rejection_predecision_factorization_code_audit.md`](plugin_bridge_counter_keyed_initial_tilt_rejection_predecision_factorization_code_audit.md)
  — equation-to-code and staging-boundary audit of the forty-second
  implementation checkpoint: the bounded partial executable reference map
  \(G^{42}_{r,j}\), from \(D^M\) to
  \(\{F_{37}\}\mathbin{\dot\cup}\mathcal R\), whose random-word input
  excludes the reserved decision tuple. On calls whose direct CP28/CP30 stages do not
  refuse, it precedes a separate \(H^{42}\) that receives fully preflighted
  \(W\) only after every ready quota exists. The preparation-failure tag is
  reserved outside the executable image. The sealed witness retains and
  digest-binds a supplied successful CP37 result for custody, while its parity
  comparison is limited to the predecision/threshold projection---\(V\),
  configurations, gaps, and quota fields. The bound CP37 digest includes its
  decision records/words and outcome, but the witness contains no CP42 applied-
  \(H^{42}\) record and asserts no \(W\)/outcome parity or failure-fiber
  parity. One \(A=1\) \(H^{42}\)-outcome comparison is a separate focused
  assertion.
  This does not prove universal live CP36/CP37 failure equivalence, discharge
  CP41's hypothesis, or supply a live source/initializer law. Qualification
  requires the focused run, additive supplement, CP41 regression, static
  gates, and final independent review.
- [`plugin_bridge_counter_keyed_initial_tilt_rejection_factorization_closure_code_audit.md`](plugin_bridge_counter_keyed_initial_tilt_rejection_factorization_closure_code_audit.md)
  — equation-to-code, factorization-boundary, and custody audit of the
  forty-third implementation checkpoint: a bounded supplied-word reference
  closure over one exact CP42 owner. Under its declared exact typed-error and
  trusted-runtime contract, \(G^{43}\) consumes only \(V\), maps exact CP28 or
  CP30 operational errors to \(F_{36}\), and otherwise retains CP42's
  \(F_{37}\)-or-ready result. The private semantic
  \(H^{43}_{\mathrm{sem}}\) receives \(W\) only after complete \(G^{43}\),
  while the separately invoked public replay facade
  first replays \(G^{43}\) for custody and therefore requires replay-stable
  failures. The resulting construction closes only the CP43-defined abstract
  reference factorization and its explicitly premised product-uniform
  corollary. It does not discharge CP41's live-parent hypothesis, certify a live
  Philox/source/initializer law, resolve natural \(F_{37}\) reachability, or
  admit a path or sampler. Final execution and independent-audit evidence is
  frozen in the linked audit.
- [`plugin_bridge_counter_keyed_initial_tilt_rejection_factorized_execution_adapter_code_audit.md`](plugin_bridge_counter_keyed_initial_tilt_rejection_factorized_execution_adapter_code_audit.md)
  — equation-to-code, source-boundary, and custody audit of the forty-fourth
  implementation checkpoint: a new one-allocation operational route from one
  complete CP27 rejection-protocol capsule through CP43's exact split and
  combined semantics. It keeps pre- and post-combined refusal outside
  \(F_{36}/F_{37}\), claims equality only after canonical semantic projection
  for calls that return a CP44 result, and provides a structural public
  validator that does not replay allocation, CP43 \(G/H\), CP36 `prepare`, or
  CP37 `decide`. Its CP41-form law is only a corollary for an abstract semantic
  map under both a fixed-runtime deterministic replay-stable total-\(G^{43}\)
  premise and a product-uniform full capsule. It neither proves equivalence to
  the legacy CP36/CP37 route nor discharges CP41's original live-parent premise.
  Its frozen focused, static, exact-string, and independent-audit evidence is
  recorded in the linked audit; CP43/CP42 execution evidence is inherited by
  exact hash and was not freshly rerun for CP44. Its disposition is **PASS WITH
  EXPLICIT SCOPE LIMITS**.
- [`plugin_bridge_counter_keyed_initial_tilt_rejection_fixed_address_source_support_obstruction_code_audit.md`](plugin_bridge_counter_keyed_initial_tilt_rejection_fixed_address_source_support_obstruction_code_audit.md)
  — source-law and overclaim-boundary audit of checkpoint forty-five. A fixed
  same-runtime CP44 request that returns an L-word capsule has a point-mass
  source law at exact TV distance `1-2^(-64L)` from product uniform. More
  generally, a deterministic successful capsule map driven by at most k free
  uint64 coordinates has conditional-success support at most `2^(64k)` and
  hence TV at least `1-2^(-64(L-k))` when L>k, without a
  success/value-independence premise. This is source-only: data processing
  supplies no semantic-output lower bound, and a constant map can erase the
  discrepancy. CP45 allocates no source and executes no CP43/CP44 semantics;
  inherited ancestry validation may run a deterministic local Philox probe
  while caller/global RNG states remain unchanged. No live uniformity,
  independence, refusal probability, randomness, initializer/path/sampler,
  empirical, or generality claim follows. Its frozen 20/20 focused result,
  post-run static gates, unchanged hashes, and independent `P0=P1=P2=0`
  review are recorded in the linked audit; the disposition is **PASS WITH
  EXPLICIT SCOPE LIMITS**.
- `../src/heterodiff/processes/plugin_bridge_counter_keyed_initial_tilt_rejection_explicit_source_model_contract.py`
  and
  `../tests/unit/test_plugin_bridge_counter_keyed_initial_tilt_rejection_explicit_source_model_contract.py`
  — checkpoint-forty-six source and focused tests for two explicitly separated
  source descriptors: deterministic fixed-request replay and a declarative
  finite exact-rational law over the two uint64 request coordinates. CP46
  records positive-event source-support/TV consequences and the exact
  weighted-fiber criterion, while certifying neither event positivity nor an
  external law realization, sampler, output discrepancy, or scientific claim.
  The frozen source/test SHA-256 values are
  `8c6d1ead643a127aa87d395de1ff707eb0506e619d53b513477777173d439318`
  and `04b73ec0f0fbd0a8a31973a02a2218cdd1ea3ad000a9648168a1f7194c7415ac`;
  final focused evidence is **24/24 passed** with static gates and independent
  `P0=P1=P2=0` audits. The complete evidence boundary is recorded in the
  linked
  [`plugin_bridge_counter_keyed_initial_tilt_rejection_explicit_source_model_contract_code_audit.md`](plugin_bridge_counter_keyed_initial_tilt_rejection_explicit_source_model_contract_code_audit.md).
- `../src/heterodiff/processes/plugin_bridge_counter_keyed_initial_tilt_rejection_external_full_capsule_execution_adapter.py`
  and
  `../tests/unit/test_plugin_bridge_counter_keyed_initial_tilt_rejection_external_full_capsule_execution_adapter.py`
  — checkpoint-forty-seven source and focused tests for one direct external
  provider of an exact \(L\)-word uint64 capsule. Identity ingestion exposes a
  \(D^L\)-element interface but certifies no source law: product uniformity,
  IID returned capsules across distinct draw identifiers, and value-
  independent success remain external premises. The adapter binds the exact
  CP46--CP45--CP44--CP43 ancestry, retires draw IDs
  only within one bounded owner lifetime, and validates retained results
  structurally without replaying the provider or CP43 semantics. The frozen
  source/test SHA-256 values are
  `2c1522cd92f186d3d428e627bdd7ba6f29a7b8fbf727fb8ca8b7852f1badcf0b`
  and `46ab42233351a681b5b7618fcbff088e1e4f474f0350b636e081148fb2af2ced`;
  final focused evidence is **31/31 passed** (22 fast and nine owner-bound)
  with static gates and independent `P0=P1=P2=0` audits. The complete
  evidence boundary is recorded in the linked
  [`plugin_bridge_counter_keyed_initial_tilt_rejection_external_full_capsule_execution_adapter_code_audit.md`](plugin_bridge_counter_keyed_initial_tilt_rejection_external_full_capsule_execution_adapter_code_audit.md).
- `../src/heterodiff/processes/plugin_bridge_counter_keyed_initial_tilt_rejection_byte_source_full_capsule_execution.py`
  and
  `../tests/unit/test_plugin_bridge_counter_keyed_initial_tilt_rejection_byte_source_full_capsule_execution.py`
  — checkpoint-forty-eight source and focused tests for the exact byte-source
  boundary above CP47. The `system-os-urandom-operational` profile binds the
  internal wrapper around the cached ordinary `os.urandom` Python API; the
  `external-exact-byte-block-unverified` profile binds one exact caller
  callback. At each reached CP47 provider boundary, the selected backend
  is called exactly once for exact `bytes` of length \(8L\), which are decoded
  by the fixed manual big-endian bijection into the exact \(L\)-word tuple passed
  once to CP47. CP47 remains the sole draw-retirement and semantic-execution
  authority. The frozen source/test SHA-256 values are
  `7be4c1bdf588950902bbdfe03e492dea15e42d0affff5d6e83f6104b798974cd`
  and `2fa6f429424d95e851496fc870ca1d2598cf44f83a6adb98c673cc93ebcdf282`;
  final focused evidence is **37/37 passed** (28 source-independent fast cases
  and nine owner-bound cases), with static gates and independent
  `P0=P1=P2=0` review. The complete evidence boundary is recorded in the linked
  [`plugin_bridge_counter_keyed_initial_tilt_rejection_byte_source_full_capsule_execution_code_audit.md`](plugin_bridge_counter_keyed_initial_tilt_rejection_byte_source_full_capsule_execution_code_audit.md).
- `../src/heterodiff/processes/plugin_bridge_counter_keyed_initial_tilt_rejection_full_source_law_admission.py`
  and
  `../tests/unit/test_plugin_bridge_counter_keyed_initial_tilt_rejection_full_source_law_admission.py`
  — checkpoint-forty-nine source and focused tests for one sealed,
  assumption-only full-source law admission gate above exact CP48 ancestry.
  For each individually fixed request and fixed pre-operation state, its
  pointwise theorem requires external assumptions of fresh-draw admissibility,
  almost-sure exact-block backend return, unconditional jointly uniform
  complete byte blocks, post-boundary complete success for every block, and
  fixed-runtime deterministic replay-stable typed-total CP43/CP42 object
  semantics. CP49 acquires no bytes and executes or replays no semantics. The
  frozen source/test SHA-256 values are
  `7951c02c60b6ca8dbbbf025f13e26e52eb7319cd4c48d416e5b841d99530bd39`
  and `a799c68ebe2d9fa415bf1282a2f28c4f87570a7d21a728373d61f5a34a100e7a`;
  final focused evidence is **28/28 passed** (21 source-independent and seven
  owner-bound cases), with a post-run **21/21** source-independent check,
  static gates, stable hashes, and independent `P0=P1=P2=0` review. The
  disposition is **PASS WITH EXPLICIT SCOPE LIMITS**. The complete evidence
  boundary is recorded in the linked
  [`plugin_bridge_counter_keyed_initial_tilt_rejection_full_source_law_admission_code_audit.md`](plugin_bridge_counter_keyed_initial_tilt_rejection_full_source_law_admission_code_audit.md).
- `claim_ledger.md` — claim, proof, experiment, and result-unlock ledger.
- `execution_preregistration.md` — mandatory numerical and artifact freeze;
  currently a pending template that authorizes no decision-bearing run.
- `novelty_audit_matrix.md` — property- and equation-level collision audit;
  novelty remains unassessed until an irreducible distinction survives.
- `source_trace.md` — trace from the supplied music manuscript to Manuscript v3.

## Status markers

- **`[DEFINED]`** — the object or protocol is specified, but this does not imply
  novelty, proof, or empirical success.
- **`[FOUNDATION]`** — standard or previously established machinery needed for
  correctness; it is not claimed as a contribution.
- **`[NOVELTY-UNASSESSED]`** — the candidate distinction has not survived the
  code-matched nearest-work audit.
- **`[THEOREM-TARGET]`** — a proposed theorem statement or proof obligation; no
  proof is claimed.
- **`[RESULT-PENDING]`** — the experiment has not produced an admissible result.
- **`[TASK-ADMISSION-PENDING]`** — the intended observation task has not yet
  satisfied the primary theory and domain-semantics contract.
- **`[METHOD-DEFINITION-PENDING]`** — the observation/association
  implementation, common-space guide, trained/selected bounded energy,
  production
  proposal, or reverse/conditional sampler semantics are not yet fully
  frozen; the displayed end-to-end method remains incomplete.
- **`[LEDGER-PENDING]`** — numerical thresholds, identities, budgets, or failure
  rules have not been immutably frozen; decision-bearing execution is blocked.
- **`[SOURCE-REPORTED]`** — a statement appears in the supplied manuscript but
  has not been independently reproduced.
- **`[STOP/PIVOT]`** — the associated claim must be retired if its gate fails.

These markers are internal controls and will be removed only when the claim
ledger authorizes submission prose.

## Current evidence boundary

This package contains no new model-quality result, cross-domain result,
listening-study outcome, or generality evidence. It does not promote software
tests, exact finite controls, data inventories, or source-reported MAESTRO
numbers into empirical findings. It contains one separately labelled,
nonconfirmatory finite-grid engineering diagnostic.

The candidate guide-plus-residual method remains novelty-unassessed and
method-definition-pending. An internally cross-audited mathematical
implementation contract now exists in
[`executable_method_spec.md`](executable_method_spec.md). Forty-eight incremental
code-matched implementation and engineering-evidence checkpoints now exist:
the transformed
capped-Poisson reference, the
reversible forward reference process, a NumPy theorem-oracle layer for
reference-relative reverse targets and population objectives, the bound
normalized association-observation row, and the analytic association
preconditioner with its explicit cap-boundary diagnostic, followed by the
bounded invariant neural/checkpoint correctness layer and the process-owned
normalized reference-candidate composer. The eighth layer is deliberately
restricted to cap one, exactly two types with positive unequal-dimensional
Gaussian fibers, and a positive two-way replacement edge. Within that scope
it adds an operationally certified nonnegative uniformization calculation,
the exact nonstationary forward density and derivatives, edit multipliers,
transition components, analytic terminal-reference TV, and the exact
backward information, Doob drift/edit controls, reset laws, initializer, and
endpoint marginal. The ninth layer uses those records to sample the exact
right-end marginal, run the event-driven reference path on the reflected
direct-time interval, and reverse its compact endpoints, times, and edit
records. Its finite-RNG gates refuse unresolved state/mixture categories,
timestamp collisions, and the unsupported initial-boundary-jump convention.
A tenth checkpoint then extends the process-owned composer with a sealed,
deterministic query of
\(\gamma_J(S-u)\Lambda^0(x)\) before RNG. It distinguishes the exact clean
hold from an active structural-zero exit, refuses direct-time breakpoint
collisions and binary64 rate loss, preflights every reachable normalized-
reference categorical route, and makes the subsequent route draw revalidate
that record without changing the underlying RNG stream.
A subsequent eleventh checkpoint extends the analytic preconditioner with a
canonical retained/overflow-observation certificate. It uses exact-rational
Gershgorin covariance witnesses, directed log arithmetic, a cap-aware
injection polynomial, an independent overflow-tail lower witness, and global
flattened ∇log-guide/Hessian bounds. The certificate is deliberately
model-level under normalized probability-simplex and Markov-kernel semantics:
the existing pointwise evaluator has no uniform floating-point forward-error
enclosure, so this layer cannot yet be consumed as an operational thinning
guarantee.
A twelfth checkpoint now wraps that evaluator with a fail-closed represented
range gate. For a fixed retained or overflow observation, it constructs
directed log endpoints and their outward-rounded width, preserves a raw exact
finite binary64 log guide bit for bit only when the certificate's live
model/observation binding holds, the returned time/state match the request,
and the value passes the interval gate. It assembles legal represented
birth/death/replacement edits from two admitted endpoints. This proves a
coarse uniform discrepancy bound over successful evaluations and a direct
represented edit envelope; it does not prove small arithmetic error, totality
or liveness over unbounded coordinates, coordinate derivatives, continuous
drift, residual composition, a controlled clock, or a sampler.
A thirteenth checkpoint adds the distinct general residual primitive. It
reuses the bounded typed-DeepSets core under independent residual semantics,
consumes process-owned direct time and a procedurally frozen finite-vector
conditioner, applies the cubic clean-hold gate without a second saturation,
and evaluates the core only on active rows. Its certificate binds process,
observation/task/context schemas, conditioner adapter, residual role,
checkpoint, runtime, and run provenance; it inherits global value,
same-condition state-pair, full flattened physical-coordinate
gradient/Hessian, and Laplacian bounds. Mathematical and operational gate
rounding are separated and outward-bounded. It does not authenticate the
origin of a supplied context tensor or certify time/conditioner derivatives,
training success, base/guide/residual composition, or a sampler.
A fourteenth checkpoint now composes the three jump-log contributions for one
active, already sampled process-valid reference candidate. It independently
recomputes the certified base at direct time, the fixed-observation
range-gated guide edit at reverse time, and the separately certified residual
at direct time; then it adds the three returned binary64 values exactly as
rationals and rounds once. The certificate and evaluation record bind the
process, endpoints, edit kind, times, distinct context schemas, guide outcome,
base/residual checkpoints and roles, provenance, and live state. Separate
mathematical and operational component bounds are outward-composed into a
time-specific aggregate log witness. Base and residual neural state storage
must be physically disjoint, including overlapping views. This layer remains
successful-only because the represented guide can refuse; it neither
exponentiates the bound nor constructs a rate-space envelope, total exit,
waiting/acceptance law, continuous drift, initializer, path, or sampler.
A fifteenth checkpoint now adds a separate totalized association jump guide.
For one fixed retained or overflow observation, its factory first preflights
point-evaluation resources over the full capped finite-binary64 state domain
and all reverse times. Successful range-gated raw values are preserved
bitwise; only typed numerical/range point failures use the exact-rational
interval midpoint rounded once. Point and edit records bind runtime-specific
streaming state digests. The certificate supplies the interval width \(W_m\),
a sharper midpoint-fallback point bound, and an outward \(2W_m\) analytic-edit
discrepancy bound. Exact rational operational endpoint differences telescope,
but independently rounded binary64 edges have no exact cycle-closure claim.
This is explicitly a new jump-only operational surrogate when fallback is
used, not the analytic conditional/posterior or Doob target. The fourteenth
composer does not yet consume it, and it supplies no derivatives, continuous
drift, rate envelope, clock, RNG, path, or sampler admission.
A sixteenth checkpoint now adds the corresponding jump-only residual
operational layer while leaving checkpoint thirteen unchanged. Every
successful certified residual point is preserved bitwise. Only the exact typed
strictly active tiny-cubic-gate failure uses the exact rational gate times the
represented bounded-core value from a private checkpoint-materialized model,
rounded once. Supplied batches are evaluated only through detached canonical
snapshots; public/private model custody, consumed-subnormal DAZ/FTZ probes,
streaming digests, structural point/edge bounds, and narrow exception handling
are replayed. Exact rational endpoint differences telescope, but their rounded
binary64 values need not. The rescaling branch is an operational surrogate,
not an exact real neural residual or conditional/posterior target. Checkpoint
fourteen consumes neither totalizer, and this layer supplies no derivative,
drift, rate envelope, clock, RNG, path, or sampler admission.
A seventeenth checkpoint now selects one explicit jump-only operational target

\[
\Phi_{\mathbb Q}^{\mathrm{op}}(u,x)
=\iota(V_{64}(S-u,x,c_{\mathrm{base}}))
+\iota(G_{64}^{\mathrm{totalized}}(u,x;\text{fixed observation}))
+\iota(R_{64}^{\mathrm{totalized}}(S-u,x,c_{\mathrm{resid}})).
\]

For one active process-valid birth, death, or replacement candidate it
recomputes all six represented endpoint values, subtracts and sums them as
exact rationals, and rounds the aggregate once to nearest-even binary64.
Component-rounded edges are recorded but are not used in the aggregate. The
exact rational edge is consequently a coboundary of the displayed operational
point function; separately rounded binary64 edges still need not close a
cycle. The certificate transitively binds the process, fixed guide outcome,
contexts, totalizer certificates, base/residual checkpoints and provenance,
runtime, and composition role. Evaluation uses a private checkpoint-
materialized base while retaining an external live base owner for custody;
external base, private base, external residual, and private residual model
storage must be pairwise disjoint. This is explicitly an operational
surrogate, not the exact analytic guide, exact real neural target,
conditional/posterior target, or Doob transform. Checkpoint fourteen remains
unchanged. The new composer stops in log space and supplies no exponentiation,
rate envelope, total exit, clock, RNG, derivative/drift, initializer, path, or
sampler admission.
A separate eighteenth checkpoint consumes that exact operational edge and the
deterministic reference intensity. Relative to the normalized reference route
law, it defines

\[
I_{\mathbb Q}^{\mathrm{op}}(u,x,y)
=\Lambda_{S-u}^0(x)
\exp\{\Delta_{\mathbb Q}\Phi^{\mathrm{op}}(u;x,y)\}.
\]

It exponentiates the exact rational edge, not checkpoint seventeen's rounded
display, using adaptive 192/384/768/1536-digit directed Decimal direct-product
intervals. A successful active candidate receives one correctly rounded
finite normal binary64 integrand and an outward interval. Before any route
draw, it constructs

\[
E_{\mathbb Q}^{\mathrm{op}}(u,x)
=\operatorname{rd}_{\uparrow}
\{\Lambda_{S-u}^0(x)e^{D_\Phi^{\mathrm{op}}}\},
\]

plus a process-global counterpart. These dominate every admitted candidate
and therefore upper-bound the operational controlled total exit; they are not
the exact active exit. Structural-zero reference intensity gives an exact
zero without target evaluation. The checkpoint does not admit a route draw,
waiting/acceptance randomness, rounded detailed balance, an exact stationary
target, derivatives/drift, initialization, paths, or a sampler.
A nineteenth checkpoint consumes that local envelope for one successful-return
local operation. Successive words from one Philox stream define an ideal
uniform prefix and a directed Decimal enclosure of
\(\tau=-\log(U)/E_{64}^{\mathrm{op}}\). Real eligibility is inclusive at the
right endpoint, \(\tau\le b-a\), but a public return requires a uniquely rounded
binary64 timestamp satisfying \(a<t_{64}^{\mathrm{proposal}}<b\); exact
right-end equality or represented collapse to either boundary is refused. Only
after such a hit does the same stream enter the inherited process-owned route
draw. That route retains its finite-resolution binary64 CDF, integer, and
standard-normal semantics; this checkpoint does not upgrade it to a variable-
bit exact route law. Acceptance uses an exact variable-word Bernoulli for the
reduced rational quotient of the actual represented candidate integrand and
envelope, \(I_{64}^{\mathrm{op}}/E_{64}^{\mathrm{op}}\), never a simplified
exponential, conditional on the declared uniform-word model and a resolved
bounded trial. Resource-cap exhaustion is a refusal. The record's
`proposal_time` is the authoritative local
operational-clock timestamp and is distinct from the midpoint-frozen
reverse/direct generative times. Stream-state continuity is checked across
waiting, route, and acceptance, but there is no counter-keyed
run/step/occurrence/proposal contract. This is successful-return local evidence
only: it supplies no rejection loop, accepted-state envelope recomputation,
proposal ceiling, continuous-destination operational fixture, lineage,
drift/Strang integration, initializer, path, or full sampler.
A separate twentieth checkpoint coordinates repeated checkpoint-nineteen
operations within one fixed local interval. If a candidate is rejected, the
next clock starts at the returned binary64 `proposal_time` and reuses the exact
state, reference-intensity, and envelope objects. If it is accepted, the
destination is canonicalized and a fresh process-owned reference intensity and
fresh checkpoint-eighteen envelope are constructed immediately at the same
frozen reverse/direct generative time, before either continuation or a cap
decision. Each accepted parent pair is identity-distinct from the initial pair
and every earlier accepted epoch, including a semantic \(A\to B\to A\)
return. One mutable Philox stream is checked across every wait, inherited
route, potential/rate evaluation, acceptance decision, and accepted-state
refresh.

The loop returns a sealed transcript only after checkpoint nineteen certifies
that the remaining interval is exhausted, including structural-zero and
zero-duration no-RNG holds. Structural zero takes precedence when it coincides
with zero duration. The exact proposal budget lies in 0--64 and counts every
completed candidate proposal, including rejections. If the state remains
active at the cap, the call refuses before drawing another waiting time; it
does not return a truncated trajectory. An acceptance at the cap is still
followed by mandatory intensity/envelope refresh, after which a structural-
zero hold may complete successfully or an active state refuses. Failures do
not roll back already consumed Philox bits. Because each renewal starts from a
rounded binary64 timestamp and the inherited categorical/Gaussian route is
finite-resolution, this is not an unconditional completion theorem, exact
real-time Poisson/CTMC or frozen-jump path law, analytic/conditional target,
counter-keyed stream, lineage contract, drift/Strang step, initializer, path,
or full sampler. Its focused route evidence remains all-atomic; a continuous-
destination operational fixture remains pending.
A separate twenty-first checkpoint leaves those frozen historical records
unchanged and adds reconstructable same-runtime route evidence. It captures
the complete canonical Philox state immediately before and after the delegated
route, reconstructs a fresh local Philox generator, and calls the frozen
process-owned route composer exactly once. Validation requires the replayed
candidate digest and every post-state field to match. The record retains the
labelled source occurrence, exact binary64 destination coordinates, declared
source/destination dimensions, quotient multiplicity, and represented
analytic route factors. Fixed fixtures cover a continuous birth and genuine
2D-to-3D and 3D-to-2D reset replacements; death remains an admissible
non-continuous record and triggers no hidden resampling. This closes the
specific post-hoc continuous-route custody gap, but not the ideal route law:
NumPy's categorical, integer, and standard-normal operations remain finite-
resolution, no bounded normal raw-word trace is supplied, and Test 29's
distributional comparison remains pending.
A separate twenty-second checkpoint composes the frozen bounded loop and
route-evidence owner without altering either parent. It captures exact Philox
snapshots around one black-box checkpoint-twenty run, reconstructs a fresh
local stream from the entry snapshot, replays every checkpoint-nineteen
waiting and acceptance raw-word prefix, inserts one checkpoint-twenty-one
route witness at each reconstructed route boundary, and replays the terminal
waiting prefix. The ordered route records are positionally bound to the loop's
waiting, intensity, envelope, route, candidate, decision, source,
destination, and RNG fields, and the reconstructed full exit must equal the
caller's captured checkpoint-twenty exit. Acceptance, rejection, refresh,
terminal, and proposal-cap semantics remain owned by checkpoint twenty.
Offline validation accepts no caller RNG. A post-loop overlay failure is
fail-closed but nontransactional: checkpoint twenty's already consumed caller
bits are not rolled back and no partial composite result is returned. This
closes bounded-loop route custody for returned continuous proposals, not the
ideal route law, Test 29, unconditional completion, liveness, a path, or the
full sampler.
A separate twenty-third checkpoint leaves checkpoint twenty-two and all of its
parents frozen. It adds two prerequisites for a future production path. First,
it issues initially unused NumPy Philox receipts at the direct address

\[
\operatorname{key}=(\texttt{run\_id},\texttt{domain\_tag}),
\qquad
\operatorname{counter}=(0,\texttt{step\_index},
\texttt{occurrence\_serial},\texttt{proposal\_index}),
\]

with fixed, disjoint jump-proposal, terminal-wait, initializer, left-Brownian,
and right-Brownian domain tags. The address components are neither hashed nor
folded, and the complete empty Philox state is reconstructable only in the same
declared runtime. Second, it fully revalidates one returned checkpoint-twenty-
two transcript and overlays persistent positional lineage without placing an
identifier in the model state. Equal-valued bootstrap occurrences receive
distinct position-derived identifiers. Accepted births and replacements create
fresh monotone identifiers, accepted deaths and replacements retire the exact
indexed source identifier, and stable sorting uses the event model key only.
Rejections and the terminal waiting record reuse the exact lineage-state object.
The retained retired-identifier ledger prevents reuse within that exact custody
chain. This is not evidence that checkpoint twenty-two was proposal-keyed or
consumed any issued receipt. It does not consume occurrence, initializer, or
Brownian streams, certify Brownian coupling, implement drift or initialization,
construct a path or Strang step, or admit the full sampler. Independent
bootstraps or deliberate forks require a fresh `run_id`; the module maintains no
global run-ID or one-shot address registry.
A separate twenty-fourth checkpoint leaves checkpoints nineteen through
twenty-three frozen and adds a new successor-owned direct Philox domain,
`operational_epoch`, with tag 6. At an active loop boundary with \(p\) completed
proposals it constructs

\[
\operatorname{key}=(\texttt{run\_id},6),
\qquad
\operatorname{counter}=(0,\texttt{step\_index},0,p),
\]

reconstructs one local same-runtime Philox generator, and uses that exact
generator continuously for checkpoint nineteen's wait and, when a candidate is
due, route and represented-ratio acceptance. A candidate epoch binds one exact
checkpoint-twenty iteration, one checkpoint-twenty-one route witness, and one
checkpoint-twenty-three lineage transition. An active tag-6 wait may instead
certify stochastic right-endpoint exhaustion and then creates no proposal,
route witness, or lineage transition. A preflight-known structural-zero or
zero-duration hold binds the frozen checkpoint-twenty-three `terminal_wait`
receipt and consumes zero random words. The legacy tag-1 `jump_proposal`
receipts remain unconsumed. The successor accepts no caller RNG, but this does
not prove one-shot address use, statistical independence, an exact route or
frozen-jump law, unconditional completion, liveness, a path, or a sampler.
Before nested reconstruction or digest traversal, exact-type and resource
preflights bound candidate configurations/events and live-plus-retired lineage
records. Returned records require canonical context tuples and their digests,
the exact parent certificate objects, deep supplied waiting/iteration/evidence
validation, positionally complete per-proposal digest chains, and identity—not
merely equality—between lineage events and the unlabelled model projection.
The frozen checkpoint-twenty-four audit records **46/46 focused tests** and
**200/200 nonduplicative inherited tests**, with a final independent **PASS
WITH EXPLICIT SCOPE LIMITS** and no P0, P1, or P2 finding.
A separate twenty-fifth checkpoint consumes only the already reserved
bootstrap tag-3 initializer receipts. For a bootstrap occurrence with run ID
`r` and positive positional serial `ell`, it fixes the initializer step to zero
and uses

\[
\operatorname{key}=(r,3),
\qquad
\operatorname{counter}=(0,0,\ell,0).
\]

The admitted input has at most 64 live initial-origin occurrences, no retired
identifier, positional serials `1,...,n`, and the exact event identities in the
unlabelled model projection. The caller supplies one exact positive Python-
integer count per live occurrence, with at most 4,096 `raw64` words per
occurrence and 65,536 words in aggregate. The entire plan is preflighted before
the first receipt is issued; an empty bootstrap with plan `()` is the only
successful zero-word case. Every record retains exact pre/post Philox snapshots,
replays its raw prefix in the same runtime, and checks that the key and upper
counter limbs do not change. The owner accepts no caller RNG and returns the
exact input lineage-state object and model projection unchanged.

These words are deliberately uninterpreted. They do not define cardinality,
event type, coordinate, categorical, integer, Gaussian, rejection, or SIR
outputs and therefore do not implement a general or conditional initializer.
Because global cardinality and final occurrence serials do not exist before
initialization, a future general initializer requires a separate disjoint
global control domain rather than using per-occurrence tag-3 payload streams
to choose their own subjects. Test 28 remains **OPEN**, Test 29 is unchanged
and open, and Test 30 remains **PENDING**. The linked checkpoint-twenty-five
audit records **61/61 focused tests** in 393.02 seconds, **46/46 direct
checkpoint-twenty-four inherited tests** with zero skipped/failed in 749.21
seconds of pytest time (750.06 seconds external wall time), and **54/54 direct
checkpoint-twenty-three inherited tests** with zero skipped/failed in 1,042.33
seconds of pytest time (1,043.18 seconds external wall time). The final
nonduplicative five-suite inherited regression passed **200/200**, with zero
skipped/failed, in 1,564.54 seconds of pytest time (1,565.54 seconds external
wall time); all ten pre/post source and test hashes matched and no files changed.
Its independent disposition is **PASS WITH EXPLICIT SCOPE LIMITS**,
P0=P1=P2=0.
A twenty-sixth checkpoint now supplies the separate law-neutral global
initializer-control namespace that checkpoint twenty-five deliberately left
open. For run ID `r`, initialization index `i`, serialized stage coordinate
`g`, and attempt coordinate `a`, it uses the direct address

\[
\operatorname{key}=(r,7),
\qquad
\operatorname{counter}=(0,i,g,a).
\]

One exact canonical plan contains at most 64 strictly lexicographically
ordered `(stage_index, attempt_index, raw64_word_count)` entries, with at most
4,096 words per stream and 65,536 words in aggregate. The complete plan is
preflighted before any plan-addressed tag-7 control stream or record is
constructed. Plan `()` is a zero-word namespace no-op that creates no such
stream or record and consumes no plan-addressed word; it is not an empty
configuration. Every nonempty record retains exact pre/post Philox snapshots,
replays the prefix in the same runtime, checks no upper-counter carry, and
advances no caller RNG. Reissuing an address replays the same prefix; a longer
request overlaps and extends that prefix rather than continuing from the
earlier post-state.

This checkpoint assigns no meaning to stage or attempt coordinates and defines
no branch/retry chronology, output transform, cardinality/type/coordinate law,
enumeration/rejection/SIR rule, accepted-configuration-to-lineage mapping, or
initializer distribution. Tag 7 separates initialization indices only inside
the new namespace. It does not repair tag 3's omission of that coordinate or
coordinate tag-3 occurrence payloads. Test 28 therefore remains **OPEN**, Test
29 remains open and unchanged, Test 30 remains **PENDING**, and `R2-HYBRID`
remains **NOT RUN**. The checkpoint-twenty-six focused suite passed **45/45**
in 323.22 seconds (323.90 seconds external wall time), and its fresh direct
checkpoint-twenty-five regression passed **61/61**, with zero skipped/failed,
in 389.42 seconds of pytest time (390.14 seconds external wall time). The final
nonduplicative five-suite inherited regression passed **200/200**, with zero
skipped/failed, in 1,707.20 seconds of pytest time (1,708.48 seconds external
wall time); all ten pre/post source and test hashes matched and no files
changed. The independent disposition is **PASS WITH EXPLICIT SCOPE LIMITS**,
P0=P1=P2=0.
A twenty-seventh checkpoint now supplies the fixed initializer-protocol
allocation that checkpoint twenty-six deliberately left open. For a fixed
positive block tuple \(W=(w_0,\ldots,w_{B-1})\), outer work item \(a\), and
block \(b\), it assigns the injective parent attempt coordinate \(aB+b\). Its
canonical strategy plans are

\[
\begin{array}{c|c|c}
\text{strategy} & \text{stage/role} & \text{allocation}\\
\hline
\text{enumeration} & 0/\texttt{enumeration\_selection}
  & ((0,0,s))\\
\text{rejection} & 1/\texttt{rejection\_attempt}
  & ((1,aB+b,w_b))_{a,b}\\
\text{SIR particle} & 2/\texttt{sir\_particle}
  & ((2,jB+b,w_b))_{j,b}\\
\text{SIR selection} & 3/\texttt{sir\_resample}
  & ((3,0,s))\\
\text{reference} & 4/\texttt{reference\_candidate}
  & ((4,b,w_b))_b.
\end{array}
\]

Enumeration has literal budget one, no work-item block tuple, and one positive
selection prefix. Rejection has a positive fixed attempt budget, at least one
positive block per attempt, no separate selection prefix, and materializes
every attempt block in advance. SIR has a positive fixed particle budget, the
same positive block tuple per particle, and one positive stage-3 selection
prefix after every particle block. Reference has literal budget one, one
positive multiblock candidate capsule, and no selection prefix. The inherited
limits remain 64 records, 4,096 words per record, and 65,536 aggregate words.
The advertised 64 rejection attempts and 63 SIR particles are absolute
single-block maxima; multiblock requests reach the record cap sooner. Reissue
replays the same prefixes.

Checkpoint twenty-seven certifies only fixed protocol allocation and complete
parent-prefix materialization. It computes no enumeration support or
normalization, rejection predicate, acceptance, success/failure/fallback, SIR
weight or resampling law, reference law, finite-resolution transform,
cardinality, event, coordinate, configuration, initializer output,
accepted-configuration lineage, or tag-3 payload mapping. Test 28 remains
**OPEN**, Test 29 remains open and unchanged, Test 30 remains **PENDING**, and
`R2-HYBRID` remains **NOT RUN**. Its hash-stable focused suite passed **76/76**
in 197.19 seconds, and independent API/custody, hostile, and law-boundary
reviews report **P0=P1=P2=0**. The disposition is **PASS WITH EXPLICIT SCOPE
LIMITS**. The manuscript source remains unchanged.

A twenty-eighth checkpoint now gives only the fixed-word-budget, no-retry
reference
strategy an ancestry-bound finite-resolution interpretation. For reference cap
\(N\le64\) and maximum fiber dimension \(D\), it consumes the fixed layout

\[
L=1+N+ND,
\]

with one count word, \(N\) contiguous type words, and an \(N\times D\)
row-major coordinate segment. The parent capsule is the canonical greedy
partition of \(L\le65{,}536\) words into blocks of at most 4,096. Every raw
slot's type and all \(D\) coordinates—including inactive slots and
lower-dimensional padding—are transformed before the count word is decoded.
Only the decoded leading prefix becomes active. Canonical sorting uses the
event model key plus raw-slot index and records both directions of the stable
duplicate-safe position map.

Count and type targets are exact rational laws induced by the recorded
binary64 reference parameters. Each is converted to positive Hamilton quotas
over \(2^{64}\), with exact target-to-dyadic TV recorded. A coordinate word
\(w\) uses

\[
j=w\mathbin{\texttt{>>}}11,
\quad r=\min(j,2^{53}-1-j),
\quad p=\frac{2r+1}{2^{54}},
\]

followed by a symmetric lower-tail SciPy `ndtri` evaluation and sign
reflection. The resulting \(\Gamma_{\mathrm{rt}}\) is a runtime-specific finite
codebook, not a Gaussian distribution.

Under an explicitly hypothetical product-uniform word source, the exact
finite pushforward is

\[
Q_{\mathrm{fin}}
=\sum_{n=0}^{N}q_n^C
  (\Sigma_n)_\#(\nu_{\mathrm{fin}}^{\otimes n}),
\qquad
\nu_{\mathrm{fin}}(d,\mathrm d r)
=q_d^T\Gamma_{\mathrm{rt}}^{\otimes k_d}(\mathrm d r).
\]

For canonical finite-support \(x\), with multiplicities \(m_e\),

\[
Q_{\mathrm{fin}}\{x\}
=q_{|x|}^C\frac{|x|!}{\prod_e m_e!}
  \prod_{e\in x}\nu_{\mathrm{fin}}\{e\}.
\]

Actual counter-keyed Philox words are deterministic and procedural only; no
uniformity, independence, or physical-randomness claim is made. A finite
coordinate marginal and a Gaussian have TV one. Whenever a positive-
dimensional sector has positive mass under both configuration laws, their
conditional laws on that sector also have TV one. The unconditional
configuration TV is not generally one because empty and zero-dimensional
configurations can overlap.
If every type is positive-dimensional, it is
\(1-\min(q_0,p_0)\), where \(q_0\) and \(p_0\) are the finite and target empty
masses. No weak or Wasserstein bound is certified.

The checkpoint also bounds exact-rational work at 131,072 bits per integer and
16,777,216 aggregate bits, uses canonical hexadecimal digest projections for
large ratio integers, and deeply replays its manifest, raw slots, result, and
checkpoint-twenty-seven parent. The frozen source and focused-test SHA-256
values are
`69a05b843b32b542e6a3d291d7fa55e3d79fbde46bc394cc010637ce18f2bde4`
and
`8df4e6078e948a17f6ba2fb7fe8c82f8a05201fa73b3be8ac48911d48f1ec026`.
Its hash-stable focused suite passed **58/58** in 259.68 seconds of pytest time
(260.30 seconds external wall time); a fresh exact checkpoint-twenty-seven
parent regression passed **76/76** in 214.96 seconds of pytest time
(215.54 seconds external wall time). Independent final reviews report
**P0=P1=P2=0**. Test 28 nevertheless remains **OPEN**: checkpoint 29 supplies
only the narrow fixed reference-transform diagnostic described next, while the
cumulative stack has only scoped all-atomic enumeration and finite-rejection
precursors. A complete general initializer law, SIR semantics, an empirical
benchmark for a general conditional or tilted initializer, initializer
admission, and accepted-configuration lineage/tag-3 coordination remain absent.
Test 29 remains
open and unchanged, Test 30 remains **PENDING**, and `R2-HYBRID` remains
**NOT RUN**. The manuscript source remains unchanged.

A twenty-ninth checkpoint preregistered and completed one sole, bounded
engineering diagnostic of that finite reference transformer. Two frozen
deterministic grids each contained 16,384 addresses: an atomic cap-two fixture
and a positive-dimensional cap-one fixture. All five prespecified exact
statistics—atomic configuration TV, continuous count TV, continuous raw-slot
type TV, maximum top-53 coordinate CDF discrepancy, and maximum top-4 pair
TV—fell within their frozen envelopes derived under the hypothetical i.i.d.
product-uniform word model. The exact terminal status is `PASS`; the one-shot
attempt is spent, its failure/deviation/exclusion/retry/rerun lists are empty,
and independent scientific recomputation and custody audits both report
**P0=P1=P2=0**. The
execution audit
records the exact ratios, thresholds, margins, artifacts, hashes, runtime,
and STARTED-v2/terminal-v2 custody chain.

This is nonconfirmatory engineering evidence `E29-REF`, not a scientific or
generality result. It certifies no Philox uniformity, independence, or
randomness; no \(Q_{\mathrm{fin}}\) sampling law; no continuous reference law;
and no general initializer admission. Formal Test 28 remains **OPEN**, Formal
Test 29 remains **OPEN**, Test 30 remains **PENDING**, and `R2-HYBRID` remains
**NOT RUN**. No claim row or confirmatory result slot is promoted. No Gaussian
TV experiment was run because the finite codebook and a continuous Gaussian
already have TV one on a positive-dimensional realized type.

A thirtieth checkpoint now supplies the separate deterministic time-zero
operational log-factor prerequisite documented in its
incremental audit. For the
selected base initial law \(\rho_0^\phi=\Pi_N\), one canonical configuration
\(x\), and one explicit residual context \(c\), it computes

\[
L_{\mathrm{init},\mathbb Q}^{\mathrm{op}}(x;c)
=\iota\!\left(G_{64}^{\mathrm{totalized}}(0,x)\right)
+\iota\!\left(R_{64}^{\mathrm{totalized}}(S,x,c)\right)
\]

as an exact sum of the represented binary64 component values and rounds the
aggregate once to nearest-even binary64. The learned base energy
\(V_\phi(S,x)\) is intentionally excluded because the base law is already
\(\Pi_N\). The sealed point record binds the process-owned reference, guide,
residual, endpoint orientation, context, transitive certificates, and a
directed interval derived from the guide interval and residual bound. Its
process-instance identities and hashes are same-process procedural custody
witnesses under a trusted, unmodified runtime, not cross-run semantic or
loaded-code authentication; the residual conditioner-adapter origin is not
authenticated.

The frozen checkpoint-thirty source/test SHA-256 values are
`b3436037b7e3a0eff00cc06564b18a77026f9024948432259b505a3f4a6b1adc`
and
`d2fa142b08b8118fb06c52acb40e0d3fae3d9ad18397b2d98725f1db7f02115d`.
The focused warnings-as-errors suite passed **37/37** in 99.16 seconds. A
separate inherited parent selection passed **175/175** in 111.26 seconds; these
are not represented as one combined run. Independent final reviews report
**P0=P1=P2=0**. This is software evidence for one deterministic log-space
point contract, not a trained-model, conditional-generation, distributional,
or generality result. Formal Test 28 remains **OPEN**, Formal Test 29 remains
**OPEN**, Test 30 remains **PENDING**, and `R2-HYBRID` remains **NOT RUN**. No
claim row or confirmatory result slot is promoted. Exact bounded all-atomic
support enumeration was the next prerequisite; positive-dimensional Gaussian
support remains non-enumerable, and checkpoint twenty-eight's finite codebook
is singular with respect to it.

A thirty-first checkpoint now supplies that prerequisite only for the exact
bounded **all-atomic** case, as documented in its
incremental audit.
For increasing process-owned type identifiers \((d_1,\ldots,d_K)\), it lifts
the stored activity and raw type weights to exact rationals,

\[
a=\iota(\vartheta_{64}),\qquad
r_j=\iota(w_{d_j,64}),\qquad
p_j=\frac{r_j}{\sum_k r_k},
\]

and, for every canonical count vector \(m\) with \(|m|\le N\), records the
unnormalized represented-parameter base coefficient

\[
b_{\mathbb Q}(m)
=a^{|m|}\prod_j\frac{p_j^{m_j}}{m_j!}.
\]

There is no additional \(|m|!\) factor. States are ordered by increasing
cardinality and then lexicographically, with type IDs in increasing order.
The implementation verifies the local factorial recurrence, every exact
cardinality subtotal \(a^n/n!\), and
\(\sum_m b_{\mathbb Q}(m)=Z_N(a)=\sum_{n=0}^N a^n/n!\). It stores this
normalizer only as a completeness witness and does not materialize normalized
base masses.

The frozen resource boundary is \(1\le K\le64\), \(0\le N\le255\),
\(\binom{N+K}{K}\le256\) states, and
\(K\binom{N+K}{K+1}\le32{,}640\) emitted occurrences. Each exact numerator
and denominator is limited to 8,192 bits and the defined aggregate exact-
rational bit witness to 8,388,608 bits. That witness counts each conceptual
rational in the frozen formula once; it is not a Python-memory ceiling.
Eligibility, support, coefficients, and these
resource checks complete before the first checkpoint-thirty point callback;
then one replay-validated checkpoint-thirty point is attached to every state.
Any positive-dimensional type refuses the entire reference, even at cap zero.

The frozen checkpoint-thirty-one source/test SHA-256 values are
`26d55b5777654c4bdaa575ac22a1d7a5b34ac06e06e5f604de6acb5ecb3e6076` and
`689561207ab367273115eaceecd2e2ce581d4a586ebeb09148e147d246ac4ec7`.
The focused evidence is `42 passed in 301.86 seconds`; the separately executed
inherited-parent and adjacent-protocol-boundary selection is
`149 passed in 327.07 seconds`. This remains software
evidence for exact finite
support/coefficient enumeration, not a trained-model, conditional-generation,
distributional, or generality result. No normalized masses, point-factor
exponentiation, tilted normalization, categorical selection, rejection, SIR,
RNG, initializer output, continuous codebook, path, or sampler is supplied.
Checkpoint twenty-seven stage 0 remains a separate unconsumed allocation.
Formal Test 28 remains **OPEN**, Formal Test 29 remains **OPEN**, Test 30
remains **PENDING**, and `R2-HYBRID` remains **NOT RUN**. No claim row or
confirmatory result slot is promoted.

A thirty-second checkpoint now constructs the next dependency for a successful
checkpoint-thirty-one all-atomic enumeration, as documented in its
incremental audit.
For exact parent coefficients \(b_i\) and checkpoint-thirty exact represented-
component sums \(q_i\), it defines the ideal operational law

\[
P_i=\frac{b_i e^{q_i}}{\sum_k b_k e^{q_k}}.
\]

After maximum-log centering, adaptive directed Decimal intervals enclose every
weight and normalized ideal mass. The exact-rational normalized midpoint proxy
\(\widetilde P\) must satisfy a recorded ideal-to-proxy TV bound at most
\(2^{-96}\). A positive Hamilton allocation over \(2^{64}\) quotas, with
canonical ordinal ties, yields the exact dyadic law \(Q\); the recorded
triangle bound requires \(\operatorname{TV}(P,Q)\le2^{-48}\). One explicit
exact Python integer in \(0,2^{64})\) is then mapped through the complete
half-open cumulative quota table.

The checkpoint uses checkpoint thirty's exact rational component sum, not its
rounded display float. It caps support at 256 states, centered-log magnitude at
10,000, each exact integer at 131,072 bits, and the defined aggregate rational
witness at 16,777,216 bits; unresolved enclosure precision through 1,536
digits and excessive exact work fail closed. Every public operation performs
bounded transitive replay and terminal mutation checks.

The frozen checkpoint-thirty-two source/test SHA-256 values are
`19cd92cce71cd4a43a5ecc659b1616d4600f8874e34ec6ba7238f3bccd05f189` and
`f8ec145d717db1abb275a167e3fa55b3b668defdc0b7cdf3fa959f357b7ef17a`.
The focused evidence is `62 passed in 371.07 seconds`; the separately executed
inherited-parent and adjacent-boundary selection is
`249 passed in 878.48 seconds`. Independent numerical, source,
and custody reviews report **P0=P1=P2=0**. This is software evidence for a
finite-resolution operational law under an explicit-word interface, not
evidence that the word is uniform or independent, not exact sampling from the
transcendental ideal law, and not a trained-model, conditional-generation, or
generality result. At checkpoint thirty-two itself, checkpoint twenty-seven
stage 0 was still unbound. Formal
Test 28 remains **OPEN**, Formal Test 29 remains **OPEN**, Test 30 remains
**PENDING**, and `R2-HYBRID` remains **NOT RUN**. No claim row or confirmatory
result slot is promoted.

A thirty-third checkpoint now closes the narrow stage-0 binding dependency, as
documented in its
incremental audit.
For exact unsigned run \(r\) and initialization index \(i\), it asks the exact
checkpoint-twenty-seven owner for

```text
strategy = enumeration
strategy_budget = 1
work_item_raw64_word_counts = ()
selection_raw64_word_count = 1
```

and therefore materializes the sole plan `((0,0,1),)` at

\[
\operatorname{key}=(r,7),
\qquad
\operatorname{counter}=(0,i,0,0).
\]

The bridge first replays the caller-supplied checkpoint-thirty-two preparation,
requires the two parent stacks to share the exact reference composer, guide,
and residual, validates the complete protocol result, and forwards the sole
parent word unchanged to checkpoint thirty-two. The returned result retains the
exact parent protocol result, entry, address, raw-word tuple, preparation,
selection, selected row, count vector, configuration, dyadic quota interval,
and inherited ideal-to-dyadic TV witness.

For any fixed checkpoint-thirty-two preparation \(p\), let \(f_p\) be its
deterministic uint64 lookup. If the live word source is replaced by a separate
abstract source

\[
U\sim\operatorname{Uniform}(\{0,\ldots,2^{64}-1\}),
\]

then \(f_p(U)\sim Q_p^{\mathrm{dyadic}}\), checkpoint thirty-two's dyadic law.
This pushforward conclusion is counterfactual: the abstract source \(U\) is not
identified with the live checkpoint-thirty-three word source, although their
realized uint64 values may coincide. Separately, the fixed preparation already
certifies
\(\operatorname{TV}(P_p^{\mathrm{operational}},
Q_p^{\mathrm{dyadic}})\le2^{-48}\). For every fixed live address \((r,i)\), both the
Philox word and \(f_p\) output are deterministic point masses. The checkpoint
therefore certifies neither a live output distribution nor actual Philox
uniformity, independence, or randomness, and it does not sample the analytic
target exactly. It accepts no caller RNG, creates no second RNG namespace, and
has no retry or fallback; it is not correct to call it a no-RNG checkpoint
because the inherited tag-7 parent materializes one word.

The frozen checkpoint-thirty-three source/test SHA-256 values are
`cef3ccb8f1dc786142a4d3bbd8f9b358c038f936c8c1b52fabfc2c633aa82e64` and
`8a4218469ad135738e4e94398061747a417c734a38cfc1a51983092ed21d7c6c`.
Its focused evidence is `57 passed in 1079.17 seconds`; the inherited checkpoint-
twenty-seven, checkpoint-thirty-two, and checkpoint-thirty-three regression is
`195 passed in 1569.17 seconds`. Independent source and test audits report
**P0=P1=P2=0**. This remains scoped software evidence for one protocol-bound
finite-resolution all-atomic selection. It does not admit an initializer,
support mixed/continuous states, implement rejection/SIR/reference strategies,
coordinate lineage or tag-3 payloads, or construct drift, a path, or a sampler.
Formal Test 28 remains **OPEN**, Formal Test 29 remains **OPEN**, Test 30 remains
**PENDING**, and `R2-HYBRID` remains **NOT RUN**. No claim row or confirmatory
result slot is promoted.

A thirty-fourth checkpoint now supplies a fixed live all-atomic initial-state
configuration constructor, as documented in its
incremental audit.
Its factory canonically owns the context, materializes checkpoint thirty-one
enumeration and checkpoint thirty-two preparation exactly once each, performs
their initial direct validations, and binds the exact checkpoint-thirty-three
selection owner. Later custody checks may revalidate these fixed objects but do
not rematerialize them. The live API then exposes only
`initialize(run_id, initialization_index)` and
`validate_result(result, run_id, initialization_index)`. Each
successful initialization uses exactly one parent tag-7 word at key
`(run_id, 7)` and counter `(0, initialization_index, 0, 0)`, with no per-call caller context,
preparation, RNG, or word; no added RNG namespace, retry, or fallback exists.
The returned all-atomic configuration is valid as an initial state, and replay
at the same address is exact and deterministic rather than a fresh draw.

The only positive output/pushforward-law theorem is counterfactual. For fixed
preparation \(p\),
substitute an abstract ideal
\(U\sim\operatorname{Uniform}(\{0,\ldots,2^{64}-1\})\) into the deterministic
lookup \(f_p\); then \(f_p(U)\sim Q_p^{\mathrm{dyadic}}\).
Independently of the abstract-\(U\) premise, the fixed preparation carries the
separate inherited TV witness

\[
\operatorname{TV}(P_p^{\mathrm{operational}},
Q_p^{\mathrm{dyadic}})\le2^{-48}.
\]

Here the source \(U\) is not identified with the live parent word source,
although their realized uint64 values may coincide. Meanwhile,
\(P_p^{\mathrm{operational}}\) is the
ideal operational-surrogate law, not an analytic conditional or posterior
target. A fixed live address yields deterministic word and output point masses.
Consequently the certificate fields for actual word uniformity, independence,
product law, and physical randomness are false. A live output law is not
certified; `live_initializer_distribution_admitted`, `initializer_admissible`,
and `general_initializer_admissible` are false, and mixed/continuous
initialization is unsupported. The module and audit retain `admission` in their
names only as the historical checkpoint label.

The frozen checkpoint-thirty-four source/test SHA-256 values are
`e8e7dee2a1773fbc836b920c4289a1c1b555698f2f07e5c62d3b3ffb2ee423a1` and
`98a864e9119f6c78b33c1380bf7e7904b70f9ffbfd76edaccb06db8703a742c3`.
Its focused evidence is `65/65 passed in 1186.81 seconds`; the inherited checkpoint-
thirty-one through checkpoint-thirty-four regression is
`226/226 passed in 3178.43 seconds`. Independent final reviews report
**P0=P1=P2=0**. Formal Test 28 remains **OPEN**, Formal Test 29 remains **OPEN**,
Test 30 remains **PENDING**, and `R2-HYBRID` remains **NOT RUN**. No C-row,
R-slot, nonconfirmatory-evidence row, novelty decision, scientific or model-
quality result, generality statement, or manuscript conclusion is promoted.
The venue-neutral TeX manuscript is intentionally untouched at this checkpoint.

A thirty-fifth checkpoint now supplies a bounded finite mixed reference
configuration constructor with bootstrap lineage and occurrence-local tag-3
prefix custody, as documented in its
incremental audit.
The live operation accepts only `initialize(run_id)`: initialization index is
fixed to zero. It invokes checkpoint twenty-eight's finite tag-7 reference
transform, queries the process-owned reference intensity at reverse time
positive zero, maps canonical occurrence position \(j\) to checkpoint-twenty-
three initial lineage serial \(j+1\), and asks checkpoint twenty-five to
consume exactly

\[
c_j=\max(1,d_j)
\]

uninterpreted tag-3 words for event dimension \(d_j\). The empty configuration
uses no tag-3 stream. The returned configuration is the exact CP28 canonical
configuration, and lineage occurrences and tag-3 records preserve its event
identities. Validation replay does not invoke another CP28 initialization or
CP25 consumption. Reusing one `run_id` is exact deterministic replay, not a
fresh draw.

For one fixed manifest \(m\), let \(F_m\) be the complete CP28 finite
configuration transform and \(L_m\) its complete tag-7 word budget. Only after
replacing that complete live capsule by a separate abstract vector

\[
U=(U_0,\ldots,U_{L_m-1}),
\qquad
U_\ell\overset{\mathrm{iid}}{\sim}
\operatorname{Unif}\{0,\ldots,2^{64}-1\},
\]

does the finite counting identity give

\[
F_m(U)\sim Q_{\mathrm{fin},m}.
\]

This theorem concerns only the configuration component. It does not describe
the live NumPy Philox words, the tag-3 words, lineage, or the complete CP35
result. Writing \(\delta_N=\operatorname{TV}(p_N,q_N)\) for the exact count-
law dyadic discrepancy and \(\delta_A=\operatorname{TV}(p_A,q_A)\) for the
type-law discrepancy, the structural projection has the exact-rational upper
witness

\[
\min\!\left\{
1,
\delta_N+\sum_n p_N(n)\left[1-(1-\delta_A)^n\right]
\right\}.
\]

This is an upper bound obtained by product coupling and data processing, not
an asserted equality. Conditional on any structural cell with positive
probability under both laws and positive total active coordinate dimension,
CP28's finite 53-bit midpoint codebook and the corresponding analytic Gaussian
fiber have TV one.
That conditional singularity does not imply unconditional full-configuration
TV one.

Tag-7 block addresses use key `(run_id, 7)` and counters
`(0, 0, 4, block_index)`. Tag-3 occurrence serial \(s\) uses key
`(run_id, 3)` and counter `(0, 0, s, 0)`. The tags are disjoint, but the tag-3
address omits initialization index. Fixing index zero avoids an immediate
collision inside CP35; it does **not** certify tag-3 cross-initialization
disjointness for a future multi-index initializer.

The frozen checkpoint-thirty-five source/test SHA-256 values are
`f8d20a73e5fe0bd728182636c7235532433ec477e130dce4cc026e967869b768` and
`8a633c1033ad6c4dde25ee5e174e3ed9592cb8eb9320835bcc1d9f90cb11acde`.
The focused suite passed **64/64 with warnings-as-errors in 998.81 seconds**.
The no-cache direct-parent checkpoint-23/checkpoint-25/checkpoint-28 regression
passed **173/173**, with 0 failed/errors/skips/xfail/xpass and no warnings,
under warnings-as-errors in **1251.19 seconds (0:20:51)**. All involved hashes
remained unchanged. The disposition is **PASS WITH EXPLICIT SCOPE LIMITS**.
Formal Test 28 remains **OPEN**, Formal Test 29 remains
**OPEN**, Test 30 remains **PENDING**, and `R2-HYBRID` remains **NOT RUN**.
No C-row, R-slot, nonconfirmatory-evidence row, novelty decision, scientific
or model-quality result, generality statement, or manuscript conclusion is
promoted. The venue-neutral TeX manuscript remains untouched.

A thirty-sixth checkpoint now supplies fixed-budget rejection-attempt proposal
and point-score preparation, as documented in its
incremental audit.
For a frozen attempt budget \(A\), let \(B\) and \(L\) be checkpoint twenty-
eight's reference-block and proposal-word counts. Every attempt contains the
exact \(B\)-block, \(L\)-word CP28 proposal layout followed by one reserved
one-word block. Checkpoint twenty-seven first materializes all
\(A(B+1)\) records. CP36 then materializes and validates every CP28 slot's
transformed fields before count decode, constructs and validates the final
activity-bearing slot records, forms the duplicate-stable canonical candidate,
obtains checkpoint thirty's exact represented score \(q\), and records the
reduced rational witness \(q-U\le0\) against the frozen exact global upper
bound \(U\).

For attempt \(a\), block \(b\), and raw-word offset \(o\), the full logical word
coordinate has key `(run_id, 7)`, counter
`(0, initialization_index, 1, a*(B+1)+b)`, and separate offset \(o\). The
reserved block is \(b=B\) and has length one. The resource contract is

\[
A\le\min\!\left\{
64,
\left\lfloor\frac{64}{B+1}\right\rfloor,
\left\lfloor\frac{65536}{L+1}\right\rfloor
\right\}.
\]

The reserved word is stored but never converted, exponentiated, compared, or
used to decide or select an attempt. The only probabilistic theorem replaces
the distinct full logical coordinates by a separate abstract iid-uniform
uint64 family and totalizes the deterministic operation into
`Success(abstract preparation batch)` disjoint-unioned with `Failure`. It gives
only data processing,
\(\operatorname{TV}(F_{\#}\nu,F_{\#}U)\le\operatorname{TV}(\nu,U)\), and a
conditional triangle ledger if a separate source approximation is supplied.
It gives no failure probability, success-conditional law, live Philox law,
acceptance, selection, initializer law or admission, lineage/tag-3
coordination, Brownian coupling, drift, path, or sampler.

The frozen checkpoint-thirty-six source/test SHA-256 values are
`fd87881c04801510e74edde8676583d7068b387c3e091adeba8732f6b6ce4b59` and
`8a7469dc18ab47c3b2dde1a3a8eeeb86c7764709a511b1b2ed105dd081d1ceeb`.
The focused suite collected 115 tests and passed **115/115** with 0 failed, 0
skipped, and no warnings under warnings-as-errors in **1455.63 seconds
(0:24:15)** of pytest time and **1456.13 seconds** external wall time. The
no-cache parent regression passed **171/171** with 0 failed, 0 skipped, and no
warnings under warnings-as-errors in **485.58 seconds (0:08:05)** of pytest
time and **486.19 seconds** external wall time. The disposition is **PASS WITH
EXPLICIT SCOPE LIMITS**. Formal Tests 28 and 29 remain **OPEN**, Test 30
remains **PENDING**, and `R2-HYBRID` remains **NOT RUN**. No claim or result
slot is promoted, and the venue-neutral TeX manuscript remains untouched.

A thirty-seventh checkpoint now applies the finite-resolution rejection rule
documented in its
incremental audit.
For the exact CP36 gap \(\delta_a=q_a-U\le0\), let

\[
D=2^{64},\qquad K_a=\left\lfloor D e^{\delta_a}\right\rfloor .
\]

CP37 certifies every quota before the first semantic decision comparison, then
accepts attempt \(a\) exactly when its inherited word satisfies \(w_a<K_a\).
Threshold preflight may read a reserved word to validate its exact type and
uint64 range, but no word is compared with a quota until the complete threshold
tuple exists. The first accepted attempt selects its exact CP36 configuration;
if all attempts reject, `exhausted` is a valid bounded outcome. Validation or
numerical-certification failure raises and returns no result; it is never
reported as exhaustion. Later CP36 words remain materialized but semantically
uninterpreted after an earlier selection.

The quota branches are exact on CP36's dyadic domain: \(K=D\) at \(\delta=0\),
\(K=0\) at \(\delta\le-64\), \(K=D-1\) for
\(-2^{-64}<\delta<0\), and otherwise an adaptive 192/384/768/1536/3072-digit
Decimal enclosure identifies the unique scaled floor. Thus

\[
0\le e^{\delta_a}-K_a/D<2^{-64}.
\]

For fixed proposal/score data that exclude the realized reserved words and a
separate abstract iid-uniform uint64 family, \(p_a=K_a/D\) gives
\(\Pr(J=j)=p_j\prod_{i<j}(1-p_i)\) and
\(\Pr(\mathrm{Exhausted})=\prod_i(1-p_i)\). For the corresponding fixed-data
comparison between independent-coordinate ideal and dyadic Bernoulli
sequences, a common-uniform coupling bounds the first-index-or-exhaustion law's
total-variation discrepancy strictly below \(A/2^{64}\).
These are not laws conditional on the complete CP36 record, a live Philox law,
or an exact ideal-rejection/normalized-tilt theorem. At a fixed live address,
the inherited words and CP37 result are deterministic replay.

The frozen checkpoint-thirty-seven source/test SHA-256 values are
`acbe2bd14305560360ec40595314a19a66f37ceec22d4e22321c05f14d050fed` and
`ea255cc36ee17c20b355e237fd5a87de89bd9458ef42f5b850124b14f6b49f91`.
The focused suite passed **44/44** in **423.78 seconds** of pytest time and
**424.30 seconds** external wall time; its log SHA-256 is
`b83af9ebf878c198916d5b5e6737478dfcfa80e53f64bc26f75b236d21058579`.
The no-cache CP36 direct-parent regression passed **115/115** in **1777.84
seconds (0:29:37)** of pytest time and **1778.76 seconds** external wall time;
its log SHA-256 is
`3c9266f00e96da99850d343ccc137bf1a09bd68546852486391abad9bba744d4`.
Neither log reports a failure, skip, or warning. The disposition is **PASS WITH
EXPLICIT SCOPE LIMITS**. Formal Tests 28 and 29 remain **OPEN**, Test 30 remains
**PENDING**, and `R2-HYBRID` remains **NOT RUN**. No claim, initializer
admission, result slot, or manuscript conclusion is promoted, and the venue-
neutral TeX manuscript remains untouched.

A thirty-eighth checkpoint now materializes the exact finite-batch
counterfactual law documented in its
incremental audit.
It conditions only on the direct word-free projection
\(B=((j,x_j,\delta_j,K_j))_{j=0}^{A-1}\), which excludes reserved decision
words, decisions, the realized outcome, and parent digests that indirectly
bind those words. With \(D=2^{64}\), \(p_j=K_j/D\), and a separate abstract
iid-uniform uint64 word family independent of \(B\), it records

\[
\Pr(J=j\mid B)=p_j\prod_{i<j}(1-p_i),\qquad
\Pr(E\mid B)=\prod_i(1-p_i).
\]

Structurally equal canonical candidates are aggregated as
\(m_B(x)=\sum_{j:x_j=x}\Pr(J=j\mid B)\). The selected-configuration law
\(m_B(x)/Z_B\), where \(Z_B=1-\Pr(E\mid B)\), is defined only when \(Z_B>0\).
If all quotas vanish, \(Z_B=0\), exhaustion has mass one, and every optional
selected-conditioned mass is absent. The augmented law always normalizes.

Separately, independent continuous common uniforms couple the ideal
\(e^{\delta_j}\) and dyadic \(p_j\) decisions. Data processing through the
first-selected-configuration-or-exhaustion map gives the strict fixed-\(B\)
bound

\[
\operatorname{TV}\!\left(
  \mathcal L_B(X_{\mathrm{dyadic}}\sqcup E),
  \mathcal L_B(X_{\mathrm{ideal}}\sqcup E)
\right)<\frac{A}{2^{64}}.
\]

This is an augmented, pre-selection-conditioning comparison. CP38 itself does
not directly reuse it unchanged for the law conditional on selection. The live
CP37/CP38 outcome at a fixed address remains deterministic replay and is not a
draw from the
counterfactual law. A selected configuration is certified only as
structurally valid for one operational initial state; generic
`initializer_admissible` remains false. Lineage and tag-3 attachment remain
deferred because their current namespace does not distinguish every
initialization index under one run. The conditioning digest is streamed with
explicit framing and enforces the 64-attempt, 64-event-per-configuration, and
65,536-coordinate-per-event caps.

Checkpoint-thirty-eight is frozen at source SHA-256
`5614c0f79dc318d2a19b920d1a787056f153cbf4dc2b7b4da2bd0cd65592b627`
and focused-test SHA-256
`97d4752b00e119a9ff8011e38500ff2de2efa2738791244fbca3d15680188184`.
The no-cache, warnings-as-errors focused suite passed 45/45 in 681.48 seconds,
and the no-cache, warnings-as-errors CP37 direct-parent regression passed
44/44 in 428.82 seconds.
Static gates and the independent source audit passed; the disposition is
**PASS WITH EXPLICIT SCOPE LIMITS**. Formal Tests 28 and 29 remain **OPEN**,
Test 30 remains **PENDING**, and `R2-HYBRID` remains **NOT RUN**. No claim,
initializer admission, result slot, evidence row, or manuscript conclusion is
promoted, and the venue-neutral TeX manuscript remains untouched.

A thirty-ninth checkpoint now adds construction-time selected-state lineage
and initialization-indexed local tag-3 coordination, as documented in its
incremental audit.
For run \(r\) and initialization index \(i\), it calls the exact CP38
`resolve(r, i)` once. If CP38 selects exact CP37 attempt \(a\) and exact
configuration \(x=(e_0,\ldots,e_{n-1})\), CP39 queries the process-owned
reference intensity at reverse time zero and constructs CP23 positional
bootstrap lineage. Canonical position \(j\) retains the exact selected event
and maps to serial \(j+1\), origin initialization \(i\), and origin position
\(j\). It is not replaced by a CP38 duplicate-aggregation representative or
ordinal.

For the occurrence at position \(j\), CP39 constructs its own address and
prefix:

\[
\operatorname{key}=(r,3),\qquad
\operatorname{counter}=(0,i,j+1,a+1),\qquad
N_j=\max(1,d_j),
\]

where \(d_j\) is the checkpoint-twenty-eight manifest dimension of \(e_j\).
The positive final limb is disjoint from valid legacy tag-3 initializer
addresses whose final limb is zero. This is a local address-layout statement,
not global run-ID uniqueness, one-shot use, cross-bootstrap merge safety,
lineage-fork prevention, or statistical independence. CP39 uses its own
address and stream records; it neither forges a CP23 address DTO nor invokes
CP25 initializer-stream consumption. Each raw64 prefix retains exact initial
and final Philox snapshots, exact words, no upper-counter carry, and same-
runtime replay. The words are uninterpreted shape metadata and do not generate,
alter, or explain selected coordinates.

A selected empty configuration remains selected: it retains its exact empty
configuration, reverse-time-zero intensity, and present empty lineage, with no
local stream. Exhaustion instead retains no selected attempt, configuration,
intensity, lineage, address, stream, occurrence, or prefix. The exhausted
branch invokes no selected-branch composer preflight, CP23 bootstrap, or CP39
result address/stream/occurrence construction; certification and live-binding
Philox probes remain separate procedural checks. Validation does not call
CP38 `resolve`, CP23 bootstrap, or CP39 child constructors. It does recompute
the deterministic composer preflight through intensity validation and replay
every stored selected-branch stream.

The fixed caps are 64 occurrence records, 4,096 raw64 words per occurrence,
and 65,536 raw64 words in aggregate. Same-address behavior is deterministic
replay, not a fresh draw. CP39 supplies no Philox law, semantic tag-3 payload,
coordinate-generation law, live initializer distribution, generic initializer
admission, selected-conditioned reuse of CP38's ideal/dyadic TV comparison,
normalized tilted law, Brownian consumption, drift, path, liveness, or sampler.

The final evidence record fixes source SHA-256
`d9851ab3a0ab68e8d748db497c386264f26e42e4131cd679c4282a4a609a65ac`
and focused-test SHA-256
`4d7c0c763b874717a47697c160670e9d68343ae780c77bffe861cb50eb8673da`.
The no-cache, warnings-as-errors focused suite passed 65/65 in 2,983.10
seconds of pytest time and 2,983.75 seconds of external wall time. The direct
CP38 parent source/test identities remain
`5614c0f79dc318d2a19b920d1a787056f153cbf4dc2b7b4da2bd0cd65592b627`
and
`97d4752b00e119a9ff8011e38500ff2de2efa2738791244fbca3d15680188184`;
its no-cache, warnings-as-errors regression passed 45/45 in 789.66 seconds of
pytest time and 790.13 seconds of external wall time. Static gates and the
independent final source, hostile-test, and documentation reviews returned
**P0=P1=P2=0**. The CP39 audit status is **PASS WITH EXPLICIT SCOPE LIMITS**.
Formal Tests 28 and 29 remain **OPEN**, Test 30 remains **PENDING**, and
`R2-HYBRID` remains
**NOT RUN**. No claim, initializer admission, result slot, evidence row, or
manuscript conclusion is promoted, and the venue-neutral TeX manuscript
remains untouched.

A fortieth checkpoint now adds the explicit finite-resolution rejection target
and narrow downstream state-admission boundary documented in its
incremental audit.
It accepts only one exact CP39 owner and invokes `coordinate(r,i)` exactly once.
For the embedded CP38 direct word-free successful batch

\[
B=\bigl((j,x_j,\delta_j,K_j)\bigr)_{j=0}^{A-1},
\qquad D=2^{64},\qquad p_j=K_j/D,
\]

it retains the exact duplicate-aggregated masses

\[
\alpha_j=p_j\prod_{k<j}(1-p_k),\qquad
m_B(x)=\sum_{j:x_j=x}\alpha_j,
\qquad e_B=\prod_j(1-p_j),\qquad Z_B=1-e_B,
\]

and defines the always-normalized augmented target

\[
Q_B^{\mathrm{aug}}
=\sum_xm_B(x)\delta_x+e_B\delta_{\bot_E}.
\]

If and only if \(Z_B>0\), it also defines

\[
Q_B^{\mathrm{sel}}(x)=m_B(x)/Z_B.
\]

Conservative quotas give ideal selection mass \(Z_B^\star\ge Z_B\). Combining
the conditioning-stability inequality with CP38's strict augmented comparison
therefore gives

\[
\operatorname{TV}(P_B^{\mathrm{sel}},Q_B^{\mathrm{sel}})
<\frac{2A}{2^{64}Z_B}
\qquad (Z_B>0).
\]

CP40 records the exact raw rational on the right as a strict upper bound and
records its clipping at one only as a non-strict display bound. The clipped
bound is nonvacuous exactly when the raw rational is below one; all comparison
numeric values are absent and the corresponding definition, strictness, and
nonvacuity flags are false when \(Z_B=0\), while fixed comparison/proof
metadata remains present.

On selection, including selected-empty, the exact CP39 configuration,
intensity, lineage, and occurrence payloads are retained by identity and the
state crosses only this declared fixed-\(B\) downstream structural boundary.
The CP38 target row is selected by the parent's configuration ordinal and is a
mass witness only; its stable duplicate representative never replaces the
actual selected CP39 object. On exhaustion, the target remains present but all
state, intensity, lineage, occurrence, and stream fields are absent. Parent,
validation, or construction failure returns no CP40 record and is never
relabeled as exhaustion.

The target requires one successfully materialized CP36 batch and CP38's
separate abstract iid decision-word premise. The live fixed-address result is
deterministic replay, not a target draw. CP40 supplies no live word or
initializer law, unconditional CP36 batch or failure law, exact ideal
rejection, global normalized tilt, all-strategy general initializer, semantic
tag-3 coordinate generation, Brownian consumption, drift, path, liveness, or
sampler.

Checkpoint forty is frozen at source SHA-256
`1d92574611498aeed62cd16bb232ef22f95b365b689b5351219e0539e0e6b115`
and focused-test SHA-256
`30b5f93413b8c5448d85a1b7f768da5b394143d363061db418f5847272c80305`.
The focused suite contains 45 collected tests. Its final result is
**45/45 passed** in **3908.56** seconds of pytest time and **3909.19** seconds
external wall time.
The frozen direct-parent CP39 source/test identities are
`d9851ab3a0ab68e8d748db497c386264f26e42e4131cd679c4282a4a609a65ac`
and
`4d7c0c763b874717a47697c160670e9d68343ae780c77bffe861cb50eb8673da`;
an inherited no-cache, warnings-as-errors regression of that exact frozen pair
passed **65/65** in **2983.10** seconds of pytest time and **2983.75** seconds
external wall time. CP39 was not freshly rerun for CP40. Static gates passed,
and independent final read-only source, hostile-test, and documentation audits
returned **P0=P1=P2=0**. The read-only audits do not substitute for execution.
The CP40 focused execution passed, and the unchanged CP39 pair is covered by
the inherited exact-hash regression evidence above. CP40 is **PASS WITH
EXPLICIT SCOPE LIMITS**.
Formal Tests 28 and 29 remain **OPEN**, Test 30 remains **PENDING**, and
`R2-HYBRID` remains **NOT RUN**. No C-row, R-slot, nonconfirmatory-evidence row,
novelty decision, scientific/model-quality result, generality statement, or
manuscript conclusion is promoted, and the venue-neutral TeX manuscript
remains untouched.

A forty-first checkpoint now records the
[failure-aware abstract rejection source law](plugin_bridge_counter_keyed_initial_tilt_rejection_failure_aware_source_law_code_audit.md).
It is exactly an **abstract product-uniform failure-aware source law
conditional on an explicit unproved factorization hypothesis**. With
\(D=2^{64}\), it partitions CP36's normalized coordinates into
\(V\in[D]^M\) for proposal/scoring and \(W\in[D]^A\) for one reserved decision
word per attempt. The separate hypothesis says the word-free preparation
success/failure projection and complete quota tuple depend only on \(V\);
CP36--CP40 motivate but do not prove that noninterference.

The symbolic predecision map distinguishes preparation failure \(F_{36}\),
quota-certification failure \(F_{37}\), and successful word-free batches \(B\).
With symbolic product-uniform masses \(\phi_{36}\), \(\phi_{37}\), and
\(\lambda_B\), it defines

\[
\begin{aligned}
Q^{\mathrm{aug}}(F_{36})&=\phi_{36},&
Q^{\mathrm{aug}}(F_{37})&=\phi_{37},\\
Q^{\mathrm{aug}}(E)&=\sum_B\lambda_Be_B,&
Q^{\mathrm{aug}}(x)&=\sum_B\lambda_Bm_B(x).
\end{aligned}
\]

Preparation failure, quota failure, exhaustion, and configurations are
distinct atoms; selected-empty remains a configuration atom. Duplicates
aggregate across batches, and the law normalizes exactly. No fiber or numeric
failure, batch, configuration, exhaustion, or selection mass is enumerated or
materialized.

Writing \(\rho=\sum_B\lambda_B\), the ideal and dyadic augmented laws agree
when \(\rho=0\); for \(\rho>0\), their TV distance is strictly below
\(\rho A/2^{64}\), and universally it is strictly below \(A/2^{64}\). Let
\(S_P\ge S_Q\) be their global ideal and dyadic selection masses.
No dyadic selected law or comparison bound is defined when \(S_Q=0\).
If \(S_Q>0\), with
\(\Delta=\operatorname{TV}(P^{\mathrm{aug}},Q^{\mathrm{aug}})\),

\[
\operatorname{TV}(P^{\mathrm{sel}},Q^{\mathrm{sel}})
\le\frac{\Delta}{\max(S_P,S_Q)}
=\frac{\Delta}{S_P}
\le\frac{\Delta}{S_Q}
<\frac{\rho A}{2^{64}S_Q}
\le\frac{A}{2^{64}S_Q}.
\]

This coefficient-one bound conditions by the larger selection mass. CP41 is
descriptive and calls no CP40 admission, CP39 coordination, CP38 resolution,
CP37 decision, or CP36 preparation operation. It consumes no source-law
\(V/W\) coordinate and no caller/global RNG. Transitive
certification/live-binding may execute CP39's local fixed Philox runtime probe
of three raw words for procedural custody; that is not a live source draw,
result, or fiber enumeration. CP41 supplies no executable proof of
factorization, live Philox/source/initializer law, live failure semantics,
exact ideal rejection, global analytic normalization, or general admission.

Checkpoint-41 source SHA-256 is
`79827f05b1a157dfaaed53146a17a7f9e006170c36bf6823510a87d338abe254`, and
focused-test SHA-256 is
`36e445057613dff7ea5d0606fa4c7924886549b57f94b58c4b3850c51678fcc3`.
The no-cache, warnings-as-errors focused run collected **28** tests and passed
**28/28** in **759.21** seconds of pytest time and **759.70** seconds external
wall time. Static gates were clean under Black, pyflakes,
Python 3.9 byte-compilation, ASCII, and the at-most-88-column check.
The final independent source/test re-audit reports **P0=P1=P2=0**.
The final independent documentation audits also report **P0=P1=P2=0**.

The inherited CP40 source/test hashes remain
`1d92574611498aeed62cd16bb232ef22f95b365b689b5351219e0539e0e6b115`
and
`30b5f93413b8c5448d85a1b7f768da5b394143d363061db418f5847272c80305`.
That exact pair passed **45/45** in **3908.56** seconds of pytest time and
**3909.19** seconds external wall time; it was not freshly rerun for CP41.
The CP41 disposition is **PASS WITH EXPLICIT SCOPE LIMITS**.
Formal Tests 28 and 29 remain **OPEN**, Test 30 remains **PENDING**, and
`R2-HYBRID` remains **NOT RUN**. No C-row, R-slot, evidence row, novelty
decision, scientific/model-quality result, generality statement, or manuscript
conclusion is promoted, and the venue-neutral TeX manuscript remains
untouched.

A forty-second checkpoint now provides the
[staged predecision factorization reference evaluator](plugin_bridge_counter_keyed_initial_tilt_rejection_predecision_factorization_code_audit.md).
For fixed valid request/context parameters \(r,j\), its partial executable map
is
\[
G^{42}_{r,j}:D^M\rightharpoonup
\{F_{37}\}\mathbin{\dot\cup}\mathcal R.
\]
It accepts the complete ordered
CP41 proposal/scoring-word tuple \(V\), but no reserved decision word. On
calls whose identity-bound direct CP28/CP30 callbacks do not refuse, it
transforms and scores every attempt before constructing quotas with the exact
CP37 primitive. A result is `ready` only after the complete quota tuple exists;
an exact post-preflight CP37 quota error becomes the modeled
quota-certification-failure tag. The public preparation-failure tag is
reserved outside the executable image: transform and score refusals propagate
rather than being relabelled.

The separate \(H\) stage validates and replays \(G\). For a ready record it
preflights all \(W\in[D]^A\) before its first half-open comparison
\(w_i<K_i\), then returns the first selected configuration or exhaustion. A
modeled quota failure passes through without decision-word access. CP42 also
supports a finite supplied successful-instance witness against exact live
CP36/CP37 records with identical proposal words. The sealed witness retains and
digest-binds the exact supplied CP37 result for custody; its digest includes
the live CP37 decision records/words and selected-or-exhausted outcome. The
parity comparison is limited to the predecision/threshold projection---\(V\),
configurations, gaps, and quota fields. The witness contains no CP42 applied-
\(H^{42}\) record and asserts no \(W\)/outcome parity or failure-fiber parity.
One \(A=1\) \(H^{42}\)-outcome comparison is a separate focused assertion.
Neither statement is a universal equivalence theorem.

CP42 therefore certifies decision-word noninterference for its own staged
reference evaluator, not for the totalized live CP36/CP37 map assumed by CP41.
It neither discharges CP41's factorization hypothesis nor changes CP41's
symbolic source-law status. It enumerates no fiber, materializes no numeric
mass, consumes no caller/global RNG, and calls no CP36--CP40 operational
method. It supplies no live Philox/source/initializer law, general initializer
admission, tag-3 semantics, Brownian coupling, drift, path, liveness, or
sampler.

Checkpoint-42 source SHA-256 is
`a6dbe506c289992ec797a32b6e034a41681af5f18f5721f7c2e1a87af66d2a71`,
and focused-test SHA-256 is
`8814ba75e4b7eff2bd90309d1cd139a6c313dfaf16009e4e4e0497598610b153`.
The final no-cache, warnings-as-errors result is
**29/29 passed** in **3599.47** seconds of pytest time and **3600.09** seconds
external wall time. Static gates are **PASS** under Black, pyflakes, Python 3.9
byte-compilation, ASCII, the at-most-88-column check, and five-test collection.
The additive supplement has SHA-256
`d3b8d1213ea4c94cd776f0628d2bae56fed4e041a975571d936bc43ab749e9fe`
and passed **5/5** in **1273.25** seconds of pytest time and **1274.44**
seconds external wall time. The exact CP41 focused regression passed **28/28**
in **805.41** seconds of pytest time and **806.05** seconds external wall time.
Final independent review is **PASS (independent audit: P0=P1=P2=0)**. The
supplement's \(F_{37}\) case is profiler-injected exact-exception branch
evidence, not evidence that an unchanged valid parent naturally reaches that
failure. Its \(K=0\) and \(K=2^{64}\) cases validate the pure \(H^{42}\)
constructor, not public-owner \(G^{42}/H^{42}\) endpoint integration. CP42 is
**PASS WITH EXPLICIT SCOPE LIMITS**.
Formal Tests 28 and 29 remain **OPEN**, Test 30 remains **PENDING**, and
`R2-HYBRID` remains **NOT RUN**. No C-row, R-slot, evidence row, novelty
decision, scientific/model-quality result, generality statement, or manuscript
conclusion is promoted, and the venue-neutral TeX manuscript remains
untouched.

A forty-third checkpoint now records the
[supplied-word factorization closure](plugin_bridge_counter_keyed_initial_tilt_rejection_factorization_closure_code_audit.md).
For one exact CP42 owner, fixed valid request/context parameters \(r,j\),
\(D=2^{64}\), and \([D]=\{0,\ldots,D-1\}\), its declared typed-error,
trusted-runtime reference map is

\[
G^{43}_{r,j}:[D]^M\longrightarrow
\{F_{36}\}\mathbin{\dot\cup}\{F_{37}\}\mathbin{\dot\cup}\mathcal R.
\]

It consumes the complete ordered proposal/scoring tuple \(V\in[D]^M\) and no
reserved decision word. An exact declared CP28 reference-initializer error or
CP30 initial-tilt error becomes the payload-free preparation-failure atom
\(F_{36}\). Every other exception, including subclasses of those exact types,
remains a refusal. If neither exact preparation error occurs, CP42 supplies
either its modeled \(F_{37}\) quota-certification failure or a ready record with
the complete quota tuple. Exact CP36/CP41 logical-coordinate order is retained
through certified split/join maps between the full word tuple and \(V,W\).

The factorization theorem concerns the private `_apply_trusted` semantic kernel
\(H^{43}_{\mathrm{sem}}\), not the separately invoked public replay facade. For
\(F_{36}\) or \(F_{37}\), \(H^{43}_{\mathrm{sem}}\) returns the same atom without
reading \(W\). For a ready record, it fully preflights \(W\in[D]^A\) before the
first half-open comparison \(w_a<K_a\), then returns the first selected
configuration or bounded exhaustion. The combined entry point implements one
ordered composition

\[
T^{43}_{r,j}(V,W)
=H^{43}_{\mathrm{sem}}\!\left(G^{43}_{r,j}(V),W\right)
\]

with exactly one \(G^{43}\) evaluation followed by one private-kernel
evaluation.
The certificate names this boundary explicitly through
`complete_g_before_semantic_h_certified`,
`semantic_h43_failure_passthrough_without_w_access_certified`, and
`semantic_h43_full_w_preflight_before_comparison_certified`.

The public replay facade `apply_decision_words` is not replay-free. It
validates the sealed predecision, re-evaluates \(G^{43}\) from its
stored \(r,j,V\), requires the exact predecision result digest to match, and
only then invokes \(H^{43}_{\mathrm{sem}}\). Consequently, stable \(F_{36}\) or
\(F_{37}\) replays pass through without touching \(W\), whereas a transient
failure whose replay changes refuses before \(W\) is accessed. This public
replay facade is neither replay-free nor a second statement of the private semantic
factorization.

Under a fixed owner and runtime, deterministic replay-stable total \(G^{43}\),
the declared exact typed-error contract, and an **abstract** product-uniform
\(V\) independent of product-uniform \(W\), the CP43-defined failure/ready fibers
give the recorded product-uniform factorization corollary. This is a finite
reference-semantics corollary, not a live Philox law, live initializer law, or
discharge of CP41's live-parent factorization hypothesis.

The \(F_{37}\) boundary remains deliberately narrow. A reviewed mathematical
argument bounds valid CP30/CP36 gaps by dyadic denominator exponent 1074 and
excludes wrong-type, nondyadic, positive-gap, coefficient-size, Decimal-range,
resource, nonnesting, escaped-quota, and terminal-branch routes. It is explicitly
not a machine proof. Natural valid-parent \(F_{37}\) reachability is unresolved:
only the adaptive 3072-digit floor-separation route remains open, with neither a
natural counterexample nor an impossibility theorem. Profiler-injected
\(F_{37}\) evidence is branch evidence only.

The closure runtime digest binds the CP43 evaluator, predecision validator,
private semantic kernel, public replay facade, combined entry point, and owner-
snapshot guards in the declared Python/platform runtime. That binding is procedural,
runtime-specific, nonportable, and noncryptographic; loaded-code integrity is
not certified, and the checkpoint assumes a trusted, unmodified runtime.
The full-outcome parity API binds one supplied successful live CP37 result and
its words, thresholds, comparison count, selected-or-exhausted outcome, and
selected configuration. The focused test code constructs that witness for only
one live outcome; the opposite selected/exhausted branch is covered only by
synthetic \(H^{43}_{\mathrm{sem}}\) cases. This is an explicit finite witness scope limit,
not universal live equivalence or live-failure parity.

Frozen CP43 source SHA-256 is
`12977ea4c38c8f5cb595d823e129f0f9dd8e0cadb1a151247d3278464c64fd64`, and
frozen focused-test SHA-256 is
`5f8372c4e80e5539e08444170f687af36b755998e6e96ffbdbe57331178f9944`. The
final no-cache, warnings-as-errors focused run collected **62** tests and
returned **62/62 passed** in **12949.69** seconds of pytest time and
**12950.26** seconds external wall time.

The frozen exact-hash regression identities are CP42 source
`a6dbe506c289992ec797a32b6e034a41681af5f18f5721f7c2e1a87af66d2a71`, CP42
primary test
`8814ba75e4b7eff2bd90309d1cd139a6c313dfaf16009e4e4e0497598610b153`, and CP42
additive-supplement test
`d3b8d1213ea4c94cd776f0628d2bae56fed4e041a975571d936bc43ab749e9fe`. The
primary regression returned **29/29 passed** in **3409.31** seconds of pytest
time and **3409.78** seconds external wall time. The supplement regression
returned **5/5 passed** in **1205.53** seconds of pytest time and **1205.98**
seconds external wall time. The pre/post hash status is
`PASS (pre/post exact CP42 source and test hashes unchanged)`.

Static gates are **PASS (Black, pyflakes, Python 3.9 byte-compilation, ASCII,
and 62-test collection); line-length audit has five reviewed exceptions**,
with details `Black left both files unchanged; exactly five lines exceeded 88
columns (source 56, 1683, 1705, and 1712; test 780), all identifier or
qualified-name lines`. The final independent audit is **PASS WITH ONE EXPLICIT
P2 SCOPE LIMIT**, with details `P0=0, P1=0; P2=1: only one live CP37 outcome has
a full parity witness, while the opposite outcome is covered only by synthetic
semantic-H tests; no universal live-equivalence claim is made`. The CP43
disposition is **PASS WITH EXPLICIT SCOPE LIMITS**. These are scoped software-
engineering results and do not alter the open scientific statuses below.

Formal Tests 28 and 29 remain **OPEN**, Test 30 remains **PENDING**, and
`R2-HYBRID` remains **NOT RUN**. CP43 materializes no numeric fiber or mass and
certifies no live source, Philox, initializer, conditional/tilted initializer,
path, liveness, or sampler law. It does not close CP41's live-parent
factorization premise, `METHOD-FREEZE/BASE-LAW`, the remaining initializer and
source-law work, or any C-row, R-slot, novelty, scientific/model-quality,
cross-domain, or generality claim. The venue-neutral manuscript artifacts remain
unchanged.

A forty-fourth checkpoint now records the
[one-allocation factorized execution adapter](plugin_bridge_counter_keyed_initial_tilt_rejection_factorized_execution_adapter_code_audit.md).
For one exact valid request \(r,j\), CP44 makes one adapter-level call to the
exact CP27 `allocate` API for the complete attempt-interleaved CP36 rejection
layout. This is deliberately not a replay-free source claim: CP27's inherited
allocation implementation performs its own deterministic internal validation
replay before returning the validated capsule. CP44 makes no second allocation,
requests no extra source word, and adds no caller/global RNG, retry, fallback,
or rollback.

Writing the acquired full capsule as \(Z\in[D]^{M+A}\), CP44 flattens its words
in chronological CP27 entry order, reconstructs the CP36 proposal/decision
layout, and requires CP43's exact split and join to give

\[
\operatorname{split}_{43}(Z)=(V,W),
\qquad
\operatorname{join}_{43}(V,W)=Z.
\]

It then calls CP43 `evaluate_and_apply` exactly once. The strongest executable
statement is pointwise on calls that actually return a CP44 result after final
structural and custody checks: the canonical semantic projection---status,
comparison count, selected attempt index, and selected-configuration
digest---equals the corresponding projection of

\[
T^{43}_{r,j}(V,W)
=H^{43}_{\mathrm{sem}}\!\left(G^{43}_{r,j}(V),W\right).
\]

This is not Python-record equality: CP44 additionally retains the complete
source capsule and its custody evidence. A CP27 allocation exception propagates
without a CP44 result. Malformed-source, preflight, and split/join failures
refuse before the CP43 semantic map. Repeated owner, dependency, and source-
custody checks can instead refuse after CP43 has evaluated but before CP44
returns a result. Both classes remain adapter refusals with no CP44 result and
are neither \(F_{36}\) nor \(F_{37}\). Only after a valid source capsule exists
can CP43 produce its exact post-source preparation-failure, quota-
certification-failure, selected, or exhausted status.

The CP44 public `validate_result` path is structural and nonreplaying in the
operational sense: it performs custody, partition, projection, and record
checks without a new CP27 allocation, CP43 \(G\), semantic \(H\), or combined
evaluation, CP36 `prepare`, or CP37 `decide`. Structural traversal, hashing,
and deterministic recomputation still occur. Thus "nonreplaying" does not mean
zero validation work.

Its selected-code runtime fingerprint uses explicit marshal version 2 behind
a recursive exact constant-domain guard, avoiding false digest changes from
live reference topology. This is CP44-only procedural custody: it neither
modifies CP43 nor certifies arbitrary-instrumentation ancestry stability,
portable attestation, or loaded-code integrity.

For one fixed owner/runtime, additionally assume that \(G^{43}\) is
deterministic, replay-stable, and total under CP43's declared typed-error
contract. Under the further abstract premise that the complete \(Z\) is
product-uniform on the exact distinct coordinates, CP43's split is a coordinate
permutation, so \(V\) and \(W\) are independent product-uniform tuples and the
abstract semantic map \(S^{44}(Z)=T^{43}(\operatorname{split}_{43}(Z))\) has the
CP41-form symbolic mixture over \(F_{36}\), \(F_{37}\), exhaustion, and selected
configurations. No source/refusal mass, fiber, or other mass is numerically
materialized. This is not a law for the live adapter, CP27/Philox output,
allocation success, freshness, independence, or randomness.

CP44 constructs a new factorized route by bypassing CP36 `prepare` and CP37
`decide`; it does not prove preparation-, decision-, failure-, chronology-, or
whole-record equivalence to that legacy route and does not discharge or
theorem-level supersede CP41's original live-parent factorization premise.
Natural valid-parent \(F_{37}\) reachability and the 3,072-digit adaptive floor-
separation question remain unresolved. CP44 promotes no numeric source law,
initializer, path, sampler, scientific/model-quality, cross-domain, or
generality claim, and the venue-neutral manuscript artifacts remain unchanged.

Final CP44 execution evidence is frozen in the linked standalone audit. The
frozen source contains `1829` lines and has SHA-256
`42d0bdbf112628e7c2589f7e57b79e60b31b77105cd7be324716198dd3d63e9d`;
the `829`-line focused test has SHA-256
`e0ad09b5b6bbc2143331d5e82c2eabf8d505f1829e25a321273eb73e34c442d6`.
The final no-cache, warnings-as-errors run collected **26** cases and returned
**26/26 passed** in **50165.86** seconds of pytest time and **50166.38** seconds
external wall time; pre/post source and test hashes were unchanged. There were
no failures, errors, skips, xfails, xpasses, or warnings.

Black, pyflakes, flake8 `E9,F63,F7,F82`, Python 3.9.13 and locked Python 3.11.5
syntax compilation, ASCII screening, exact collection, and the exact 16-symbol
export/signature check passed. Eighteen formatter-stable, identifier-dominated
lines exceeded 88 columns and were individually reviewed. All six exact
contract blocks occur once and byte-match the frozen source. Independent CP44
source and test audits found `P0=P1=P2=0`.

No parent suite was freshly rerun for CP44. Exact-hash inherited evidence
remains the historical CP43 **62/62 passed** record
(**12949.69/12950.26** seconds pytest/wall), CP42 primary **29/29 passed**
record (**3409.31/3409.78** seconds), and CP42 supplement **5/5 passed** record
(**1205.53/1205.98** seconds). The untouched venue-neutral Markdown and TeX
manuscripts retain SHA-256 values
`0569b18aefb2aefa6c24af0559880f66c4a0daa6b2073169d30c892515e976a8` and
`0ad9abccbc38ccc41e9fb3f7a1f8db6a4a197d23c3946da60a3cd4b93b475ba9`.
The CP44 disposition is **PASS WITH EXPLICIT SCOPE LIMITS**. This freezes only
the scoped engineering record and promotes no live source, numeric-mass,
initializer/path/sampler, scientific, model-quality, cross-domain, generality,
C-row, R-slot, or manuscript claim.

A forty-fifth checkpoint now records the
[fixed-address source-support obstruction](plugin_bridge_counter_keyed_initial_tilt_rejection_fixed_address_source_support_obstruction_code_audit.md).
Let D = 2^64 and let L be CP44's complete capsule length. For one fixed
owner/runtime/request that returns z in [D]^L, deterministic same-address
replay makes the canonical live source law delta_z, and exactly

\[
\operatorname{TV}(\delta_z,U_L)=1-D^{-L}.
\]

More generally, a deterministic partial successful-capsule map driven by at
most k free uint64 coordinates has conditional-success support at most D^k.
For any request law with positive success probability,

\[
\operatorname{TV}(\nu_{\mathrm{succ}},U_L)
\ge 1-D^{k-L}\quad\text{when }L>k,
\]

while support counting alone gives only zero when L <= k. Conditioning
cannot enlarge support, so no success/value-independence premise is required.
Every external entropy-bearing coordinate must nevertheless be included in
k. The symbolic implementation accepts every exact nonnegative integer k,
uses digit-limit-independent signed-hex integer digesting, and never
materializes enormous powers.

This obstruction remains in source space. Data processing gives an output-TV
upper bound, not a lower bound; a constant semantic map makes both output laws
identical. CP45 therefore does not establish any discrepancy for CP43/CP44
semantic outputs. It also supplies no source/refusal probability,
unconditional adapter law, natural \(F_{37}\) resolution, live product uniformity or
nondegenerate V/W independence, physical randomness,
freshness, initializer/path/sampler admission, or scientific/model/generality
evidence.

CP45 certification and bound description make no CP27 source allocation and
execute no CP43/CP44 semantics. Caller/global Python, NumPy, and PyTorch RNG
states remain unchanged. The narrower contract explicitly discloses that
inherited ancestry validation may run a deterministic local Philox runtime
probe; it does not claim absence of every transitive RNG call. Exact parent and
local helper surfaces, construction tokens, records, and digests are guarded
procedurally, while loaded-code integrity, portability, and cryptographic
authentication remain false. The venue-neutral manuscripts remain unchanged.

Final CP45 source-independent, static, hostile-audit, and full focused evidence
is frozen in the linked standalone audit. The authoritative warnings-as-errors
run passed 20/20 in `19448.25 s` (`5:24:08`), with unchanged source/test hashes
and final independent severity count `P0=P1=P2=0`; the disposition is **PASS
WITH EXPLICIT SCOPE LIMITS**. No manuscript claim is promoted by this
checkpoint.

A forty-sixth checkpoint freezes an explicit two-model source contract. Write
\(D=2^{64}\), let \(L\) be the complete CP44 capsule length, and retain CP45's
certified \(L>2\). The fixed-request descriptor treats one exact
`(run_id, initialization_index)` as deterministic replay. Conditional on a
named event having positive mass, its symbolic capsule law is a Dirac mass and

\[
\operatorname{TV}(\delta_z,U_L)=1-D^{-L}.
\]

The distinct external-law descriptor accepts only a declared finite exact-
rational probability mass function on the two uint64 request coordinates. If
its support size is \(s\), any deterministic partial request-to-capsule map,
conditional on a positive named event, has capsule support at most \(s\) and

\[
\operatorname{TV}(\nu_{\mathcal A},U_L)\ge 1-\frac{s}{D^L}.
\]

The complete-validated-capsule acquisition event and the CP44 returned-result
event remain distinct identifiers. Their positive mass is required to define
the corresponding conditional law but is explicitly not certified; CP46
instantiates neither conditional capsule law. The executable declaration API
is capped at 4,096 atoms. That resource cap is separate from the analytic
current-surface theorem: two uint64 coordinates give request support at most
\(D^2\), which is strictly smaller than \(D^L\) because \(L>2\), so this
surface cannot produce the full product-uniform capsule law through a
deterministic map.

More generally, request support at least \(D^L\) is necessary but not
sufficient for product uniformity. Under a realized request law \(\mu\), a
deterministic partial map \(F\), and a positive conditioning event
\(\mathcal A\), the conditional capsule pushforward is \(U_L\) if and only if
every output fiber has conditional \(\mu\)-mass \(D^{-L}\). CP46 records this
weighted-fiber criterion but certifies neither realization of the declared
external law nor the required fiber balance. Its source-TV lower bounds do not
descend through an arbitrary semantic map: data processing gives an upper
bound, and a constant map can erase the discrepancy.

Ordinary CP46 model construction and validation return sealed cached
descriptors and do not call the CP45 owner's live-binding method. Explicit
live-ancestry revalidation is separately available; cached certificate checks
and explicit revalidation may still inherit CP45's disclosed deterministic
local Philox probe. Each ordinary model therefore records that live CP45
ancestry was not revalidated for that model. CP46 supplies no external-law
realization or request sampler, event probability, unconditional capsule or
output law, live uniformity or request-coordinate independence, full-capsule
product uniformity, nondegenerate V/W independence, physical randomness,
cross-call freshness, output-TV lower bound, initializer/path/sampler
admission, loaded-code integrity, portability, cryptographic authentication,
or scientific/model-quality/generality claim.

The standalone
[`CP46 audit`](plugin_bridge_counter_keyed_initial_tilt_rejection_explicit_source_model_contract_code_audit.md)
records the complete evidence boundary. The frozen CP46 source is
`src/heterodiff/processes/plugin_bridge_counter_keyed_initial_tilt_rejection_explicit_source_model_contract.py`
with SHA-256
`8c6d1ead643a127aa87d395de1ff707eb0506e619d53b513477777173d439318`.
Its focused test is
`tests/unit/test_plugin_bridge_counter_keyed_initial_tilt_rejection_explicit_source_model_contract.py`
with SHA-256
`04b73ec0f0fbd0a8a31973a02a2218cdd1ea3ad000a9648168a1f7194c7415ac`.
The final run returned **24/24 passed** in **4765.71 seconds** of pytest time
and **4766.28 seconds** real time: 15 source-independent fast cases and nine
owner-bound cases. Exact finite enumeration covered 1,848 positive
partial-map/law cases and 10,000 derived-coordinate/map compositions. Static
gates passed, final independent audits reported `P0=P1=P2=0`, and the CP46
disposition is **PASS WITH EXPLICIT SCOPE LIMITS**.

A forty-seventh checkpoint freezes the external full-capsule execution
adapter. It binds one exact CP46--CP45--CP44--CP43 ancestry and calls one
direct provider at most once per execution, and exactly once when the provider
boundary is reached, for an exact tuple of \(L\) uint64 words. Direct identity
ingestion exposes all \(D^L\) capsules, but interface cardinality is not a
probability law. Product-uniform capsules and IID returned capsules across
distinct draw identifiers require external provider-law premises; total or
appropriately value-independent success conditions for the provider and
downstream stages are additionally required for the corresponding returned-
result law. Value-dependent failure can bias the law conditional on return.

Before provider invocation, the adapter atomically retires the draw identifier
within one bounded owner lifetime. Duplicate identifiers refuse before the
provider, and API-mediated provider, shape, or downstream failure does not
roll back a completed retirement. Equal capsules under distinct identifiers
remain legal. Successful execution uses CP43's exact split, join, and combined
evaluation. Retained-result and ledger validation is structural and does not
replay the provider, CP43 \(G/H\), CP44 execution, CP27 allocation, CP36
preparation, or CP37 decision.

CP47 certifies no provider randomness, physical entropy, live product-uniform
or IID law, cross-owner/process/restart uniqueness, concurrent or reentrant
semantic safety, adaptive retry, semantic-output TV lower bound,
initializer/path/sampler admission, scientific or model-quality result,
cross-domain generality, or manuscript claim. Its selected-code fingerprint
and sealed records are same-process procedural custody, not loaded-code
integrity, portability, cryptographic authentication, or resilience to a
provider's hostile private-state mutation through same-process introspection.

The standalone
[`CP47 audit`](plugin_bridge_counter_keyed_initial_tilt_rejection_external_full_capsule_execution_adapter_code_audit.md)
records the complete evidence boundary. The frozen source is
`src/heterodiff/processes/plugin_bridge_counter_keyed_initial_tilt_rejection_external_full_capsule_execution_adapter.py`
at **2,512 lines / 108,814 bytes**, with SHA-256
`2c1522cd92f186d3d428e627bdd7ba6f29a7b8fbf727fb8ca8b7852f1badcf0b`.
The focused test is
`tests/unit/test_plugin_bridge_counter_keyed_initial_tilt_rejection_external_full_capsule_execution_adapter.py`
at **1,446 lines / 52,122 bytes**, with SHA-256
`46ab42233351a681b5b7618fcbff088e1e4f474f0350b636e081148fb2af2ced`.
The authoritative warnings-as-errors run returned **31/31 passed**---22 fast
cases and nine owner-bound cases---in **7763.03 seconds** of pytest time
(**2:09:23**), with `real 30735.62`, `user 7141.85`, and `sys 545.25`
seconds; the external real time includes host suspension. A post-run fast
partition returned **22/22 passed** in **1.17 seconds**. Static gates passed,
final independent audits reported `P0=P1=P2=0`, and the CP47 disposition is
**PASS WITH EXPLICIT SCOPE LIMITS**.

A forty-eighth checkpoint freezes the
[byte-source full-capsule execution boundary](plugin_bridge_counter_keyed_initial_tilt_rejection_byte_source_full_capsule_execution_code_audit.md).
It binds one exact CP47 owner and its transitive CP46--CP43 ancestry to exactly
one of two profiles. The `system-os-urandom-operational` profile uses the
internal wrapper around the cached ordinary `os.urandom` Python API; the
`external-exact-byte-block-unverified` profile uses one exact caller callback.
At each reached CP47 provider boundary, the selected backend
is called exactly once with
`(source_instance_sha256, draw_index, 8L)` and must return exact `bytes` of
length \(8L\). Every exact byte value is accepted by the codec, but later
CP47/CP43 refusal remains possible. No coercion, retry,
filtering, fallback, replacement, truncation, padding, or alternate source is
permitted. The block is decoded by a fixed manual big-endian map into the exact
\(L\)-word uint64 tuple passed once to CP47. CP47 remains the sole
draw-retirement and semantic-execution authority. CP48 retains the exact raw
bytes, decoded words, CP47 result, and structural custody without replaying the
backend or CP47 execution during validation.

Writing \(D=2^{64}\), the codec
\(B:\{0,\ldots,255\}^{8L}\to[D]^L\) is a bijection. Let
\(U_{\mathrm{byte},8L}\) denote the jointly uniform complete byte-block law
and \(U_L\) the product-uniform uint64 law. Then, for every byte-block law
\(\mu\),

\[
\operatorname{TV}(B_{\#}\mu,U_L)
=\operatorname{TV}(\mu,U_{\mathrm{byte},8L}).
\]

Joint uniformity of the complete \(8L\)-byte block consequently yields
product-uniform words, but uniform one-byte marginals do not suffice. IID word
capsules require jointly or sequentially uniform backend blocks on distinct
draw identifiers. Given positive CP48 return-event mass, conditioning on a
returned result preserves the claimed law only when the complete CP48 success
likelihood is constant over capsule values; totality is sufficient. An IID
returned sequence additionally requires positive joint return-event mass and
the corresponding joint success condition. The system profile certifies only
the cached Python API call boundary. It certifies no operating-system law,
independence, totality, physical entropy, internal retry or syscall count,
cryptographic security, freshness, reproducibility, or authentication.

CP47 remains the only retirement authority under same-draw concurrency. The
focused race and reentry evidence requires one backend boundary, the exact CP47
duplicate type and message, bounded release-in-finally synchronization,
per-worker thread-context cleanup, and empty provider acquisition state. This
does not certify broader concurrent or reentrant semantic safety beyond CP47
retirement, asynchronous scheduling guarantees, or hostile same-process
private-state tamper resilience.

The frozen CP48 source is
`src/heterodiff/processes/plugin_bridge_counter_keyed_initial_tilt_rejection_byte_source_full_capsule_execution.py`
at **2,025 lines / 82,973 bytes**, with SHA-256
`7be4c1bdf588950902bbdfe03e492dea15e42d0affff5d6e83f6104b798974cd`.
The focused test is
`tests/unit/test_plugin_bridge_counter_keyed_initial_tilt_rejection_byte_source_full_capsule_execution.py`
at **1,692 lines / 62,124 bytes**, with SHA-256
`2fa6f429424d95e851496fc870ca1d2598cf44f83a6adb98c673cc93ebcdf282`.
The authoritative no-cache, warnings-as-errors run collected **37** cases and
returned **37/37 passed**---28 source-independent fast cases and nine
owner-bound cases---in **15191.58 seconds** of pytest time, including
**15048.01 seconds** for owner-bound fixture setup. External timing was
`15192.11` seconds real, `13929.09` seconds user, and `1211.79` seconds system.
The unchanged frozen pair then passed the exact **28/28** fast partition in
**2.16 seconds**. Static gates passed. Independent review reported
`P0=P1=P2=0`; the remaining P3 asynchronous-scheduling gap is retained as an
explicit nonclaim, not promoted to a concurrency guarantee. The CP48
disposition is **PASS WITH EXPLICIT SCOPE LIMITS**.

CP48 certifies no backend or operating-system law, backend totality or success
probability, full-block uniformity, IID behavior, physical entropy,
cryptographic security, cross-call freshness, distinct values for distinct
draw identifiers, global/cross-owner/cross-process/fork/restart uniqueness,
backend internal behavior or syscall count, unconditional returned-result law,
semantic-output TV lower bound, loaded-code integrity, runtime portability,
source-instance authentication, CP46 declared-law realization,
initializer/path/sampler admission, scientific or model-quality result,
cross-domain generality, or manuscript claim. The venue-neutral Markdown and
TeX manuscripts remain unchanged at SHA-256 values
`0569b18aefb2aefa6c24af0559880f66c4a0daa6b2073169d30c892515e976a8` and
`0ad9abccbc38ccc41e9fb3f7a1f8db6a4a197d23c3946da60a3cd4b93b475ba9`.

A forty-ninth checkpoint freezes the
[assumption-gated full-source law admission boundary](plugin_bridge_counter_keyed_initial_tilt_rejection_full_source_law_admission_code_audit.md).
It binds one exact CP48 owner and its transitive CP47--CP43 ancestry to one
sealed external assumption declaration. The declaration is assumption-only
and never attests either CP48 backend. For each individually fixed
`(run_id, initialization_index, draw_index)` request in one fixed pre-operation
state, its antecedent assumes a fresh draw, available retirement capacity, and
passing pre-boundary structural/live guards; almost-sure backend return of one
exact \(8L\)-byte block with an unconditional jointly uniform complete-block
law; complete post-boundary success for every exact byte value; and fixed-
runtime deterministic replay-stable typed-total CP43/CP42 object semantics.
Duplicate-draw, capacity-exhaustion, and other pre-boundary refusals lie
outside this pointwise kernel and are not totalized by the declaration.

Let \(C\) be CP48's byte/word bijection, let \(U_{\mathrm{bytes}}\) be the
jointly uniform law on complete \(8L\)-byte blocks, and let
\(U_{\mathrm{words}}\) be the product-uniform law on \([D]^L\), where
\(D=2^{64}\). For one fixed request, define

\[
T_{\mathrm{obj}}(w)
=
(\text{status},\text{comparison count},\text{selected attempt index},
 \text{canonical bit-exact CP42 configuration value or None}).
\]

This object-semantic map keeps `preparation_failure`,
`quota_certification_failure`, `selected`, and `exhausted` distinct. Replacing
only its final configuration value by the canonical configuration SHA-256
gives CP44's canonical projection of the CP43 applied decision; a returned
record separately retains the actual selected runtime object by identity,
which is custody evidence outside the probability space. For a complete byte-
block law \(\mu\) and \(B\sim\mu\), CP49 records the pointwise identities

\[
\operatorname{Law}(T_{\mathrm{obj}}(C(B)))
=
(T_{\mathrm{obj}}\circ C)_{\#}\mu
\]

and

\[
\operatorname{TV}\!\left(
 (T_{\mathrm{obj}}\circ C)_{\#}\mu,
 (T_{\mathrm{obj}})_{\#}U_{\mathrm{words}}
\right)
\le
\operatorname{TV}(\mu,U_{\mathrm{bytes}}).
\]

Thus the declared jointly uniform full-block premise gives the exact CP43/CP42
object-semantic reference pushforward. The inequality is only a data-
processing upper bound; CP49 supplies no semantic-output TV lower bound.

If \(R\) is complete return, \(s(b)=\Pr(R\mid B=b)\), and
\(Z=\sum_b\mu(b)s(b)>0\), then

\[
\Pr(C(B)=w\mid R)
=
\frac{\mu(C^{-1}(w))s(C^{-1}(w))}{Z}.
\]

Under the jointly uniform block law, the returned word law is uniform if and
only if the complete-success likelihood is positive and constant on the whole
block domain. Almost-sure exact-block backend return together with post-
boundary complete success for every byte value is sufficient, but those are
declared mathematical assumptions, not verified behavior. Per-call or
marginal premises do not imply a returned sequence is IID. Such a conclusion
would additionally require a joint product-uniform block-vector law, or each
new block conditionally uniform given the complete prior and adaptive history,
plus positive joint return mass and value-independent joint complete success.
CP49 proves no adaptive-stopping or retry theorem.

CP49 acquires no bytes and evaluates no CP43/CP42 semantics. Description,
admission of an already returned CP48 result, and ordinary validation are
structural, nonexecuting, and nonreplaying. Explicit live-ancestry
revalidation is separate and may replay ancestry validation only; it never
acquires backend bytes or executes CP43 semantics. An admitted result preserves
its exact CP48 record, CP43 applied decision, natural semantic status,
comparison count, selected-attempt index, and byte/word custody. On the
selected branch it additionally preserves the exact nested CP42 configuration
object by identity and its canonical SHA-256. The controlled all-zero,
one-attempt selected witness therefore supplies one exact word preimage of the
full enriched semantic atom and hence nonempty enriched-atom and coarser
configuration-value fibers. Under the declared abstract uniform and total
semantics, the witnessed atom and selection event have positive reference mass
at least \(D^{-L}=2^{-64L}\). This is neither operational source-law evidence
nor general initializer admission.

The frozen CP49 source is
`src/heterodiff/processes/plugin_bridge_counter_keyed_initial_tilt_rejection_full_source_law_admission.py`
at **1,913 lines / 84,530 bytes**, with SHA-256
`7951c02c60b6ca8dbbbf025f13e26e52eb7319cd4c48d416e5b841d99530bd39`.
The focused test is
`tests/unit/test_plugin_bridge_counter_keyed_initial_tilt_rejection_full_source_law_admission.py`
at **1,765 lines / 70,075 bytes**, with SHA-256
`a799c68ebe2d9fa415bf1282a2f28c4f87570a7d21a728373d61f5a34a100e7a`.
The authoritative no-cache, warnings-as-errors run collected 28 tests and
passed **28/28** in **25354.31 seconds** of pytest time (**7:02:34**), split
into 21 source-independent and seven owner-bound cases; shared owner-fixture
setup took **17897.94 seconds**. External timing was `25366.40` seconds real,
`23535.81` seconds user, and `1681.97` seconds system, with zero errors,
failures, or skips. The unchanged frozen pair then passed the exact **21/21**
source-independent partition, with seven owner-bound cases deselected, in
**2.04 seconds** of pytest time; external timing was `2.62` seconds real,
`1.67` seconds user, and `0.45` seconds system. Black, locked CPython 3.11
byte-compilation, locked Pyflakes, and fatal Flake8 `E9/F63/F7/F82` gates
passed, and the source/test hashes remained unchanged.

The first-success snapshot through its completed runner record, stable status,
and JUnit file is authoritative. After that completion, an unintended
automatic repeat appended a second start record and 21 progress dots to the
outer log before it was stopped. Its process and launch label are absent, it
produced no result, and none of its partial output is used as evidence. With
that provenance containment disclosed, final independent reviews report
`P0=P1=P2=0`, and CP49's disposition is **PASS WITH EXPLICIT SCOPE LIMITS**.

CP49 verifies no backend, operating-system, or external-callback law;
almost-sure return, joint uniformity, totality, success mass, independence,
physical randomness or entropy, security, freshness, or operational
realization. It certifies no unconditional returned-result law, returned-
sequence IID law, adaptive query/stopping/retry or random-oracle theorem,
duplicate/capacity/pre-boundary refusal totalization, global/cross-owner/
cross-process/fork/restart/machine uniqueness, CP41-premise discharge, legacy
CP36/CP37 universal equivalence, CP40 fixed-batch target or initializer
admission, live or general initializer distribution, exact ideal rejection,
global analytic tilt, intensity, lineage, tag-3 payload, path, or sampler. It
supplies no loaded-code attestation, runtime portability, cryptographic
custody, formal Test 28 closure, scientific/model-quality/cross-domain/
generality conclusion, nonconfirmatory experiment, confirmatory result,
novelty decision, C-row, R-slot, or manuscript claim. Formal Tests 28 and 29
remain **OPEN**, Test 30 remains **PENDING**, and `R2-HYBRID` remains **NOT
RUN**. The venue-neutral Markdown and TeX manuscripts remain unchanged at
SHA-256 values
`0569b18aefb2aefa6c24af0559880f66c4a0daa6b2073169d30c892515e976a8` and
`0ad9abccbc38ccc41e9fb3f7a1f8db6a4a197d23c3946da60a3cd4b93b475ba9`.

A separate cap-two calculation checks the factorial and
occurrence-route multiplicities; it is not a general-cap implementation.
The separate records for the first forty-nine checkpoints cover the
clean hold, balanced birth/death/replacement edits,
closed-form OU motion, event-driven simulation, finite/Gaussian reversal
controls, marginal jump-flux and relative-score objectives, and structured
unnormalized importance arithmetic, plus exact retained/overflow observation
normalization, duplicate-orbit factors, typed atomic/Gaussian channels, and
coordinate gradients, plus conjugate reverse-to-terminal propagation, literal
cap restriction, exact small-instance blocked-birth flux, guide gradients and
edit ratios, replayable unnormalized cap proposals, global energy/derivative
bounds, snapshot and graph custody, exact/Hutchinson objectives, symbolic
output gauges, supplied-rate operational guards, exact normalized
birth/death/replacement proposal factors, process-valid continuous edits, and
the sampled base-energy integrand, together with the scoped mixed known-law
identities, both operational point totalizers, and the target-explicit exact-
rational operational edge composition, rate-space domination, successful-
return local wait/route/represented-ratio decision, and bounded local
coordination, followed by same-runtime route replay evidence and its ordered
integration across a successfully returned bounded-loop transcript, and then
the direct counter-key namespace plus post-hoc persistent-lineage prerequisite,
followed by bounded operational-epoch-keyed execution with integrated route and
lineage custody, and then bounded bootstrap-only tag-3 raw-prefix custody.
The twenty-sixth checkpoint then adds bounded pre-cardinality tag-7 global-
control raw-prefix custody with an explicit initialization-index address limb.
The twenty-seventh adds fixed, strategy-specific stages and injective
multiblock work-item allocation over that namespace, while leaving every word
uninterpreted.
The twenty-eighth interprets only the fixed reference capsule as a finite
configuration, with exact quota/codebook/layout evidence and an explicitly
hypothetical product-uniform pushforward. It does not implement a conditional
or tilted initializer, the other three strategies, lineage/tag-3 coordination,
or initializer admission.
The twenty-ninth adds only the preregistered deterministic-grid diagnostic and
its one-shot evidence custody. Its pass decision is relative to
counterfactual product-uniform envelopes and does not promote the finite
pushforward to an actual Philox sampling law or close any initializer,
sampler, or generality gate.
The thirtieth adds only the deterministic guide-plus-residual point log factor
for the selected \(\Pi_N\) base law, with exact represented-value composition,
one final binary64 rounding, replay custody, and an outward log-value interval.
It excludes \(V_\phi\) and does not exponentiate or normalize the factor,
enumerate support, select a configuration, consume randomness, initialize a
state, construct a path, or admit a sampler.
The thirty-first adds only exact complete enumeration of the resource-admitted
all-atomic support, exact represented-parameter base coefficients and their
normalizer witness, and one replay-validated checkpoint-thirty point per state.
It refuses continuous types and supplies no normalized mass, exponentiated or
normalized tilt, selection, RNG, initializer binding, path, or sampler.
The thirty-second adds only deterministic preparation of a certified positive
dyadic approximation to the all-atomic operational tilted law and exact lookup
from an explicit uint64 word. It does not source or certify the word, bind the
initializer protocol, sample the ideal transcendental law exactly, admit an
initializer, support mixed/continuous states, or construct a path or sampler.
The thirty-third adds only the exact checkpoint-twenty-seven enumeration-stage
word binding for that selector, including its one-entry tag-7 plan, unchanged
word forwarding, shared parent ancestry, and replayable configuration-valued
projection. It creates no second RNG namespace and accepts no caller RNG, but
it does materialize one parent Philox word. It certifies no actual word law,
exact ideal-law sample, initializer admission, mixed/continuous support,
lineage/tag-3 coordination, path, or sampler.
The thirty-fourth adds only a factory-owned live all-atomic initial-state
configuration constructor over that fixed parent stack and a counterfactual
replacement-\(U\) pushforward theorem. It certifies deterministic same-address
replay and a valid configuration, not a live initializer distribution or
admission, actual word uniformity/independence, general or mixed/continuous
initialization, lineage/tag-3 coordination, path, or sampler.
The thirty-fifth adds only the fixed-index CP28 finite mixed reference
configuration constructor, reverse-time-zero intensity, duplicate-safe CP23
bootstrap lineage, and CP25 dimension-shaped uninterpreted tag-3 prefixes.
Its separate abstract iid-uniform complete-capsule theorem defines only the
configuration law \(Q_{\mathrm{fin}}\); it does not certify live Philox or
tag-3 laws, continuous Gaussian or capped-Poisson sampling, conditional/tilted
initialization or admission, tag-3 cross-initialization disjointness, a path,
or a sampler.
The thirty-sixth adds only fixed-budget rejection-stage proposal and score
preparation: CP27 materializes the complete tag-7 stage-1 prefix, CP28
transforms every proposal slot, CP30 supplies exact \(q\), and CP36 certifies
the exact rational inequality \(q-U\le0\) while retaining one uninterpreted
word per attempt. Its abstract distinct-coordinate iid-word theorem is
failure-augmented and conditional; it supplies no failure probability,
success-conditional law, live word law, decision, acceptance, selection,
initializer output or admission, lineage/tag-3 coordination, path, or sampler.
The thirty-seventh adds only exact conservative finite-resolution quotas,
threshold-before-comparison chronology, half-open interpretation of a prefix of
the inherited CP36 words, and either the first selected configuration or valid
bounded exhaustion. Its conditional product formula requires fixed
proposal/score data and separate abstract iid-uniform words. Separately, a
fixed-data common-uniform coupling of independent-coordinate ideal and dyadic
Bernoulli sequences gives the strict \(A/2^{64}\) finite-outcome comparison. It
supplies no live source law,
failure probability, exact ideal rejection or normalized tilted law,
initializer admission, lineage/tag-3 coordination, path, or sampler.
The thirty-eighth adds only the complete exact fixed-\(B\) counterfactual
dyadic law, stable duplicate-configuration aggregation, the
\(Z_B>0\) selected-law boundary, and the strict unconditioned augmented
\(<A/2^{64}\) ideal/dyadic comparison from a separate common-uniform coupling.
It supplies no live source or CP36 success law, no selected-conditioned reuse
of that TV bound, no generic initializer admission, and no lineage/tag-3,
Brownian, drift, path, or sampler semantics. Its frozen focused and
direct-parent suites passed 45/45 and 44/44, respectively, and its disposition
is **PASS WITH EXPLICIT SCOPE LIMITS**.
The thirty-ninth adds only one-CP38-`resolve` construction-time coordination of the
exact selected configuration and attempt with reverse-time-zero intensity,
CP23 positional bootstrap lineage, and bounded CP39-local tag-3 prefixes. Its
address includes initialization index, lineage serial, and selected-attempt
suffix and is disjoint from valid legacy suffix-zero tag-3 addresses. Selected-
empty and exhausted results remain distinct. The prefixes are uninterpreted,
same-address replay is deterministic, and no generic admission, live law,
global/one-shot/fork guarantee, coordinate generation, Brownian, path, or
sampler semantics follows. Its audit status is **PASS WITH EXPLICIT SCOPE
LIMITS**.
The fortieth adds only the exact augmented dyadic target conditional on CP38's
direct word-free successful batch, the \(Z_B>0\) selected-state target, the
selection-mass-scaled strict ideal/dyadic comparison, and one narrow downstream
structural state/no-state boundary over the exact CP39 result. It preserves the
actual selected CP39 object rather than substituting the target row's duplicate
representative. It supplies no live or unconditional initializer law, CP36
success/failure law, exact ideal rejection, global normalized tilt,
all-strategy general admission, semantic tag-3 payload, Brownian, path, or
sampler semantics. Its frozen source and tests passed all 45 focused tests;
unchanged exact-hash CP39 parent evidence is inherited. Its status is **PASS
WITH EXPLICIT SCOPE LIMITS**.
The forty-first adds only a symbolic failure-aware mixture over the complete
CP36 abstract word template, conditional on a new explicit **unproved**
factorization hypothesis. It distinguishes CP36 preparation failure, CP37
quota-certification failure, exhaustion, and configuration atoms; records the
\(\rho=0\) identity, strict \(\rho A/2^{64}\) augmented bound, and the
positive-\(S_Q\) factor-one conditioned bound; and performs no CP36--CP40
operational call. It consumes no source-law \(V/W\) coordinate and no
caller/global RNG; transitive certification/live-binding may execute
CP39's local three-word Philox runtime probe only for procedural custody. It
materializes no numeric fiber or probability and supplies no live
Philox/source/initializer law, exact ideal rejection, global normalized tilt,
general admission, Brownian/path, or sampler semantics. Final focused execution
passed **28/28** under no-cache, warnings-as-errors conditions; the
disposition is **PASS WITH EXPLICIT SCOPE LIMITS**. The final independent
documentation audits report **P0=P1=P2=0**.
The forty-second adds only a bounded partial staged reference evaluator
\(G^{42}_{r,j}\), on the domain where direct CP28/CP30 stages do not refuse,
complete ready quotas before a separate fully preflighted \(H^{42}\), modeled
quota-failure pass-through without decision-word access, and finite supplied
successful-instance predecision/threshold projection parity with exact live
CP36/CP37 records. Its preparation-failure branch is reserved outside the
executable image. Its reference semantics is not universally identified with
live failure behavior, and it does not discharge CP41's hypothesis or supply
numeric fibers, a live source law, initializer admission, Brownian/path, or
sampler semantics. Its focused, supplemental, CP41-regression, static, and
independent-review evidence is final. Its disposition is
**PASS WITH EXPLICIT SCOPE LIMITS**.
The forty-third adds only the bounded CP43-defined supplied-word reference
closure under an exact typed-error and trusted-runtime contract. It totalizes
exact declared CP28/CP30 operational errors as \(F_{36}\), retains CP42's
\(F_{37}\)-or-ready result, and places private semantic
\(H^{43}_{\mathrm{sem}}\) after the
complete \(V\)-only \(G^{43}\). Its combined entry point evaluates that
composition once. Its separate public replay facade replays \(G^{43}\) for custody
and therefore does not promise transient-failure pass-through. The abstract
product-uniform corollary requires a fixed runtime, deterministic replay-stable
total \(G^{43}\), and independent product-uniform \(V,W\); it is not a live
Philox/source law. Natural valid-parent \(F_{37}\) reachability and the final
adaptive floor-separation route remain unresolved. One supplied live outcome
supports a full-outcome parity witness, while the opposite outcome remains only
synthetic \(H^{43}_{\mathrm{sem}}\) coverage; no universal live equivalence follows. CP43
does not discharge CP41's live-parent hypothesis or supply numeric fibers,
initializer admission, Brownian/path, or sampler semantics. Its hashes,
focused result, regression, timings, static gates, independent audit, and
disposition are frozen in the explicit evidence record above; the disposition
is **PASS WITH EXPLICIT SCOPE LIMITS**.
The forty-fourth adds a new returned-result-conditional execution route from
one complete CP27 rejection capsule to one CP43 combined evaluation. One
adapter-level CP27 `allocate` call is exact even though that inherited API
performs its own deterministic internal validation replay. The acquired
\(Z\in[D]^{M+A}\) is split into exact \(V,W\) coordinates and joined back to
\(Z\); whenever CP44 returns after final custody, its canonical semantic
projection equals that of the one CP43 combined result by construction. Pre-
and post-combined refusal remain outside \(F_{36}/F_{37}\). Public CP44
validation is structural and does not replay allocation, CP43 \(G/H\), CP36
`prepare`, or CP37 `decide`. The CP41-form pushforward is recorded only for an
abstract semantic map under fixed-runtime deterministic replay-stable total
\(G^{43}\) and product-uniform \(Z\). CP44 bypasses rather than proves
equivalence to the legacy CP36/CP37 route; CP41's original premise and natural
\(F_{37}\)
reachability remain unresolved. It establishes no live Philox/source law,
numeric mass, initializer/path/sampler admission, or scientific, model-
quality, cross-domain, or generality result. Its final focused, static, exact-
string, and independent-audit evidence is frozen above; CP43/CP42 execution
evidence is inherited by exact hash and was not freshly rerun for CP44. Its
disposition is **PASS WITH EXPLICIT SCOPE LIMITS**.

The forty-fifth records the fixed-address source-support obstruction. A
returned fixed request is a point mass at exact source TV `1-D^(-L)` from
product uniform. A deterministic successful capsule map driven by at most k
free uint64 coordinates has conditional-success source TV at least
`1-D^(k-L)` when L>k, without requiring success/value independence. This
source result gives no output-TV lower bound. CP45 makes no source allocation
or CP43/CP44 semantic call, but its inherited ancestry checks may run a
deterministic local Philox probe without changing caller/global RNG state. It
supplies no positive live source/refusal/unconditional law, randomness,
initializer/path/sampler admission, scientific/model/generality evidence, or
manuscript claim. Final focused evidence is recorded in its linked audit after
the authoritative 20/20 pass; its disposition is **PASS WITH EXPLICIT SCOPE
LIMITS**.

The forty-sixth adds only sealed explicit source-model descriptors over the
same CP45-bound capsule. It separates deterministic fixed-request replay from
a declarative finite exact-rational law on the two uint64 request coordinates.
Given a positive named conditioning event, the former has exact source TV
`1-D^(-L)` and the latter, with support s, has capsule support at most s and
source TV at least `1-s/D^L`. Acquisition and returned-result events remain
distinct and neither event's positive mass is proved. The executable
declaration cap of 4,096 atoms is separate from the analytic `D^2` current-
surface bound; inherited `L>2` excludes a product-uniform complete capsule.
Support at least `D^L` is necessary but not sufficient: exact uniformity
requires every conditional output fiber to have mass `D^(-L)`. CP46 certifies
neither external-law realization nor that balance, and source TV implies no
semantic-output TV lower bound. Ordinary models are cached descriptors;
explicit live-ancestry revalidation is separate. The frozen 24/24 evidence,
exact enumerations, static gates, hashes, and independent `P0=P1=P2=0` audits
support **PASS WITH EXPLICIT SCOPE LIMITS**, with no randomness,
freshness/independence, unconditional law, initializer/path/sampler,
scientific/model-quality/generality, or manuscript claim.

The forty-seventh adds the direct external full-capsule execution boundary.
An execution invokes at most one provider, after bounded local owner-lifetime
draw retirement, for an exact \(L\)-word uint64 tuple; the tuple is ingested
identically and passed through the exact CP43 split/join/combined route under
CP46--CP43 ancestry.
The \(D^L\) interface is not a source law. Product uniformity, IID returned
capsules across distinct draw identifiers, and the success conditions needed
to avoid value-conditioned bias remain external premises. Structural
validation does not replay source or semantics. The
frozen 31/31 evidence, 22/9 partition, post-run 22/22 fast check, static gates,
hashes, and independent `P0=P1=P2=0` audits support **PASS WITH EXPLICIT SCOPE
LIMITS**. It certifies no randomness or live law, global uniqueness, broader
concurrent or reentrant semantic safety beyond atomic duplicate reservation,
adaptive retry, output-TV, initializer/path/sampler, scientific/model-quality,
generality, or manuscript claim.

The forty-eighth adds only the exact byte-source-to-CP47 full-capsule boundary.
Its `system-os-urandom-operational` profile binds the cached ordinary
`os.urandom` Python API wrapper, and its
`external-exact-byte-block-unverified` profile binds one exact callback; both
require one exact
\(8L\)-byte block at each reached provider boundary and use the fixed manual
big-endian bijection to obtain the exact \(L\)-word tuple. The bijection
preserves total variation, but product uniformity requires joint full-block
uniformity, IID requires the corresponding distinct-draw block law, and
returned-result claims require positive return mass plus value-independent
complete CP48 success. CP47 remains the sole retirement and semantic authority.
The frozen 37/37 evidence, 28/9 partition, post-run 28/28 fast check, static
gates, hashes, and independent `P0=P1=P2=0` review support **PASS WITH EXPLICIT
SCOPE LIMITS**. The P3 asynchronous-scheduling gap remains an explicit
nonclaim. CP48 promotes no backend or operating-system law, randomness,
security, broader concurrency guarantee, output-TV, initializer/path/sampler,
scientific/model-quality, generality, or manuscript claim.

The forty-ninth adds only one sealed, assumption-gated, pointwise one-draw
CP43/CP42 object-semantic reference pushforward above exact CP48 ancestry. Its
external antecedent assumes pre-boundary fresh-draw admissibility, almost-sure
exact-block return with an unconditional jointly uniform complete byte-block
law, post-boundary complete success for every byte value, and fixed-runtime
deterministic replay-stable typed-total semantics. With CP48's bijection \(C\),
the enriched map \(T_{\mathrm{obj}}\) preserves the four natural statuses and
satisfies the recorded pushforward identity and TV data-processing upper
bound. Structural admission is nonexecuting and nonreplaying; a selected
result retains the exact nested CP42 configuration by identity and witnesses
nonempty enriched-atom and configuration-value fibers, with abstract reference
mass at least \(2^{-64L}\) only under the declared premises. The frozen
**28/28** evidence, 21/7 partition, post-run **21/21** source-independent
check, static gates, stable hashes, contained partial-repeat provenance, and
independent `P0=P1=P2=0` reviews support **PASS WITH EXPLICIT SCOPE LIMITS**.
CP49 promotes no backend law or attestation, totality or return-mass evidence,
IID or adaptive theorem, duplicate/capacity totalization, global uniqueness,
CP41-premise discharge or legacy-route equivalence, CP40 initializer
admission, formal Test 28 closure, path/sampler, scientific/model/generality,
or manuscript claim.

Native-domain transforms and Jacobians, a scalable
trainer and trained/selected checkpoint, analytic-target-preserving evaluation
as an alternative to the now-explicit operational surrogate, exact active
total-exit evaluation if required by the final algorithm, unconditional
completion beyond the bounded fail-closed local coordination layer, semantic
SIR decisions, any selected exact-ideal rejection alternative, a live/global
initializer source law, numeric CP36/CP37 failure and successful-batch laws,
universal live-failure equivalence and discharge of CP41's factorization
premise, and adaptive failure/source chronology,
the remaining initializer strategies, and a general
conditional/tilted initializer law and admission rule,
legacy tag-1 proposal-receipt
consumption, random-word-consuming terminal-wait execution, semantic tag-3
payload interpretation and coordinate-generation semantics, selected-state
coordination beyond CP39's fixed-batch positional-bootstrap scope, global or
cross-bootstrap merge/fork/one-shot address guarantees, and occurrence-stream
semantics beyond the narrow positional bootstrap prefixes,
Brownian stream consumption, coarse/fine Brownian coupling,
continuous drift, lineage-aware split-step simulation, ideal continuous-
destination distribution recovery, and any
general-cap or general-type mixed-oracle extension remain pending. The ninth
layer closes only the scoped known-law compact-path RNG by exact time reversal.
The tenth closes only the deterministic reference-clock query; it does not
construct the outward-rounded \(e^{D_\Psi}\)-controlled clock, draw a waiting
time, integrate a learned total exit, make a finite-resolution-safe acceptance
decision, or implement the learned/general path sampler. The eleventh closes
only the real-arithmetic guide range and coordinate regularity under its
normalized probability/Markov semantics. The twelfth closes only a coarse
successful-only represented scalar value/edit bridge; sharp floating-point
analysis, total evaluation, coordinate derivatives, and the aggregate
guide/residual operational clock remain pending. The thirteenth closes only
the separate residual value/state-pair and physical-coordinate certificate;
the conditional population/nuisance loss remains pending. The fourteenth
closes only successful same-candidate log-space edge composition; it does not
close the operational rate product, total learned exit, waiting/acceptance,
drift, initializer, or path. The fifteenth closes only fallback coverage of
the two declared typed point-failure classes for a new jump-only operational
surrogate after its resource preflight and under its trusted-runtime contract;
it neither preserves the analytic target nor closes the composer, rate, clock,
drift, RNG, path, or sampler layers. The sixteenth closes only the exact typed
active tiny-gate failure for a distinct checkpoint-private jump-only
operational residual; it neither preserves the exact real neural residual nor
closes the composer, rate, clock, drift, RNG, path, or sampler layers. The
seventeenth closes only explicit operational-target selection and exact-
rational, single-round log-space composition for one active process-valid
candidate. It does not preserve the analytic or conditional/posterior target
and does not close exponentiation, the rate envelope or total exit, the clock,
waiting/acceptance RNG, drift, initialization, paths, or the sampler. The
eighteenth closes exact-edge exponentiation and no-RNG instantaneous/global
upper envelopes only for that operational target. It does not compute the
active total exit, admit the route draw, implement waiting/acceptance RNG, or
close drift, initialization, paths, or the sampler. The
nineteenth closes only a successful-return local wait/route/accept operation
for the represented operational surrogate. It does not close the repeated
proposal loop, continuous-destination operational evidence, counter-keyed
streams, lineage, drift/Strang integration, initialization, paths, liveness, or
the full sampler. The twentieth separately closes bounded repetition with
rejection-clock continuation, exact rejection-parent reuse, and mandatory
accepted-state intensity/envelope refresh, but only on successful interval-
exhaustion returns. Active proposal-cap exhaustion is a refusal. It does not
upgrade the rounded renewal clock or inherited finite-resolution route, and it
does not close continuous-destination operational evidence, unconditional
completion or an exact frozen-jump law, counter-keyed streams, lineage,
drift/Strang integration, initialization, paths, liveness, or the full
sampler. The twenty-first separately closes same-runtime, post-hoc replay
custody for concrete continuous-destination routes, including both directions
of a genuinely unequal positive-dimensional replacement. It does not upgrade
the finite-output route to an exact categorical/integer/Gaussian law, bound
normal raw-word consumption, close Test 29, establish unconditional
completion, or add counter-keyed lineage, drift, initialization, paths,
liveness, or the full sampler. The twenty-second separately closes ordered
route-evidence custody across every completed proposal in one successfully
returned bounded checkpoint-twenty transcript, including exact reconstruction
from loop entry through the terminal waiting prefix to loop exit. It does not
upgrade the inherited finite-resolution route or rounded renewal clock,
establish unconditional completion or liveness, preserve an analytic or
conditional target, or add counter-keyed lineage, drift, initialization,
paths, or the full sampler. The
twenty-third separately closes only direct, injective address construction and
same-runtime reconstruction for initially unused Philox namespace receipts,
plus a deterministic persistent-lineage overlay on an already returned and
fully revalidated checkpoint-twenty-two result. It does not make checkpoint
twenty-two proposal-keyed, certify consumption of any issued stream, enforce
global run-ID uniqueness or prevent deliberate lineage forks, consume or couple
Brownian streams, implement drift or initialization, construct a path or Strang
step, or admit the full sampler. The
twenty-fourth separately closes only bounded, successful-return, same-runtime
operational-epoch-keyed execution. Every active epoch has a direct tag-6
address; every actual proposal occurs in its uniquely indexed epoch, but an
active tag-6 epoch may instead be the stochastic terminal epoch. Deterministic
terminal holds bind a tag-2 receipt without consuming a word. The checkpoint
does not consume legacy tag-1 proposal receipts or random words from tag 2,
make checkpoint twenty-two keyed, prove independence or one-shot use, consume
initializer/occurrence/Brownian streams, implement drift, initialization, a
path or Strang step, prove an exact jump law or liveness, or admit the full
sampler. The twenty-fifth separately closes only bounded, bootstrap-form,
same-runtime custody of uninterpreted tag-3 `raw64` prefixes for existing
positional lineage serials at fixed step zero. It returns the exact initial
lineage state, accepts no caller RNG, and does not define a cardinality, event,
coordinate, categorical, Gaussian, rejection, SIR, or other initializer output
law. A separate global initializer control domain, general initializer,
occurrence protocol beyond these prefixes, Brownian coupling, drift, path, and
full sampler remain open at checkpoint twenty-five. The twenty-sixth
separately closes only the bounded, law-neutral tag-7 namespace and exact
prefix custody for a canonical pre-cardinality control plan. It adds the
`initialization_index` address limb but assigns no stage/attempt semantics,
branch/retry chronology, output transform, or initializer law; it does not
coordinate the older tag-3 occurrence payloads or map accepted configurations
to lineage. Brownian coupling, drift, paths, and the full sampler remain open.
The twenty-seventh separately closes only fixed strategy/stage allocation,
multiblock work-item coordinates, complete up-front prefix materialization,
and exact parent replay. It takes no branch and defines no enumeration,
rejection, SIR, reference, finite-resolution transform, configuration, or
initializer output law; lineage and tag-3 coordination also remain open.
The twenty-eighth separately closes only the reference strategy's fixed finite
transform, exact count/type quota records, complete coordinate-padding
materialization, and duplicate-stable canonical configuration mapping. Its
law statement is conditional on hypothetical product-uniform words. It does
not certify actual Philox uniformity/independence/randomness, equality to the
continuous capped-Poisson reference, enumeration/rejection/SIR, a conditional
or tilted initializer, initializer admission, lineage/tag-3 coordination,
Brownian coupling, drift, a path, liveness, or the full sampler.
The twenty-ninth separately closes only the preregistered frozen-grid
reference-transform diagnostic and its one-shot custody. Its pass is scoped
to prespecified engineering discrepancies under hypothetical product-uniform
envelopes; it certifies no Philox law, continuous reference law, initializer
admission, model quality, scientific result, or sampler.
The thirtieth separately closes only deterministic evaluation of the selected
time-zero operational log factor at one supplied point. It does not close
factor exponentiation or normalization, support enumeration, rejection, SIR,
categorical selection, an initializer law or admission, accepted-state lineage
or tag-3 coordination, Brownian coupling, drift, a path, liveness, or the full
sampler.
The thirty-first separately closes only exact complete support enumeration and
represented-parameter base-coefficient completeness for resource-admitted
all-atomic references. It stores no normalized mass, does not exponentiate or
normalize the attached point factors, and performs no selection, rejection,
SIR, RNG, initializer-protocol binding, accepted-state lineage or tag-3
coordination, continuous-codebook construction, drift, path, liveness, or
sampler admission.
The thirty-second separately closes only directed all-atomic tilted-weight and
normalized-mass enclosures, exact proxy normalization, positive Hamilton
quotas, rigorous ideal-to-dyadic TV control, and explicit-word lookup. It does
not certify actual-word randomness, bind checkpoint twenty-seven stage 0,
admit an initializer, support mixed/continuous configurations, coordinate
lineage or tag-3 payloads, or construct drift, a path, liveness, or a sampler.
The thirty-third separately closes only the one-word checkpoint-twenty-seven
stage-0 binding for the all-atomic selector, with exact tag-7 address, parent-
word, preparation, selection, and configuration custody. For fixed preparation
\(p\), its only pushforward statement substitutes a separate abstract uniform
uint64 source \(U\) into the deterministic lookup. The abstract and live word
sources are not identified, although their realized uint64 values may
coincide. A
fixed live address has deterministic word and output point masses. It does not
certify actual Philox uniformity/independence/randomness, exact ideal-law sampling,
initializer admission, mixed/continuous support, remaining strategies,
lineage/tag-3 coordination, Brownian coupling, drift, a path, liveness, or a
sampler.
The thirty-fourth separately closes only the fixed all-atomic configuration-
constructor interface and its transitive preparation/selection custody. The
configuration is valid as an initial state, but same-address replay is
deterministic. Independently of the abstract-\(U\) premise, the preparation-level
TV bound relates only the ideal operational-surrogate law to the dyadic law;
live distributional
admission, `initializer_admissible`, actual word laws, general or
mixed/continuous initialization, lineage/tag-3 coordination, drift, path,
liveness, and sampler claims remain open or false.
The thirty-fifth separately closes only construction-time coordination from
one CP28 finite reference configuration to CP23 bootstrap lineage and bounded
CP25 tag-3 prefixes with count \(\max(1,d_j)\). The complete-capsule theorem is
counterfactual and configuration-only, the structural-TV expression is an
upper bound rather than equality, and finite-codebook fibers on such cells
have conditional TV one against analytic Gaussian fibers. The live API
fixes initialization index zero; because tag-3 addresses omit that index,
cross-initialization disjointness is not certified. Live output laws,
conditional/tilted or general initializer admission, Brownian coupling, drift,
paths, liveness, and sampler claims remain false or open.
The thirty-sixth separately closes only fixed-budget stage-1 proposal and score
preparation. Every attempt uses the exact CP28 capsule plus one reserved
uninterpreted word and records the exact CP30 \(q-U\le0\) witness. Its total
abstract map includes a distinguished failure output because scoring may fail;
it supplies neither a failure bound nor a law conditional on success. Live
randomness, decision, acceptance, selection, initializer admission,
lineage/tag-3, Brownian, drift, path, liveness, and sampler claims remain false
or open.
The thirty-seventh separately closes only the conservative one-word decision
layer over a successfully prepared CP36 batch. It certifies every exact quota
before any word-to-quota comparison, selects the first accepted attempt or
returns bounded exhaustion, and records only the fixed-data abstract-iid
outcome probability. It does not close CP36 failure probability or success-
conditional laws, identify live words with the abstract family, implement the
ideal transcendental Bernoulli exactly, normalize or admit an initializer,
coordinate selected-state lineage/tag-3 payloads, or construct Brownian motion,
drift, a path, liveness, or a sampler.
The thirty-eighth separately defines only the counterfactual finite-batch law
conditional on the direct word-free \(B\). It aggregates duplicate candidate
configurations, defines selection conditioning only for positive \(Z_B\), and
retains a strict augmented ideal/dyadic TV comparison that cannot be reused
after selection conditioning. It does not make the deterministic live trace
random, supply a CP36 successful-batch or failure law, admit a generic
initializer, repair the initialization-index gap in the lineage/tag-3
namespace, or construct Brownian motion, drift, a path, liveness, or a sampler.
The thirty-ninth separately closes only construction-time coordination of an
exact CP38 selected result with reverse-time-zero intensity, CP23 positional
bootstrap lineage, and local tag-3 prefixes whose address contains the
initialization index and selected attempt. It distinguishes a selected empty
state from exhaustion and preserves exact event identities even for structural
duplicates. It does not make the live trace random, interpret tag-3 payloads,
generate selected coordinates, provide global/cross-bootstrap/merge/fork/one-
shot address guarantees, admit an initializer, reuse CP38's TV comparison after
selection conditioning, or construct Brownian motion, drift, a path, liveness,
or a sampler. Its final software evidence is bound above, and its disposition
is **PASS WITH EXPLICIT SCOPE LIMITS**.
The fortieth separately closes only the exact finite-resolution target
conditional on the direct word-free successful batch, the correctly scaled
selected-conditioned comparison when \(Z_B>0\), and a narrow structural
state/no-state admission boundary over one exact CP39 result. It does not make
the live trace random, integrate CP36 failure or successful-batch probability,
implement exact ideal rejection or a global normalized tilted law, admit every
initializer strategy, interpret tag-3 payloads, generate coordinates, or
construct Brownian motion, drift, a path, liveness, or a sampler. Its source
and test artifacts are frozen and passed all 45 focused tests; unchanged exact-
hash CP39 direct-parent evidence remains applicable. Its status is **PASS WITH
EXPLICIT SCOPE LIMITS**.
The sixth, seventh, tenth, eleventh, twelfth,
thirteenth, fourteenth,
fifteenth,
sixteenth, seventeenth, eighteenth, nineteenth, twentieth, twenty-first,
twenty-second, twenty-third, twenty-fourth, twenty-fifth, twenty-sixth,
twenty-seventh, twenty-eighth, twenty-ninth, thirtieth, thirty-first,
thirty-second, thirty-third, thirty-fourth, thirty-fifth, thirty-sixth,
thirty-seventh, thirty-eighth, thirty-ninth, fortieth, forty-first,
forty-second, forty-third, forty-fourth, forty-fifth, forty-sixth,
forty-seventh, forty-eighth, and forty-ninth
checkpoints assume a trusted, unmodified
Python/PyTorch runtime where applicable, and none of these scoped checkpoints
admits the production sampler. They do not close
`METHOD-FREEZE/BASE-LAW`, promote novelty, or establish an empirical or
generality result; in particular, `R2-HYBRID` remains **NOT RUN**. The
confirmatory experiment is the association-aware
guide/residual versus unified
direct-conditioning comparison on one frozen noisy unordered-subset task. A
top-tier framework claim additionally requires the mixed continuous known-law
recovery experiment with the learned/sampled method, natural association in
two real domains, representative-cardinality scaling, a competitive
unconditional base, and a third real-domain result.

## Editing discipline

1. Update `claim_ledger.md` before strengthening any sentence.
2. Insert numerical results only from frozen, validated result artifacts.
3. Keep source-manuscript reproduction numbers explicitly labeled until an
   independent reproduction decision exists.
4. Write the final abstract, contribution list, Results prose, and Conclusion
   only after the result ledger freezes.
5. Move to a venue-specific LaTeX template only after the scientific identity
   and main figure/table set stabilize.
