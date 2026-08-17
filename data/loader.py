"""Load the single JSON dataset through its Pydantic model.

`load_graph` validates the schema version on every call (unless `validate=False`),
mirroring `delivery.loader.load_delivery_graph`. `data/processed/graph.json` is the
source of truth for the road layer; its `metadata.schema_version` must match the
single source in `config.settings.SCHEMA_VERSION` (CONVENTION.md § 11).
The default path comes from `config.paths`.
"""

import json
from pathlib import Path

from config.paths import ROAD_GRAPH_PATH
from config.settings import SCHEMA_VERSION
from shared.validators import ensure_schema_version

from .models import GraphData

DATA_PATH = ROAD_GRAPH_PATH


def validate_schema_version(metadata: dict) -> None:
    """Raise when `metadata["schema_version"]` disagrees with the shared version."""
    ensure_schema_version(
        metadata.get("schema_version", SCHEMA_VERSION), SCHEMA_VERSION, what="Road graph"
    )


def load_graph(path: Path | None = None, *, validate: bool = True) -> GraphData:
    target = path if path is not None else DATA_PATH
    raw = json.loads(target.read_text(encoding="utf-8"))
    if validate:
        validate_schema_version(raw.get("metadata", {}))
    return GraphData.model_validate(raw)


def load_metadata(path: Path | None = None) -> dict:
    target = path if path is not None else DATA_PATH
    return json.loads(target.read_text(encoding="utf-8")).get("metadata", {})
