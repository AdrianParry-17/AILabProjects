"""Build/algorithm default tuning values (CONVENTION.md § 11).

Every magic number the pipeline scripts used to hard-code now lives here so the
`data/`, `delivery/`, and `algorithms/` layers import shared, single-source values.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Final

# HCMC city-centre bounding box [south, west, north, east].
BBOX: Final[list[float]] = [10.7500, 106.6650, 10.8000, 106.7150]

# Road classes retained by the OSM snapshot and their tuning profiles.
ROAD_CLASSES: Final[set[str]] = {"primary", "secondary", "tertiary"}
DEFAULT_SPEED: Final[dict[str, float]] = {
    "primary": 45.0,
    "secondary": 35.0,
    "tertiary": 30.0,
}
CONGESTION_BASE: Final[dict[str, float]] = {
    "primary": 2.0,
    "secondary": 2.6,
    "tertiary": 3.2,
}
RISK_BASE: Final[dict[str, float]] = {
    "primary": 0.6,
    "secondary": 1.0,
    "tertiary": 1.5,
}

# OSM tag pairs mapped to delivery POI kinds (build_osm_snapshot).
POI_FILTER: Final[dict[tuple[str, str], str]] = {
    ("amenity", "marketplace"): "delivery_market",
    ("shop", "supermarket"): "delivery_supermarket",
    ("amenity", "bus_station"): "delivery_bus_station",
    ("amenity", "hospital"): "delivery_hospital",
    ("amenity", "university"): "delivery_university",
}

# Delivery Graph synthetic-POI tuning (delivery/builder.py).
AIRPORT_POSITION: Final[tuple[float, float]] = (10.8188, 106.6520)  # Tân Sơn Nhất (lat, lon)
DEFAULT_COUNTS: Final[dict[str, int]] = {
    "delivery_supermarket": 5,
    "delivery_market": 5,
    "delivery_bus_station": 4,
    "delivery_hospital": 6,
    "delivery_university": 5,
    "delivery_warehouse": 5,
    "delivery_airport": 1,
}
K_NEAREST: Final[int] = 2

# Delivery Graph hard minimums enforced on load (delivery/loader.py).
MIN_NODES: Final[int] = 20
MIN_EDGES: Final[int] = 30

# Edge-cost model weights (ALGORITHM_SPEC.md § 14):
#   Cost = alpha * Distance + beta * Time + gamma * Congestion + delta * Risk


@dataclass(frozen=True, slots=True)
class CostWeights:
    distance: float = 0.3  # alpha
    time: float = 0.4  # beta
    congestion: float = 0.2  # gamma
    risk: float = 0.1  # delta


DEFAULT_WEIGHTS: Final[CostWeights] = CostWeights()
