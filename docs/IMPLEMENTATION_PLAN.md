# IMPLEMENTATION_PLAN.md

**HCMC Delivery AI Search - GUI Implementation Plan (single source of truth during dev)**

Version: 1.0

Owner: Hưng (all UI tasks)

Approved source of truth: `docs/GUI_ROADMAP.md` (v2.0). This plan converts the approved
phases (0–4) from the roadmap into executable tasks and 1–2 h coding sessions. It does **not**
change the architecture, any public API, any ownership boundary, or any milestone objective.
Where this file lists a concrete function/class name, it is the *execution* of a roadmap
element, never a new architectural rule.

**Frozen constraints**
- No edits to `core/search_result.py` or `algorithms/*` from GUI work.
- Service/public HTTP contract is exactly `GUI_ROADMAP.md §11`.
- Mock invariants are `GUI_ROADMAP.md §6.6`.
- Animation consumes `SearchStep` only (`GUI_ROADMAP.md §9`).
- Any new result field lives on the **service serialization** side, never `core`.

**Global gates**
- Backend: `python -m pytest` green; `ruff check .` clean.
- Web: `npm test` green; `npm run build` passes.
- Every commit is independently mergeable.

---

## 0. Conventions used in this plan

- **Task** = one mergeable unit (maps 1:1 to a `GUI_ROADMAP.md §16` milestone).
- **Session** = one 1–2 h block inside a task. Every task has ≥1 session; larger tasks have 2.
- **Owner** = H (Hưng) unless stated otherwise.
- **Public API** = what other layers / the HTTP client are allowed to depend on.
- **Internal API** = implementation detail; may change.
- Every `§17` task (P0–P4) maps to exactly one task or session below; `§16` milestone
  objectives and commit messages are 

---

## A. Full UI Design Specification

> Additive design layer. Consistent with `GUI_ROADMAP v2.0` `§14` (components, hooks, store,
> naming, CSS Modules, testing) and `§15`. Nothing here changes architecture or public APIs.

### A.1 Visual style
- **Character:** a calm, dense "delivery operations console" built around the map. Flat
  surfaces, restrained color, high legibility; a single vivid accent reserved for the running
  route. No glare, no heavy skeuomorphism.
- **Surface model:** light theme by default; panels are flat with a thin hairline border
  (`--c-border`) plus a near-white surface; elevation comes from border + faint shadow +
  `--c-surface-2` wells. Interaction is communicated with hover/active/focus, not glow.
- **Controls + states:** predictable hover/active/focus on every control, a discrete
  selected-state ring on canvas nodes, and a marching-ants dash for the animated route.
- **Density:** comfortable (8–12 px gutters) for pointer devices; a `compact` variant on the
  StepTimeline keeps a long search scannable.

---

### A.2 Color palette
Design tokens (only tokens, no ad-hoc hex in components):

| Token | Value | Use |
|---|---|---|
| `--c-bg` | `#F7F9FB` | app background |
| `--c-surface` | `#FFFFFF` | panels, cards |
| `--c-surface-2` | `#EEF3F5` | wells, inset, hover surfaces |
| `--c-border` | `#DFE5EA` | hairline borders |
| `--c-text` | `#17202A` | primary text |
| `--c-text-secondary` | `#5B6B7B` | captions, secondary |
| `--c-primary` | `#0E7768` | actions, active tabs (AA ≥ 4.5:1 on white) |
| `--c-primary-hover` | `#0A5F53` | hover of primary |
| `--c-accent` | `#F07A1D` | the running route path (AA ≥ 3:1 on light map) |
| `--c-selected` | `#15859C` | selected node ring |
| `--c-success` | `#2E7D32` | `Ready` / `Finished` |
| `--c-warning` | `#B26A00` | `Replay`, `(mô phỏng)` mock tag |
| `--c-danger` | `#C62828` | `Error`, destructive |
| `--c-frontier` | `#7C4DFF` | live frontier markers |

- Contrast: body text ≥ 4.5:1, large text / UI chrome ≥ 3:1 (WCAG AA).
- The `(mô phỏng)` tag is always `--c-warning` + a `sim` icon; never green. Meaning is never
  carried by color alone (the tag also reads text).

---

### A.3 Typography
- **Face:** system stack — `Inter, -apple-system, "Segoe UI", Roboto, sans-serif`; all numeric /
  data values use `font-variant-numeric: tabular-nums` for aligned columns.
- **Scale (px):** 11 label · 13 body · 14 emphasized · 16 panel title · 20 section · 32 app
  brand. Line-height 1.4 (display 1.2), letter-spacing 0 on body.
- **Weights:** 400 default, 500 emphasized labels, 600 controls/buttons, 700 numbers/titles.
- Headings carry proper semantic hierarchy; the map always exposes a text list of its nodes as
  an accessibility fallback.

---

### A.4 Spacing system
- 4-point scale: `4 / 8 / 12 / 16 / 24 / 32 / 48`.
- Panel padding 16, stacked-panel gutter 12, toolbar gutter 8–12, control-group gap 8.
  Tokenized (`--space-*`); no ad-hoc px.

---

### A.5 Shadows
- `--shadow-1` `0 1px 2px rgb(0 0 0 / .06)` — resting panels.
- `--shadow-2` `0 8px 24px -8px rgb(0 0 0 / .18)` — overlays, poppers, drawers.
- `--shadow-focus` `0 0 0 3px rgb(14 119 102 / .28)` — visible keyboard focus ring.
- Elevation is reserved for overlays/status; no glow-on-hover effects.

---

### A.6 Border radius
- `--radius-sm` 3 px (badges, tags) · `--radius-md` 8 px (inputs, cards) · `--radius-full`
  999 px (pills, toolbar buttons). Radius is contextual, not global.

---

