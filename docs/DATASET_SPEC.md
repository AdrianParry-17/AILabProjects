# DATASET_SPEC.md

**HCMC Delivery AI Search - Road Dataset Specification (Processed layer)**

Version: 3.0

Owner: Hưng (dataset engineering)

Status: **Authoritative** (for the processed road dataset, `data/processed/graph.json`,
and the segmentation into RAW / PROCESSED / EXPORTED data layers).

This document is the contract for the **road** dataset and the crawl pipeline. It is the
source of truth for `data/models.py` and `data/processed/graph.json`. The POI-only
application layer (`data/exports/delivery_graph.json`) is specified in
`docs/DELIVERY_GRAPH.md`. Project-level data-layer definitions are in
`docs/ARCHITECTURE.md § 3-5`.

---

# 1. Purpose & Scope

## 1.1 What it governs

* `data/models.py` (Node, Edge, GraphData) — the authoritative schema.
* `data/processed/graph.json` — the processed **road graph** (junctions + connective
  roads + the crawled `poi_*` delivery POIs).
* `data/raw/hcmc_overpass.json` — the raw OSM export (provenance).
* The reproducible pipeline in `scripts/`.
* Node/edge value choices and the deterministic synthetic overlay rules.

## 1.2 What it does NOT govern

* The application-layer POI graph (`data/exports/delivery_graph.json`) →
  `docs/DELIVERY_GRAPH.md`.
* Algorithm implementation → `ALGORITHM_SPEC.md` + `docs/BFS_SPEC.md`.
* Frontend payloads → `docs/MAP_CONTRACT.md`.

The dataset stores **base** edge attributes only (`distance_km`, `time_min`,
`congestion`, `risk`). Runtime traffic scenarios multiply these in the cost layer; they
are not stored per scenario.

---

# 2. Data Layers (short)

Referenced precisely in `docs/ARCHITECTURE.md § 3`:

| Layer | Path | Schema | Role |
|-------|------|--------|------|
| RAW | `data/raw/hcmc_overpass.json` | Overpass `elements` | immutable provenance |
| PROCESSED (road) | `data/processed/graph.json` | `data.models.GraphData` | the full network; **single source of truth** |
| EXPORTED (delivery) | `data/exports/delivery_graph.json` | `delivery.models.DeliveryGraph` | application layer, derived |

---

# 3. Provenance (real vs synthetic)

| Data | Source |
|------|--------|
| Road topology, one-way rules, road names/classes | Real OSM ways/nodes via bounded Overpass query |
| Road topology, one-way rules, road names/classes | Real OSM ways/nodes via bounded Overpass query |
| Node coordinates | Real OSM node coordinates |
| Junction contraction, edge polylines | Derived by `scripts/build_osm_snapshot.py` |
| `distance_km` | Sum of Haversine segment lengths along the retained polyline |
| `time_min` (base) | `distance_km / speed_kph * 60`; speed from `maxspeed` tag or class default |
| `congestion`, `risk`, flood flags | **Deterministic synthetic education overlay** (SHA-256 thresholds + class constants) |
| Delivery POIs (market/supermarket/bus station/hospital/university) | Real OSM POIs snapped to nearest retained junction (≤ 1500 m) |
| Warehouse / Airport POIs | **Synthetic** nodes snapped onto the road graph (see `DELIVERY_GRAPH.md`) |

> Disclaimer stored in `graph.json` metadata: road topology/tags from OSM; congestion,
> flood, risk, ETA are deterministic educational simulations, not live data or advice.

---

# 4. Authoritative Schema — `data/models.py`

## 4.1 Node

```python
class Node(BaseModel):
    id: str
    name: str
    latitude: float
    longitude: float
    kind: str = "intersection"
    attributes: dict = Field(default_factory=dict)
```

| Field | Type | Rules |
|-------|------|-------|
| `id` | str | unique, stable. Junctions: `osm_<osm_node_id>`. POIs: `poi_<node|way>_<osm_id>`. Warehouse/airport: `poi_warehouse_<i>` / `poi_airport_tansonnhat`. |
| `name` | str | Vietnamese display name. |
| `latitude` / `longitude` | float | WGS84 decimal degrees. |
| `kind` | str | `intersection`, `gateway`, `bridge_access`, `delivery_market`, `delivery_supermarket`, `delivery_bus_station`, `delivery_hospital`, `delivery_university`, `delivery_warehouse`, `delivery_airport`. |
| `attributes` | dict | `osm_node_id`, `road_names`, `raw_degree`; POIs add `osm_type`, `osm_id`, `delivery_destination`, `snap_distance_m`. |

