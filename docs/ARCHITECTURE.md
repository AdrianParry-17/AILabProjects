# ARCHITECTURE.md

**HCMC Delivery AI Search - Project Architecture & API Contract**

Version: 4.0

Status: **Authoritative** (for project structure, dependency flow, data classification,
design principles, and the backend/API contract).

This document is the single agreed mental model of the project. Every other spec in this
repository (`CONVENTION.md`, `ALGORITHM_SPEC.md`, `docs/*`) references it instead of
redefining structure or dependency flow. When two documents conflict on **what goes where
or who imports whom**, this file wins.

---

# 1. Design Principles

1. **Pure algorithms.** A search algorithm only consumes a graph and returns exactly one
   `SearchResult`. It never loads files, renders UI, or prints.
2. **Shared models, no duplication.** `data/models.py` owns dataset models, `core/` owns
   the search framework (`SearchResult`, registry), `shared/` owns generic protocols and
   helpers. Reuse before copy.
3. **Two-layer graph with a single topology source.** One Road Graph (all OSM roads,
   backend-only, shortest-path computation) and one Delivery Graph (only meaningful POIs,
   which algorithms, UI, animation, and reports operate on).
4. **Dependency flows downward.** Lower layers (`shared`, `config`, `core`) never import
   domain layers (`data`, `delivery`, `algorithms`, `visualization`, `ui`).
5. **JSON is the API surface.** The React frontend talks to a thin JSON service whose
   payloads are exactly the Pydantic models, field names unchanged.
6. **Reproducibility.** Pipeline inputs are versioned; derived files can be regenerated
   with a single script.

---

# 2. Authoritative Project Structure

```
project/
├── shared/                  # lowest layer: generic, dependency-free utilities
│   ├── __init__.py
│   ├── types.py             # NodeLike, EdgeLike, GraphLike protocols; LatLon, Polyline
│   ├── constants.py         # EARTH_RADIUS_M
│   ├── enums.py             # Direction, TrafficCondition, AlgorithmName
│   ├── exceptions.py        # AILabError, DataError, InvalidGraphError, SearchError, ...
│   ├── logger.py            # get_logger(), configure_cli_logging()
│   ├── helpers.py           # haversine_m(), stable_fraction()
│   └── validators.py        # ensure_schema_version(), ensure_unique()
├── config/                  # single-source configuration (imports shared only)
│   ├── __init__.py
│   ├── paths.py             # RAW_DIR/ROAD_GRAPH_PATH/DELIVERY_GRAPH_PATH/...
│   ├── defaults.py          # BBOX, POI_FILTER, DEFAULT_COUNTS, CostWeights, ...
│   └── settings.py          # PROJECT_NAME, SCHEMA_VERSION
├── core/                    # reusable search framework (imports shared only)
│   ├── __init__.py
│   ├── search_algorithm.py  # SearchAlgorithm ABC, ALGORITHM_REGISTRY, run_algorithm()
│   ├── search_result.py     # SearchResult + SearchStep (uniform output model)
│   ├── search_event.py      # SearchEvent / SearchEventKind
│   ├── search_history.py    # SearchHistory (bounded in-memory run log)
│   └── search_metrics.py    # SearchMetrics summary derived from a SearchResult
├── data/                    # road dataset models + raw/processed/exported JSON files
│   ├── __init__.py
│   ├── models.py            # Pydantic: Node, Edge, GraphData   (authoritative schema)
│   ├── loader.py            # load_graph() -> GraphData; load_metadata() -> dict
│   ├── raw/                 # RAW layer: the one-time OSM snapshot
│   │   └── hcmc_overpass.json
│   ├── processed/           # PROCESSED: graph.json (1103 nodes, 2279 directed edges)
│   │   └── graph.json
│   └── exports/             # EXPORTED: delivery_graph.json (31 POIs, 70 edges)
│       └── delivery_graph.json
├── delivery/                # application-layer graph + road shortest-path helpers
│   ├── __init__.py
│   ├── models.py            # DeliveryNode, DeliveryEdge, DeliveryGraph
│   ├── loader.py            # load_delivery_graph / load_delivery_metadata
│   ├── road.py              # RoadGraph; dijkstra(); shortest_path(); .edge()
│   ├── builder.py           # build_delivery_graph() (MST + kNN)
│   └── route.py             # expand_poi_path() : POI path -> street-level route
├── algorithms/              # search algorithms, one module per algorithm
│   ├── __init__.py          # re-exports bfs, run_algorithm, edge_cost, ...
│   ├── base.py              # shared build_result / reconstruct_path / register
│   ├── bfs.py               # BFSAlgorithm + bfs()   (implemented)
│   ├── dfs.py               # placeholder (DFS teammate)
│   ├── ucs.py               # placeholder (UCS teammate)
│   ├── astar.py             # placeholder (A* teammate)
│   ├── dijkstra.py          # placeholder (Dijkstra teammate)
│   ├── ida_star.py          # placeholder (IDA* teammate)
│   ├── metrics.py           # path_metrics, path_total_cost, build_edge_lookup, ...
│   └── heuristic.py         # edge_cost; re-exports CostWeights / DEFAULT_WEIGHTS
├── visualization/           # GeoJSON map/report serialization (no search logic)
│   ├── __init__.py
│   └── geojson.py           # point_geometry, route_to_geojson, graph_to_geojson
├── tests/                   # test suite, one subpackage per owner
│   ├── algorithms/          # tests/algorithms/test_bfs.py
│   ├── core/                # tests/core/test_core.py
│   ├── data/                # tests/data/test_loader.py
│   ├── delivery/            # tests/delivery/test_integration.py
│   └── visualization/       # tests/visualization/test_geojson.py
├── scripts/                 # reproducible pipeline (imports data, delivery, algorithms)
│   ├── overpass_hcmc.ql     # the Overpass query used to fetch RAW
│   ├── fetch_overpass.py    # RAW: download OSM
│   ├── build_osm_snapshot.py# OSM raw -> data/processed/graph.json (road graph)
│   └── build_delivery_graph.py  # processed/graph.json -> exports/delivery_graph.json
├── ui/                      # React frontend (separate project directory, no Python)
└── docs/                    # this documentation
```

