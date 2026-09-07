from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

import pytest


ROOT = Path(__file__).resolve().parents[2]
SUPPORT = (
    ROOT / "databricks" / "notebooks" / "b08_conventional_runtime_support.py"
)


@pytest.fixture()
def workflow():
    specification = importlib.util.spec_from_file_location(
        "b08_staged_test_package_target", SUPPORT
    )
    assert specification is not None
    assert specification.loader is not None
    module = importlib.util.module_from_spec(specification)
    sys.modules[specification.name] = module
    specification.loader.exec_module(module)
    try:
        yield module
    finally:
        sys.modules.pop(specification.name, None)


@pytest.mark.parametrize(
    ("package_markers_present", "expected_to_pass"),
    ((False, False), (True, True)),
    ids=("missing-package-markers", "canonical-package-markers"),
)
def test_real_pytest_subprocess_needs_staged_test_package_but_never_staged_src(
    workflow,
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
    package_markers_present: bool,
    expected_to_pass: bool,
) -> None:
    if not hasattr(sys.flags, "safe_path"):
        pytest.skip("requires Python 3.11+ PYTHONSAFEPATH enforcement")
    staged_root = tmp_path / "staged"
    unit_root = staged_root / "tests" / "unit"
    unit_root.mkdir(parents=True)
    (unit_root / "test_sibling.py").write_text(
        "HELPER_VALUE = 'staged-sibling-imported'\n", encoding="utf-8"
    )
    (unit_root / "test_entry.py").write_text(
        """from pathlib import Path
import sys

from tests.unit import test_sibling


def test_sibling_import_without_staged_source_path():
    staged_root = Path(__file__).resolve().parents[2]
    assert sys.flags.safe_path is True
    normalized_sys_path = {
        str(Path(item).resolve()) for item in sys.path if item
    }
    assert str((staged_root / "src").resolve()) not in normalized_sys_path
    assert test_sibling.HELPER_VALUE == "staged-sibling-imported"
""",
        encoding="utf-8",
    )

    # Both settings are deliberate traps. The managed runner must discard
    # PYTHONPATH and replace project pytest configuration with its temporary
    # config, so neither route can expose staged src/heterodiff.
    (staged_root / "pyproject.toml").write_text(
        '[tool.pytest.ini_options]\npythonpath = ["src"]\n', encoding="utf-8"
    )
    local_package = staged_root / "src" / "heterodiff"
    local_package.mkdir(parents=True)
    (local_package / "__init__.py").write_text(
        'raise RuntimeError("STAGED_SRC_MUST_NOT_BE_IMPORTED")\n',
        encoding="utf-8",
    )
    monkeypatch.setenv("PYTHONSAFEPATH", "1")
    monkeypatch.setenv("PYTHONPATH", str(staged_root / "src"))
    monkeypatch.setenv("PYTEST_ADDOPTS", "--import-mode=importlib")

    if package_markers_present:
        for relative in workflow.TEST_PACKAGE_MARKERS:
            (staged_root / relative).write_bytes((ROOT / relative).read_bytes())

    selected = (
        "tests/unit/test_entry.py",
        "tests/unit/test_sibling.py",
    )
    monkeypatch.setattr(workflow, "TARGETED_TEST_FILES", selected)
    monkeypatch.setattr(workflow, "TARGETED_PYTEST_SELECTORS", selected)

    if not expected_to_pass:
        with pytest.raises(
            workflow.B08ConventionalRuntimeError, match="TARGETED_INTEGRATION_TESTS_FAILED"
        ) as caught:
            workflow._run_targeted_tests(staged_root)
        assert "tests" in caught.value.diagnostics["output_excerpt"]
        return

    result = workflow._run_targeted_tests(staged_root)
    assert result["returncode"] == 0
    assert result["passed"] == 1
    assert result["test_file_count"] == 2
    assert result["pytest_selectors"] == list(selected)
