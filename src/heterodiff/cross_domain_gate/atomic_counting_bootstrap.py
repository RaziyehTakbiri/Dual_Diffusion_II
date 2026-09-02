"""Source-only process bootstrap for the atomic-counting reference gate.

This file is the sole admitted Python entry point for the gate's executor,
workers, auditor, evidence publisher, and focused test processes.  Invoke it
by its repository-relative filesystem path and with all three startup flags::

    python -S -s -B \
      src/heterodiff/cross_domain_gate/atomic_counting_bootstrap.py probe

The bootstrap deliberately imports only :mod:`sys` until it has replaced the
interpreter's startup path.  It then constructs ``sys.path`` from the selected
interpreter's standard-library directories, the exact repository ``src``
directory, and the selected interpreter's site-packages directory.  It never
calls ``site.main`` and never processes a ``.pth`` file.

The role grammar is intentionally closed.  A role-specific implementation is
loaded only after path, interpreter, repository-tree, bytecode, and temporary
cache invariants pass.  The bootstrap creates no receipt, audit, evidence
bundle, or gate decision itself.
"""

from __future__ import annotations

# ``sys`` is built in.  Do not add an import above the provisional path reset:
# a caller-controlled PYTHONPATH or the direct-script directory must not get an
# opportunity to impersonate a standard-library module.
import sys as _sys


BOOTSTRAP_SCHEMA = "heterodiff-atomic-counting-source-bootstrap-v1"

_BOOTSTRAP_RELATIVE_PATH = (
    "src/heterodiff/cross_domain_gate/atomic_counting_bootstrap.py"
)
_EVIDENCE_OUTPUT = (
    "research/evidence/"
    "cross_domain_atomic_counting_reference_gate_v1_20260722"
)
_FOCUSED_TEST_PATHS = (
    "tests/unit/test_atomic_counting_grid.py",
    "tests/unit/test_atomic_counting_reference.py",
    "tests/unit/test_cross_domain_counting_fixtures.py",
    "tests/unit/test_cross_domain_counting_windows.py",
    "tests/unit/test_atomic_counting_evidence.py",
    "tests/integration/test_cross_domain_atomic_counting_evidence.py",
    "tests/unit/test_atomic_counting_execution.py",
    "tests/unit/test_atomic_counting_audit.py",
    "tests/unit/test_atomic_counting_reference_torch.py",
    "tests/integration/test_cross_domain_atomic_counting_training_torch.py",
)
_ROLES = frozenset(
    {
        "audit-parent",
        "audit-worker",
        "evidence-runner",
        "execution-parent",
        "focused-pytest",
        "probe",
        "training-worker",
    }
)
_PINNED_ROLES = frozenset(
    {
        "audit-parent",
        "audit-worker",
        "evidence-runner",
        "execution-parent",
        "training-worker",
    }
)
_LOWER_HEX = frozenset("0123456789abcdef")
_EXECUTABLE_IDENTITIES = {
    "base": {
        "implementation": "cpython",
        "python_version": "3.9.13",
        "sha256": "b82a1dcaab6a6deae7a574bdbad8e5299909930664cb585f4a0116b905131582",
        "size_bytes": 4003360,
    },
    "pinned": {
        "implementation": "cpython",
        "python_version": "3.11.5",
        "sha256": "ff2d7180d4aa2dcc03193194c1999509239e00101ade54fcdd736d9fc25bd0c6",
        "size_bytes": 152624,
    },
}
_ATTESTATION_ENVIRONMENT_FIELDS = (
    "HETERODIFF_BOOTSTRAP_SCHEMA",
    "HETERODIFF_BOOTSTRAP_SHA256",
    "HETERODIFF_PYTHON_EXECUTABLE_SHA256",
    "HETERODIFF_PYTHON_EXECUTABLE_SIZE",
    "HETERODIFF_PYTHON_IMPLEMENTATION",
    "HETERODIFF_PYTHON_VERSION",
)
_ALLOWED_STARTUP_PYTHON_ENVIRONMENT = {
    "PYTHONDONTWRITEBYTECODE": "1",
    "PYTHONHASHSEED": "0",
    "PYTHONNOUSERSITE": "1",
}
_FROZEN_STARTUP_FLAGS = {
    "bytes_warning": 0,
    "debug": 0,
    "dev_mode": False,
    "dont_write_bytecode": 1,
    "hash_randomization": 0,
    "ignore_environment": 0,
    "inspect": 0,
    "interactive": 0,
    "isolated": 0,
    "no_site": 1,
    "no_user_site": 1,
    "optimize": 0,
    "quiet": 0,
    "utf8_mode": 1,
    "verbose": 0,
}


class AtomicCountingBootstrapError(RuntimeError):
    """A source-bound bootstrap invariant or frozen argument failed."""


def _provisional_stdlib_candidates():
    """Derive paths without importing a path-manipulation module."""

    major = _sys.version_info[0]
    minor = _sys.version_info[1]
    prefix = _sys.base_prefix.rstrip("/\\")
    if _sys.platform == "win32":
        return (
            prefix + "\\python{}{}.zip".format(major, minor),
            prefix + "\\Lib",
            prefix + "\\DLLs",
        )
    version = "python{}.{}".format(major, minor)
    library = prefix + "/lib/" + version
    return (
        prefix + "/lib/python{}{}.zip".format(major, minor),
        library,
        library + "/lib-dynload",
    )


_STARTUP_PATH = tuple(_sys.path)
_STARTUP_FLAG_ERROR = None
if not (
    _sys.flags.no_site == 1
    and _sys.flags.no_user_site == 1
    and _sys.flags.dont_write_bytecode == 1
):
    _STARTUP_FLAG_ERROR = (
        "bootstrap requires the interpreter startup flags -S -s -B"
    )

