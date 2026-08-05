from __future__ import annotations

import copy
import importlib.util
from pathlib import Path

import pytest


SCRIPT_PATH = Path(__file__).resolve().parents[2] / "scripts" / "import_hcmc_snapshot.py"
SPEC = importlib.util.spec_from_file_location("import_hcmc_snapshot", SCRIPT_PATH)
assert SPEC is not None and SPEC.loader is not None
IMPORTER = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(IMPORTER)


def _source_export() -> dict:
    nodes = [
        {
            "id": f"n{index}",
            "name": f"Node {index}",
            "latitude": 10.75 + index * 0.0001,
            "longitude": 106.68 + index * 0.0001,
            "kind": "delivery_market" if index < 2 else "intersection",
            "attributes": {},
        }
        for index in range(20)
    ]

    def edge(start: int, end: int, direction: str = "one-way") -> dict:
        return {
            "start": f"n{start}",
            "end": f"n{end}",
            "direction": direction,
            "distance_km": 0.1,
            "time_min": 0.13,
            "congestion": 2.0,
            "risk": 1.0,
            "road_name": "Delivery Road",
            "road_class": "primary",
            "attributes": {
                "length_geometry": [
                    [nodes[start]["longitude"], nodes[start]["latitude"]],
                    [nodes[end]["longitude"], nodes[end]["latitude"]],
                ]
            },
        }

    edges = [edge(index, (index + 1) % 20) for index in range(20)]
    for index in range(5):
        edges.extend(
            [edge(index, index + 10, "two-way"), edge(index + 10, index, "two-way")]
        )
    return {
        "metadata": {
            "id": "source",
            "name": "Source",
            "city": "Ho Chi Minh City",
            "country": "Việt Nam",
            "source": "OpenStreetMap contributors",
            "stats": {},
        },
        "nodes": nodes,
        "edges": edges,
    }


def test_migration_converts_schema_without_expanding_directed_source_rows():
    canonical = IMPORTER.migrate(
        _source_export(),
        raw_way_speeds={},
        processed_sha256="PROCESSED",
        raw_sha256="RAW",
    )

    assert len(canonical["nodes"]) == 20
    assert len(canonical["edges"]) == 30
    assert all(edge["bidirectional"] is False for edge in canonical["edges"])
    assert all(edge["traversable"] is True for edge in canonical["edges"])
    assert all(edge["risk"] == 0.2 for edge in canonical["edges"])
    assert all(edge["speed_kph"] == 45 for edge in canonical["edges"])
    assert "latitude" not in canonical["nodes"][0]
    assert canonical["nodes"][0]["lat"] == 10.75
    assert "length_geometry" not in canonical["edges"][0]["attributes"]
    assert "geometry" in canonical["edges"][0]["attributes"]
    assert canonical["metadata"]["stats"]["source_one_way_arcs"] == 20
    assert canonical["metadata"]["stats"]["source_two_way_arcs"] == 10
    assert canonical["metadata"]["stats"]["processed_source_sha256"] == "PROCESSED"
    assert canonical["metadata"]["stats"]["raw_source_sha256"] == "RAW"


def test_migration_rejects_two_way_row_without_explicit_reverse():
    source = _source_export()
    source["edges"][21] = copy.deepcopy(source["edges"][21])
    source["edges"][21]["start"] = "n11"
    source["edges"][21]["end"] = "n0"

    with pytest.raises(IMPORTER.ImportValidationError, match="explicit reverse records"):
        IMPORTER.migrate(source, raw_way_speeds={})


def test_migration_rejects_risk_that_cannot_be_normalized_to_fraction():
    source = _source_export()
    source["edges"][0]["risk"] = 5.01

    with pytest.raises(IMPORTER.ImportValidationError, match="0-5 scale"):
        IMPORTER.migrate(source, raw_way_speeds={})
