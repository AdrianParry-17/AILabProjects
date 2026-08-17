"""Common cost function and heuristic estimates.

The path-cost equation is (see ALGORITHM_SPEC § 14):

    Cost = alpha * Distance + beta * Time + gamma * Congestion + delta * Risk

The weights (`CostWeights`, `DEFAULT_WEIGHTS`) live in `config/defaults.py` — this
module only provides the shared `edge_cost` consumed by every weighted algorithm
(UCS, A*, Dijkstra) and by BFS for its reporting-only `total_cost`. `CostWeights` /
`DEFAULT_WEIGHTS` are re-exported here for callers that used `algorithms.heuristic`.
"""

from __future__ import annotations

import math
from typing import Protocol

from config.defaults import DEFAULT_WEIGHTS, CostWeights
from shared.types import EdgeLike

__all__ = [
    "DEFAULT_WEIGHTS",
    "CostWeights",
    "GeoNode",
    "edge_cost",
    "haversine_km",
    "straight_line_heuristic",
]


class GeoNode(Protocol):
    """A node exposing WGS84 coordinates (satisfied by `data.Node`/`delivery.DeliveryNode`)."""

    latitude: float
    longitude: float


def edge_cost(edge: EdgeLike, weights: CostWeights = DEFAULT_WEIGHTS) -> float:
    """Base cost of a single directed edge using raw dataset attributes."""
    return (
        weights.distance * edge.distance_km
        + weights.time * edge.time_min
        + weights.congestion * edge.congestion
        + weights.risk * edge.risk
    )


def haversine_km(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Great-circle distance in kilometres between two WGS84 points."""
    earth_radius_km = 6371.0088
    phi1, phi2 = math.radians(lat1), math.radians(lat2)
    delta_phi = math.radians(lat2 - lat1)
    delta_lambda = math.radians(lon2 - lon1)
    value = (
        math.sin(delta_phi / 2) ** 2
        + math.cos(phi1) * math.cos(phi2) * math.sin(delta_lambda / 2) ** 2
    )
    return 2 * earth_radius_km * math.asin(math.sqrt(min(1.0, value)))


def straight_line_heuristic(
    node: GeoNode,
    goal: GeoNode,
    weights: CostWeights = DEFAULT_WEIGHTS,
) -> float:
    """Admissible lower bound on the remaining `edge_cost` from `node` to `goal`.

    Only the (non-negative) distance component is counted: a straight line is always
    shorter than the road path, and every omitted component (time, congestion, risk)
    is non-negative, so `h` never overestimates the true remaining cost.
    """
    return weights.distance * haversine_km(
        node.latitude, node.longitude, goal.latitude, goal.longitude
    )
