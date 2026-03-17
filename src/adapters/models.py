"""Minimal models for Signal Dispatch adapters.

Extracted from prediction-markets/src/models.py to keep SD self-contained.
Only includes types actually needed by the adapter layer.
"""

from dataclasses import dataclass


@dataclass
class OsintResult:
    """Structured output from an OSINT data source adapter."""

    source: str               # Adapter name (e.g., "federal_register")
    source_url: str           # URL of the specific document/record
    fetch_time: str           # ISO timestamp of fetch
    data_points: list[dict]   # Source-specific structured data
    staleness_hours: float    # How old is this data?
    confidence: float         # Adapter's self-assessed reliability (0.0-1.0)
    summary: str              # Human-readable one-liner
    market_relevance: float   # How relevant to the queried market (0.0-1.0)
