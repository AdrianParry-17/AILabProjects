# DELIVERY_GRAPH.md

**HCMC Delivery AI Search - Delivery Graph Specification (exported application layer)**

Version: 1.0

Owner: Hưng (builds) / consumed by algorithms + UI

Status: **Authoritative** (for `delivery/` and `data/exports/delivery_graph.json`).

This document specifies the POI-only **application-layer** graph that search algorithms,
the UI, animation, and reports actually operate on. It is derived from the road graph in
`data/processed/graph.json` (see `docs/DATASET_SPEC.md`) via
`scripts/build_delivery_graph.py` (backed by the `delivery/` package).

---

# 1. Purpose & Relationship

* The **road graph** (`data/processed/graph.json`, ~1100 nodes) is too large and mixed
  (every OSM intersection) for a clean teaching scenario.
* The **delivery graph** (`data/exports/delivery_graph.json`) keeps only meaningful POIs
  (warehouse, market, supermarket, bus station, hospital, university, airport) and the
  abstract edges between them. Search operates here.
* The `delivery/` package also hosts the road shortest-path engine (Dijkstra) that the
  builder and the UI route-expansion use.

---

# 2. File Contract

| Item | Value |
|------|-------|
| Final file | `data/exports/delivery_graph.json` |
| Pydantic models | `delivery/models.py` (DeliveryNode, DeliveryEdge, DeliveryGraph) |
| Loader | `delivery/loader.py` -> `load_delivery_graph()` -> `DeliveryGraph`, `load_delivery_metadata()` -> dict |
| Builder | `delivery/builder.py` -> `build_delivery_graph()`; CLI `scripts/build_delivery_graph.py` |
| Road engine | `delivery/road.py` -> `RoadGraph` (dijkstra, shortest_path, edge, outgoing) |
| Route expansion | `delivery/route.py` -> `expand_poi_path()` |
| Encoding | UTF-8 |

## 2.1 `data/exports/delivery_graph.json` is GENERATED OUTPUT — never edit by hand

`data/exports/delivery_graph.json` is a **derived artifact**. It is produced by
`scripts/build_delivery_graph.py` from the road graph (`data/processed/graph.json`) and
is fully deterministic under a fixed seed. Treating it as read-only is a maintainability
requirement:

* **Never edit it manually.** Any change done by hand is silently overwritten the next
  time the file is rebuilt, so the source of truth (`data/processed/graph.json`) and the
  JSON would drift. Reproduce manually instead:
  ```bash
  python scripts/build_delivery_graph.py
  ```
* The loader relies on these invariants (see § 5) and **validates them on every load**
  (`delivery/loader.validate_delivery_graph`). A hand-edited file that breaks the schema
  version, referential integrity, or direction rules fails loudly instead of
  misbehaving silently in a search.
* The file's `metadata` carries `"generated": true` and `"schema_version"` so tools can
  assert it is fresh and correctly-versioned.

Reproduce:

```bash
python scripts/build_delivery_graph.py
```

## 2.2 Versioning

`delivery/models.py` re-exports `SCHEMA_VERSION == "1.0"` from `config/settings.py` (the
single source of truth). The generated JSON's `metadata.schema_version` MUST equal it;
the loader refuses to load a mismatch. Bump `SCHEMA_VERSION` (and regenerate the JSON +
update `docs/*`) together whenever a breaking change is made to
`DeliveryNode`/`DeliveryEdge`/`DeliveryGraph`. Non-breaking additions (new optional
fields) keep the version unchanged.

---

## 3. Schema (authoritative — `delivery/models.py`)

```python
class DeliveryNode(BaseModel):
    id: str
    name: str
    latitude: float
    longitude: float
    kind: str
    attributes: dict = Field(default_factory=dict)


class DeliveryEdge(BaseModel):
    edge_id: str                 # unique, e.g. "de_001"
    start: str
    end: str
    distance_km: float           # = road-graph shortest path in km
    time_min: float
    congestion: float
    risk: float
    direction: str               # "two-way" | "one-way"
    road_path: list[str] = ...   # underlying road node ids
    road_name: str
    road_class: str
    attributes: dict = Field(default_factory=dict)
        # geometry: [[lon,lat], ...] flattened road polyline
        # derived_from_road_shortest_path: True


class DeliveryGraph(BaseModel):
    metadata: dict = Field(default_factory=dict)
    nodes: list[DeliveryNode]
    edges: list[DeliveryEdge]
```

