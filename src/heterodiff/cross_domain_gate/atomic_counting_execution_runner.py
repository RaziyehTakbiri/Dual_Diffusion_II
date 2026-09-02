"""Direct-path stdlib-only launcher for atomic-counting production execution.

Invoke exactly as:

``.venv-m1/bin/python src/heterodiff/cross_domain_gate/atomic_counting_execution_runner.py status``

or replace ``status`` with ``run``.  Importing through ``heterodiff`` is not the
production surface because package initialization imports NumPy before child
processes are launched.
"""

from __future__ import annotations

from atomic_counting_execution import assert_stdlib_only_parent, main


if __name__ == "__main__":  # pragma: no cover - exercised as a direct script
    assert_stdlib_only_parent()
    raise SystemExit(main())
