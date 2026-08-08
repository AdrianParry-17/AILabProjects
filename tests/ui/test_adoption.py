"""Adoption seam (Task-027): a real teammate algorithm bypasses the mock.

Proof, via TestClient: a fake teammate registered in ``ALGORITHM_REGISTRY``
(like a shipped ``algorithms/dfs.py`` with ``@register_algorithm``) returns a
real ``SearchResult`` with ``source="real"`` and is replayable from history;
the registry entry is restored afterwards.

The full endpoint-key contract (GUI_ROADMAP.md § 15: pytest + jsonschema in
``tests/ui/contract/``) lives in ``tests/ui/contract/test_endpoint_contract.py``.
"""

from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from core.search_algorithm import ALGORITHM_REGISTRY, SearchAlgorithm
from core.search_result import SearchResult
from ui.service.main import create_app
from ui.service.mocks import MockDFS

START = "poi_node_10539950899"
GOAL = "poi_airport_tansonnhat"


class TeammateDFS(SearchAlgorithm):
    """Stand-in for the DFS teammate's real implementation.

    Reuses the mock's traversal so the result is a valid delivery-graph
    ``SearchResult``, but prefixes the explanation so tests can prove the
    registered class — not the mock fallback — produced the response.
    """

    name = "dfs"

    def search(
        self,
        graph,
        start: str,
        goal: str,
        **kwargs: object,
    ) -> SearchResult:
        result = MockDFS().search(graph, start, goal, **kwargs)
        return result.model_copy(
            update={"explanation": f"TEAMMATE_DFS: {result.explanation}"}
        )


@pytest.fixture(scope="module")
def client() -> TestClient:
    return TestClient(create_app())


@pytest.fixture
def client_with_adopted_dfs(
    monkeypatch: pytest.MonkeyPatch,
) -> TestClient:
    """A TestClient whose registry carries the fake teammate's ``dfs`` module."""
    monkeypatch.setitem(ALGORITHM_REGISTRY, "dfs", TeammateDFS)
    return TestClient(create_app())


# -- adoption: source="real" through the whole HTTP stack -------------------


def test_adopted_teammate_bypasses_mock(client_with_adopted_dfs: TestClient) -> None:
    response = client_with_adopted_dfs.post(
        "/api/search",
        json={"algorithm": "dfs", "start": START, "goal": GOAL},
    )
    assert response.status_code == 200
    body = response.json()
    assert body["run"]["source"] == "real"
    assert "TEAMMATE_DFS" in body["result"]["explanation"]
    assert body["result"]["path"][0] == START
    assert body["result"]["path"][-1] == GOAL


def test_adopted_run_is_replayable_from_history(
    client_with_adopted_dfs: TestClient,
) -> None:
    response = client_with_adopted_dfs.post(
        "/api/search",
        json={"algorithm": "dfs", "start": START, "goal": GOAL},
    )
    assert response.status_code == 200
    run_id = response.json()["run"]["id"]

    replay = client_with_adopted_dfs.get(f"/api/history/{run_id}")
    assert replay.status_code == 200
    run = replay.json()["run"]
    assert run["source"] == "real"
    assert run["algorithm"] == "dfs"
    assert "TEAMMATE_DFS" in replay.json()["result"]["explanation"]

    runs = client_with_adopted_dfs.get("/api/history").json()["runs"]
    assert runs[0]["id"] == run_id
    assert runs[0]["source"] == "real"


def test_registry_is_restored_after_adoption(client: TestClient) -> None:
    """The fixture's registry entry is removed again: dfs -> mock fallback."""
    response = client.post(
        "/api/search",
        json={"algorithm": "dfs", "start": START, "goal": GOAL},
    )
    assert response.status_code == 200
    body = response.json()
    assert body["run"]["source"] == "mock"
    assert "mô phỏng" in body["result"]["explanation"]
