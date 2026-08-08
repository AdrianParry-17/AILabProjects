"""Data-layer tests: default loader path and schema/version contract."""

from __future__ import annotations

from data.loader import DATA_PATH, load_graph, load_metadata
from data.models import SCHEMA_VERSION


def test_default_path_points_to_processed_graph() -> None:
    assert DATA_PATH.name == "graph.json"
    assert DATA_PATH.parent.name == "processed"


def test_load_graph_reads_committed_dataset() -> None:
    graph = load_graph()
    assert len(graph.nodes) >= 1000
    assert len(graph.edges) >= 2000


def test_load_metadata_matches_shared_schema_version() -> None:
    metadata = load_metadata()
    assert metadata["schema_version"] == SCHEMA_VERSION
