"""Build the application-layer Delivery Graph from the road graph.

Selection
---------
POIs are chosen deterministically from the road graph (the `poi_*` nodes crawled from
OSM), with 4-6 representatives per kind. Warehouse and airport are synthetic POIs (no
OSM filter exists for them); they are created at fixed/deterministic locations and
snapped onto the nearest retained road junction, exactly like OSM POIs.

Edges
-----
Every DeliveryEdge corresponds to the Road Graph's directed shortest path between two
POIs (by distance). An undirected candidate pair is turned into:

* two DeliveryEdges (two-way) when it belongs to the Minimum Spanning Tree — this
  guarantees every POI can reach every other POI;
* one DeliveryEdge (one-way) when it comes from k-nearest-neighbour links — this adds
  realistic asymmetry (one-way streets) that matters for search experiments.

Example:
    python scripts/build_delivery_graph.py --input data/processed/graph.json \
        --output data/exports/delivery_graph.json
"""

from __future__ import annotations

import argparse
import json
import math
import random
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path

from config.defaults import (
    AIRPORT_POSITION,
    BBOX,
    DEFAULT_COUNTS,
    K_NEAREST,
)
from config.paths import DELIVERY_GRAPH_PATH, ROAD_GRAPH_PATH
from data.models import Edge, GraphData, Node
from delivery.models import (
    SCHEMA_VERSION,
    DeliveryEdge,
    DeliveryGraph,
    DeliveryNode,
)
from delivery.road import RoadGraph
from shared.helpers import haversine_m


def select_pois(road: GraphData, counts: dict[str, int]) -> list[Node]:
    """Deterministically sample `counts[kind]` POIs per kind, spread over space."""
    by_kind: dict[str, list[Node]] = {}
    for node in road.nodes:
        if node.id.startswith("poi_"):
            by_kind.setdefault(node.kind, []).append(node)

    selected: list[Node] = []
    for kind, wanted in counts.items():
        pool = sorted(by_kind.get(kind, []), key=lambda n: n.id)
        if not pool:
            continue
        if len(pool) <= wanted:
            chosen = pool
        else:
            chosen = [pool[round(i * (len(pool) - 1) / (wanted - 1))] for i in range(wanted)]
        selected.extend(chosen)
    return selected


def nearest_junction(road: GraphData, position: tuple[float, float]) -> Node:
    junctions = [n for n in road.nodes if n.id.startswith("osm_")]
    return min(
        junctions,
        key=lambda node: haversine_m(position, (node.latitude, node.longitude)),
    )


def synthetic_poi(
    road: GraphData,
    *,
    kind: str,
    name: str,
    poi_id: str,
    position: tuple[float, float],
    rng: random.Random,
) -> Node:
    junction = nearest_junction(road, position)
    access_distance = max(haversine_m(position, (junction.latitude, junction.longitude)), 20.0)
    return Node(
        id=poi_id,
        name=name,
        latitude=round(position[0], 7),
        longitude=round(position[1], 7),
        kind=kind,
        attributes={
            "osm_type": "synthetic",
            "osm_id": None,
            "delivery_destination": True,
            "snap_distance_m": round(access_distance, 2),
            "snapped_to": junction.id,
            "overlay_provenance": "synthetic POI snapped onto the road graph",
        },
    )


def warehouse_nodes(road: GraphData, count: int, rng: random.Random) -> list[Node]:
    nodes: list[Node] = []
    for index in range(count):
        # Deterministic pseudo-random points inside the bbox, then snapped.
        latitude = BBOX[0] + (BBOX[2] - BBOX[0]) * rng.uniform(0.08, 0.92)
        longitude = BBOX[1] + (BBOX[3] - BBOX[1]) * rng.uniform(0.08, 0.92)
        nodes.append(
            synthetic_poi(
                road,
                kind="delivery_warehouse",
                name=f"Kho hàng số {index + 1}",
                poi_id=f"poi_warehouse_{index + 1}",
                position=(latitude, longitude),
                rng=rng,
            )
        )
    return nodes


def airport_node(road: GraphData) -> Node:
    return synthetic_poi(
        road,
        kind="delivery_airport",
        name="Sân bay Tân Sơn Nhất",
        poi_id="poi_airport_tansonnhat",
        position=AIRPORT_POSITION,
        rng=random.Random(0),
    )


