"""Centralized project configuration (CONVENTION.md § 11).

Dataset paths, build/algorithm defaults, and application settings live here so that
`algorithms/`, `delivery/`, `data/`, and `scripts/` never hard-code magic numbers.
"""

from config.defaults import (
    BBOX,
    DEFAULT_COUNTS,
    DEFAULT_WEIGHTS,
    K_NEAREST,
    MIN_EDGES,
    MIN_NODES,
    POI_FILTER,
    CostWeights,
)
from config.paths import (
    DATA_DIR,
    DELIVERY_GRAPH_PATH,
    EXPORTS_DIR,
    PROCESSED_DIR,
    RAW_DIR,
    RAW_OSM_PATH,
    ROAD_GRAPH_PATH,
)
from config.settings import (
    PROJECT_NAME,
    PROJECT_VERSION,
    SCHEMA_VERSION,
)

__all__ = [
    "BBOX",
    "DATA_DIR",
    "DEFAULT_COUNTS",
    "DEFAULT_WEIGHTS",
    "DELIVERY_GRAPH_PATH",
    "EXPORTS_DIR",
    "K_NEAREST",
    "MIN_EDGES",
    "MIN_NODES",
    "POI_FILTER",
    "PROCESSED_DIR",
    "PROJECT_NAME",
    "PROJECT_VERSION",
    "RAW_DIR",
    "RAW_OSM_PATH",
    "ROAD_GRAPH_PATH",
    "SCHEMA_VERSION",
    "CostWeights",
]
