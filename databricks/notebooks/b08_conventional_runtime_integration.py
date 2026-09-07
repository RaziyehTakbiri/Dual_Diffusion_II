# Databricks notebook source
"""B08 managed notebook installation and synthetic integration.

Pull this notebook, its support module, and their matching anchor together.
Attach the existing DBR 17.3 x86_64 CPU cluster. Choose Run all ONCE.
The seven cells install the pinned dependencies with Databricks %pip, restart,
build the project wheel, install it with %pip, restart, then verify and test.
Both restarts are normal command boundaries. No parameters are required.
Return the final JSON from the last cell. Do not run the diagnostic helper.
"""

from pathlib import Path
import hashlib
import importlib.util
import json
import sys

_b08_root = next(
    parent for parent in (Path.cwd(), *Path.cwd().parents)
    if (parent / "requirements/b08-conventional-runtime-controller-anchor-v1.json").is_file()
)
_b08_anchor = json.loads((_b08_root / "requirements/b08-conventional-runtime-controller-anchor-v1.json").read_bytes())
_b08_support_path = _b08_root / "databricks/notebooks/b08_conventional_runtime_support.py"
_b08_support_bytes = _b08_support_path.read_bytes()
if {"sha256": hashlib.sha256(_b08_support_bytes).hexdigest(), "size_bytes": len(_b08_support_bytes)} != {
    key: _b08_anchor["support_module"][key] for key in ("sha256", "size_bytes")
}:
    raise RuntimeError("B08_SUPPORT_SOURCE_MISMATCH_PULL_THE_COMPLETE_UPDATE")
_b08_spec = importlib.util.spec_from_file_location("b08_managed_runtime", _b08_support_path)
b08_runtime = importlib.util.module_from_spec(_b08_spec)
sys.modules[_b08_spec.name] = b08_runtime
exec(compile(_b08_support_bytes, str(_b08_support_path), "exec"), b08_runtime.__dict__)

b08_runtime.managed_action("prepare")

# COMMAND ----------

# MAGIC %pip install --upgrade --force-reinstall --only-binary=:all: --require-hashes -r /tmp/heterodiff-b08-managed-current/dependencies.lock

# COMMAND ----------

from pathlib import Path
import hashlib
import importlib.util
import json
import sys

_b08_root = next(
    parent for parent in (Path.cwd(), *Path.cwd().parents)
    if (parent / "requirements/b08-conventional-runtime-controller-anchor-v1.json").is_file()
)
_b08_anchor = json.loads((_b08_root / "requirements/b08-conventional-runtime-controller-anchor-v1.json").read_bytes())
_b08_support_path = _b08_root / "databricks/notebooks/b08_conventional_runtime_support.py"
_b08_support_bytes = _b08_support_path.read_bytes()
if {"sha256": hashlib.sha256(_b08_support_bytes).hexdigest(), "size_bytes": len(_b08_support_bytes)} != {
    key: _b08_anchor["support_module"][key] for key in ("sha256", "size_bytes")
}:
    raise RuntimeError("B08_SUPPORT_SOURCE_MISMATCH_PULL_THE_COMPLETE_UPDATE")
_b08_spec = importlib.util.spec_from_file_location("b08_managed_runtime", _b08_support_path)
b08_runtime = importlib.util.module_from_spec(_b08_spec)
sys.modules[_b08_spec.name] = b08_runtime
exec(compile(_b08_support_bytes, str(_b08_support_path), "exec"), b08_runtime.__dict__)

b08_runtime.managed_action("dependencies_restart")
dbutils.library.restartPython()

# COMMAND ----------

from pathlib import Path
import hashlib
import importlib.util
import json
import sys