## 4.2 Edge

```python
class Edge(BaseModel):
    start: str
    end: str
    distance_km: float = Field(ge=0)
    time_min: float = Field(ge=0)
    congestion: float = Field(ge=0)
    risk: float = Field(ge=0)
    direction: str
    road_name: str = ""
    road_class: str = ""
    attributes: dict = Field(default_factory=dict)
```

| Field | Type | Rules |
|-------|------|-------|
| `start` / `end` | str | existing node ids, `start != end`. |
| `distance_km` | float | Haversine polyline length, `>= 0.001`. |
| `time_min` | float | base travel time `>= 0`. |
| `congestion` | float | 1.0–5.0. |
| `risk` | float | 0.0–5.0. |
| `direction` | str | `"two-way"` (stored as a reverse pair) or `"one-way"`. |
| `road_name` | str | dominant OSM road name(s), `"/"`-joined. |
| `road_class` | str | `primary`, `secondary`, `tertiary`, `service` (connector). |
| `attributes` | dict | `osm_way_ids`, `length_geometry` (`[lon,lat]` polyline), `bridge`, `flood_prone`, `incident_prone`, `close_during_incident`, `overlay_provenance`; connectors add `synthetic_access_connector`. |

## 4.3 GraphData

(Section renumbered to §4.3 below.)

```python
class GraphData(BaseModel):
    nodes: list[Node]
    edges: list[Edge]
```

A top-level `metadata` object (id, name, city, source, `osm_base_timestamp`, bbox, stats,
license, disclaimer) rides in the JSON and is read via `data.loader.load_metadata()`.
`metadata.schema_version` MUST equal `config.settings.SCHEMA_VERSION` (currently `"1.0"`,
the single source re-exported by `data.models` and `delivery.models`).

---

# 5. Hard Requirements (road graph)

The delivered `data/processed/graph.json` MUST satisfy each item; the current build does.

1. Node count ≥ 20 (current: 1103).
2. Directed edge count ≥ 30 (current: 2279).
3. Real locations: road nodes are HCMC city-centre intersections from OSM.
4. Referential integrity: every `start`/`end` names an existing node.
5. No self-loops (`start != end`).
6. No duplicate ordered pairs.
7. Two-way roads have their reverse edge present.
8. Range checks: `distance_km >= 0`, `time_min >= 0`, `congestion in [1,5]`,
   `risk >= 0`, `direction in {"one-way","two-way"}`.
9. Undirected connectivity (largest component retained).
10. Attribute variety so different criteria can diverge.
11. Loads cleanly via `data.loader.load_graph()`.
12. Node id prefixes `osm_` / `poi_` upheld.

---

## 6. Crawl Pipeline (reproducible)

```text
scripts/overpass_hcmc.ql          -> Overpass QL query
scripts/fetch_overpass.py         -> POST -> data/raw/hcmc_overpass.json        (RAW)
scripts/build_osm_snapshot.py     -> contract OSM -> data/processed/graph.json  (road graph)
scripts/build_delivery_graph.py   -> road graph -> data/exports/delivery_graph.json (delivery)
```

### 6.1 Query

* BBox `[south=10.7500, west=106.6650, north=10.8000, east=106.7150]` (Districts 1 & 3 core).
* Roads: `way["highway"~"^(primary|secondary|tertiary)$"]`.
* POIs: `amenity=marketplace`, `shop=supermarket`, `amenity=bus_station`,
  `amenity=hospital`, `amenity=university` (node + way).
* `(._;>;)` recurses children; `out body` returns the full snapshot.

### 6.2 Build steps (`build_osm_snapshot.py`)

1. Keep coordinates; keep ways matching the filter.
2. Build undirected adjacency for component/contraction analysis.
3. Keep the largest undirected component.
4. Junctions = degree ≠ 2; contract degree-2 chains.
5. Recover directions from `oneway`/roundabout tags.
6. Derive `distance_km`, `time_min`, base `congestion`, `risk` (class constants + stable
   per-edge seed).
