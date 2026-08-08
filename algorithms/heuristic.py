"""Common cost function and heuristic estimates.

The path-cost equation is (see ALGORITHM_SPEC § 14):

    Cost = alpha * Distance + beta * Time + gamma * Congestion + delta * Risk

The weights (`CostWeights`, `DEFAULT_WEIGHTS`) live in `config/defaults.py` — this
module only provides the shared `edge_cost` consumed by every weighted algorithm
(UCS, A*, Dijkstra) and by BFS for its reporting-only `total_cost`. `CostWeights` /
`DEFAULT_WEIGHTS` are re-exported here for callers that used `algorithms.heuristic`.
"""

from __future__ import annotations

from config.defaults import DEFAULT_WEIGHTS, CostWeights
from shared.types import EdgeLike

__all__ = ["DEFAULT_WEIGHTS", "CostWeights", "edge_cost"]


def edge_cost(edge: EdgeLike, weights: CostWeights = DEFAULT_WEIGHTS) -> float:
    """Base cost of a single directed edge using raw dataset attributes."""
    return (
        weights.distance * edge.distance_km
        + weights.time * edge.time_min
        + weights.congestion * edge.congestion
        + weights.risk * edge.risk
    )
