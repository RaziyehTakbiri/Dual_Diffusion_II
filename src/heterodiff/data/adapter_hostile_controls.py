"""Closed development inventory for the adapter hostile-control harness.

This module contains no fixture, parser, adapter, or publication logic.  It
only freezes the Section 10.6 control identities, their Phase-C/Phase-D
ownership, and the exact failure boundary expected from each executable
control.  In particular, the public/private publication attack is a HOLD; it
cannot be represented as an executable Phase-C pass before the Phase-D
publisher and independent verifier exist.

The small AST check is a negative control for the shared capability planner
and runner.  It rejects identity-bearing values when they select control flow;
identity may still be copied into receipts and error-independent labels.
"""

from __future__ import annotations

import ast
from dataclasses import dataclass
from enum import Enum
import re
from typing import Optional, Tuple


class HostileControlStatus(str, Enum):
    """Closed implementation state for one Section 10.6 control."""

    PHASE_C_EXECUTABLE = "PHASE_C_EXECUTABLE"
    HOLD_UNIMPLEMENTED_PHASE_D = "HOLD/UNIMPLEMENTED_PHASE_D"


class HostileControlOwner(str, Enum):
    """Milestone that owns the enforcement boundary."""

    PHASE_C = "phase_c"
    PHASE_D = "phase_d"


class HostileFailureBoundary(str, Enum):
    """Exact layer expected to stop one hostile construction."""

    EVENT_CONFIGURATION_CONSTRUCTOR = (
        "event_configuration_constructor"
    )
    COVERAGE_LEDGER_CONSTRUCTOR = "coverage_ledger_constructor"
    ADAPTER_CAPABILITIES_CONSTRUCTOR = (
        "adapter_capabilities_constructor"
    )
    COMPLETE_EVIDENCE_VALIDATOR = "complete_evidence_validator"
    CAPABILITY_CONTROL_FLOW_AST = "capability_control_flow_ast"
    PUBLICATION_VERIFIER = "publication_verifier"


class HostileHarnessCode(str, Enum):
    """Stable codes emitted by this registry's own fail-closed checks."""

    CONTROL_ID_UNKNOWN = "CONTROL_ID_UNKNOWN"
    CONTROL_NOT_EXECUTABLE = "CONTROL_NOT_EXECUTABLE"
    SOURCE_SYNTAX_INVALID = "SOURCE_SYNTAX_INVALID"
    IDENTITY_DEPENDENT_CONTROL_FLOW = (
        "IDENTITY_DEPENDENT_CONTROL_FLOW"
    )


class HostileHarnessError(ValueError):
    """A coded failure owned by the domain-neutral hostile harness."""

    def __init__(self, message: str, *, code: HostileHarnessCode) -> None:
        if type(message) is not str:
            raise TypeError("hostile-harness message must be exact text")
        if type(code) is not HostileHarnessCode:
            raise TypeError("hostile-harness code must be exact")
        super().__init__(message)
        self.code = code.value


_CONTROL_ID_RE = re.compile(r"^HC-[A-Z0-9]+(?:-[A-Z0-9]+)*$")
_EXCEPTION_NAME_RE = re.compile(
    r"^[a-z_][a-z0-9_.]*\.[A-Z][A-Za-z0-9_]*$"
)
_ERROR_CODE_RE = re.compile(r"^[A-Z][A-Z0-9_]*$")


