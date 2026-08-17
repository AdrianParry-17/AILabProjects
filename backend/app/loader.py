"""Validated JSON dataset loader."""

from __future__ import annotations

import json
from math import isfinite
from pathlib import Path
from typing import Any

from .domain import (
    DatasetMetadata,
    DirectedEdge,
    GraphNode,
    GraphValidationError,
    RoadGraph,
)


class DatasetLoadError(GraphValidationError):
    """Raised when a dataset cannot be read or has an invalid schema."""


def _required(mapping: dict[str, Any], key: str, context: str) -> Any:
    if key not in mapping:
        raise DatasetLoadError(f"Missing {key!r} in {context}")
    return mapping[key]


def _mapping(value: Any, context: str) -> dict[str, Any]:
    if not isinstance(value, dict):
        raise DatasetLoadError(f"{context} must be an object")
    return value


def _optional_bbox(value: Any) -> tuple[float, float, float, float] | None:
    if value is None:
        return None
    if not isinstance(value, list) or len(value) != 4:
        raise DatasetLoadError("metadata.bbox must be [south, west, north, east]")
    try:
        result = tuple(float(item) for item in value)
    except (TypeError, ValueError) as exc:
        raise DatasetLoadError("metadata.bbox values must be numbers") from exc
    if not all(isfinite(item) for item in result):
        raise DatasetLoadError("metadata.bbox values must be finite")
    return result  # type: ignore[return-value]


def _normalize_geometry(
    attributes: dict[str, Any],
    source: GraphNode,
    target: GraphNode,
    context: str,
) -> dict[str, Any]:
    """Validate, orient and endpoint-anchor an optional edge polyline."""

    normalized = dict(attributes)
    raw_geometry = normalized.get("geometry")
    if raw_geometry is None:
        return normalized
    if not isinstance(raw_geometry, list) or len(raw_geometry) < 2:
        raise DatasetLoadError(f"{context}.attributes.geometry must contain at least 2 points")
    geometry: list[list[float]] = []
    for index, raw_point in enumerate(raw_geometry):
        if not isinstance(raw_point, (list, tuple)) or len(raw_point) < 2:
            raise DatasetLoadError(
                f"{context}.attributes.geometry[{index}] must be [longitude, latitude]"
            )
        try:
            lon, lat = float(raw_point[0]), float(raw_point[1])
        except (TypeError, ValueError) as exc:
            raise DatasetLoadError(
                f"{context}.attributes.geometry[{index}] coordinates must be numbers"
            ) from exc
        if not (isfinite(lon) and isfinite(lat) and -180 <= lon <= 180 and -90 <= lat <= 90):
            raise DatasetLoadError(
                f"{context}.attributes.geometry[{index}] has invalid coordinates"
            )
        geometry.append([lon, lat])

    source_position = [source.lon, source.lat]
    target_position = [target.lon, target.lat]

    def squared_distance(first: list[float], second: list[float]) -> float:
        return (first[0] - second[0]) ** 2 + (first[1] - second[1]) ** 2

    forward_error = squared_distance(geometry[0], source_position) + squared_distance(
        geometry[-1], target_position
    )
    reverse_error = squared_distance(geometry[-1], source_position) + squared_distance(
        geometry[0], target_position
    )
    if reverse_error + 1e-18 < forward_error:
        geometry.reverse()

    # Contracted OSM polylines normally match exactly. Anchoring within the
    # loader also makes imported datasets safe for seamless route concatenation.
    if squared_distance(geometry[0], source_position) > 1e-18:
        geometry.insert(0, source_position)
    else:
        geometry[0] = source_position
    if squared_distance(geometry[-1], target_position) > 1e-18:
        geometry.append(target_position)
    else:
        geometry[-1] = target_position
    normalized["geometry"] = geometry
    return normalized


