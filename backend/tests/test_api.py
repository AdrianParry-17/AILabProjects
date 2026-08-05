from __future__ import annotations

from fastapi.testclient import TestClient

from app.config import TEACHING_DATASET_PATH
from app.main import create_app


def test_health_metadata_graph_and_search_contracts():
    with TestClient(create_app(TEACHING_DATASET_PATH)) as client:
        health = client.get("/api/v1/health")
        assert health.status_code == 200
        assert health.json()["dataset_id"] == "hcmc-delivery-teaching-fixture-v1"
        assert health.json()["node_count"] == 7

        metadata = client.get("/api/v1/metadata")
        assert metadata.status_code == 200
        assert metadata.json()["api"]["name"] == "HCMC Delivery Route Lab API"
        assert len(metadata.json()["algorithms"]) == 8
        assert {item["id"] for item in metadata.json()["heuristics"]} == {
            "zero", "haversine", "travel_time", "traffic_aware"
        }

        graph = client.get(
            "/api/v1/graph",
            params={"scenario": "incident", "include_geojson": True},
        )
        assert graph.status_code == 200
        assert any(edge["traffic"]["closed"] for edge in graph.json()["directed_edges"])
        assert all(edge["traversable"] for edge in graph.json()["directed_edges"])
        assert len(graph.json()["graph_geojson"]["features"]) == len(
            graph.json()["directed_edges"]
        )

        compact_graph = client.get(
            "/api/v1/graph",
            params={"scenario": "incident", "compact": True},
        )
        assert compact_graph.status_code == 200
        assert compact_graph.json()["graph_geojson"]["features"] == []
        assert [edge["id"] for edge in compact_graph.json()["directed_edges"]] == [
            edge["id"] for edge in graph.json()["directed_edges"]
        ]
        assert [edge["geometry"] for edge in compact_graph.json()["directed_edges"]] == [
            edge["geometry"] for edge in graph.json()["directed_edges"]
        ]
        assert all(
            "geometry" not in edge["attributes"]
            for edge in compact_graph.json()["directed_edges"]
        )

        overlay = client.get("/api/v1/traffic", params={"scenario": "heavy_rain"})
        assert overlay.status_code == 200
        assert overlay.json()["scenario"]["id"] == "heavy_rain"
        assert len(overlay.json()["edges"]) == health.json()["directed_edge_count"]
        assert set(overlay.json()["edges"][0]) == {
            "edge_id", "multiplier", "effective_speed_kph", "travel_time_s",
            "congestion", "closed",
        }

        response = client.post(
            "/api/v1/search",
            json={
                "start_id": "courier_hub",
                "goal_id": "ben_thanh_market",
                "algorithm": "astar",
                "heuristic": "travel_time",
                "scenario": "morning_rush",
                "include_alternative": True,
            },
        )
        assert response.status_code == 200, response.text
        body = response.json()
        assert body["found"]
        assert body["path"][0] == "courier_hub"
        assert body["path"][-1] == "ben_thanh_market"
        assert body["route_geojson"]["type"] == "LineString"
        assert body["cost_breakdown"]["total_cost"] == body["metrics"]["path_cost"]
        assert set(body) >= {
            "path", "route_geojson", "metrics", "trace", "explanation",
            "alternative", "cost_breakdown", "algorithm", "heuristic",
        }


def test_validation_and_multi_route():
    with TestClient(create_app(TEACHING_DATASET_PATH)) as client:
        invalid = client.post(
            "/api/v1/search",
            json={"start_id": "missing", "goal_id": "ben_thanh_market"},
        )
        assert invalid.status_code == 422
        assert invalid.json()["error"]["code"] == "unknown_node"

        multi = client.post(
            "/api/v1/multi-route",
            json={
                "start_id": "courier_hub",
                "stop_ids": ["ben_thanh_market", "coop_mart", "city_university"],
                "method": "held_karp",
                "scenario": "normal",
                "return_to_start": True,
            },
        )
        assert multi.status_code == 200, multi.text
        body = multi.json()
        assert sorted(body["stop_order"]) == sorted(
            ["ben_thanh_market", "coop_mart", "city_university"]
        )
        assert body["visit_sequence"][0] == body["visit_sequence"][-1] == "courier_hub"