# This is a provisional standard-library-only path.  Nonexistent candidates
# are harmless for the first frozen/builtin imports and are removed below.
_sys.path[:] = list(_provisional_stdlib_candidates())
_sys.path_importer_cache.clear()

import os as _os
import stat as _stat


def _canonical_existing_stdlib_paths():
    result = []
    for candidate in _provisional_stdlib_candidates():
        if not _os.path.exists(candidate):
            continue
        canonical = _os.path.realpath(candidate)
        if not _os.path.isabs(canonical):
            raise AtomicCountingBootstrapError(
                "a standard-library path is not absolute"
            )
        if canonical not in result:
            result.append(canonical)
    if not result:
        raise AtomicCountingBootstrapError(
            "selected interpreter has no discoverable standard-library path"
        )
    return tuple(result)


_STDLIB_PATHS = _canonical_existing_stdlib_paths()
_sys.path[:] = list(_STDLIB_PATHS)
_sys.path_importer_cache.clear()

# Every remaining import resolves through the now-sanitized standard-library
# path.  In particular, repository and dependency paths are not present yet.
import hashlib as _hashlib
import importlib.machinery as _machinery
import importlib.util as _importlib_util
import json as _json
import tempfile as _tempfile


def _canonical_json_bytes(value):
    return _json.dumps(
        value,
        allow_nan=False,
        ensure_ascii=True,
        separators=(",", ":"),
        sort_keys=True,
    ).encode("utf-8")


def _ancestor(path, levels):
    result = path
    for _unused in range(levels):
        result = _os.path.dirname(result)
    return result


def _require_regular_file(path, *, name, maximum_bytes=None):
    flags = _os.O_RDONLY | getattr(_os, "O_CLOEXEC", 0)
    flags |= getattr(_os, "O_NOFOLLOW", 0)
    try:
        descriptor = _os.open(path, flags)
    except OSError as error:
        raise AtomicCountingBootstrapError(
            "{} cannot be opened as a source-bound file".format(name)
        ) from error
    try:
        before = _os.fstat(descriptor)
        if not _stat.S_ISREG(before.st_mode):
            raise AtomicCountingBootstrapError(
                "{} must be a regular file".format(name)
            )
        if maximum_bytes is not None and before.st_size > maximum_bytes:
            raise AtomicCountingBootstrapError(
                "{} exceeds its byte ceiling".format(name)
            )
        chunks = []
        remaining = before.st_size
        while remaining:
            chunk = _os.read(descriptor, min(remaining, 1024 * 1024))
            if not chunk:
                raise AtomicCountingBootstrapError(
                    "{} was truncated while reading".format(name)
                )
            chunks.append(chunk)
            remaining -= len(chunk)
        if _os.read(descriptor, 1):
            raise AtomicCountingBootstrapError(
                "{} grew while reading".format(name)
            )
        after = _os.fstat(descriptor)
        before_identity = (
            before.st_dev,
            before.st_ino,
            before.st_size,
            before.st_mtime_ns,
            before.st_ctime_ns,
        )
        after_identity = (
            after.st_dev,
            after.st_ino,
            after.st_size,
            after.st_mtime_ns,
            after.st_ctime_ns,
        )
        if before_identity != after_identity:
            raise AtomicCountingBootstrapError(
                "{} changed while reading".format(name)
            )
        return b"".join(chunks), before
    finally:
        _os.close(descriptor)


def _project_layout():
    supplied = _os.path.abspath(__file__)
    bootstrap = _os.path.realpath(supplied)
    if supplied != bootstrap:
        raise AtomicCountingBootstrapError(
            "bootstrap path must not contain a symbolic-link component"
        )
    root = _ancestor(bootstrap, 4)
    expected = _os.path.join(
        root,
        "src",
        "heterodiff",
        "cross_domain_gate",
        "atomic_counting_bootstrap.py",
    )
    if bootstrap != expected:
        raise AtomicCountingBootstrapError(
            "bootstrap is not at its exact repository-relative path"
        )
    cwd = _os.path.abspath(_os.getcwd())
    if cwd != _os.path.realpath(cwd) or cwd != root:
        raise AtomicCountingBootstrapError(
            "bootstrap working directory must be the canonical repository root"
        )
    source = _os.path.join(root, "src")
    tests = _os.path.join(root, "tests")
    for path, name in ((root, "repository root"), (source, "src"), (tests, "tests")):
        try:
            observed = _os.lstat(path)
        except OSError as error:
            raise AtomicCountingBootstrapError(
                "{} directory is unavailable".format(name)
            ) from error
        if not _stat.S_ISDIR(observed.st_mode) or _stat.S_ISLNK(observed.st_mode):
            raise AtomicCountingBootstrapError(
                "{} must be a nonsymlink directory".format(name)
            )
    return root, source, tests, bootstrap


