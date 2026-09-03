import hashlib
import importlib.util
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[2]
NOTEBOOK = (
    REPO_ROOT
    / "databricks/notebooks/"
    "b08_n1_candidate_002_object_snapshot_forensics_v2.py"
)


def load_notebook():
    spec = importlib.util.spec_from_file_location(
        "b08_n1_candidate_002_object_snapshot_forensics_v2",
        NOTEBOOK,
    )
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_zero_byte_intent_is_repeatable_and_read_only(tmp_path):
    module = load_notebook()
    attempt = tmp_path / "attempt"
    attempt.mkdir()
    intent = attempt / "attempt-intent.json"
    intent.write_bytes(b"")
    before = intent.stat()

    result = module.capture_spent_attempt(str(attempt))
    after = intent.stat()

    assert (
        result["decision"]
        == "READ_ONLY_FORENSIC_REPEATABLE_PATH_SNAPSHOTS_COMPLETE"
    )
    assert result["forensic_classification"] == "STABLY_ZERO_BYTE_INTENT_VISIBLE"
    assert result["snapshots_equal"] is True
    assert result["snapshot_count_completed"] == 2
    assert before.st_size == after.st_size == 0
    assert before.st_mtime_ns == after.st_mtime_ns
    assert result["custody_model"]["prior_device_inode_gate_used"] is False


def test_partial_intent_and_unexpected_payload_is_never_opened(
    tmp_path,
    monkeypatch,
):
    module = load_notebook()
    attempt = tmp_path / "attempt"
    attempt.mkdir()
    (attempt / "attempt-intent.json").write_bytes(b"partial")
    (attempt / "unexpected.bin").write_bytes(b"must-not-be-read")
    opened = []
    original_open = module.os.open

    def recording_open(path, *args, **kwargs):
        opened.append(path)
        return original_open(path, *args, **kwargs)

    monkeypatch.setattr(module.os, "open", recording_open)
    result = module.capture_spent_attempt(str(attempt))

    assert result["forensic_classification"] == "STABLY_PARTIAL_INTENT_VISIBLE"
    assert result["unexpected_leaf_names"] == ["unexpected.bin"]
    assert "unexpected.bin" not in opened
    assert result["safety"]["unexpected_leaf_payload_opened_or_read"] is False


def test_complete_expected_intent(tmp_path, monkeypatch):
    module = load_notebook()
    attempt = tmp_path / "attempt"
    attempt.mkdir()
    payload = b"complete-intent\n"
    (attempt / "attempt-intent.json").write_bytes(payload)
    monkeypatch.setattr(module, "EXPECTED_INTENT_SIZE_BYTES", len(payload))
    monkeypatch.setattr(
        module,
        "EXPECTED_INTENT_SHA256",
        hashlib.sha256(payload).hexdigest(),
    )

    result = module.capture_spent_attempt(str(attempt))

    assert result["forensic_classification"] == (
        "STABLY_COMPLETE_EXPECTED_INTENT_VISIBLE"
    )


def test_same_size_wrong_hash_intent(tmp_path, monkeypatch):
    module = load_notebook()
    attempt = tmp_path / "attempt"
    attempt.mkdir()
    payload = b"wrong"
    (attempt / "attempt-intent.json").write_bytes(payload)
    monkeypatch.setattr(module, "EXPECTED_INTENT_SIZE_BYTES", len(payload))
    monkeypatch.setattr(module, "EXPECTED_INTENT_SHA256", "0" * 64)

    result = module.capture_spent_attempt(str(attempt))

    assert result["forensic_classification"] == (
        "STABLY_MISMATCHING_INTENT_VISIBLE"
    )


def test_absent_intent_is_stable_classification(tmp_path):
    module = load_notebook()
    attempt = tmp_path / "attempt"
    attempt.mkdir()

    result = module.capture_spent_attempt(str(attempt))

    assert result["forensic_classification"] == (
        "STABLY_NOT_VISIBLE_IN_TWO_PATH_SNAPSHOTS"
    )


