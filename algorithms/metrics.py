"""Shared path-metric aggregation used by every search algorithm.

No duplication: all algorithms consume these helpers instead of re-implementing
edge lookups or sum accumulation. Consumes any graph exposing `nodes`/`edges`
(`data.GraphData` or `delivery.DeliveryGraph`) via the `GraphLike` protocol
(defined in `shared/types.py`).
"""

from __future__ import annotations

from itertools import pairwise

from shared.types import EdgeLike, GraphLike


def find_edge(graph: GraphLike, start: str, end: str) -> EdgeLike | None:
    """Return the directed edge from start to end, or None if it does not exist."""
    for edge in graph.edges:
        if edge.start == start and edge.end == end:
            return edge
    return None


def build_edge_lookup(graph: GraphLike) -> dict[tuple[str, str], EdgeLike]:
    """Build an id-pair -> Edge map for O(1) lookups along reconstructed paths."""
    return {(edge.start, edge.end): edge for edge in graph.edges}


def path_metrics(
    graph: GraphLike,
    path: list[str],
    edge_lookup: dict[tuple[str, str], EdgeLike] | None = None,
) -> tuple[float, float]:
    """Sum distance_km and time_min along a reconstructed path.

    Returns (total_distance_km, total_time_min). Both are 0.0 for an empty/one-node path.
    """
    if len(path) < 2:
        return 0.0, 0.0
    lookup = edge_lookup if edge_lookup is not None else build_edge_lookup(graph)
    distance = 0.0
    time_min = 0.0
    for source, target in pairwise(path):
        edge = lookup.get((source, target))
        if edge is None:
            raise ValueError(
                f"Path references missing directed edge: {source!r} -> {target!r}"
            )
        distance += edge.distance_km
        time_min += edge.time_min
    return distance, time_min


def path_total_cost(
    graph: GraphLike,
    path: list[str],
    edge_lookup: dict[tuple[str, str], EdgeLike] | None = None,
    *,
    cost_fn,
) -> float:
    """Sum a caller-supplied edge cost function along the path.

    Mirrors `path_metrics`: a path referencing a missing directed edge raises
    `ValueError` rather than silently dropping it.
    """
    lookup = edge_lookup if edge_lookup is not None else build_edge_lookup(graph)
    total = 0.0
    for source, target in pairwise(path):
        edge = lookup.get((source, target))
        if edge is None:
            raise ValueError(
                f"Path references missing directed edge: {source!r} -> {target!r}"
            )
        total += cost_fn(edge)
    return total
