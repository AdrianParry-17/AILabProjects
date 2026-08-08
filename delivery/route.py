"""Expand a Delivery-Graph POI path into a full street-level Road Graph route.

Search algorithms work on the Delivery Graph (few POI hops); the UI and reports want
the detailed map geometry. This module bridges the two layers: given the POI-level
path, it stitches together the per-edge road paths stored in the DeliveryEdges (or
re-computes them against the Road Graph).
"""

from __future__ import annotations

from dataclasses import dataclass, field
from itertools import pairwise

from delivery.models import DeliveryGraph
from delivery.road import RoadGraph


@dataclass
class ExpandedRoute:
    """Street-level route built by concatenating POI-to-POI road paths."""

    node_ids: list[str] = field(default_factory=list)
    geometry: list[list[float]] = field(default_factory=list)
    hops: int = 0
    distance_km: float = 0.0
    time_min: float = 0.0


def expand_poi_path(
    poi_path: list[str],
    road_graph: RoadGraph,
    delivery_graph: DeliveryGraph | None = None,
) -> ExpandedRoute:
    """Expand a list of POI ids into a full road-node route.

    The full geometry is the concatenation of each DeliveryEdge's `road_path`/geometry
    when a DeliveryGraph is given; otherwise each hop is re-computed with the Road
    Graph's shortest path.
    """
    if len(poi_path) < 2:
        return ExpandedRoute(node_ids=list(poi_path), hops=max(0, len(poi_path) - 1))

    route = ExpandedRoute()
    for source, target in pairwise(poi_path):
        edge = None
        if delivery_graph is not None:
            edge = next(
                (e for e in delivery_graph.edges if e.start == source and e.end == target),
                None,
            )
        if edge is not None and edge.road_path:
            segment_nodes = list(edge.road_path)
            segment_geometry: list[list[float]] = list(
                edge.attributes.get("geometry", [])
            )
            segment_distance = edge.distance_km
            segment_time = edge.time_min
        else:
            path = road_graph.shortest_path(source, target)
            if path is None:
                raise ValueError(
                    f"Cannot expand hop {source!r} -> {target!r}: no road path"
                )
            segment_nodes = list(path.node_ids)
            segment_geometry = list(path.geometry)
            segment_distance = path.distance_km
            segment_time = path.time_min

        route.distance_km += segment_distance
        route.time_min += segment_time
        route.hops += 1
        if not route.node_ids:
            route.node_ids.extend(segment_nodes)
            route.geometry.extend(segment_geometry)
        else:
            route.node_ids.extend(segment_nodes[1:])
            route.geometry.extend(segment_geometry[1:])
    return route