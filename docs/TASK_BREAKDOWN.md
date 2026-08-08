# TASK_BREAKDOWN.md

**HCMC Delivery AI Search - GUI Engineering Backlog (executable)**

Version: 1.0

Owner: H (Hưng)

Status: **Single source of truth during implementation.**

Provenance: pure decomposition of `docs/IMPLEMENTATION_PLAN.md` (v1.0) and the frozen docs
(`GUI_ROADMAP.md` v2.0, `UI_DESIGN_SYSTEM.md`, `COMPONENT_SPEC.md`). This file adds **no** new
feature, architecture, API, component, or responsibility. Every task below maps 1:1 to an
existing `IMPLEMENTATION_PLAN.md` section (see §7 mapping table). If a task cannot be mapped,
it must not be created.

**Frozen constraints (inherited from the plan)**
- No edits to `core/search_result.py`, `algorithms/*`, `config`, `data` from this work.
- Service/public HTTP contract is exactly `GUI_ROADMAP.md §11`.
- Mock invariants are `GUI_ROADMAP.md §6.6`.
- Animation consumes `SearchStep` only (`GUI_ROADMAP.md §9`).
- New result fields live on the **service serialization** side, never `core`.

**Global gates (run after every task)**
- Backend: `python -m pytest` green; `ruff check .` clean.
- Web: `npm test` green; `npm run build` passes.
- Every commit is independently mergeable.

---

## 0. How to read this backlog

- One task = one commit + one merge unit, sized **1–3 h**. No task is larger.
- Task IDs are `Task-001 … Task-029`, ordered by dependency, grouped by phase.
- Each task lists its **Dependencies** by Task ID. If it has none, it is startable immediately.
- **Parallelizable** marks tasks that can run on a second workstream without merge conflicts.
- After every phase there is a **Milestone checkpoint (MS-0 … MS-4)** listing the gates.
- The **Plan ref** column/value in every task is the authoritative mapping to
  `IMPLEMENTATION_PLAN.md`; the §7 table is the machine-checkable summary.
- Estimated time is engineering time including the task's own tests, excluding the global gate.

---

## 1. Backlog

### PHASE 0 — Pre-flight (optional)

### Task-001 — Add `GREEDY` to `AlgorithmName`
- **Plan ref:** `IMPLEMENTATION_PLAN.md` § "Task 0.1"
- **Goal:** expose `AlgorithmName.GREEDY` additively so the catalog/selector can use a typed enum.
- **Dependencies:** none.
- **Estimated time:** 1 h.
- **Files created:** `tests/shared/test_enums.py`
- **Files modified:** `shared/enums.py` (only; additive)
- **Functions/classes:** member `GREEDY = "greedy"` on `AlgorithmName`.
- **Acceptance criteria:** `AlgorithmName.GREEDY.value == "greedy"`; no existing member changed;
  `pytest` + `ruff` green.
- **Unit tests:** `test_enums.py` — GREEDY value; all members unique.
- **Integration tests:** none.
- **Regression risks:** if a teammate has uncommitted edits to `shared/enums.py`, defer this task
  (plan § "Must wait for teammates").
- **Commit message:** `feat: add GREEDY to AlgorithmName`
- **Parallelizable:** Yes — independent of all `1.x`; skip if `"greedy"` string form suffices.

---

### PHASE 1 — Graph serving + map shell

### Task-002 — Scaffold `ui/service` package + deps in root manifest
- **Plan ref:** `IMPLEMENTATION_PLAN.md` § "Task 1.1" (package part)
- **Goal:** create the service package; declare its dependencies in the single root
  `requirements.txt` (the service is part of this project, not a microservice).
- **Dependencies:** none.
- **Estimated time:** 1 h.
- **Files created:** `ui/service/__init__.py`
- **Files modified:** `requirements.txt` (add `fastapi`, `uvicorn`)
- **Functions/classes:** none (package bootstrap).
- **Acceptance criteria:** `from ui.service import ...` imports; `requirements.txt` lists
  `fastapi` + `uvicorn`; `ruff check .` clean.
- **Unit tests:** none.
- **Integration tests:** none.
- **Regression risks:** none (no logic).
- **Commit message:** `feat(ui): scaffold service package`
- **Parallelizable:** Yes — independent.

### Task-003 — Graph loader + cache (`graphs.py`)
- **Plan ref:** `IMPLEMENTATION_PLAN.md` § "Task 1.1" (loader + cache)
- **Goal:** load delivery + road graphs once (cached) and build the `/graph` payload.
- **Dependencies:** Task-002.
- **Estimated time:** 1.5 h.
- **Files created:** `ui/service/graphs.py`, `tests/ui/service/__init__.py`,
  `tests/ui/service/test_graphs.py`
- **Files modified:** `ui/service/__init__.py` (exports)
- **Functions/classes:** `graphs.load_graphs()`, `graphs.get_delivery_graph()`,
  `graphs.get_road_graph()`, `graphs.get_graph_payload() -> dict` (graph/bbox/metadata).
- **Acceptance criteria:** `get_graph_payload()["metadata"]["node_count"] == 31` and
  `edge_count == 70`; two calls return identical (cached) objects; no `algorithms.*` import;
  `ruff` clean.
- **Unit tests:** `test_graphs.py` — node/edge counts; cache identity across calls.
- **Integration tests:** none.
- **Regression risks:** graph path drift; layer-order imports (only `data`/`delivery`, never
  `algorithms`).
- **Commit message:** `feat(ui): graph loader+cache`

