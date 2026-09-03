import hashlib
import importlib.util
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
NOTEBOOK = (
    REPO_ROOT
    / "databricks/notebooks/b08_n1_candidate_002_read_only_forensics.py"
)
EXPECTED_INTENT = b"x" * 2322


def load_notebook():
    spec = importlib.util.spec_from_file_location(
        "b08_n1_candidate_002_read_only_forensics",
        NOTEBOOK,
    )
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def capture(module, target, device=None, inode=None):
    observed = target.lstat()
    return module.capture_spent_attempt(
        str(target),
        observed.st_dev if device is None else device,
        observed.st_ino if inode is None else inode,
    )


def test_inventory_is_read_only_and_reports_zero_byte_intent(tmp_path):
    module = load_notebook()
    attempt = tmp_path / "attempt"
    attempt.mkdir()
    intent = attempt / "attempt-intent.json"
    intent.write_bytes(b"")

    before = intent.stat()
    result = capture(module, attempt)
    after = intent.stat()

    assert result["decision"] == "READ_ONLY_FORENSIC_INVENTORY_COMPLETE"
    assert result["visible_leaf_names"] == ["attempt-intent.json"]
    assert (
        result["forensic_classification"]
        == "ZERO_BYTE_INTENT_VISIBLE_FAILURE_BEFORE_PAYLOAD_WRITE_LIKELY"
    )
    assert result["entries"][0]["sha256"] == hashlib.sha256(b"").hexdigest()
    assert (
        result["safety"][
            "mutating_filesystem_operation_requested_by_notebook"
        ]
        is False
    )
    assert result["safety"]["unity_catalog_volume_read_performed"] is False
    assert before.st_size == after.st_size == 0
    assert before.st_mtime_ns == after.st_mtime_ns


def test_inventory_reports_partial_and_unexpected_leaf(tmp_path):
    module = load_notebook()
    attempt = tmp_path / "attempt"
    attempt.mkdir()
    (attempt / "attempt-intent.json").write_bytes(EXPECTED_INTENT[:17])
    (attempt / "unexpected.bin").write_bytes(b"unexpected")

    result = capture(module, attempt)

    assert result["forensic_classification"] == "PARTIAL_INTENT_PAYLOAD_VISIBLE"
    assert result["unexpected_leaf_names"] == ["unexpected.bin"]
    unexpected = next(
        entry for entry in result["entries"] if entry["name"] == "unexpected.bin"
    )
    assert unexpected["payload_read"] is False
    assert "sha256" not in unexpected
    assert result["safety"]["unexpected_leaf_payload_opened_or_read"] is False


def test_inventory_reports_full_size_hash_mismatch(tmp_path):
    module = load_notebook()
    attempt = tmp_path / "attempt"
    attempt.mkdir()
    (attempt / "attempt-intent.json").write_bytes(EXPECTED_INTENT)

    result = capture(module, attempt)

    assert result["intent_matches_expected_size"] is True
    assert result["intent_matches_expected_sha256"] is False
    assert result["forensic_classification"] == "INTENT_PAYLOAD_MISMATCH_VISIBLE"


def test_inventory_structures_absent_root_failure(tmp_path):
    module = load_notebook()
    result = module.capture_spent_attempt(
        str(tmp_path / "absent"),
        1,
        1,
    )

    assert result["decision"] == "READ_ONLY_FORENSIC_INVENTORY_FAILED"
    assert result["error_type"] == "FileNotFoundError"
    assert result["safety"]["direct_external_network_endpoint_accessed"] is False


def test_exact_production_target_has_no_ambient_override():
    module = load_notebook()

    assert module.EXACT_TARGET_DIRECTORY.endswith(
        "/b08_runtime_output/b08-n1-overlay-candidate-002"
    )
    assert "HETERODIFF_B08_N1_FORENSIC_TARGET" not in NOTEBOOK.read_text(
        encoding="utf-8"
    )


def test_reported_root_binding_mismatch_stops_before_enumeration(
    tmp_path,
    monkeypatch,
):
    module = load_notebook()
    attempt = tmp_path / "attempt"
    attempt.mkdir()
    (attempt / "attempt-intent.json").write_bytes(b"secret")

    opened = []
    original_open = module.os.open

    def recording_open(*args, **kwargs):
        opened.append(args[0])
        return original_open(*args, **kwargs)

    monkeypatch.setattr(module.os, "open", recording_open)
    observed = attempt.lstat()
    result = module.capture_spent_attempt(
        str(attempt),
        observed.st_dev,
        observed.st_ino + 1,
    )

    assert result["decision"] == "READ_ONLY_FORENSIC_INVENTORY_FAILED"
    assert result["error_detail"] == "REPORTED_SPENT_ATTEMPT_ROOT_BINDING_MISMATCH"
    assert opened == []


def test_expected_symlink_leaf_is_not_opened(tmp_path):
    module = load_notebook()
    attempt = tmp_path / "attempt"
    attempt.mkdir()
    payload = tmp_path / "payload"
    payload.write_bytes(b"must-not-be-read")
    (attempt / "attempt-intent.json").symlink_to(payload)

    result = capture(module, attempt)

    intent = result["entries"][0]
    assert intent["kind"] == "SYMLINK"
    assert intent["payload_read"] is False
    assert "sha256" not in intent
    assert result["forensic_classification"] == "ATTEMPT_INTENT_NOT_REGULAR"


