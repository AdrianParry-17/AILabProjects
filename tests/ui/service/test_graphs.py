"""ui/service/graphs unit tests (Task-003)."""

from __future__ import annotations

import ast
import inspect

from config.settings import SCHEMA_VERSION
from ui.service import graphs

EXPECTED_NODE_COUNT = 31
EXPECTED_EDGE_COUNT = 70

NODE_FIELD_NAMES = {"attributes", "id", "kind", "latitude", "longitude", "name"}
EDGE_FIELD_NAMES = {
    "attributes",
    "congestion",
    "direction",
    "distance_km",
    "edge_id",
    "end",
    "risk",
    "road_class",
    "road_name",
    "road_path",
    "start",
    "time_min",
}


def test_payload_node_and_edge_counts() -> None:
    payload = graphs.get_graph_payload()
    assert payload["metadata"]["node_count"] == EXPECTED_NODE_COUNT
    assert payload["metadata"]["edge_count"] == EXPECTED_EDGE_COUNT
    assert len(payload["graph"]["nodes"]) == EXPECTED_NODE_COUNT
    assert len(payload["graph"]["edges"]) == EXPECTED_EDGE_COUNT


def test_payload_metadata_schema_version() -> None:
    assert graphs.get_graph_payload()["metadata"]["schema_version"] == SCHEMA_VERSION


def test_payload_shape_matches_roadmap_section_11() -> None:
    payload = graphs.get_graph_payload()
    assert set(payload) == {"graph", "bbox", "metadata"}
    assert set(payload["graph"]) == {"nodes", "edges", "geojson"}


def test_node_field_names_match_map_contract() -> None:
    nodes = graphs.get_graph_payload()["graph"]["nodes"]
    assert all(set(node) == NODE_FIELD_NAMES for node in nodes)


def test_edge_field_names_match_map_contract() -> None:
    edges = graphs.get_graph_payload()["graph"]["edges"]
    assert all(set(edge) == EDGE_FIELD_NAMES for edge in edges)


def test_bbox_is_lat_lon_bounds() -> None:
    payload = graphs.get_graph_payload()
    latitudes = [node["latitude"] for node in payload["graph"]["nodes"]]
    longitudes = [node["longitude"] for node in payload["graph"]["nodes"]]
    assert payload["bbox"] == [
        min(latitudes),
        min(longitudes),
        max(latitudes),
        max(longitudes),
    ]


def test_geojson_is_feature_collection_with_point_and_line_features() -> None:
    payload = graphs.get_graph_payload()
    geojson = payload["graph"]["geojson"]
    assert geojson["type"] == "FeatureCollection"
    features = geojson["features"]
    assert len(features) == EXPECTED_NODE_COUNT + EXPECTED_EDGE_COUNT
    point_count = sum(
        1 for feature in features if feature["geometry"]["type"] == "Point"
    )
    line_count = sum(
        1 for feature in features if feature["geometry"]["type"] == "LineString"
    )
    assert point_count == EXPECTED_NODE_COUNT
    assert line_count == EXPECTED_EDGE_COUNT


def test_loader_returns_cached_objects() -> None:
    assert graphs.load_graphs() is graphs.load_graphs()
    assert graphs.get_delivery_graph() is graphs.get_delivery_graph()
    assert graphs.get_road_graph() is graphs.get_road_graph()
    assert graphs.get_delivery_graph() is graphs.load_graphs()[0]
    assert graphs.get_road_graph() is graphs.load_graphs()[1]


def test_payload_is_cached_identical() -> None:
    assert graphs.get_graph_payload() is graphs.get_graph_payload()


def test_no_algorithms_import() -> None:
    module = ast.parse(inspect.getsource(graphs))
    imported_modules: list[str] = []
    for node in ast.walk(module):
        if isinstance(node, ast.Import):
            imported_modules.extend(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module:
            imported_modules.append(node.module)
    assert not any(
        name == "algorithms" or name.startswith("algorithms.")
        for name in imported_modules
    )
