"""MockDFS invariant tests (Task-022, GUI_ROADMAP § 6.6) on micro + delivery."""

from __future__ import annotations

import pytest

from ui.service import graphs
from ui.service.mocks import MockDFS

from .helpers import micro_graph
from .invariants import assert_ss6_6

DFS = MockDFS()


@pytest.fixture(scope="module")
def delivery():
    return graphs.get_delivery_graph()


def test_micro_path_invariants() -> None:
    graph = micro_graph()
    assert_ss6_6(DFS.search, graph, "a", "d", expect_path=True)


def test_delivery_path_invariants(delivery) -> None:
    nodes = delivery.nodes
    start, goal = nodes[0].id, nodes[-1].id
    assert_ss6_6(DFS.search, delivery, start, goal, expect_path=True)


def test_reaches_goal_and_path_endpoints() -> None:
    graph = micro_graph()
    result = DFS.search(graph, "a", "d")
    assert result.path[0] == "a"
    assert result.path[-1] == "d"


def test_start_equals_goal_trivial() -> None:
    graph = micro_graph()
    result = DFS.search(graph, "a", "a")
    assert result.path == ["a"]
    assert result.visited_nodes == ["a"]
    assert result.total_distance_km == 0.0


def test_empty_path_when_unreachable() -> None:
    graph = micro_graph()
    result = DFS.search(graph, "a", "z")
    assert result.path == []
    assert result.steps  # it searched before giving up
    assert result.total_distance_km == 0.0


def test_no_self_loops() -> None:
    graph = micro_graph()
    result = DFS.search(graph, "a", "d")
    for step in result.steps:
        assert step.current_node not in step.frontier