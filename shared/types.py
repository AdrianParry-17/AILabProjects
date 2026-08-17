"""Generic, reusable type aliases and structural types.

Only generic utility types live here (no project-specific models). Project models
live in `data/models.py`, `delivery/models.py`, and `core/`.
"""

from __future__ import annotations

from typing import Any, Protocol

# Node id is a stable string (e.g. "osm_123", "poi_warehouse_1").
NodeId = str

# (latitude, longitude) in WGS84 decimal degrees.
LatLon = tuple[float, float]

# A [longitude, latitude] point (matching the dataset geometry convention).
LonLat = list[float]

# A polyline of [lon, lat] points (dataset geometry convention).
Polyline = list[LonLat]


class NodeLike(Protocol):
    """The minimum a graph node must expose for search + metrics."""

    id: str


class EdgeLike(Protocol):
    """The minimum a directed edge must expose for search + metrics.

    Satisfied by `data.models.Edge` and `delivery.models.DeliveryEdge`.
    """

    start: str
    end: str
    distance_km: float
    time_min: float
    congestion: float
    risk: float


class GraphLike(Protocol):
    """Structural type accepted by every search algorithm and metric helper.

    Both `data.models.GraphData` and `delivery.models.DeliveryGraph` satisfy it
    (each exposes `.nodes` / `.edges`). NOTE: the collection members are typed `Any`
    because of a mypy 2.3 structural-matching regression for `Sequence` members in a
    `Protocol`; the per-element contracts are documented by `NodeLike` / `EdgeLike`
    (CONVENTION.md § 4.2 allows `Any` at a heterogeneous layer boundary).
    """

    nodes: Any
    edges: Any