def _parse_pyvenv_cfg(path):
    raw, _identity = _require_regular_file(
        path, name="pyvenv.cfg", maximum_bytes=16 * 1024
    )
    try:
        text = raw.decode("utf-8")
    except UnicodeDecodeError as error:
        raise AtomicCountingBootstrapError("pyvenv.cfg is not UTF-8") from error
    values = {}
    for raw_line in text.splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#"):
            continue
        if "=" not in line:
            raise AtomicCountingBootstrapError("pyvenv.cfg has a malformed line")
        key, value = (piece.strip() for piece in line.split("=", 1))
        folded = key.casefold()
        if not key or folded in values:
            raise AtomicCountingBootstrapError(
                "pyvenv.cfg has an empty or duplicate key"
            )
        values[folded] = value
    version = values.get("version")
    expected_prefix = "{}.{}".format(
        _sys.version_info[0], _sys.version_info[1]
    )
    if version is None or not (
        version == expected_prefix or version.startswith(expected_prefix + ".")
    ):
        raise AtomicCountingBootstrapError(
            "pyvenv.cfg version does not match the selected interpreter"
        )
    if values.get("include-system-site-packages", "false").casefold() != "false":
        raise AtomicCountingBootstrapError(
            "gate virtual environment must exclude system site-packages"
        )
    return values


def _selected_site_packages(root):
    executable = _os.path.abspath(_sys.executable)
    if not executable or not _os.path.isabs(executable):
        raise AtomicCountingBootstrapError(
            "selected interpreter does not expose an absolute executable path"
        )
    executable_directory = _os.path.dirname(executable)
    candidate_root = _os.path.dirname(executable_directory)
    configuration = _os.path.join(candidate_root, "pyvenv.cfg")
    venv_root = None
    if _os.path.lexists(configuration):
        if _os.path.islink(configuration):
            raise AtomicCountingBootstrapError("pyvenv.cfg must not be a symlink")
        _parse_pyvenv_cfg(configuration)
        venv_root = _os.path.realpath(candidate_root)

    major = _sys.version_info[0]
    minor = _sys.version_info[1]
    if _sys.platform == "win32":
        site = _os.path.join(venv_root or _sys.base_prefix, "Lib", "site-packages")
    else:
        site = _os.path.join(
            venv_root or _sys.base_prefix,
            getattr(_sys, "platlibdir", "lib"),
            "python{}.{}".format(major, minor),
            "site-packages",
        )
    site = _os.path.realpath(site)
    try:
        observed = _os.lstat(site)
    except OSError as error:
        raise AtomicCountingBootstrapError(
            "selected interpreter site-packages directory is unavailable"
        ) from error
    if not _stat.S_ISDIR(observed.st_mode) or _stat.S_ISLNK(observed.st_mode):
        raise AtomicCountingBootstrapError(
            "selected interpreter site-packages must be a nonsymlink directory"
        )
    return executable, _os.path.realpath(executable), venv_root, (site,)


def _is_within(path, directory):
    try:
        return _os.path.commonpath((path, directory)) == directory
    except ValueError:
        return False


def _forbidden_repository_import_artifacts(source, tests):
    native_suffixes = tuple(
        suffix.casefold() for suffix in _machinery.EXTENSION_SUFFIXES
    ) + (".so", ".pyd", ".dylib", ".dll")
    forbidden_plain = (".pyc", ".pyo", ".zip", ".pth")
    violations = []
    for tree in (source, tests):
        for directory, directories, files in _os.walk(tree, topdown=True):
            directories.sort()
            files.sort()
            retained = []
            for name in directories:
                path = _os.path.join(directory, name)
                observed = _os.lstat(path)
                relative = _os.path.relpath(path, _os.path.dirname(source))
                if _stat.S_ISLNK(observed.st_mode):
                    violations.append(relative + " [symlink-directory]")
                    continue
                if not _stat.S_ISDIR(observed.st_mode):
                    violations.append(relative + " [non-directory]")
                    continue
                # PEP 3147 caches are never traversed or importable: -B
                # prevents new writes and the repository path hook below uses
                # a source-only loader whose get_code never consults pyc.
                if name == "__pycache__":
                    continue
                retained.append(name)
            directories[:] = retained
            for name in files:
                path = _os.path.join(directory, name)
                observed = _os.lstat(path)
                relative = _os.path.relpath(path, _os.path.dirname(source))
                if _stat.S_ISLNK(observed.st_mode):
                    violations.append(relative + " [symlink-file]")
                    continue
                if not _stat.S_ISREG(observed.st_mode):
                    violations.append(relative + " [non-regular-file]")
                    continue
                folded = name.casefold()
                if folded.endswith(forbidden_plain) or folded.endswith(native_suffixes):
                    violations.append(relative)
    return tuple(sorted(violations))


def _require_clean_repository_import_tree(source, tests):
    violations = _forbidden_repository_import_artifacts(source, tests)
    if violations:
        sample = ", ".join(violations[:8])
        if len(violations) > 8:
            sample += ", ..."
        raise AtomicCountingBootstrapError(
            "repository src/tests contain {} unbound import artifact(s): {}".format(
                len(violations), sample
            )
        )


class _RepositorySourceLoader(_machinery.SourceFileLoader):
    """Compile repository modules from source without consulting bytecode."""

    def get_code(self, fullname):
        source_path = self.get_filename(fullname)
        source = self.get_data(source_path)
        return self.source_to_code(source, source_path)


def _install_repository_source_hook(source, tests):
    source_roots = (
        _os.path.realpath(source),
        _os.path.realpath(tests),
    )

    def source_only_path_hook(path):
        canonical = _os.path.realpath(_os.fspath(path))
        if not any(
            _is_within(canonical, source_root)
            for source_root in source_roots
        ):
            raise ImportError
        return _machinery.FileFinder(
            canonical,
            (_RepositorySourceLoader, _machinery.SOURCE_SUFFIXES),
        )

    _sys.path_hooks.insert(0, source_only_path_hook)
    for key in tuple(_sys.path_importer_cache):
        try:
            canonical = _os.path.realpath(_os.fspath(key))
        except TypeError:
            continue
        if any(
            _is_within(canonical, source_root)
            for source_root in source_roots
        ):
            _sys.path_importer_cache.pop(key, None)