def test_failure_receipt_is_hashed_but_never_parsed(tmp_path):
    module = load_notebook()
    attempt = tmp_path / "attempt"
    attempt.mkdir()
    payload = b"not-json-but-control-evidence"
    (attempt / "construction-failure-receipt.json").write_bytes(payload)

    result = module.capture_spent_attempt(str(attempt))
    receipt = result["stable_projection"]["control_leaves"][
        "construction-failure-receipt.json"
    ]

    assert receipt["sha256"] == hashlib.sha256(payload).hexdigest()
    assert receipt["size_bytes"] == len(payload)
    assert result["forensic_classification"] == (
        "STABLY_NOT_VISIBLE_IN_TWO_PATH_SNAPSHOTS"
    )


def test_prior_inode_device_mode_timestamp_are_not_acceptance_fields(tmp_path):
    module = load_notebook()
    attempt = tmp_path / "attempt"
    attempt.mkdir()
    (attempt / "attempt-intent.json").write_bytes(b"")

    result = module.capture_spent_attempt(str(attempt))
    projection = result["stable_projection"]

    def keys(value):
        if isinstance(value, dict):
            return set(value).union(
                *(keys(child) for child in value.values())
            )
        if isinstance(value, list):
            return set().union(*(keys(child) for child in value))
        return set()

    projection_keys = keys(projection)
    assert "inode" not in projection_keys
    assert "device" not in projection_keys
    assert "mode" not in projection_keys
    assert "mtime" not in projection_keys
    assert (
        result["custody_model"][
            "device_inode_permission_bits_or_timestamp_used_for_custody_acceptance"
        ]
        is False
    )


def test_symlink_root_is_rejected(tmp_path):
    module = load_notebook()
    real = tmp_path / "real"
    real.mkdir()
    alias = tmp_path / "alias"
    alias.symlink_to(real, target_is_directory=True)

    result = module.capture_spent_attempt(str(alias))

    assert result["decision"] == (
        "READ_ONLY_OBJECT_SNAPSHOT_FORENSIC_INVENTORY_FAILED"
    )
    assert result["error_detail"] == (
        "SPENT_ATTEMPT_ROOT_NOT_VISIBLE_NONSYMLINK_DIRECTORY"
    )


def test_symlink_control_leaf_is_stably_not_read(tmp_path):
    module = load_notebook()
    attempt = tmp_path / "attempt"
    attempt.mkdir()
    payload = tmp_path / "payload"
    payload.write_bytes(b"must-not-be-read")
    (attempt / "attempt-intent.json").symlink_to(payload)

    result = module.capture_spent_attempt(str(attempt))

    assert result["forensic_classification"] == (
        "STABLY_NONREGULAR_INTENT_NOT_READ"
    )
    assert result["decision"] == "HOLD_FORENSIC_ALLOWLISTED_CONTROL_LEAF_UNREAD"
    assert result["safety"]["control_leaf_payload_read_performed"] is False


def test_oversize_control_leaf_is_stably_refused_without_open(
    tmp_path,
    monkeypatch,
):
    module = load_notebook()
    attempt = tmp_path / "attempt"
    attempt.mkdir()
    (attempt / "attempt-intent.json").write_bytes(b"oversize")
    monkeypatch.setattr(module, "MAX_CONTROL_LEAF_BYTES", 1)

    result = module.capture_spent_attempt(str(attempt))
    intent = result["stable_projection"]["control_leaves"][
        "attempt-intent.json"
    ]

    assert intent["payload_read"] is False
    assert intent["read_refusal"] == "CONTROL_LEAF_SIZE_EXCEEDS_BOUND"
    assert result["forensic_classification"] == (
        "STABLY_UNREAD_INTENT_REQUIRES_REVIEW"
    )
    assert result["decision"] == "HOLD_FORENSIC_ALLOWLISTED_CONTROL_LEAF_UNREAD"
    assert result["safety"]["control_leaf_payload_read_performed"] is False


def test_visible_leaf_count_is_bounded(tmp_path, monkeypatch):
    module = load_notebook()
    attempt = tmp_path / "attempt"
    attempt.mkdir()
    (attempt / "one").write_bytes(b"1")
    (attempt / "two").write_bytes(b"2")
    monkeypatch.setattr(module, "MAX_VISIBLE_LEAF_COUNT", 1)

    result = module.capture_spent_attempt(str(attempt))

    assert result["error_detail"] == "VISIBLE_LEAF_COUNT_EXCEEDS_BOUND"
    assert result["safety"]["control_leaf_payload_read_performed"] is False


