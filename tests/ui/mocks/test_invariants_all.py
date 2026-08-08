"""Finalized § 6.6 invariant suite (Task-028): every mock x every graph kind.

Runs the GUI_ROADMAP.md § 6.6 invariants for all four mock providers on the
micro graph and the delivery graph, plus the edge cases the per-mock files
spot-check: unreachable goals (micro ``a -> z``) and the § 6.5 trivial
``start == goal`` run on the delivery graph.
"""

from __future__ import annotations

import pytest

from ui.service import graphs
from ui.service.mocks import MockAstar, MockDFS, MockGreedy, MockProvider, MockUCS

from .helpers import micro_graph
from .invariants import assert_ss6_6

PROVIDERS: dict[str, type[MockProvider]] = {
    "dfs": MockDFS,
    "ucs": MockUCS,
    "greedy": MockGreedy,
    "astar": MockAstar,
}


@pytest.fixture(scope="module")
def delivery():
    return graphs.get_delivery_graph()


@pytest.mark.parametrize("name", sorted(PROVIDERS))
def test_micro_invariants(name: str) -> None:
    assert_ss6_6(PROVIDERS[name]().search, micro_graph(), "a", "d", expect_path=True)


@pytest.mark.parametrize("name", sorted(PROVIDERS))
def test_delivery_invariants(name: str, delivery) -> None:
    start, goal = delivery.nodes[0].id, delivery.nodes[-1].id
    assert_ss6_6(PROVIDERS[name]().search, delivery, start, goal, expect_path=True)


@pytest.mark.parametrize("name", sorted(PROVIDERS))
def test_micro_unreachable_invariants(name: str) -> None:
    """``z`` has only an inbound edge, so ``a -> z`` must return path == []."""
    assert_ss6_6(
        PROVIDERS[name]().search, micro_graph(), "a", "z", expect_path=False
    )


@pytest.mark.parametrize("name", sorted(PROVIDERS))
def test_delivery_start_equals_goal_trivial(name: str, delivery) -> None:
    """§ 6.5 on the delivery graph: trivial path, zero metrics."""
    start = delivery.nodes[0].id
    result = PROVIDERS[name]().search(delivery, start, start, enable_logging=True)
    assert result.path == [start]
    assert result.total_distance_km == 0.0
    assert result.total_time_min == 0.0
    assert result.total_cost == 0.0
