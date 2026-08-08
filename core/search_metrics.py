"""Summary metrics derived from a `SearchResult`.

Distinct from `algorithms/metrics.py` (which aggregates *edge* metrics along a path
from the graph); this module summarizes a completed `SearchResult` for reports/UI.
"""

from __future__ import annotations

from dataclasses import dataclass

from core.search_result import SearchResult


@dataclass(frozen=True, slots=True)
class SearchMetrics:
    """Compact summary of a finished search."""

    hops: int
    nodes_visited: int
    distance_km: float
    time_min: float
    cost: float
    processing_time_ms: float

    @classmethod
    def from_result(cls, result: SearchResult) -> SearchMetrics:
        return cls(
            hops=max(0, len(result.path) - 1),
            nodes_visited=len(result.visited_nodes),
            distance_km=result.total_distance_km,
            time_min=result.total_time_min,
            cost=result.total_cost,
            processing_time_ms=result.processing_time_ms,
        )
