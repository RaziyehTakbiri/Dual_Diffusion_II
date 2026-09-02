# B08 AWS Databricks existing-cluster data-free preflight

**Reported:** 2026-09-02  
**Candidate state:** `NO_GO_CURRENT_CLUSTER_CONFIGURATION_FOR_B08`  
**Study or test data accessed:** no  
**Capture helper executed:** no  
**Field, blocker, Formal-Test, or timetable delta:** zero

## 1. Evidence boundary

This record evaluates only the sanitized, data-free facts reported from the
existing Databricks cluster. The raw cluster export contained operator and
workspace identity metadata; those values are intentionally neither repeated
nor committed. The report is user-supplied rather than externally
authenticated, and it does not establish an administrator, reservation,
container, runtime image, or production run.

The reported preflight bound the previously reviewed helper bytes
`f1123e302f1f7731570d0649af45ed7fc881c7d4487beda29578a741d0b75642`
and the empty administrator template bytes
`f8a910f8c3d8c9458b7c68de18adcefc439fa2975f8fa83957ad2af1755ec8cf`.
It explicitly returned `DATA_FREE_LOCAL_PREFLIGHT_ONLY`,
`capture_executed=false`, and `study_or_test_data_accessed=false`.

## 2. Sanitized observed facts

| Property | Reported value |
|---|---|
| Databricks Runtime environment | `17.3` |
| Spark runtime family | `17.3.x-scala2.13` |
| Runtime selection | Machine Learning enabled |
| Compute kind | classic preview |
| Access mode | dedicated |
| Topology | single node |
| CPU architecture | `aarch64` |
| CPU count | 32 |
| Python | `3.12.3` |
| Node family | AWS `c6gd.8xlarge` |
| Automatic termination | 15 minutes |
| `/local_disk0` total bytes | 1,869,022,597,120 |
| `/local_disk0` available bytes | 1,762,609,524,736 |
| `/local_disk0` available inodes | 115,964,718 |

The raw free-space observation exceeds the frozen combined floor of
1,133,871,366,144 bytes by 628,738,158,592 bytes. This is capacity visibility
only. No exclusive, disjoint, non-sparse, quota-enforced, same-filesystem, or
durability-bound reservation was created.

Only `PYTHONHASHSEED=0` matched the exact deterministic-control contract.
`LANG` was `C.UTF-8` rather than `C`; `LC_ALL`, `TZ`, the six single-thread
controls, the four Python isolation controls reported by the cell, and the
empty accelerator selection were unset. No scientific process was launched.

## 3. No-go reasons

The current cluster configuration is ineligible for the exact B08 production
contract for five independent reasons.

1. **Custom-container incompatibility.** Databricks documents that AWS
   Graviton instance types do not support Databricks Container Services for
   dedicated compute. The reported `aarch64`/`c6gd` candidate is therefore
   incompatible with the contract's immutable custom-container requirement.
2. **Runtime incompatibility.** Databricks documents that Databricks Runtime
   for Machine Learning does not support Databricks Container Services for
   dedicated compute. The reported ML-runtime selection independently blocks
   the required container route.
3. **Deterministic controls are not installed.** The effective environment
   does not reproduce the accepted B08 CPU-only, single-threaded,
   locale/timezone, and Python-isolation controls.
4. **Storage is free space, not a reservation.** AWS documents that instance
   store is erased when its instance is stopped, hibernated, or terminated.
   The raw `/local_disk0` capacity and 15-minute automatic termination do not
   establish the required accountable reservation or commit-boundary
   durability.
5. **Effective policy values remain unresolved.** The sanitized report does
   not establish on-demand-only capacity, disabled Photon, fixed effective
   topology after policy resolution, custom image digest, or a complete
   production lock.

Official references:

- [Databricks compute configuration and Graviton limitations](https://docs.databricks.com/aws/en/compute/configure)
- [Databricks Container Services for dedicated compute](https://docs.databricks.com/aws/en/compute/custom-containers)
- [Databricks Clusters API schema](https://docs.databricks.com/api/clusters/v2/list-clusters)
- [AWS EC2 instance-store persistence](https://docs.aws.amazon.com/AWSEC2/latest/UserGuide/instance-store-lifetime.html)
- [AWS C6g/C6gd specifications](https://aws.amazon.com/ec2/instance-types/c6g/)

## 4. Required successor cluster

Do not run the qualification capture or any scientific code on the current
cluster. Create a successor whose effective, policy-resolved configuration
provides all of the following before the capture is attempted:

1. AWS classic compute with dedicated access and a fixed single-node topology;
2. an explicitly selected **x86_64**, non-fleet CPU node type;
3. a pinned **standard** Databricks Runtime, not Databricks Runtime ML;
4. Databricks Container Services enabled and an approved custom image resolved
   to an immutable `sha256:` digest;
5. `runtime_engine=STANDARD`, Photon disabled, and on-demand-only capacity with
   no spot or fallback path;
6. the exact deterministic environment specified by the B08 qualification
   contract;
7. automatic termination disabled for the bounded qualification/run window;
8. an administrator-approved storage root with at least
   1,133,871,366,144 reserved bytes and 4,096 post-reservation inodes, together
   with exclusivity, allocation, quota, filesystem, ownership, term, and
   durability receipts; and
9. a sanitized effective cluster JSON, completed administrator reservation
   record, immutable container digest, and private local capture output.

Node type, runtime build, image, storage mechanism, region, and administrator
identity must be selected from the user's actual workspace and approved
infrastructure. This record does not invent them.

## 5. Project effect

This is a terminal no-go for the **current configuration**, not for AWS
Databricks as a platform. The enum-compatibility remediation to the data-free
capture helper is an implementation correction only and does not convert this
cluster into an eligible candidate.

The marked-task view remains 62 checked / 101 open / 163 total. Fields remain
24 open / 148 closed; blockers remain 7 open / 5 closed; Formal Tests remain
`OPEN` / `OPEN` / `PENDING`; B08 and Wave 2 remain open. No calibration, data
access, training, inference, scientific entropy, result inspection, claim,
release, or submission occurred.
