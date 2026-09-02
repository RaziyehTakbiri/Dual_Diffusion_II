"""Direct-path launcher for the standard-library counting-gate audit parent.

Run this file by filesystem path, not with ``python -m``.  That avoids importing
the top-level :mod:`heterodiff` package before the parent has launched its
bounded child processes.
"""

from __future__ import annotations

from pathlib import Path
import runpy


def main() -> None:
    target = Path(__file__).resolve(strict=True).with_name(
        "atomic_counting_audit.py"
    )
    runpy.run_path(str(target), run_name="__main__")


if __name__ == "__main__":
    main()