Distribution of responsibilities is captured in each package's `README.md` and in
`CONVENTION.md § 2`.

---

## 3. Authoritative Dependency Flow

Allowed import graph (higher may import lower; never the reverse):

```text
ui/  (React)                      # not .py; talks to the API over JSON
 ^
 |  (HTTP)
backend/service (thin JSON wrapper)   # (owned by whoever owns the UI-facing service)
 ^
 |
visualization                       # serializes graphs/routes for the map
 ^
 |
algorithms / delivery               # search + application graph
 ^           ^
 |           |                       (delivery imports data + shared/config)
 |           └────────────────┐
 |                            |
core  (search framework)     |
 ^    (imports shared only)   |
 |                            |
data / config                 # domain models / config values (import shared only)
 ^   ^
 |   |
shared/                       # lowest layer; imports only stdlib
```

Explicitly allowed for a given module `X`:

* `shared` may import: stdlib, itself.
* `config` may import: `shared`, stdlib, itself.
* `core` may import: `shared`, stdlib, pydantic, itself.
* `data` may import: `config`, `shared`, pydantic, stdlib, itself.
* `delivery` may import `data`, `config`, `shared`, and its sibling modules.
* `algorithms` may import `core`, `data`, `config`, `shared`, stdlib, itself, and
  `delivery` only when an algorithm must expand a POI path to road-level geometry via
  `delivery.route`.
* `visualization` may import `shared` (and the data shapes of `data`/`delivery`).
* any test may import everything above it.
* `scripts` may import `data`, `delivery`, `algorithms`, `config`, `shared`.

Forbidden:

* `data/` importing `delivery`, `algorithms`, `visualization`, or `ui`.
* `config/` or `core/` importing `data`, `delivery`, `algorithms`, `ui`.
* Importing `ui/` from any Python module.
* Any import of `streamlit`.

If you find yourself importing upward, stop and refactor (inject the value, move the
helper into the lower layer, or widen the lower-layer API). Circular imports are a
hard error.

---

## 4. JSON Serialization Contract

* All JSON is generated by Pydantic `model_dump()` (UTF-8, no trailing garbage).
* **Field names MUST match the Python field names exactly** (snake_case). No camelCase.
* Integers/booleans/strings are JSON-native. Coordinates are decimal degrees.
* Pydantic models are forward-compatible: a parser must ignore unknown fields; a
  **generated** file may add optional fields but never drop/rename existing ones.
