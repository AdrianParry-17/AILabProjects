"""§ 7 error-path suite (Task-028): every failure envelope over TestClient.

Covers the codes the flow tests do not: `503 GRAPH_NOT_FOUND` for the missing
file / invalid graph variants, `504 SEARCH_TIMEOUT` (with an injected fake
sleep so the test is never flaky), and the exact ``{error: {code, message,
details}}`` envelope shape for every § 7 code (GUI_ROADMAP.md § 7).
"""

from __future__ import annotations

import time
from typing import Any

import pytest
from fastapi.testclient import TestClient

from core.search_algorithm import ALGORITHM_REGISTRY, SearchAlgorithm
from core.search_result import SearchResult
from shared.exceptions import InvalidGraphError
from ui.service import backends, graphs
from ui.service import main as main_module
from ui.service.main import create_app

START = "poi_node_10539950899"
GOAL = "poi_airport_tansonnhat"


@pytest.fixture(scope="module")
def client() -> TestClient:
    return TestClient(create_app())


def _search_body(**overrides: Any) -> dict[str, Any]:
    body = {"algorithm": "bfs", "start": START, "goal": GOAL}
    body.update(overrides)
    return body


def assert_envelope(body: dict[str, Any], status_code: int, code: str) -> None:
    """Assert the § 7 envelope shape ``{error: {code, message, details}}``."""
    assert set(body) == {"error"}
    error = body["error"]
    assert set(error) == {"code", "message", "details"}
    assert error["code"] == code
    assert isinstance(error["details"], dict)
    assert isinstance(error["message"], str) and error["message"]


# -- 503 GRAPH_NOT_FOUND ----------------------------------------------------


def test_missing_graph_file_maps_to_503(client: TestClient, monkeypatch: pytest.MonkeyPatch) -> None:
    def missing() -> dict:
        raise FileNotFoundError("data/exports/delivery_graph.json")

    monkeypatch.setattr(graphs, "get_graph_payload", missing)
    response = client.get("/api/graph")
    assert response.status_code == 503
    assert_envelope(response.json(), 503, "GRAPH_NOT_FOUND")


def test_invariant_violating_graph_maps_to_503(client: TestClient, monkeypatch: pytest.MonkeyPatch) -> None:
    def broken() -> dict:
        raise InvalidGraphError("edge refers to an unknown node")

    monkeypatch.setattr(graphs, "get_graph_payload", broken)
    response = client.get("/api/graph")
    assert response.status_code == 503
    assert_envelope(response.json(), 503, "GRAPH_NOT_FOUND")


# -- 504 SEARCH_TIMEOUT -----------------------------------------------------


def test_slow_search_maps_to_504(client: TestClient, monkeypatch: pytest.MonkeyPatch) -> None:
    """504 for a run that overruns the deadline; the injected fake sleep keeps
    the test fast and deterministic (Task-028 regression risk)."""

    def slow(algorithm: str, start: str, goal: str, *, enable_logging: bool):
        time.sleep(1.0)
        return None, "real"

    monkeypatch.setattr(main_module, "SEARCH_TIMEOUT_MS", 50)
    monkeypatch.setattr(backends, "run_search", slow)

    response = client.post(
        "/api/search",
        json={"algorithm": "bfs", "start": START, "goal": GOAL},
    )
    assert response.status_code == 504
    assert_envelope(response.json(), 504, "SEARCH_TIMEOUT")


# -- 400 INVALID_INPUT ------------------------------------------------------


def test_unknown_node_maps_to_400(client: TestClient) -> None:
    response = client.post(
        "/api/search",
        json={"algorithm": "bfs", "start": "unknown_node", "goal": GOAL},
    )
    assert response.status_code == 400
    assert_envelope(response.json(), 400, "INVALID_INPUT")


# -- 404 ALGORITHM_UNKNOWN --------------------------------------------------


def test_unknown_algorithm_maps_to_404(client: TestClient) -> None:
    response = client.post(
        "/api/search",
        json=_search_body(algorithm="no-such-algorithm"),
    )
    assert response.status_code == 404
    assert_envelope(response.json(), 404, "ALGORITHM_UNKNOWN")


# -- registered-algorithm failures (GUI_ROADMAP § 10: never masked) ---------


def test_registered_internal_key_error_maps_to_500(
    client: TestClient, monkeypatch: pytest.MonkeyPatch
) -> None:
    """A registered algorithm's internal KeyError is a bug -> SEARCH_FAILED.

    It must NOT be mistaken for a registry miss (404) or masked by the mock.
    """

    def boom_search(self, graph, start, goal, **kwargs) -> SearchResult:
        raise KeyError("SECRET_INTERNAL_DETAIL")

    buggy = type(
        "BuggyDFS",
        (SearchAlgorithm,),
        {"name": "dfs", "search": boom_search},
    )
    monkeypatch.setitem(ALGORITHM_REGISTRY, "dfs", buggy)
    response = client.post("/api/search", json=_search_body(algorithm="dfs"))
    assert response.status_code == 500
    assert_envelope(response.json(), 500, "SEARCH_FAILED")
    assert "SECRET_INTERNAL_DETAIL" not in str(response.json())


def test_registered_placeholder_falls_back_to_mock(
    client: TestClient, monkeypatch: pytest.MonkeyPatch
) -> None:
    """A registered placeholder -> the mock, `source="mock"` (GUI_ROADMAP § 10)."""

    def not_ready(self, graph, start, goal, **kwargs) -> SearchResult:
        raise NotImplementedError("owned by the UCS teammate")

    placeholder = type(
        "PlaceholderUCS",
        (SearchAlgorithm,),
        {"name": "ucs", "search": not_ready},
    )
    monkeypatch.setitem(ALGORITHM_REGISTRY, "ucs", placeholder)
    response = client.post("/api/search", json=_search_body(algorithm="ucs"))
    assert response.status_code == 200
    body = response.json()
    assert body["run"]["source"] == "mock"
    assert "mô phỏng" in body["result"]["explanation"]


def test_registered_placeholder_without_mock_maps_to_409(
    client: TestClient, monkeypatch: pytest.MonkeyPatch
) -> None:
    """No mock exists for a registered placeholder -> 409 (GUI_ROADMAP § 7)."""

    def not_ready(self, graph, start, goal, **kwargs) -> SearchResult:
        raise NotImplementedError("not ready")

    placeholder = type(
        "PlaceholderSapphire",
        (SearchAlgorithm,),
        {"name": "sapphire", "search": not_ready},
    )
    monkeypatch.setitem(ALGORITHM_REGISTRY, "sapphire", placeholder)
    try:
        response = client.post("/api/search", json=_search_body(algorithm="sapphire"))
        assert response.status_code == 409
        assert_envelope(response.json(), 409, "ALGORITHM_UNAVAILABLE")
    finally:
        ALGORITHM_REGISTRY.pop("sapphire", None)


# -- 500 SEARCH_FAILED (never leaks internals) ------------------------------


def test_unexpected_failure_maps_to_500(client: TestClient, monkeypatch: pytest.MonkeyPatch) -> None:
    def boom(algorithm: str, start: str, goal: str, *, enable_logging: bool):
        raise RuntimeError("SECRET_INTERNAL_DETAIL")

    monkeypatch.setattr(backends, "run_search", boom)
    response = client.post(
        "/api/search",
        json=_search_body(),
    )
    assert response.status_code == 500
    assert_envelope(response.json(), 500, "SEARCH_FAILED")
    assert "SECRET_INTERNAL_DETAIL" not in str(response.json())
