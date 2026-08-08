"""/health + /graph API flows (GUI_ROADMAP.md § 11) via TestClient."""

from __future__ import annotations

import jsonschema
import pytest
from fastapi.testclient import TestClient

from tests.ui.contract.test_graph_payload import GRAPH_PAYLOAD_SCHEMA
from ui.service import graphs
from ui.service.main import create_app


@pytest.fixture(scope="module")
def client() -> TestClient:
    return TestClient(create_app())


def test_health_returns_ok(client: TestClient) -> None:
    response = client.get("/api/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_graph_returns_200_with_contract_body(client: TestClient) -> None:
    response = client.get("/api/graph")
    assert response.status_code == 200
    body = response.json()
    assert set(body) == {"graph", "bbox", "metadata"}
    assert body["metadata"]["node_count"] == 31
    assert body["metadata"]["edge_count"] == 70
    assert set(body["graph"]) == {"nodes", "edges", "geojson"}
    jsonschema.validate(body, GRAPH_PAYLOAD_SCHEMA)


def test_graph_returns_503_envelope_on_load_failure(
    client: TestClient, monkeypatch: pytest.MonkeyPatch
) -> None:
    def fail() -> dict:
        raise FileNotFoundError("delivery_graph.json is missing")

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


def test_graph_returns_500_envelope_on_unexpected_failure(
    client: TestClient, monkeypatch: pytest.MonkeyPatch
) -> None:
    def fail() -> dict:
        raise RuntimeError("payload serialization bug")

    monkeypatch.setattr(graphs, "get_graph_payload", fail)
    response = client.get("/api/graph")
    assert response.status_code == 500
    body = response.json()
    assert set(body) == {"error"}
    assert set(body["error"]) == {"code", "message", "details"}
    assert body["error"]["code"] == "INTERNAL"
