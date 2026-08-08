"""Dijkstra's Algorithm — placeholder.

Owned by the Dijkstra teammate. Implement `dijkstra()` (and a registered
`SearchAlgorithm` subclass, matching `algorithms/bfs.py`) per ALGORITHM_SPEC.md.
Note: the Road Graph (`delivery/road.py`) already has an internal Dijkstra for
shortest-path derivation; this module is the *search-layer* Dijkstra on the Delivery
Graph. Until then calling `dijkstra()` raises `NotImplementedError`.
"""

from __future__ import annotations

from shared.types import GraphLike


def dijkstra(
    graph: GraphLike,
    start: str,
    goal: str,
    enable_logging: bool = True,
):
    """Dijkstra's Algorithm — not implemented yet (owner: Dijkstra teammate)."""
    raise NotImplementedError(
        "Dijkstra is not implemented yet; it is owned by the Dijkstra teammate "
        "(algorithms/dijkstra.py)."
    )
