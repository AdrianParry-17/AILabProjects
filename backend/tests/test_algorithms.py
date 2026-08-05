from __future__ import annotations

import pytest

from app.algorithms import SearchOptions, run_algorithm
from app.heuristics import HeuristicRegistry


ALL_ALGORITHMS = [
    "bfs",
    "dfs",
    "ucs",
    "dijkstra",
    "astar",
    "greedy_best_first",
    "bidirectional_dijkstra",
    "ida_star",
]


def assert_valid_path(graph, result) -> None:
    assert result.found
    assert result.path[0] == "s"
    assert result.path[-1] == "g"
    assert len(result.edge_ids) == len(result.path) - 1
    for source, target, edge_id in zip(result.path, result.path[1:], result.edge_ids):
        edge = graph.edge(edge_id)
        assert (edge.source, edge.target) == (source, target)


@pytest.mark.parametrize("algorithm", ALL_ALGORITHMS)
def test_every_algorithm_returns_a_valid_route(small_graph, distance_calculator, algorithm):
    result = run_algorithm(
        small_graph,
        distance_calculator,
        HeuristicRegistry(),
        algorithm,
        "zero",
        "s",
        "g",
        SearchOptions(include_trace=True, max_trace_events=500),
    )
    assert_valid_path(small_graph, result)
    assert result.metrics["expanded_nodes"] >= 1
    assert result.trace_events[0]["event"] == "start"
    expected_trace_fields = {
        "step", "event", "node_id", "parent_id", "edge_id", "direction",
        "frontier_size", "explored_count", "g_cost", "h_cost", "f_cost",
        "depth", "message",
    }
    assert set(result.trace_events[0]) == expected_trace_fields


@pytest.mark.parametrize("algorithm", ["ucs", "dijkstra", "astar", "bidirectional_dijkstra", "ida_star"])
def test_optimal_weighted_algorithms_choose_lower_cost_path(
    small_graph, distance_calculator, algorithm
):
    result = run_algorithm(
        small_graph,
        distance_calculator,
        HeuristicRegistry(),
        algorithm,
        "zero",
        "s",
        "g",
    )
    assert result.path == ["s", "b", "c", "g"]
    assert result.total_cost == pytest.approx(0.12)


def test_bfs_optimizes_hops_not_weighted_cost(small_graph, distance_calculator):
    result = run_algorithm(
        small_graph, distance_calculator, HeuristicRegistry(), "bfs", "zero", "s", "g"
    )
    assert result.path == ["s", "a", "g"]
    assert result.total_cost == pytest.approx(0.2)


def test_expansion_limit_is_reported(small_graph, distance_calculator):
    result = run_algorithm(
        small_graph,
        distance_calculator,
        HeuristicRegistry(),
        "bfs",
        "zero",
        "s",
        "g",
        SearchOptions(max_expansions=1),
    )
    assert not result.found
    assert result.status == "limit_reached"


def test_start_equal_goal_has_zero_cost(small_graph, distance_calculator):
    result = run_algorithm(
        small_graph, distance_calculator, HeuristicRegistry(), "astar", "travel_time", "s", "s"
    )
    assert result.path == ["s"]
    assert result.edge_ids == []
    assert result.total_cost == 0