def _untrusted_preimport_modules(bootstrap, stdlib_paths):
    violations = []
    for name, module in sorted(_sys.modules.items()):
        origin = getattr(getattr(module, "__spec__", None), "origin", None)
        if origin in (None, "built-in", "frozen"):
            continue
        try:
            canonical = _os.path.realpath(_os.fspath(origin))
        except TypeError:
            violations.append(name)
            continue
        if canonical == bootstrap or any(
            _is_within(canonical, directory) for directory in stdlib_paths
        ):
            continue
        violations.append(name)
    return tuple(violations)


def _environment_inputs(role):
    required = {
        "MKL_NUM_THREADS": "1",
        "OMP_NUM_THREADS": "1",
        "PYTHONHASHSEED": "0",
    }
    for name, expected in required.items():
        if _os.environ.get(name) != expected:
            raise AtomicCountingBootstrapError(
                "effective {} must be exactly {} before interpreter startup".format(
                    name, expected
                )
            )
    if _os.environ.get("PYTHONHOME"):
        raise AtomicCountingBootstrapError(
            "PYTHONHOME is forbidden for the source-bound bootstrap"
        )
    python_environment = {
        name: value
        for name, value in _os.environ.items()
        if name.startswith("PYTHON")
    }
    forbidden_python_environment = {
        name: value
        for name, value in python_environment.items()
        if name not in _ALLOWED_STARTUP_PYTHON_ENVIRONMENT
        or value != _ALLOWED_STARTUP_PYTHON_ENVIRONMENT[name]
    }
    if forbidden_python_environment:
        raise AtomicCountingBootstrapError(
            "startup-affecting PYTHON* environment channels are forbidden"
        )
    if (
        "PYTEST_DISABLE_PLUGIN_AUTOLOAD" in _os.environ
        and _os.environ["PYTEST_DISABLE_PLUGIN_AUTOLOAD"] != "1"
    ):
        raise AtomicCountingBootstrapError(
            "PYTEST_DISABLE_PLUGIN_AUTOLOAD must be exactly 1 when present"
        )
    runtime_injected = {}
    if _sys.platform == "darwin":
        owner = getattr(_os, "getuid", lambda: None)()
        runtime_injected = {
            "LC_CTYPE": "C.UTF-8",
            "__CF_USER_TEXT_ENCODING": "0x{:X}:0x0:0x0".format(owner),
        }
        if any(
            _os.environ.get(name) != expected
            for name, expected in runtime_injected.items()
        ):
            raise AtomicCountingBootstrapError(
                "macOS/CPython runtime-injected startup environment differs "
                "from the frozen baseline"
            )
    allowed_names = set(required)
    allowed_names.update(_ALLOWED_STARTUP_PYTHON_ENVIRONMENT)
    allowed_names.add("PYTEST_DISABLE_PLUGIN_AUTOLOAD")
    allowed_names.update(runtime_injected)
    if role in ("audit-parent", "focused-pytest"):
        allowed_names.add("PATH")
        path = _os.environ.get("PATH")
        if (
            not path
            or _os.pathsep in path
            or not _os.path.isabs(path)
            or path != _os.path.realpath(path)
        ):
            raise AtomicCountingBootstrapError(
                "audit/focused startup PATH must be one canonical absolute directory"
            )
        try:
            path_status = _os.lstat(path)
        except OSError as error:
            raise AtomicCountingBootstrapError(
                "audit/focused startup PATH directory is unavailable"
            ) from error
        if not _stat.S_ISDIR(path_status.st_mode) or _stat.S_ISLNK(
            path_status.st_mode
        ):
            raise AtomicCountingBootstrapError(
                "audit/focused startup PATH must be a nonsymlink directory"
            )
    unexpected = sorted(set(_os.environ) - allowed_names)
    if unexpected:
        raise AtomicCountingBootstrapError(
            "startup environment inventory contains unbound channels: {}".format(
                ", ".join(unexpected[:8])
            )
        )
    return {
        "path": _os.environ.get("PATH"),
        "pythonpath_was_present": "PYTHONPATH" in _os.environ,
        "required": required,
    }


def _require_startup_semantics(role):
    mismatches = []
    for name, expected in sorted(_FROZEN_STARTUP_FLAGS.items()):
        if getattr(_sys.flags, name, None) != expected:
            mismatches.append(name)
    optional_flags = {
        "int_max_str_digits": -1,
        "safe_path": False,
        "warn_default_encoding": 0,
    }
    for name, expected in sorted(optional_flags.items()):
        if hasattr(_sys.flags, name) and getattr(_sys.flags, name) != expected:
            mismatches.append(name)
    if mismatches:
        raise AtomicCountingBootstrapError(
            "interpreter startup flags differ from the frozen baseline: {}".format(
                ", ".join(mismatches)
            )
        )
    if getattr(_sys, "_xoptions", None) != {}:
        raise AtomicCountingBootstrapError(
            "interpreter -X options differ from the frozen baseline"
        )
    expected_warnoptions = ["error"] if role == "training-worker" else []
    if list(_sys.warnoptions) != expected_warnoptions:
        raise AtomicCountingBootstrapError(
            "interpreter warning options differ from the frozen role baseline"
        )


