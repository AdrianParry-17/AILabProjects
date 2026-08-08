"""MockUCS invariant tests (Task-023, GUI_ROADMAP § 6.6) + cost optimality.

The micro graph has equal edge costs, so UCS finds the fewest-hops path there.
A dedicated cost graph verifies UCS picks the minimum-total-cost path even when
it is NOT the fewest hops.
"""

from __future__ import annotations

from types import SimpleNamespace

import pytest

from ui.service import graphs
from ui.service.mocks import MockUCS

from .helpers import edge, micro_graph, node
from .invariants import assert_ss6_6

UCS = MockUCS()


@pytest.fixture(scope="module")
def delivery():
    return graphs.get_delivery_graph()


def test_micro_path_invariants() -> None:
    assert_ss6_6(UCS.search, micro_graph(), "a", "d", expect_path=True)


def test_delivery_path_invariants(delivery) -> None:
    start, goal = delivery.nodes[0].id, delivery.nodes[-1].id
    assert_ss6_6(UCS.search, delivery, start, goal, expect_path=True)


def test_start_equals_goal_trivial() -> None:
    """§ 6.5: start == goal → trivial path, zero metrics, visited == [start]."""
    graph = micro_graph()
    result = UCS.search(graph, "a", "a")
    assert result.path == ["a"]
    assert result.visited_nodes == ["a"]
    assert result.total_distance_km == 0.0
    assert result.total_time_min == 0.0
    assert result.total_cost == 0.0


def test_cost_optimal_where_cheapest_is_not_fewest_hops() -> None:
    """UCS chooses the more-hops but cheaper path over a single expensive hop."""
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
            edge("a", "b", distance_km=100.0),  # expensive straight hop
            edge("b", "d", distance_km=1.0),
            edge("a", "e", distance_km=1.0),
            edge("e", "f", distance_km=1.0),
            edge("f", "d", distance_km=1.0),
        ],
    )
    result = UCS.search(graph, "a", "d")
    # Fewest hops is a-b-d (2, cost ~101); cheapest is a-e-f-d (3 hops, cost ~3).
    assert result.path == ["a", "e", "f", "d"]


def test_frontier_is_deterministic() -> None:
    """The frontier at each step is reproducible across identical runs."""
    graph = micro_graph()
    result = UCS.search(graph, "a", "d")
    again = UCS.search(graph, "a", "d")
    assert [s.frontier for s in result.steps] == [s.frontier for s in again.steps]