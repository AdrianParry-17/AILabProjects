"""Tests for `ui.service.history` (Task-012): search run history store."""

from __future__ import annotations

from core.search_result import SearchResult
from ui.service import history


def _result(hops: int = 3) -> SearchResult:
    return SearchResult(
        path=[f"n{i}" for i in range(hops + 1)],
        visited_nodes=["n0", "n1", "n2"],
        steps=[],
        total_distance_km=1.0,
        total_time_min=2.0,
        total_cost=3.0,
        processing_time_ms=4.0,
        explanation="ok",
    )


def test_record_and_recent_returns_newest_first() -> None:
    history.clear()
    first = history.record(
        algorithm="bfs", start="a", goal="c", source="real", result=_result()
    )
    second = history.record(
        algorithm="dfs", start="a", goal="c", source="real", result=_result()
    )
    assert first.id != second.id
    recent = history.recent()
    assert [r.id for r in recent] == [second.id, first.id]
    history.clear()


def test_get_returns_recorded_or_none() -> None:
    history.clear()
    run = history.record(
        algorithm="bfs", start="a", goal="c", source="real", result=_result()
    )
    assert history.get(run.id) == run
    assert history.get("r-999") is None
    history.clear()


def test_hops_derived_from_path() -> None:
    history.clear()
    run = history.record(
        algorithm="bfs", start="a", goal="d", source="real", result=_result(hops=4)
    )
    assert run.hops == 4
    assert run.result is not None
    history.clear()