def build_road_with_snap_connectors(road: GraphData, pois: list[Node]) -> GraphData:
    """Add synthetic POI nodes and their access-connector edges to the road graph."""
    extra_nodes = [node for node in pois if node.attributes.get("osm_type") == "synthetic"]
    if not extra_nodes:
        return road
    nodes = list(road.nodes)
    edges = list(road.edges)
    for node in extra_nodes:
        snapped = node.attributes["snapped_to"]
        access_distance = float(node.attributes["snap_distance_m"])
        nodes.append(node)
        connector_attributes = {
            "synthetic_access_connector": True,
            "overlay_provenance": "synthetic POI snapped to nearest retained road junction",
        }
        for start, end in ((node.id, snapped), (snapped, node.id)):
            edges.append(
                Edge(
                    start=start,
                    end=end,
                    distance_km=round(access_distance / 1000.0, 3),
                    time_min=round(access_distance / 1000.0 / 20.0 * 60.0, 2),
                    congestion=1.0,
                    risk=0.3,
                    direction="two-way",
                    road_name=f"Lối tiếp cận {node.name}",
                    road_class="service",
                    attributes=dict(connector_attributes),
                )
            )
    return GraphData(nodes=nodes, edges=edges)


def candidate_pairs(pois: list[Node], road_graph: RoadGraph) -> list[tuple[int, int]]:
    """Return (i, j) pairs covered by the MST plus k-nearest-neighbour links."""
    size = len(pois)
    distance: list[list[float]] = [[0.0] * size for _ in range(size)]
    for i in range(size):
        for j in range(i + 1, size):
            path = road_graph.shortest_path(pois[i].id, pois[j].id)
            forward = path.distance_km if path else math.inf
            reverse_path = road_graph.shortest_path(pois[j].id, pois[i].id)
            backward = reverse_path.distance_km if reverse_path else math.inf
            distance[i][j] = min(forward, backward)
            distance[j][i] = distance[i][j]

    # Minimum Spanning Tree over the (undirected) pairwise distances.
    tree_pairs: set[tuple[int, int]] = set()
    connected = {0}
    while len(connected) < size:
        best = min(
            (
                (i, j)
                for i in connected
                for j in range(size)
                if j not in connected
            ),
            key=lambda pair: distance[pair[0]][pair[1]],
        )
        a, b = (best[0], best[1]) if best[0] < best[1] else (best[1], best[0])
        tree_pairs.add((a, b))
        connected.add(best[1])

    # k-nearest-neighbour links (undirected, deduplicated against MST edges).
    knn_pairs: set[tuple[int, int]] = set()
    for i in range(size):
        ranked = sorted(
            ((j, distance[i][j]) for j in range(size) if j != i),
            key=lambda item: item[1],
        )
        for j, _ in ranked[:K_NEAREST]:
            a, b = (i, j) if i < j else (j, i)
            key = (a, b)
            if key not in tree_pairs and key not in knn_pairs:
                knn_pairs.add(key)

    return list(tree_pairs) + list(knn_pairs)


def delivery_edges(
    pois: list[Node],
    road_graph: RoadGraph,
    tree_pairs: set[tuple[int, int]],
    knn_pairs: set[tuple[int, int]],
) -> list[DeliveryEdge]:
    """Turn candidate undirected pairs into directed DeliveryEdges."""
    edges: list[DeliveryEdge] = []
    ordered = tree_pairs | knn_pairs
    counter = 0
    for index, (i, j) in enumerate(sorted(ordered)):
        two_way = (i, j) in tree_pairs
        if two_way:
            directions = [(i, j), (j, i)]
        else:
            directions = [(i, j)]
        for source, target in directions:
            path = road_graph.shortest_path(pois[source].id, pois[target].id)
            if path is None:
                continue
            road_names: Counter[str] = Counter()
            road_classes: Counter[str] = Counter()
            for left, right in zip(path.node_ids[:-1], path.node_ids[1:]):
                edge = road_graph.edge(left, right)
                if edge is None:
                    continue
                road_names[edge.road_name] += 1
                road_classes[edge.road_class] += 1
            edges.append(
                DeliveryEdge(
                    edge_id=f"de_{counter:03d}",
                    start=pois[source].id,
                    end=pois[target].id,
                    distance_km=round(path.distance_km, 3),
                    time_min=round(path.time_min, 2),
                    congestion=round(path.congestion, 2),
                    risk=round(path.risk, 3),
                    direction="two-way" if two_way else "one-way",
                    road_path=list(path.node_ids),
                    road_name=road_names.most_common(1)[0][0] if road_names else "",
                    road_class=road_classes.most_common(1)[0][0] if road_classes else "",
                    attributes={
                        "geometry": [
                            [round(lon, 7), round(lat, 7)] for lon, lat in path.geometry
                        ],
                        "derived_from_road_shortest_path": True,
                    },
                )
            )
            counter += 1
    return edges


