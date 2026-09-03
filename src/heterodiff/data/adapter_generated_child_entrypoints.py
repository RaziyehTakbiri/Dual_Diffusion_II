"""Zero-argument generated-adapter factories for source-bound child runs.

These factories are deliberately separate from case transport.  A selected
implementation-closure manifest binds one exact callable to one adapter
identity before a child is launched; the output-blind request consequently
does not contain an adapter selector.

The four generated adapters are bounded cross-domain development fixtures.
They demonstrate the general child boundary but do not establish quality on
official datasets or support a cross-domain generalization claim.
"""

from __future__ import annotations

from .generated_conformance_adapters import (
    GeneratedHAdapter,
    GeneratedMAdapter,
    GeneratedPAdapter,
    GeneratedRAdapter,
)


def build_generated_h_adapter() -> GeneratedHAdapter:
    """Return a fresh continuous-time generated adapter."""

    return GeneratedHAdapter()


def build_generated_m_adapter() -> GeneratedMAdapter:
    """Return a fresh symbolic-counting generated adapter."""

    return GeneratedMAdapter()


def build_generated_p_adapter() -> GeneratedPAdapter:
    """Return a fresh clinical-counting generated adapter."""

    return GeneratedPAdapter()


def build_generated_r_adapter() -> GeneratedRAdapter:
    """Return a fresh transaction-counting generated adapter."""

    return GeneratedRAdapter()


__all__ = [
    "build_generated_h_adapter",
    "build_generated_m_adapter",
    "build_generated_p_adapter",
    "build_generated_r_adapter",
]
