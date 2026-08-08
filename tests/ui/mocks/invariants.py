"""Shared § 6.6 invariant assertions for every mock algorithm.

These helpers run against both the micro graph and the delivery graph so the
mocks can be proven to satisfy the GUI_ROADMAP.md § 6.6 contract:
  - path[0] == start and path[-1] == goal (or path == [] when unreachable);
  - steps[i].current_node == visited_nodes[i], equal lengths;
  - last frontier is empty at the final step;
  - every frontier has unique node ids (§ 6.2: re-seen nodes never re-enter);
  - metrics back-calculate from the path (path_metrics / path_total_cost);
  - enable_logging=False => steps == [], path/metrics unchanged;
  - all numeric fields are >= 0 (never None).
"""

from __future__ import annotations

from collections.abc import Callable

from algorithms.heuristic import edge_cost
from algorithms.metrics import build_edge_lookup, path_metrics, path_total_cost
from core.search_result import SearchResult, SearchStep


def assert_ss6_6(
    run: Callable[..., SearchResult],
    graph,
    start: str,
    goal: str,
    *,
    expect_path: bool = True,
) -> None:
    """Run a mock and assert every § 6.6 invariant.

    Args:
        run: a callable ``(graph, start, goal, enable_logging=...) -> SearchResult``.
        graph: the micro or delivery graph.
        start / goal: endpoints for the run.
        expect_path: whether a path is expected (searchable pair).
    """
    on = run(graph, start, goal, enable_logging=True)
    _assert_on(on, graph, start, goal, expect_path)

    off = run(graph, start, goal, enable_logging=False)
    assert_logging_off(off, on)

    # Determinism: the same inputs give the same result every time.
    again = run(graph, start, goal, enable_logging=True)
    assert again == on


def _assert_on(
    result: SearchResult,
    graph,
    start: str,
    goal: str,
    expect_path: bool,
) -> None:
    assert isinstance(result, SearchResult)
    assert isinstance(result.steps, list)
    assert all(isinstance(s, SearchStep) for s in result.steps)

    # All numeric fields are >= 0 numbers (never None).
    for value in (
        result.total_distance_km,
        result.total_time_min,
        result.total_cost,
        result.processing_time_ms,
    ):
        assert isinstance(value, (int, float))
        assert value >= 0

    # steps[i].current_node == visited_nodes[i], equal lengths.
    assert len(result.steps) == len(result.visited_nodes)
    for step, current in zip(result.steps, result.visited_nodes):
        assert step.current_node == current

    # No self-loops within a frontier frame.
    for step in result.steps:
        assert step.current_node not in step.frontier

    # § 6.2: re-seen nodes never re-enter the frontier — ids are unique.
    for step in result.steps:
        assert len(set(step.frontier)) == len(step.frontier)

    # path[0] == start and path[-1] == goal (or empty when unreachable).
    if result.path:
        assert result.path[0] == start
        assert result.path[-1] == goal
    else:
        assert not expect_path

    # Last frontier is empty at the final step.
    if result.steps:
        assert result.steps[-1].frontier == []

    # Metrics back-calculate from the path.
    if result.path:
        lookup = build_edge_lookup(graph)
        distance, time_min = path_metrics(graph, result.path, lookup)
        cost = path_total_cost(graph, result.path, lookup, cost_fn=edge_cost)
        assert result.total_distance_km == round(distance, 3)
        assert result.total_time_min == round(time_min, 3)
        assert result.total_cost == round(cost, 3)


def assert_logging_off(off: SearchResult, on: SearchResult) -> None:
    """enable_logging=False -> steps==[] and path/metrics unchanged."""
    assert off.steps == []
    assert off.path == on.path
    assert off.total_distance_km == on.total_distance_km
    assert off.total_time_min == on.total_time_min
    assert off.total_cost == on.total_cost