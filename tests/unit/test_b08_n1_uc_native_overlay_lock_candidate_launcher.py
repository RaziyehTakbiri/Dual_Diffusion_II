import contextlib
import hashlib
import io
import json
import os
from pathlib import Path

import pytest


ROOT = Path(__file__).resolve().parents[2]
LAUNCHER = (
    ROOT
    / "databricks"
    / "notebooks"
    / "b08_n1_uc_native_overlay_lock_candidate_launcher.py"
)


def _load_launcher_without_automatic_main():
    source = LAUNCHER.read_text(encoding="utf-8")
    body, suffix = source.rsplit("\nmain()\n", 1)
    assert suffix == ""
    namespace = {
        "__file__": str(LAUNCHER),
        "__name__": "launcher_unit_test",
    }
    exec(compile(body + "\n", str(LAUNCHER), "exec"), namespace, namespace)
    return namespace


@pytest.fixture
def launcher():
    return _load_launcher_without_automatic_main()


def _make_repo(launcher, tmp_path, builder_payload=b"answer = 42\n"):
    notebook_dir = tmp_path / "databricks" / "notebooks"
    notebook_dir.mkdir(parents=True)
    builder_path = tmp_path / Path(launcher["BUILDER_RELATIVE_PATH"].as_posix())
    launcher_path = tmp_path / Path(
        launcher["LAUNCHER_RELATIVE_PATH"].as_posix()
    )
    builder_path.write_bytes(builder_payload)
    launcher_path.write_bytes(LAUNCHER.read_bytes())
    return tmp_path, builder_path, launcher_path


def _forbidden(label):
    def fail(*args, **kwargs):
        raise AssertionError(label)

    return fail


def _result(stdout):
    return json.loads(stdout.getvalue())


def test_default_launcher_gate_observes_bytes_but_never_compiles_or_executes(
    launcher, monkeypatch, tmp_path
):
    repo, builder, _ = _make_repo(launcher, tmp_path)
    monkeypatch.delenv(
        "HETERODIFF_B08_N1_UC_NATIVE_LAUNCHER_EXPECTED_BUILDER_SHA256",
        raising=False,
    )
    monkeypatch.setitem(launcher, "locate_repo_root", lambda: repo)
    monkeypatch.setitem(launcher, "compile", _forbidden("builder compiled"))
    monkeypatch.setitem(launcher, "exec", _forbidden("builder executed"))
    stdout = io.StringIO()
    with contextlib.redirect_stdout(stdout):
        launcher["main"]()
    result = _result(stdout)
    assert result["decision"] == "HOLD_REVIEWED_BUILDER_SHA256_REQUIRED"
    assert result["builder_executed"] is False
    assert result["observed_builder_sha256"] == hashlib.sha256(
        builder.read_bytes()
    ).hexdigest()


def test_mismatched_launcher_hash_never_compiles_or_executes(
    launcher, monkeypatch, tmp_path
):
    repo, builder, _ = _make_repo(launcher, tmp_path)
    monkeypatch.setitem(launcher, "locate_repo_root", lambda: repo)
    monkeypatch.setitem(launcher, "launcher_parameter", lambda: "f" * 64)
    monkeypatch.setitem(launcher, "compile", _forbidden("builder compiled"))
    monkeypatch.setitem(launcher, "exec", _forbidden("builder executed"))
    stdout = io.StringIO()
    with contextlib.redirect_stdout(stdout):
        launcher["main"]()
    result = _result(stdout)
    assert result["decision"] == "STOP_REVIEWED_BUILDER_SHA256_MISMATCH"
    assert result["builder_executed"] is False
    assert result["operator_expected_builder_sha256"] == "f" * 64
    assert result["observed_builder_sha256"] == hashlib.sha256(
        builder.read_bytes()
    ).hexdigest()


