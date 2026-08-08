"""Shared building blocks for concrete algorithm modules.

Hosts the helpers every `algorithms/*.py` owner uses (path reconstruction and uniform
`SearchResult` assembly) plus the `register_algorithm` decorator re-export. No single
algorithm's strategy lives here — that belongs to the per-algorithm module.
"""

from __future__ import annotations

import time

from core.search_algorithm import SearchAlgorithm, register_algorithm
from core.search_result import SearchResult, SearchStep

__all__ = [
    "SearchAlgorithm",
    "SearchResult",
    "SearchStep",
    "build_result",
    "reconstruct_path",
    "register_algorithm",
]


def reconstruct_path(parent: dict[str, str | None], goal: str) -> list[str]:
    """Rebuild the start->goal node list from a predecessor map."""
    path: list[str] = []
    node: str | None = goal
    while node is not None:
        path.append(node)
        node = parent[node]
    path.reverse()
    return path


def build_result(
    *,
    path: list[str],
    visited_order: list[str],
    steps: list[SearchStep],
    total_distance_km: float,
    total_time_min: float,
    total_cost: float,
    started: float,
    explanation: str,
) -> SearchResult:
    """Assemble a `SearchResult` with the uniform rounding/timing contract."""
    return SearchResult(
        path=path,
        visited_nodes=visited_order,
        steps=steps,
        total_distance_km=round(total_distance_km, 3),
        total_time_min=round(total_time_min, 3),
        total_cost=round(total_cost, 3),
        processing_time_ms=round((time.perf_counter() - started) * 1000.0, 3),
        explanation=explanation,
    )
