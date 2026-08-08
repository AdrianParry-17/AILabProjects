"""/graph error mapping: corrupt or unparseable graph sources -> 503 GRAPH_NOT_FOUND.

Covers the graph-load failure paths of `ui.service.main.get_graph`
(GUI_ROADMAP.md § 7) that the happy-path flow tests do not: invalid JSON and
Pydantic validation failures must surface as `503 GRAPH_NOT_FOUND`.
"""

from __future__ import annotations

import json

import pytest
from fastapi.testclient import TestClient
from pydantic import ValidationError

from ui.service import graphs
from ui.service.main import create_app


@pytest.fixture(scope="module")
def client() -> TestClient:
    return TestClient(create_app())


def test_invalid_json_maps_to_503_graph_not_found(
    client: TestClient, monkeypatch: pytest.MonkeyPatch
) -> None:
    def fail() -> dict:
        raise json.JSONDecodeError("corrupt json", "doc", 0)

    monkeypatch.setattr(graphs, "get_graph_payload", fail)
    response = client.get("/api/graph")
    assert response.status_code == 503
    assert response.json() == {
        "error": {
            "code": "GRAPH_NOT_FOUND",
            "message": "Graph files are missing or failed to load.",
            "details": {},
        }
    }


def test_validation_failure_maps_to_503_graph_not_found(
    client: TestClient, monkeypatch: pytest.MonkeyPatch
) -> None:
    def fail() -> dict:
        raise ValidationError.from_exception_data("delivery graph", [])

    monkeypatch.setattr(graphs, "get_graph_payload", fail)
    response = client.get("/api/graph")
    assert response.status_code == 503
    body = response.json()
    assert set(body) == {"error"}
    assert body["error"]["code"] == "GRAPH_NOT_FOUND"