@dataclass(frozen=True)
class HostileControlSpec:
    """One immutable hostile-control registry row."""

    control_id: str
    statement: str
    owner: HostileControlOwner
    status: HostileControlStatus
    failure_boundary: HostileFailureBoundary
    expected_exception: Optional[str]
    expected_code: Optional[str]

    def __post_init__(self) -> None:
        if type(self.control_id) is not str or _CONTROL_ID_RE.fullmatch(
            self.control_id
        ) is None:
            raise ValueError("control_id must be a canonical HC identifier")
        if type(self.statement) is not str or not self.statement:
            raise TypeError("statement must be nonempty exact text")
        if type(self.owner) is not HostileControlOwner:
            raise TypeError("owner must be exact HostileControlOwner")
        if type(self.status) is not HostileControlStatus:
            raise TypeError("status must be exact HostileControlStatus")
        if type(self.failure_boundary) is not HostileFailureBoundary:
            raise TypeError(
                "failure_boundary must be exact HostileFailureBoundary"
            )
        if self.status is HostileControlStatus.PHASE_C_EXECUTABLE:
            if self.owner is not HostileControlOwner.PHASE_C:
                raise ValueError("an executable control must be owned by Phase C")
            if (
                type(self.expected_exception) is not str
                or _EXCEPTION_NAME_RE.fullmatch(self.expected_exception) is None
            ):
                raise ValueError(
                    "an executable control needs a canonical exception class"
                )
            if self.expected_code is not None and (
                type(self.expected_code) is not str
                or _ERROR_CODE_RE.fullmatch(self.expected_code) is None
            ):
                raise ValueError("expected_code must be a canonical error code")
            if (
                self.failure_boundary
                is HostileFailureBoundary.PUBLICATION_VERIFIER
            ):
                raise ValueError(
                    "a Phase-C control cannot claim publication enforcement"
                )
        else:
            if self.owner is not HostileControlOwner.PHASE_D:
                raise ValueError("the publication HOLD must be owned by Phase D")
            if (
                self.failure_boundary
                is not HostileFailureBoundary.PUBLICATION_VERIFIER
            ):
                raise ValueError(
                    "the Phase-D HOLD must name the publication verifier"
                )
            if self.expected_exception is not None or self.expected_code is not None:
                raise ValueError(
                    "an unimplemented control cannot advertise a passing failure"
                )


_ADAPTER_CONFORMANCE_ERROR = (
    "heterodiff.data.adapter_evidence.AdapterConformanceError"
)
_HARNESS_ERROR = (
    "heterodiff.data.adapter_hostile_controls.HostileHarnessError"
)


