"""Load the Delivery Graph from `data/exports/delivery_graph.json`.

The two-layer architecture separates the Road Graph (backend shortest-path) from the
application-layer Delivery Graph that search/UI/animation/reports consume. This is the
entry point that loads that application graph.

`load_delivery_graph` validates the payload on every call (unless `validate=False`):
schema version, referential integrity, uniqueness, direction symmetry, hard minimums
and strong connectivity. This turns a corrupted or hand-edited
`data/exports/delivery_graph.json` into an early, explicit error instead of a silent
misbehaving search. `data/exports/delivery_graph.json` is a *generated* artifact — it
must be rebuilt with `scripts/build_delivery_graph.py`, never edited by hand.
"""

import json
from collections import defaultdict, deque
from pathlib import Path

from config.defaults import MIN_EDGES, MIN_NODES
from config.paths import DELIVERY_GRAPH_PATH
from config.settings import SCHEMA_VERSION
from shared.exceptions import InvalidGraphError
from shared.validators import ensure_schema_version, ensure_unique

from .models import DeliveryGraph

DATA_PATH = DELIVERY_GRAPH_PATH


def validate_delivery_graph(graph: DeliveryGraph) -> None:
    """Validate the hard invariants of the Delivery Graph (see DELIVERY_GRAPH.md § 5).

    Raises:
        InvalidGraphError: with a precise description of the first violated invariant.
    """
    metadata = graph.metadata or {}
    file_schema = metadata.get("schema_version", SCHEMA_VERSION)
    ensure_schema_version(
        file_schema, SCHEMA_VERSION, what="Delivery graph"
    )

    if len(graph.nodes) < MIN_NODES:
        raise InvalidGraphError(
            f"Delivery graph has {len(graph.nodes)} nodes < minimum {MIN_NODES}"
        )
    if len(graph.edges) < MIN_EDGES:
        raise InvalidGraphError(
            f"Delivery graph has {len(graph.edges)} edges < minimum {MIN_EDGES}"
        )

    node_ids = [node.id for node in graph.nodes]
    ensure_unique(node_ids, what="delivery node ids")

    node_set = set(node_ids)
    edge_ids = [edge.edge_id for edge in graph.edges]
    ensure_unique(edge_ids, what="delivery edge ids")
    if any(not edge.edge_id for edge in graph.edges):
        raise InvalidGraphError("Every delivery edge must have a non-empty edge_id")

    reverse: dict[tuple[str, str], str] = {}
    for edge in graph.edges:
        if edge.start not in node_set:
            raise InvalidGraphError(f"Delivery edge start {edge.start!r} is not a node")
        if edge.end not in node_set:
            raise InvalidGraphError(f"Delivery edge end {edge.end!r} is not a node")
        if edge.start == edge.end:
            raise InvalidGraphError(f"Delivery edge is a self-loop: {edge.start!r}")
        if edge.direction not in {"one-way", "two-way"}:
            raise InvalidGraphError(
                f"Delivery edge {edge.edge_id} has invalid direction {edge.direction!r}"
            )
        key = (edge.start, edge.end)
        if key in reverse:
            raise InvalidGraphError(f"Duplicate directed delivery edge {key}")
        reverse[key] = edge.direction

    for edge in graph.edges:
        reverse_key = (edge.end, edge.start)
        if edge.direction == "two-way" and reverse_key not in reverse:
            raise InvalidGraphError(
                f"Two-way delivery edge {edge.edge_id} ({edge.start} -> {edge.end}) "
                "has no reverse edge"
            )
        if edge.direction == "one-way" and reverse_key in reverse:
            raise InvalidGraphError(
                f"One-way delivery edge {edge.edge_id} ({edge.start} -> {edge.end}) "
                "has a reverse edge; direction contradicts the data"
            )

    adjacency: dict[str, list[str]] = defaultdict(list)
    for edge in graph.edges:
        adjacency[edge.start].append(edge.end)

    def reachable_from(source: str) -> set[str]:
        seen: set[str] = set()
        queue: deque[str] = deque([source])
        while queue:
            current = queue.popleft()
            if current in seen:
                continue
            seen.add(current)
            queue.extend(adjacency[current])
        return seen

    for node in graph.nodes:
        if len(reachable_from(node.id)) != len(node_set):
            raise InvalidGraphError(
                f"Delivery graph is not strongly connected: {len(reachable_from(node.id))}"
                f" of {len(node_set)} nodes reachable from {node.id!r}"
            )


def load_delivery_graph(
    path: Path | None = None, *, validate: bool = True
) -> DeliveryGraph:
    target = path if path is not None else DATA_PATH
    graph = DeliveryGraph.model_validate_json(target.read_text(encoding="utf-8"))
    if validate:
        validate_delivery_graph(graph)
    return graph


def load_delivery_metadata(path: Path | None = None) -> dict:
    target = path if path is not None else DATA_PATH
    return json.loads(target.read_text(encoding="utf-8")).get("metadata", {})