def build_delivery_graph(
    road: GraphData,
    *,
    counts: dict[str, int] | None = None,
    seed: int = 42,
) -> DeliveryGraph:
    """Build the Delivery Graph from the road graph.

    Returns a connected, directed Delivery Graph: the MST guarantees every POI can
    reach every other POI; kNN links add realistic one-way shortcuts.
    """
    selected_counts = {**DEFAULT_COUNTS, **(counts or {})}
    rng = random.Random(seed)
    pois = select_pois(road, selected_counts)
    pois.extend(warehouse_nodes(road, selected_counts["delivery_warehouse"], rng))
    if selected_counts.get("delivery_airport", 0) > 0:
        pois.append(airport_node(road))

    road_with_pois = build_road_with_snap_connectors(road, pois)
    road_graph = RoadGraph(road_with_pois)

    pair_list = candidate_pairs(pois, road_graph)
    tree_pairs: set[tuple[int, int]] = set()
    knn_pairs: set[tuple[int, int]] = set()
    for pair in pair_list[: len(pois) - 1]:
        a, b = pair
        tree_pairs.add((a, b) if a < b else (b, a))
    for pair in pair_list[len(pois) - 1 :]:
        a, b = pair
        knn_pairs.add((a, b) if a < b else (b, a))

    nodes = [
        DeliveryNode(
            id=node.id,
            name=node.name,
            latitude=node.latitude,
            longitude=node.longitude,
            kind=node.kind,
            attributes=dict(node.attributes),
        )
        for node in pois
    ]
    edges = delivery_edges(pois, road_graph, tree_pairs, knn_pairs)

    directed = len(edges)
    two_way = sum(1 for edge in edges if edge.direction == "two-way")
    return DeliveryGraph(
        metadata={
            "id": "hcmc-delivery-graph-2026",
            "name": "HCMC Delivery Search Graph (application layer)",
            "schema_version": SCHEMA_VERSION,
            "generated": True,
            "manual_edits": False,
            "source": "derived from data/processed/graph.json via scripts/build_delivery_graph.py",
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "algorithm": {
                "connectivity": "minimum spanning tree (two-way)",
                "shortcuts": f"{K_NEAREST}-nearest-neighbour (one-way)",
                "pairwise_metric": "road graph directed shortest path (distance_km)",
            },
            "description": "Application-layer POI graph for BFS/DFS/UCS/A* and UI/animation/reports.",
            "disclaimer": "Congestion/risk/ETA are deterministic educational simulations.",
            "stats": {
                "poi_nodes": len(nodes),
                "directed_edges": directed,
                "two_way_edges": two_way,
                "one_way_edges": directed - two_way,
            },
        },
        nodes=nodes,
        edges=edges,
    )


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--input",
        type=Path,
        default=ROAD_GRAPH_PATH,
        help="Road graph JSON",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=DELIVERY_GRAPH_PATH,
        help="Output delivery graph",
    )
    parser.add_argument("--seed", type=int, default=42)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    road = GraphData.model_validate_json(args.input.read_text(encoding="utf-8"))
    graph = build_delivery_graph(road, seed=args.seed)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    with args.output.open("w", encoding="utf-8", newline="\n") as destination:
        json.dump(graph.model_dump(), destination, ensure_ascii=False, indent=2)
        destination.write("\n")
    stats = graph.metadata["stats"]
    print(
        f"Wrote {args.output}: {stats['poi_nodes']} POIs, {stats['directed_edges']} "
        f"directed edges ({stats['two_way_edges']} two-way / "
        f"{stats['one_way_edges']} one-way)"
    )


if __name__ == "__main__":
    main()