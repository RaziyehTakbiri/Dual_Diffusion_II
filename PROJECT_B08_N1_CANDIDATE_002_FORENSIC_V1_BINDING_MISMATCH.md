# B08 N1 candidate-002 forensic V1 binding-mismatch record

## Disposition

**`READ_ONLY_FORENSIC_INVENTORY_FAILED_SAFE_HOLD`.** The exact V1 forensic
notebook stopped before directory enumeration because the current Unity Catalog
Volume FUSE view did not reproduce the prior construction run's reported root
device/inode binding.

This record is a semantic transcription of operator-supplied JSON. It does not
claim a raw-output byte hash, externally authenticated operator identity, or
externally attested execution time.

## Exact supplied outcome

- decision: `READ_ONLY_FORENSIC_INVENTORY_FAILED`;
- error type: `RuntimeError`;
- error detail: `REPORTED_SPENT_ATTEMPT_ROOT_BINDING_MISMATCH`;
- target:
  `/Volumes/development/team_eds_supplychain/b08_runtime_output/b08-n1-overlay-candidate-002`;
- control-leaf payload read performed: `false`;
- control-leaf payload read may have been performed: `false`;
- mutating filesystem operation requested: `false`;
- chmod/chown requested: `false`;
- package resolution/build/install, Spark, Databricks REST, calibration,
  training, and inference: `false`;
- Databricks-managed storage I/O may have occurred: `true`.

## Meaning

This safe HOLD is useful evidence rather than a repeated construction failure.
It confirms that device/inode continuity from the prior run cannot be used as a
portable custody primitive for this Unity Catalog Volume across the current
FUSE session. It neither proves that the path was replaced nor permits the
reader to weaken the reviewed V1 gate in place.

The V1 notebook did not enumerate the root or read either allowlisted control
leaf. The intent therefore remains unclassified as absent, zero, partial,
complete, or mismatching.

## Successor boundary

A new, separately reviewed read-only V2 may inspect only the same exact path.
It must make no historical-lineage claim and must use object-storage semantics:
bounded stable roster observation plus two matching path-based size/SHA-256
snapshots for each exact allowlisted operational-control leaf. It must never
open unexpected payloads and must truthfully disclose managed `/Volumes` I/O.

No construction retry, `candidate-003` allocation, network/build action,
canonical lock, F151/F152 state change, B08/Wave-2 closure, scientific result,
or timetable completion follows from this record. Exact project-state delta:
zero.