def test_symlink_root_is_rejected(tmp_path):
    module = load_notebook()
    real = tmp_path / "real"
    real.mkdir()
    alias = tmp_path / "alias"
    alias.symlink_to(real, target_is_directory=True)
    observed = alias.lstat()

    result = module.capture_spent_attempt(
        str(alias),
        observed.st_dev,
        observed.st_ino,
    )

    assert result["decision"] == "READ_ONLY_FORENSIC_INVENTORY_FAILED"
    assert result["error_detail"] == "SPENT_ATTEMPT_ROOT_NOT_PHYSICAL_DIRECTORY"


def test_complete_expected_intent_is_classified(tmp_path, monkeypatch):
    module = load_notebook()
    attempt = tmp_path / "attempt"
    attempt.mkdir()
    intent_bytes = b"exact-control-intent\n"
    (attempt / "attempt-intent.json").write_bytes(intent_bytes)
    monkeypatch.setattr(module, "EXPECTED_INTENT_SIZE_BYTES", len(intent_bytes))
    monkeypatch.setattr(
        module,
        "EXPECTED_INTENT_SHA256",
        hashlib.sha256(intent_bytes).hexdigest(),
    )

    result = capture(module, attempt)

    assert result["intent_matches_expected_size"] is True
    assert result["intent_matches_expected_sha256"] is True
    assert (
        result["forensic_classification"]
        == "COMPLETE_EXPECTED_INTENT_PAYLOAD_VISIBLE"
    )


def test_oversize_expected_control_leaf_is_not_read(tmp_path, monkeypatch):
    module = load_notebook()
    attempt = tmp_path / "attempt"
    attempt.mkdir()
    (attempt / "attempt-intent.json").write_bytes(b"oversize")
    monkeypatch.setattr(module, "MAX_CONTROL_LEAF_BYTES", 1)

    result = capture(module, attempt)

    intent = result["entries"][0]
    assert intent["payload_read"] is False
    assert intent["payload_read_skip_reason"] == "CONTROL_LEAF_SIZE_EXCEEDS_BOUND"
    assert "sha256" not in intent


def test_visible_leaf_count_is_bounded(tmp_path, monkeypatch):
    module = load_notebook()
    attempt = tmp_path / "attempt"
    attempt.mkdir()
    (attempt / "one").write_bytes(b"1")
    (attempt / "two").write_bytes(b"2")
    monkeypatch.setattr(module, "MAX_VISIBLE_LEAF_COUNT", 1)

    result = capture(module, attempt)

    assert result["decision"] == "READ_ONLY_FORENSIC_INVENTORY_FAILED"
    assert result["error_detail"] == "VISIBLE_LEAF_COUNT_EXCEEDS_BOUND"


def test_late_root_rebind_failure_preserves_control_read_telemetry(
    tmp_path,
    monkeypatch,
):
    module = load_notebook()
    attempt = tmp_path / "attempt"
    attempt.mkdir()
    (attempt / "attempt-intent.json").write_bytes(b"control")
    initial = attempt.lstat()
    original_lstat = module.os.lstat
    calls = {"count": 0}

    def rebound_lstat(path):
        observed = original_lstat(path)
        calls["count"] += 1
        if calls["count"] == 2:
            values = list(observed)
            values[1] = observed.st_ino + 1
            return module.os.stat_result(values)
        return observed

    monkeypatch.setattr(module.os, "lstat", rebound_lstat)
    result = module.capture_spent_attempt(
        str(attempt),
        initial.st_dev,
        initial.st_ino,
    )

    assert result["decision"] == "READ_ONLY_FORENSIC_INVENTORY_FAILED"
    assert result["error_detail"] == "SPENT_ATTEMPT_DECLARED_PATH_REBOUND"
    assert result["safety"]["control_leaf_payload_read_performed"] is True
    assert (
        result["safety"][
            "control_leaf_payload_read_may_have_been_performed"
        ]
        is True
    )
    assert result["safety"]["study_or_test_data_path_requested_by_notebook"] is False


def test_notebook_contains_no_mutating_or_network_calls():
    source = NOTEBOOK.read_text(encoding="utf-8")
    forbidden = (
        "os.mkdir(",
        "os.makedirs(",
        "os.remove(",
        "os.unlink(",
        "os.rename(",
        "os.replace(",
        "os.chmod(",
        "os.fchmod(",
        "os.chown(",
        "os.fchown(",
        "os.write(",
        "subprocess",
        "requests",
        "urllib",
        "socket",
        "dbutils.fs",
        "spark.",
    )
    assert all(token not in source for token in forbidden)


def test_main_uses_only_the_frozen_target_and_reported_binding():
    source = NOTEBOOK.read_text(encoding="utf-8")

    assert "capture_spent_attempt(\n        EXACT_TARGET_DIRECTORY," in source
    assert "        EXPECTED_ROOT_DEVICE,\n        EXPECTED_ROOT_INODE," in source