_b08_root = next(
    parent for parent in (Path.cwd(), *Path.cwd().parents)
    if (parent / "requirements/b08-conventional-runtime-controller-anchor-v1.json").is_file()
)
_b08_anchor = json.loads((_b08_root / "requirements/b08-conventional-runtime-controller-anchor-v1.json").read_bytes())
_b08_support_path = _b08_root / "databricks/notebooks/b08_conventional_runtime_support.py"
_b08_support_bytes = _b08_support_path.read_bytes()
if {"sha256": hashlib.sha256(_b08_support_bytes).hexdigest(), "size_bytes": len(_b08_support_bytes)} != {
    key: _b08_anchor["support_module"][key] for key in ("sha256", "size_bytes")
}:
    raise RuntimeError("B08_SUPPORT_SOURCE_MISMATCH_PULL_THE_COMPLETE_UPDATE")
_b08_spec = importlib.util.spec_from_file_location("b08_managed_runtime", _b08_support_path)
b08_runtime = importlib.util.module_from_spec(_b08_spec)
sys.modules[_b08_spec.name] = b08_runtime
exec(compile(_b08_support_bytes, str(_b08_support_path), "exec"), b08_runtime.__dict__)

b08_runtime.managed_action("build")

# COMMAND ----------

# MAGIC %pip install --force-reinstall --no-deps /tmp/heterodiff-b08-managed-current/heterodiff-0.1.0-py3-none-any.whl

# COMMAND ----------

from pathlib import Path
import hashlib
import importlib.util
import json
import sys

_b08_root = next(
    parent for parent in (Path.cwd(), *Path.cwd().parents)
    if (parent / "requirements/b08-conventional-runtime-controller-anchor-v1.json").is_file()
)
_b08_anchor = json.loads((_b08_root / "requirements/b08-conventional-runtime-controller-anchor-v1.json").read_bytes())
_b08_support_path = _b08_root / "databricks/notebooks/b08_conventional_runtime_support.py"
_b08_support_bytes = _b08_support_path.read_bytes()
if {"sha256": hashlib.sha256(_b08_support_bytes).hexdigest(), "size_bytes": len(_b08_support_bytes)} != {
    key: _b08_anchor["support_module"][key] for key in ("sha256", "size_bytes")
}:
    raise RuntimeError("B08_SUPPORT_SOURCE_MISMATCH_PULL_THE_COMPLETE_UPDATE")
_b08_spec = importlib.util.spec_from_file_location("b08_managed_runtime", _b08_support_path)
b08_runtime = importlib.util.module_from_spec(_b08_spec)
sys.modules[_b08_spec.name] = b08_runtime
exec(compile(_b08_support_bytes, str(_b08_support_path), "exec"), b08_runtime.__dict__)

b08_runtime.managed_action("project_restart")
dbutils.library.restartPython()

# COMMAND ----------

from pathlib import Path
import hashlib
import importlib.util
import json
import sys

_b08_root = next(
    parent for parent in (Path.cwd(), *Path.cwd().parents)
    if (parent / "requirements/b08-conventional-runtime-controller-anchor-v1.json").is_file()
)
_b08_anchor = json.loads((_b08_root / "requirements/b08-conventional-runtime-controller-anchor-v1.json").read_bytes())
_b08_support_path = _b08_root / "databricks/notebooks/b08_conventional_runtime_support.py"
_b08_support_bytes = _b08_support_path.read_bytes()
if {"sha256": hashlib.sha256(_b08_support_bytes).hexdigest(), "size_bytes": len(_b08_support_bytes)} != {
    key: _b08_anchor["support_module"][key] for key in ("sha256", "size_bytes")
}:
    raise RuntimeError("B08_SUPPORT_SOURCE_MISMATCH_PULL_THE_COMPLETE_UPDATE")
_b08_spec = importlib.util.spec_from_file_location("b08_managed_runtime", _b08_support_path)
b08_runtime = importlib.util.module_from_spec(_b08_spec)
sys.modules[_b08_spec.name] = b08_runtime
exec(compile(_b08_support_bytes, str(_b08_support_path), "exec"), b08_runtime.__dict__)

b08_runtime.managed_action("verify")
