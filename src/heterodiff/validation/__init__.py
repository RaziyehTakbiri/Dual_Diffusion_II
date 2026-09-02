"""Independent, dependency-optional validation oracles.

Nothing in this package participates in training or production data
transformation.  Its results are evidence about agreement with independently
maintained implementations.
"""

from .mido_oracle import (
    MIDO_ORACLE_VERSION,
    MidoDifferentialError,
    MidoDifferentialReport,
    MidoUnavailableError,
    MidoVersionError,
    validate_midi_bytes_against_mido,
    validate_midi_file_against_mido,
    validate_parsed_midi_against_mido,
)

__all__ = [
    "MIDO_ORACLE_VERSION",
    "MidoDifferentialError",
    "MidoDifferentialReport",
    "MidoUnavailableError",
    "MidoVersionError",
    "validate_midi_bytes_against_mido",
    "validate_midi_file_against_mido",
    "validate_parsed_midi_against_mido",
]