### Task-004 — `/health` + `/graph` endpoints + GeoJSON + error envelope
- **Plan ref:** `IMPLEMENTATION_PLAN.md` § "Task 1.2" (session 1.2a)
- **Goal:** expose the graph over HTTP with the §11 shape and `503 GRAPH_NOT_FOUND`.
- **Dependencies:** Task-003.
- **Estimated time:** 2 h.
- **Files created:** `ui/service/main.py`, `ui/service/serialization.py`, `ui/service/errors.py`
- **Files modified:** `ui/service/__init__.py`
- **Functions/classes:** `main.create_app()`, `main.main()`; `serialization.to_graph_geojson()`,
  `serialization.bbox_of()`; `errors.ErrorEnvelope` / `errors.to_envelope()` (minimal; extended in
  Task-012).
- **Acceptance criteria:** `GET /health` → `200 {"status":"ok"}`; `GET /graph` → `200` with
  `graph/bbox/metadata` keys matching `GUI_ROADMAP §11`; forced load failure → `503
  GRAPH_NOT_FOUND` envelope; field names match `MAP_CONTRACT` (`latitude`/`longitude`,
  `edge_id`/`start`/`end`).
- **Unit tests:** deferred to Task-005 (contract).
- **Integration tests:** deferred to Task-005 (TestClient).
- **Regression risks:** serialized key renames vs `MAP_CONTRACT`; GeoJSON orientation must stay
  `[lon, lat]`.
- **Commit message:** `feat(ui): graph+health endpoints`

### Task-005 — Graph contract + API tests
- **Plan ref:** `IMPLEMENTATION_PLAN.md` § "Task 1.2" (session 1.2b)
- **Goal:** prove `/health` + `/graph` shape and the 503 path.
- **Dependencies:** Task-004.
- **Estimated time:** 1 h.
- **Files created:** `tests/ui/contract/__init__.py`, `tests/ui/contract/test_graph_payload.py`,
  `tests/ui/api/__init__.py`, `tests/ui/api/test_graph_flows.py`
- **Files modified:** none.
- **Functions/classes:** jsonschema for the §11 graph payload.
- **Acceptance criteria:** contract schema test green; TestClient `/graph` → 200; monkeypatched
  503 → `GRAPH_NOT_FOUND` envelope; full `pytest` green.
- **Unit tests:** contract schema test (jsonschema vs MAP_CONTRACT).
- **Integration tests:** TestClient 200 + 503 flows.
- **Regression risks:** none new.
- **Commit message:** `test(ui): graph contract + API flows`

### Task-006 — React/Vite shell + `api/client.ts` (mock|fetch transports)
- **Plan ref:** `IMPLEMENTATION_PLAN.md` § "Task 1.3" (scaffold + client) + §E.1/E.2
- **Goal:** boot the web app; client exposes `getGraph`/`getHealth` over pluggable
  `VITE_API_MODE=mock|http` transports.
- **Dependencies:** Task-005 (contract gold). May start from §E fixtures without the backend.
- **Estimated time:** 2 h.
- **Files created:** `ui/web/package.json`, `ui/web/vite.config.ts`, `ui/web/index.html`,
  `ui/web/src/main.tsx`, `ui/web/src/App.tsx`,
  `ui/web/src/api/{client.ts, transport.ts, types.ts}`,
  `ui/web/src/api/fixtures/*.json`,
  `ui/web/src/api/{fetch,mock}/client.ts`
- **Files modified:** none.
- **Functions/classes/components:** `App.tsx` (boot); `Layout`/`Header`/`StatusBar` skeleton
  (`§B.1`, `§D.8` base); `client.ts` public API `getGraph()`, `getHealth()`.
- **Acceptance criteria:** `npm run dev` boots; `getGraph` works via mock transport with no
  backend; switching `VITE_API_MODE=http` needs zero component changes; `npm run build` passes.
- **Unit tests:** `client.test.ts` (mock `fetch`) — response shape matches §11.
- **Integration tests:** none yet (fixture-based).
- **Regression risks:** `.env`/API-URL config; state shape drift (kept to §11).
- **Commit message:** `feat(ui): app shell+client`
- **Parallelizable:** Yes — can run alongside Task-004/005 when built against §E fixtures.

### Task-007 — Zustand store: graph slice + `loadGraph`
- **Plan ref:** `IMPLEMENTATION_PLAN.md` § "Task 1.3" (store part) + §B.4
- **Goal:** single store; graph slice + status; `loadGraph` action.
- **Dependencies:** Task-006.
- **Estimated time:** 1.5 h.
- **Files created:** `ui/web/src/state/store.ts`,
  `ui/web/src/state/slices/graphSlice.ts`, `ui/web/src/state/store.test.ts`
- **Files modified:** `ui/web/src/main.tsx` (mount store)
- **Functions/actions:** `store` (combineSlices); `graphSlice` `{geojsonNodes, geojsonEdges,
  bbox}`; status `Loading → Ready | Error`; action `loadGraph()`; selectors `selectGraph`,
  `selectStatus`.
- **Acceptance criteria:** after `loadGraph()`, `store.graph.edges.length === 70` (mock
  transport); status `Ready`; `npm run build` passes.
- **Unit tests:** `store.test.ts` — loadGraph populates graph; error → `Error`.
- **Integration tests:** none.
- **Regression risks:** slice-shape drift vs components (use narrow selectors, §B.4).
- **Commit message:** `feat(ui): graph slice+loadGraph`

### Task-008 — GraphCanvas static render (projection, Edges, Nodes, Empty)
- **Plan ref:** `IMPLEMENTATION_PLAN.md` § "Task 1.4" (render) + §C.1–C.3
- **Goal:** paint 31 nodes / 70 edges from the store; `MapPane` container; empty state.
- **Dependencies:** Task-007.
- **Estimated time:** 2.5 h.
- **Files created:** `ui/web/src/components/GraphCanvas/{index.tsx, index.module.css,
  index.test.tsx}`, `ui/web/src/components/MapPane/{index.tsx, index.module.css}`,
  `ui/web/src/lib/{coords.ts, format.ts}`,
  `ui/web/src/components/shared/{EmptyState, Spinner}`
