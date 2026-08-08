"""/algorithms + /version API flows (GUI_ROADMAP.md § 11/§ 12) via TestClient."""

from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from ui.service.backends import AlgorithmCatalog
from ui.service.main import create_app


@pytest.fixture(scope="module")
def client() -> TestClient:
    return TestClient(create_app())


def test_algorithms_returns_the_catalog(client: TestClient) -> None:
    response = client.get("/api/algorithms")
    assert response.status_code == 200
    body = response.json()
    assert set(body) == {"algorithms"}
    assert body["algorithms"] == AlgorithmCatalog().all()
    for entry in body["algorithms"]:
        assert set(entry) == {"id", "label", "mock"}
        assert isinstance(entry["label"], str)
        assert isinstance(entry["mock"], bool)


def test_algorithms_marks_bfs_real_and_mocks(client: TestClient) -> None:
    response = client.get("/api/algorithms")
    by_id = {entry["id"]: entry for entry in response.json()["algorithms"]}
    assert set(by_id) == {"bfs", "dfs", "ucs", "greedy", "astar"}
    assert by_id["bfs"]["mock"] is False
    assert by_id["dfs"]["mock"] is True
    assert by_id["ucs"]["mock"] is True
    assert by_id["greedy"]["mock"] is True
    assert by_id["astar"]["mock"] is True


def test_version_returns_gate_fields(client: TestClient) -> None:
    response = client.get("/api/version")
    assert response.status_code == 200
    body = response.json()
    assert set(body) == {"service", "version", "api_version"}
    assert body["service"]
    assert body["version"]
    assert body["api_version"]
