"""Search lifecycle events for animation/history/reports.

`SearchResult.steps` is the persisted step stream; `SearchEvent` is the richer,
optionally-produced event that UI animation and `SearchHistory` can consume. BFS
emits a step per expanded node, which adapts to a `SearchEvent` via `from_step`.
"""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass
from enum import Enum

from core.search_result import SearchStep


class SearchEventKind(str, Enum):
    START = "start"
    NODE_EXPANDED = "node_expanded"
    GOAL_REACHED = "goal_reached"
    FAILED = "failed"
    FINISHED = "finished"


@dataclass(frozen=True, slots=True)
class SearchEvent:
    """One observable step of a search run."""

    kind: SearchEventKind
    node_id: str
    frontier: tuple[str, ...]
    message: str = ""

    @classmethod
    def from_step(
        cls,
        step: SearchStep,
        *,
        kind: SearchEventKind = SearchEventKind.NODE_EXPANDED,
    ) -> SearchEvent:
        return cls(kind=kind, node_id=step.current_node, frontier=tuple(step.frontier))

    @classmethod
    def from_steps(
        cls,
        steps: Sequence[SearchStep],
        *,
        kind: SearchEventKind = SearchEventKind.NODE_EXPANDED,
    ) -> list[SearchEvent]:
        return [cls.from_step(step, kind=kind) for step in steps]
