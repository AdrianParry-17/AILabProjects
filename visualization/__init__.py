"""Visualization layer: map/report serialization of graphs and routes.

Depends on `shared` (+ optionally `core`/`delivery` for their data shapes). Contains
no search logic — it only renders what other layers compute (ARCHITECTURE.md § 3).
"""

from visualization.geojson import (
    edge_geometry,
    graph_to_geojson,
    point_geometry,
    route_to_geojson,
)

__all__ = [
    "edge_geometry",
    "graph_to_geojson",
    "point_geometry",
    "route_to_geojson",
]