### A.7 Icon library
- Inline SVG set in `ui/web/src/lib/icons.tsx` (stroke 1.5; 16/20/24) — no runtime icon
  dependency (offline-safe, tree-shakeable, theme-consistent).
- Icons are decorative by default (`aria-hidden`); meaning comes from text / `aria-label`.
- Set: `Play, Pause, StepForward, Reset, ZoomIn, ZoomOut, Fit, Route, Search, History, Clock,
  AlertCircle, Spinner, ChevronLeft, ChevronRight, Tag, Settings`.

---

### A.8 Animation principles
- Motile, short, unobtrusive; **transform/opacity only**, 150–250 ms `ease-out`; respect
  `prefers-reduced-motion: reduce` → 0 ms / static.
- Frame transition: a subtle fade/slide for a new step; route reveal via marching-ants dash.
- A running search never re-renders the whole tree on each beat — `animation.ts` computes the
  next frame and only the small animation surfaces update (see C.4, B.7).
- **Auto-pause when the tab is hidden**; playback pacing is user-gesture driven.

---

### A.9 Responsive breakpoints
| Window | Layout |
|---|---|
| ≥ 1200 px | 3 columns: map (flex 1) + sidebar (300 px) + inspector (320 px) |
| 768–1199 px | map + sidebar; inspector becomes a collapsible bottom drawer |
| < 768 px | single column; canvas full-bleed, panels stack below, toolbar docks to bottom |

- Core nodes/steps remain reachable from mobile (a compact node list is available beside the map).

---

### A.10 Loading / Empty / Error screens
- **Loading:** store `Loading` → skeleton panels, `Spinner`, MapCanvas shows a dashed bbox
  skeleton; controls disabled; `StatusBar` "Loading…".
- **Empty:** shared `EmptyState`; contextual copy ("Select start and goal, then Run");
  History/Metrics show their own empty state when empty.
- **Error:** shared `ErrorBox` (title + code + message + Retry). Distinct handling for graph
  load error, search error (uses `ErrorEnvelope` code), and network error.
- **Replay:** status `Replay` shows "Replay of <run>"; controls reuse the same Run surfaces.

---

### A.11 Accessibility rules
- Semantic landmarks (`<main>`, `<nav>`, `<aside>`); map has `role="img"` + accessible name
  + an equivalent keyboard-reachable list of nodes.
- Every control is keyboard usable (arrow keys to change node/step; Tab reaches all panels).
- Visible `:focus-visible` ring (`--shadow-focus`); never `outline: none` without an alternative.
- `aria-live="polite"` on the StatusBar and the search summary.
- Icons are `aria-hidden`; meaning never conveyed by color alone.
- Touch targets ≥ 44×44 px; no dead regions.

---

## B. React Architecture

### B.1 Component tree
```
App                          (boot: loadGraph, error/loading guard, providers)
└─ Layout
   ├─ Header                 (brand, version, connection status)
   ├─ MapPane (full-bleed)
   │  └─ GraphCanvas          ← the heavy SVG surface; one slider + layers
   ├─ Sidebar
   │  ├─ ControlPanel        (start/goal pickers + AlgorithmSelector + Run)
   │  ├─ StepTimeline        (list/steps + AnimationControls)
   │  ├─ MetricsPanel
   │  └─ HistoryPanel         (lazy-loaded)
   └─ StatusBar               (aria-live; error/empty floating overlays)
```
- Panels read the store; `GraphCanvas` is independent of side panels. `App`/`Layout` are the
  only components with significant effects.

---

### B.2 Folder ownership
```
ui/web/src/
├─ main.tsx                  (mount + providers)
├─ App.tsx                   (boot: loadGraph, error boundary)
├─ state/store.ts            (Zustand — single source of truth)
│  └─ slices/                (graphSlice, searchSlice, timelineSlice, historySlice, uiSlice)
├─ api/{client.ts, transport.ts, types.ts, fixtures/*.json}
├─ services/animation.ts     (pure step reducer + frame model)
├─ lib/{coords.ts, format.ts, icons.tsx, theme.css, filter.ts}
└─ components/
   ├─ GraphCanvas/  Sidebar/  ControlPanel/  AlgorithmSelector/
   ├─ StepTimeline/  MetricsPanel/  HistoryPanel/  StatusBar/
   └─ shared/  (Button, Select, NodePicker, ErrorBox, EmptyState, Spinner, useXxx hooks)
```
- Ownership: each folder owns its index + styles + tests; no circular imports; shared logic
  lives in `lib/` / `services/`.

---

### B.3 Hooks conventions
- `useState`/`useEffect` only at a component's *shell/leaf boundary*; all logic moves into
  plain functions/reducers (`animation.ts`, `lib/coords.ts`) so it is unit-testable without a
  component mounted.
- Custom hooks are `use*`, read the store via a selector, and **never write**. A hook that
  needs mutation exposes an action and returns it from the hook (e.g. `useRunSearch()` returns
  `{ run, status }`).
- No `useEffect` recompute for derived data; derive in selectors / `useMemo`. Effects are only
  for side-effects (fetch on boot, playback beat scheduling, `ResizeObserver`).

---

### B.4 Zustand usage
- One store, created once in `store.ts`; slices combined with `combineSlices`. Actions are the
  **only** writers: `loadGraph, runSearch, advanceStep, stepTo, play, pause, restart,
  replayRun, setStatus`.
- Components read via `useStore(s => s.slice)` narrow selectors; they never write slices
  directly. Writes happen only inside actions (single source of truth, testable).
- Selectors are pure functions returning stable references (e.g. `selectVisibleNodes`,
  `selectFrameAt(i)`), minimising subscriber churn.

---

### B.5 Memoization strategy
- `React.memo` on **leaf presentational** components with primitive or stable props
  (`Nodes`, `Edges`, `RouteOverlay`, `StepRow`, `MetricRow`); **not** on components that
  subscribe to the whole store (such a memo is pointless).
