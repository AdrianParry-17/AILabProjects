"""Serialization helpers that turn graph data and routes into GeoJSON.

Consumed by the UI and by reports; contains no search logic (algorithms live in
`algorithms/`, route expansion in `delivery/route.py`). Pure stdlib on purpose.
"""

from __future__ import annotations

from typing import Any

from shared.types import GraphLike, Polyline


def point_geometry(node: Any) -> list[float]:
    """Return the [lon, lat] position of a node-like object."""
    return [node.longitude, node.latitude]


def edge_geometry(edge: Any) -> Polyline | None:
    """Return the stored polyline of an edge, if it carries one."""
    geometry = edge.attributes.get("geometry")
    if isinstance(geometry, list) and geometry:
        return geometry
    return None


def route_to_geojson(
    polyline: Polyline,
    *,
    properties: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Encode a route polyline as a GeoJSON LineString feature."""
    return {
        "type": "Feature",
        "geometry": {"type": "LineString", "coordinates": list(polyline)},
        "properties": dict(properties or {}),
    }


def graph_to_geojson(graph: GraphLike) -> dict[str, Any]:
    """Encode a whole graph (nodes + edges) as a GeoJSON FeatureCollection.

    Nodes become Point features, edges LineString features (falling back to a
    straight [lon, lat] segment between endpoints when no geometry is stored).
    """
    features: list[dict[str, Any]] = []
    positions = {node.id: point_geometry(node) for node in graph.nodes}
    for node in graph.nodes:
        features.append(
            {
                "type": "Feature",
                "geometry": {"type": "Point", "coordinates": positions[node.id]},
                "properties": {"id": node.id, "name": node.name, "kind": node.kind},
            }
        )
    for edge in graph.edges:
        geometry = edge_geometry(edge)
        if geometry is None:
            start = positions.get(edge.start)
            end = positions.get(edge.end)
            if start is None or end is None:
                continue
            geometry = [start, end]
        features.append(
            {
                "type": "Feature",
                "geometry": {"type": "LineString", "coordinates": geometry},
                "properties": {"start": edge.start, "end": edge.end},
            }
        )
    return {"type": "FeatureCollection", "features": features}
