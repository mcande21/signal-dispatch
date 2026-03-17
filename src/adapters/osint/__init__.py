"""OSINT data source adapters -- Signal Dispatch local copy.

Copied from prediction-markets project. Import paths adapted for src.adapters.* namespace.
"""

from .federal_register import FederalRegisterAdapter
from .congress import CongressAdapter
from .fec import FecAdapter

__all__ = [
    "FederalRegisterAdapter",
    "CongressAdapter",
    "FecAdapter",
]
