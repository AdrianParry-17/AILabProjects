"""Core road-graph domain types.

The graph deliberately uses only the Python standard library.  It supports a
directed multigraph (several road segments may connect the same two nodes),
which is important for real OSM-derived street data.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from math import asin, cos, isfinite, radians, sin, sqrt
from types import MappingProxyType
from typing import Any, Iterable, Mapping


class GraphValidationError(ValueError):
    """Raised when a graph or dataset violates a domain invariant."""


@dataclass(frozen=True, slots=True)
class GraphNode:
    id: str
    name: str
    kind: str
    lat: float
    lon: float
    attributes: Mapping[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if not self.id.strip():
            raise GraphValidationError("Node id cannot be empty")
        if not self.name.strip():
            raise GraphValidationError(f"Node {self.id!r} must have a name")
        if not (isfinite(self.lat) and -90 <= self.lat <= 90):
            raise GraphValidationError(f"Node {self.id!r} has an invalid latitude")
        if not (isfinite(self.lon) and -180 <= self.lon <= 180):
            raise GraphValidationError(f"Node {self.id!r} has an invalid longitude")
        object.__setattr__(self, "attributes", MappingProxyType(dict(self.attributes)))


@dataclass(frozen=True, slots=True)
class DirectedEdge:
    id: str
    source: str
    target: str
    distance_m: float
    speed_kph: float
    road_name: str
    road_class: str = "local"
    risk: float = 0.1
    traversable: bool = True
    attributes: Mapping[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if not self.id.strip():
            raise GraphValidationError("Edge id cannot be empty")
        if not self.source.strip() or not self.target.strip():
            raise GraphValidationError(f"Edge {self.id!r} must have source and target")
        if self.source == self.target:
            raise GraphValidationError(f"Self-loop edge {self.id!r} is not supported")
        if not isfinite(self.distance_m) or self.distance_m <= 0:
            raise GraphValidationError(f"Edge {self.id!r} distance_m must be positive")
        if not isfinite(self.speed_kph) or self.speed_kph <= 0:
            raise GraphValidationError(f"Edge {self.id!r} speed_kph must be positive")
        if not isfinite(self.risk) or not 0 <= self.risk <= 1:
            raise GraphValidationError(f"Edge {self.id!r} risk must be between 0 and 1")
        object.__setattr__(self, "attributes", MappingProxyType(dict(self.attributes)))

    @property
    def free_flow_time_s(self) -> float:
        return self.distance_m / (self.speed_kph * 1000 / 3600)


@dataclass(frozen=True, slots=True)
class DatasetMetadata:
    id: str
    name: str
    city: str
    country: str
    version: str
    source: str
    description: str
    generated_at: str | None = None
    disclaimer: str | None = None
    source_url: str | None = None
    license: str | None = None
    attribution: str | None = None
    osm_base_timestamp: str | None = None
    overpass_query: str | None = None
    network_filter: str | None = None
    bbox: tuple[float, float, float, float] | None = None
    stats: Mapping[str, Any] = field(default_factory=dict)


class RoadGraph:
    """Immutable directed multigraph with deterministic adjacency order."""

    def __init__(self, nodes: Iterable[GraphNode], edges: Iterable[DirectedEdge]) -> None:
        node_map: dict[str, GraphNode] = {}
        for node in nodes:
            if node.id in node_map:
                raise GraphValidationError(f"Duplicate node id: {node.id}")
            node_map[node.id] = node
        if not node_map:
            raise GraphValidationError("Graph must contain at least one node")

        edge_map: dict[str, DirectedEdge] = {}
        adjacency: dict[str, list[DirectedEdge]] = {node_id: [] for node_id in node_map}
        incoming: dict[str, list[DirectedEdge]] = {node_id: [] for node_id in node_map}
        for edge in edges:
            if edge.id in edge_map:
                raise GraphValidationError(f"Duplicate directed edge id: {edge.id}")
            if edge.source not in node_map:
                raise GraphValidationError(
                    f"Edge {edge.id!r} references unknown source {edge.source!r}"
                )
            if edge.target not in node_map:
                raise GraphValidationError(
                    f"Edge {edge.id!r} references unknown target {edge.target!r}"
                )
            edge_map[edge.id] = edge
            adjacency[edge.source].append(edge)
            incoming[edge.target].append(edge)

        self._nodes = MappingProxyType(node_map)
        self._edges = MappingProxyType(edge_map)
        self._adjacency = MappingProxyType(
            {key: tuple(value) for key, value in adjacency.items()}
        )
        self._incoming = MappingProxyType(
            {key: tuple(value) for key, value in incoming.items()}
        )
        # Imported or hand-authored datasets can slightly understate geometric
        # length.  Calibrating the straight-line lower bound preserves the
        # admissibility claim made by the heuristic registry.
        ratios = []
        for edge in edge_map.values():
            geometric = haversine_meters(node_map[edge.source], node_map[edge.target])
            if geometric > 0:
                ratios.append(edge.distance_m / geometric)
        self._distance_lower_bound_scale = min(1.0, min(ratios, default=1.0))

    @property
    def nodes(self) -> Mapping[str, GraphNode]:
        return self._nodes

    @property
    def edges(self) -> Mapping[str, DirectedEdge]:
        return self._edges

    def neighbors(self, node_id: str) -> tuple[DirectedEdge, ...]:
        try:
            return self._adjacency[node_id]
        except KeyError as exc:
            raise KeyError(f"Unknown node id: {node_id}") from exc

    def incoming(self, node_id: str) -> tuple[DirectedEdge, ...]:
        try:
            return self._incoming[node_id]
        except KeyError as exc:
            raise KeyError(f"Unknown node id: {node_id}") from exc

    def node(self, node_id: str) -> GraphNode:
        try:
            return self._nodes[node_id]
        except KeyError as exc:
            raise KeyError(f"Unknown node id: {node_id}") from exc

    def edge(self, edge_id: str) -> DirectedEdge:
        try:
            return self._edges[edge_id]
        except KeyError as exc:
            raise KeyError(f"Unknown edge id: {edge_id}") from exc

    def edge_coordinates(self, edge_id: str) -> list[list[float]]:
        """Return an oriented [longitude, latitude] polyline for an edge."""

        edge = self.edge(edge_id)
        geometry = edge.attributes.get("geometry")
        if isinstance(geometry, (list, tuple)) and len(geometry) >= 2:
            coordinates = [[float(point[0]), float(point[1])] for point in geometry]
        else:
            source = self.node(edge.source)
            target = self.node(edge.target)
            coordinates = [[source.lon, source.lat], [target.lon, target.lat]]
        return coordinates

    @property
    def max_speed_kph(self) -> float:
        return max((edge.speed_kph for edge in self._edges.values()), default=1.0)

    @property
    def distance_lower_bound_scale(self) -> float:
        return self._distance_lower_bound_scale

    def route_geojson(
        self, path: list[str], edge_ids: list[str] | None = None
    ) -> dict[str, Any] | None:
        if not path:
            return None
        if edge_ids is not None and len(edge_ids) != max(0, len(path) - 1):
            raise GraphValidationError("edge_ids length must equal len(path) - 1")
        if edge_ids:
            coordinates: list[list[float]] = []
            for index, edge_id in enumerate(edge_ids):
                edge = self.edge(edge_id)
                if edge.source != path[index] or edge.target != path[index + 1]:
                    raise GraphValidationError(
                        f"Edge {edge_id!r} does not connect path segment "
                        f"{path[index]!r} -> {path[index + 1]!r}"
                    )
                segment = self.edge_coordinates(edge_id)
                if coordinates and _same_position(coordinates[-1], segment[0]):
                    coordinates.extend(segment[1:])
                else:
                    coordinates.extend(segment)
        else:
            coordinates = [[self.node(node_id).lon, self.node(node_id).lat] for node_id in path]
        # A GeoJSON LineString must contain at least two positions. Represent a
        # zero-length start==goal route with two identical coordinates.
        if len(coordinates) == 1:
            coordinates.append(list(coordinates[0]))
        return {
            "type": "LineString",
            "coordinates": coordinates,
        }


def haversine_meters(a: GraphNode, b: GraphNode) -> float:
    """Great-circle distance using mean Earth radius."""

    earth_radius_m = 6_371_008.8
    lat1, lon1, lat2, lon2 = map(radians, (a.lat, a.lon, b.lat, b.lon))
    delta_lat = lat2 - lat1
    delta_lon = lon2 - lon1
    value = sin(delta_lat / 2) ** 2 + cos(lat1) * cos(lat2) * sin(delta_lon / 2) ** 2
    return 2 * earth_radius_m * asin(sqrt(min(1.0, value)))


def _same_position(a: list[float], b: list[float], tolerance: float = 1e-9) -> bool:
    return abs(a[0] - b[0]) <= tolerance and abs(a[1] - b[1]) <= tolerance
