"""Road Graph: backend-only shortest-path computation on the OSM road network.

Encapsulates `data.models.GraphData` and provides directed Dijkstra shortest paths.
The delivery-graph builder (and the UI detail expansion) use this layer; search
algorithms themselves operate on the Delivery Graph, not on this one.
"""

from __future__ import annotations

import heapq
from dataclasses import dataclass, field
from itertools import pairwise

from data.models import Edge, GraphData


@dataclass
class RoadPath:
    """A concrete street-level route between two nodes (typically two POIs)."""

    node_ids: list[str] = field(default_factory=list)
    distance_km: float = 0.0
    time_min: float = 0.0
    congestion: float = 0.0
    risk: float = 0.0
    geometry: list[list[float]] = field(default_factory=list)


class RoadGraph:
    """Indexed, directed access to the road graph with Dijkstra shortest paths."""

    def __init__(self, graph: GraphData) -> None:
        self.graph = graph
        self._coords: dict[str, list[float]] = {}
        self._out: dict[str, list[Edge]] = {}
        self._edge_by_pair: dict[tuple[str, str], Edge] = {}
        for node in graph.nodes:
            self._coords[node.id] = [node.longitude, node.latitude]
        for edge in graph.edges:
            self._out.setdefault(edge.start, []).append(edge)
            self._edge_by_pair[(edge.start, edge.end)] = edge

    def outgoing(self, node: str) -> list[Edge]:
        return self._out.get(node, [])

    def edge(self, source: str, target: str) -> Edge | None:
        return self._edge_by_pair.get((source, target))

    def dijkstra(self, start: str) -> tuple[dict[str, float], dict[str, str | None]]:
        """Return (distance, predecessor) for all nodes reachable from `start`."""
        dist: dict[str, float] = {start: 0.0}
        prev: dict[str, str | None] = {start: None}
        heap: list[tuple[float, str]] = [(0.0, start)]
        while heap:
            d, node = heapq.heappop(heap)
            if d > dist.get(node, float("inf")):
                continue
            for edge in self.outgoing(node):
                new_distance = d + edge.distance_km
                if new_distance < dist.get(edge.end, float("inf")):
                    dist[edge.end] = new_distance
                    prev[edge.end] = node
                    heapq.heappush(heap, (new_distance, edge.end))
        return dist, prev

    def shortest_path(self, start: str, end: str) -> RoadPath | None:
        """Shortest directed path (by distance) from `start` to `end`, or None."""
        dist, prev = self.dijkstra(start)
        if end not in dist:
            return None
        node_ids: list[str] = []
        cursor: str | None = end
        while cursor is not None:
            node_ids.append(cursor)
            cursor = prev[cursor]
        node_ids.reverse()
        return self._aggregate(node_ids)

    def _aggregate(self, node_ids: list[str]) -> RoadPath:
        distance = 0.0
        time_min = 0.0
        congestion = 0.0
        risk = 0.0
        geometry: list[list[float]] = []
        for source, target in pairwise(node_ids):
            edge = self.edge(source, target)
            if edge is None:
                raise ValueError(f"Missing road edge {source!r} -> {target!r}")
            distance += edge.distance_km
            time_min += edge.time_min
            congestion = max(congestion, edge.congestion)
            risk = max(risk, edge.risk)
            edge_geom = edge.attributes.get("length_geometry")
            if isinstance(edge_geom, list) and edge_geom:
                for point in edge_geom:
                    if not geometry or geometry[-1] != point:
                        geometry.append(point)
            else:
                for node in (source, target):
                    position = self._coords.get(node, [])
                    if position and (not geometry or geometry[-1] != position):
                        geometry.append(position)
        return RoadPath(
            node_ids=list(node_ids),
            distance_km=distance,
            time_min=time_min,
            congestion=congestion,
            risk=risk,
            geometry=geometry,
        )