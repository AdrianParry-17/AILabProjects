from __future__ import annotations

from app.costs import CostCalculator, CostWeights
from app.domain import DirectedEdge
from app.traffic import TrafficModel


def test_traffic_scenarios_are_deterministic():
    edge = DirectedEdge("stable", "a", "b", 1000, 40, "Road", road_class="primary")
    first = TrafficModel().status(edge, "morning_rush")
    second = TrafficModel().status(edge, "morning_rush")
    assert first == second
    assert first.travel_time_s is not None
    assert first.travel_time_s > first.free_flow_time_s


def test_incident_closes_only_explicitly_flagged_edges():
    model = TrafficModel()
    closed = DirectedEdge(
        "closed", "a", "b", 100, 30, "Bridge",
        attributes={"close_during_incident": True},
    )
    open_edge = DirectedEdge("open", "a", "b", 100, 30, "Road")
    assert model.status(closed, "incident").closed
    assert not model.status(open_edge, "incident").closed


def test_cost_breakdown_sums_components(small_graph):
    calculator = CostCalculator(small_graph, TrafficModel(), "heavy_rain", CostWeights())
    breakdown = calculator.aggregate(["sb", "bc", "cg"])
    assert breakdown["distance_m"] == 120
    assert breakdown["traffic_delay_s"] > 0
    assert breakdown["total_cost"] == sum(breakdown["components"].values())
    assert sum(breakdown["weights"].values()) == 1