def _replace_environment(role, inputs, prefix, attestation):
    required = inputs["required"]
    allowed = {
        "MKL_NUM_THREADS": required["MKL_NUM_THREADS"],
        "OMP_NUM_THREADS": required["OMP_NUM_THREADS"],
        "PYTHONDONTWRITEBYTECODE": "1",
        "PYTHONHASHSEED": required["PYTHONHASHSEED"],
        "PYTHONNOUSERSITE": "1",
        "PYTHONPYCACHEPREFIX": prefix,
        "PYTEST_DISABLE_PLUGIN_AUTOLOAD": "1",
        "HETERODIFF_BOOTSTRAP_SCHEMA": attestation["schema"],
        "HETERODIFF_BOOTSTRAP_SHA256": attestation["bootstrap_sha256"],
        "HETERODIFF_PYTHON_EXECUTABLE_SHA256": attestation[
            "executable_sha256"
        ],
        "HETERODIFF_PYTHON_EXECUTABLE_SIZE": str(
            attestation["executable_size_bytes"]
        ),
        "HETERODIFF_PYTHON_IMPLEMENTATION": attestation[
            "python_implementation"
        ],
        "HETERODIFF_PYTHON_VERSION": attestation["python_version"],
    }
    # The current audit parent resolves the separately frozen base interpreter
    # before launching it.  PATH has no import effect after the exact sys.path
    # replacement, and every child independently checks executable bytes.
    if role in ("audit-parent", "focused-pytest") and inputs["path"]:
        allowed["PATH"] = inputs["path"]
    _os.environ.clear()
    _os.environ.update(allowed)


def _observed_executable_identity(real_executable):
    raw, observed = _require_regular_file(
        real_executable,
        name="resolved Python executable",
        maximum_bytes=8 * 1024 * 1024,
    )
    result = {
        "executable_sha256": _hashlib.sha256(raw).hexdigest(),
        "executable_size_bytes": observed.st_size,
        "python_implementation": _sys.implementation.name,
        "python_version": "{}.{}.{}".format(*_sys.version_info[:3]),
    }
    matches = []
    for name, expected in _EXECUTABLE_IDENTITIES.items():
        if result == {
            "executable_sha256": expected["sha256"],
            "executable_size_bytes": expected["size_bytes"],
            "python_implementation": expected["implementation"],
            "python_version": expected["python_version"],
        }:
            matches.append(name)
    if len(matches) != 1:
        raise AtomicCountingBootstrapError(
            "resolved Python executable differs from both frozen identities"
        )
    result["identity"] = matches[0]
    return result


def _create_pycache_prefix():
    path = _tempfile.mkdtemp(prefix="heterodiff-atomic-counting-pycache-")
    _os.chmod(path, 0o700)
    observed = _os.lstat(path)
    owner = getattr(_os, "getuid", lambda: observed.st_uid)()
    if (
        not _stat.S_ISDIR(observed.st_mode)
        or _stat.S_ISLNK(observed.st_mode)
        or observed.st_uid != owner
        or _stat.S_IMODE(observed.st_mode) != 0o700
        or _os.listdir(path)
    ):
        raise AtomicCountingBootstrapError(
            "fresh pycache prefix is not empty and owner-only"
        )
    _sys.pycache_prefix = path
    _os.environ["PYTHONPYCACHEPREFIX"] = path
    return path, (
        observed.st_dev,
        observed.st_ino,
        observed.st_uid,
        _stat.S_IMODE(observed.st_mode),
    )


def _remove_empty_pycache_prefix(path, identity):
    if path is None:
        return
    observed = _os.lstat(path)
    current = (
        observed.st_dev,
        observed.st_ino,
        observed.st_uid,
        _stat.S_IMODE(observed.st_mode),
    )
    if current != identity or not _stat.S_ISDIR(observed.st_mode):
        raise AtomicCountingBootstrapError(
            "pycache prefix identity changed during bootstrap execution"
        )
    if _os.listdir(path):
        raise AtomicCountingBootstrapError(
            "pycache prefix is no longer empty despite -B"
        )
    _os.rmdir(path)


def _prepare(role):
    if _STARTUP_FLAG_ERROR is not None:
        raise AtomicCountingBootstrapError(_STARTUP_FLAG_ERROR)
    _require_startup_semantics(role)
    if "site" in _sys.modules:
        raise AtomicCountingBootstrapError(
            "site was imported before the source-bound bootstrap"
        )
    root, source, tests, bootstrap = _project_layout()
    environment_inputs = _environment_inputs(role)
    executable, real_executable, venv_root, site_packages = (
        _selected_site_packages(root)
    )
    exact_path = _STDLIB_PATHS + (source,) + site_packages
    if len(set(exact_path)) != len(exact_path):
        raise AtomicCountingBootstrapError("exact bootstrap sys.path has duplicates")
    if any(not _os.path.isabs(path) for path in exact_path):
        raise AtomicCountingBootstrapError("exact bootstrap sys.path is not absolute")
    _sys.path[:] = list(exact_path)
    _sys.path_importer_cache.clear()
    _install_repository_source_hook(source, tests)
    untrusted = _untrusted_preimport_modules(bootstrap, _STDLIB_PATHS)
    if untrusted:
        raise AtomicCountingBootstrapError(
            "untrusted module(s) were imported before bootstrap setup: {}".format(
                ", ".join(untrusted[:8])
            )
        )
    _require_clean_repository_import_tree(source, tests)
    prefix, prefix_identity = _create_pycache_prefix()
    raw, _bootstrap_identity = _require_regular_file(
        bootstrap, name="bootstrap source", maximum_bytes=1024 * 1024
    )
    bootstrap_sha256 = _hashlib.sha256(raw).hexdigest()
    executable_identity = _observed_executable_identity(real_executable)
    attestation = {
        "schema": BOOTSTRAP_SCHEMA,
        "bootstrap_sha256": bootstrap_sha256,
        "executable_sha256": executable_identity["executable_sha256"],
        "executable_size_bytes": executable_identity["executable_size_bytes"],
        "python_implementation": executable_identity["python_implementation"],
        "python_version": executable_identity["python_version"],
    }
    _replace_environment(
        role, environment_inputs, prefix, attestation
    )
    return {
        "attestation": attestation,
        "bootstrap": bootstrap,
        "bootstrap_sha256": bootstrap_sha256,
        "executable": executable,
        "executable_identity": executable_identity,
        "hash_seed": environment_inputs["required"]["PYTHONHASHSEED"],
        "prefix": prefix,
        "prefix_identity": prefix_identity,
        "pythonpath_was_present": environment_inputs[
            "pythonpath_was_present"
        ],
        "real_executable": real_executable,
        "root": root,
        "site_packages": site_packages,
        "source": source,
        "tests": tests,
        "venv_root": venv_root,
    }


