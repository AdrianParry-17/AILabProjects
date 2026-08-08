"""Graph loading + caching for the GUI JSON service.

Loads the delivery graph and the road graph exactly once (module-level
``functools.cache``) and builds the ``GET /graph`` payload of
``docs/GUI_ROADMAP.md`` § 11: the delivery graph (``graph`` with nodes / edges /
geojson), a ``bbox`` and ``metadata``. GeoJSON / bbox conversion is delegated to
``serialization`` so those contracts live in a single place. Depends only on the
``data`` / ``delivery`` / ``config`` layers plus ``serialization`` — never on
``algorithms`` (GUI_ROADMAP.md § 2 coupling rule).
"""

from __future__ import annotations

from functools import cache
from typing import Any

from config.settings import SCHEMA_VERSION
from data.loader import load_graph
from delivery.loader import load_delivery_graph
from delivery.models import DeliveryGraph
from delivery.road import RoadGraph

from . import serialization

__all__ = [
    "get_delivery_graph",
    "get_graph_payload",
    "get_road_graph",
    "load_graphs",
]


@cache
def load_graphs() -> tuple[DeliveryGraph, RoadGraph]:
    """Load the delivery + road graphs once and cache them for the process lifetime.

    Returns:
        ``(delivery_graph, road_graph)``; the same objects on every call.
    """
    delivery_graph = load_delivery_graph()
    road_graph = RoadGraph(load_graph())
    return delivery_graph, road_graph


def get_delivery_graph() -> DeliveryGraph:
    """Return the cached application-layer delivery graph."""
    return load_graphs()[0]


def get_road_graph() -> RoadGraph:
    """Return the cached road graph (backend shortest-path layer)."""
    return load_graphs()[1]


@cache
def get_graph_payload() -> dict[str, Any]:
    """Build the ``GET /graph`` payload (GUI_ROADMAP.md § 11).

    Graph → GeoJSON / bbox conversion is delegated to ``serialization`` so the
    ``[lon, lat]`` and ``[min_lat, min_lon, max_lat, max_lon]`` contracts live in
    a single source of truth.

    Returns:
        ``graph`` (nodes / edges / geojson of the delivery graph), ``bbox``
        (``[min_lat, min_lon, max_lat, max_lon]``) and ``metadata``
        (``schema_version`` / ``node_count`` / ``edge_count``).
    """
    delivery_graph = get_delivery_graph()
    return {
        "graph": {
            "nodes": [node.model_dump() for node in delivery_graph.nodes],
            "edges": [edge.model_dump() for edge in delivery_graph.edges],
            "geojson": serialization.to_graph_geojson(delivery_graph),
        },
        "bbox": serialization.bbox_of(delivery_graph),
        "metadata": {
            "schema_version": SCHEMA_VERSION,
            "node_count": len(delivery_graph.nodes),
            "edge_count": len(delivery_graph.edges),
        },
    }
