# HCMC Delivery Route Search

AI search-algorithms project: find and compare delivery routes in real Ho Chi Minh City
road topology. Python backend + React frontend.

The backend is a real FastAPI service that runs a genuine BFS search on a real
(OSM-derived) HCMC road/delivery dataset and streams per-node `SearchStep` animation
frames to the UI. DFS / UCS / Greedy / A* are demoed by deterministic service mocks
until those teammate modules land (marked `(mô phỏng)` in the UI).

## Quickstart

Prerequisites: Python 3.11+, Node.js 18+.

### 1. Install dependencies

```bash
python -m venv .venv
.venv\Scripts\Activate.ps1            # Windows
# source .venv/bin/activate           # macOS / Linux
pip install -r requirements.txt

cd ui/web && npm install && cd ../..
```

### 2. Start the backend (FastAPI on 127.0.0.1:8000)

```bash
python -m ui.service.main
```

Verify: open http://127.0.0.1:8000/api/health -> `{"status":"ok"}`.
See the full API in section *API overview*.

### 3. Start the frontend (Vite on http://localhost:5173)

For the **real backend** (recommended), set the frontend to HTTP mode first:

```bash
cd ui/web
echo "VITE_API_MODE=http" > .env.local    # PowerShell: Set-Content .env.local "VITE_API_MODE=http"
npm install                                # first time only
npm run dev
```

Open http://localhost:5173, pick two locations, choose **Breadth-First Search**
and run. The status bar shows "Backend connected" and the run source is `real`.

> **Important (frontend API mode).** The frontend ships a fixture transport as its
> default (`VITE_API_MODE=mock`). In mock mode the web app serves static fixture JSON
> and **ignores your selected locations** — every BFS run shows the same canned path
> with `source=mock`. The backend is NOT involved in that mode. To run against the
> real service (as above) the `VITE_API_MODE=http` setting is required. The default
> backend URL is `http://127.0.0.1:8000/api`; override with `VITE_API_BASE_URL`.

## What you can do

- Load the HCMC delivery graph on an interactive map / graph view.
- Run **BFS** (real) or DFS / UCS / Greedy / A* (mocked, `(mô phỏng)`) between any
  two delivery POIs (markets, hospitals, universities, warehouses, airport, ...).
- Animate the search step by step (Play / Pause / Step / Restart), inspect the
  frontier at every expansion, and compare hops, distance, time, and cost.
- Replay recorded runs from the history panel.
- Switch between Graph and Map renderers without re-running the search.

## Project layout

```
cf. docs/ARCHITECTURE.md for the full dependency flow.

shared/        # generic, dependency-free utilities (protocols, exceptions, helpers)
config/        # single-source paths, defaults (cost weights), settings
core/          # reusable search framework (SearchResult, SearchStep, registry)
data/          # road dataset models + raw/processed/exports JSON
delivery/      # POI delivery graph, Dijkstra road engine, route expansion
algorithms/    # BFS (real) + shared cost/path helpers; placeholders for DFS/UCS/A*/Dijkstra/IDA*
visualization/ # GeoJSON map/report serialization
scripts/       # reproducible crawl + build pipeline
tests/         # test suite by owner
ui/
  service/     # backend: FastAPI app, endpoints, mocks, serialization, history
  web/         # frontend: React + Vite + TypeScript + Zustand + Leaflet
```

## Datasets

The two-layer graph: the **delivery graph** (what algorithms/UI/animation run on, a
strongly-connected POI overlay) is derived from the **road graph** (all OSM roads used
for shortest-path geometry).

| Graph | File | Size | Role |
|---|---|---|---|
| Road graph | `data/processed/graph.json` (generated) | 1103 nodes / 2279 edges | street-level routing, expanded `route` geometry |
| Delivery graph | `data/exports/delivery_graph.json` (generated) | 31 POIs / 70 edges | search + animation + metrics |
| Raw crawl | `data/raw/hcmc_overpass.json` (immutable provenance) | — | only source for regeneration |

Both datasets are already committed; regenerate them only if you change crawl or build:

```bash
python scripts/fetch_overpass.py
python scripts/build_osm_snapshot.py
python scripts/build_delivery_graph.py
```

## Tests & quality gates

```bash
python -m pytest                  # backend (154 tests)
ruff check .                       # linter
cd ui/web && npm test              # frontend Vitest (258 tests)
cd ui/web && npm run build         # typecheck (tsc) + production build
```

## API overview

Base `/api`, JSON, UTF-8. Every non-2xx uses the error envelope
`{"error": {"code", "message", "details"}}`.

| Endpoint | Description |
|---|---|
| `GET /api/health` | liveness → `{"status":"ok"}` |
| `GET /api/graph` | delivery graph payload: `graph` (nodes/edges/geojson), `bbox`, `metadata` |
| `GET /api/algorithms` | catalog with `mock` flags per algorithm |
| `GET /api/version` | service / schema / api version gate |
| `POST /api/search` | `{algorithm, start, goal, enable_logging}` → `{run, result, metrics, route}` |
| `GET /api/history` | recent runs (summaries) |
| `GET /api/history/{id}` | a full recorded run incl. steps (replay) |

`POST /api/search` returns `result.steps` — one `SearchStep {current_node, frontier, reason}`
per expanded node — which the frontend replays as the animation timeline.

## Docs index

- `docs/ARCHITECTURE.md` — structure, dependency flow, data layers, API boundary.
- `docs/DATASET_SPEC.md` — road dataset + crawling.
- `docs/DELIVERY_GRAPH.md` — delivery graph + builder.
- `docs/BFS_SPEC.md` — BFS contract.
- `docs/ALGORITHM_SPEC.md` — shared algorithm framework + cost model (§14).
- `docs/MAP_CONTRACT.md` — React payloads.
- `docs/GUI_ROADMAP.md` — REST API contracts, error envelope, mock design.
- `docs/ROADMAP.md` — task plan. `CONVENTION.md` — coding conventions.
- `docs/UI_TASK_BREAKDOWN.md` / `docs/UI_IMPLEMENTATION_PLAN.md` — frontend workstream.