- **Files modified:** `ui/web/src/App.tsx` (render `MapPane → GraphCanvas`)
- **Functions/classes/components:** `GraphCanvas` (store-driven, no props, `§D.1`);
  `lib/coords.project/projectPolyline/fitBounds`; `EdgeLayer` (memoised, `pointer-events:none`);
  `Nodes` (POI glyphs); `EmptyState`; `Spinner`.
- **Acceptance criteria:** paints 31/70 ≤ 200 ms; static layers memoised; `graph==null` →
  `EmptyState`.
- **Unit tests:** render 3 nodes/edges; empty when `graph==null`.
- **Integration tests:** visual check against the real service (marker count).
- **Regression risks:** SVG transform bugs; non-uniform scale must stay aspect-correct (§C.3).
- **Commit message:** `feat(ui): render graph canvas`

### Task-009 — GraphCanvas interactions (select/hover/tooltip/pan/zoom/fit + a11y)
- **Plan ref:** `IMPLEMENTATION_PLAN.md` § "Task 1.4" (interactions) + §C.4–C.5
- **Goal:** complete the canvas interaction model and accessibility fallback.
- **Dependencies:** Task-008.
- **Estimated time:** 2 h.
- **Files created:** `ui/web/src/components/shared/Tooltip` (custom tooltip),
  `ui/web/src/components/GraphCanvas/NodeListFallback` (a11y node list)
- **Files modified:** `ui/web/src/components/GraphCanvas/index.tsx` (interaction handlers)
- **Functions/components:** `onSelectNode` → store `selectNode`; `onHover`; wheel/pinch zoom
  anchored at pointer (scale 0.5–4); `Fit` + dblclick; `ResizeObserver` → viewBox; `aria-selected`;
  keyboard-reachable node list; native `<title>` + custom tooltip.
- **Acceptance criteria:** click selects (ring); hover highlights + tooltip (id, kind, name); zoom
  clamped; fit restores; node list reachable by keyboard; honours reduced-motion.
- **Unit tests:** node-click emits selection; zoom clamp; tooltip render.
- **Integration tests:** manual pan/zoom against the real graph.
- **Regression risks:** wheel must not steal sidebar scroll (`stopPropagation`, §C.4).
- **Commit message:** `feat(ui): canvas select/hover/zoom`

#### MS-1 checkpoint (end of Phase 1) — see §5.

---

### PHASE 2 — Neutral search on BFS

### Task-010 — SearchResult serialization + metrics helper
- **Plan ref:** `IMPLEMENTATION_PLAN.md` § "Task 2.1" (session 2.1a)
- **Goal:** turn a real `SearchResult` into the §11 response and derive metrics.
- **Dependencies:** Task-004 (payload style).
- **Estimated time:** 1.5 h.
- **Files created:** none (extends existing files).
- **Files modified:** `ui/service/serialization.py`
- **Functions/classes:** `serialization.search_result_to_contract(result)`,
  `serialization.metrics_from_result(result)` (hops, nodes_visited, distance_km, time_min, cost,
  processing_time_ms).
- **Acceptance criteria:** round-trips a real BFS `SearchResult` on the delivery graph; keys match
  §11 `POST /search` response; metrics derived from the result.
- **Unit tests:** serialization round-trip on a real BFS result.
- **Integration tests:** none.
- **Regression risks:** field-name drift vs `SearchResult`; never rename core fields.
- **Commit message:** `feat(ui): search serialization`
- **Parallelizable:** Yes — can run alongside Task-005…009 (frontend) after Task-004.

### Task-011 — Route expansion + `routing.run` (real-only)
- **Plan ref:** `IMPLEMENTATION_PLAN.md` § "Task 2.1" (session 2.1b)
- **Goal:** expand a POI path to street GeoJSON; run a real search via `run_algorithm`.
- **Dependencies:** Task-010.
- **Estimated time:** 1.5 h.
- **Files created:** `ui/service/routing.py`
- **Files modified:** none.
- **Functions/classes:** `routing.expand_path(path, graph, delivery_graph) -> dict | None`
  (via `delivery.route.expand_poi_path`); `routing.run(name, start, goal, enable_logging) ->
  (SearchResult, source)`.
- **Acceptance criteria:** `expand_path` returns a `[lon,lat]` polyline for a found path and `None`
  when `path==[]`; edge-missing `ValueError` is surfaced, not swallowed.
- **Unit tests:** route expansion returns a `LineString` for a found path, `None` for empty.
- **Integration tests:** none.
- **Regression risks:** `ValueError` from `path_total_cost` consistency must surface; `[lon,lat]`
  orientation.
- **Commit message:** `feat(ui): route expansion+routing`

### Task-012 — `POST /search` endpoint + full error mapping + history recording
- **Plan ref:** `IMPLEMENTATION_PLAN.md` § "Task 2.2" (session; recording hook per §2.6)
- **Goal:** expose `POST /search` with all §11 status codes and record runs.
- **Dependencies:** Task-011.
- **Estimated time:** 2 h.
- **Files created:** `ui/service/history.py` (service-side holder for core `SearchHistory`),
  `ui/service/errors.py` (extend: full §7 codes)
- **Files modified:** `ui/service/main.py` (add `create_search`)
- **Functions/classes:** `main.create_search()`; `errors` typed §7 codes
  (`InvalidInputError`, `AlgorithmUnknownError`, `AlgorithmUnavailableError`,
  `SearchFailedError`, `SearchTimeoutError`) + `error_response` for
  `INVALID_INPUT`/`ALGORITHM_UNKNOWN`/`ALGORITHM_UNAVAILABLE`/`SEARCH_FAILED`/
  `SEARCH_TIMEOUT`; `history.record(run)`.
- **Acceptance criteria:** `POST /search` → 200 (real BFS); unknown goal → `400 INVALID_INPUT`;
  unknown algorithm → `404 ALGORITHM_UNKNOWN`; timeout → `504 SEARCH_TIMEOUT`; run recorded;
  never leaks a stack trace.
