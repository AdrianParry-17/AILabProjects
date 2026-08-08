"""Build a compact, directed delivery-teaching graph from a bounded Overpass response.

Adapted from the reference project (AI-App-Map-Search) for the HCMC city-centre
delivery scenario. It contracts OSM shape points between junctions, preserves one-way
direction, retains OSM ids/geometry for provenance, snaps delivery POIs (markets,
supermarkets, bus stations) onto the retained road graph, and emits the dataset in the
project's agreed schema (data/models.py): distance_km / time_min / congestion / risk /
direction.

Traffic, congestion, flood and risk values are deterministic educational overlays, NOT
observations or live traffic from OpenStreetMap.

Example:
    python scripts/build_osm_snapshot.py --input data/raw/hcmc_overpass.json \
        --output data/processed/graph.json
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from collections import Counter, defaultdict, deque
from collections.abc import Iterable
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from config.defaults import (
    BBOX,
    CONGESTION_BASE,
    DEFAULT_SPEED,
    MIN_EDGES,
    MIN_NODES,
    POI_FILTER,
    RISK_BASE,
    ROAD_CLASSES,
)
from config.paths import RAW_OSM_PATH, ROAD_GRAPH_PATH
from config.settings import SCHEMA_VERSION
from shared.helpers import haversine_m, stable_fraction


def parse_speed(value: Any, fallback: float) -> float:
    if isinstance(value, list):
        value = value[0] if value else None
    if not value:
        return fallback
    match = re.search(r"(\d+(?:\.\d+)?)", str(value))
    if not match:
        return fallback
    speed = float(match.group(1))
    if "mph" in str(value).lower():
        speed *= 1.60934
    return min(90.0, max(10.0, speed))


def one_way_mode(tags: dict[str, Any]) -> int:
    value = str(tags.get("oneway", "")).lower()
    if value in {"-1", "reverse"}:
        return -1
    if value in {"yes", "true", "1"} or tags.get("junction") == "roundabout":
        return 1
    return 0


def largest_component(adjacency: dict[int, set[int]]) -> set[int]:
    unseen = set(adjacency)
    components: list[set[int]] = []
    while unseen:
        seed = next(iter(unseen))
        component = {seed}
        queue = deque([seed])
        unseen.remove(seed)
        while queue:
            current = queue.popleft()
            for neighbor in adjacency[current]:
                if neighbor in unseen:
                    unseen.remove(neighbor)
                    component.add(neighbor)
                    queue.append(neighbor)
        components.append(component)
    return max(components, key=len)


def feature_center(
    element: dict[str, Any], coordinates: dict[int, tuple[float, float]]
) -> tuple[float, float] | None:
    if element["type"] == "node":
        return float(element["lat"]), float(element["lon"])
    points = [
        coordinates[node_id]
        for node_id in element.get("nodes", [])
        if node_id in coordinates
    ]
    if not points:
        return None
    return sum(point[0] for point in points) / len(points), sum(
        point[1] for point in points
    ) / len(points)


def iter_pairs(values: Iterable[int]) -> Iterable[tuple[int, int]]:
    iterator = iter(values)
    try:
        previous = next(iterator)
    except StopIteration:
        return
    for current in iterator:
        yield previous, current
        previous = current


def build_snapshot(raw: dict[str, Any]) -> dict[str, Any]:
    elements = raw.get("elements", [])
    coordinates = {
        int(element["id"]): (float(element["lat"]), float(element["lon"]))
        for element in elements
        if element.get("type") == "node" and "lat" in element and "lon" in element
    }
    road_ways = [
        element
        for element in elements
        if element.get("type") == "way"
        and element.get("tags", {}).get("highway") in ROAD_CLASSES
    ]
    if not road_ways:
        raise ValueError(
            "The response contains no primary/secondary/tertiary road ways"
        )

    adjacency: dict[int, set[int]] = defaultdict(set)
    segment_records: dict[tuple[int, int], list[dict[str, Any]]] = defaultdict(list)
    incident_records: dict[int, list[dict[str, Any]]] = defaultdict(list)

    for way in road_ways:
        tags = way.get("tags", {})
        road_class = str(tags["highway"])
        record = {
            "way_id": int(way["id"]),
            "name": str(tags.get("name") or tags.get("ref") or "Đường chưa đặt tên"),
            "road_class": road_class,
            "speed_kph": parse_speed(tags.get("maxspeed"), DEFAULT_SPEED[road_class]),
            "mode": one_way_mode(tags),
            "bridge": str(tags.get("bridge", "")).lower()
            not in {"", "no", "false", "0"},
        }
        way_nodes = [
            int(value) for value in way.get("nodes", []) if int(value) in coordinates
        ]
        for source, target in iter_pairs(way_nodes):
            adjacency[source].add(target)
            adjacency[target].add(source)
            directional = {**record, "way_forward": (source, target)}
            segment_records[tuple(sorted((source, target)))].append(directional)
            incident_records[source].append(directional)
            incident_records[target].append(directional)

    component = largest_component(adjacency)
    adjacency = {
        node: {n for n in neighbors if n in component}
        for node, neighbors in adjacency.items()
        if node in component
    }
    junctions = {node for node, neighbors in adjacency.items() if len(neighbors) != 2}
    if not junctions:
        junctions.add(next(iter(component)))

    def direction_allowed(source: int, target: int) -> bool:
        records = segment_records[tuple(sorted((source, target)))]
        for record in records:
            forward = tuple(record["way_forward"]) == (source, target)
            if (
                record["mode"] == 0
                or (record["mode"] == 1 and forward)
                or (record["mode"] == -1 and not forward)
            ):
                return True
        return False

    collapsed_paths: list[list[int]] = []
    visited_segments: set[tuple[int, int]] = set()
    for origin in sorted(junctions):
        for first in sorted(adjacency[origin]):
            segment_key = tuple(sorted((origin, first)))
            if segment_key in visited_segments:
                continue
            path = [origin, first]
            visited_segments.add(segment_key)
            previous, current = origin, first
            safety = 0
            while current not in junctions:
                candidates = adjacency[current] - {previous}
                if not candidates:
                    break
                following = next(iter(candidates))
                key = tuple(sorted((current, following)))
                if key in visited_segments:
                    break
                path.append(following)
                visited_segments.add(key)
                previous, current = current, following
                safety += 1
                if safety > len(component):
                    raise RuntimeError(
                        "Cycle guard tripped while contracting the road graph"
                    )
            if len(path) >= 2 and path[-1] in junctions and path[0] != path[-1]:
                collapsed_paths.append(path)

    road_names_by_junction: dict[int, list[str]] = {}
    for node_id in junctions:
        names = [
            record["name"]
            for record in incident_records[node_id]
            if record["name"] != "Đường chưa đặt tên"
        ]
        road_names_by_junction[node_id] = [
            name for name, _ in Counter(names).most_common(3)
        ]

    nodes: list[dict[str, Any]] = []
    for node_id in sorted(junctions):
        names = road_names_by_junction[node_id]
        adjacent_records = incident_records[node_id]
        is_bridge_access = any(record["bridge"] for record in adjacent_records)
        if len(names) >= 2:
            display_name = f"{names[0]} × {names[1]}"
        elif names:
            display_name = f"Nút {names[0]}"
        else:
            display_name = f"Giao lộ OSM {node_id}"
        degree = len(adjacency[node_id])
        nodes.append(
            {
                "id": f"osm_{node_id}",
                "name": display_name,
                "latitude": round(coordinates[node_id][0], 7),
                "longitude": round(coordinates[node_id][1], 7),
                "kind": "bridge_access"
                if is_bridge_access
                else "gateway"
                if degree == 1
                else "intersection",
                "attributes": {
                    "osm_node_id": node_id,
                    "road_names": names,
                    "raw_degree": degree,
                },
            }
        )

    edges: list[dict[str, Any]] = []
    for path_index, path in enumerate(collapsed_paths):
        pairs = list(iter_pairs(path))
        distance = sum(
            haversine_m(coordinates[source], coordinates[target])
            for source, target in pairs
        )
        records = [
            record
            for source, target in pairs
            for record in segment_records[tuple(sorted((source, target)))]
        ]
        weighted_names = Counter(record["name"] for record in records)
        road_name = " / ".join([name for name, _ in weighted_names.most_common(2)])
        road_class = Counter(record["road_class"] for record in records).most_common(1)[
            0
        ][0]
        speed = min(record["speed_kph"] for record in records)
        forward_allowed = all(
            direction_allowed(source, target) for source, target in pairs
        )
        backward_allowed = all(
            direction_allowed(target, source) for source, target in pairs
        )
        bridge = any(record["bridge"] for record in records)
        seed = f"{path[0]}:{path[-1]}:{road_name}"
        simulated_flood_prone = stable_fraction(seed + ":flood") < (
            0.18 if bridge else 0.10
        )
        incident_prone = stable_fraction(seed + ":incident") < 0.09
        close_during_incident = stable_fraction(seed + ":closure") < 0.025

        distance_m = max(distance, 1.0)
        distance_km = round(distance_m / 1000.0, 3)
        time_min = round(distance_m / 1000.0 / speed * 60.0, 2)
        congestion = round(
            max(
                1.0,
                min(
                    5.0,
                    CONGESTION_BASE[road_class]
                    + (0.5 if bridge else 0.0)
                    + (0.4 if simulated_flood_prone else 0.0)
                    + 1.4 * (stable_fraction(seed + ":cong") - 0.5),
                ),
            ),
            2,
        )
        risk = round(
            min(
                5.0,
                max(
                    0.0,
                    RISK_BASE[road_class]
                    + (1.0 if bridge else 0.0)
                    + (0.8 if simulated_flood_prone else 0.0),
                ),
            ),
            3,
        )
        attributes = {
            "osm_way_ids": sorted({record["way_id"] for record in records}),
            "length_geometry": [
                [round(coordinates[node][1], 7), round(coordinates[node][0], 7)]
                for node in path
            ],
            "bridge": bridge,
            "flood_prone": simulated_flood_prone,
            "incident_prone": incident_prone,
            "close_during_incident": close_during_incident,
            "overlay_provenance": "deterministic synthetic educational layer",
        }
        base = {
            "road_name": road_name,
            "road_class": road_class,
            "attributes": attributes,
        }
        common = {
            "distance_km": distance_km,
            "time_min": time_min,
            "congestion": congestion,
            "risk": risk,
            **base,
        }
        if forward_allowed and backward_allowed:
            # Two-way road -> two directed records (matches data/models.py convention).
            edges.append(
                {
                    "start": f"osm_{path[0]}",
                    "end": f"osm_{path[-1]}",
                    "direction": "two-way",
                    **common,
                }
            )
            edges.append(
                {
                    "start": f"osm_{path[-1]}",
                    "end": f"osm_{path[0]}",
                    "direction": "two-way",
                    **common,
                }
            )
        else:
            if forward_allowed:
                edges.append(
                    {
                        "start": f"osm_{path[0]}",
                        "end": f"osm_{path[-1]}",
                        "direction": "one-way",
                        **common,
                    }
                )
            if backward_allowed:
                edges.append(
                    {
                        "start": f"osm_{path[-1]}",
                        "end": f"osm_{path[0]}",
                        "direction": "one-way",
                        **common,
                    }
                )

    poi_elements = [
        element
        for element in elements
        if element.get("type") in {"node", "way"}
        and element.get("tags", {})
        and any(
            (key, value) in POI_FILTER for key, value in element.get("tags", {}).items()
        )
    ]
    junction_positions = [(node_id, coordinates[node_id]) for node_id in junctions]
    seen_poi_names: set[str] = set()
    for poi in sorted(
        poi_elements,
        key=lambda item: (str(item.get("tags", {}).get("name") or ""), int(item["id"])),
    ):
        name = str(poi["tags"].get("name") or "").strip()
        normalized_name = re.sub(r"\W+", "", name.casefold())
        if not normalized_name or normalized_name in seen_poi_names:
            continue
        center = feature_center(poi, coordinates)
        if center is None:
            continue
        nearest_id, nearest_position = min(
            junction_positions, key=lambda item: haversine_m(center, item[1])
        )
        access_distance = haversine_m(center, nearest_position)
        if access_distance > 1_500:
            continue
        seen_poi_names.add(normalized_name)
        poi_kind = next(
            POI_FILTER[(key, value)]
            for key, value in poi["tags"].items()
            if (key, value) in POI_FILTER
        )
        poi_id = f"poi_{poi['type']}_{poi['id']}"
        nodes.append(
            {
                "id": poi_id,
                "name": name,
                "latitude": round(center[0], 7),
                "longitude": round(center[1], 7),
                "kind": poi_kind,
                "attributes": {
                    "osm_type": poi["type"],
                    "osm_id": int(poi["id"]),
                    "delivery_destination": True,
                    "snap_distance_m": round(access_distance, 2),
                },
            }
        )
        connector = {
            "distance_km": round(max(access_distance, 20.0) / 1000.0, 3),
            "time_min": round(max(access_distance, 20.0) / 1000.0 / 20.0 * 60.0, 2),
            "congestion": 1.0,
            "risk": 0.3,
            "road_name": f"Lối tiếp cận {name}",
            "road_class": "service",
            "attributes": {
                "synthetic_access_connector": True,
                "overlay_provenance": "POI snapped to nearest retained OSM road junction",
            },
        }
        edges.append(
            {
                "start": poi_id,
                "end": f"osm_{nearest_id}",
                "direction": "two-way",
                **connector,
            }
        )
        edges.append(
            {
                "start": f"osm_{nearest_id}",
                "end": poi_id,
                "direction": "two-way",
                **connector,
            }
        )

    if len(nodes) < MIN_NODES or len(edges) < MIN_EDGES:
        raise ValueError(
            f"Dataset below lab minimum: {len(nodes)} nodes, {len(edges)} edges"
        )

    timestamp = raw.get("osm3s", {}).get("timestamp_osm_base")
    return {
        "metadata": {
            "id": "hcmc-city-centre-delivery-2026",
            "name": "HCMC City-Centre Delivery Route Search Graph",
            "city": "Ho Chi Minh City",
            "country": "Việt Nam",
            "version": "1.0.0",
            "schema_version": SCHEMA_VERSION,
            "source": "OpenStreetMap contributors via bounded Overpass snapshot; ODbL 1.0",
            "source_url": "https://www.openstreetmap.org/copyright",
            "overpass_query": "scripts/overpass_hcmc.ql",
            "osm_base_timestamp": timestamp,
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "bbox": BBOX,
            "network_filter": "primary|secondary|tertiary",
            "description": "Contracted directed road topology for a delivery shipper AI search laboratory.",
            "disclaimer": "Road topology/tags come from OSM. Congestion, flood susceptibility, risk and ETA are deterministic educational simulations—not live traffic.",
            "license": "ODbL-1.0",
            "attribution": "© OpenStreetMap contributors",
            "stats": {
                "raw_osm_road_ways": len(road_ways),
                "contracted_road_nodes": len(junctions),
                "delivery_pois": len(seen_poi_names),
                "stored_road_nodes": sum(
                    1 for n in nodes if not n["id"].startswith("poi_")
                ),
                "stored_nodes": len(nodes),
                "stored_edges": len(edges),
            },
        },
        "nodes": nodes,
        "edges": edges,
    }


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--input",
        type=Path,
        default=RAW_OSM_PATH,
        help="Overpass JSON response",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=ROAD_GRAPH_PATH,
        help="Output teaching-graph JSON",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    with args.input.open("r", encoding="utf-8") as source:
        raw = json.load(source)
    snapshot = build_snapshot(raw)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    with args.output.open("w", encoding="utf-8", newline="\n") as destination:
        json.dump(snapshot, destination, ensure_ascii=False, indent=2)
        destination.write("\n")
    stats = snapshot["metadata"]["stats"]
    print(
        f"Wrote {args.output}: {stats['stored_nodes']} nodes, {stats['stored_edges']} edges"
    )


if __name__ == "__main__":
    main()
