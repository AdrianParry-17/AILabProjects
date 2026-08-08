"""Depth-First Search (DFS) — placeholder.

Owned by the DFS teammate. Implement `dfs()` (and a registered `SearchAlgorithm`
subclass, matching `algorithms/bfs.py`) per ALGORITHM_SPEC.md. Until then calling
`dfs()` raises `NotImplementedError` so consumers fail loudly instead of silently
getting an unfinished implementation.
"""

from __future__ import annotations

from shared.types import GraphLike


def dfs(
    graph: GraphLike,
    start: str,
    goal: str,
    enable_logging: bool = True,
):
    """Depth-First Search — not implemented yet (owner: DFS teammate)."""
    raise NotImplementedError(
        "DFS is not implemented yet; it is owned by the DFS teammate (algorithms/dfs.py)."
    )
