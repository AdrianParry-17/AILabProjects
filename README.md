# HCMC Delivery Route Search

AI search-algorithms project: find and compare delivery routes in real Ho Chi Minh City
road topology. Backend in Python, frontend in **React.js**. See `docs/`.

## Two-layer graph

* **Road graph** (`data/processed/graph.json`, 1103 nodes / 2279 directed edges): all OSM
  roads, backend-only, used for shortest-path computation.
* **Delivery graph** (`data/exports/delivery_graph.json`, 31 POIs / 70 directed edges):
  only meaningful delivery POIs (warehouse, market, hospital, university, airport, ...)
  that algorithms, UI, animation, and reports operate on.

Architecture and dependency flow: `backend/app/` (FastAPI) + `frontend/` (React).

## Packages

```
shared/        # generic, dependency-free utilities (protocols, exceptions, helpers)
config/        # single-source paths, defaults, settings
core/          # reusable search framework (SearchResult, algorithm registry)
data/          # road dataset models + raw/processed/exports JSON
delivery/      # POI delivery graph, Dijkstra road engine, route expansion
algorithms/    # BFS + UCS + A* + shared cost/path/heuristic helpers
visualization/ # GeoJSON map/report serialization
backend/       # FastAPI routing API (app/ + data/), serves /api/v1
frontend/      # React + Vite + Leaflet single-route planner
tests/         # test suite by owner
scripts/       # reproducible crawl + build pipeline
```

## Setup

```bash
python -m venv .venv
.venv\Scripts\Activate.ps1     # Windows
pip install -r requirements.txt
```

## Run

Backend (FastAPI, serves `/api/v1` on port 8000):

```bash
python -m uvicorn backend.app.main:app --port 8000
```

Frontend (Vite dev server on port 5173, proxies to `/api/v1`):

```bash
cd frontend
npm install
npm run dev
```

## Tests & checks

```bash
python -m pytest
ruff check .
mypy data delivery algorithms core config shared visualization tests
```

## Docs index

* `docs/DATASET_SPEC.md` — road dataset + crawling.
* `docs/DELIVERY_GRAPH.md` — delivery graph + builder.
* `docs/BFS_SPEC.md` — BFS contract.
* `docs/ROADMAP.md` — task plan (see also the calendar in `Lab_1_Plan.pdf`).
* `CONVENTION.md` — coding conventions. `ALGORITHM_SPEC.md` — shared algorithm framework.