def load_dataset(path: str | Path) -> tuple[DatasetMetadata, RoadGraph]:
    dataset_path = Path(path)
    try:
        raw = json.loads(dataset_path.read_text(encoding="utf-8"))
    except FileNotFoundError as exc:
        raise DatasetLoadError(f"Dataset file not found: {dataset_path}") from exc
    except json.JSONDecodeError as exc:
        raise DatasetLoadError(
            f"Dataset JSON is invalid at line {exc.lineno}, column {exc.colno}: {exc.msg}"
        ) from exc
    except OSError as exc:
        raise DatasetLoadError(f"Cannot read dataset {dataset_path}: {exc}") from exc

    root = _mapping(raw, "dataset root")
    meta_raw = _mapping(_required(root, "metadata", "dataset root"), "metadata")
    metadata = DatasetMetadata(
        id=str(_required(meta_raw, "id", "metadata")),
        name=str(_required(meta_raw, "name", "metadata")),
        city=str(meta_raw.get("city", "Thành phố Hồ Chí Minh")),
        country=str(meta_raw.get("country", "Việt Nam")),
        version=str(meta_raw.get("version", "1")),
        source=str(meta_raw.get("source", "unknown")),
        description=str(meta_raw.get("description", "")),
        generated_at=str(meta_raw["generated_at"]) if meta_raw.get("generated_at") else None,
        disclaimer=str(meta_raw["disclaimer"]) if meta_raw.get("disclaimer") else None,
        source_url=str(meta_raw["source_url"]) if meta_raw.get("source_url") else None,
        license=str(meta_raw["license"]) if meta_raw.get("license") else None,
        attribution=str(meta_raw["attribution"]) if meta_raw.get("attribution") else None,
        osm_base_timestamp=(
            str(meta_raw["osm_base_timestamp"]) if meta_raw.get("osm_base_timestamp") else None
        ),
        overpass_query=str(meta_raw["overpass_query"]) if meta_raw.get("overpass_query") else None,
        network_filter=str(meta_raw["network_filter"]) if meta_raw.get("network_filter") else None,
        bbox=_optional_bbox(meta_raw.get("bbox")),
        stats=_mapping(meta_raw.get("stats", {}), "metadata.stats"),
    )

    nodes_raw = _required(root, "nodes", "dataset root")
    edges_raw = _required(root, "edges", "dataset root")
    if not isinstance(nodes_raw, list) or not isinstance(edges_raw, list):
        raise DatasetLoadError("nodes and edges must be arrays")

    nodes: list[GraphNode] = []
    for index, item in enumerate(nodes_raw):
        value = _mapping(item, f"nodes[{index}]")
        try:
            nodes.append(
                GraphNode(
                    id=str(_required(value, "id", f"nodes[{index}]")),
                    name=str(_required(value, "name", f"nodes[{index}]")),
                    kind=str(value.get("kind", "intersection")),
                    lat=float(_required(value, "lat", f"nodes[{index}]")),
                    lon=float(_required(value, "lon", f"nodes[{index}]")),
                    attributes=_mapping(value.get("attributes", {}), f"nodes[{index}].attributes"),
                )
            )
        except (TypeError, ValueError) as exc:
            raise DatasetLoadError(f"Invalid nodes[{index}]: {exc}") from exc

    node_lookup = {node.id: node for node in nodes}
    directed_edges: list[DirectedEdge] = []
    for index, item in enumerate(edges_raw):
        value = _mapping(item, f"edges[{index}]")
        context = f"edges[{index}]"
        try:
            base_id = str(_required(value, "id", context))
            source = str(_required(value, "source", context))
            target = str(_required(value, "target", context))
            if source not in node_lookup:
                raise DatasetLoadError(f"{context} references unknown source {source!r}")
            if target not in node_lookup:
                raise DatasetLoadError(f"{context} references unknown target {target!r}")
            raw_attributes = _mapping(value.get("attributes", {}), f"{context}.attributes")
            common: dict[str, Any] = {
                "distance_m": float(_required(value, "distance_m", context)),
                "speed_kph": float(value.get("speed_kph", 35)),
                "road_name": str(value.get("road_name", "Unnamed road")),
                "road_class": str(value.get("road_class", "local")),
                "risk": float(value.get("risk", 0.1)),
                "traversable": bool(value.get("traversable", True)),
            }
            directed_edges.append(
                DirectedEdge(
                    id=base_id,
                    source=source,
                    target=target,
                    attributes=_normalize_geometry(
                        raw_attributes, node_lookup[source], node_lookup[target], context
                    ),
                    **common,
                )
            )
            if bool(value.get("bidirectional", False)):
                reverse_id = str(value.get("reverse_id", f"{base_id}__reverse"))
                reverse_common = dict(common)
                reverse_common["speed_kph"] = float(
                    value.get("reverse_speed_kph", common["speed_kph"])
                )
                directed_edges.append(
                    DirectedEdge(
                        id=reverse_id,
                        source=target,
                        target=source,
                        attributes=_normalize_geometry(
                            raw_attributes,
                            node_lookup[target],
                            node_lookup[source],
                            f"{context} reverse",
                        ),
                        **reverse_common,
                    )
                )
        except (TypeError, ValueError) as exc:
            raise DatasetLoadError(f"Invalid {context}: {exc}") from exc

    try:
        return metadata, RoadGraph(nodes, directed_edges)
    except GraphValidationError as exc:
        raise DatasetLoadError(f"Invalid graph: {exc}") from exc