def test_content_change_between_independent_snapshots_returns_hold(
    tmp_path,
    monkeypatch,
):
    module = load_notebook()
    attempt = tmp_path / "attempt"
    attempt.mkdir()
    (attempt / "attempt-intent.json").write_bytes(b"control")
    original = module.snapshot_projection

    def changed_projection(path, ordinal, state):
        result = original(path, ordinal, state)
        if ordinal == 2:
            result["projection"]["control_leaves"]["attempt-intent.json"][
                "sha256"
            ] = "0" * 64
            result["projection_sha256"] = hashlib.sha256(
                module.canonical_json_bytes(result["projection"])
            ).hexdigest()
        return result

    monkeypatch.setattr(module, "snapshot_projection", changed_projection)
    result = module.capture_spent_attempt(str(attempt))

    assert result["decision"] == "HOLD_FORENSIC_PATH_SNAPSHOTS_NOT_REPEATABLE"
    assert result["forensic_classification"] == (
        "UNRESOLVED_NONREPEATABLE_SNAPSHOTS"
    )


def test_within_snapshot_roster_change_is_structured_late_failure(
    tmp_path,
    monkeypatch,
):
    module = load_notebook()
    attempt = tmp_path / "attempt"
    attempt.mkdir()
    (attempt / "attempt-intent.json").write_bytes(b"")
    original = module.bounded_roster
    calls = {"count": 0}

    def changed_roster(descriptor):
        calls["count"] += 1
        result = original(descriptor)
        if calls["count"] == 2:
            return result + [{"kind": "REGULAR_FILE", "name": "late", "size_bytes": 0}]
        return result

    monkeypatch.setattr(module, "bounded_roster", changed_roster)
    result = module.capture_spent_attempt(str(attempt))

    assert result["error_detail"] == "VISIBLE_LEAF_ROSTER_CHANGED_WITHIN_SNAPSHOT"
    assert result["snapshot_count_attempted"] == 1
    assert result["snapshot_count_completed"] == 0
    assert result["safety"]["control_leaf_payload_read_performed"] is True


def test_volume_late_failure_does_not_claim_managed_read_was_false():
    module = load_notebook()
    state = {
        "snapshot_count_attempted": 2,
        "snapshot_count_completed": 1,
        "active_snapshot_ordinal": 2,
        "completed_snapshots": [{"bounded": "first"}],
        "control_leaf_payload_read_may_have_been_performed": True,
        "control_leaf_payload_read_performed": True,
        "control_leaf_payload_bytes_read_total": 17,
        "control_leaf_payload_reads_completed": 1,
    }

    result = module.public_failure(
        module.EXACT_TARGET_DIRECTORY,
        RuntimeError("LATE_FAILURE"),
        state,
    )

    safety = result["safety"]
    assert safety["unity_catalog_volume_read_attempted"] is True
    assert safety["databricks_managed_storage_io_may_have_been_performed"] is True
    assert "unity_catalog_volume_read_performed" not in safety
    assert "databricks_managed_storage_io_performed" not in safety
    assert safety["control_leaf_payload_read_performed"] is True


def test_root_descriptor_is_closed_when_roster_fails(tmp_path, monkeypatch):
    module = load_notebook()
    attempt = tmp_path / "attempt"
    attempt.mkdir()
    opened = []
    closed = []
    original_open = module.os.open
    original_close = module.os.close

    def recording_open(*args, **kwargs):
        descriptor = original_open(*args, **kwargs)
        opened.append(descriptor)
        return descriptor

    def recording_close(descriptor):
        closed.append(descriptor)
        return original_close(descriptor)

    def failing_roster(_descriptor):
        raise RuntimeError("INJECTED_ROSTER_FAILURE")

    monkeypatch.setattr(module.os, "open", recording_open)
    monkeypatch.setattr(module.os, "close", recording_close)
    monkeypatch.setattr(module, "bounded_roster", failing_roster)
    result = module.capture_spent_attempt(str(attempt))

    assert result["error_detail"] == "INJECTED_ROSTER_FAILURE"
    assert opened
    assert set(opened).issubset(closed)


