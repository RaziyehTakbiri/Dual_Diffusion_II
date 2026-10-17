# Export-only repair of the controlled comparison

2026-09-13. The first fixed local CPU invocation failed while serializing its
first route, after eight continuous fits but before any complete route result
was written. NumPy's rank comparison produced `numpy.bool_`, which the strict
JSON encoder rejected. The original output directory
`research/fixtures/continuous_residual_capacity_cpu_2026_09_13` is preserved,
including protocol, pre-fit source bindings, empty first-route file and failure
record. No numeric comparison result from that run was displayed or inspected
before this repair.

The repair converts only that metadata flag to a Python `bool` and encodes
payloads before opening a destination file, preventing this export error from
leaving an empty new file. No target, coefficient, fitting operation, collocation
point, degree, objective, tolerance, rank threshold or numerical budget changes.

This is a disclosed local software-repair repeat of the fixed experiment, not
the prospective protocol's uninterrupted no-retry execution. A new output
directory ending `_export_repair` is used; there is no overwrite or automated
retry. The repaired run repeats all 24 routes and reports all outcomes. The
eight fits in the failed invocation are additional work, not removed from the
history or counted as successfully recorded results.
