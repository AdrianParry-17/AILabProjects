"""Tests for `ui.service.routing` (Task-011): real routing + route expansion."""

from __future__ import annotations

import pytest

from core.search_result import SearchResult
from ui.service import graphs, routing

START = "poi_node_10539950899"
GOAL = "poi_airport_tansonnhat"


def test_run_real_bfs_returns_real_source() -> None:
    result, source = routing.run("bfs", START, GOAL)
    assert isinstance(result, SearchResult)
    assert source == "real"
    assert result.path


def test_run_unknown_algorithm_raises_key_error() -> None:
    with pytest.raises(KeyError):
        routing.run("not-an-algorithm", START, GOAL)


def test_expand_path_returns_line_string_feature() -> None:
    delivery = graphs.get_delivery_graph()
    road = graphs.get_road_graph()
    result, _ = routing.run("bfs", START, GOAL)
    feature = routing.expand_path(result.path, road, delivery)
    assert feature is not None
    assert feature["type"] == "Feature"
    assert feature["geometry"]["type"] == "LineString"
    coords = feature["geometry"]["coordinates"]
    assert coords
    assert all(len(pair) == 2 for pair in coords)


def test_expand_path_returns_none_for_short_path() -> None:
    assert routing.expand_path([], None) is None
    assert routing.expand_path([START], graphs.get_road_graph()) is None


def test_expand_path_propagates_missing_road_error() -> None:
    road = graphs.get_road_graph()
    with pytest.raises((ValueError, KeyError)):
        routing.expand_path(["unknown_road_a", "unknown_road_b"], road, None)