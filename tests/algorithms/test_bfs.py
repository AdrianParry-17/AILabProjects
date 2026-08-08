"""By-hand BFS trace tests (see docs/BFS_SPEC.md § 10)."""

from __future__ import annotations

from algorithms.bfs import bfs
from data.models import Edge, GraphData, Node

# Hand-built graph:
#   A -> B, A -> C, B -> D, C -> E, D -> E
# BFS from A to E expands A, B, C, D, E in that order and returns path A-C-E.
NODES = [
    Node(id="A", name="A", latitude=10.0, longitude=106.0),
    Node(id="B", name="B", latitude=10.0, longitude=106.0),
    Node(id="C", name="C", latitude=10.0, longitude=106.0),
    Node(id="D", name="D", latitude=10.0, longitude=106.0),
    Node(id="E", name="E", latitude=10.0, longitude=106.0),
]
EDGES = [
    Edge(
        start="A",
        end="B",
        distance_km=1.0,
        time_min=1.0,
        congestion=1.0,
        risk=0.0,
        direction="one-way",
    ),
    Edge(
        start="A",
        end="C",
        distance_km=3.0,
        time_min=3.0,
        congestion=1.0,
        risk=0.0,
        direction="one-way",
    ),
    Edge(
        start="B",
        end="D",
        distance_km=1.0,
        time_min=1.0,
        congestion=1.0,
        risk=0.0,
        direction="one-way",
    ),
    Edge(
        start="C",
        end="E",
        distance_km=2.0,
        time_min=2.0,
        congestion=1.0,
        risk=0.0,
        direction="one-way",
    ),
    Edge(
        start="D",
        end="E",
        distance_km=1.0,
        time_min=1.0,
        congestion=1.0,
        risk=0.0,
        direction="one-way",
    ),
]
GRAPH = GraphData(nodes=NODES, edges=EDGES)


def test_bfs_returns_fewest_hops_path() -> None:
    result = bfs(GRAPH, "A", "E")
    assert result.path == ["A", "C", "E"]
    assert result.path[0] == "A"
    assert result.path[-1] == "E"


def test_bfs_expansion_order_matches_manual_trace() -> None:
    result = bfs(GRAPH, "A", "E")
    assert result.visited_nodes == ["A", "B", "C", "D", "E"]
    assert [step.current_node for step in result.steps] == ["A", "B", "C", "D", "E"]
    assert len(result.steps) == len(result.visited_nodes)


def test_bfs_frontier_matches_manual_trace() -> None:
    result = bfs(GRAPH, "A", "E")
    assert result.steps[0].frontier == ["B", "C"]
    assert result.steps[1].frontier == ["C", "D"]
    assert result.steps[2].frontier == ["D", "E"]
    assert result.steps[3].frontier == ["E"]


def test_bfs_is_not_cost_optimal() -> None:
    # A-E via C: hops=2 but distance=5.0. A-B-D-E: hops=3 but distance=3.0.
    # BFS returns A-C-E (fewest hops), not the shortest distance route.
    result = bfs(GRAPH, "A", "E")
    assert result.path == ["A", "C", "E"]
    assert result.total_distance_km == 5.0


def test_bfs_start_equals_goal() -> None:
    result = bfs(GRAPH, "A", "A")
    assert result.path == ["A"]
    assert result.steps == []


def test_bfs_missing_node_returns_empty_path() -> None:
    result = bfs(GRAPH, "A", "Z")
    assert result.path == []


def test_bfs_disconnected_pair_returns_empty_path() -> None:
    isolated = GraphData(
        nodes=NODES + [Node(id="F", name="F", latitude=11.0, longitude=107.0)],
        edges=EDGES,
    )
    result = bfs(isolated, "A", "F")
    assert result.path == []


def test_bfs_enable_logging_false_omits_steps() -> None:
    result = bfs(GRAPH, "A", "E", enable_logging=False)
    assert result.steps == []
    assert result.path == ["A", "C", "E"]
    assert result.visited_nodes == ["A", "B", "C", "D", "E"]


def test_bfs_enable_logging_false_still_times_processing() -> None:
    result = bfs(GRAPH, "A", "E", enable_logging=False)
    assert result.processing_time_ms >= 0.0
