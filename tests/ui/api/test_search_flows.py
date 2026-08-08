"""/search API flows (GUI_ROADMAP.md § 11) via TestClient, covering the § 7
error codes: 200 contract body + history recording, 404 ALGORITHM_UNKNOWN, 400
INVALID_INPUT, 400 malformed body, 504 SEARCH_TIMEOUT, and 500 SEARCH_FAILED
that never leaks stack traces.
"""

from __future__ import annotations

from typing import Any

import jsonschema
import pytest
from fastapi.testclient import TestClient

from ui.service import backends, history
from ui.service import main as main_module
from ui.service.main import create_app

START = "poi_node_10539950899"
GOAL = "poi_airport_tansonnhat"

SEARCH_RESPONSE_SCHEMA: dict[str, Any] = {
    "type": "object",
    "properties": {
        "run": {
            "type": "object",
            "required": ["id", "algorithm", "source"],
            "additionalProperties": False,
            "properties": {
                "id": {"type": "string"},
                "algorithm": {"type": "string"},
                "source": {"type": "string"},
            },
        },
        "result": {
            "type": "object",
            "required": [
                "path",
                "visited_nodes",
                "steps",
                "total_distance_km",
                "total_time_min",
                "total_cost",
                "processing_time_ms",
                "explanation",
            ],
            "additionalProperties": False,
            "properties": {
                "path": {"type": "array", "items": {"type": "string"}},
                "visited_nodes": {"type": "array", "items": {"type": "string"}},
                "steps": {"type": "array"},
                "total_distance_km": {"type": "number"},
                "total_time_min": {"type": "number"},
                "total_cost": {"type": "number"},
                "processing_time_ms": {"type": "number"},
                "explanation": {"type": "string"},
            },
        },
        "metrics": {
            "type": "object",
            "required": [
                "hops",
                "nodes_visited",
                "distance_km",
                "time_min",
                "cost",
                "processing_time_ms",
            ],
            "additionalProperties": False,
            "properties": {
                "hops": {"type": "integer"},
                "nodes_visited": {"type": "integer"},
                "distance_km": {"type": "number"},
                "time_min": {"type": "number"},
                "cost": {"type": "number"},
                "processing_time_ms": {"type": "number"},
            },
        },
        "route": {
            "anyOf": [
                {"type": "null"},
                {
                    "type": "object",
                    "required": ["type", "geometry"],
                    "additionalProperties": False,
                    "properties": {
                        "type": {"const": "Feature"},
                        "geometry": {
                            "type": "object",
                            "required": ["type", "coordinates"],
                            "additionalProperties": False,
                            "properties": {
                                "type": {"const": "LineString"},
                                "coordinates": {
                                    "type": "array",
                                    "items": {
                                        "type": "array",
                                        "items": {"type": "number"},
                                        "minItems": 2,
                                        "maxItems": 2,
                                    },
                                },
                            },
                        },
                    },
                },
            ]
        },
    },
    "required": ["run", "result", "metrics", "route"],
    "additionalProperties": False,
}


@pytest.fixture(scope="module")
def client() -> TestClient:
    return TestClient(create_app())


def _search_body(**overrides: Any) -> dict[str, Any]:
    body = {"algorithm": "bfs", "start": START, "goal": GOAL, "enable_logging": True}
    body.update(overrides)
    return body


def test_search_returns_200_with_contract_body(client: TestClient) -> None:
    response = client.post("/api/search", json=_search_body())
    assert response.status_code == 200
    body = response.json()
    jsonschema.validate(body, SEARCH_RESPONSE_SCHEMA)
    assert body["run"]["algorithm"] == "bfs"
    assert body["run"]["source"] == "real"
    assert body["result"]["path"]
    assert body["metrics"]["hops"] == len(body["result"]["path"]) - 1
    assert body["route"]["geometry"]["type"] == "LineString"


def test_search_records_steps_for_animation_by_default(client: TestClient) -> None:
    """Logging is on for normal interactive searches: steps reach the client."""
    response = client.post("/api/search", json=_search_body())
    assert response.status_code == 200
    steps = response.json()["result"]["steps"]
    assert steps, "a normal search must carry SearchSteps for the animation"
    for step in steps:
        assert set(step) == {"current_node", "frontier", "reason"}


def test_search_omits_steps_when_logging_is_explicitly_off(client: TestClient) -> None:
    response = client.post("/api/search", json=_search_body(enable_logging=False))
    assert response.status_code == 200
    body = response.json()
    assert body["result"]["steps"] == []
    assert body["result"]["path"], "path/metrics stay intact with logging off"


def test_search_records_run_in_history(client: TestClient) -> None:
    history.clear()
    response = client.post("/api/search", json=_search_body())
    assert response.status_code == 200
    run_id = response.json()["run"]["id"]
    recent = history.recent()
    assert any(r.id == run_id for r in recent)
    assert history.get(run_id) is not None
    history.clear()


def test_search_unknown_algorithm_returns_404(client: TestClient) -> None:
    response = client.post(
        "/api/search", json=_search_body(algorithm="not-an-algorithm")
    )
    assert response.status_code == 404
    assert response.json()["error"]["code"] == "ALGORITHM_UNKNOWN"


def test_search_dfs_falls_back_to_mock(client: TestClient) -> None:
    response = client.post("/api/search", json=_search_body(algorithm="dfs"))
    assert response.status_code == 200
    body = response.json()
    assert body["run"]["source"] == "mock"
    assert body["run"]["algorithm"] == "dfs"
    assert body["result"]["path"]
    assert "mô phỏng" in body["result"]["explanation"]


def test_search_unknown_goal_returns_400(client: TestClient) -> None:
    response = client.post(
        "/api/search", json=_search_body(start="unknown_node", goal=GOAL)
    )
    assert response.status_code == 400
    assert response.json()["error"]["code"] == "INVALID_INPUT"


def test_search_malformed_body_returns_400(client: TestClient) -> None:
    response = client.post("/api/search", json={"algorithm": "bfs"})
    assert response.status_code == 400
    assert response.json()["error"]["code"] == "INVALID_INPUT"


def test_search_timeout_returns_504(client: TestClient, monkeypatch: pytest.MonkeyPatch) -> None:
    import time

    def slow(algorithm: str, start: str, goal: str, *, enable_logging: bool):
        time.sleep(1.0)
        return None, "real"

    monkeypatch.setattr(main_module, "SEARCH_TIMEOUT_MS", 50)
    monkeypatch.setattr(backends, "run_search", slow)

    response = client.post("/api/search", json=_search_body())
    assert response.status_code == 504
    assert response.json()["error"]["code"] == "SEARCH_TIMEOUT"


def test_search_failure_never_leaks_stack_trace(
    client: TestClient, monkeypatch: pytest.MonkeyPatch
) -> None:
    def boom(algorithm: str, start: str, goal: str, *, enable_logging: bool):
        raise ValueError("SECRET_INTERNAL_DETAIL")

    monkeypatch.setattr(backends, "run_search", boom)
    response = client.post("/api/search", json=_search_body())
    assert response.status_code == 500
    body = response.json()
    assert body["error"]["code"] == "SEARCH_FAILED"
    assert "SECRET_INTERNAL_DETAIL" not in str(body)