"""Regression checks for the canonical HCMC delivery snapshot."""

from __future__ import annotations

import json
from collections import Counter

from app.config import DEFAULT_DATASET_PATH
from app.costs import CostWeights
from app.engine import RoutingEngine
from app.loader import load_dataset


PROCESSED_SOURCE_SHA256 = (
    "309798671DB1C7A29ACA7EEEA198C9E5903EAF8A71AED05F6DC47D9F690F41B1"
)
RAW_SOURCE_SHA256 = (
    "8F53BFF35B37E7B59234DEE15BB6CF14715C05460F80B0A568168A38009D60BD"
)


def _reachable(graph, start_id: str, *, reverse: bool = False) -> set[str]:
    reached = {start_id}
    pending = [start_id]
    while pending:
        current = pending.pop()
        edges = graph.incoming(current) if reverse else graph.neighbors(current)
        for edge in edges:
            neighbor = edge.source if reverse else edge.target
            if edge.traversable and neighbor not in reached:
                reached.add(neighbor)
                pending.append(neighbor)
    return reached


def test_default_hcmc_snapshot_contract_and_provenance():
    metadata, graph = load_dataset(DEFAULT_DATASET_PATH)
    raw = json.loads(DEFAULT_DATASET_PATH.read_text(encoding="utf-8"))

    assert metadata.id == "hcmc-city-centre-delivery-osm-2026"
    assert metadata.city == "Thành phố Hồ Chí Minh"
    assert metadata.version == "2.0.0"
    assert metadata.license == "ODbL-1.0"
    assert metadata.attribution == "© OpenStreetMap contributors"
    assert metadata.bbox == (10.75, 106.665, 10.8, 106.715)
    assert metadata.stats["processed_source_sha256"] == PROCESSED_SOURCE_SHA256
    assert metadata.stats["raw_source_sha256"] == RAW_SOURCE_SHA256

    assert len(raw["nodes"]) == len(graph.nodes) == 1_103
    # Source rows are already directed arcs. No two-way row may be expanded again.
    assert len(raw["edges"]) == len(graph.edges) == 2_279
    assert all(edge.get("bidirectional") is False for edge in raw["edges"])
    assert Counter(
        edge["attributes"]["source_direction"] for edge in raw["edges"]
    ) == {"one-way": 1_039, "two-way": 1_240}

    assert all(edge.traversable for edge in graph.edges.values())
    assert all(0 <= edge.risk <= 1 for edge in graph.edges.values())
    assert min(edge.risk for edge in graph.edges.values()) == 0.06
    assert max(edge.risk for edge in graph.edges.values()) == 0.66
    assert sum("geometry" in edge["attributes"] for edge in raw["edges"]) == 1_905

    for edge in graph.edges.values():
        geometry = graph.edge_coordinates(edge.id)
        source = graph.node(edge.source)
        target = graph.node(edge.target)
        assert geometry[0] == [source.lon, source.lat]
        assert geometry[-1] == [target.lon, target.lat]


def test_primary_delivery_component_is_strongly_connected():
    metadata, graph = load_dataset(DEFAULT_DATASET_PATH)
    primary_nodes = {
        node.id
        for node in graph.nodes.values()
        if node.attributes.get("routing_component") == "primary"
    }
    delivery_pois = {
        node.id for node in graph.nodes.values() if node.kind.startswith("delivery_")
    }
    primary_delivery_pois = delivery_pois & primary_nodes

    assert len(delivery_pois) == metadata.stats["delivery_pois"] == 187
    assert len(primary_delivery_pois) == metadata.stats[
        "delivery_pois_in_primary_component"
    ] == 172
    assert len(primary_nodes) == metadata.stats[
        "largest_strongly_connected_component"
    ] == 992
    assert len(delivery_pois - primary_nodes) == 15

    root = next(iter(primary_nodes))
    assert primary_nodes <= _reachable(graph, root)
    assert primary_nodes <= _reachable(graph, root, reverse=True)


def test_recommended_delivery_defaults_are_reachable_and_use_osm_geometry():
    metadata, graph = load_dataset(DEFAULT_DATASET_PATH)
    start_id = metadata.stats["recommended_start_id"]
    goal_id = metadata.stats["recommended_goal_id"]
    assert start_id == "poi_way_152994798"
    assert goal_id == "poi_way_39514795"
    assert graph.node(start_id).attributes["routing_component"] == "primary"
    assert graph.node(goal_id).attributes["routing_component"] == "primary"

    engine = RoutingEngine(metadata, graph)
    response = engine.search(
        start_id=start_id,
        goal_id=goal_id,
        algorithm="astar",
        heuristic="travel_time",
        scenario="normal",
        weights=CostWeights(),
        include_trace=False,
        max_trace_events=0,
        max_expansions=100_000,
        include_alternative=False,
    )

    assert response["found"]
    assert response["path"][0] == start_id
    assert response["path"][-1] == goal_id
    expected_count = sum(
        len(graph.edge_coordinates(edge_id)) for edge_id in response["edge_ids"]
    ) - max(0, len(response["edge_ids"]) - 1)
    assert len(response["route_geojson"]["coordinates"]) == expected_count
    assert len(response["route_geojson"]["coordinates"]) > len(response["path"])