- **Unit tests:** deferred to Task-013.
- **Integration tests:** TestClient status paths (Task-013).
- **Regression risks:** `SEARCH_TIMEOUT_MS` enforcement; envelope parity with `§7`.
- **Commit message:** `feat(ui): /search endpoint`

### Task-013 — `/search` API tests
- **Plan ref:** `IMPLEMENTATION_PLAN.md` § "Task 2.2" (tests)
- **Goal:** prove the `/search` status paths and contract keys.
- **Dependencies:** Task-012.
- **Estimated time:** 1 h.
- **Files created:** `tests/ui/api/test_search_flows.py`
- **Files modified:** none.
- **Functions/classes:** none.
- **Acceptance criteria:** positive 200; unknown algorithm → 404; unknown goal → 400; response keys
  match §11; full `pytest` green.
- **Unit tests:** status-path tests via TestClient.
- **Integration tests:** TestClient.
- **Regression risks:** none new.
- **Commit message:** `test(ui): /search status paths`

### Task-014 — Animation engine (pure reducer)
- **Plan ref:** `IMPLEMENTATION_PLAN.md` § "Task 2.4" + `GUI_ROADMAP §9`
- **Goal:** pure `SearchStep` → frame reducer, algorithm-agnostic.
- **Dependencies:** none (SearchStep only).
- **Estimated time:** 1.5 h.
- **Files created:** `ui/web/src/services/animation.ts`,
  `ui/web/src/services/animation.test.ts`
- **Files modified:** none.
- **Functions/classes:** `initialFrame()`, `applyFrame(prev, step)`, `isDone(frame, steps)`;
  frame model `{index, current, frontierIds, visitedIds, reason, isDone}`.
- **Acceptance criteria:** `activeIndex` advances monotonically; `isDone` true at last step; replay
  is independent of algorithm name.
- **Unit tests:** progress; `isDone` ends; independent of name.
- **Integration tests:** none.
- **Regression risks:** none (pure function).
- **Commit message:** `feat(ui): animation engine`
- **Parallelizable:** Yes — independent of backend; run alongside Task-012/013.

### Task-015 — Client API completion (search/listAlgorithms/getHistory/getVersion + envelope)
- **Plan ref:** `IMPLEMENTATION_PLAN.md` §E.2 (client), § "Task 1.3" client extension
- **Goal:** full client API with identical shapes across both transports and one error envelope.
- **Dependencies:** Task-006 (client base), Task-012 (search response shape).
- **Estimated time:** 1.5 h.
- **Files created:** `ui/web/src/api/fixtures/search.json`
- **Files modified:** `ui/web/src/api/client.ts`, `ui/web/src/api/types.ts`,
  `ui/web/src/api/fetch/client.ts`, `ui/web/src/api/mock/client.ts`
- **Functions/classes:** `client.search(algorithm,start,goal)`, `client.listAlgorithms()`,
  `client.getHistory()`, `client.getVersion()`; transports map failures → `ErrorEnvelope`
  `{code, message, details}`.
- **Acceptance criteria:** both transports return identical shapes; errors surface `ErrorEnvelope`;
  `VITE_API_MODE` switch works with zero component changes.
- **Unit tests:** `client.test.ts` (mock `fetch`) for each method + error mapping.
- **Integration tests:** fetch transport against the service via TestClient.
- **Regression risks:** `snake_case` preservation; envelope parity.
- **Commit message:** `feat(ui): client search+history+version`

### Task-016 — Search slice + `runSearch` + ControlPanel + StatusBar
- **Plan ref:** `IMPLEMENTATION_PLAN.md` § "Task 2.3" (ControlPanel part), §B.4/§B.7, §D.3, §D.8
- **Goal:** wire the search state machine and the control surface that drives it.
- **Dependencies:** Task-007 (store), Task-015 (client).
- **Estimated time:** 2.5 h.
- **Files created:** `ui/web/src/state/slices/searchSlice.ts`,
  `ui/web/src/components/ControlPanel/{index.tsx, index.module.css, index.test.tsx}`,
  `ui/web/src/components/shared/NodePicker`,
  `ui/web/src/components/StatusBar/{index.tsx, index.module.css}`
- **Files modified:** `ui/web/src/state/store.ts`, `ui/web/src/App.tsx` (Sidebar shell w/ ControlPanel)
- **Functions/actions/components:** `searchSlice` `{selectedAlgorithm, start, goal, result,
  source}`; action `runSearch()` (validate → `POST /search` → result/source); `setStatus`;
  status slice (8 states per `GUI_ROADMAP §8`); `ControlPanel` (Run disabled until start & goal &
  !busy; Enter submits; `snake_case` payload); `NodePicker`; `StatusBar` (`aria-live`, 8 states,
  `(mô phỏng)` tag, error block).
- **Acceptance criteria:** Run disabled-empty; selecting nodes targets the store; search payload is
  `snake_case`; StatusBar reflects every state.
- **Unit tests:** Run disabled when blank; `runSearch` calls client with selection; status
  transitions.
- **Integration tests:** manual BFS run against the service.
- **Regression risks:** invalid state-machine transitions (`§8`); store writers only via actions.
- **Commit message:** `feat(ui): control panel+status`

### Task-017 — AlgorithmSelector (catalog + `(mô phỏng)` tags)
- **Plan ref:** `IMPLEMENTATION_PLAN.md` § "Task 2.3" (selector part), §D.4
- **Goal:** catalog-driven selector; never branches on algorithm names.
- **Dependencies:** Task-015 (listAlgorithms), Task-016 (value/setAlgorithm).
- **Estimated time:** 1 h.
- **Files created:** `ui/web/src/components/AlgorithmSelector/{index.tsx, index.module.css,
  index.test.tsx}`