- Narrow store selectors → components re-render only when their slice changes.
- `useCallback` for callbacks passed into memoized children (`onStep`, `onReplay`,
  `onSelectNode`) with stable deps.
- `useMemo` for moderately expensive derived values (`visibleNodes`, route polyline points,
  metrics rows, timeline marks).

---

### B.6 Render flow
```
store change (frame / selection / graph)
  → subscribers fire
  → narrow selectors decide which components re-render
GraphCanvas: static layer (nodes/edges) is memoised → re-renders only when `graph` changes;
    animation layer re-renders on `frame`; route layer re-renders only when `path` changes.
```
- One frame commit per playback beat (~16–33 ms); cancel a pending `rAF` on pause.

---

### B.7 State update flow
- **Ready:** `App` calls `loadGraph()` → store sets `graph`, transitions `ui.status =
  Loading → Ready`.
- **Run:** `ControlPanel` emits `onRun(algorithm, start, goal)` → action `runSearch(...)` sets
  busy `Playing`-index → client resolves → store sets `result/steps`, `frame = 0`, status →
  `Playing` → StepTimeline/Metrics/History react to their slices.
- **Playback:** `services/animation.next(frame)` (pure) returns the next `frame`; a `play`
  scheduler beats at the cadence, writes `timeline.frame`; at the last step → status
  `Finished`.
- **Replay:** `HistoryPanel.onReplay(id)` → `replayRun(id)` loads stored steps into the same
  shapes; `ui.replay = true`; playback controls reuse the same actions.

---

## C. GraphCanvas Implementation Specification

### C.1 Rendering technology: SVG (primary)
- **SVG** for 31 nodes / 70 edges: crisp, fully accessible (DOM), no retina re-draw cost, free
  tiling/hover. Use `<g class="layer">` container groups for each layer.
- The Canvas-2D path is listed as an **optional** fallback only if a future graph size defeats
  the budget; the layer model and coordinate utils stay identical, so a swap is mechanical.
  Do not implement it now.

### C.2 Layers
Bottom → top:
1. base plate (subtle map grid / bbox frame)
2. `Edges` — polylines (static, `pointer-events:none`)  — memoised
3. `Nodes` — POI glyphs; each is a hotspot `<circle>`, hover ring, selected ring  — memoised
4. `RouteOverlay` — polyline of the expanded path, `--c-accent`, marching-ants dash; re-renders
   only when `path` changes
5. `AnimLayer` — live frontier (`--c-frontier`), current-node ring (pulse), visited tint;
   re-renders on each `frame` only

### C.3 Coordinate transformation
- Project GeoJSON `[lon, lat]` → view: `x = lon` (offset), `y = -lat` (offset); scale to fit
  bbox within the canvas viewBox with 4% margin, non-uniform `sx, sy` kept aspect-correct.
- `lib/coords.ts` exposes `project(node)` (precomputed id → (x,y) map), `projectPolyline`,
  `fitBounds(bbox, w, h)`, `worldToView`, `viewToWorld`.
- `ResizeObserver` updates `viewBox` on container resize.

### C.4 Interaction model
| Interaction | Trigger | Result |
|---|---|---|
| Pan | drag background / trackbpad | pans the scene `<g>`, clamped to fit+margin |
| Zoom | wheel (mouse), pinch (touch) | scale 0.5–4, anchored at pointer |
| Zoom fit | `Fit` button / double-click | fit whole graph |
| Select node | click a node | `selectNode(node)` → selected ring |
| Hover | pointer enter node/edge | highlight stroke + tooltip (id, kind, name) |
| Route | after a search result | animated marching-ants polyline |
- Handlers use `stopPropagation` to not steal sidebar scroll; wheel only zooms the map.

### C.5 Hover & selection & tooltips
- Static edge group has `pointer-events: none`; each node is its own `<g>` hotspot.
- Native `<title>` for hover tooltip plus a custom tooltip positioned on pointer for detail.
- Selection adds `selected` class → `--c-selected` ring; `current` class for the animation
  cursor. `aria-selected` is set on the selected node for a11y.

### C.6 Performance expectations
| Metric | Budget | Technique |
|---|---|---|
| First paint 31/70 | ≤ 200 ms | single commit, precomputed coords, no network blocking |
| Frame render (decay) | ≤ 4 ms / advance | memoised static layer + O(1) id lookups, no scans |
| Playback | ≥30 fps (target 60) | transform/opacity-only AnimLayer, rAF cadence |
| Pan/zoom | jank-free | transform-only via SVG `transform`, re-fit not recompute |
| Route expansion | ≤ 100 ms (backend) | handled on the Python service |

---

## D. Component Specifications

> Legend: **P** props, **S** owned state, **E** emitted events, **D** deps, **AC** acceptance.

### D.1 `GraphCanvas`
- **P:** `graph?`, `selection?`, `route?`, `frame?` (narrow selectors from store).
- **S:** `transform`, `hoveredNode`, `viewBox` (layout).
- **E:** `onSelectNode(nodeId)`, `onHover(nodeId?)`.
- **D:** `lib/coords.ts`, `shared/Button`, `layers/`, store actions.
- **AC:** draws every node/edge; click selects; hover tooltip; route polyline when `path`
  present; frontier/current ring; O(1) hotbox; resizes; honours reduced-motion; accessible
  node list fallback.

### D.2 `Sidebar` (composition root)
- **P:** none (composes children).
- **E:** none.
- **D:** `ControlPanel`, `StepTimeline`, `MetricsPanel`, `HistoryPanel`.
- **AC:** renders all child panels; their empty states; collapses to a drawer at < 768 px.

