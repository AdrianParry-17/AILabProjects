"""A* Search — placeholder.

Owned by the A* teammate. Implement `astar()` (and a registered `SearchAlgorithm`
subclass, matching `algorithms/bfs.py`) per ALGORITHM_SPEC.md. Use the shared cost
(`algorithms/heuristic.py`) and heuristic estimates owned there. Until then calling
`astar()` raises `NotImplementedError` so consumers fail loudly instead of silently
getting an unfinished implementation.
"""

from __future__ import annotations

from shared.types import GraphLike


def astar(
    graph: GraphLike,
    start: str,
    goal: str,
    enable_logging: bool = True,
):
    """A* Search — not implemented yet (owner: A* teammate)."""
    raise NotImplementedError(
        "A* is not implemented yet; it is owned by the A* teammate (algorithms/astar.py)."
    )
