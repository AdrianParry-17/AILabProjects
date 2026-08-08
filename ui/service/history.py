"""In-memory search run history for the GUI service (GUI_ROADMAP.md § 9).

Records each `/search` call as a `RecordedRun` and keeps the recent list
available to the frontend (`getHistory`). Module-level singletons keep the state
process-scoped; this is a dev/demo store, not a durable database.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from itertools import count

from core.search_history import SearchHistory, SearchRun
from core.search_result import SearchResult

__all__ = ["RecordedRun", "clear", "get", "get_run", "list_runs", "recent", "record"]


@dataclass(frozen=True)
class RecordedRun:
    """A single recorded search run for the history store."""

    id: str
    algorithm: str
    start: str
    goal: str
    source: str
    created_at: str
    hops: int
    result: SearchResult


_HISTORY = SearchHistory()
_RECORDS: list[RecordedRun] = []
_IDS = count(1)


def record(
    *,
    algorithm: str,
    start: str,
    goal: str,
    source: str,
    result: SearchResult,
) -> RecordedRun:
    """Record a completed search run and return its `RecordedRun`."""
    created_at = datetime.now(timezone.utc).isoformat()
    run_id = f"r-{next(_IDS)}"
    recorded = RecordedRun(
        id=run_id,
        algorithm=algorithm,
        start=start,
        goal=goal,
        source=source,
        created_at=created_at,
        hops=len(result.path) - 1 if result.path else 0,
        result=result,
    )
    _RECORDS.append(recorded)
    _HISTORY.record(SearchRun(algorithm=algorithm, start=start, goal=goal, result=result))
    return recorded


def recent(limit: int = 20) -> list[RecordedRun]:
    """Return the most recent recorded runs (newest first)."""
    return list(reversed(_RECORDS))[:limit]


def get(run_id: str) -> RecordedRun | None:
    """Return a single recorded run by id, or ``None`` if unknown."""
    for run in _RECORDS:
        if run.id == run_id:
            return run
    return None


def list_runs(limit: int = 20) -> list[dict[str, object]]:
    """Return the § 11 ``GET /history`` run summaries (newest first).

    Each summary is a plain JSON-serializable dict: `id`, `algorithm`, `start`,
    `goal`, `source`, `created_at`, `hops`. It deliberately omits the `result`
    (replay fetches the full run via `get_run`).
    """
    return [
        {
            "id": run.id,
            "algorithm": run.algorithm,
            "start": run.start,
            "goal": run.goal,
            "source": run.source,
            "created_at": run.created_at,
            "hops": run.hops,
        }
        for run in recent(limit)
    ]


def get_run(run_id: str) -> RecordedRun | None:
    """Return the full recorded run by id (incl. `result` for replay), or None."""
    return get(run_id)


def clear() -> None:
    """Remove all recorded runs (test/code owner tooling)."""
    _RECORDS.clear()
    _HISTORY.clear()