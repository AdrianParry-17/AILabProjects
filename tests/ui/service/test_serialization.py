"""SearchResult serialization + metrics round-trip (IMPLEMENTATION_PLAN § Task 2.1a).

Proves a real BFS `SearchResult` on the delivery graph serializes to the § 11
`POST /search` response keys and that the derived metrics match the result.
"""

from __future__ import annotations

from algorithms import bfs
from core.search_result import SearchResult
from ui.service import serialization
from ui.service.graphs import get_delivery_graph, get_graph_payload

_GRAPH = get_graph_payload()
_NODES = _GRAPH["graph"]["nodes"]
_START = _NODES[0]["id"]
_GOAL = _NODES[-1]["id"]


def test_search_result_round_trips_contract_keys() -> None:
    delivery_graph = get_delivery_graph()
    result = bfs(delivery_graph, _START, _GOAL)

    body = serialization.search_result_to_contract(result)

    assert set(body) == {
        "path",
        "visited_nodes",
        "steps",
        "total_distance_km",
        "total_time_min",
        "total_cost",
        "processing_time_ms",
        "explanation",
    }
    assert body["path"] == result.path
    assert body["visited_nodes"] == result.visited_nodes
    assert body["total_distance_km"] == result.total_distance_km
    assert body["processing_time_ms"] == result.processing_time_ms


def test_bfs_finds_a_real_path_on_delivery_graph() -> None:
    result = bfs(get_delivery_graph(), _START, _GOAL)
    assert result.path
    assert result.path[0] == _START
    assert result.path[-1] == _GOAL


def test_metrics_derived_from_result() -> None:
    result = bfs(get_delivery_graph(), _START, _GOAL)
    metrics = serialization.metrics_from_result(result)

    assert set(metrics) == {
        "hops",
        "nodes_visited",
        "distance_km",
        "time_min",
        "cost",
        "processing_time_ms",
    }
    assert metrics["hops"] == max(0, len(result.path) - 1)
    assert metrics["nodes_visited"] == len(result.visited_nodes)
    assert metrics["distance_km"] == result.total_distance_km
    assert metrics["time_min"] == result.total_time_min
    assert metrics["cost"] == result.total_cost
    assert metrics["processing_time_ms"] == result.processing_time_ms


def test_empty_result_serializes_with_zero_hops() -> None:
    result = SearchResult(
        path=[],
        visited_nodes=[],
        steps=[],
        total_distance_km=0.0,
        total_time_min=0.0,
        total_cost=0.0,
        processing_time_ms=0.0,
        explanation="no route",
    )
    metrics = serialization.metrics_from_result(result)
    assert metrics["hops"] == 0
    assert metrics["nodes_visited"] == 0
