"""Uniform-Cost Search (UCS) — placeholder.

Owned by the UCS teammate. Implement `ucs()` (and a registered `SearchAlgorithm`
subclass, matching `algorithms/bfs.py`) per ALGORITHM_SPEC.md. Until then calling
`ucs()` raises `NotImplementedError` so consumers fail loudly instead of silently
getting an unfinished implementation.
"""

from __future__ import annotations

from shared.types import GraphLike


def ucs(
    graph: GraphLike,
    start: str,
    goal: str,
    enable_logging: bool = True,
):
    """Uniform-Cost Search — not implemented yet (owner: UCS teammate)."""
    raise NotImplementedError(
        "UCS is not implemented yet; it is owned by the UCS teammate (algorithms/ucs.py)."
    )
