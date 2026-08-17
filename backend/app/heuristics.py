"""Heuristic registry with explicit admissibility claims."""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import asdict, dataclass

from .costs import CostCalculator
from .domain import RoadGraph, haversine_meters


@dataclass(frozen=True, slots=True)
class HeuristicMetadata:
    id: str
    label: str
    description: str
    admissible: bool
    consistent: bool
    warning: str | None = None


HeuristicFunction = Callable[[str, str, RoadGraph, CostCalculator], float]


def _zero(_: str, __: str, ___: RoadGraph, ____: CostCalculator) -> float:
    return 0.0


def _straight_distance_km(node_id: str, goal_id: str, graph: RoadGraph) -> float:
    return (
        haversine_meters(graph.node(node_id), graph.node(goal_id))
        / 1000
        * graph.distance_lower_bound_scale
    )


def _haversine(node_id: str, goal_id: str, graph: RoadGraph, cost: CostCalculator) -> float:
    # Only the distance component is counted; every omitted component is non-negative.
    return cost.weights.distance * _straight_distance_km(node_id, goal_id, graph)


def _travel_time(node_id: str, goal_id: str, graph: RoadGraph, cost: CostCalculator) -> float:
    distance_km = _straight_distance_km(node_id, goal_id, graph)
    fastest_possible_minutes = distance_km / graph.max_speed_kph * 60
    return (
        cost.weights.distance * distance_km
        + cost.weights.travel_time * fastest_possible_minutes
    )


def _traffic_aware(node_id: str, goal_id: str, graph: RoadGraph, cost: CostCalculator) -> float:
    distance_km = _straight_distance_km(node_id, goal_id, graph)
    outgoing = [
        cost.traffic_status(edge).multiplier
        for edge in graph.neighbors(node_id)
        if cost.is_traversable(edge)
    ]
    estimated_multiplier = sum(outgoing) / len(outgoing) if outgoing else 1.0
    free_flow_minutes = distance_km / graph.max_speed_kph * 60
    predicted_minutes = free_flow_minutes * estimated_multiplier
    predicted_delay = max(0.0, predicted_minutes - free_flow_minutes)
    return (
        cost.weights.distance * distance_km
        + cost.weights.travel_time * predicted_minutes
        + cost.weights.traffic_delay * predicted_delay
    )


class HeuristicRegistry:
    def __init__(self) -> None:
        self._entries: dict[str, tuple[HeuristicMetadata, HeuristicFunction]] = {
            "zero": (
                HeuristicMetadata(
                    "zero",
                    "Zero heuristic",
                    "Always returns zero; A* becomes Dijkstra/UCS.",
                    True,
                    True,
                ),
                _zero,
            ),
            "haversine": (
                HeuristicMetadata(
                    "haversine",
                    "Haversine distance lower bound",
                    "Weights a dataset-calibrated great-circle lower bound and omits non-negative costs.",
                    True,
                    True,
                ),
                _haversine,
            ),
            "travel_time": (
                HeuristicMetadata(
                    "travel_time",
                    "Optimistic travel-time lower bound",
                    "Uses straight-line distance at the graph's maximum free-flow speed.",
                    True,
                    True,
                ),
                _travel_time,
            ),
            "traffic_aware": (
                HeuristicMetadata(
                    "traffic_aware",
                    "Traffic-aware estimate",
                    "Projects the current node's mean traffic multiplier toward the goal.",
                    False,
                    False,
                    "May overestimate and therefore may sacrifice A*/IDA* optimality.",
                ),
                _traffic_aware,
            ),
        }

    def metadata(self) -> list[dict[str, object]]:
        return [asdict(metadata) for metadata, _ in self._entries.values()]

    def get_metadata(self, name: str) -> HeuristicMetadata:
        try:
            return self._entries[name][0]
        except KeyError as exc:
            raise ValueError(f"Unknown heuristic {name!r}") from exc

    def estimate(
        self,
        name: str,
        node_id: str,
        goal_id: str,
        graph: RoadGraph,
        cost: CostCalculator,
    ) -> float:
        try:
            function = self._entries[name][1]
        except KeyError as exc:
            choices = ", ".join(self._entries)
            raise ValueError(f"Unknown heuristic {name!r}; choose one of: {choices}") from exc
        return max(0.0, function(node_id, goal_id, graph, cost))
