"""Deterministic, explainable traffic scenarios.

No live traffic feed is implied.  Scenario variation is derived from stable
edge identifiers, road classes and explicit dataset flags, so identical input
always produces identical output across processes and platforms.
"""

from __future__ import annotations

import hashlib
from dataclasses import asdict, dataclass
from typing import Any

from .domain import DirectedEdge


@dataclass(frozen=True, slots=True)
class ScenarioDefinition:
    id: str
    label: str
    description: str
    base_multiplier: float
    jitter: float


SCENARIOS: dict[str, ScenarioDefinition] = {
    "normal": ScenarioDefinition(
        "normal",
        "Normal traffic",
        "Snapshot baseline congestion with light deterministic variation.",
        1.00,
        0.08,
    ),
    "morning_rush": ScenarioDefinition(
        "morning_rush",
        "Morning rush hour",
        "Higher delay on primary and arterial approaches to the city centre.",
        1.22,
        0.28,
    ),
    "evening_rush": ScenarioDefinition(
        "evening_rush",
        "Evening rush hour",
        "Widespread congestion with stronger river-crossing pressure.",
        1.30,
        0.32,
    ),
    "heavy_rain": ScenarioDefinition(
        "heavy_rain",
        "Heavy rain",
        "Reduced speeds, especially on bridges and higher-risk segments.",
        1.34,
        0.22,
    ),
    "incident": ScenarioDefinition(
        "incident",
        "Road disruption",
        "A deterministic teaching scenario that closes explicitly flagged road segments.",
        1.12,
        0.18,
    ),
}


@dataclass(frozen=True, slots=True)
class TrafficStatus:
    edge_id: str
    scenario: str
    multiplier: float
    effective_speed_kph: float
    free_flow_time_s: float
    travel_time_s: float | None
    delay_s: float | None
    congestion: str
    closed: bool
    reason: str

    def as_dict(self) -> dict[str, Any]:
        return asdict(self)


class TrafficModel:
    def __init__(self) -> None:
        self._cache: dict[tuple[str, str], TrafficStatus] = {}

    @staticmethod
    def scenario_metadata() -> list[dict[str, Any]]:
        return [asdict(item) for item in SCENARIOS.values()]

    @staticmethod
    def validate_scenario(scenario: str) -> None:
        if scenario not in SCENARIOS:
            choices = ", ".join(SCENARIOS)
            raise ValueError(f"Unknown traffic scenario {scenario!r}; choose one of: {choices}")

    @staticmethod
    def _bucket(edge_id: str, scenario: str) -> float:
        digest = hashlib.sha256(f"{scenario}|{edge_id}".encode()).digest()
        value = int.from_bytes(digest[:8], "big")
        return value / ((1 << 64) - 1)

    def status(self, edge: DirectedEdge, scenario: str) -> TrafficStatus:
        self.validate_scenario(scenario)
        cache_key = (edge.id, scenario)
        if cache_key in self._cache:
            return self._cache[cache_key]

        definition = SCENARIOS[scenario]
        attributes = edge.attributes
        closed = bool(
            scenario == "incident" and attributes.get("close_during_incident", False)
        )
        road_factor = 1.0
        reason_parts = [definition.label]

        try:
            base_congestion = float(attributes.get("base_congestion", 1.0))
        except (TypeError, ValueError):
            base_congestion = 1.0
        base_congestion = min(5.0, max(1.0, base_congestion))
        road_factor *= 1.0 + (base_congestion - 1.0) * 0.10
        if base_congestion > 1.0:
            reason_parts.append(f"snapshot baseline {base_congestion:.2f}/5")

        if scenario == "morning_rush" and edge.road_class in {"primary", "arterial"}:
            road_factor *= 1.12
            reason_parts.append("major-road demand")
        elif scenario == "evening_rush":
            if attributes.get("bridge", False):
                road_factor *= 1.18
                reason_parts.append("river-crossing demand")
            elif edge.road_class in {"primary", "arterial"}:
                road_factor *= 1.09
                reason_parts.append("major-road demand")
        elif scenario == "heavy_rain":
            road_factor *= 1.0 + 0.16 * edge.risk
            if attributes.get("bridge", False):
                road_factor *= 1.16
                reason_parts.append("wet bridge")
            else:
                reason_parts.append("wet road")
        elif scenario == "incident" and attributes.get("incident_prone", False):
            road_factor *= 1.20
            reason_parts.append("incident vicinity")

        multiplier = definition.base_multiplier * road_factor * (
            1.0 + definition.jitter * self._bucket(edge.id, scenario)
        )
        multiplier = round(max(1.0, multiplier), 6)
        free_flow = edge.free_flow_time_s

        if closed:
            status = TrafficStatus(
                edge_id=edge.id,
                scenario=scenario,
                multiplier=multiplier,
                effective_speed_kph=0.0,
                free_flow_time_s=round(free_flow, 6),
                travel_time_s=None,
                delay_s=None,
                congestion="closed",
                closed=True,
                reason="; ".join(reason_parts + ["segment closed by scenario"]),
            )
        else:
            travel_time = free_flow * multiplier
            if multiplier <= 1.15:
                congestion = "light"
            elif multiplier <= 1.45:
                congestion = "moderate"
            elif multiplier <= 1.80:
                congestion = "heavy"
            else:
                congestion = "severe"
            status = TrafficStatus(
                edge_id=edge.id,
                scenario=scenario,
                multiplier=multiplier,
                effective_speed_kph=round(edge.speed_kph / multiplier, 6),
                free_flow_time_s=round(free_flow, 6),
                travel_time_s=round(travel_time, 6),
                delay_s=round(travel_time - free_flow, 6),
                congestion=congestion,
                closed=False,
                reason="; ".join(reason_parts + ["stable edge variation"]),
            )

        self._cache[cache_key] = status
        return status
