"""In-memory search run history (UI/report convenience).

Kept intentionally small: a bounded ring of past runs keyed by algorithm/start/goal.
Persistence (files, DB) is owned by whoever owns the reports feature.
"""

from __future__ import annotations

from collections import deque
from dataclasses import dataclass

from core.search_result import SearchResult


@dataclass(frozen=True, slots=True)
class SearchRun:
    """One recorded search execution."""

    algorithm: str
    start: str
    goal: str
    result: SearchResult


class SearchHistory:
    """Bounded, thread-agnostic record of past search runs."""

    def __init__(self, capacity: int = 100) -> None:
        self.capacity = capacity
        self._runs: deque[SearchRun] = deque(maxlen=capacity)

    def record(self, run: SearchRun) -> None:
        self._runs.append(run)

    def recent(self) -> list[SearchRun]:
        return list(self._runs)

    def clear(self) -> None:
        self._runs.clear()

    def __len__(self) -> int:
        return len(self._runs)
