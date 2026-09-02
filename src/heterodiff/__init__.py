"""HeteroDiff research package with lazy event-primitive exports.

Importing a package initializer is part of the runtime-attestor startup path.
The event transforms use NumPy, so eager re-export would import the numerical
stack before a child validates its request and startup state.  PEP 562 lazy
attributes preserve the public ``from heterodiff import Event`` interface
without crossing that boundary during an ordinary package import.
"""

__all__ = [
    "AffineTransform",
    "BoundedLogitTransform",
    "ContinuousField",
    "CountedEvent",
    "Event",
    "EventConfiguration",
    "EventObservation",
    "EventTypeSchema",
    "FeatureSchema",
    "IdentityTransform",
    "LogTransform",
    "MarkStatus",
    "MultiplicityMode",
    "ObservationPattern",
    "ObservationView",
    "ObservedAnchor",
    "SimplexALRTransform",
    "SupportKind",
    "TimeMeasureKind",
    "TimeReference",
    "TransformError",
    "canonical_sort",
    "transform_for_field",
]

__version__ = "0.1.0"


_EVENT_EXPORTS = frozenset(__all__)


def __getattr__(name: str) -> object:
    if name not in _EVENT_EXPORTS:
        raise AttributeError("module %r has no attribute %r" % (__name__, name))
    from . import events

    value = getattr(events, name)
    globals()[name] = value
    return value


def __dir__() -> list[str]:
    return sorted(set(globals()).union(_EVENT_EXPORTS))
