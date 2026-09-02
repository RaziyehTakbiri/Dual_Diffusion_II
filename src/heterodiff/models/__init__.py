"""Model configuration primitives that do not import optional frameworks.

The NumPy event/process core must remain importable without PyTorch.  Concrete
reference neural modules therefore live in :mod:`heterodiff.models.fixed_grid`
and are imported explicitly only after installing the ``reference`` extra.
"""

from .reference_config import FixedGridReferenceConfig

__all__ = ["FixedGridReferenceConfig"]