### 3.1 Node id scheme

| Kind | id pattern | latitude/longitude |
|------|-----------|---------------------|
| Crawled POI (market/supermarket/bus station/hospital/university) | `poi_<node\|way>_<osm_id>` | real OSM center |
| Warehouse (synthetic) | `poi_warehouse_<i>` | pseudo-random point in bbox, snapped |
| Airport (synthetic) | `poi_airport_tansonnhat` | Tân Sơn Nhất, snapped |

### 3.2 Edge metrics

Each delivery edge's metrics equal the **road-graph directed shortest path** between the
two POIs (by `distance_km`). `congestion`/`risk` are the max along that path;
`time_min` the sum. This guarantees the POI graph's cost behaves like real driving.

---

## 4. Selection & Construction

`delivery/builder.py`:

1. **POI selection**: deterministic sample of 4–6 per kind from the road graph
   (`delivery_supermarket`, `delivery_market`, `delivery_bus_station`,
   `delivery_hospital`, `delivery_university`). ~24–30 POIs.
2. **Synthetic nodes**: warehouses placed deterministically in the bbox, and an airport,
   each snapped to the nearest road junction (reusing the same snapping rule as OSM POIs).
3. **Pairwise distance**: for every ordered candidate pair, run
   `RoadGraph.shortest_path(`).
4. **Connectivity (MST)**: a Minimum Spanning Tree over the POIs guarantees every POI can
   reach every other POI (edges stored **two-way**).
5. **Shortcuts (kNN)**: k-nearest-neighbour links (k=2) add realistic one-way shortcuts,
   making the graph non-trivial for hop-count searches vs weighted searches.

Result invariants (current build): **31 nodes / 70 directed edges (60 two-way, 10
one-way)**, strongly connected.

---

## 4.1 Mapping: Road Graph → Delivery Graph (explicit)

Every Delivery Graph element is derived from the Road Graph by a fixed, documented rule.
This is the authoritative mapping used by `delivery/builder.py`; keep it in sync with the
code.

| Delivery Graph element | Derived from Road Graph | Rule |
|------------------------|-------------------------|------|
| `DeliveryNode` (crawled POIs: market/supermarket/bus station/hospital/university) | `data.Node` with `id.startswith("poi_")` | same `id`; `name`, `latitude`, `longitude`, `kind` copied verbatim; `attributes` copied |
| `DeliveryNode` (warehouse) | **synthetic** `Node` (`osm_type == "synthetic"`) | pseudo-random point in bbox, snapped to nearest `osm_` junction; stored as POI node with `snapped_to`/`snap_distance_m` |
| `DeliveryNode` (airport) | **synthetic** `Node` (`poi_airport_tansonnhat`) | fixed Tân Sơn Nhất position, snapped to nearest `osm_` junction |
| `DeliveryEdge.metrics` (`distance_km`, `time_min`, `congestion`, `risk`) | `RoadGraph.shortest_path(poi_i, poi_j)` | `distance_km` = sum of road-edge `distance_km`; `time_min` = sum of `time_min`; `congestion`/`risk` = **max** along the road path |
| `DeliveryEdge.road_path` | same shortest path | exact `RoadPath.node_ids` (road-level) |
| `DeliveryEdge.attributes.geometry` | same shortest path | `[[lon, lat], ...]` polyline from `RoadPath.geometry`, rounded to 7 decimals |
| `DeliveryEdge.direction` | candidate-pair class | `"two-way"` for MST pairs (both directions stored), `"one-way"` for kNN links (forward only) |
| `DeliveryEdge.edge_id` | builder counter | `de_<seq:03d>`; unique across the graph |
| `DeliveryGraph.metadata.schema_version` | `delivery.models.SCHEMA_VERSION` (re-export of `config.settings.SCHEMA_VERSION`) | fixed at build time; validated on load |