def test_exact_hash_compiles_and_executes_the_same_in_memory_payload_with_evidence(
    launcher, monkeypatch, tmp_path
):
    payload = b"reviewed_builder_sentinel = 73\n"
    repo, builder, launcher_path = _make_repo(launcher, tmp_path, payload)
    expected_sha256 = hashlib.sha256(payload).hexdigest()
    observed = {}
    token = object()

    def recording_compile(data, filename, mode):
        observed["compiled_payload"] = data
        observed["compiled_filename"] = filename
        observed["compiled_mode"] = mode
        observed["payload_identity"] = id(data)
        return token

    def recording_exec(code, globals_namespace, locals_namespace):
        assert code is token
        assert globals_namespace is locals_namespace
        observed["namespace"] = globals_namespace

    monkeypatch.setitem(launcher, "locate_repo_root", lambda: repo)
    monkeypatch.setitem(launcher, "launcher_parameter", lambda: expected_sha256)
    monkeypatch.setitem(launcher, "compile", recording_compile)
    monkeypatch.setitem(launcher, "exec", recording_exec)
    launcher["main"]()

    assert observed["compiled_payload"] == payload
    assert observed["compiled_filename"] == str(builder)
    assert observed["compiled_mode"] == "exec"
    namespace = observed["namespace"]
    evidence = namespace["HETERODIFF_HASH_FIRST_LAUNCH_EVIDENCE"]
    assert evidence == {
        "schema_version": launcher["LAUNCH_SCHEMA"],
        "builder_relative_path": launcher["BUILDER_RELATIVE_PATH"].as_posix(),
        "operator_expected_builder_sha256": expected_sha256,
        "executed_payload_sha256": expected_sha256,
        "executed_payload_size_bytes": len(payload),
        "launcher_relative_path": launcher["LAUNCHER_RELATIVE_PATH"].as_posix(),
        "launcher_source_sha256": hashlib.sha256(
            launcher_path.read_bytes()
        ).hexdigest(),
        "launcher_source_size_bytes": len(launcher_path.read_bytes()),
        "same_in_memory_payload_compiled_and_executed": True,
    }
    assert namespace["__file__"] == str(builder)
    assert namespace["__name__"] == "__main__"


def test_absent_builder_fails_closed_before_compile_or_exec(
    launcher, monkeypatch, tmp_path
):
    repo, builder, _ = _make_repo(launcher, tmp_path)
    builder.unlink()
    monkeypatch.setitem(launcher, "locate_repo_root", lambda: repo)
    monkeypatch.setitem(launcher, "launcher_parameter", lambda: "0" * 64)
    monkeypatch.setitem(launcher, "compile", _forbidden("builder compiled"))
    monkeypatch.setitem(launcher, "exec", _forbidden("builder executed"))
    with pytest.raises(
        RuntimeError, match="REPOSITORY_FILE_NOT_PHYSICAL_REGULAR_FILE"
    ):
        launcher["main"]()


def test_symlink_builder_fails_closed_without_touching_target(
    launcher, tmp_path
):
    target = tmp_path / "outside-builder.py"
    target.write_bytes(b"preserve = True\n")
    link = tmp_path / "builder-link.py"
    link.symlink_to(target)
    before = target.read_bytes()
    with pytest.raises(OSError):
        launcher["read_builder_once"](link)
    assert target.read_bytes() == before


def test_repository_file_read_rejects_external_ancestor_directory_symlink(
    launcher, tmp_path
):
    repo = tmp_path / "repo"
    repo.mkdir()
    external_databricks = tmp_path / "external-databricks"
    external_notebooks = external_databricks / "notebooks"
    external_notebooks.mkdir(parents=True)
    external_builder = external_notebooks / Path(
        launcher["BUILDER_RELATIVE_PATH"].name
    )
    external_builder.write_bytes(b"EXTERNAL_SENTINEL = True\n")
    (repo / "databricks").symlink_to(
        external_databricks, target_is_directory=True
    )
    before = external_builder.read_bytes()

    with pytest.raises(
        RuntimeError, match="REPOSITORY_FILE_NOT_PHYSICAL_REGULAR_FILE"
    ):
        launcher["read_repository_file_once"](
            repo, launcher["BUILDER_RELATIVE_PATH"]
        )

    assert external_builder.read_bytes() == before