- **Files modified:** `ui/web/src/components/ControlPanel/index.tsx` (embed)
- **Functions/components:** `AlgorithmSelector` (props `catalog`, `value`, `disabled`;
  `onChange(name)`); renders `mock:true` items with the `(mô phỏng)` tag + sim icon; keyboard arrow
  navigation.
- **Acceptance criteria:** lists only BFS (from catalog) today; mock items tagged; arrow-key
  navigation; no name-branching logic.
- **Unit tests:** renders catalog; tag for mock; arrow nav.
- **Integration tests:** none.
- **Regression risks:** name-branching temptation (never; use catalog metadata only).
- **Commit message:** `feat(ui): algorithm selector`

### Task-018 — StepTimeline + AnimationControls + playback beat
- **Plan ref:** `IMPLEMENTATION_PLAN.md` § "Task 2.5", §D.5, §B.4 actions
- **Goal:** step slider + play/pause/step/restart; monotonic playback; `Finished`.
- **Dependencies:** Task-014 (animation), Task-016 (runSearch + status).
- **Estimated time:** 2.5 h.
- **Files created:** `ui/web/src/components/StepTimeline/{index.tsx, index.module.css,
  index.test.tsx}`, `ui/web/src/components/shared/AnimationControls`
- **Files modified:** `ui/web/src/state/store.ts` (timeline/step actions)
- **Functions/actions/components:** `advanceStep()`, `stepTo(i)`, `play()`, `pause()`,
  `restart()`; timeline slice `{activeIndex, playing, speed, status}` (roadmap `animation` slice);
  rAF playback scheduler (auto-pause on hidden tab, §A.8); frame → GraphCanvas.
- **Acceptance criteria:** slider draws steps; play→pause→resume; `stepTo` only in
  `Ready/Paused/Finished`; last step → `Finished`; `activeIndex` monotonic; timers safe on pause.
- **Unit tests:** play→pause→resume; step nav; finish→Finished.
- **Integration tests:** manual BFS playback.
- **Regression risks:** rAF leak on unmount; invalid transitions (`§8`).
- **Commit message:** `feat(ui): timeline UI`

### Task-019 — MetricsPanel
- **Plan ref:** `IMPLEMENTATION_PLAN.md` § "Task 2.6" (metrics part), §D.6
- **Goal:** render result metrics + explanation; empty state.
- **Dependencies:** Task-016 (result in store).
- **Estimated time:** 1.5 h.
- **Files created:** `ui/web/src/components/MetricsPanel/{index.tsx, index.module.css,
  index.test.tsx}`, `ui/web/src/lib/metrics.ts` (derived rows, tabular-nums)
- **Files modified:** `ui/web/src/App.tsx` (embed in Sidebar)
- **Functions/components:** `MetricsPanel` (props `result?`); rows `distance_km` / `time_min` /
  `cost` / `processing_time_ms` + explanation; empty state; copy button (lazy per §F.2).
- **Acceptance criteria:** renders metrics + explanation; updates per search; empty when no result.
- **Unit tests:** renders numbers (tabular); empty state; updates per search.
- **Integration tests:** none.
- **Regression risks:** locale formatting (use `Intl`, no `moment`, §F.3).
- **Commit message:** `feat(ui): metrics panel`

### Task-020 — Service `/history` + `/history/:id`
- **Plan ref:** `IMPLEMENTATION_PLAN.md` § "Task 2.6" (service part)
- **Goal:** list recent runs and fetch a full run for replay.
- **Dependencies:** Task-012 (recording hook + `history.py`).
- **Estimated time:** 1.5 h.
- **Files created:** `tests/ui/api/test_history_flows.py`
- **Files modified:** `ui/service/history.py` (add list/get), `ui/service/main.py` (add handlers)
- **Functions/classes:** `history.list_runs()`, `history.get_run(id)`;
  `main.get_history()`, `main.get_history_by_id()`.
- **Acceptance criteria:** `GET /history` → run summaries `{id, algorithm, start, goal, source,
  created_at, hops}`; `GET /history/:id` → full result incl. steps; `404 NOT_FOUND` for missing id.
- **Unit tests:** none service-side beyond tests.
- **Integration tests:** TestClient history flows.
- **Regression risks:** in-memory reset on restart (accepted; bounded `SearchHistory`).
- **Commit message:** `feat(ui): history endpoints`

### Task-021 — HistoryPanel + replay + Sidebar composition
- **Plan ref:** `IMPLEMENTATION_PLAN.md` § "Task 2.6" (panel part), §D.7, §B.2, §D.2
- **Goal:** list runs (lazy) and replay from stored steps with no network call; assemble Sidebar.
- **Dependencies:** Task-015 (getHistory), Task-018 (replay uses same playback actions),
  Task-020 (history endpoints).
- **Estimated time:** 2 h.
- **Files created:** `ui/web/src/components/HistoryPanel/{index.tsx, index.module.css,
  index.test.tsx}` (React.lazy), `ui/web/src/components/Sidebar/{index.tsx, index.module.css}`
- **Files modified:** `ui/web/src/App.tsx` (Sidebar assembles ControlPanel, StepTimeline,
  MetricsPanel, HistoryPanel), `ui/web/src/state/store.ts` (`replayRun`, `replay` flag)
- **Functions/actions/components:** `replayRun(id)` (hydrate from history slice, no network;
  `replay = true`); `HistoryPanel` (props `history`, `onReplay(id)`); `Sidebar` (drawer <768 px,
  §A.9).
- **Acceptance criteria:** lists runs (name, start, goal, result); click replays without an API
  call; empty state; lazy chunk loads after `Ready`; drawer at <768 px.
- **Unit tests:** renders runs; replay hydrates steps; empty state.
- **Integration tests:** manual replay.
- **Regression risks:** lazy-chunk suspense; replay vs fresh-search state.
- **Commit message:** `feat(ui): history panel+replay`

#### MS-2 checkpoint (end of Phase 2) — see §5.