def test_leaf_and_root_descriptors_close_when_read_fails(tmp_path, monkeypatch):
    module = load_notebook()
    attempt = tmp_path / "attempt"
    attempt.mkdir()
    (attempt / "attempt-intent.json").write_bytes(b"control")
    opened = []
    closed = []
    original_open = module.os.open
    original_close = module.os.close

    def recording_open(*args, **kwargs):
        descriptor = original_open(*args, **kwargs)
        opened.append(descriptor)
        return descriptor

    def recording_close(descriptor):
        closed.append(descriptor)
        return original_close(descriptor)

    def failing_read(_descriptor, _size):
        raise RuntimeError("INJECTED_READ_FAILURE")

    monkeypatch.setattr(module.os, "open", recording_open)
    monkeypatch.setattr(module.os, "close", recording_close)
    monkeypatch.setattr(module.os, "read", failing_read)
    result = module.capture_spent_attempt(str(attempt))

    assert result["error_detail"] == "INJECTED_READ_FAILURE"
    assert len(opened) >= 2
    assert set(opened).issubset(closed)


def test_partial_bytes_then_read_failure_is_reported_truthfully(
    tmp_path,
    monkeypatch,
):
    module = load_notebook()
    attempt = tmp_path / "attempt"
    attempt.mkdir()
    (attempt / "attempt-intent.json").write_bytes(b"control")
    original_read = module.os.read
    calls = {"count": 0}

    def partial_then_failure(descriptor, size):
        calls["count"] += 1
        if calls["count"] == 1:
            return original_read(descriptor, size)
        raise RuntimeError("INJECTED_AFTER_PARTIAL_READ_FAILURE")

    monkeypatch.setattr(module.os, "read", partial_then_failure)
    result = module.capture_spent_attempt(str(attempt))

    assert result["error_detail"] == "INJECTED_AFTER_PARTIAL_READ_FAILURE"
    assert result["safety"]["control_leaf_payload_bytes_read_total"] == 7
    assert result["safety"]["control_leaf_payload_read_performed"] is True
    assert result["safety"]["control_leaf_payload_reads_completed"] == 0


def test_roster_iterator_closes_when_iteration_fails(tmp_path, monkeypatch):
    module = load_notebook()
    attempt = tmp_path / "attempt"
    attempt.mkdir()

    class FailingIterator:
        def __init__(self):
            self.closed = False

        def __iter__(self):
            return self

        def __next__(self):
            raise RuntimeError("INJECTED_ITERATION_FAILURE")

        def close(self):
            self.closed = True

    iterator = FailingIterator()
    monkeypatch.setattr(module.os, "scandir", lambda _descriptor: iterator)
    result = module.capture_spent_attempt(str(attempt))

    assert result["error_detail"] == "INJECTED_ITERATION_FAILURE"
    assert iterator.closed is True


def test_absent_root_is_structured_failure(tmp_path):
    module = load_notebook()

    result = module.capture_spent_attempt(str(tmp_path / "absent"))

    assert result["error_type"] == "FileNotFoundError"
    assert result["snapshot_count_attempted"] == 1
    assert result["custody_model"]["required_snapshot_pair_completed"] is False
    assert result["custody_model"]["observed_basis"] == (
        "PARTIAL_OR_NO_SNAPSHOT_PAIR"
    )


def test_production_main_is_exact_and_has_no_runtime_override():
    module = load_notebook()
    source = NOTEBOOK.read_text(encoding="utf-8")

    assert module.EXACT_TARGET_DIRECTORY == (
        "/Volumes/development/team_eds_supplychain/b08_runtime_output/"
        "b08-n1-overlay-candidate-002"
    )
    assert "getenv(" not in source
    assert "os.environ" not in source
    assert "capture_spent_attempt(EXACT_TARGET_DIRECTORY)" in source


def test_source_has_no_mutating_package_spark_rest_or_network_calls():
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
        "dbutils",
        "spark.",
    )
    assert all(token not in source for token in forbidden)


def test_snapshot_projection_digest_is_deterministic(tmp_path):
    module = load_notebook()
    attempt = tmp_path / "attempt"
    attempt.mkdir()
    (attempt / "attempt-intent.json").write_bytes(b"stable")

    first = module.capture_spent_attempt(str(attempt))
    second = module.capture_spent_attempt(str(attempt))

    assert first["stable_projection_sha256"] == second["stable_projection_sha256"]
