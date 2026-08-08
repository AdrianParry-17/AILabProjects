# UI

React.js frontend + FastAPI JSON service for the HCMC Delivery AI Search app.
Consumes exactly the JSON payloads in `docs/MAP_CONTRACT.md`: the graph payload
for the static map, `SearchResult` for the metrics panel and step-by-step
animation, and the expanded route polyline for the highlighted path.
`CONVENTION.md § 3` forbids Python UI frameworks — the frontend is React.js only.

## Layout

```
ui/
  service/        FastAPI backend (main, graphs, backends, mocks, history,
                  serialization, routing, errors) — serves /api/*
  web/            React + TypeScript frontend (Vite)
  README.md       this file
```

## Quick start

Two processes, run from the repo root (backend) and `ui/web` (frontend):

```bash
# Terminal 1 — JSON service on http://127.0.0.1:8000
python -m ui.service.main

# Terminal 2 — frontend dev server on http://localhost:5173
cd ui/web
npm install     # first time only
npm run dev
```

Open http://localhost:5173, pick two delivery POIs and run a search.

## Endpoints (`/api`)

| Method | Path | Returns |
|--------|------|---------|
| GET | `/health` | liveness probe |
| GET | `/graph` | delivery graph payload (`graph` / `bbox` / `metadata`) |
| GET | `/algorithms` | selectable algorithms (`id` / `label` / `mock`) |
| GET | `/version` | service / schema / API version gate |
| POST | `/search` | `{run, result, metrics, route}` for one search |
| GET | `/history` | recent run summaries |
| GET | `/history/{run_id}` | one recorded run incl. steps (replay) |

Errors follow the § 7 envelope `{"error": {"code", "message", "details"}}` —
`400 INVALID_INPUT`, `404 ALGORITHM_UNKNOWN`, `503 GRAPH_NOT_FOUND`,
`504 SEARCH_TIMEOUT`, `500 SEARCH_FAILED` / `INTERNAL`.

## Real vs mock algorithms

Today only **BFS** is a shipped real algorithm. DFS/UCS/Greedy/A* are served by
in-process mocks (`ui/service/mocks.py`) that satisfy the `§ 6.6` invariant
contract; the UI marks them with a `(mock)` badge (algorithm list, status bar,
history) and their explanations read `… - mô phỏng: …`.

Teammate modules are discovered **on demand** (Task-026): `POST /search` imports
`algorithms/<name>.py` at first use, so a teammate shipping `algorithms/dfs.py`
with `@register_algorithm` flips DFS from mock to real (`source="real"`)
with zero service changes — see `tests/ui/test_adoption.py` and
`docs/ui_notes.md`.

## Tests & checks

```bash
# Frontend (ui/web)
npm test          # vitest
npm run build     # tsc --noEmit && vite build

# Backend gates run from the repo root
python -m pytest tests
python -m ruff check .
```

See `docs/ui_notes.md` for the end-to-end walkthrough and recorded performance
evidence.