def _probe_payload(context):
    prefix = context["prefix"]
    observed = _os.lstat(prefix)
    owner = getattr(_os, "getuid", lambda: observed.st_uid)()
    return {
        "bootstrap_path": _BOOTSTRAP_RELATIVE_PATH,
        "bootstrap_schema": BOOTSTRAP_SCHEMA,
        "bootstrap_sha256": context["bootstrap_sha256"],
        "cwd_excluded_from_sys_path": context["root"] not in _sys.path,
        "descendant_attestation": dict(context["attestation"]),
        "descendant_attestation_environment_fields": list(
            _ATTESTATION_ENVIRONMENT_FIELDS
        ),
        "dont_write_bytecode": _sys.flags.dont_write_bytecode == 1,
        "effective_pythonhashseed": context["hash_seed"],
        "executable_identity": context["executable_identity"]["identity"],
        "legacy_import_artifact_count": 0,
        "no_site": _sys.flags.no_site == 1,
        "no_user_site": _sys.flags.no_user_site == 1,
        "preimport_untrusted_module_count": 0,
        "pycache_prefix_empty": not _os.listdir(prefix),
        "pycache_prefix_owner_only": (
            _stat.S_ISDIR(observed.st_mode)
            and not _stat.S_ISLNK(observed.st_mode)
            and observed.st_uid == owner
            and _stat.S_IMODE(observed.st_mode) == 0o700
        ),
        "python_implementation": _sys.implementation.name,
        "python_version": "{}.{}.{}".format(*_sys.version_info[:3]),
        "pythonpath_ignored": True,
        "site_imported": "site" in _sys.modules,
        "site_packages_role": (
            "pinned-venv-site-packages"
            if context["venv_root"] is not None
            else "frozen-base-site-packages"
        ),
        "startup_path_replaced": tuple(_sys.path) != _STARTUP_PATH,
        "startup_pythonpath_present": context["pythonpath_was_present"],
        "status": "BOOTSTRAP_READY",
        "sys_path_roles": [
            *("stdlib-{}".format(index) for index in range(len(_STDLIB_PATHS))),
            "repository-src",
            "selected-site-packages",
        ],
        "venv_detected": context["venv_root"] is not None,
        "venv_root_role": (
            ".venv-m1" if context["venv_root"] is not None else None
        ),
    }


def _require_interpreter_identity(context, role, arguments):
    needs_pinned = role in _PINNED_ROLES or (
        role == "focused-pytest" and arguments == ("pinned",)
    )
    identity = context["executable_identity"]["identity"]
    if needs_pinned:
        expected = _os.path.join(context["root"], ".venv-m1")
        expected_executable = _os.path.join(expected, "bin", "python")
        if (
            identity != "pinned"
            or context["venv_root"] != expected
            or _os.path.abspath(context["executable"]) != expected_executable
        ):
            raise AtomicCountingBootstrapError(
                "{} requires the exact frozen .venv-m1/bin/python".format(role)
            )
    if role == "focused-pytest" and arguments == ("base",):
        if identity != "base" or context["venv_root"] is not None:
            raise AtomicCountingBootstrapError(
                "focused-pytest base requires the exact frozen base interpreter"
            )
    if role == "probe":
        expected_venv = _os.path.join(context["root"], ".venv-m1")
        if identity == "pinned" and (
            context["venv_root"] != expected_venv
            or _os.path.abspath(context["executable"])
            != _os.path.join(expected_venv, "bin", "python")
        ):
            raise AtomicCountingBootstrapError(
                "pinned probe requires the exact .venv-m1/bin/python"
            )
        if identity == "base" and context["venv_root"] is not None:
            raise AtomicCountingBootstrapError(
                "base probe must not run through a virtual environment"
            )