SECTION_10_6_HOSTILE_CONTROLS: Tuple[HostileControlSpec, ...] = (
    HostileControlSpec(
        "HC-SIMPLE-DUPLICATE-ATOMS",
        "A SIMPLE configuration contains repeated full model atoms.",
        HostileControlOwner.PHASE_C,
        HostileControlStatus.PHASE_C_EXECUTABLE,
        HostileFailureBoundary.EVENT_CONFIGURATION_CONSTRUCTOR,
        "builtins.ValueError",
        None,
    ),
    HostileControlSpec(
        "HC-FINITE-COUNTING-DUPLICATE-COLLAPSE",
        "A finite-counting adapter collapses one repeated occurrence.",
        HostileControlOwner.PHASE_C,
        HostileControlStatus.PHASE_C_EXECUTABLE,
        HostileFailureBoundary.COMPLETE_EVIDENCE_VALIDATOR,
        _ADAPTER_CONFORMANCE_ERROR,
        "NATIVE_EXPECTATION_MISMATCH",
    ),
    HostileControlSpec(
        "HC-TIE-JITTER",
        "An adapter changes one member of a declared source-time tie.",
        HostileControlOwner.PHASE_C,
        HostileControlStatus.PHASE_C_EXECUTABLE,
        HostileFailureBoundary.EVENT_CONFIGURATION_CONSTRUCTOR,
        "builtins.ValueError",
        None,
    ),
    HostileControlSpec(
        "HC-OMITTED-INVENTORY-ITEM",
        "An adapter omits one independently inventoried source item.",
        HostileControlOwner.PHASE_C,
        HostileControlStatus.PHASE_C_EXECUTABLE,
        HostileFailureBoundary.COMPLETE_EVIDENCE_VALIDATOR,
        _ADAPTER_CONFORMANCE_ERROR,
        "INVENTORY_EXPECTATION_MISMATCH",
    ),
    HostileControlSpec(
        "HC-DOUBLE-DISPOSITION",
        "One source item is assigned two primary dispositions.",
        HostileControlOwner.PHASE_C,
        HostileControlStatus.PHASE_C_EXECUTABLE,
        HostileFailureBoundary.COVERAGE_LEDGER_CONSTRUCTOR,
        "builtins.ValueError",
        None,
    ),
    HostileControlSpec(
        "HC-PRIVATE-IDENTIFIER-IN-NATIVE",
        "A private source identifier is injected into native model state.",
        HostileControlOwner.PHASE_C,
        HostileControlStatus.PHASE_C_EXECUTABLE,
        HostileFailureBoundary.COMPLETE_EVIDENCE_VALIDATOR,
        _ADAPTER_CONFORMANCE_ERROR,
        "NATIVE_EXPECTATION_MISMATCH",
    ),
    HostileControlSpec(
        "HC-FITTED-CAPABILITY-NO-FIT",
        "A fitted-capability descriptor binds the no-fit sentinel.",
        HostileControlOwner.PHASE_C,
        HostileControlStatus.PHASE_C_EXECUTABLE,
        HostileFailureBoundary.COMPLETE_EVIDENCE_VALIDATOR,
        _ADAPTER_CONFORMANCE_ERROR,
        "FITTED_STATE_REQUIRED",
    ),
    HostileControlSpec(
        "HC-ATOMIC-GRID-CONTINUOUS",
        "A continuous-time descriptor advertises the atomic-grid codec.",
        HostileControlOwner.PHASE_C,
        HostileControlStatus.PHASE_C_EXECUTABLE,
        HostileFailureBoundary.ADAPTER_CAPABILITIES_CONSTRUCTOR,
        "builtins.ValueError",
        None,
    ),
    HostileControlSpec(
        "HC-PRIVATE-VALUE-PUBLIC-EVIDENCE",
        "A private value is placed in serialized public evidence.",
        HostileControlOwner.PHASE_D,
        HostileControlStatus.HOLD_UNIMPLEMENTED_PHASE_D,
        HostileFailureBoundary.PUBLICATION_VERIFIER,
        None,
        None,
    ),
    HostileControlSpec(
        "HC-IDENTITY-DEPENDENT-BEHAVIOR",
        "Shared conformance control flow reads a registered identity label.",
        HostileControlOwner.PHASE_C,
        HostileControlStatus.PHASE_C_EXECUTABLE,
        HostileFailureBoundary.CAPABILITY_CONTROL_FLOW_AST,
        _HARNESS_ERROR,
        "IDENTITY_DEPENDENT_CONTROL_FLOW",
    ),
)

SECTION_10_6_HOSTILE_CONTROL_IDS: Tuple[str, ...] = tuple(
    control.control_id for control in SECTION_10_6_HOSTILE_CONTROLS
)

if len(set(SECTION_10_6_HOSTILE_CONTROL_IDS)) != len(
    SECTION_10_6_HOSTILE_CONTROL_IDS
):  # pragma: no cover - immutable module invariant
    raise RuntimeError("hostile-control IDs must be unique")


def hostile_control(control_id: str) -> HostileControlSpec:
    """Return one exact registry row or fail closed on an unknown ID."""

    if type(control_id) is not str:
        raise TypeError("control_id must be exact text")
    for control in SECTION_10_6_HOSTILE_CONTROLS:
        if control.control_id == control_id:
            return control
    raise HostileHarnessError(
        "hostile-control identity is not frozen",
        code=HostileHarnessCode.CONTROL_ID_UNKNOWN,
    )


def phase_c_executable_controls() -> Tuple[HostileControlSpec, ...]:
    """Return the immutable Phase-C execution inventory."""

    return tuple(
        control
        for control in SECTION_10_6_HOSTILE_CONTROLS
        if control.status is HostileControlStatus.PHASE_C_EXECUTABLE
    )


def require_phase_c_executable(control_id: str) -> HostileControlSpec:
    """Reject a HOLD control instead of allowing a caller to mark it passed."""

    control = hostile_control(control_id)
    if control.status is not HostileControlStatus.PHASE_C_EXECUTABLE:
        raise HostileHarnessError(
            "hostile control is not executable in Phase C",
            code=HostileHarnessCode.CONTROL_NOT_EXECUTABLE,
        )
    return control


