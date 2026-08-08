"""Visualization-layer tests: GeoJSON serialization contract."""

from __future__ import annotations

from data.models import Edge, GraphData, Node
from visualization import graph_to_geojson, route_to_geojson

NODES = [
    Node(id="A", name="A", latitude=10.0, longitude=106.0),
    Node(id="B", name="B", latitude=10.1, longitude=106.1),
]
EDGES = [
    Edge(
        start="A",
        end="B",
        distance_km=1.0,
        time_min=1.0,
        congestion=1.0,
        risk=0.0,
        direction="two-way",
        attributes={"geometry": [[106.0, 10.0], [106.05, 10.05], [106.1, 10.1]]},
    ),
]
GRAPH = GraphData(nodes=NODES, edges=EDGES)


def test_graph_to_geojson_shape() -> None:
    payload = graph_to_geojson(GRAPH)
    assert payload["type"] == "FeatureCollection"
    assert len(payload["features"]) == len(NODES) + len(EDGES)
    points = [f for f in payload["features"] if f["geometry"]["type"] == "Point"]
    lines = [f for f in payload["features"] if f["geometry"]["type"] == "LineString"]
    assert len(points) == 2
    assert len(lines) == 1
    assert lines[0]["geometry"]["coordinates"][0] == [106.0, 10.0]


def test_route_to_geojson_shape() -> None:
    feature = route_to_geojson([[106.0, 10.0], [106.1, 10.1]], properties={"name": "r1"})
    assert feature["type"] == "Feature"
    assert feature["geometry"]["type"] == "LineString"
    assert feature["properties"]["name"] == "r1"
