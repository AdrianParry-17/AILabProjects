"""Path metric helpers used by every algorithm (algorithms/metrics.py)."""

from __future__ import annotations

import pytest

from algorithms.metrics import (
    build_edge_lookup,
    path_metrics,
    path_total_cost,
)
from data.models import Edge, GraphData, Node


def _edge(start: str, end: str, /, **kw: float) -> Edge:
    return Edge(
        start=start,
        end=end,
        distance_km=kw.get("distance_km", 1.0),
        time_min=kw.get("time_min", 1.0),
        congestion=kw.get("congestion", 1.0),
        risk=kw.get("risk", 0.0),
        direction="one-way",
    )


NODES = [
    Node(id="A", name="A", latitude=10.0, longitude=106.0),
    Node(id="B", name="B", latitude=10.0, longitude=106.0),
    Node(id="C", name="C", latitude=10.0, longitude=106.0),
]
EDGES = [_edge("A", "B", distance_km=1.0, time_min=2.0), _edge("B", "C", distance_km=3.0, time_min=4.0)]
GRAPH = GraphData(nodes=NODES, edges=EDGES)
LOOKUP = build_edge_lookup(GRAPH)


def test_build_edge_lookup_indexes_by_id_pair() -> None:
    assert set(LOOKUP) == {("A", "B"), ("B", "C")}
    assert LOOKUP[("A", "B")].time_min == 2.0


def test_path_metrics_sums_distance_and_time() -> None:
    distance, time_min = path_metrics(GRAPH, ["A", "B", "C"], LOOKUP)
    assert distance == 1.0 + 3.0
    assert time_min == 2.0 + 4.0


def test_path_metrics_returns_zero_for_short_path() -> None:
    assert path_metrics(GRAPH, ["A"], LOOKUP) == (0.0, 0.0)


def test_path_metrics_raises_on_missing_edge() -> None:
    with pytest.raises(ValueError):
        path_metrics(GRAPH, ["A", "C"], LOOKUP)


def test_path_total_cost_sums_cost_fn() -> None:
    total = path_total_cost(GRAPH, ["A", "B", "C"], LOOKUP, cost_fn=lambda e: e.distance_km)
    assert total == 1.0 + 3.0


def test_path_total_cost_raises_on_missing_edge() -> None:
    with pytest.raises(ValueError):
        path_total_cost(GRAPH, ["A", "C"], LOOKUP, cost_fn=lambda e: e.distance_km)