---

### PHASE 3 — Mock algorithms (service only)

### Task-022 — mocks.py shared helpers + MockDFS
- **Plan ref:** `IMPLEMENTATION_PLAN.md` § "Task 3.1" (session 3.1a)
- **Goal:** mock provider base + DFS mock satisfying `§6.6`.
- **Dependencies:** Task-011 (reuse serialization/metrics helpers).
- **Estimated time:** 1.5 h.
- **Files created:** `ui/service/mocks.py`, `tests/ui/mocks/__init__.py`,
  `tests/ui/mocks/test_mock_dfs.py`
- **Files modified:** none.
- **Functions/classes:** `MockProvider` protocol; shared out-adjacency (same edge order as
  `run_algorithm("bfs", …)`) + edge-cost helpers (`algorithms.heuristic.edge_cost`); `MockDFS`
  (LIFO stack frontier, visited order recorded).
- **Acceptance criteria:** DFS mock satisfies `§6.6` on micro + delivery (path endpoints, step
  order, no self-loops, metric forms); `enable_logging=False` → `steps==[]`; deterministic.
- **Unit tests:** invariant tests on micro + delivery.
- **Integration tests:** none.
- **Regression risks:** deterministic neighbor order must match BFS cadence (§6.1).
- **Commit message:** `feat(ui): mock DFS`

### Task-023 — MockUCS + invariant tests
- **Plan ref:** `IMPLEMENTATION_PLAN.md` § "Task 3.1" (session 3.1b)
- **Goal:** cost-ordered UCS mock.
- **Dependencies:** Task-022.
- **Estimated time:** 1.5 h.
- **Files created:** `tests/ui/mocks/test_mock_ucs.py`
- **Files modified:** `ui/service/mocks.py` (extend)
- **Functions/classes:** `MockUCS` (priority queue relaxation).
- **Acceptance criteria:** `§6.6` invariants micro + delivery; cost-ordered frontier; metrics
  idempotent.
- **Unit tests:** invariant tests.
- **Integration tests:** none.
- **Regression risks:** re-seen nodes must never re-enter the frontier (§6.2).
- **Commit message:** `feat(ui): mock UCS`

### Task-024 — MockGreedy + MockAstar
- **Plan ref:** `IMPLEMENTATION_PLAN.md` § "Task 3.2"
- **Goal:** heuristic mocks via `algorithms.heuristic` + `haversine`.
- **Dependencies:** Task-023.
- **Estimated time:** 1.5 h.
- **Files created:** `tests/ui/mocks/test_mock_heuristic.py`
- **Files modified:** `ui/service/mocks.py` (extend)
- **Functions/classes:** `MockGreedy`, `MockAstar`.
- **Acceptance criteria:** `§6.6` invariants; greedy reaches goal; A* optimal on micro;
  deterministic tie-break.
- **Unit tests:** invariants + optimality on micro.
- **Integration tests:** none.
- **Regression risks:** tie-break determinism.
- **Commit message:** `feat(ui): mock Greedy/A*`

### Task-025 — backends.py catalog + real→mock fallback
- **Plan ref:** `IMPLEMENTATION_PLAN.md` § "Task 3.3"
- **Goal:** catalog + fallback so the frontend never knows which algorithm is real.
- **Dependencies:** Task-023, Task-024.
- **Estimated time:** 2 h.
- **Files created:** `ui/service/backends.py`, `tests/ui/service/test_backends.py`
- **Files modified:** `ui/service/main.py` (wire `run_search` into `/search`)
- **Functions/classes:** `AlgorithmCatalog` (names, labels, mock flags); `SearchBackend`;
  `run_search(name, …)` — try `run_algorithm`, on `KeyError`/`NotImplementedError` return the
  mock; `source` returned.
- **Acceptance criteria:** BFS → real; DFS → mock with `source:"mock"`; unknown name → error;
  catalog marks `mock` per name; contract response unchanged.
- **Unit tests:** `test_backends.py` — real / mock / unknown.
- **Integration tests:** TestClient with fallback active.
- **Regression risks:** fallback fires only for registry-miss/placeholder (roadmap §10 note);
  never mask a real crash.
- **Commit message:** `feat(ui): real->mock fallback`

#### MS-3 checkpoint (end of Phase 3) — see §5.

---

### PHASE 4 — Teammate-ready

### Task-026 — Dynamic algorithm discovery
- **Plan ref:** `IMPLEMENTATION_PLAN.md` § "Task 4.1"
- **Goal:** load real teammate modules on demand.
- **Dependencies:** Task-025.
- **Estimated time:** 1.5 h.
- **Files created:** none.
- **Files modified:** `ui/service/backends.py`
- **Functions/classes:** `import_module("algorithms." + name)` on demand; keep fallback behavior.
- **Acceptance criteria:** a teammate algorithm is found by discovery; still falls back on
  `KeyError`/`NotImplementedError`.
- **Unit tests:** discovery test with a fake module.
- **Integration tests:** none.
- **Regression risks:** module-level side effects on import; name collisions.
- **Commit message:** `feat(ui): dynamic algo import`

