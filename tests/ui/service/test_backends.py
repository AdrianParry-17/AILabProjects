"""Tests for `ui.service.backends` (Task-025/026): catalog + real→mock fallback
+ on-demand dynamic discovery of teammate algorithm modules."""

from __future__ import annotations

import types

import pytest

from core.search_algorithm import ALGORITHM_REGISTRY, SearchAlgorithm
from core.search_result import SearchResult
from ui.service import backends
from ui.service.errors import AlgorithmUnavailableError, AlgorithmUnknownError

START = "poi_node_10539950899"
GOAL = "poi_airport_tansonnhat"

# A fake teammate module: a `@register_algorithm` class, exactly like
# `algorithms/bfs.py`. Discovery must import it on demand; the exec below runs
# the decorator, which is the module-level registration side effect.
_FAKE_MODULE_SOURCE = """
from core.search_algorithm import SearchAlgorithm, register_algorithm
from core.search_result import SearchResult

@register_algorithm
class SapphireSearch(SearchAlgorithm):
    name = "sapphire"

    def search(self, graph, start, goal, **kwargs):
        return SearchResult(
            path=[start, goal],
            visited_nodes=[start, goal],
            steps=[],
            total_distance_km=0.0,
            total_time_min=0.0,
            total_cost=0.0,
            processing_time_ms=0.0,
            explanation="SapphireSearch (fake teammate module).",
        )
"""


def test_catalog_marks_bfs_real_and_others_mock() -> None:
    catalog = backends.AlgorithmCatalog()
    assert catalog.is_mock("bfs") is False
    for name in ("dfs", "ucs", "greedy", "astar"):
        assert catalog.is_mock(name) is True


def test_catalog_exposes_names_labels_and_flags() -> None:
    entries = backends.AlgorithmCatalog().all()
    assert {e["id"] for e in entries} == {"bfs", "dfs", "ucs", "greedy", "astar"}
    assert all({"id", "label", "mock"} <= set(e) for e in entries)
    assert backends.AlgorithmCatalog().label("bfs") == "Breadth-First Search"


def test_bfs_runs_real() -> None:
    result, source = backends.run_search("bfs", START, GOAL)
    assert source == "real"
    assert result.path


def test_dfs_falls_back_to_mock() -> None:
    result, source = backends.run_search("dfs", START, GOAL)
    assert source == "mock"
    assert result.path
    assert "mô phỏng" in result.explanation


def test_unknown_name_raises_algorithm_unknown() -> None:
    with pytest.raises(AlgorithmUnknownError):
        backends.run_search("not-an-algorithm", START, GOAL)


def test_mock_provider_signature_matches_real() -> None:
    """Fallback mock returns a uniform SearchResult like the real backend."""
    result, source = backends.run_search("astar", START, GOAL)
    assert source == "mock"
    assert result.path[0] == START
    assert result.path[-1] == GOAL
    assert result.total_distance_km >= 0


def test_search_backend_isolated_for_unit() -> None:
    backend = backends.SearchBackend()
    result, source = backend.run("greedy", START, GOAL)
    assert source == "mock"
    assert isinstance(result.path, list)


# -- Task-026: on-demand dynamic discovery ---------------------------------


def test_discovery_imports_teammate_module_on_demand(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """A teammate module is found by `import_module("algorithms.<name>")`.

    The fake import performs the module-level `@register_algorithm` side effect
    exactly like importing `algorithms/<name>.py` from disk would.
    """
    imported: list[str] = []

    def fake_import(name: str) -> types.ModuleType:
        imported.append(name)
        module = types.ModuleType(name)
        exec(  # noqa: S102 - the seam test emulates the file import side effect
            compile(_FAKE_MODULE_SOURCE, "<algorithms/sapphire.py>", "exec"),
            module.__dict__,
        )
        return module

    monkeypatch.setattr(backends, "import_module", fake_import)
    try:
        result, source = backends.run_search("sapphire", START, GOAL)
    finally:
        ALGORITHM_REGISTRY.pop("sapphire", None)

    assert imported == ["algorithms.sapphire"]
    assert source == "real"
    assert "SapphireSearch" in result.explanation


def test_discovery_missing_module_keeps_algorithm_unknown(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """An unimportable module still errors: no module, no mock -> unknown."""
    imported: list[str] = []
    real_import_module = backends.import_module

    def spy(name: str):
        imported.append(name)
        return real_import_module(name)

    monkeypatch.setattr(backends, "import_module", spy)
    with pytest.raises(AlgorithmUnknownError):
        backends.run_search("no-such-module-xyz", START, GOAL)
    assert imported == ["algorithms.no-such-module-xyz"]


def test_registered_internal_key_error_is_never_masked(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """GUI_ROADMAP § 10: a registered algorithm's KeyError bug propagates.

    It must NOT fall back to the mock (a crash is not a registry miss).
    """

    class BuggyDFS(SearchAlgorithm):
        name = "dfs"

        def search(self, graph, start, goal, **kwargs) -> SearchResult:
            raise KeyError("missing internal map key")

    monkeypatch.setitem(ALGORITHM_REGISTRY, "dfs", BuggyDFS)
    with pytest.raises(KeyError):
        backends.run_search("dfs", START, GOAL)


def test_registered_placeholder_falls_back_to_mock(
    monkeypatch: pytest.MonkeyPatch,
    ) -> None:
    """A registered placeholder (NotImplementedError) falls back to the mock.

    GUI_ROADMAP § 10: `NotImplementedError` is a placeholder's explicit
    "not ready" marker, so the mock takes over (Task-026 acceptance: "still
    falls back on KeyError/NotImplementedError").
    """

    class PlaceholderDFS(SearchAlgorithm):
        name = "dfs"

        def search(self, graph, start, goal, **kwargs) -> SearchResult:
            raise NotImplementedError("owned by the DFS teammate; not ready yet")

    monkeypatch.setitem(ALGORITHM_REGISTRY, "dfs", PlaceholderDFS)
    result, source = backends.run_search("dfs", START, GOAL)
    assert source == "mock"
    assert result.path[0] == START
    assert result.path[-1] == GOAL
    assert "mô phỏng" in result.explanation


def test_registered_placeholder_without_mock_raises_unavailable(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """A registered placeholder with no mock -> `409 ALGORITHM_UNAVAILABLE`.

    GUI_ROADMAP § 7: `ALGORITHM_UNAVAILABLE` applies when the real path raises
    and no mock exists.
    """

    class PlaceholderSapphire(SearchAlgorithm):
        name = "sapphire"

        def search(self, graph, start, goal, **kwargs) -> SearchResult:
            raise NotImplementedError("not ready")

    monkeypatch.setitem(ALGORITHM_REGISTRY, "sapphire", PlaceholderSapphire)
    try:
        with pytest.raises(AlgorithmUnavailableError):
            backends.run_search("sapphire", START, GOAL)
    finally:
        ALGORITHM_REGISTRY.pop("sapphire", None)


def test_discovery_placeholder_module_imports_but_registers_nothing() -> None:
    """`algorithms/dfs.py` exists but is a placeholder -> still the mock."""
    result, source = backends.run_search("dfs", START, GOAL)
    assert source == "mock"
    assert result.path[0] == START
    assert result.path[-1] == GOAL