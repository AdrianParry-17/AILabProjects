"""MockGreedy + MockAstar invariant tests (Task-024, GUI_ROADMAP § 6.6).

Covers: § 6.6 invariants on micro + delivery, greedy reaching the goal,
A* cost-optimality on the micro graph, and deterministic tie-breaking.
"""

from __future__ import annotations

from types import SimpleNamespace

import pytest

from ui.service import graphs
from ui.service.mocks import MockAstar, MockGreedy, MockUCS

from .helpers import edge, micro_graph, node
from .invariants import assert_ss6_6

GREEDY = MockGreedy()
ASTAR = MockAstar()
UCS = MockUCS()


@pytest.fixture(scope="module")
def delivery():
    return graphs.get_delivery_graph()


# -- § 6.6 invariants -----------------------------------------------------


def test_greedy_micro_invariants() -> None:
    assert_ss6_6(GREEDY.search, micro_graph(), "a", "d", expect_path=True)


def test_greedy_delivery_invariants(delivery) -> None:
    start, goal = delivery.nodes[0].id, delivery.nodes[-1].id
    assert_ss6_6(GREEDY.search, delivery, start, goal, expect_path=True)


def test_astar_micro_invariants() -> None:
    assert_ss6_6(ASTAR.search, micro_graph(), "a", "d", expect_path=True)


def test_astar_delivery_invariants(delivery) -> None:
    start, goal = delivery.nodes[0].id, delivery.nodes[-1].id
    assert_ss6_6(ASTAR.search, delivery, start, goal, expect_path=True)


# -- greedy reaches the goal ----------------------------------------------


def test_greedy_reaches_goal_on_micro() -> None:
    result = GREEDY.search(micro_graph(), "a", "d")
    assert result.path
    assert result.path[0] == "a"
    assert result.path[-1] == "d"


def test_greedy_reaches_goal_on_delivery(delivery) -> None:
    start, goal = delivery.nodes[0].id, delivery.nodes[-1].id
    result = GREEDY.search(delivery, start, goal)
    assert result.path
    assert result.path[-1] == goal


# -- A* optimality on micro -----------------------------------------------


def test_astar_is_cost_optimal_on_micro() -> None:
    """A* cost equals UCS cost on the micro graph (admissible heuristic)."""
    graph = micro_graph()
    astar = ASTAR.search(graph, "a", "d")
    ucs = UCS.search(graph, "a", "d")
    assert astar.total_cost == ucs.total_cost
    assert astar.total_distance_km == ucs.total_distance_km


def test_astar_optimal_on_cheap_vs_few_hops() -> None:
    """A* picks the cheaper (longer) path, same as UCS, on a cost graph."""
    graph = SimpleNamespace(
        nodes=[
            node("a", 10.0, 106.0),
            node("b", 10.0, 106.1),
            node("c", 10.0, 106.2),
            node("d", 10.0, 106.3),
            node("e", 10.0, 106.15),
            node("f", 10.1, 106.2),
        ],
        edges=[
            edge("a", "b", distance_km=100.0),
            edge("b", "d", distance_km=1.0),
            edge("a", "e", distance_km=1.0),
            edge("e", "f", distance_km=1.0),
            edge("f", "d", distance_km=1.0),
        ],
    )
    astar = ASTAR.search(graph, "a", "d")
    ucs = UCS.search(graph, "a", "d")
    assert astar.path == ucs.path == ["a", "e", "f", "d"]


# -- deterministic tie-break ----------------------------------------------


def test_greedy_is_deterministic() -> None:
    graph = micro_graph()
    first = GREEDY.search(graph, "a", "d")
    second = GREEDY.search(graph, "a", "d")
    assert first.path == second.path
    assert [s.frontier for s in first.steps] == [s.frontier for s in second.steps]


def test_astar_is_deterministic() -> None:
    graph = micro_graph()
    first = ASTAR.search(graph, "a", "d")
    second = ASTAR.search(graph, "a", "d")
    assert first.path == second.path
    assert [s.frontier for s in first.steps] == [s.frontier for s in second.steps]


# -- § 6.2 frontier uniqueness (regression) --------------------------------


def test_astar_frontier_has_unique_node_ids(delivery) -> None:
    """§ 6.2 regression: re-seen nodes never re-enter the frontier.

    A* may relax a node after it was already pushed (lazy heap deletion); the
    logged frontier must still list every node id at most once. Reproduces a
    bug that duplicated ids (e.g. ``poi_way_826183551 -> poi_way_1469357721``).
    """
    ids = [n.id for n in delivery.nodes]
    for start in ids:
        for goal in ids:
            if start == goal:
                continue
            result = ASTAR.search(delivery, start, goal, enable_logging=True)
            for step in result.steps:
                assert len(set(step.frontier)) == len(step.frontier)


# -- trivial cases --------------------------------------------------------


def test_greedy_start_equals_goal() -> None:
    result = GREEDY.search(micro_graph(), "a", "a")
    assert result.path == ["a"]
    assert result.total_distance_km == 0.0


def test_astar_start_equals_goal() -> None:
    result = ASTAR.search(micro_graph(), "a", "a")
    assert result.path == ["a"]
    assert result.total_distance_km == 0.0