7. Snap named POIs (dedup) to the nearest junction (≤ 1500 m), adding bidirectional
   `service` connectors.
8. Emit two records per two-way road, one per one-way road.
9. Validate ≥ 20 nodes / ≥ 30 edges; write UTF-8 JSON with metadata.

### 6.3 Overlay formulas (deterministic)

- `stable_fraction(seed)` = SHA-256 digest as float in `[0,1]`.
- Flood prone: threshold `0.18` (bridge) else `0.10`. Incident `0.09`. Close `0.025`.
- `congestion = clamp(1, 5, BASE[class] + bridge(0.5) + flood(0.4) + 1.4*(fraction-0.5))`.
- `risk = clamp(0, 5, RISK_BASE[class] + bridge(1.0) + flood(0.8))`.
- `BASE`/`RISK_BASE`: primary 2.0/0.6, secondary 2.6/1.0, tertiary 3.2/1.5.
- Default speeds km/h: primary 45, secondary 35, tertiary 30.

---

## 7. Traffic Conditions (runtime)

| Condition | `time_min` | `congestion` |
|-----------|-----------|--------------|
| Normal | x1.0 | x1.0 |
| Rush hour | x1.5 | x1.5 (cap 5.0) |
| Rain / flood | x2.0 | x2.0 (cap 5.0) |
| Incident / closed road | — | remove edges `close_during_incident` |

Cost reference (weights owned in `config/defaults.py`; `edge_cost` in
`algorithms/heuristic.py`):

```
Cost = α·Distance + β·Time + γ·Congestion + δ·Risk   (α .3 β .4 γ .2 δ .1)
```

---

## 8. Current Snapshot Statistics

| Statistic | Value |
|-----------|-------|
| Raw OSM road ways | 2008 |
| Contracted road junctions | 916 |
| Road nodes by kind | intersection 827, gateway 70, bridge_access 19 |
| Crawled POIs | 187 (supermarket 50, market 35, hospital 52, university 40, bus_station 10) |
| Stored nodes | 1103 |
| Stored directed edges | 2279 |
| One-way / two-way | 1039 / 1240 |
| Edge road classes | tertiary 776, primary 695, secondary 434, service 374 |
| Congestion range | 1.0 – 4.5 |
| Risk range | 0.3 – 3.3 |
| OSM base timestamp | 2026-08-05T13:24:17Z |

Numbers above reflect `data/processed/graph.json` as committed. Regenerating may shift the
totals slightly; treat the file's own `metadata.stats` as the live source.

---

## 9. Validation Checklist

- [ ] `data/processed/graph.json` loads via `data.loader.load_graph()` with no Pydantic error.
- [ ] Node count ≥ 20; directed edges ≥ 30.
- [ ] All `start`/`end` reference real nodes; no self-loops; no duplicate ordered pairs.
- [ ] Two-way roads have their reverse edge present.
- [ ] Values in declared ranges.
- [ ] Vietnamese names; ids follow prefix rules.
- [ ] Undirected graph connected (spot-check BFS).
- [ ] At least one scenario where distance-optimal ≠ time-optimal ≠ cost-optimal.
- [ ] `metadata` present (source, timestamp, license, disclaimer).

---

## 10. Assumptions

- Congestion/risk/traffic sim effects are **simulated deterministically**, not scraped.
- Network simplified to primary/secondary/tertiary + connectors (no residential detail).
- Base `time_min` assumes Normal traffic + class default speeds.
- Coordinates are OSM-accurate (map display, not survey precision).
- POI snapping uses nearest junction within 1500 m; connector is a synthetic access edge.

---

## 11. Sync Note

This file is the single dataset contract. It replaced older int-id / CSV-era documents.
String ids (`osm_*` / `poi_*`), two-layer data (RAW/PROCESSED/EXPORTED), and OSM
provenance are now authoritative in `docs/ARCHITECTURE.md`, `data/models.py`, and this
file. Update `docs/DELIVERY_GRAPH.md` and `docs/MAP_CONTRACT.md` if this schema changes.