### D.3 `ControlPanel`
- **P:** `nodes`, `start`, `goal`, `busy` (from store).
- **S:** open/closed; focused picker fields.
- **E:** `onRun(algorithm, start, goal)`, `onChangeStart(id)`, `onChangeGoal(id)`.
- **D:** `shared/NodePicker`, `AlgorithmSelector`, `lib/format`.
- **AC:** Run disabled until start & goal && !busy; selector shows `(mô phỏng)` for mocks;
  emits `snake_case` payload; Enter submits when valid.

### D.4 `AlgorithmSelector`
- **P:** `catalog` (`{name,label,mock:boolean}[]`), `value`, `disabled`.
- **E:** `onChange(name)`.
- **D:** `lib/format`, `icons.tsx` (tag).
- **AC:** lists only BFS (from catalog) today; mock items tagged; keyboard arrow navigation.

### D.5 `StepTimeline`
- **P:** `steps`, `activeIndex`, `status`.
- **E:** `stepTo(n)`, `play`, `pause`, `restart`, `reset`.
- **D:** `services/animation.ts`, `shared/AnimationControls`, `lib/format`.
- **AC:** shows the step slider; monotonic advance; last step → `Finished`; pause stops the
  beat; `stepTo` only in `Ready/Paused/Finished`; replay is read-only for steps.

### D.6 `MetricsPanel`
- **P:** `result?` (SearchResult JSON).
- **E:** none.
- **D:** `lib/format` (tabular numbers), `shared/Button` (copy).
- **AC:** renders distance_km / time_min / cost / processing_time_ms + explanation; empty when
  no result; updates per search.

### D.7 `HistoryPanel`
- **P:** `history`, `onReplay(id)`.
- **E:** `onReplay(id)`.
- **D:** `lib/format`, lazy chunk.
- **AC:** lists runs (name, start, goal, result); click → replay from stored steps without a
  network call; empty state.

### D.8 `StatusBar`
- **P:** `status` (8-state machine), `result?`, `source`.
- **S:** none (derives aria-live text).
- **E:** none.
- **D:** store `uiSlice`.
- **AC:** `aria-live=polite`; maps all 8 states; adds `(mô phỏng)` when `source === "mock"`;
  error block shows code + message + Retry.

### D.9 `ErrorBox` / `EmptyState` (shared)
- **P:** ErrorBox: `title`, `message`, `action?`/`retry?`; EmptyState: `title`, `subtitle?`,
  `icon?`, `action?`.
- **D:** design tokens, `shared/Button`.
- **AC:** consistent visual, accessible region label, `Retry` action callback; reused everywhere
  (no per-file copies).

### D.10 Shared primitives
- `Button` (variants primary/secondary/danger/ghost, sizes, icons), `Spinner`,
  `NodePicker`, `Tooltip`. All honour reduced-motion and `--shadow-focus`.

---

## E. API Development Strategy (front-end-first)

### E.1 Order of work: contract → fixtures → mocks → real
1. Write the **DTO types** + **JSON fixtures** shaped by `MAP_CONTRACT` / `GUI_ROADMAP §11`
   first — no backend needed. Fixtures live in `src/api/fixtures/*.json` with the exact keys
   `§11` emits (`meta.schema_version`, `source`, and so on).
2. Implement a **client** with pluggable transports: a `fetchClient` (real HTTP) and a
   `mockClient` (serves fixtures, mirrors the error envelope, simulates small latency).
3. Swap mode via `VITE_API_MODE=mock|http`; switch to real API with **zero component changes**.

### E.2 Single public client API
```
src/api/client.ts       — public: getGraph, listAlgorithms, search, getHistory, getVersion
  ├─ fetch/client.ts    — real HTTP; maps failures to ErrorEnvelope
  └─ mock/client.ts     — serves fixtures with §-matching envelope (+ latency)
```
- Components depend only on `client.ts`. Tests run against `mock client` and the real service
  via `TestClient` — never against env-specific code.
- Errors surface the same `ErrorEnvelope` shape (`int code/status`, message) in both transports,
  so the UI handles one error path.

### E.3 Switching modes without touching components
- The App detects `VITE_API_MODE` (or server-first-available) and instantiates one transport;
  everything else imports from `client.ts`. Contract tests on the real service cover race.

---

## F. Performance Guidelines

### F.1 Selective memoization
- `React.memo` on leaf presentational components with primitive/stable props (`Nodes`, `Edges`,
  `RouteOverlay`, `StepRow`); never memo a component that subscribes to the whole store.
- `useMemo` for `visibleNodes`, `routePathPts`, `metricsRows`, `timelineMarks`.
- `useCallback` for stable callbacks (`onStep`, `onReplay`, `onSelectNode`).
- Narrow selectors everywhere else (B.5).

### F.2 Lazy loading
- `React.lazy` + `Suspense` for `HistoryPanel` and the metrics “export” helper (loaded after
  `Ready`); the map/shell stays in the core bundle.

### F.3 Bundle organization
```
core  : main.tsx + App + Layout + MapPane + GraphCanvas + store + api (small)
async : HistoryPanel + MetricsPanel-export + lib/format + icons
vendor: react, react-dom (long-cache; preload on Ready)
```
- Tree-shaking icons; no date/moment — use `Intl`.

### F.4 Performance budget verification
- After Phase 4, verify: `GET /graph` ≤ 150 ms; `POST /search` p95 ≤ 300 ms; first paint ≤ 200
  ms; live frame ≤ 4 ms; frame ≥ 30 fps. Record results in the Phase 4 evidence.

---

## G. Acceptance criteria by task

> Acceptance = the observable proof that the task is done beyond "tests pass". Every test /
> gate below is run from the repo root.