### Task-027 — Adoption + contract tests
- **Plan ref:** `IMPLEMENTATION_PLAN.md` § "Task 4.2"
- **Goal:** prove a real teammate algorithm bypasses the mock (`source=real`).
- **Dependencies:** Task-026.
- **Estimated time:** 2 h.
- **Files created:** `tests/ui/__init__.py`, `tests/ui/test_adoption.py`
- **Files modified:** none.
- **Functions/classes:** fake teammate algorithm registering via `ALGORITHM_REGISTRY`.
- **Acceptance criteria:** fake-team real `SearchResult` bypasses the mock (`source=real`); full
  contract suite green (every endpoint's JSON keys vs MAP_CONTRACT).
- **Unit tests:** adoption via TestClient.
- **Integration tests:** TestClient.
- **Regression risks:** registry coupling.
- **Commit message:** `test(ui): adoption seam`
- **Parallelizable:** Yes — can run alongside Task-028 after Task-026.

### Task-028 — Error-path + mock-invariant tests
- **Plan ref:** `IMPLEMENTATION_PLAN.md` § "Task 4.3"
- **Goal:** cover §7 error paths and finalize the `§6.6` invariant suite.
- **Dependencies:** Task-026.
- **Estimated time:** 2 h.
- **Files created:** `tests/ui/api/test_errors.py`, `tests/ui/mocks/test_invariants_all.py`
- **Files modified:** none.
- **Functions/classes:** none.
- **Acceptance criteria:** graph load failure → `503 GRAPH_NOT_FOUND`; timeout → `504
  SEARCH_TIMEOUT`; invalid input → `400 INVALID_INPUT`; `§6.6` invariants green on micro +
  delivery.
- **Unit tests:** invariant suite.
- **Integration tests:** TestClient error paths.
- **Regression risks:** timeout-test flakiness (inject a fake sleep).
- **Commit message:** `test(ui): error + mock invariants`
- **Parallelizable:** Yes — can run alongside Task-027 after Task-026.

### Task-029 — Delivery walkthrough + README + perf evidence
- **Plan ref:** `IMPLEMENTATION_PLAN.md` § "Task 4.4"
- **Goal:** end-to-end run sheet + docs + recorded performance audit.
- **Dependencies:** Task-027, Task-028.
- **Estimated time:** 2 h.
- **Files created:** `ui/README.md`, `docs/ui_notes.md` (documentation only)
- **Files modified:** none.
- **Functions/classes:** none.
- **Acceptance criteria:** run sheet executes end-to-end (service start, UI, BFS real, DFS mock
  with `(mô phỏng)` tag, replay, status bar); budgets recorded: `GET /graph` ≤ 150 ms, `POST
  /search` p95 ≤ 300 ms, first paint ≤ 200 ms, frame ≤ 4 ms, ≥ 30 fps.
- **Unit tests:** none.
- **Integration tests:** manual walkthrough.
- **Regression risks:** none.
- **Commit message:** `docs(ui): walkthrough + README`

#### MS-4 checkpoint (end of Phase 4) — see §5.

---

## 2. Milestone checkpoints

> Gates are run from the repo root. "Manual" = a human-driven visual/UX check on ≥ 1280×800.

### MS-0 — after Task-001 (Phase 0)
- [ ] `python -m pytest` green (incl. `tests/shared/test_enums.py`), `ruff check .` clean
- [ ] `npm` gates: n/a (no web code yet)
- [ ] Manual: n/a (enum only)

### MS-1 — after Task-009 (Phase 1)
- [ ] `python -m pytest` green (34 prior + new), `ruff check .` clean
- [ ] `npm test` green; `npm run build` passes
- [ ] Manual: start service → `GET /health` 200, `GET /graph` 200 with 31/70; UI boots to `Ready`;
      canvas paints 31 nodes / 70 edges; select/hover/zoom/fit work; empty graph → `EmptyState`
- [ ] Budget spot-check: `GET /graph` ≤ 150 ms; first paint ≤ 200 ms
- [ ] No edits to `core/search_result.py`, `algorithms/*`, `config`

### MS-2 — after Task-021 (Phase 2)
- [ ] `python -m pytest` green, `ruff check .` clean; `npm test` green; `npm run build` passes
- [ ] Manual: run a real BFS search via UI; play/pause/step to `Finished`; metrics panel shows
      numbers; history lists runs; replay works with no network call; empty/error states;
      StatusBar reflects all 8 states; keyboard + reduced-motion honoured
- [ ] Frame render ≤ 4 ms per advance; ≥ 30 fps during playback

### MS-3 — after Task-025 (Phase 3)
- [ ] `python -m pytest` green (mock invariants micro + delivery), `ruff check .` clean
- [ ] `npm` gates: unchanged from MS-2 (no web changes this phase)
- [ ] Manual: select DFS → `(mô phỏng)` tag visible; fallback works; catalog marks `mock` per name;
      verified that landing a real teammate algorithm needs **zero** frontend edits

### MS-4 — after Task-029 (Phase 4, final)
- [ ] Full `python -m pytest` (34 + new) green; `ruff check .` clean
- [ ] `npm test` green; `npm run build` passes
- [ ] Manual: full walkthrough per `ui/README.md` run sheet (service start, UI, BFS real, DFS
      mock, replay, status bar)
- [ ] Performance audit recorded (F.4): `GET /graph` ≤ 150 ms; `POST /search` p95 ≤ 300 ms;
      first paint ≤ 200 ms; frame ≤ 4 ms; ≥ 30 fps
- [ ] `ui/README.md` + `docs/ui_notes.md` written

---

## 3. Dependency graph

```
Phase 0        Task-001   (optional · parallel to everything)
                 │
Phase 1         Task-002 → Task-003 → Task-004 → Task-005 ─────────────────────────────┐
 (service)                  │            │                                             │
                 ┌──────────┘            ├──────────────► Task-010 → Task-011 → Task-012 → Task-013
                 │                       │                    (Phase 2 service)           │
                 ▼                       └──────────────► Task-006 → Task-007 → Task-008 → Task-009
            (Phase 1 web)                (006 may start from §E fixtures, parallel)       │
                                                                                         │
Phase 2        Task-010 → Task-011 → Task-012 → Task-013 ────────────► Task-015 ─► Task-016 ─► Task-017
                 │          │          │                                │            │
                 │          │          └────────────────────────────► Task-020 ─► Task-021
                 │          └────────────► Task-014 (parallel, independent)            ▲
                 │                          │                                           │
                 │                          └──────────────────────► Task-018 ─► Task-019 ┘
                 │
                 └───────────────────────────────────────────────────► Task-022 → Task-023 → Task-024 → Task-025
Phase 3                                                                                              │
Phase 4                                                                                              ▼
                                                                                              Task-026 → Task-027 ─► Task-029
                                                                                                          │
                                                                                                     Task-028 (parallel to 027)
```

**Cross-links not drawn as arrows (for readability):**
- Task-015 also needs Task-006 (client base).
- Task-016 also needs Task-007 (store) — drives the `└►` from 007 lane into 016.
- Task-018 needs Task-014 (animation) and Task-016 (runSearch/status).
- Task-021 needs Task-015 (getHistory), Task-018 (replay controls), Task-020 (history endpoints).
- Task-022 needs Task-011 (serialization/metrics helpers).
- Task-025 needs Task-023 **and** Task-024 (both mocks).
- Task-029 needs Task-027 **and** Task-028.

**Parallel development (from plan § "Cross-cutting 4"):**
- Task-001 parallel to any `1.x`.
- Task-010 parallel to Task-005…009 (frontend) after Task-004.
- Task-014 parallel to Task-012/013 (pure reducer, no backend).
- Task-027 and Task-028 in parallel after Task-026.
- Task-006 may start from §E fixtures in parallel with Task-004/005.

---

## 4. Implementation timeline

Solo critical path ≈ 41 h of engineering (plus gates). Weeks below assume ~60% utilization with
verification; parallel tasks shorten it if a second engineer helps.

| Week | Tasks | Expected deliverables | Merge points |
|---|---|---|---|
| **W1** | Task-001…009 (Phase 0 + 1) | optional `GREEDY`; service serving `/health` + `/graph` (31/70, cached); React shell boots to `Ready`; GraphCanvas paints with select/hover/zoom | After every green task; **MS-1** at week end |
| **W2** | Task-010…021 (Phase 2) | `POST /search` (real BFS, 4+ status codes); full client API; ControlPanel + AlgorithmSelector; animation; StepTimeline; MetricsPanel; `/history` + replay | After every green task; **MS-2** at week end |
| **W3** | Task-022…025 (Phase 3) | DFS/UCS/Greedy/A* mocks satisfying §6.6; catalog + real→mock fallback | After every green task; **MS-3** at week end |
| **W4** | Task-026…029 (Phase 4) | dynamic discovery; adoption + error-path tests; `ui/README.md` + `docs/ui_notes.md`; recorded perf audit | After every green task; **MS-4** = final delivery |

Second-engineer lanes (parallel, no merge conflicts): Task-001, Task-010, Task-014,
Task-027/Task-028.

---

## 5. Task → `IMPLEMENTATION_PLAN.md` mapping (no orphans, no duplicates)

| Task | Plan ref (section) | Task | Plan ref (section) |
|---|---|---|---|
| Task-001 | § "Task 0.1" | Task-016 | § "Task 2.3" (ControlPanel) + §D.3/§D.8 |
| Task-002 | § "Task 1.1" (package) | Task-017 | § "Task 2.3" (AlgorithmSelector) + §D.4 |
| Task-003 | § "Task 1.1" (loader+cache) | Task-018 | § "Task 2.5" + §D.5 |
| Task-004 | § "Task 1.2" (session 1.2a) | Task-019 | § "Task 2.6" (MetricsPanel) + §D.6 |
| Task-005 | § "Task 1.2" (session 1.2b) | Task-020 | § "Task 2.6" (service /history) |
| Task-006 | § "Task 1.3" (scaffold) + §E.1/§E.2 | Task-021 | § "Task 2.6" (panel) + §D.7/§D.2 |
| Task-007 | § "Task 1.3" (store) + §B.4 | Task-022 | § "Task 3.1" (session 3.1a) |
| Task-008 | § "Task 1.4" (render) + §C.1–C.3 | Task-023 | § "Task 3.1" (session 3.1b) |
| Task-009 | § "Task 1.4" (interactions) + §C.4–C.5 | Task-024 | § "Task 3.2" |
| Task-010 | § "Task 2.1" (session 2.1a) | Task-025 | § "Task 3.3" |
| Task-011 | § "Task 2.1" (session 2.1b) | Task-026 | § "Task 4.1" |
| Task-012 | § "Task 2.2" (endpoint) | Task-027 | § "Task 4.2" |
| Task-013 | § "Task 2.2" (tests) | Task-028 | § "Task 4.3" |
| Task-014 | § "Task 2.4" (+ roadmap §9) | Task-029 | § "Task 4.4" |
| Task-015 | §E.2 (client) + § "Task 1.3" client | | |

No task maps to more than one plan scope; every plan task 0.1–4.4 is fully decomposed with no
overlap.

---

## 6. Daily implementation workflow

```
1. Pick one task from the backlog (in order; honor its Dependencies).
2. Implement it (only files listed under "Files created/modified").
3. Run the task's unit tests.
4. Run the global gates: pytest && ruff check . && npm test && npm run build.
5. Fix defects before moving on; never commit red.
6. Commit with the task's commit message (one commit per task).
7. Merge (independently mergeable).
8. Re-check the dependency graph: are any now-unblocked tasks ready to pick next?
9. Repeat.
```

Rules:
- One task at a time. If blocked, pick the next unblocked task (see parallel lanes).
- If a mismatch with `GUI_ROADMAP.md` is found, update `GUI_ROADMAP.md` **first**, then this file.
- Any new task requires a `Plan ref`; un-mappable tasks are rejected (requirement §9/§10).
- Verify merge-ability: after each task the branch contains exactly that task's diff.

---

## 7. Change control

- This file is derived, never a source of decisions. Architecture, APIs, components, and
  responsibilities live in the frozen docs; this file only schedules their execution.
- Adding, removing, or re-scoping a task = re-mapping to `IMPLEMENTATION_PLAN.md`, not a design
  change. If no plan section covers the work, it is out of scope and must be raised with the
  roadmap owner first.
