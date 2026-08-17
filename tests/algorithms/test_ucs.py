"""By-hand UCS trace tests (see ALGORITHM_SPEC.md § 7.3/§ 9)."""

from __future__ import annotations

from algorithms.ucs import ucs
from core.search_algorithm import ALGORITHM_REGISTRY
from data.models import Edge, GraphData, Node

# Same graph as the BFS by-hand trace so the two algorithms are directly comparable:
#   A -> B, A -> C, B -> D, C -> E, D -> E
# UCS from A to E must prefer A-B-D-E (weighted cost 2.7) over BFS's A-C-E (3.9).
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


def test_ucs_is_registered() -> None:
    assert ALGORITHM_REGISTRY["ucs"] is not None


def test_ucs_returns_minimum_cost_path() -> None:
    result = ucs(GRAPH, "A", "E")
    assert result.path == ["A", "B", "D", "E"]
    assert result.path[0] == "A"
    assert result.path[-1] == "E"


def test_ucs_prefers_cost_optimal_over_fewest_hops() -> None:
    # BFS returns A-C-E (2 hops, distance 5.0, cost 3.9); UCS must pick the cheaper
    # A-B-D-E (3 hops, distance 3.0, cost 2.7) because it honours weighted edge costs.
    result = ucs(GRAPH, "A", "E")
    assert result.path == ["A", "B", "D", "E"]
    assert result.total_cost == 2.7
    assert result.total_distance_km == 3.0


def test_ucs_expansion_order_matches_manual_trace() -> None:
    result = ucs(GRAPH, "A", "E")
    assert result.visited_nodes == ["A", "B", "D", "C", "E"]
    assert [step.current_node for step in result.steps] == ["A", "B", "D", "C", "E"]


def test_ucs_frontier_matches_manual_trace() -> None:
    result = ucs(GRAPH, "A", "E")
    assert result.steps[0].frontier == ["B", "C"]
    assert result.steps[1].frontier == ["D", "C"]
    assert result.steps[2].frontier == ["C", "E"]
    assert result.steps[3].frontier == ["E"]


def test_ucs_start_equals_goal() -> None:
    result = ucs(GRAPH, "A", "A")
    assert result.path == ["A"]
    assert result.steps == []


def test_ucs_missing_node_returns_empty_path() -> None:
    result = ucs(GRAPH, "A", "Z")
    assert result.path == []


def test_ucs_disconnected_pair_returns_empty_path() -> None:
    isolated = GraphData(
        nodes=NODES + [Node(id="F", name="F", latitude=11.0, longitude=107.0)],
        edges=EDGES,
    )
    result = ucs(isolated, "A", "F")
    assert result.path == []


def test_ucs_enable_logging_false_omits_steps() -> None:
    result = ucs(GRAPH, "A", "E", enable_logging=False)
    assert result.steps == []
    assert result.path == ["A", "B", "D", "E"]


def test_ucs_is_deterministic() -> None:
    first = ucs(GRAPH, "A", "E")
    second = ucs(GRAPH, "A", "E")
    assert first.path == second.path
    assert first.visited_nodes == second.visited_nodes
    assert [step.frontier for step in first.steps] == [step.frontier for step in second.steps]