Notes:

* Node **ids are the shared key** between layers — a `DeliveryNode.id` always names a
  `poi_*` node that also exists in the Road Graph (or is a synthetic POI appended to it
  by `build_road_with_snap_connectors`).
* Edge **metrics are not averaged**; they are the exact aggregate of the underlying road
  shortest path, so cost behaves like real driving. This is the guarantee that makes the
  small POI graph a faithful proxy for the full road network.
* A `DeliveryEdge` may span many road edges; `road_path` retains the full chain so the UI
  can draw real streets without re-running Dijkstra.

---

## 4.2 Why `K_NEAREST = 2`?

`K_NEAREST = 2` controls how many one-way "shortcut" links each POI adds on top of the
connectivity MST.

* **What it buys.** Two links per POI keep the graph *sparse but non-trivial*: with only
  the MST the graph is a tree (one path per pair → every search trivial and identical),
  while a single nearest link per POI still yields too many coinciding hop-counts. With
  `k = 2`, the graph has enough alternative one-way shortcuts that **hop-count-optimal
  (BFS) and cost-optimal (UCS/A\*) paths genuinely differ** — the central teaching point.
* **Cost of going higher.** Each extra `k` adds up to `n` one-way edges (≈31 per step)
  and makes the delivery graph denser and closer to the raw road graph, diluting the
  "meaningful POI abstraction" the layer exists to provide, and adding visual clutter for
  the UI. It also increases build time (every pair still needs a road-graph shortest
  path, so the dominant cost is pairwise, not `k`).
* **Determinism.** The kNN selection uses a stable sort on `(distance, node id)`; combined
  with the fixed seed the whole build is reproducible.

The value is deliberately a module constant (`config/defaults.py::K_NEAREST`) with a
documented trade-off rather than a CLI flag, so the dataset stays comparable across the
team.

---

## 5. Hard Requirements

These invariants are **enforced by `delivery/loader.validate_delivery_graph()` on every
`load_delivery_graph()`** (disable with `validate=False` at your own risk):

1. Nodes ≥ 20; directed edges ≥ 30 (current 31/70).
2. Every `DeliveryNode.id` unique; every `DeliveryEdge.start`/`end` exists.
3. Strong connectivity: from any node, every other node is reachable (MST guarantees it).
4. One-way edges are real (only one direction present); two-way edges have their reverse.
5. Every `DeliveryEdge.edge_id` unique and non-empty.
6. `road_path` non-empty for edges that have a drivable route.
7. Deterministic: same input + seed → identical output.
8. `metadata.schema_version == delivery.models.SCHEMA_VERSION`.

---

## 6. Road Graph Engine (`delivery/road.py`)

Used by the builder and by the UI for street-level rendering.

```python
class RoadGraph:
    def __init__(self, graph: GraphData): ...
    def outgoing(self, node: str) -> list[Edge]
    def edge(self, source: str, target: str) -> Edge | None
    def dijkstra(self, start: str) -> tuple[dict[str, float], dict[str, str | None]]  # dist, prev
    def shortest_path(self, start: str, end: str) -> RoadPath | None
```

Dijkstra uses only `distance_km` (cost weights are the algorithms' concern, not the road
engine's). `shortest_path` returns node ids, aggregate metrics, and a `[lon, lat]`
polyline.

---

## 7. Route Expansion (`delivery/route.py`)

Turn a POI-level `SearchResult.path` into a drawable street route:

```python
def expand_poi_path(poi_path, road_graph, delivery_graph=None) -> ExpandedRoute
```

`ExpandedRoute` = merged `node_ids`, `geometry` (polyline), `hops`, `distance_km`,
`time_min`. The UI uses `geometry` to draw the road-level line and can show intermediate
stopovers.

---

## 8. Relationship to other docs

* `docs/DATASET_SPEC.md` — the input road graph + overlay rules.
* `backend/app/` — serves the graph and expanded geometry to the UI.
* `ALGORITHM_SPEC.md` — algorithms operate on this graph and call `expand_poi_path`.