# Databricks notebook source
# MAGIC %md
# MAGIC # Source-only two-domain adapter smoke test
# MAGIC After pulling the project Git folder, choose **Run all**. No package
# MAGIC installation or Python restart is required, including in a new notebook.
# MAGIC Tiny invented examples run in a separate Python process with site packages
# MAGIC disabled. This is **SOURCE_ONLY_ADAPTER_SMOKE_NOT_INSTALLED_WHEEL**;
# MAGIC it does not extend or replace the earlier installed-wheel verification.
# MAGIC The child explicitly loads the source data submodules without the unrelated
# MAGIC legacy `heterodiff.data` initializer exports, which would require NumPy.
# MAGIC No imports are redirected in your notebook's Python session.
# MAGIC A false F061 count-compatibility result is expected for these tiny inputs.
# MAGIC No real data is opened, and no training, splitting, approval, or admission
# MAGIC takes place. The frozen 128-validation/128-test policy is unchanged.

# COMMAND ----------

from pathlib import Path
import json
import subprocess
import sys

_relative = Path('src/heterodiff/data/two_domain_supplied_input_adapter.py')
_cwd = Path.cwd()
_root = next((parent for parent in (_cwd, *_cwd.parents)
              if (parent / 'pyproject.toml').is_file()
              and (parent / _relative).is_file()), None)
if _root is None:
    raise RuntimeError('Open this notebook inside the pulled project Git folder.')

# COMMAND ----------

_child = r"""
from pathlib import Path
import importlib.machinery
import importlib.util
import json
import sys

source = (Path(sys.argv[1]) / 'src').resolve()
if not (sys.flags.isolated and sys.flags.no_site and sys.dont_write_bytecode):
    raise RuntimeError('SOURCE_ONLY_CHILD_ISOLATION_REQUIRED')
sys.path.insert(0, str(source))
import heterodiff

# Explicit source-only submodule loading. The legacy data initializer exports
# unrelated NumPy utilities; those exports are not part of this adapter smoke.
spec = importlib.machinery.ModuleSpec('heterodiff.data', loader=None, is_package=True)
spec.submodule_search_locations = [str(source / 'heterodiff' / 'data')]
data_package = importlib.util.module_from_spec(spec)
sys.modules['heterodiff.data'] = data_package
heterodiff.data = data_package
from heterodiff.data import two_domain_supplied_input_adapter as adapter

expected_adapter_path = source / 'heterodiff/data/two_domain_supplied_input_adapter.py'
if Path(adapter.__file__).resolve() != expected_adapter_path:
    raise RuntimeError('SOURCE_ONLY_ADAPTER_ORIGIN_MISMATCH')

phys_text = (
    'Time,Parameter,Value\n00:00,RecordID,101\n00:00,Age,42\n'
    '00:00,Gender,1\n00:00,Height,-1\n00:00,ICUType,2\n'
    '00:00,Weight,70\n00:10,HR,80\n00:10,HR,80\n00:10,HR,-1\n'
)
retail_row = {
    'InvoiceNo': '123456', 'StockCode': 'DEMO', 'Description': None,
    'Quantity': 2, 'InvoiceDate': (2009, 12, 1, 1, 0, 0, 0),
    'UnitPrice': '0.10', 'CustomerID': '101', 'Country': 'UK',
}
phys = adapter.adapt_physionet_record_texts((phys_text,))
retail = adapter.adapt_retail_decoded_rows((dict(retail_row), dict(retail_row)))
assert len(phys.groups[0].configuration.events) == 3
assert phys.groups[0].occurrences[0].event == phys.groups[0].occurrences[1].event
assert len(retail.groups[0].configuration.events) == 2
assert [row['row_ordinal'] for row in retail.split_rows()] == [0, 1]
assert not phys.summary()['f061_count_assessment']['compatible_with_frozen_exact_128_128_rule']
assert not retail.summary()['f061_count_assessment']['compatible_with_frozen_exact_128_128_rule']
assert not any(name in sys.modules for name in ('numpy', 'scipy', 'torch'))
print(json.dumps({
    'decision': 'PASS_TWO_DOMAIN_SUPPLIED_INPUT_ADAPTER_SYNTHETIC_SMOKE',
    'scope': 'SOURCE_ONLY_ADAPTER_SMOKE_NOT_INSTALLED_WHEEL',
    'site_packages_disabled': True,
    'legacy_data_initializer_exports_executed': False,
    'numerical_libraries_imported': False,
    'physionet': phys.summary(), 'retail': retail.summary(),
    'real_dataset_accessed': False,
    'training_or_scientific_evaluation_executed': False,
    'approval_or_admission_granted': False,
}, indent=2, sort_keys=True))
"""

# COMMAND ----------

_completed = subprocess.run(
    [sys.executable, '-I', '-S', '-B', '-c', _child, str(_root)],
    cwd=str(_root), capture_output=True, text=True, timeout=60,
)
if _completed.returncode != 0:
    raise RuntimeError('SOURCE_ONLY_ADAPTER_SMOKE_FAILED:\n' + _completed.stderr)
_result = json.loads(_completed.stdout)
print(json.dumps(_result, indent=2, sort_keys=True))
