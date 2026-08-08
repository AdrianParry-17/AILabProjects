# HCMC Delivery Route Search

AI search-algorithms project: find and compare delivery routes in real Ho Chi Minh City
road topology. Backend in Python, frontend in **React.js**. See `docs/`.

## Two-layer graph

* **Road graph** (`data/processed/graph.json`, 1103 nodes / 2279 directed edges): all OSM
  roads, backend-only, used for shortest-path computation.
* **Delivery graph** (`data/exports/delivery_graph.json`, 31 POIs / 70 directed edges):
  only meaningful delivery POIs (warehouse, market, hospital, university, airport, ...)
  that algorithms, UI, animation, and reports operate on.

Architecture and dependency flow: `docs/ARCHITECTURE.md`.

## Packages

```
shared/        # generic, dependency-free utilities (protocols, exceptions, helpers)
config/        # single-source paths, defaults, settings
core/          # reusable search framework (SearchResult, algorithm registry)
data/          # road dataset models + raw/processed/exports JSON
delivery/      # POI delivery graph, Dijkstra road engine, route expansion
algorithms/    # BFS + shared cost/path helpers; placeholders for DFS/UCS/A*/Dijkstra/IDA*
visualization/ # GeoJSON map/report serialization
tests/         # test suite by owner
scripts/       # reproducible crawl + build pipeline
ui/            # React frontend (WIP)
```

## Reproduce the datasets

```bash
python scripts/fetch_overpass.py
python scripts/build_osm_snapshot.py
python scripts/build_delivery_graph.py
```

## Setup

```bash
python -m venv .venv
.venv\Scripts\Activate.ps1     # Windows
pip install -r requirements.txt
```

## Tests & checks

```bash
python -m pytest
ruff check .
mypy data delivery algorithms core config shared visualization tests
```

## Docs index

* `docs/ARCHITECTURE.md` — structure, dependency flow, data layers, API contract.
* `docs/DATASET_SPEC.md` — road dataset + crawling.
* `docs/DELIVERY_GRAPH.md` — delivery graph + builder.
* `docs/BFS_SPEC.md` — BFS contract.
* `docs/MAP_CONTRACT.md` — React payloads.
* `docs/ROADMAP.md` — task plan (see also the calendar in `Lab_1_Plan.pdf`).
* `CONVENTION.md` — coding conventions. `ALGORITHM_SPEC.md` — shared algorithm framework.