def _training_arguments(arguments):
    if len(arguments) < 6:
        raise AtomicCountingBootstrapError(
            "training-worker arguments do not match the frozen grammar"
        )
    if arguments[:1] != ("--domain",) or arguments[2:3] != ("--mode",):
        raise AtomicCountingBootstrapError(
            "training-worker arguments do not match the frozen grammar"
        )
    domain = arguments[1]
    mode = arguments[3]
    if domain not in ("music", "clinical_style"):
        raise AtomicCountingBootstrapError("training-worker domain is invalid")
    if mode not in ("continuous", "prefix", "resume"):
        raise AtomicCountingBootstrapError("training-worker mode is invalid")
    directory = "runs/{}".format(domain)
    output = {
        "continuous": "continuous.json",
        "prefix": "prefix.json",
        "resume": "resumed.json",
    }[mode]
    common = (
        "--domain",
        domain,
        "--mode",
        mode,
        "--output",
        directory + "/" + output,
    )
    if mode == "continuous":
        expected = common
    elif mode == "prefix":
        expected = common + ("--checkpoint", directory + "/step5.ckpt")
    else:
        if len(arguments) != 12:
            raise AtomicCountingBootstrapError(
                "training-worker resume arguments do not match the frozen grammar"
            )
        digest = arguments[9] if arguments[8:9] == (
            "--expected-checkpoint-sha",
        ) else ""
        if (
            len(digest) != 64
            or any(character not in _LOWER_HEX for character in digest)
        ):
            raise AtomicCountingBootstrapError(
                "training-worker resume digest is not canonical SHA-256"
            )
        expected = common + (
            "--checkpoint",
            directory + "/step5.ckpt",
            "--expected-checkpoint-sha",
            digest,
            "--prior-output",
            directory + "/prefix.json",
        )
    if arguments != expected:
        raise AtomicCountingBootstrapError(
            "training-worker arguments do not match the frozen grammar"
        )
    return expected


def _audit_worker_arguments(arguments):
    if len(arguments) < 2 or arguments[:1] != ("--domain",):
        raise AtomicCountingBootstrapError(
            "audit-worker arguments do not match the frozen grammar"
        )
    domain = arguments[1]
    if domain not in ("music", "clinical_style"):
        raise AtomicCountingBootstrapError("audit-worker domain is invalid")
    directory = "runs/{}".format(domain)
    expected = (
        "--domain",
        domain,
        "--continuous",
        directory + "/continuous.json",
        "--prefix",
        directory + "/prefix.json",
        "--resumed",
        directory + "/resumed.json",
        "--checkpoint",
        directory + "/step5.ckpt",
        "--receipt",
        directory + "/receipt.json",
    )
    if arguments != expected:
        raise AtomicCountingBootstrapError(
            "audit-worker arguments do not match the frozen grammar"
        )
    return expected


def _domain_arguments(domain, *, include_review, include_audit):
    label = domain.replace("_", "-")
    directory = "runs/{}".format(domain)
    result = (
        "--{}-continuous".format(label),
        directory + "/continuous.json",
        "--{}-prefix".format(label),
        directory + "/prefix.json",
        "--{}-resumed".format(label),
        directory + "/resumed.json",
        "--{}-checkpoint".format(label),
        directory + "/step5.ckpt",
        "--{}-receipt".format(label),
        directory + "/receipt.json",
    )
    if include_review:
        result += (
            "--{}-review".format(label),
            directory + "/review.json",
        )
    if include_audit:
        result += (
            "--{}-audit".format(label),
            directory + "/audit.json",
        )
    return result


_AUDIT_PARENT_ARGUMENTS = (
    "audit",
) + _domain_arguments(
    "music", include_review=True, include_audit=True
) + _domain_arguments(
    "clinical_style", include_review=True, include_audit=True
)

_EVIDENCE_INPUT_ARGUMENTS = _domain_arguments(
    "music", include_review=False, include_audit=True
) + _domain_arguments(
    "clinical_style", include_review=False, include_audit=True
)


def _validated_arguments(role, arguments):
    if role == "probe":
        expected = ()
    elif role == "execution-parent":
        if arguments not in (("status",), ("run",)):
            raise AtomicCountingBootstrapError(
                "execution-parent accepts exactly status or run"
            )
        return arguments
    elif role == "training-worker":
        return _training_arguments(arguments)
    elif role == "audit-parent":
        if arguments in (("preflight",), ("probe",)):
            return arguments
        expected = _AUDIT_PARENT_ARGUMENTS
    elif role == "audit-worker":
        return _audit_worker_arguments(arguments)
    elif role == "evidence-runner":
        if arguments == ("status",):
            return arguments
        expected = (
            arguments[0] if arguments else "",
            "--output",
            _EVIDENCE_OUTPUT,
        ) + _EVIDENCE_INPUT_ARGUMENTS
        if not arguments or arguments[0] not in ("publish", "verify"):
            raise AtomicCountingBootstrapError(
                "evidence-runner command is not publish, verify, or status"
            )
    elif role == "focused-pytest":
        if arguments not in (("base",), ("pinned",)):
            raise AtomicCountingBootstrapError(
                "focused-pytest accepts exactly base or pinned"
            )
        return arguments
    else:
        raise AtomicCountingBootstrapError("unknown bootstrap role")
    if arguments != expected:
        raise AtomicCountingBootstrapError(
            "{} arguments do not match the frozen grammar".format(role)
        )
    return expected


def _load_source_entry(context, filename, module_name):
    path = _os.path.join(
        context["source"], "heterodiff", "cross_domain_gate", filename
    )
    _require_regular_file(path, name=filename, maximum_bytes=4 * 1024 * 1024)
    loader = _RepositorySourceLoader(module_name, path)
    specification = _importlib_util.spec_from_file_location(
        module_name, path, loader=loader
    )
    if specification is None:
        raise AtomicCountingBootstrapError(
            "could not create a source-only entry specification"
        )
    module = _importlib_util.module_from_spec(specification)
    _sys.modules[module_name] = module
    try:
        loader.exec_module(module)
    except BaseException:
        _sys.modules.pop(module_name, None)
        raise
    return module


