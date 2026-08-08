# UI notes: delivery walkthrough + performance evidence

Companion to `ui/README.md`. Task-029: an end-to-end run sheet that a human can
execute, plus the recorded performance audit against the Phase-4 budgets
(`docs/TASK_BREAKDOWN.md` Task-029).

- [1. End-to-end run sheet](#1-end-to-end-run-sheet)
- [2. Where the `(mock)` / `(mô phỏng)` tag shows](#2-where-the-mock--mô-phỏng-tag-shows)
- [3. Teammate adoption walkthrough](#3-teammate-adoption-walkthrough)
- [4. Recorded performance evidence](#4-recorded-performance-evidence)
- [5. Budget checklist](#5-budget-checklist)

---

## 1. End-to-end run sheet

Run this once per machine/PR to confirm the whole UI works.

1. **Start the service** (repo root):
   ```bash
   python -m ui.service.main
   ```
   Wait for `Uvicorn running on http://127.0.0.1:8000`; probe
   `curl http://127.0.0.1:8000/api/health` → `{"status":"ok"}`.

2. **Start the frontend** (`ui/web`):
   ```bash
   npm install
   npm run dev
   ```
   Open http://localhost:5173. The status bar turns **Ready** once
   `GET /api/graph` has loaded (31 POIs on the map).

3. **BFS — real algorithm** (no marker):
   - Pick `Chợ Vạn Kiếp` as start, `Sân bay Tân Sơn Nhất` as goal.
   - Run **Breadth-First Search**. Expect: a route polyline, metrics panel
     populated (`Tổng quãng đường`, `Tổng thời gian ước tính`, `Tổng chi phí`,
     `Thời gian xử lý (ms)`), and an animation of expanded nodes.
   - Status bar shows the run **without** any `(mock)` marker; the explanation
     has no `mô phỏng` text → `source="real"`.

4. **DFS — mock fallback** (tagged):
   - Run **Depth-First Search** on the same pair. Expect:
     - status bar + history row show the **`(mock)`** marker,
     - the explanation panel reads `DFS - mô phỏng: …`,
     - same UI behavior as BFS (animation, metrics, replay) — the mock is
       transparent to the frontend.

5. **Replay**:
   - Open the history panel, click a recent run → it replays its steps.
   - The history list shows the `(mock)` badge only for mock runs.

6. **Status bar edge cases**:
   - Unknown start/goal → `400 INVALID_INPUT` envelope shown as an error state
     (never a stack trace).
   - Unknown algorithm → `404 ALGORITHM_UNKNOWN`.
   - With the service stopped, the frontend shows a **Retry** state instead of
     crashing.

---

## 2. Where the `(mock)` / `(mô phỏng)` tag shows

The frontend never hard-codes algorithm names; it branches on two payload
fields (GUI_ROADMAP.md § 13):

| UI element | Source | Marker |
|------------|--------|--------|
| Algorithm selector | `GET /algorithms` → `mock` flag | `(mock)` next to mock providers |
| Status bar | `POST /search` → `run.source` | `(mock)` when `source === "mock"` |
| History rows | `GET /history` → `run.source` | `mock` badge for mock runs |
| Explanation panel | `result.explanation` | Vietnamese text `… - mô phỏng: …` |

So a teammate module that flips an algorithm to `source="real"` (see § 3)
automatically removes every `(mock)` marker — no frontend change needed.

---

## 3. Teammate adoption walkthrough

Simulates the DFS teammate delivering `algorithms/dfs.py` (the seam proven by
`tests/ui/test_adoption.py`):

1. Drop a module `algorithms/dfs.py` registering, like `algorithms/bfs.py`:
   ```python
   @register_algorithm
   class DFSAlgorithm(SearchAlgorithm):
       name = "dfs"
       def search(self, graph, start, goal, **kwargs) -> SearchResult: ...
   ```
2. Restart the service. No catalog/service edits.
3. `POST /api/search` with `"algorithm": "dfs"` now returns
   `"source": "real"` (the mock fallback is bypassed; discovery imported the
   module on demand).
4. `GET /api/algorithms` still declares `mock: true` for `dfs` until the
   catalog is updated in `ui/service/backends.py` — the status bar uses the
   response `source`, so it already shows the real run correctly.

Fallback contract (unchanged by discovery): an unimportable module, a module
that registers nothing, or a registered placeholder (`NotImplementedError`)
still serves the mock with `source="mock"`.

---

## 4. Recorded performance evidence

Measured 2026-08-07, local dev machine (Windows), service via
`python -m ui.service.main`, client on the same machine (stdlib `urllib`,
loopback, no keep-alive). Warm caches (graph payload cached after first call).
20 search samples, 10 graph samples.

| Endpoint | min | mean | p95 | max | Budget | Verdict |
|----------|-----|------|-----|-----|--------|---------|
| `GET /api/graph` | 64.2 ms | 84.7 ms | 111.4 ms | 111.4 ms | ≤ 150 ms | pass |
| `POST /api/search` (BFS real) | 4.3 ms | 19.5 ms | 31.5 ms | 31.8 ms | p95 ≤ 300 ms | pass |
| `GET /api/version` | 2.4 ms | 10.0 ms | 32.5 ms | 32.5 ms | n/a (reference) | — |

Frontend budgets (first paint ≤ 200 ms, frame ≤ 4 ms, ≥ 30 fps) are browser
metrics and are measured manually with DevTools. They are still-open manual
checks — recorded in the checklist below as `[ ]`, pending one DevTools
Performance pass (Task-029 requires them recorded before final sign-off).

---

## 5. Budget checklist

Service-side (automated, see § 4):

- [x] `GET /api/graph` ≤ 150 ms
- [x] `POST /api/search` p95 ≤ 300 ms

Frontend-side (manual, DevTools **Performance** tab, ≥ 1280×800) — **open**;
each item needs one measured run recorded here before Task-029 acceptance is complete:

- [ ] First paint ≤ 200 ms
- [ ] Animation frame ≤ 4 ms while stepping a search
- [ ] ≥ 30 fps during step-by-step animation

Re-run § 4 whenever the graph dataset or the service changes; re-run the
manual checklist after frontend changes that touch rendering.
