"""End-to-end workflow test: Delivery Graph -> Search -> Route Expansion -> Visualization.

This is the maintainability/integration contract test. It exercises the exact chain the
React UI and demo rely on, against the committed dataset files:

    1. DeliveryGraph (+ RoadGraph) load and validate.
    2. BFS search on the Delivery Graph -> SearchResult.
    3. expand_poi_path -> ExpandedRoute (street-level polyline).
    4. The Visualization payload = the serialized SearchResult + ExpandedRoute JSON.

It does not rebuild the dataset (that is covered by builder determinism checks); it
validates that the committed artifacts and the whole pipeline agree.
"""

from __future__ import annotations

from algorithms.bfs import bfs
from core.search_result import SearchResult
from data.loader import load_graph
from delivery.loader import (
    load_delivery_graph,
    load_delivery_metadata,
    validate_delivery_graph,
)
from delivery.models import DeliveryGraph
from delivery.road import RoadGraph
from delivery.route import ExpandedRoute, expand_poi_path


def _workflow() -> tuple[DeliveryGraph, RoadGraph, SearchResult, ExpandedRoute]:
    road = load_graph()
    delivery = load_delivery_graph()  # validates on load
    road_graph = RoadGraph(road)

    start = delivery.nodes[0].id
    goal = delivery.nodes[-1].id
    result = bfs(delivery, start, goal)

    expanded = expand_poi_path(result.path, road_graph, delivery)
    return delivery, road_graph, result, expanded


def test_delivery_graph_loads_and_validates() -> None:
    delivery = load_delivery_graph()
    validate_delivery_graph(delivery)  # explicit, idempotent
    metadata = load_delivery_metadata()
    assert metadata["generated"] is True
    assert metadata["schema_version"] == "1.0"
    stats = metadata["stats"]
    assert stats["poi_nodes"] == len(delivery.nodes) == 31
    assert stats["directed_edges"] == len(delivery.edges) == 70


def test_workflow_search_returns_path_into_expanded_route() -> None:
    delivery, _road_graph, result, expanded = _workflow()
    start = delivery.nodes[0].id
    goal = delivery.nodes[-1].id
    assert result.path[0] == start
    assert result.path[-1] == goal
    assert len(result.path) >= 2
    # The expanded route must embed every POI in the search path in order.
    for poi in result.path:
        assert poi in expanded.node_ids


def test_workflow_expanded_route_has_valid_geometry_metrics() -> None:
    _, _, _result, expanded = _workflow()
    assert expanded.hops >= 1
    assert expanded.distance_km > 0.0
    assert expanded.time_min > 0.0
    assert len(expanded.geometry) >= 2
    for point in expanded.geometry:
        assert len(point) == 2
        lon, lat = point
        assert 105.0 < lon < 108.0  # WGS84 decimal degrees, [lon, lat] order
        assert 9.0 < lat < 12.0
        assert lat < lon  # HCMC bbox: longitude >> latitude; confirms [lon, lat] order


def test_workflow_search_result_serializes_to_map_contract() -> None:
    _, _, result, _ = _workflow()
    payload = result.model_dump()
    expected = {
        "path",
        "visited_nodes",
        "steps",
        "total_distance_km",
        "total_time_min",
        "total_cost",
        "processing_time_ms",
        "explanation",
    }
    assert set(payload) == expected
    # steps matches the UI animation contract: same order as visited_nodes.
    assert [step["current_node"] for step in payload["steps"]] == payload["visited_nodes"]


def test_workflow_expanded_route_serializes_to_map_contract() -> None:
    _, _, _, expanded = _workflow()
    contract_fields = ("node_ids", "geometry", "hops", "distance_km", "time_min")
    # ExpandedRoute is a dataclass; mirror the served JSON shape field-for-field.
    payload: dict[str, object] = {
        "node_ids": expanded.node_ids,
        "geometry": expanded.geometry,
        "hops": expanded.hops,
        "distance_km": expanded.distance_km,
        "time_min": expanded.time_min,
    }
    assert set(payload) == set(contract_fields)
    geometry = payload["geometry"]
    assert isinstance(geometry, list)
    assert geometry
    assert all(isinstance(point, list) and len(point) == 2 for point in geometry)
