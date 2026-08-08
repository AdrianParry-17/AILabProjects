"""Graph -> JSON/GeoJSON serialization for the GUI service.

Task-004 scope: reusable graph conversions (GeoJSON FeatureCollection + bounding
box). Task-010 adds `search_result_to_contract` + `metrics_from_result` for the
§ 11 `POST /search` response. Field names and coordinate orientation follow
`docs/MAP_CONTRACT.md` exactly; this module never renames model fields.
"""

from __future__ import annotations

from typing import Any

from core.search_result import SearchResult
from delivery.models import DeliveryGraph
from visualization.geojson import graph_to_geojson

__all__ = [
    "bbox_of",
    "metrics_from_result",
    "search_result_to_contract",
    "to_graph_geojson",
]


def to_graph_geojson(graph: DeliveryGraph) -> dict[str, Any]:
    """Encode a graph as a GeoJSON FeatureCollection (nodes + edges).

    Delegates to `visualization.geojson.graph_to_geojson` so the `[lon, lat]`
    orientation lives in a single place (MAP_CONTRACT.md § 2.2).
    """
    return graph_to_geojson(graph)


def bbox_of(graph: DeliveryGraph) -> list[float]:
    """Return the `[min_lat, min_lon, max_lat, max_lon]` bounds of a graph."""
    latitudes = [node.latitude for node in graph.nodes]
    longitudes = [node.longitude for node in graph.nodes]
    return [min(latitudes), min(longitudes), max(latitudes), max(longitudes)]


def search_result_to_contract(result: SearchResult) -> dict[str, Any]:
    """Encode a `SearchResult` as the § 11 `POST /search` ``result`` object.

    Mirrors `SearchResult` field names exactly (MAP_CONTRACT § 2): `path`,
    `visited_nodes`, `steps`, `total_distance_km`, `total_time_min`,
    `total_cost`, `processing_time_ms`, `explanation`.
    """
    return {
        "path": list(result.path),
        "visited_nodes": list(result.visited_nodes),
        "steps": [step.model_dump() for step in result.steps],
        "total_distance_km": result.total_distance_km,
        "total_time_min": result.total_time_min,
        "total_cost": result.total_cost,
        "processing_time_ms": result.processing_time_ms,
        "explanation": result.explanation,
    }


def metrics_from_result(result: SearchResult) -> dict[str, Any]:
    """Derive the § 11 `metrics` object from a `SearchResult`.

    `hops = path.length - 1` and `nodes_visited = len(visited_nodes)` are
    front-end derived values (COMPONENT_SPEC § 0.2); the metric numbers are the
    `SearchResult` totals copied verbatim.
    """
    return {
        "hops": max(0, len(result.path) - 1),
        "nodes_visited": len(result.visited_nodes),
        "distance_km": result.total_distance_km,
        "time_min": result.total_time_min,
        "cost": result.total_cost,
        "processing_time_ms": result.processing_time_ms,
    }