| **Task** | **Acceptance criteria** |
|---|---|
| 0.1 | `AlgorithmName.GREEDY` exists, value `"greedy"`; enum uniqueness test green; no other member changed; `pytest`+`ruff` green. |
| 1.1 | `get_graph_payload()` returns 31 nodes / 70 edges; cache id-equivalent across two calls; service imports with no `algorithms` dep; fire `ruff` clean. |
| 1.2 | `/health` → 200 `{"status":"ok"}`; `/graph` → 200 body matches §11 sample keys; forced 503 → `GRAPH_NOT_FOUND` envelope; contract schema test green. |
| 1.3 | Shell boots to `Ready`; after `loadGraph`, `store.graph.edges.length === 70`; mock-client test green; `npm run build` passes. |
| 1.4 | Canvas paints 31 nodes / 70 edges; click emits `onSelectNode`; hover highlights; empty graph → `EmptyState`; first paint < budget. |
| 2.1 | A real BFS `SearchResult` round-trips via `serialization`; `expand_path` → polyline or `null`; metrics derived; contract test asserts §11 keys. |
| 2.2 | `/search` positive case passes; unknown algorithm → `ALGORITHM_UNKNOWN`; unknown goal → `INVALID_INPUT`; the 4 status tests green. |
| 2.3 | Selector lists only BFS (from catalog); `(mô phỏng)` tag; Run disabled until start & goal; payload emitted uses `snake_case` keys. |
| 2.4 | `animation.ts` reducer is monotonic; `isDone` ends; replay independent of name; unit test green. |
| 2.5 | Timeline draws each step; play/pause/step work; final step → `Finished`; RTL tests green. |
| 2.6 | History records runs; replay uses stored steps without an API call; metrics panel renders numbers. |
| 3.1 | DFS/UCS mocks satisfy §6.6 invariants on micro + delivery; logging off → empty steps; metrics idempotent. |
| 3.2 | Greedy/A* inherit §6.6; deterministic via tie-breaker; all reach goal. |
| 3.3 | BFS → real path; DFS → mock with `source:"mock"`; per-name `mock` flag in catalog; unknown name → error. |
| 4.1 | Dynamic `importlib` discovery for a real teammate algorithm; still falls to mock on `KeyError`/`NotImplementedError`. |
| 4.2 | Adoption test: a fake-team algorithm returning a real `SearchResult` bypasses the mock (`source=real`); contract tests green. |
| 4.3 | Error-path tests for graph load failure (503), timeout (`504 SEARCH_TIMEOUT`), invalid input (400); §6.6 invariants on micro + delivery. |
| 4.4 | The run sheet executes end-to-end: service start, UI, BFS real, DFS mock `(mô phỏng)`, budget check recorded. |

---

## H. Definition of Done (per phase)

### Phase 0 — Pre-flight
- [ ] (if enabled) `shared/enums.py` is additive-only; `AlgorithmName` tests green; `pytest` +
      `ruff` green.

### Phase 1 — Graph serving + map shell
- [ ] Service graph loader cached; `/health` + `/graph` tested via `TestClient`.
- [ ] App boots, `loadGraph` populates store, StatusBar shows state; canvas paints 31/70.
- [ ] Budget spot-check: `GET /graph` ≤ 150 ms; first paint ≤ 200 ms.
- [ ] No edits to `core/search_result.py`, `algorithms/*`, `config`; 34+ prior tests still green.

### Phase 2 — BFS search
- [ ] `/search` contract round-trip; metrics; 4 status codes; history recording.
- [ ] Controls + selector (BFS only) + `(mô phỏng)` tag + disabled-empty; StepTimeline + play/
      pause/step + `Finished`; Metrics + History + replay.
- [ ] UI frame ≤ 4 ms (advance); ≥ 30–60 fps; keyboard + reduced-motion honoured.
- [ ] `pytest`, `ruff`, `npm test`, `npm run build` all green.

### Phase 3 — mocks
- [ ] DFS/UCS, Greedy/A* mocks satisfy §6.6 invariants on micro + delivery; fallback + `source`/
      `mock` flag; tests for both micro and delivery graphs.
- [ ] Verified that landing a real teammate algorithm needs **zero** edits.