def _focused_pytest(context):
    import pytest

    pytest_origin = _os.path.realpath(getattr(pytest, "__file__", ""))
    if not any(
        _is_within(pytest_origin, directory)
        for directory in context["site_packages"]
    ):
        raise AtomicCountingBootstrapError(
            "pytest did not resolve from selected interpreter site-packages"
        )
    # The root is appended only after pytest itself resolves from the selected
    # dependency tree.  A loader-free root finder can expose the ``tests``
    # namespace, while the tests-directory path is handled by the source-only
    # hook.  No root-level Python module is importable.
    original_path = tuple(_sys.path)
    root = context["root"]
    _sys.path.append(root)
    _sys.path_importer_cache[root] = _machinery.FileFinder(root)

    empty_configuration = _os.path.join(context["prefix"], "pytest.ini")
    flags = _os.O_WRONLY | _os.O_CREAT | _os.O_EXCL
    flags |= getattr(_os, "O_CLOEXEC", 0)
    descriptor = _os.open(empty_configuration, flags, 0o600)
    try:
        payload = b"[pytest]\n"
        if _os.write(descriptor, payload) != len(payload):
            raise AtomicCountingBootstrapError(
                "focused pytest configuration write stalled"
            )
        _os.fsync(descriptor)
    finally:
        _os.close(descriptor)
    arguments = (
        "-q",
        "-ra",
        "-W",
        "error",
        "-c",
        empty_configuration,
        "--rootdir",
        context["root"],
        "--confcutdir",
        context["root"],
        "--noconftest",
        "--import-mode=importlib",
        "--assert=plain",
        "-p",
        "no:cacheprovider",
    ) + _FOCUSED_TEST_PATHS
    try:
        return int(pytest.main(list(arguments), plugins=[]))
    finally:
        try:
            _os.unlink(empty_configuration)
        except FileNotFoundError:
            pass
        _sys.path[:] = list(original_path)
        _sys.path_importer_cache.pop(root, None)


def _dispatch(context, role, arguments):
    # Close the scan/import interval as much as practical.  Repository modules
    # are additionally handled by a source-only loader that never reads pyc.
    _require_clean_repository_import_tree(context["source"], context["tests"])
    if role == "execution-parent":
        module = _load_source_entry(
            context,
            "atomic_counting_execution.py",
            "_heterodiff_atomic_counting_execution_entry",
        )
        module.assert_stdlib_only_parent()
        return int(module.main(arguments))
    if role == "training-worker":
        module = _load_source_entry(
            context,
            "atomic_counting_training_worker_torch.py",
            "_heterodiff_atomic_counting_training_worker_entry",
        )
        return int(module.main(arguments))
    if role == "audit-parent":
        module = _load_source_entry(
            context,
            "atomic_counting_audit.py",
            "_heterodiff_atomic_counting_audit_entry",
        )
        module.assert_stdlib_only_parent()
        return int(module.main(arguments))
    if role == "audit-worker":
        module = _load_source_entry(
            context,
            "atomic_counting_audit_worker_torch.py",
            "_heterodiff_atomic_counting_audit_worker_entry",
        )
        return int(module.main(arguments))
    if role == "evidence-runner":
        module = _load_source_entry(
            context,
            "atomic_counting_evidence_runner.py",
            "_heterodiff_atomic_counting_evidence_runner_entry",
        )
        return int(module.main(arguments))
    if role == "focused-pytest":
        return _focused_pytest(context)
    raise AtomicCountingBootstrapError("probe cannot be dispatched as a mutable role")


def _error_payload(error):
    return {
        "bootstrap_schema": BOOTSTRAP_SCHEMA,
        "error_type": type(error).__name__,
        "message": str(error),
        "status": "HOLD",
    }


def main():
    context = None
    prefix = None
    prefix_identity = None
    try:
        raw_arguments = tuple(_sys.argv[1:])
        if (
            not raw_arguments
            or len(raw_arguments) > 40
            or any(
                type(token) is not str or not token or len(token) > 4096
                for token in raw_arguments
            )
        ):
            raise AtomicCountingBootstrapError(
                "bootstrap requires one bounded role and its frozen arguments"
            )
        role = raw_arguments[0]
        if role not in _ROLES:
            raise AtomicCountingBootstrapError("unknown bootstrap role")
        arguments = _validated_arguments(role, raw_arguments[1:])
        context = _prepare(role)
        prefix = context["prefix"]
        prefix_identity = context["prefix_identity"]
        _require_interpreter_identity(context, role, arguments)
        if role == "probe":
            payload = _probe_payload(context)
            _remove_empty_pycache_prefix(prefix, prefix_identity)
            prefix = None
            _sys.stdout.buffer.write(_canonical_json_bytes(payload) + b"\n")
            _sys.stdout.buffer.flush()
            return 0
        result = _dispatch(context, role, arguments)
        _remove_empty_pycache_prefix(prefix, prefix_identity)
        prefix = None
        return result
    except Exception as error:
        if prefix is not None:
            try:
                _remove_empty_pycache_prefix(prefix, prefix_identity)
                prefix = None
            except (AtomicCountingBootstrapError, OSError):
                pass
        _sys.stderr.buffer.write(_canonical_json_bytes(_error_payload(error)) + b"\n")
        _sys.stderr.buffer.flush()
        return 2
    finally:
        if prefix is not None:
            try:
                _remove_empty_pycache_prefix(prefix, prefix_identity)
            except (AtomicCountingBootstrapError, OSError):
                pass


if __name__ == "__main__":
    _exit_code = main()
    # CPython enters a post-script interactive session even after SystemExit
    # when -i/PYTHONINSPECT affected startup.  Such a process already fails the
    # frozen flag check above; terminate without granting that unbound session.
    if _sys.flags.inspect or _sys.flags.interactive:
        _os._exit(_exit_code)
    raise SystemExit(_exit_code)


__all__ = ["AtomicCountingBootstrapError", "BOOTSTRAP_SCHEMA", "main"]
