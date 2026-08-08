"""Endpoint contract: every /api payload's JSON keys vs MAP_CONTRACT.md / §11.

GUI_ROADMAP.md § 15: contract tests use pytest + jsonschema and assert every
endpoint's JSON keys against MAP_CONTRACT — `additionalProperties: false` turns
any field rename into a test failure. Reuses `GRAPH_PAYLOAD_SCHEMA` for the
graph payload and mirrors the `SEARCH_RESPONSE_SCHEMA` shapes the flow tests
already validate (MAP_CONTRACT.md § 2/§ 3/§ 4, GUI_ROADMAP.md § 11).
"""

from __future__ import annotations

import jsonschema
import pytest
from fastapi.testclient import TestClient

from ui.service import backends
from ui.service.main import create_app

from .test_graph_payload import GRAPH_PAYLOAD_SCHEMA

START = "poi_node_10539950899"
GOAL = "poi_airport_tansonnhat"

SEARCH_STEP_SCHEMA = {
    "type": "object",
    "required": ["current_node", "frontier", "reason"],
    "additionalProperties": False,
    "properties": {
        "current_node": {"type": "string"},
        "frontier": {"type": "array", "items": {"type": "string"}},
        "reason": {"type": "string"},
    },
}

SEARCH_RESULT_SCHEMA = {
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
        "steps": {"type": "array", "items": SEARCH_STEP_SCHEMA},
        "total_distance_km": {"type": "number"},
        "total_time_min": {"type": "number"},
        "total_cost": {"type": "number"},
        "processing_time_ms": {"type": "number"},
        "explanation": {"type": "string"},
    },
}

SEARCH_METRICS_SCHEMA = {
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
}

ROUTE_SCHEMA = {
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
}

SEARCH_RUN_SCHEMA = {
    "type": "object",
    "required": ["id", "algorithm", "source"],
    "additionalProperties": False,
    "properties": {
        "id": {"type": "string"},
        "algorithm": {"type": "string"},
        "source": {"type": "string"},
    },
}

SEARCH_RESPONSE_SCHEMA = {
    "type": "object",
    "required": ["run", "result", "metrics", "route"],
    "additionalProperties": False,
    "properties": {
        "run": SEARCH_RUN_SCHEMA,
        "result": SEARCH_RESULT_SCHEMA,
        "metrics": SEARCH_METRICS_SCHEMA,
        "route": ROUTE_SCHEMA,
    },
}

HISTORY_RUN_SCHEMA = {
    "type": "object",
    "required": ["id", "algorithm", "start", "goal", "source", "created_at", "hops"],
    "additionalProperties": False,
    "properties": {
        "id": {"type": "string"},
        "algorithm": {"type": "string"},
        "start": {"type": "string"},
        "goal": {"type": "string"},
        "source": {"type": "string"},
        "created_at": {"type": "string"},
        "hops": {"type": "integer"},
    },
}

HISTORY_RESPONSE_SCHEMA = {
    "type": "object",
    "required": ["runs"],
    "additionalProperties": False,
    "properties": {"runs": {"type": "array", "items": HISTORY_RUN_SCHEMA}},
}

HISTORY_ITEM_RESPONSE_SCHEMA = {
    "type": "object",
    "required": ["run", "result"],
    "additionalProperties": False,
    "properties": {
        "run": HISTORY_RUN_SCHEMA,
        "result": SEARCH_RESULT_SCHEMA,
    },
}

HEALTH_SCHEMA = {
    "type": "object",
    "required": ["status"],
    "additionalProperties": False,
    "properties": {"status": {"type": "string"}},
}

VERSION_SCHEMA = {
    "type": "object",
    "required": ["service", "version", "api_version"],
    "additionalProperties": False,
    "properties": {
        "service": {"type": "string"},
        "version": {"type": "string"},
        "api_version": {"type": "string"},
    },
}

CATALOG_SCHEMA = {
    "type": "object",
    "required": ["algorithms"],
    "additionalProperties": False,
    "properties": {
        "algorithms": {
            "type": "array",
            "items": {
                "type": "object",
                "required": ["id", "label", "mock"],
                "additionalProperties": False,
                "properties": {
                    "id": {"type": "string"},
                    "label": {"type": "string"},
                    "mock": {"type": "boolean"},
                },
            },
        }
    },
}


@pytest.fixture(scope="module")
def client() -> TestClient:
    return TestClient(create_app())


def test_every_endpoint_matches_map_contract(client: TestClient) -> None:
    jsonschema.validate(client.get("/api/health").json(), HEALTH_SCHEMA)
    jsonschema.validate(client.get("/api/version").json(), VERSION_SCHEMA)
    jsonschema.validate(client.get("/api/algorithms").json(), CATALOG_SCHEMA)
    jsonschema.validate(client.get("/api/graph").json(), GRAPH_PAYLOAD_SCHEMA)

    response = client.post(
        "/api/search",
        json={"algorithm": "bfs", "start": START, "goal": GOAL},
    )
    assert response.status_code == 200
    jsonschema.validate(response.json(), SEARCH_RESPONSE_SCHEMA)

    jsonschema.validate(client.get("/api/history").json(), HISTORY_RESPONSE_SCHEMA)
    run_id = response.json()["run"]["id"]
    jsonschema.validate(
        client.get(f"/api/history/{run_id}").json(), HISTORY_ITEM_RESPONSE_SCHEMA
    )


def test_search_result_ids_exist_in_graph_payload(client: TestClient) -> None:
    """MAP_CONTRACT § 3.2: every id in the output maps to a graph node."""
    graph = client.get("/api/graph").json()
    node_ids = {node["id"] for node in graph["graph"]["nodes"]}
    assert node_ids

    result = client.post(
        "/api/search",
        json={"algorithm": "bfs", "start": START, "goal": GOAL},
    ).json()["result"]

    for node_id in result["path"] + result["visited_nodes"]:
        assert node_id in node_ids
    for step in result["steps"]:
        assert step["current_node"] in node_ids
        assert all(frontier_id in node_ids for frontier_id in step["frontier"])


def test_catalog_mock_flags_match_backend_dispatch(client: TestClient) -> None:
    """§ 11 catalog `mock` flags agree with the current real→mock dispatch."""
    entries = client.get("/api/algorithms").json()["algorithms"]
    flags = {entry["id"]: entry["mock"] for entry in entries}
    assert flags["bfs"] is False
    for name in ("dfs", "ucs", "greedy", "astar"):
        assert flags[name] is True
        _, source = backends.run_search(name, START, GOAL)
        assert (source == "mock") is flags[name]