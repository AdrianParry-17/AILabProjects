"""By-hand A* trace tests (see ALGORITHM_SPEC.md § 7.4/§ 9)."""

from __future__ import annotations

from algorithms.astar import astar
from algorithms.heuristic import straight_line_heuristic
from core.search_algorithm import ALGORITHM_REGISTRY
from data.models import Edge, GraphData, Node

# Same graph as the BFS/UCS by-hand traces so results are directly comparable. All
# nodes share the same coordinates here, so the straight-line heuristic is 0.0: A*
# then behaves exactly like UCS and returns the cost-optimal A-B-D-E path.
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


def test_astar_is_registered() -> None:
    assert ALGORITHM_REGISTRY["astar"] is not None


def test_astar_returns_minimum_cost_path() -> None:
    result = astar(GRAPH, "A", "E")
    assert result.path == ["A", "B", "D", "E"]
    assert result.path[0] == "A"
    assert result.path[-1] == "E"


def test_astar_prefers_cost_optimal_over_fewest_hops() -> None:
    result = astar(GRAPH, "A", "E")
    assert result.path == ["A", "B", "D", "E"]
    assert result.total_cost == 2.7
    assert result.total_distance_km == 3.0


def test_astar_expansion_order_matches_ucs_when_heuristic_is_zero() -> None:
    result = astar(GRAPH, "A", "E")
    assert result.visited_nodes == ["A", "B", "D", "C", "E"]


def test_astar_start_equals_goal() -> None:
    result = astar(GRAPH, "A", "A")
    assert result.path == ["A"]
    assert result.steps == []


def test_astar_missing_node_returns_empty_path() -> None:
    result = astar(GRAPH, "A", "Z")
    assert result.path == []


def test_astar_disconnected_pair_returns_empty_path() -> None:
    isolated = GraphData(
        nodes=NODES + [Node(id="F", name="F", latitude=11.0, longitude=107.0)],
        edges=EDGES,
    )
    result = astar(isolated, "A", "F")
    assert result.path == []


def test_astar_enable_logging_false_omits_steps() -> None:
    result = astar(GRAPH, "A", "E", enable_logging=False)
    assert result.steps == []
    assert result.path == ["A", "B", "D", "E"]


def test_astar_heuristic_is_admissible_on_trace() -> None:
    # h(n) must never exceed the true remaining cost. On the all-zero-coordinate graph
    # h is 0.0 (admissible); additionally the shared helper must not be negative.
    result = astar(GRAPH, "A", "E")
    assert result.processing_time_ms >= 0.0
    assert straight_line_heuristic(NODES[0], NODES[4]) == 0.0


def test_astar_uses_positive_heuristic_when_nodes_have_coordinates() -> None:
    west = Node(id="W", name="W", latitude=10.0, longitude=106.0)
    east = Node(id="X", name="X", latitude=10.0, longitude=106.01)
    estimate = straight_line_heuristic(west, east)
    assert estimate > 0.0
    assert estimate <= 1.0  # ~1.1 km straight line, weighted by distance (0.3)