### Phase 4 — teammate-ready
- [ ] Dynamic discovery + adoption (BFS real, fake-team real, DFS mock).
- [ ] Error-path + invariant tests complete; walkthrough doc + `ui/README.md; performance audits recorded.
- [ ] Full `pytest` (34 + new), `ruff`, `npm test`, `npm run build` all green.

---

## Phase 0 — (optional) `GREEDY` in `AlgorithmName`

> Optional: only needed if the selector wants a typed enum for `greedy`. The service may also
> use the string `"greedy"` directly (roadmap §10). Enable it only if it does not conflict with
> a teammate's in-progress enum. If skipped, Phase 3/4 use the string form.

### Task 0.1 — Add `GREEDY` member

- **Objective**: expose `AlgorithmName.GREEDY` additively.
- **Owner:** H (core).
- **Dependencies:** none.
- **Files to create:** `tests/shared/test_enums.py`.
- **Files to modify:** `shared/enums.py` (only).
- **Functions/classes:** member `GREEDY = "greedy"` on `AlgorithmName`.
- **Expected public API:** `AlgorithmName.GREEDY` (additive; all existing members unchanged).
- **Internal API:** none.
- **Estimated LOC:** ~1 + ~8 test.
- **Difficulty:** trivial.
- **Regression risks:** additive-only; no risk. If a teammate is mid-edit of `enums.py`,
  defer this task (see §1).
- **Tests:** unit `AlgorithmName.GREEDY.value == "greedy"`; all members unique.
- **Integration:** none.
- **Commit:** `feat: add GREEDY to AlgorithmName`

---

## PHASE 1 — graph serving + map rendering (no search)

### Task 1.1 — Service package + graph loader + cache
- **Objective:** load `data/exports/delivery_graph.json` + road graph once and serve them.
- **Owner:** H.
- **Dependencies:** none.
- **Files created:** `ui/service/__init__.py`, `ui/service/graphs.py`
- **Files modified:** `requirements.txt` (add `fastapi`, `uvicorn` to the single root manifest).
- **Functions/classes:**
  - `graphs.load_graphs() -> tuple[DeliveryGraph, RoadGraph]` (cached via module-level `lru_cache`/singleton).
  - `graphs.get_delivery_graph() -> DeliveryGraph`
  - `graphs.get_road_graph() -> RoadGraph`
  - `graphs.get_graph_payload() -> dict` (features + bbox + meta)
- **Expected public API (service):** none yet (no HTTP).
- **Internal API:** the four functions of `graphs`.
- **Estimated LOC:** ~80.
- **Difficulty:** low.
- **Regression risks:** graph path drift; importing `delivery.loader`/`data.loader`/`RoadGraph`
  without breaking layer order. Ensure no import of `algorithms.*`.
- **Unit tests:** `tests/ui/service/test_graphs.py` — `get_graph_payload()` returns 31 nodes/70 edges;
  cache returns same object on two calls.
- **Integration tests:** none yet.
- **Commit:** `feat(ui): graph loader+cache`

**Session 1.1a — package + loader (≈1.5 h)**
- **Goal:** create the service package with a working graph loader.
- **Files:** `ui/service/__init__.py`, `ui/service/graphs.py`,
  `tests/ui/service/test_graphs.py`, `tests/ui/service/__init__.py`, `requirements.txt`.
- **Order:**
  1. Create `ui/service/__init__.py` (docstring; empty per convention).
  2. Add the service dependency packages to the root `requirements.txt` (single manifest;
     the service is part of this project, not independently deployable).
  3. Implement `graphs.py`: `load_graphs()` loads `delivery` + `road` and returns a
     dataclass/tuple; backend caches with `@functools.lru_cache`.
  4. Add tests,then run `pytest -q` + `ruff`.
- **Expected output:** `from ui.service import graphs; graphs.get_graph_payload()["metadata"]["node_count"] == 31`.
- **DoD:** public script outputs 31 nodes / 70 edges; two loader calls return identical objects; tests green.
- **Regression checklist:** import graph intact; `ruff` clean; no web code exists yet.

### Task 1.2 — `/graph` + `/health` endpoints + GeoJSON
- **Objective:** expose the graph over HTTP.
- **Owner:** H.
- **Dependencies:** 1.1.
- **Files created:** `ui/service/main.py`, `ui/service/serialization.py` (graph part),
  `ui/service/errors.py` (minimal `ErrorEnvelope`, extended later in 2.2).
- **Files modified:** none.
- **Functions/classes:**
  - `main.create_app() -> FastAPI`
  - `main.main()` (uvicorn run)
  - `serialization.to_graph_geojson(...)`, `serialization.bbox_of(...)`
- **Expected public API (HTTP):** `GET /health → 200 {"status":"ok"}`, `GET /graph → 200`
  with `graph/bbox/meta` (`GUI_ROADMAP §11`), `503 GRAPH_NOT_FOUND` on load failure.
- **Internal API:** `main` handlers call `graphs.get_graph_payload`, `errors.to_envelope`.
- **Estimated LOC:** ~90.
- **Difficulty:** low.
- **Regression risks:** serialized keys must match MAP_CONTRACT exactly (no renames); GeoJSON
  orientation `[lon, lat]`.
- **Tests:** contract test `tests/ui/contract/test_graph_payload.py` (jsonschema vs MAP_CONTRACT);
  `tests/ui/contract/__init__.py`.
- **Integration:** `tests/ui/api/test_graph_flows.py` — `TestClient` asserts `/graph` 200 and
  `503` on forced load failure (monkeypatched).
- **Commit:** `feat(ui): graph+health endpoints`

**Session 1.2a — serialization + handlers (≈1 h)**
- **Goal:** implement `serialization.py` graph payload and `main.py` `/health` `/graph`.
- **Files:** `ui/service/main.py`, `ui/service/serialization.py`, `ui/service/errors.py`.
- **Order:** 1) `serialization.graph_payload(...)`; 2) `errors.ErrorEnvelope`; 3) `main.get_health`;
  4) `main.get_graph` wrapping load errors into the envelope; 5) `main()` runs uvicorn.

**Session 1.2b — API + contract tests (≈1 h)**
- **Goal:** prove endpoints + shape.
- **Files:** `tests/ui/contract/test_graph_payload.py`, `tests/ui/api/test_graph_flows.py`.
- **Steps:** 1) contract schema test; 2) `TestClient` 200 assertion; 3) monkeypatched 503; 4) run tests.
- **DoD:** `/health` 200; `/graph` 200 matches §11 sample shape; 503 path covered.
- **Regression:** rerun full `pytest`; nothing else changed.

### Task 1.3 — React shell + store (graph slice)
- **Objective:** boot the React app and store, fetching the graph.
- **Dependencies:** 1.2 (contract/gold), can build against a local fixture.
- **Owner:** H.
- **Files created:** `ui/web/package.json`, `ui/web/vite.config.ts`, `ui/web/index.html`,
  `ui/web/src/main.tsx`, `ui/web/src/api/client.ts`, `ui/web/src/state/store.ts`.
- **Functions/classes:**
  - `api/client.ts`: `getGraph()`, `getHealth()`, later `getHistory()/search()/listAlgorithms()`.
  - `state/store.ts`: slices `graph { geojsonNodes, geojsonEdges, bbox }`, plus `search`
    placeholder defaults.
- **Public APIs (web internal):** `useStore`, `fetchGraph()` action; `graph` selectors.
- **Estimated LOC:** ~90.
- **Difficulty:** med.
- **Regression risks:** state shape drift vs components; missing `.env` for API URL.
- **Tests:** component `web/src/api/client.test.ts` (mock `fetch`);
  `web/src/state/store.test.ts` (Zustand actions).
- **Integration:** run `npm run dev` against service; canvas shows node count later.
- **Commit:** `feat(ui): app shell+store`

**Session 1.3 — shell + client + store (≈1.5 h)**
- **Goal:** App loads, store populates `graph`.
- **Files/order:** scaffold react/vite; `client.ts` with `fetchGraph()`; `store.ts` with
  `loadGraph` action + loading/error slice; tests for `loadGraph` using a stubbed `fetch`.
- **Expected output:** store `graph.edges.length === 70` after `loadGraph()`.
- **DoD:** unit tests green; `npm run build` passes.

### Task 1.4 — GraphCanvas (render + select/hover)
- **Objective:** render nodes+edges and surface select/hover.
- **Dependencies:** 1.3.
- **Files created:** `ui/web/src/components/GraphCanvas/{index.tsx,index.module.css,index.test.tsx}`,
  plus shared `components/shared/{Empty,Spinner}`.
- **Public API (React):** `<GraphCanvas/>` no props; reads store; emits `selectNode`, `hoverNode`.
- **Estimated LOC:** ~130.
- **Difficulty:** med.
- **Regression risks:** many-node layers outweigh; wrong SVG coordinate transform.
- **Tests:** render 3 nodes/edges; empty when `graph==null`; node-click emits selection.
- **Integration:** visual check after serving real graph (count markers).
- **Commit:** `feat(ui): render graph canvas`

**Session 1.4 (≈2 h)**
- **Steps:** build a viewport→world transform; paint edges (GeoJSON LineString) then nodes
  (points), color by kind; subscribe select/hover to store; add `EmptyState` + `Spinner`;
  component + snapshot tests.
- **DoD:** the canvas renders 31 POIs / 70 edges with selection highlight and hover tooltip.

---

## PHASE 2 — neutral search on BFS

### Task 2.1 — Search result serialization + routing (real-only)
- **Objective:** turn a real `SearchResult` into the MAP_CONTRACT response and compute metrics.
- **Owner:** H.
- **Dependencies:** 1.2 (payload style), plus contract docs.
- **Files created:** `ui/service/routing.py`, `ui/service/serialization.py` (extend).
- **Functions/classes:**
  - `serialization.search_result_to_contract(result) -> dict`
  - `serialization.metrics_from_result(result) -> dict`
  - `routing.expand_path(path, graph, delivery_graph) -> dict | None`
  - `routing.run(name, start, goal, enable_logging) -> (SearchResult, source)`
- **Public (service):** none yet (called by main in 2.2).
- **Regression risks:** field-name drift vs `SearchResult`; edge-missing `ValueError` now raising
  (path_total_cost consistency) must be surfaced, not swallowed.
- **Tests:** serialization round-trip on a real BFS `SearchResult` (run on delivery graph);
  route expansion returns a `LineString` for a found path, `None` when `path==[]`.
- **Commit:** `feat(ui): search + serialization`

**Sessions 2.1a/2.1b (2×1 h):** implement serialization → metric helper → route expansion →
tests. DoD: contract test asserts exact `GUI_ROADMAP §11` `POST /search` response keys.

### Task 2.2 — `POST /search` + metrics
- **Objective:** `POST /search` → 200/400/409/500/504, `GUI_ROADMAP §11`.
- **Depends:** 2.1.
- **Files:** `ui/service/main.py` (extend), `ui/service/errors.py` (extend).
- **Owner:** H.
- **Functions:** `errors` typed §7 codes (`InvalidInputError`,
  `AlgorithmUnknownError`, `AlgorithmUnavailableError`, `SearchFailedError`,
  `SearchTimeoutError`) + `error_response`; `main.create_search()` calling
  `routing.run(...)` then serializing + recording `SearchHistory`.
- **Estimated LOC:** ~70.
- **Difficulty:** med.
- **Tests:** API test positive + `INVALID_INPUT` (unknown goal) + `ALGORITHM_UNKNOWN`.
- **Commit:** `feat(ui): /search endpoint`

**Session 2.2 (≈1.5 h):** add search error types; wire handler; test the 4 status paths.

### Task 2.3 — ControlPanel + AlgorithmSelector (BFS)
- **Depends:** 2.2 (search response shape).
- **Files:** `ui/web/src/components/ControlPanel/`, `AlgorithmSelector/`.
- **Owner:** H.
- **Scope:** start/goal pickers (from graph nodes), Run disabled until both set; selector list =
  catalog (only BFS today); `(mô phỏng)` tag rendered for `mock:true`.
- **Estimated LOC:** ~100.
- **Difficulty:** med.
- **Tests:** Run disabled when blank; selecting nodes targets store; API called with selection.
- **Commit:** `feat(ui): controls + selector(BFS)`

**Session 2.3 (≈1.5 h):** picker selects; store `runSearch` re-used; tests.

### Task 2.4 — Animation engine (pure reducer)
- **Depends:** concept from §9 roadmap (SearchStep only).
- **Files:** `ui/web/src/services/animation.ts`, `animation.test.ts`.
- **APIs:** `initialFrame()`, `applyFrame(prev, step)`, `isDone(frame, steps)`.
- **LOC ~40/low.**
- **Tests:** progress; `isDone` ends; replays independent of name.
- **Commit:** `feat(ui): animation engine`

**Session 2.4 (≈1 h):** reduce frame; test.
**Session 2.4b (≈1 h):** `applyFrame` current/frontier/reason; binding.

### Task 2.5 — StepTimeline + animation controls
- **Depends:** 2.4 + 2.3.
- **Files:** `StepTimeline/{index, styles, test}.`, `AnimationControls/`.
- **LOC ~90/med. Tests:** play→pause→resume; step nav; finish→Finished.
- **Commit:** `feat(ui): timeline UI`

**Session 2.5 (≈1.5 h)**
- **Steps:** build the step slider; play/pause/step handlers; fwd/back; timers safe on pause.
- **DoD:** monotonic `activeIndex`; a11y labels; `Finished` at last step.

### Task 2.6 — Metrics + history panels + `/history`
- **Depends:** 2.2, 2.5.
- **Files:** `MetricsPanel/`, `HistoryPanel/`, service `/history` + recording; web client
  `getHistory`, `replay(id)`.
- **LOC ~110/med.**
- **Tests:** metrics render; replay uses stored steps.
- **Commit:** `feat(ui): metrics + history`

**Session 2.6 (≈1.5 h):** record runs; list + replay; metrics panel; tests.

---

## PHASE 3 — mock algorithms (service only)

### Task 3.1 — mocks DFS + UCS
- **Owner:** H.
- **Depends:** 2.1 (reuse serialization/metrics helpers).
- **Files:** `ui/service/mocks.py`.
- **APIs:** `MockProvider`; `MockDFS`, `MockUCS`.
- **Implementation contract per `GUI_ROADMAP §6.6`:**
  - deterministic neighbor order from `graph.edges`;
  - DFS: LIFO stack frontier, visited order recorded;
  - UCS: cost-ordered priority queue (`heapq` via `algorithms.heuristic.edge_cost`), relaxation.
- **LOC ~95/med.**
- **Tests (mock invariants §6.6):** path endpoints, step order, no self-loops, metric forms.
- **Commit:** `feat(ui): mock DFS/UCS`

**Session 3.1a:** shared out-adjacency/edge-cost helpers; MockDFS.
**Session 3.1b:** MockUCS + invariant tests on micro + delivery.

### Task 3.2 — mocks Greedy + A*
- **Depends:** 3.1 (shared helpers).
- **File:** `ui/service/mocks.py` (extend).
- **APIs:** `MockGreedy`, `MockAstar` (heuristic via `algorithms.heuristic` + `haversine`).
- **Tests:** invariants; greedy reaches goal; A* optimality on micro.
- **Commit:** `feat(ui): mock Greedy/A*`

### Task 3.3 — real→mock fallback (backends closure)
- **Depends:** 3.1 + 3.2.
- **File:** `ui/service/backends.py`.
- **APIs:** `AlgorithmCatalog`, `SearchBackend`, `run_search`.
- **Behavior:** try `run_algorithm`; on `KeyError`/`NotImplementedError` return the mock; else real.
  `source` returned; catalog marks `mock` per name.
- **Tests:** BFS real; DFS mock; unknown name error.
- **Commit:** `feat(ui): real->mock fallback`

---

## PHASE 4 — teammate-ready

### Task 4.1 — dynamic algorithm discovery
- **File:** `ui/service/backends.py`.
- **Depends:** 3.3.
- **Mechanism:** `import_module("algorithms." + name)` on demand; keep fallback behavior.
- **Commit:** `feat(ui): dynamic algo import`

### Task 4.2 — adoption + contract tests
- **File:** `tests/ui/test_adoption.py`, `tests/ui/__init__.py`, `tests/ui/contract/`.
- **Test:** a fake teammate algorithm (real `SearchResult`) bypasses the mock (`source=real`).
- **Commit:** `test(ui): adoption seam`

### Task 4.3 — error-path + mock-invariant tests
- **Files:** `tests/ui/api/`, `tests/ui/mocks/`.
- **Test of §7 errors:** graph load failure (503), timeout (`504 SEARCH_TIMEOUT`), invalid (400).
- **Commit:** `test(ui): error + mock invariants`

### Task 4.4 — delivery walkthrough + README/ui notes
- **Depends:** 4.1.
- **Files:** `ui/README.md` + `docs/ui_notes.md` (documentation only).
- **Goal:** end-to-end run sheet (service start, UI, BFS real, DFS mock, `(mô phỏng)` tag).
- **Commit:** `docs(ui): walkthrough + README`

---

## Cross-cutting

### 1) Dependency graph

```
0.1 (optional)
  |
