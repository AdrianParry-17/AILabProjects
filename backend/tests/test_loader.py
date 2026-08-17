from __future__ import annotations

import json

import pytest

from app.loader import DatasetLoadError, load_dataset


def test_loader_expands_bidirectional_edge(tmp_path):
    path = tmp_path / "graph.json"
    path.write_text(
        json.dumps(
            {
                "metadata": {"id": "x", "name": "X"},
                "nodes": [
                    {"id": "a", "name": "A", "lat": 16, "lon": 108},
                    {"id": "b", "name": "B", "lat": 16.01, "lon": 108.01},
                ],
                "edges": [
                    {
                        "id": "ab", "source": "a", "target": "b",
                        "distance_m": 1500, "bidirectional": True,
                    }
                ],
            }
        ),
        encoding="utf-8",
    )
    metadata, graph = load_dataset(path)
    assert metadata.id == "x"
    assert set(graph.edges) == {"ab", "ab__reverse"}
    assert graph.edge("ab__reverse").source == "b"


def test_loader_orients_geometry_for_forward_and_generated_reverse(tmp_path):
    path = tmp_path / "geometry.json"
    path.write_text(
        json.dumps(
            {
                "metadata": {"id": "geometry", "name": "Geometry"},
                "nodes": [
                    {"id": "a", "name": "A", "lat": 16.0, "lon": 108.0},
                    {"id": "b", "name": "B", "lat": 16.01, "lon": 108.01},
                ],
                "edges": [
                    {
                        "id": "ab",
                        "source": "a",
                        "target": "b",
                        "distance_m": 1600,
                        "bidirectional": True,
                        "attributes": {
                            "geometry": [
                                [108.01, 16.01], [108.005, 16.005], [108.0, 16.0]
                            ]
                        },
                    }
                ],
            }
        ),
        encoding="utf-8",
    )
    _, graph = load_dataset(path)
    assert graph.edge_coordinates("ab") == [
        [108.0, 16.0], [108.005, 16.005], [108.01, 16.01]
    ]
    assert graph.edge_coordinates("ab__reverse") == [
        [108.01, 16.01], [108.005, 16.005], [108.0, 16.0]
    ]


def test_loader_reports_unknown_node_reference(tmp_path):
    path = tmp_path / "invalid.json"
    path.write_text(
        json.dumps(
            {
                "metadata": {"id": "x", "name": "X"},
                "nodes": [{"id": "a", "name": "A", "lat": 16, "lon": 108}],
                "edges": [
                    {"id": "bad", "source": "a", "target": "missing", "distance_m": 1}
                ],
            }
        ),
        encoding="utf-8",
    )
    with pytest.raises(DatasetLoadError, match="unknown target"):
        load_dataset(path)


def test_loader_preserves_explicit_traversability(tmp_path):
    path = tmp_path / "traversability.json"
    path.write_text(
        json.dumps(
            {
                "metadata": {"id": "delivery", "name": "Delivery"},
                "nodes": [
                    {"id": "hub", "name": "Hub", "lat": 10.77, "lon": 106.68},
                    {"id": "stop", "name": "Stop", "lat": 10.78, "lon": 106.69},
                ],
                "edges": [
                    {
                        "id": "restricted",
                        "source": "hub",
                        "target": "stop",
                        "distance_m": 1500,
                        "traversable": False,
                    }
                ],
            }
        ),
        encoding="utf-8",
    )

    _, graph = load_dataset(path)

    assert graph.edge("restricted").traversable is False
