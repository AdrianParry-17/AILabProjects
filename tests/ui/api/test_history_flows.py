"""/history + /history/:id API flows (GUI_ROADMAP.md § 11 Task-020) via TestClient.

Covers: `GET /history` → run summaries; `GET /history/:id` → full result incl.
steps (replay data); `404 NOT_FOUND` for an unknown id (§ 7).
"""

from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from ui.service import history
from ui.service.main import create_app

START = "poi_node_10539950899"
GOAL = "poi_airport_tansonnhat"


@pytest.fixture(scope="module")
def client() -> TestClient:
    return TestClient(create_app())


@pytest.fixture(autouse=True)
def _clean_history() -> None:
    """Isolate each test from prior recorded runs."""
    history.clear()
    yield
    history.clear()


def test_history_lists_run_summaries(client: TestClient) -> None:
    search = client.post(
        "/api/search",
        json={"algorithm": "bfs", "start": START, "goal": GOAL, "enable_logging": True},
    )
    assert search.status_code == 200
    run_id = search.json()["run"]["id"]

    response = client.get("/api/history")
    assert response.status_code == 200
    body = response.json()
    assert body["runs"][0]["id"] == run_id
    summary = body["runs"][0]
    assert set(summary) == {"id", "algorithm", "start", "goal", "source", "created_at", "hops"}
    assert summary["algorithm"] == "bfs"
    assert summary["start"] == START
    assert summary["goal"] == GOAL
    assert summary["source"] == "real"
    assert summary["hops"] >= 0


def test_history_by_id_returns_full_result(client: TestClient) -> None:
    search = client.post(
        "/api/search",
        json={"algorithm": "bfs", "start": START, "goal": GOAL, "enable_logging": True},
    )
    assert search.status_code == 200
    run_id = search.json()["run"]["id"]

    response = client.get(f"/api/history/{run_id}")
    assert response.status_code == 200
    body = response.json()
    assert set(body) == {"run", "result"}
    assert body["run"]["id"] == run_id
    assert set(body["result"]) == {
        "path",
        "visited_nodes",
        "steps",
        "total_distance_km",
        "total_time_min",
        "total_cost",
        "processing_time_ms",
        "explanation",
    }
    assert body["result"]["path"]
    assert body["result"]["steps"], "recorded runs keep SearchSteps for replay"


def test_history_by_id_returns_404_for_unknown(client: TestClient) -> None:
    response = client.get("/api/history/r-does-not-exist")
    assert response.status_code == 404
    body = response.json()
    assert body["error"]["code"] == "NOT_FOUND"
    assert body["error"]["details"]["id"] == "r-does-not-exist"