1.1 ─► 1.2 ─► 1.3 ─► 1.4
 2.1 ─► 2.2 ─► 2.4 ─► 2.5 ─► 2.6
 2.1 ─► 2.3
 2.2 ─► 3.1 ─► 3.2 ─► 3.3 ─► 4.1 ─► 4.2
                                         4.3 (parallel with 4.2)
```

### 2) Recommended commit order
1. `0.1` (if enabled) · 2. `1.1` · 3. `1.2` · 4. `1.3` · 5. `1.4` · 6. `2.1` · 7. `2.4` ·
8. `2.2` · 9. `2.3` · 10. `2.5` · 11. `2.6` · 12. `3.1` · 13. `3.2` · 14. `3.3` ·
15. `4.1` · 16. `4.2` · 17. `4.3` · 18. `4.4`

### 3) Merge order
Identical to commit order; each commit is independently green (`pytest`+`ruff`; web `npm test`).

### 4) Parallel development
- `2.4` (pure animation) parallel to `2.2` (service) after `2.1`.
- `4.2`/`4.3` in parallel after `4.1`.
- `0.1` (if enabled) parallel to `1.x`.

### 5) Must wait for teammates
- Only adoption **verification** against a real non-BFS algorithm to prove zero-edit adoption.
- `0.1` waits to merge if a teammate has uncommitted edits to `shared/enums.py`.
- No other task waits.

### 6) Completely independent
- `0.1` (if enabled) and `1.1`; `2.4` (pure reducer, only depends on `SearchStep`).

---

## Final notes

- Keep everything consistent with `GUI_ROADMAP.md`. If a mismatch with the roadmap is found
  during implementation, update **this file** only after updating the roadmap.
- Run gates after every session; fix defects before committing.
- Never edit `core/search_result.py`, `algorithms/*`, `config`, `data` from this work.