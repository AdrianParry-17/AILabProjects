"""Weighted delivery-route cost model and transparent cost breakdowns."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from math import inf, isfinite
from typing import Any, Iterable

from .domain import DirectedEdge, RoadGraph
from .traffic import TrafficModel, TrafficStatus


@dataclass(frozen=True, slots=True)
class CostWeights:
    distance: float = 0.25
    travel_time: float = 0.50
    traffic_delay: float = 0.20
    risk: float = 0.05

    def __post_init__(self) -> None:
        values = (self.distance, self.travel_time, self.traffic_delay, self.risk)
        if any(not isfinite(value) or value < 0 for value in values):
            raise ValueError("Cost weights must be finite and non-negative")
        if sum(values) <= 0:
            raise ValueError("At least one cost weight must be positive")

    def normalized(self) -> "CostWeights":
        total = self.distance + self.travel_time + self.traffic_delay + self.risk
        return CostWeights(
            distance=self.distance / total,
            travel_time=self.travel_time / total,
            traffic_delay=self.traffic_delay / total,
            risk=self.risk / total,
        )

    def as_dict(self) -> dict[str, float]:
        return asdict(self)


@dataclass(frozen=True, slots=True)
class EdgeCostBreakdown:
    edge_id: str
    distance_m: float
    free_flow_time_s: float
    travel_time_s: float
    traffic_delay_s: float
    risk_exposure: float
    components: dict[str, float]
    total_cost: float


class CostCalculator:
    """Converts unlike route properties into a documented dimensionless score.

    Units before weighting:
    - distance: kilometres
    - travel time and delay: minutes
    - risk: risk fraction multiplied by kilometres of exposure
    """

    def __init__(
        self,
        graph: RoadGraph,
        traffic: TrafficModel,
        scenario: str,
        weights: CostWeights,
    ) -> None:
        TrafficModel.validate_scenario(scenario)
        self.graph = graph
        self.traffic = traffic
        self.scenario = scenario
        self.weights = weights.normalized()
        self._breakdown_cache: dict[str, EdgeCostBreakdown | None] = {}

    def traffic_status(self, edge: DirectedEdge) -> TrafficStatus:
        return self.traffic.status(edge, self.scenario)

    def edge_breakdown(self, edge: DirectedEdge) -> EdgeCostBreakdown | None:
        if edge.id in self._breakdown_cache:
            return self._breakdown_cache[edge.id]
        status = self.traffic_status(edge)
        if status.closed or status.travel_time_s is None or status.delay_s is None:
            self._breakdown_cache[edge.id] = None
            return None

        distance_km = edge.distance_m / 1000
        travel_minutes = status.travel_time_s / 60
        delay_minutes = status.delay_s / 60
        risk_exposure = edge.risk * distance_km
        components = {
            "distance": self.weights.distance * distance_km,
            "travel_time": self.weights.travel_time * travel_minutes,
            "traffic_delay": self.weights.traffic_delay * delay_minutes,
            "risk": self.weights.risk * risk_exposure,
        }
        breakdown = EdgeCostBreakdown(
            edge_id=edge.id,
            distance_m=edge.distance_m,
            free_flow_time_s=status.free_flow_time_s,
            travel_time_s=status.travel_time_s,
            traffic_delay_s=status.delay_s,
            risk_exposure=risk_exposure,
            components=components,
            total_cost=sum(components.values()),
        )
        self._breakdown_cache[edge.id] = breakdown
        return breakdown

    def edge_cost(self, edge: DirectedEdge) -> float:
        breakdown = self.edge_breakdown(edge)
        return inf if breakdown is None else breakdown.total_cost

    def is_traversable(self, edge: DirectedEdge) -> bool:
        return edge.traversable and self.edge_breakdown(edge) is not None

    def aggregate(self, edge_ids: Iterable[str]) -> dict[str, Any]:
        totals = {
            "distance_m": 0.0,
            "free_flow_time_s": 0.0,
            "travel_time_s": 0.0,
            "traffic_delay_s": 0.0,
            "risk_exposure": 0.0,
        }
        components = {"distance": 0.0, "travel_time": 0.0, "traffic_delay": 0.0, "risk": 0.0}
        edge_count = 0
        for edge_id in edge_ids:
            edge = self.graph.edge(edge_id)
            breakdown = self.edge_breakdown(edge)
            if breakdown is None:
                raise ValueError(f"Cannot aggregate closed or inaccessible edge {edge_id!r}")
            edge_count += 1
            totals["distance_m"] += breakdown.distance_m
            totals["free_flow_time_s"] += breakdown.free_flow_time_s
            totals["travel_time_s"] += breakdown.travel_time_s
            totals["traffic_delay_s"] += breakdown.traffic_delay_s
            totals["risk_exposure"] += breakdown.risk_exposure
            for key, value in breakdown.components.items():
                components[key] += value

        rounded_components = {
            key: round(value, 9) for key, value in components.items()
        }
        return {
            "weights": self.weights.as_dict(),
            "units": {
                "distance": "kilometres before weighting",
                "travel_time": "minutes before weighting",
                "traffic_delay": "minutes before weighting",
                "risk": "risk fraction × kilometres before weighting",
                "total_cost": "dimensionless weighted score",
            },
            "edge_count": edge_count,
            **{key: round(value, 6) for key, value in totals.items()},
            "components": rounded_components,
            # Derive the public total from the public component values so clients
            # can verify the invariant exactly, without a 1e-9 rounding mismatch.
            "total_cost": round(sum(rounded_components.values()), 9),
        }