_IDENTITY_CONTROL_MARKERS = frozenset(
    (
        "adapter_id",
        "adapter_version",
        "contract_version",
        "dataset",
        "domain",
        "file_format",
        "file_path",
        "filename",
        "identity",
        "parser",
        "policy_sha256",
        "registered_domain",
        "source_path",
    )
)


def _identity_bearing_name(name: str) -> bool:
    normalized = name.lower().strip("_")
    if normalized in _IDENTITY_CONTROL_MARKERS:
        return True
    return any(
        normalized.endswith("_" + marker)
        or normalized.startswith(marker + "_")
        for marker in _IDENTITY_CONTROL_MARKERS
    )


def _expression_reads_identity(expression: ast.AST) -> bool:
    for node in ast.walk(expression):
        if isinstance(node, ast.Name) and _identity_bearing_name(node.id):
            return True
        if isinstance(node, ast.Attribute) and _identity_bearing_name(node.attr):
            return True
        if (
            isinstance(node, ast.Call)
            and isinstance(node.func, ast.Name)
            and node.func.id in ("getattr", "hasattr", "setattr")
            and len(node.args) >= 2
            and isinstance(node.args[1], ast.Constant)
            and type(node.args[1].value) is str
            and _identity_bearing_name(node.args[1].value)
        ):
            return True
    return False


class _IdentityControlFlowVisitor(ast.NodeVisitor):
    def __init__(self) -> None:
        self.violation = False

    def _check(self, expression: ast.AST) -> None:
        if _expression_reads_identity(expression):
            self.violation = True

    def visit_If(self, node: ast.If) -> None:
        self._check(node.test)
        self.generic_visit(node)

    def visit_IfExp(self, node: ast.IfExp) -> None:
        self._check(node.test)
        self.generic_visit(node)

    def visit_While(self, node: ast.While) -> None:
        self._check(node.test)
        self.generic_visit(node)

    def visit_Match(self, node: ast.Match) -> None:
        self._check(node.subject)
        self.generic_visit(node)

    def visit_comprehension(self, node: ast.comprehension) -> None:
        for condition in node.ifs:
            self._check(condition)
        self.generic_visit(node)

    def visit_Subscript(self, node: ast.Subscript) -> None:
        # Identity-keyed handler maps are dispatch tables even without an
        # explicit ``if`` or ``match`` statement.
        self._check(node.slice)
        self.generic_visit(node)

    def visit_Call(self, node: ast.Call) -> None:
        if (
            isinstance(node.func, ast.Name)
            and node.func.id in ("getattr", "hasattr", "setattr")
        ):
            self._check(node)
        self.generic_visit(node)


def assert_capability_only_control_flow(source_text: str) -> None:
    """Reject identity-bearing selectors in shared planner/runner source."""

    if type(source_text) is not str:
        raise TypeError("source_text must be exact text")
    try:
        tree = ast.parse(source_text)
    except SyntaxError:
        raise HostileHarnessError(
            "control-flow source is not valid Python",
            code=HostileHarnessCode.SOURCE_SYNTAX_INVALID,
        ) from None
    visitor = _IdentityControlFlowVisitor()
    visitor.visit(tree)
    if visitor.violation:
        raise HostileHarnessError(
            "shared control flow reads an identity-bearing value",
            code=HostileHarnessCode.IDENTITY_DEPENDENT_CONTROL_FLOW,
        )


__all__ = [
    "HostileControlOwner",
    "HostileControlSpec",
    "HostileControlStatus",
    "HostileFailureBoundary",
    "HostileHarnessCode",
    "HostileHarnessError",
    "SECTION_10_6_HOSTILE_CONTROL_IDS",
    "SECTION_10_6_HOSTILE_CONTROLS",
    "assert_capability_only_control_flow",
    "hostile_control",
    "phase_c_executable_controls",
    "require_phase_c_executable",
]
