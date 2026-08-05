from __future__ import annotations

import pytest

from app.costs import CostCalculator, CostWeights
from app.domain import DirectedEdge, GraphNode, RoadGraph
from app.traffic import TrafficModel


@pytest.fixture
def small_graph() -> RoadGraph:
    nodes = [
        GraphNode("s", "Courier hub", "delivery_depot", 10.7700, 106.6800),
        GraphNode("a", "Junction A", "intersection", 10.7704, 106.6804),
        GraphNode("b", "Junction B", "intersection", 10.7700, 106.6803),
        GraphNode("c", "Junction C", "intersection", 10.7700, 106.6806),
        GraphNode("g", "Delivery stop", "delivery_market", 10.7700, 106.6809),
    ]
    edges = [
        # BFS sees A first and takes two hops (cost .2); weighted search takes B/C (cost .12).
        DirectedEdge("sa", "s", "a", 100, 30, "SA", risk=0),
        DirectedEdge("ag", "a", "g", 100, 30, "AG", risk=0),
        DirectedEdge("sb", "s", "b", 40, 30, "SB", risk=0),
        DirectedEdge("bc", "b", "c", 40, 30, "BC", risk=0),
        DirectedEdge("cg", "c", "g", 40, 30, "CG", risk=0),
        DirectedEdge("as", "a", "s", 100, 30, "AS", risk=0),
        DirectedEdge("ga", "g", "a", 100, 30, "GA", risk=0),
        DirectedEdge("bs", "b", "s", 40, 30, "BS", risk=0),
        DirectedEdge("cb", "c", "b", 40, 30, "CB", risk=0),
        DirectedEdge("gc", "g", "c", 40, 30, "GC", risk=0),
    ]
    return RoadGraph(nodes, edges)


@pytest.fixture
def distance_calculator(small_graph: RoadGraph) -> CostCalculator:
    return CostCalculator(
        small_graph,
        TrafficModel(),
        "normal",
        CostWeights(distance=1, travel_time=0, traffic_delay=0, risk=0),
    )
