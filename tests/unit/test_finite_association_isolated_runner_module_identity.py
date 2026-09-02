"""No-training regression tests for the direct-script worker module identity."""

from __future__ import annotations

import json
import os
from pathlib import Path
import subprocess
import sys
import textwrap


_ROOT = Path(__file__).resolve().parents[2]
_RUNNER = _ROOT / "src/heterodiff/experiments/finite_association_isolated_runner.py"
_CANONICAL_NAME = "heterodiff.experiments.finite_association_isolated_runner"


def _subprocess_environment() -> dict[str, str]:
    environment = dict(os.environ)
    environment.update(
        {
            "PYTHONPATH": str(_ROOT / "src"),
            "PYTHONSAFEPATH": "1",
            "PYTHONDONTWRITEBYTECODE": "1",
            "PYTHONHASHSEED": "0",
            "CUDA_VISIBLE_DEVICES": "",
            "OMP_NUM_THREADS": "1",
            "OPENBLAS_NUM_THREADS": "1",
            "MKL_NUM_THREADS": "1",
            "VECLIB_MAXIMUM_THREADS": "1",
            "NUMEXPR_NUM_THREADS": "1",
            "BLIS_NUM_THREADS": "1",
        }
    )
    return environment


def test_direct_script_identity_accepts_exact_handshaken_session_without_training(
    tmp_path: Path,
) -> None:
    bootstrap = textwrap.dedent(
        """
        import contextlib
        import hashlib
        import importlib
        import io
        import json
        import os
        from pathlib import Path
        import runpy
        import sys

        runner_path = Path(sys.argv[1]).resolve(strict=True)
        custody_path = Path(sys.argv[2]).resolve()
        canonical_name = sys.argv[3]
        sys.argv = [str(runner_path), "--help"]
        with contextlib.redirect_stdout(io.StringIO()), contextlib.redirect_stderr(
            io.StringIO()
        ):
            try:
                runpy.run_path(str(runner_path), run_name="__main__")
            except SystemExit as error:
                if error.code != 0:
                    raise
            else:
                raise AssertionError("direct-script help did not exit")

        isolated = importlib.import_module(canonical_name)
        if isolated is not sys.modules[canonical_name]:
            raise AssertionError("canonical import returned another module")

        token = hashlib.sha256(b"module-identity-parent-token-v2").digest()
        token_sha256 = hashlib.sha256(token).hexdigest()
        launch_sha256 = hashlib.sha256(b"launch-authorization-v2").hexdigest()
        launch_receipt_sha256 = hashlib.sha256(b"launch-receipt-v2").hexdigest()
        request = isolated.FrozenAssociationSampledRunRequest(
            seed=1729, budget=32768, method="guided"
        )

        def consume_without_ledger(
            ledger_directory,
            authorization_sha256,
            observed_request,
            observed_token_sha256,
        ):
            if Path(ledger_directory).resolve() != custody_path:
                raise AssertionError("handshake custody path changed")
            if authorization_sha256 != launch_sha256:
                raise AssertionError("handshake authorization changed")
            if observed_request != request:
                raise AssertionError("handshake request changed")
            if observed_token_sha256 != token_sha256:
                raise AssertionError("handshake token changed")
            return {
                "launch_authorization_sha256": launch_sha256,
                "consumed_receipt_sha256": launch_receipt_sha256,
            }

        isolated._consume_launch_authorization = consume_without_ledger
        control_read, control_write = os.pipe()
        os.write(control_write, token)
        os.close(control_write)
        session = isolated._consume_parent_handshake(
            control_read,
            token_sha256,
            request=request,
            ledger_directory=custody_path,
            launch_authorization_sha256=launch_sha256,
        )
        run_key_sha256 = hashlib.sha256(b"v2-run-key").hexdigest()
        session.bind_run(run_key_sha256)

        training = importlib.import_module(
            "heterodiff.experiments.finite_association_residual_training_torch"
        )
        permit = training._issue_frozen_association_execution_permit(
            run_key_sha256=run_key_sha256,
            preflight_sha256=hashlib.sha256(b"v2-preflight").hexdigest(),
            prepared_ledger_sha256=hashlib.sha256(b"v2-prepared").hexdigest(),
            campaign_sha256=hashlib.sha256(b"v2-campaign").hexdigest(),
            execution_runtime_sha256=hashlib.sha256(b"v2-runtime").hexdigest(),
            ledger_directory=custody_path,
            total_wall_start=0.0,
            total_cpu_start=0.0,
            worker_session=session,
        )
        result = {
            "canonical_class_identity": (
                type(session) is isolated._FrozenAssociationWorkerSession
            ),
            "permit_accepted_exact_session": permit._worker_session is session,
            "permit_consumed": permit._consumed,
            "custody_path_created": custody_path.exists(),
        }
        print(json.dumps(result, sort_keys=True, separators=(",", ":")))
        """
    )
    completed = subprocess.run(
        (
            sys.executable,
            "-P",
            "-c",
            bootstrap,
            str(_RUNNER),
            str(tmp_path / "never-created-custody"),
            _CANONICAL_NAME,
        ),
        cwd=str(tmp_path),
        env=_subprocess_environment(),
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        timeout=120,
        check=False,
        text=True,
    )
    assert completed.returncode == 0, completed.stderr
    assert json.loads(completed.stdout) == {
        "canonical_class_identity": True,
        "permit_accepted_exact_session": True,
        "permit_consumed": False,
        "custody_path_created": False,
    }
    assert list(tmp_path.iterdir()) == []


def test_direct_script_identity_fails_closed_on_conflicting_registration(
    tmp_path: Path,
) -> None:
    bootstrap = textwrap.dedent(
        """
        import runpy
        import sys
        import types

        runner_path, canonical_name = sys.argv[1:]
        sys.modules[canonical_name] = types.ModuleType(canonical_name)
        sys.argv = [runner_path, "--help"]
        try:
            runpy.run_path(runner_path, run_name="__main__")
        except RuntimeError as error:
            if str(error) != "canonical isolated-runner module identity conflicts":
                raise
        else:
            raise AssertionError("conflicting canonical registration was accepted")
        """
    )
    completed = subprocess.run(
        (
            sys.executable,
            "-P",
            "-c",
            bootstrap,
            str(_RUNNER),
            _CANONICAL_NAME,
        ),
        cwd=str(tmp_path),
        env=_subprocess_environment(),
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        timeout=30,
        check=False,
        text=True,
    )
    assert completed.returncode == 0, completed.stderr
    assert completed.stdout == ""
    assert list(tmp_path.iterdir()) == []
