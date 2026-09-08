# Databricks: factorized parity and bounded performance notebook

Notebook: `databricks/notebooks/factorized_gpu_parity_and_performance.py`.

This is a separate **source-only local-prototype** check. It does not replace the earlier installed-release receipt, modify the old notebook, use a dataset, or run the production training/validation schedule. It does not create compute, install packages, restart Python, access the network, or change environment variables. CUDA execution needs a deliberate choice and permission to use the attached compute; preparing this notebook does not itself authorize a GPU or paid run.

## First use: inspection only

1. Pull the new project files into your existing Databricks Git folder.
2. Open `databricks/notebooks/factorized_gpu_parity_and_performance` from that folder.
3. Choose **Run all**. Leave `mode` at **INSPECT_ONLY**.
4. Read the JSON output. `INSPECT_ONLY_COMPLETE` means the source folder and package metadata were inspected. It does **not** mean CUDA was detected or tested.

The fields appear directly below the notebook toolbar. If the output is `SOURCE_FOLDER_REQUIRED`, enter the **absolute workspace path of the pulled project folder containing `pyproject.toml` and `src`** into `repo_root`, then choose Run all again. You can copy a workspace file/folder path from its menu; do not enter a Git URL, `/Volumes` output path, or a local Mac path. Root detection uses the notebook path or current directory and at most eight parent levels, without a Git command. On DBR14+, local code normally starts with the notebook directory as its working directory. [Databricks workspace-file documentation](https://docs.databricks.com/aws/en/files/workspace-interact).

INSPECT_ONLY imports no PyTorch module and launches no child. It reads Python/distribution metadata and the existing `CUDA_VISIBLE_DEVICES` setting; it never calls device discovery. The earlier CPU setup may have set that variable to an empty string. The notebook explains this without modifying it.

It also reports the existing `CUBLAS_WORKSPACE_CONFIG`. For the harness's deterministic CUDA matrix operations, the execution environment must supply **`:4096:8` or `:16:8` before the child launches**. This is not a widget value and is not installed or repaired by the notebook. If inspection reports it missing or invalid, arrange the intended environment's prelaunch setting before its Python process starts, then rerun INSPECT_ONLY to confirm the exact value. CPU_REFERENCE does not require it. This is a single CUDA execution setting, not a Docker/ECR or package rebuild requirement. [PyTorch deterministic-operation documentation](https://docs.pytorch.org/docs/stable/generated/torch.use_deterministic_algorithms.html).

For an authorized owner of user-managed Databricks compute, the field is on that compute's **configuration page → Advanced → Spark → Environment variables**. Add `CUBLAS_WORKSPACE_CONFIG=:4096:8` without replacing unrelated settings, following the compute owner's normal application/startup process. If that field is policy-managed, ask the owner for this exact prelaunch setting. Do not restart shared compute or change a policy just to prepare this notebook; inspection and CPU_REFERENCE can proceed without it. [Databricks environment-variable configuration](https://docs.databricks.com/aws/en/compute/configure#environment-variables).

## Deliberately running a small test

Use these visible fields, then choose **Run all**. Parameters are strings in Databricks widgets. [Databricks widget documentation](https://docs.databricks.com/aws/en/notebooks/widgets).

| Field | CPU reference check | CUDA check, only when authorized |
| --- | --- | --- |
| `mode` | `CPU_REFERENCE` | `CUDA` |
| `device` | `cpu` | A specific visible index, initially `cuda:0` |
| `iterations` | `1` | `1` |
| `maximum_seconds` | `120` | `120` |
| `acknowledgement` | `RUN BOUNDED LOCAL TEST` | `RUN BOUNDED LOCAL TEST` |
| `repo_root` | Leave blank if detected | Leave blank if detected |

`iterations` allows 1–3. One iteration covers all four domain×method cases and includes gradients, Hessians and optimizer updates; it is not one cheap kernel call. The case roster and parity tolerances are not user-adjustable widgets. `maximum_seconds` allows 5–300 and covers child startup/imports as well as execution. Timeout kills the local child and allows up to five additional seconds to confirm termination. It never turns a partial or timed-out run into a pass. If termination is not confirmed, stop and inspect the attached compute before another attempt. The timeout does not stop a Databricks cluster or guarantee release of a malfunctioning GPU driver.

CUDA uses **one explicitly selected device**, not eight-device distributed training. `cuda:0` means the first GPU visible to the process, not necessarily the physical GPU numbered zero. No automatic CPU fallback is permitted. The subprocess uses the current notebook Python executable and the selected source `src` directory; no imports are redirected in the notebook session. Third-party packages come from that existing interpreter environment.

CPU_REFERENCE performs CPU tensor computation and does not explicitly discover or synchronize CUDA in the harness. Standard PyTorch optimizer internals may still probe accelerator availability; this mode is not advertised as zero CUDA-library inspection. The stricter no-Torch/no-device-query promise applies to INSPECT_ONLY. The standard optimizer implementation is not patched to suppress its internal checks.

## Reading the result

- `INSPECT_ONLY_COMPLETE`: no numerical test or CUDA query ran.
- `INPUT_REQUIRED`: one of the visible mode/device/limit/acknowledgement values needs correction; no test launched.
- `CUDA_HIDDEN_BY_EXISTING_ENVIRONMENT`: the existing visibility setting hides GPUs. Do not rerun the earlier CPU-only bootstrap. Use the intended existing GPU environment and review its setting; the notebook changes nothing.
- `CUDA_PRELAUNCH_CONFIG_REQUIRED`: supply `CUBLAS_WORKSPACE_CONFIG=:4096:8` (or `:16:8`) through the intended execution environment before launch, then confirm it in INSPECT_ONLY. No CUDA child launched and the notebook did not mutate the environment.
- `STOP_LOCAL_QUALIFICATION` with a CPU-only PyTorch message: this notebook session lacks a CUDA-enabled build. Use an already appropriate environment on the intended compute or report the message before making a package change. The notebook will not reinstall PyTorch or suggest Docker/ECR.
- `STOP_LOCAL_WALL_TIME_LIMIT`: the bounded child did not finish; no pass and no silent retry.
- `LOCAL_HARNESS_COMPLETED_REVIEW_RESULT`: inspect the nested harness `result`. A completed wrapper is **not** a parity pass. The harness distinguishes CPU reference execution, CUDA not executed, and an actual CUDA qualification result.

After a test, return `mode` to INSPECT_ONLY for subsequent inspection-only runs. Keep the JSON output with the reported runtime, device, tolerances and bounded workload. Synthetic timing is not a production throughput forecast or a scientific quality result; CPU execution cannot certify GPU parity.

The accompanying unit tests exercise widget/default behavior, bounded root finding, metadata-only execution without numerical imports, strict mode/device/limit controls, unchanged GPU visibility, isolated child import selection, CPU-only-build error handling and local timeout termination. Fake CUDA metadata in wrapper tests is never a GPU test. Actual hardware execution must be recorded separately by the harness.

A separate actual supervised CPU-reference integration was run locally on 2026-09-08 using Python3.11.5/PyTorch2.12.1. Its four domain×method cases and exact same-device replays passed, with `PASS_CPU_REFERENCE_CUDA_NOT_EXECUTED` and zero explicit CUDA synchronization calls. This verifies the notebook-to-source-harness connection, not execution on Databricks or GPU parity. The current harness's physical check is one fixed-increment Heun step, not a complete conditional trajectory or an F105 production checkpoint run.
