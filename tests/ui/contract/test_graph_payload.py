"""Graph payload contract: jsonschema vs MAP_CONTRACT.md § 2 + GUI_ROADMAP § 11.

Every key the frontend depends on is pinned here; `additionalProperties: false`
turns any future field rename into a test failure (MAP_CONTRACT.md § 6).
"""

from __future__ import annotations

import jsonschema

from ui.service import graphs

GRAPH_PAYLOAD_SCHEMA = {
    "$schema": "https://json-schema.org/draft/2020-12/schema",
    "type": "object",
    "required": ["graph", "bbox", "metadata"],
    "properties": {
        "graph": {
            "type": "object",
            "required": ["nodes", "edges", "geojson"],
            "properties": {
                "nodes": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "required": [
                            "attributes",
                            "id",
                            "kind",
                            "latitude",
                            "longitude",
                            "name",
                        ],
                        "properties": {
                            "id": {"type": "string"},
                            "name": {"type": "string"},
                            "latitude": {"type": "number"},
                            "longitude": {"type": "number"},
                            "kind": {"type": "string"},
                            "attributes": {"type": "object"},
                        },
                        "additionalProperties": False,
                    },
                },
                "edges": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "required": [
                            "attributes",
                            "congestion",
                            "direction",
                            "distance_km",
                            "edge_id",
                            "end",
                            "risk",
                            "road_class",
                            "road_name",
                            "road_path",
                            "start",
                            "time_min",
                        ],
                        "properties": {
                            "edge_id": {"type": "string"},
                            "start": {"type": "string"},
                            "end": {"type": "string"},
                            "distance_km": {"type": "number"},
                            "time_min": {"type": "number"},
                            "congestion": {"type": "number"},
                            "risk": {"type": "number"},
                            "direction": {
                                "type": "string",
                                "enum": ["one-way", "two-way"],
                            },
                            "road_path": {
                                "type": "array",
                                "items": {"type": "string"},
                            },
                            "road_name": {"type": "string"},
                            "road_class": {"type": "string"},
                            "attributes": {"type": "object"},
                        },
                        "additionalProperties": False,
                    },
                },
                "geojson": {
                    "type": "object",
                    "required": ["type", "features"],
                    "properties": {
                        "type": {"const": "FeatureCollection"},
                        "features": {
                            "type": "array",
                            "items": {
                                "type": "object",
                                "required": ["type", "geometry", "properties"],
                                "properties": {
                                    "type": {"const": "Feature"},
                                    "geometry": {
                                        "type": "object",
                                        "required": ["type", "coordinates"],
                                        "properties": {
                                            "type": {
                                                "enum": ["Point", "LineString"]
                                            },
                                            "coordinates": {
                                                "type": "array",
                                                "items": {
                                                    "anyOf": [
                                                        {"type": "number"},
                                                        {
                                                            "type": "array",
                                                            "items": {
                                                                "type": "number"
                                                            },
                                                        },
                                                    ]
                                                },
                                            },
                                        },
                                        "additionalProperties": False,
                                    },
                                    "properties": {"type": "object"},
                                },
                                "additionalProperties": False,
                            },
                        },
                    },
                    "additionalProperties": False,
                },
            },
            "additionalProperties": False,
        },
        "bbox": {
            "type": "array",
            "items": {"type": "number"},
            "minItems": 4,
            "maxItems": 4,
        },
        "metadata": {
            "type": "object",
            "required": ["schema_version", "node_count", "edge_count"],
            "properties": {
                "schema_version": {"type": "string"},
                "node_count": {"type": "integer"},
                "edge_count": {"type": "integer"},
            },
            "additionalProperties": False,
        },
    },
    "additionalProperties": False,
}


def test_payload_matches_map_contract_schema() -> None:
    jsonschema.validate(graphs.get_graph_payload(), GRAPH_PAYLOAD_SCHEMA)


def test_payload_counts_match_roadmap_section_11() -> None:
    payload = graphs.get_graph_payload()
    assert payload["metadata"]["node_count"] == 31
    assert payload["metadata"]["edge_count"] == 70


def test_node_ids_follow_poi_convention() -> None:
    nodes = graphs.get_graph_payload()["graph"]["nodes"]
    assert nodes
    assert all(node["id"].startswith("poi_") for node in nodes)


def test_geojson_point_coordinates_are_lon_lat() -> None:
    payload = graphs.get_graph_payload()
    by_id = {node["id"]: node for node in payload["graph"]["nodes"]}
    for feature in payload["graph"]["geojson"]["features"]:
        if feature["geometry"]["type"] != "Point":
            continue
        node = by_id[feature["properties"]["id"]]
        assert feature["geometry"]["coordinates"] == [
            node["longitude"],
            node["latitude"],
        ]


def test_bbox_is_ordered_lat_lon_bounds() -> None:
    bbox = graphs.get_graph_payload()["bbox"]
    assert len(bbox) == 4
    assert bbox[0] < bbox[2]
    assert bbox[1] < bbox[3]