* **Schema versioning.** The single source of truth is
  `config/settings.py::SCHEMA_VERSION`; `data/models.py` and `delivery/models.py` each
  re-export it. Generated JSON files carry it in `metadata.schema_version`, and their
  loaders reject a mismatched file. Specifically: `data.loader.load_graph` validates the
  road graph's schema version, and `delivery.loader.load_delivery_graph` validates the
  delivery graph's schema version **and** its full set of hard invariants on every call.
  Bump the version together with the models, the regenerated JSON, and this doc set on
  any breaking schema change (see `CONVENTION.md § 11`).

The React frontend consumes exactly these two payload kinds (see `docs/MAP_CONTRACT.md`):

1. **A graph** (`GraphData` or `DeliveryGraph`), for the static map.
2. **A `SearchResult`**, for the route + animation.

---

## 5. Layered Data Model (Raw → Processed → Exported)

```
 data/raw/hcmc_overpass.json        (RAW, immutable, provenance)
      │  scripts/build_osm_snapshot.py    ("anchor" of the pipeline)
      ▼
 data/processed/graph.json          (PROCESSED = the full road dataset, ~1100 nodes)
      │  scripts/build_delivery_graph.py
      ▼
 data/exports/delivery_graph.json   (EXPORTED = application-layer, 31 POIs)
```

**Source of truth**: the **processed road dataset** `data/processed/graph.json` (and its
schema in `data/models.py`) is the single input to every derived artifact. `data/raw` is
provenance; `data/exports/delivery_graph.json` is derived. All three are stored in the
repo for reproducibility, but only `data/processed/graph.json` is editable by the build
pipeline.

**`delivery_graph.json` is generated output**: it must always be rebuilt with
`scripts/build_delivery_graph.py`, never edited by hand. Its loader validates schema
version, referential integrity, direction symmetry, minimums and strong connectivity on
every load (see `DELIVERY_GRAPH.md § 2.1`, § 5).

---

## 6. Backend / API Contract (reference)

The backend is a thin JSON shell (FastAPI or similar) over the Python packages. Its
payloads are defined by the Pydantic models above; the backend itself adds only routing.
This is a **reference contract**, not an implementation.

| Method | Path | Request | Response (Pydantic) |
|--------|------|---------|---------------------|
| GET | `/dataset` | - | `DeliveryGraph` (POI-only application graph) |
| GET | `/road` | - | `GraphData` (full road graph) |
| POST | `/search` | `{ graph, start, goal, criterion?, weights?, traffic? }` | `SearchResult` |
| POST | `/route/expand` | `{ path: [poi ids] }` | `{ geometry: [lon,lat][], details }` |

All bodies use the same field names as the Python models. The frontend (`ui/`) implements
the UX; this repo owns only the schema.

> **Concrete service surface.** The table above is the *conceptual* data-layer contract. The
> endpoints the React frontend actually calls — `GET /health`, `/graph`, `/algorithms`,
> `/version`, `POST /search`, `GET /history`, `GET /history/:id`, `GET /route` — are defined by
> the GUI service in `docs/GUI_ROADMAP.md §11` (the thin JSON shell is owned by the UI-facing
> service owner). Payload field names always follow the Pydantic models (`MAP_CONTRACT`).

---

## 7. Relationship to the other docs

| Spec | Covers | Cross-references |
|------|--------|------------------|
| `CONVENTION.md` | code style, typing, checks, exceptions | architecture §1, §3 |
| `ALGORITHM_SPEC.md` | shared algorithm interface + helper + requirements for BFS/DFS/UCS/A* | §4 (JSON) |
| `docs/DATASET_SPEC.md` | the road (processed) dataset + crawling | §3 |
| `docs/DELIVERY_GRAPH.md` | the exported delivery graph + builder | `DATASET_SPEC` |
| `docs/BFS_SPEC.md` | the BFS contract specifically | `ALGORITHM_SPEC` |
| `docs/MAP_CONTRACT.md` | React payloads, geometry, animation | §4, §6 |
| `docs/ROADMAP.md` | task-by-task plan | all above |
