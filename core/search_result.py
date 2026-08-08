"""Shared output models returned by every search algorithm.

Owned by the core framework so all algorithms (BFS, DFS, UCS, A*, ...) and the
visualization/UI layers serialize the same JSON shape (MAP_CONTRACT.md § 2).
"""

from pydantic import BaseModel


class SearchStep(BaseModel):
    """One animation frame of a search (current node + frontier + reason)."""

    current_node: str
    frontier: list[str]
    reason: str


class SearchResult(BaseModel):
    """The uniform result every search algorithm returns."""

    path: list[str]
    visited_nodes: list[str]
    steps: list[SearchStep]
    total_distance_km: float
    total_time_min: float
    total_cost: float
    processing_time_ms: float
    explanation: str