def test_repository_file_read_rejects_ancestor_swapped_after_path_check(
    launcher, monkeypatch, tmp_path
):
    repo, builder, _ = _make_repo(launcher, tmp_path / "repo")
    external_databricks = tmp_path / "external-databricks"
    external_notebooks = external_databricks / "notebooks"
    external_notebooks.mkdir(parents=True)
    external_builder = external_notebooks / builder.name
    external_builder.write_bytes(b"EXTERNAL_SENTINEL = True\n")
    globals_ = launcher["read_repository_file_once"].__globals__
    original_kind = globals_["physical_relative_kind"]
    swapped = False

    def check_then_swap(root, relative):
        nonlocal swapped
        result = original_kind(root, relative)
        if not swapped:
            swapped = True
            (repo / "databricks").rename(repo / "original-databricks")
            (repo / "databricks").symlink_to(
                external_databricks, target_is_directory=True
            )
        return result

    monkeypatch.setitem(globals_, "physical_relative_kind", check_then_swap)
    monkeypatch.setitem(
        globals_,
        "read_open_descriptor_once",
        _forbidden("external leaf descriptor was opened"),
    )

    with pytest.raises(OSError):
        launcher["read_repository_file_once"](
            repo, launcher["BUILDER_RELATIVE_PATH"]
        )


def test_repo_root_discovery_rejects_external_builder_ancestor_symlink(
    launcher, monkeypatch, tmp_path
):
    candidate = tmp_path / "candidate"
    (candidate / "src" / "heterodiff").mkdir(parents=True)
    (candidate / "pyproject.toml").write_bytes(b"[project]\n")
    external_databricks = tmp_path / "external-databricks"
    external_notebooks = external_databricks / "notebooks"
    external_notebooks.mkdir(parents=True)
    external_builder = external_notebooks / Path(
        launcher["BUILDER_RELATIVE_PATH"].name
    )
    external_launcher = external_notebooks / Path(
        launcher["LAUNCHER_RELATIVE_PATH"].name
    )
    external_builder.write_bytes(b"EXTERNAL_SENTINEL = True\n")
    external_launcher.write_bytes(b"EXTERNAL_LAUNCHER = True\n")
    (candidate / "databricks").symlink_to(
        external_databricks, target_is_directory=True
    )
    monkeypatch.setitem(launcher, "__file__", str(candidate / "hint.py"))
    monkeypatch.chdir(candidate)
    monkeypatch.setenv("HETERODIFF_REPO_ROOT_OVERRIDE", str(candidate))

    with pytest.raises(RuntimeError, match="REPOSITORY_ROOT_NOT_FOUND"):
        launcher["locate_repo_root"]()


def test_nonregular_builder_fails_closed(launcher, tmp_path):
    directory = tmp_path / "builder-directory"
    directory.mkdir()
    with pytest.raises(RuntimeError, match="BUILDER_NOT_REGULAR_FILE"):
        launcher["read_builder_once"](directory)


def test_oversize_builder_fails_closed_before_payload_read(launcher, tmp_path):
    path = tmp_path / "oversize.py"
    with path.open("wb") as handle:
        handle.truncate(launcher["BUILDER_BYTE_LIMIT"] + 1)
    with pytest.raises(RuntimeError, match="BUILDER_SIZE_OUT_OF_BOUNDS"):
        launcher["read_builder_once"](path)


def test_short_read_fails_closed(launcher, monkeypatch, tmp_path):
    path = tmp_path / "short.py"
    path.write_bytes(b"123456")
    original_read = os.read
    calls = 0

    def short_read(descriptor, size):
        nonlocal calls
        calls += 1
        if calls == 1:
            return original_read(descriptor, 2)
        return b""

    monkeypatch.setattr(os, "read", short_read)
    with pytest.raises(RuntimeError, match="BUILDER_SIZE_CHANGED_DURING_READ"):
        launcher["read_builder_once"](path)


def test_growing_builder_fails_closed(launcher, monkeypatch, tmp_path):
    path = tmp_path / "growing.py"
    path.write_bytes(b"1234")
    original_read = os.read
    first = True

    def growing_read(descriptor, size):
        nonlocal first
        chunk = original_read(descriptor, size)
        if first:
            first = False
            with path.open("ab") as handle:
                handle.write(b"5")
        return chunk

    monkeypatch.setattr(os, "read", growing_read)
    with pytest.raises(RuntimeError, match="BUILDER_SIZE_CHANGED_DURING_READ"):
        launcher["read_builder_once"](path)
