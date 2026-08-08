"""Domain-logic enums shared across layers.

Plain-string contracts in the JSON dataset stay strings (CONVENTION.md § 4.5); these
enums are the typed constants that Python code uses to build/validate those strings.
"""

from __future__ import annotations

from enum import Enum


class Direction(str, Enum):
    """Direction of a directed edge (mirrors the JSON `direction` field)."""

    ONE_WAY = "one-way"
    TWO_WAY = "two-way"


class TrafficCondition(str, Enum):
    """Runtime traffic scenario multipliers (DATASET_SPEC.md § 7)."""

    NORMAL = "normal"
    RUSH_HOUR = "rush_hour"
    RAIN = "rain"


class AlgorithmName(str, Enum):
    """The search algorithms the framework exposes (ALGORITHM_SPEC.md § 2)."""

    BFS = "bfs"
    DFS = "dfs"
    UCS = "ucs"
    ASTAR = "astar"
    DIJKSTRA = "dijkstra"
    IDA_STAR = "ida_star"
    GREEDY = "greedy"
