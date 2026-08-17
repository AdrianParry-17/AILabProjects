"""Migrate the teammate HCMC graph export into the app's canonical dataset.

The source export is deliberately treated as an import artifact. Runtime code
only reads the generated snapshot under ``backend/data``; it never imports from
or depends on ``backend/data-tmp``.

The source already contains directed arcs. In particular, every source record
labelled ``two-way`` has a separate reverse record, so this importer must not
expand those rows a second time.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import re
from collections import Counter
from math import isfinite
from pathlib import Path
from typing import Any


PROJECT_ROOT = Path(__file__).resolve().parent.parent
DEFAULT_INPUT = PROJECT_ROOT / "backend" / "data-tmp" / "processed" / "graph.json"
DEFAULT_RAW_INPUT = PROJECT_ROOT / "backend" / "data-tmp" / "raw" / "hcmc_overpass.json"
DEFAULT_OUTPUT = PROJECT_ROOT / "backend" / "data" / "hcmc_delivery_osm_snapshot.json"
ROAD_SPEED_FALLBACKS = {
    "primary": 45.0,
    "secondary": 35.0,
    "tertiary": 30.0,
    "service": 20.0,
}
MAXSPEED_PATTERN = re.compile(r"^\s*(\d+(?:\.\d+)?)\s*(mph|km/?h|kph)?\s*$", re.I)


class ImportValidationError(ValueError):
    """Raised when the temporary export cannot be migrated without guessing."""


def _object(value: Any, context: str) -> dict[str, Any]:
    if not isinstance(value, dict):
        raise ImportValidationError(f"{context} must be an object")
    return value


def _array(value: Any, context: str) -> list[Any]:
    if not isinstance(value, list):
        raise ImportValidationError(f"{context} must be an array")
    return value


def _text(value: Any, context: str) -> str:
    result = str(value).strip()
    if not result:
        raise ImportValidationError(f"{context} cannot be empty")
    return result


def _number(value: Any, context: str, *, minimum: float | None = None) -> float:
    try:
        result = float(value)
    except (TypeError, ValueError) as exc:
        raise ImportValidationError(f"{context} must be numeric") from exc
    if not isfinite(result):
        raise ImportValidationError(f"{context} must be finite")
    if minimum is not None and result < minimum:
        raise ImportValidationError(f"{context} must be >= {minimum}")
    return result


def _strongly_connected_components(
    node_ids: list[str], directed_pairs: list[tuple[str, str]]
) -> list[list[str]]:
    """Return deterministic SCCs with an iterative Kosaraju traversal."""

    adjacency = {node_id: [] for node_id in node_ids}
    reverse = {node_id: [] for node_id in node_ids}
    for source, target in directed_pairs:
        adjacency[source].append(target)
        reverse[target].append(source)

    seen: set[str] = set()
    finish_order: list[str] = []
    for root in node_ids:
        if root in seen:
            continue
        seen.add(root)
        stack: list[tuple[str, int]] = [(root, 0)]
        while stack:
            node_id, index = stack[-1]
            if index < len(adjacency[node_id]):
                neighbor = adjacency[node_id][index]
                stack[-1] = (node_id, index + 1)
                if neighbor not in seen:
                    seen.add(neighbor)
                    stack.append((neighbor, 0))
            else:
                finish_order.append(node_id)
                stack.pop()

    seen.clear()
    components: list[list[str]] = []
    for root in reversed(finish_order):
        if root in seen:
            continue
        seen.add(root)
        component: list[str] = []
        stack = [root]
        while stack:
            node_id = stack.pop()
            component.append(node_id)
            for neighbor in reverse[node_id]:
                if neighbor not in seen:
                    seen.add(neighbor)
                    stack.append(neighbor)
        components.append(component)
    return sorted(components, key=lambda item: (-len(item), item[0]))


def _parse_maxspeed(value: Any) -> float | None:
    """Parse explicit numeric OSM maxspeed values; ignore symbolic tags."""

    speeds: list[float] = []
    for part in str(value or "").split(";"):
        match = MAXSPEED_PATTERN.fullmatch(part)
        if not match:
            return None
        speed = float(match.group(1))
        if (match.group(2) or "").lower() == "mph":
            speed *= 1.609344
        if not 5 <= speed <= 130:
            return None
        speeds.append(speed)
    return min(speeds) if speeds else None


def _raw_way_speeds(raw: dict[str, Any]) -> dict[int, float | None]:
    elements = _array(raw.get("elements"), "raw.elements")
    result: dict[int, float | None] = {}
    for index, raw_element in enumerate(elements):
        element = _object(raw_element, f"raw.elements[{index}]")
        if element.get("type") != "way":
            continue
        try:
            way_id = int(element["id"])
        except (KeyError, TypeError, ValueError) as exc:
            raise ImportValidationError(f"raw.elements[{index}] has an invalid way id") from exc
        tags = _object(element.get("tags", {}), f"raw.elements[{index}].tags")
        result[way_id] = _parse_maxspeed(tags.get("maxspeed"))
    return result


def migrate(
    source: dict[str, Any],
    *,
    raw_way_speeds: dict[int, float | None] | None = None,
    processed_sha256: str | None = None,
    raw_sha256: str | None = None,
) -> dict[str, Any]:
    metadata = _object(source.get("metadata"), "metadata")
    city = _text(metadata.get("city"), "metadata.city")
    if city.casefold() not in {"ho chi minh city", "thành phố hồ chí minh", "hồ chí minh"}:
        raise ImportValidationError(
            f"Expected a Ho Chi Minh City export, received metadata.city={city!r}"
        )

    raw_nodes = _array(source.get("nodes"), "nodes")
    raw_edges = _array(source.get("edges"), "edges")
    if len(raw_nodes) < 20 or len(raw_edges) < 30:
        raise ImportValidationError("Dataset does not satisfy the lab's minimum graph size")

    node_ids: set[str] = set()
    nodes: list[dict[str, Any]] = []
    for index, raw_value in enumerate(raw_nodes):
        value = _object(raw_value, f"nodes[{index}]")
        node_id = _text(value.get("id"), f"nodes[{index}].id")
        if node_id in node_ids:
            raise ImportValidationError(f"Duplicate node id: {node_id}")
        node_ids.add(node_id)
        latitude = _number(value.get("latitude"), f"nodes[{index}].latitude")
        longitude = _number(value.get("longitude"), f"nodes[{index}].longitude")
        if not -90 <= latitude <= 90 or not -180 <= longitude <= 180:
            raise ImportValidationError(f"nodes[{index}] has invalid coordinates")
        kind = _text(value.get("kind", "intersection"), f"nodes[{index}].kind")
        attributes = dict(_object(value.get("attributes", {}), f"nodes[{index}].attributes"))
        if kind.startswith("delivery_"):
            attributes["delivery_destination"] = True
            attributes["delivery_category"] = kind.removeprefix("delivery_")
        nodes.append(
            {
                "id": node_id,
                "name": _text(value.get("name"), f"nodes[{index}].name"),
                "kind": kind,
                "lat": latitude,
                "lon": longitude,
                "attributes": attributes,
            }
        )

    directed_pairs: list[tuple[str, str]] = []
    edges: list[dict[str, Any]] = []
    direction_counts: Counter[str] = Counter()
    endpoint_counts: Counter[tuple[str, str]] = Counter()
    zero_time_fallbacks = 0
    for index, raw_value in enumerate(raw_edges):
        value = _object(raw_value, f"edges[{index}]")
        source_id = _text(value.get("start"), f"edges[{index}].start")
        target_id = _text(value.get("end"), f"edges[{index}].end")
        if source_id not in node_ids or target_id not in node_ids:
            raise ImportValidationError(
                f"edges[{index}] references an unknown endpoint: {source_id!r} -> {target_id!r}"
            )
        if source_id == target_id:
            raise ImportValidationError(f"edges[{index}] is a self-loop")
        direction = _text(value.get("direction"), f"edges[{index}].direction")
        if direction not in {"one-way", "two-way"}:
            raise ImportValidationError(f"edges[{index}] has unsupported direction {direction!r}")

        distance_km = _number(
            value.get("distance_km"), f"edges[{index}].distance_km", minimum=0.000001
        )
        time_min = _number(value.get("time_min"), f"edges[{index}].time_min", minimum=0)
        road_class = _text(value.get("road_class", "service"), f"edges[{index}].road_class")
        raw_attributes = _object(value.get("attributes", {}), f"edges[{index}].attributes")
        osm_way_ids = raw_attributes.get("osm_way_ids", [])
        referenced_way_ids = (
            [int(item) for item in osm_way_ids]
            if isinstance(osm_way_ids, list)
            else []
        )
        tagged_speeds = (
            [raw_way_speeds.get(way_id) for way_id in referenced_way_ids]
            if raw_way_speeds is not None and referenced_way_ids
            else []
        )
        if tagged_speeds and all(speed is not None for speed in tagged_speeds):
            speed_kph = min(float(speed) for speed in tagged_speeds if speed is not None)
            speed_provenance = "minimum explicit OSM maxspeed across contracted ways"
        else:
            speed_kph = ROAD_SPEED_FALLBACKS.get(road_class, 25.0)
            speed_provenance = f"documented {road_class} class fallback"
        if time_min == 0:
            zero_time_fallbacks += 1
        reconstructed_time = round(distance_km / speed_kph * 60.0, 2)
        if abs(reconstructed_time - time_min) > 0.011:
            raise ImportValidationError(
                f"edges[{index}] time/speed reconstruction differs by more than 0.01 min: "
                f"source={time_min}, reconstructed={reconstructed_time}"
            )

        congestion_score = _number(
            value.get("congestion"), f"edges[{index}].congestion", minimum=1
        )
        if congestion_score > 5:
            raise ImportValidationError(f"edges[{index}].congestion must use the source 1-5 scale")
        risk_score = _number(value.get("risk"), f"edges[{index}].risk", minimum=0)
        if risk_score > 5:
            raise ImportValidationError(f"edges[{index}].risk must use the source 0-5 scale")

        attributes = dict(raw_attributes)
        geometry = attributes.pop("length_geometry", None)
        if geometry is not None:
            attributes["geometry"] = geometry
        attributes.update(
            {
                "source_direction": direction,
                "base_congestion": congestion_score,
                "source_congestion_score": congestion_score,
                "source_time_min": time_min,
                "source_risk_score": risk_score,
                "source_risk_scale": 5.0,
                "source_record_index": index,
                "speed_provenance": speed_provenance,
            }
        )
        directed_pairs.append((source_id, target_id))
        endpoint_counts[(source_id, target_id)] += 1
        direction_counts[direction] += 1
        edges.append(
            {
                "id": f"hcmc_edge_{index:04d}",
                "source": source_id,
                "target": target_id,
                "distance_m": round(distance_km * 1000.0, 6),
                "speed_kph": round(speed_kph, 6),
                "road_name": _text(
                    value.get("road_name", "Đường chưa đặt tên"),
                    f"edges[{index}].road_name",
                ),
                "road_class": road_class,
                # The source uses the lab's fixed 0-5 risk score; the app cost
                # model uses a [0,1] fraction. Never normalize by dataset max.
                "risk": round(risk_score / 5.0, 6),
                "traversable": True,
                # Every input row is already one directed arc. Never expand it.
                "bidirectional": False,
                "attributes": attributes,
            }
        )

    two_way_pairs_missing_reverse = [
        (source_id, target_id)
        for edge, (source_id, target_id) in zip(edges, directed_pairs)
        if edge["attributes"]["source_direction"] == "two-way"
        and endpoint_counts[(target_id, source_id)] == 0
    ]
    if two_way_pairs_missing_reverse:
        sample = two_way_pairs_missing_reverse[0]
        raise ImportValidationError(
            "Source claims two-way arcs without explicit reverse records; refusing to guess "
            f"for {sample[0]!r} -> {sample[1]!r}"
        )

    components = _strongly_connected_components(list(node_ids), directed_pairs)
    primary_component = set(components[0])
    for node in nodes:
        node["attributes"]["routing_component"] = (
            "primary" if node["id"] in primary_component else "peripheral"
        )

    delivery_pois = [node for node in nodes if node["kind"].startswith("delivery_")]
    primary_delivery_pois = [node for node in delivery_pois if node["id"] in primary_component]
    recommended_start = next(
        (node for node in primary_delivery_pois if node["id"] == "poi_way_152994798"),
        primary_delivery_pois[0],
    )
    recommended_goal = next(
        (node for node in primary_delivery_pois if node["id"] == "poi_way_39514795"),
        primary_delivery_pois[1],
    )

    source_stats = dict(_object(metadata.get("stats", {}), "metadata.stats"))
    canonical_stats = {
        **source_stats,
        "canonical_nodes": len(nodes),
        "canonical_directed_edges": len(edges),
        "source_one_way_arcs": direction_counts["one-way"],
        "source_two_way_arcs": direction_counts["two-way"],
        "parallel_endpoint_pairs": sum(count > 1 for count in endpoint_counts.values()),
        "strongly_connected_components": len(components),
        "largest_strongly_connected_component": len(primary_component),
        "delivery_pois": len(delivery_pois),
        "delivery_pois_in_primary_component": len(primary_delivery_pois),
        "zero_time_speed_fallbacks": zero_time_fallbacks,
        "recommended_start_id": recommended_start["id"],
        "recommended_goal_id": recommended_goal["id"],
    }
    if processed_sha256:
        canonical_stats["processed_source_sha256"] = processed_sha256
    if raw_sha256:
        canonical_stats["raw_source_sha256"] = raw_sha256
    canonical_metadata = {
        "id": "hcmc-city-centre-delivery-osm-2026",
        "name": "Ho Chi Minh City Delivery Route Search Graph",
        "city": "Thành phố Hồ Chí Minh",
        "country": _text(metadata.get("country", "Việt Nam"), "metadata.country"),
        "version": "2.0.0",
        "source": _text(metadata.get("source"), "metadata.source"),
        "source_url": metadata.get("source_url"),
        "overpass_query": metadata.get("overpass_query"),
        "osm_base_timestamp": metadata.get("osm_base_timestamp"),
        "generated_at": metadata.get("generated_at"),
        "bbox": metadata.get("bbox"),
        "network_filter": metadata.get("network_filter"),
        "description": (
            "Contracted directed street topology and delivery POIs for an educational "
            "courier route-search laboratory in central Ho Chi Minh City."
        ),
        "disclaimer": (
            "OSM topology and tags are snapshot data. Travel time, congestion, road "
            "disruption, flood susceptibility and risk are deterministic educational "
            "estimates—not live navigation or dispatch data."
        ),
        "license": metadata.get("license", "ODbL-1.0"),
        "attribution": metadata.get("attribution", "© OpenStreetMap contributors"),
        "stats": canonical_stats,
    }
    return {"metadata": canonical_metadata, "nodes": nodes, "edges": edges}


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", type=Path, default=DEFAULT_INPUT)
    parser.add_argument("--raw-input", type=Path, default=DEFAULT_RAW_INPUT)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    args = parser.parse_args()

    try:
        processed_bytes = args.input.read_bytes()
        source = json.loads(processed_bytes.decode("utf-8"))
    except FileNotFoundError as exc:
        raise SystemExit(f"Input export not found: {args.input}") from exc
    except json.JSONDecodeError as exc:
        raise SystemExit(
            f"Invalid source JSON at line {exc.lineno}, column {exc.colno}: {exc.msg}"
        ) from exc

    try:
        raw_bytes = args.raw_input.read_bytes()
        raw_source = json.loads(raw_bytes.decode("utf-8"))
    except FileNotFoundError as exc:
        raise SystemExit(f"Raw Overpass export not found: {args.raw_input}") from exc
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise SystemExit(f"Invalid raw Overpass JSON: {exc}") from exc

    try:
        canonical = migrate(
            _object(source, "dataset root"),
            raw_way_speeds=_raw_way_speeds(_object(raw_source, "raw dataset root")),
            processed_sha256=hashlib.sha256(processed_bytes).hexdigest().upper(),
            raw_sha256=hashlib.sha256(raw_bytes).hexdigest().upper(),
        )
    except ImportValidationError as exc:
        raise SystemExit(f"Import validation failed: {exc}") from exc

    args.output.parent.mkdir(parents=True, exist_ok=True)
    # Write bytes explicitly so the canonical snapshot is identical on Windows,
    # macOS, and Linux instead of inheriting platform-native line endings.
    args.output.write_bytes(
        (json.dumps(canonical, ensure_ascii=False, indent=2) + "\n").encode("utf-8")
    )
    stats = canonical["metadata"]["stats"]
    print(
        f"Wrote {args.output}: {stats['canonical_nodes']} nodes, "
        f"{stats['canonical_directed_edges']} directed edges, "
        f"{stats['delivery_pois']} delivery POIs"
    )


if __name__ == "__main__":
    main()
