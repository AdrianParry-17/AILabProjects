"""Core framework tests: registry, run_algorithm, history, metrics."""

from __future__ import annotations

import pytest

from algorithms.bfs import BFSAlgorithm
from core.search_algorithm import ALGORITHM_REGISTRY, run_algorithm
from core.search_history import SearchHistory, SearchRun
from core.search_metrics import SearchMetrics
from data.models import Edge, GraphData, Node

# Reuse the by-hand BFS graph (A->B, A->C, B->D, C->E, D->E).
NODES = [
    Node(id="A", name="A", latitude=10.0, longitude=106.0),
    Node(id="B", name="B", latitude=10.0, longitude=106.0),
    Node(id="C", name="C", latitude=10.0, longitude=106.0),
    Node(id="D", name="D", latitude=10.0, longitude=106.0),
    Node(id="E", name="E", latitude=10.0, longitude=106.0),
]
EDGES = [
    Edge(start="A", end="B", distance_km=1.0, time_min=1.0, congestion=1.0, risk=0.0, direction="one-way"),
    Edge(start="A", end="C", distance_km=3.0, time_min=3.0, congestion=1.0, risk=0.0, direction="one-way"),
    Edge(start="B", end="D", distance_km=1.0, time_min=1.0, congestion=1.0, risk=0.0, direction="one-way"),
    Edge(start="C", end="E", distance_km=2.0, time_min=2.0, congestion=1.0, risk=0.0, direction="one-way"),
    Edge(start="D", end="E", distance_km=1.0, time_min=1.0, congestion=1.0, risk=0.0, direction="one-way"),
]
GRAPH = GraphData(nodes=NODES, edges=EDGES)


def test_bfs_is_registered_in_framework_registry() -> None:
    assert "bfs" in ALGORITHM_REGISTRY
    assert ALGORITHM_REGISTRY["bfs"] is BFSAlgorithm


def test_run_algorithm_dispatches_through_registry() -> None:
    result = run_algorithm("bfs", GRAPH, "A", "E")
    assert result.path == ["A", "C", "E"]
    assert result.path[-1] == "E"


def test_run_algorithm_unknown_name_raises_key_error() -> None:
    with pytest.raises(KeyError, match="available"):
        run_algorithm("not-an-algorithm", GRAPH, "A", "E")


def test_search_history_records_runs_bounded() -> None:
    history = SearchHistory(capacity=2)
    for goal in ("E", "D"):
        result = run_algorithm("bfs", GRAPH, "A", goal)
        history.record(SearchRun(algorithm="bfs", start="A", goal=goal, result=result))
    assert len(history) == 2
    history.record(
        SearchRun(algorithm="bfs", start="A", goal="B", result=run_algorithm("bfs", GRAPH, "A", "B"))
    )
    assert len(history) == 2
    assert history.recent()[-1].goal == "B"


def test_search_metrics_summary_from_result() -> None:
    result = run_algorithm("bfs", GRAPH, "A", "E")
    metrics = SearchMetrics.from_result(result)
    assert metrics.hops == 2
    assert metrics.nodes_visited == 5
    assert metrics.distance_km == 5.0
