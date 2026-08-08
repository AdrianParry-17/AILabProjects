# UI_TASK_BREAKDOWN.md

**HCMC Delivery AI Search - UI Polish Engineering Backlog (executable)**

Version: 1.0

Owner: H (Hưng)

Status: **Single source of truth during UI implementation.**

Provenance: pure decomposition of `docs/UI_IMPLEMENTATION_PLAN.md` (v1.0) and the frozen UI specs
(`UI_POLISH_SPEC.md`, `DESIGN_TOKENS.md`, `LAYOUT_SPEC.md`, `MAP_RENDERING_SPEC.md`,
`COMPONENT_POLISH_SPEC.md`, `MOTION_SPEC.md`). This file adds **no** new feature, architecture,
API, component, or responsibility. Every task below maps 1:1 to a `UI_IMPLEMENTATION_PLAN.md`
section (see §5 mapping table). If a task cannot be mapped, it must not be created.

**Frozen constraints (inherited from the plan)**
- No backend work, no API changes (no endpoint, body, or response changes).
- No `SearchResult` / `SearchStep` changes; no `MAP_CONTRACT` modifications.
- No algorithm implementation changes; no new endpoints.
- No architecture changes (store shape may gain renderer state only).
- Where visual polish conflicts with the functional specs (`COMPONENT_SPEC.md`, `GUI_ROADMAP.md`,
  `MAP_CONTRACT.md`), the functional specs win.
- Behavior-preservation rule: search, playback, replay, history, selection, load graph, export
  must behave identically. The visual layer may restructure markup and CSS but never change state
  transitions, store semantics, or API calls.

**Global gates (run after every task)**
- Backend: `python -m pytest` green (must stay green — backend is untouched).
- Web: `cd ui/web && npm test` green; `cd ui/web && npm run build` passes.
- Manual checks per task: (1) existing flows functionally identical; (2) pan/zoom/fit still work;
  (3) `prefers-reduced-motion` disables motion; (4) keyboard tab order logical, focus visible.
- Every commit is independently mergeable.

---

## 0. How to read this backlog

- One task = one commit + one merge unit, sized **1–3 h**. No task is larger.
- Task IDs are `T01 … T24`, ordered by dependency, grouped by phase (P0–P6). The `Txx` IDs are the
  same as `UI_IMPLEMENTATION_PLAN.md §7` (note: `T15b` is intentionally not renumbered to keep the
  plan mapping exact; it sorts right after `T15`. `T16` is intentionally absent — see §5 footnote).
- Each task lists its **Dependencies** by Task ID. If it has none, it is startable immediately.
- **Parallelizable** marks tasks that can run on a second workstream without merge conflicts.
- After every phase there is a **Milestone checkpoint (MS-P0 … MS-P6)** listing the gates.
- The **Plan ref** column/value in every task is the authoritative mapping to
  `UI_IMPLEMENTATION_PLAN.md`; the §5 table is the machine-checkable summary.
- Estimated time is engineering time including the task's own tests, excluding the global gates.
- Field label `Functions/classes/components` is used uniformly across tasks (UI work is component-
  centric; tasks with no new symbols say `none` and explain).

---

## 1. Backlog

### PHASE P0 — Token foundations

### T01 — Design token expansion
- **Plan ref:** `UI_IMPLEMENTATION_PLAN.md §7` (T01) + `DESIGN_TOKENS.md` (full) + `MOTION_SPEC.md §4/§5`
- **Goal:** add every missing token family to `src/styles/theme.css` so no component carries a
  visual value that a token already covers.
- **Dependencies:** none.
- **Estimated time:** 2 h.
- **Files created:** none.
- **Files modified:** `ui/web/src/styles/theme.css`; `ui/web/src/main.tsx` (only if a global reset
  is required)
- **Functions/classes/components:** none new (CSS custom-property token set only). Token families
  introduced in `ui/web/src/styles/theme.css`:
  - Colors: role scales (primary/secondary/success/warning/danger/info) + `Gray-50…Gray-900` +
    semantic graph colors (normal/visited/current/frontier/start/goal/selected/path).
  - Typography: Display XL → Caption sizes, line heights, letter spacing; font loading deferred
    to a future polish task (out of scope here).
  - Spacing: 8-point scale 4, 8, 12, 16, 24, 32, 40, 48, 64, 80, 96.
  - Radius: sm 4 / md 8 / lg 12 / xl 16 / round 9999.
  - Border widths: hairline 1 / strong 2 / focus 2 / selected 2.
  - Elevation 0–4 + soft shadow tokens.
  - Opacity: disabled 40 % / muted 60 % / hover 8 % / pressed 12 % / selection 16 %.
  - Motion: `--motion-very-fast 100ms / --motion-fast 150ms / --motion-normal 220ms /
    --motion-slow 300ms` (per MOTION_SPEC §4).
  - Easing: `--ease-default ease-out / --ease-panel cubic-bezier(0.22,1,0.36,1) /
    --ease-sidebar ease-in-out / --ease-linear linear`; bounce/elastic/spring/overshoot/back
    forbidden.
  - Icon family: **locked — `lucide-react`** exposed via `shared/Icon` wrapper only; sizes
    16/20/24/32. No raw SVG paths in components.
  - Node sizes 8/12/14; button/input heights 32/40/48.
  - z-index: canvas 0 / tooltip 100 / dropdown 200 (also popup) / sidebar overlay 300 / modal 400
    / toast 500 (per plan §7 T01).
  - Focus ring 2 px / radius 8 / Primary-500.
  - Card tokens: padding 16, radius 12, gap 16, border Gray-200, background white, elevation 1.
- **Acceptance criteria:** grep check — no component CSS or TSX contains a visual value for which a
  token already exists (`theme.css` excluded) — see §1 grep gates; token names follow
  `DESIGN_TOKENS.md`; motion tier names match `MOTION_SPEC §4` verbatim; easing values explicit
  (panel = `cubic-bezier(0.22, 1, 0.36, 1)`); spacing only from the 8-point scale; single icon
  family (`lucide-react`) exposed via a `shared/Icon` wrapper (no raw SVG paths in components);
  every token overridable via a future `[data-theme="dark"]` block (no duplicated visual values);
  `npm run build` green; existing tests green; no visible UI change.
- **Behavior preservation:** existing flows (search, playback, replay, history, selection, load
  graph, export) functionally identical — no store/API/state-machine changes.
- **Unit tests:** none new (grep/static checks only).
- **Integration tests:** none.
- **Regression risks:** renaming tokens that existing components already consume — keep current
  names or alias them until T23 cleanup.
- **Commit message:** `style(ui): expand design tokens to full set`
- **Parallelizable:** No — everything depends on it.

### T02 — Panel + SectionCard + Button + TextInput primitives
- **Plan ref:** `UI_IMPLEMENTATION_PLAN.md §7` (T02) + `COMPONENT_POLISH_SPEC §5/§17/§18` + `DESIGN_TOKENS §15`
- **Goal:** create the reusable surface primitives used by every region.
- **Dependencies:** T01.
- **Estimated time:** 2 h.
- **Files created:** `ui/web/src/components/shared/Panel/index.tsx` (+ `.module.css` + test);
  `ui/web/src/components/shared/SectionCard/index.tsx` (+ `.module.css` + test);
  `ui/web/src/components/shared/Button/index.tsx` (+ `.module.css` + test);
  `ui/web/src/components/shared/TextInput/index.tsx` (+ `.module.css` + test);
  `ui/web/src/components/shared/Icon/index.tsx` (+ `.module.css` + test)
- **Files modified:** `ui/web/package.json` (icon dependency, e.g. `lucide-react`)
- **Functions/classes/components:** `Panel` (white, radius 12, hairline border, soft elevation 1,
  optional title/icon/footer slots); `SectionCard` (padding 16, radius 12, soft elevation 1,
  title + divider + content, never transparent — matches Panel elevation per plan); `Button`
  (variants `primary|secondary|ghost|danger|loading|disabled`, heights 32/40/48, radius 8,
  padding 12 horizontal, spinner on loading, disabled at opacity 40 %); `TextInput` (height 40,
  radius 8, padding 12, placeholder Gray-500, focus primary outline, accessible label +
  `aria-invalid`); `Icon` (renders only `lucide-react` — locked in T01).
- **Acceptance criteria:** all five primitives consume only tokens; `Button` renders every variant
  in tests with loading/disabled behavior and reduced-motion respect; `TextInput` shows focus ring,
  validates ARIA props, supports controlled + uncontrolled; `Icon` exposes only the chosen family,
  no raw SVG paths; semantic HTML (`<section>/<header>/<footer>/<button>/<input>`); no behavior
  changes; new tests render every variant; existing suites green; build green.
- **Unit tests:** per-primitive render/variant tests (5 files).
- **Integration tests:** none.
- **Regression risks:** primitives are new (no consumers yet) — no regression surface; keep them
  out of App wiring until T04.
- **Commit message:** `feat(ui): add Panel/SectionCard/Button/TextInput/Icon primitives`
- **Parallelizable:** No — depends on T01.

### T03 — Badge + Skeleton + EmptyState primitives
- **Plan ref:** `UI_IMPLEMENTATION_PLAN.md §7` (T03) + `MOTION_SPEC §19`
- **Goal:** create the reusable state primitives.
- **Dependencies:** T01, T02.
- **Estimated time:** 1.5 h.
- **Files created:** `ui/web/src/components/shared/Badge/index.tsx` (+ `.module.css` + test);
  `ui/web/src/components/shared/Skeleton/index.tsx` (+ `.module.css` + test)
- **Files modified:** `ui/web/src/components/shared/EmptyState/index.tsx` (+ `.module.css`; refactor
  of the existing minimal version)
- **Functions/classes/components:** `Badge` (variants info/success/warning/danger, small, radius 9999, supports
  Real/Mock/status content, never dominates layout); `Skeleton` (shimmer placeholder preserving
  dimensions, `--motion-slow` pulse, allowed for history/metrics/algorithm catalog/version);
  `EmptyState` (icon + title + description + optional action button; replaces minimal
  `shared/EmptyState`).
- **Acceptance criteria:** Badge renders all variants with token colors, content not
  `aria-hidden`; Skeleton uses `--motion-slow` pulse, fixed dimensions, `aria-hidden`, never causes
  layout shift; EmptyState has illustration slot + title + description + CTA and is ARIA-labelled;
  existing `EmptyState` consumers still render; all tests green.
- **Unit tests:** badge variants; skeleton attrs; EmptyState slot rendering.
- **Integration tests:** none.
- **Regression risks:** refactoring the existing `EmptyState` — keep its public props compatible
  (add slots additively) so existing consumers compile unchanged.
- **Commit message:** `feat(ui): add Badge/Skeleton primitives, extend EmptyState`
- **Parallelizable:** No — depends on T01/T02.

#### MS-P0 checkpoint (end of Phase P0) — see §2.

---

### PHASE P1 — Layout shell

### T04 — Five-region app shell
- **Plan ref:** `UI_IMPLEMENTATION_PLAN.md §7` (T04) + `LAYOUT_SPEC §3/§19`
- **Goal:** restructure `App.tsx` into header | (left sidebar | center viz | right panel) |
  bottom timeline dock.
- **Dependencies:** T01, T02, T03.
- **Estimated time:** 2 h.
- **Files created:** `ui/web/src/components/GraphPane/index.tsx` (+ `.module.css` + test)
- **Files modified:** `ui/web/src/App.tsx`; `ui/web/src/styles/theme.css` (shell classes; refactor
  `app-*` into tokens); `ui/web/src/components/StatusBar/index.tsx` (move out of footer role)
- **Functions/classes/components:** `GraphPane` — visualization host wrapper (consumed by T08),
  with region/role markup; shell layout: header fixed 64 px; body three-column flex/grid with main
  region `flex: 1; min-width: 0`; timeline region docked full-width beneath body.
  **StatusBar fate (locked per plan §7 T04):** the existing `components/StatusBar/index.tsx`
  is **deleted** in this task; its responsibilities are absorbed into a new "Status" section
  rendered by `InfoPanel` (T06). All future StatusBar polish (T20) targets the InfoPanel Status
  section, not a standalone component.
- **Acceptance criteria:** five visible regions on desktop; header + timeline fixed; visualization
  ≥ 60 % width; responsive: ≥ 1440 px three-column, 1024–1439 px narrower right panel,
  768–1023 px sidebar collapses to drawer + timeline stays docked; **< 768 px renders a
  centered "Best viewed at ≥ 768 px" notice** overlaying the existing layout (layout does
  not collapse below 768 px — out of scope per plan §2.4); search/playback/history still work;
  `GraphPane` test asserts region/role markup; all suites green; build green.
- **Behavior preservation:** existing flows (search, playback, replay, history, selection, load
  graph, export) functionally identical — no store/API/state-machine changes; only the StatusBar
  deletion is allowed and its responsibilities move to `InfoPanel` in T06.
- **Unit tests:** `GraphPane` renders wrapper + roles; App shell renders five regions.
- **Integration tests:** manual — search, playback, history on ≥ 1280×800.
- **Regression risks:** moving StatusBar out of the footer role — preserve its store wiring; shell
  flexbox overflow (use `min-width: 0` on main).
- **Commit message:** `feat(ui): five-region app shell with GraphPane host`
- **Parallelizable:** No — foundation for P1.

### T05 — Left Sidebar restructure
- **Plan ref:** `UI_IMPLEMENTATION_PLAN.md §7` (T05) + `COMPONENT_POLISH_SPEC §4` + `MOTION_SPEC §15`
- **Goal:** group the sidebar into ordered SectionCards; remove metrics/history from it.
- **Dependencies:** T04.
- **Estimated time:** 1.5 h.
- **Files created:** none.
- **Files modified:** `ui/web/src/components/Sidebar/index.tsx` (+ `.module.css`);
  `ui/web/src/components/ControlPanel/index.tsx` (+ `.module.css`) — regroup content
- **Functions/classes/components:** sidebar sections in order: Search (start, goal), Algorithm
  (selector), Execution (Run), Optional Advanced; 24 px between sections; each section = title +
  divider + content; width 320–420 px (preferred 360); independent vertical scroll.
- **Acceptance criteria:** sidebar shows only search configuration (no metrics/history inside);
  sections separated with titles/dividers; spacing uses 8-point tokens; **drawer animation
  (tablet 768–1023 px only — desktop sidebar is fixed per T04)** open/close 220 ms slide + fade
  with `--ease-panel`; **Advanced section** height-expansion animation capped at 220 ms on all
  widths; no store/API changes; existing ControlPanel tests pass (updated only for markup).
- **Behavior preservation:** existing flows functionally identical — no store/API/state-machine
  changes.
- **Unit tests:** ControlPanel tests updated for regrouped markup.
- **Integration tests:** none.
- **Regression risks:** removing metrics/history from the sidebar breaks nothing if T06 lands next
  (metrics/history consumers move with the panel).
- **Commit message:** `style(ui): regroup sidebar into SectionCards`
- **Parallelizable:** No.

### T06 — Right Information Panel
- **Plan ref:** `UI_IMPLEMENTATION_PLAN.md §7` (T06) + `LAYOUT_SPEC §13` + `UI_POLISH_SPEC §12`
- **Goal:** create the right panel region; history moves here.
- **Dependencies:** T04, T05.
- **Estimated time:** 2 h.
- **Files created:** `ui/web/src/components/InfoPanel/index.tsx` (+ `.module.css` + test)
- **Files modified:** `ui/web/src/components/Sidebar/index.tsx` (remove history);
  `ui/web/src/components/HistoryPanel/index.tsx` (consumer unchanged)
- **Functions/classes/components:** `InfoPanel` — Status section (top, always visible — this
  section absorbs the responsibilities of the deleted `StatusBar` component per T04),
  Metrics section (compact cards), search explanation / current node / current frontier,
  History panel (supporting role); preferred width 360 px (320–420); independent scroll; contains
  no search controls.
- **Acceptance criteria:** right panel shows status, metrics, explanation, history after search;
  no search controls in the panel; history still replays runs; existing history tests green.
- **Behavior preservation:** existing flows functionally identical — no store/API/state-machine
  changes.
- **Unit tests:** `InfoPanel` renders sections per search state.
- **Integration tests:** manual — replay from the moved history list.
- **Regression risks:** HistoryPanel loses its sidebar context — keep its props/contract identical
  (moves as a consumer, not a rewrite).
- **Commit message:** `feat(ui): right info panel with status/metrics/history`
- **Parallelizable:** No.

### T07 — Playback timeline dock
- **Plan ref:** `UI_IMPLEMENTATION_PLAN.md §7` (T07) + `UI_POLISH_SPEC §11`
- **Goal:** ensure the timeline is docked full-width at the bottom, never covering the canvas.
- **Dependencies:** T04.
- **Estimated time:** 1.5 h.
- **Files created:** none.
- **Files modified:** `ui/web/src/components/StepTimeline/index.tsx` (+ `.module.css`);
  `ui/web/src/components/shared/AnimationControls/index.tsx` (+ `.module.css`);
  `ui/web/src/App.tsx` (dock placement)
- **Functions/classes/components:** timeline height 96–120 px when active; contains play/pause/
  restart/prev/next, speed, progress slider, current step, step count, playback status; hides
  gracefully when no result exists.
- **Acceptance criteria:** timeline occupies its own docked region; canvas untouched by timeline
  overlays; all required controls present and functional (existing playback logic unchanged);
  reduced-motion respected; tests green; build green.
- **Behavior preservation:** existing flows functionally identical — no store/API/state-machine
  changes.
- **Unit tests:** none new (existing timeline tests stay green).
- **Integration tests:** manual playback at ≥ 1280×800.
- **Regression risks:** flexbox overlap with canvas — the dock must be outside the visualization
  column, not absolutely positioned over it.
- **Commit message:** `style(ui): dock playback timeline at bottom`
- **Parallelizable:** No.

#### MS-P1 checkpoint (end of Phase P1) — see §2.

---

### PHASE P2 — Renderer framework

### T08 — Renderer toggle (Graph | Map)
- **Plan ref:** `UI_IMPLEMENTATION_PLAN.md §7` (T08) + `LAYOUT_SPEC §9–10` + `MAP_RENDERING_SPEC §2` + `MOTION_SPEC §8/§14`
- **Goal:** add a segmented Graph | Map control above the visualization with store-backed renderer
  state.
- **Dependencies:** T04.
- **Estimated time:** 1.5 h.
- **Files created:** `ui/web/src/components/RendererToggle/index.tsx` (+ `.module.css` + test)
- **Files modified:** `ui/web/src/state/store.ts` (renderer state + setter — new state only, no
  API change); `ui/web/src/components/GraphPane/index.tsx` (renders toggle + active renderer)
- **Functions/actions:** `renderer: "graph" | "map"` in store; setter `setRenderer()`.
- **Acceptance criteria:** toggle switches renderers instantly with animated transition (MOTION
  §8/§14); search state, playback position, and selected node survive a switch; Fit View
  transition is 220 ms with `--ease-panel`; new store test asserts renderer transitions; **no
  backend API call** (`/graph`, `/search`, `/history`, `/algorithms`, `/version`, `/health`) is
  triggered by `setRenderer()` — first-time switch to Map does fetch OpenStreetMap tiles from
  the third-party tile server, which is expected and is not a backend API call (covered
  separately by T11); default renderer on first load is Map; segmented control order Graph | Map.
- **Behavior preservation:** existing flows functionally identical — store shape may gain
  `renderer` state only; no other slice is modified.
- **Unit tests:** store renderer transition test; `RendererToggle` render + callback.
- **Integration tests:** none.
- **Regression risks:** renderer switch must never rerun search or reset playback — isolate the
  state change to the renderer slice only.
- **Commit message:** `feat(ui): renderer toggle (graph|map)`
- **Parallelizable:** No.

### T09 — Graph renderer polish (states + layers)
- **Plan ref:** `UI_IMPLEMENTATION_PLAN.md §7` (T09) + `MAP_RENDERING_SPEC` + `DESIGN_TOKENS §5` + `LAYOUT_SPEC §23`
- **Goal:** polish GraphCanvas node/edge states and layer structure per spec.
- **Dependencies:** T08.
- **Estimated time:** 2.5 h.
- **Files created:** none.
- **Files modified:** `ui/web/src/components/GraphCanvas/index.tsx` (+ `.module.css`);
  `ui/web/src/components/GraphCanvas/RouteOverlay.tsx` (align states to tokens);
  `ui/web/src/components/GraphCanvas/Legend.tsx` (keep in sync with new colors)
- **Functions/classes/components:** 8 visually distinct node states — normal, start, goal, visited,
  current, path, frontier, selected (color/size/border/opacity; sizes 8/12/14); edge categories
  normal / visited / current traversal / final path (final path strongest: wider, accent color,
  subtle glow); layer order edges → visited → path → nodes → selected → tooltip; static layers
  (edges, base nodes) memoized separately from animated layers; canvas background Gray-50.
- **Acceptance criteria:** each node state token-driven and distinct; legend matches rendering;
  final-path edges strongest; layer order correct; **memo test assertion:** static-layer
  components (Edges, base Nodes) render **0 times** across N=50 playback steps in the test
  (verified via render-prop spy or `react-test-renderer`'s `toJSON()` count); only the animated
  current-node and route overlay may re-render; all existing GraphCanvas tests pass (updated only
  for colors/markup).
- **Behavior preservation:** existing flows functionally identical — hit-test geometry (interactive
  area) independent of visual node size; selection ring stays a sibling of node, not nested.
- **Unit tests:** memo/rerender assertion for static layers; state-to-class mapping.
- **Integration tests:** manual playback visually verifies states.
- **Regression risks:** changing node sizing classes can break existing hit-testing — keep
  interactive geometry (hit area) independent of visual size.
- **Commit message:** `style(ui): graph renderer states + layer polish`
- **Parallelizable:** No.

### T10 — Shared camera + fit rules (graph + map)
- **Plan ref:** `UI_IMPLEMENTATION_PLAN.md §7` (T10) + `MAP_RENDERING_SPEC §4`
- **Goal:** apply identical camera/fit rules to both renderers.
- **Dependencies:** T09.
- **Estimated time:** 1.5 h.
- **Files created:** none (extends `ui/web/src/lib/coords.ts`).
- **Files modified:** `ui/web/src/lib/coords.ts` (bounds/fit helpers — pure, reusable by either
  renderer); `ui/web/src/components/GraphCanvas/index.tsx`. **`MapView/index.tsx` does not
  exist until T11** — the fit helper is wired into MapView in T11, not here.
- **Functions/classes/components:** shared bounds + fit helpers in `lib/coords` (fit padding
  40 px; zoom clamped to [10, 18] equivalents).
- **Acceptance criteria:** initial view and Fit use 40 px padding in both renderers; zoom stays
  within [10, 18]; camera preserved across renderer switches where the graph fits; existing
  pan/zoom tests green; map camera unit-testable via the pure helper.
- **Behavior preservation:** existing flows functionally identical — `lib/coords` refactor must
  preserve public exports (alias if needed).
- **Unit tests:** pure helper fit/bounds math.
- **Integration tests:** none.
- **Regression risks:** divergence between renderers — both must call the same `lib/coords`
  helpers (no per-renderer constants).
- **Commit message:** `refactor(ui): shared camera + fit rules`
- **Parallelizable:** No.

#### MS-P2 checkpoint (end of Phase P2) — see §2.

---

### PHASE P3 — Map renderer

### T11 — Leaflet map canvas
- **Plan ref:** `UI_IMPLEMENTATION_PLAN.md §7` (T11) + `MAP_RENDERING_SPEC §3–6`
- **Goal:** create the street-map renderer (Leaflet + OpenStreetMap).
- **Dependencies:** T08, T10.
- **Estimated time:** 2 h.
- **Files created:** `ui/web/src/components/MapView/index.tsx` (+ `.module.css` + test);
  `ui/web/src/components/MapView/useLeaflet.ts` (init/lifecycle hook)
- **Files modified:** `ui/web/package.json` (add `leaflet` dependency)
- **Functions/classes/components/hooks:** `MapView` — pure presentational shell, no graph/search
  logic; `useLeaflet` — map init/lifecycle. Interactions: wheel zoom, drag, double-click zoom,
  touch pinch, keyboard, Fit. Initial camera fits graph bounds (40 px padding), min zoom 10,
  max zoom 18. Loading state: skeleton map + fade, never a blank white panel. Top-right floating
  controls: +, −, Fit, Locate Graph.
- **Acceptance criteria:** tiles render; map interactions work; fit button works; no graph/search
  logic inside MapView; **`leaflet/dist/leaflet.css` imported exactly once** (at `main.tsx`
  or at the top of `MapView/index.tsx`) so tile layers style correctly in production;
  jsdom-safe tests (map init guarded); all suites green; build green.
- **Behavior preservation:** existing flows functionally identical — MapView is additive; no
  existing component is modified except where the GraphPane wires it in (T08 already
  supports both renderers).
- **Unit tests:** MapView renders shell + loading state; `useLeaflet` init guarded in jsdom.
- **Integration tests:** manual — tile load, pan/zoom, fit against the real service.
- **Regression risks:** Leaflet CSS/JS not bundled — import leaflet styles; window/document access
  in SSR/jsdom tests — guard map init.
- **Commit message:** `feat(ui): leaflet map canvas`
- **Parallelizable:** No.

### T12 — Map overlays + markers
- **Plan ref:** `UI_IMPLEMENTATION_PLAN.md §7` (T12) + `MAP_RENDERING_SPEC §8–15` + `MOTION_SPEC §18`
- **Goal:** draw the graph over the tiles, synced with the shared Frame.
- **Dependencies:** T11.
- **Estimated time:** 2.5 h.
- **Files created:** `ui/web/src/components/MapView/Overlays.tsx` (+ `.module.css`);
  `ui/web/src/components/MapView/RouteLine.tsx`;
  `ui/web/src/components/MapView/useFrameSync.ts`
- **Files modified:** none.
- **Functions/classes/components/hooks:** `Overlays` (road graph 2 px gray-400 @ 55 %; visited
  circles r 5 primary blue @ 35 % accumulating; current node r 8 white border blue fill with soft
  one-shot pulse; start = large green pin persistent, goal = large red pin persistent; labels
  hidden by default, shown on hover/selection/search); `RouteLine` (bright blue 5 px, rounded
  caps/joins, small glow, drawn progressively, never flashes); `useFrameSync` — thin wrapper
  calling the existing `frameAt(steps, activeIndex)` from `ui/web/src/services/animation.ts`
  (no duplication of Frame derivation). Overlay order: tiles → road graph → animated route →
  visited → current → markers. Node interactions: hover = white halo + tooltip fade (T13);
  selected = blue outline; keyboard focus = dashed outline + visible ring (T21); current-node
  pulse fires once on entry, never infinite.
- **Acceptance criteria:** overlay order matches MAP_RENDERING §7; start/goal markers persistent;
  visited nodes accumulate per SearchStep; **route draws progressively at the current playback
  rate (respects the speed selector from T17; never faster than the timeline beat)**, synced
  with the timeline; map consumes the exact same Frame as the graph renderer — no duplicated
  state.
- **Behavior preservation:** existing flows functionally identical — Frame derivation reuses the
  existing `services/animation.ts` reducer; no new state.
- **Unit tests:** `useFrameSync` maps `activeIndex` to the same frame as the graph path.
- **Integration tests:** manual — playback on the map mirrors the graph.
- **Regression risks:** duplicating Frame derivation — `useFrameSync` must call
  `services/animation.ts` only; marker/Layer lifecycle leaks on unmount — clean up in `useEffect`.
- **Commit message:** `feat(ui): map overlays + markers`
- **Parallelizable:** No.

### T13 — Tooltip + Popup (shared)
- **Plan ref:** `UI_IMPLEMENTATION_PLAN.md §7` (T13) + `MAP_RENDERING_SPEC §17` + `MOTION_SPEC §17`
- **Goal:** shared tooltip (hover) and popup (click) wired into both renderers.
- **Dependencies:** T09, T12.
- **Estimated time:** 2 h.
- **Files created:** `ui/web/src/components/shared/Popup/index.tsx` (+ `.module.css` + test)
- **Files modified:** `ui/web/src/components/shared/Tooltip/index.tsx` (+ `.module.css`; polish
  existing); `ui/web/src/components/GraphCanvas/index.tsx` (wire tooltip);
  `ui/web/src/components/MapView/index.tsx` (wire tooltip + popup)
- **Functions/classes/components:** `Tooltip` (hover: node name, id, type, coordinates, optional
  distance; small rounded card, max width 300 px; 100 ms fade + 2 px translateY); `Popup` (click:
  location name, node type, lat/lon, actions Set as Start, Set as Goal, Center Here, Close;
  actions call existing store actions; keyboard accessible).
- **Acceptance criteria:** hover shows tooltip; click shows popup; both keyboard-reachable;
  **popup is rendered only by MapView** (per MAP_RENDERING §17) — GraphCanvas receives only the
  shared `Tooltip` on hover/selection, there is no popup in graph mode; "Set as Start/Goal"
  and "Center Here" work in both renderers via shared store actions; all tooltips/popups respect
  `prefers-reduced-motion`; tests green.
- **Behavior preservation:** existing flows functionally identical — popup actions reuse existing
  store actions (`setStart`, `setGoal`, fit/camera helpers); no new API.
- **Unit tests:** Popup renders actions + fires store callbacks.
- **Integration tests:** manual — set start/goal from popup in both renderers.
- **Regression risks:** popup actions must reuse existing store actions (`setStart`, `setGoal`,
  fit/camera) — never new API.
- **Commit message:** `feat(ui): shared tooltip + popup`
- **Parallelizable:** No.

#### MS-P3 checkpoint (end of Phase P3) — see §2.

---

### PHASE P4 — Component polish

### T14 — Header
- **Plan ref:** `UI_IMPLEMENTATION_PLAN.md §7` (T14) + `COMPONENT_POLISH_SPEC §3` + `LAYOUT_SPEC §5`
- **Goal:** polish the header into its fixed 64 px role.
- **Dependencies:** T02, T04.
- **Estimated time:** 1 h.
- **Files created:** `ui/web/src/components/Header/index.tsx` (+ `.module.css` + test)
- **Files modified:** `ui/web/src/App.tsx` (use Header)
- **Functions/classes/components:** `Header` — height 64 px, fixed, white, bottom border only,
  no large shadows; app logo + title left; right side: backend status, API version, **read-only**
  renderer indicator pill; no search controls. **Renderer-control ownership (locked per plan):
  the Header's renderer pill is a read-only indicator — it is NOT a control. The only
  interactive renderer control is the segmented `RendererToggle` in `GraphPane` (T08).**
- **Acceptance criteria:** header shows title, backend status, version, active renderer (as a
  read-only indicator pill — NOT a control); no search controls; existing health/version data
  reused (no API change); the pill's interactive behavior (no-op vs scroll-to-toggle) is decided
  during implementation and documented in the component header comment.
- **Behavior preservation:** existing flows functionally identical — only display logic; no
  store/API changes.
- **Unit tests:** Header renders title + status + version + renderer pill.
- **Integration tests:** none.
- **Regression risks:** none — presentational; reuse existing health/version store selectors.
- **Commit message:** `feat(ui): dedicated header`
- **Parallelizable:** Yes — after T02/T04, independent of T05–T07.

### T15 — Metrics panel polish
- **Plan ref:** `UI_IMPLEMENTATION_PLAN.md §7` (T15) + `UI_POLISH_SPEC §13` + `COMPONENT_POLISH_SPEC §11` + `LAYOUT_SPEC §21`
- **Goal:** metrics as uniform compact cards, not a table.
- **Dependencies:** T02, T06.
- **Estimated time:** 1.5 h.
- **Files created:** none.
- **Files modified:** `ui/web/src/components/MetricsPanel/index.tsx` (+ `.module.css` + test)
- **Functions/classes/components:** `MetricsPanel` — each card icon + title + value + unit;
  2-column grid on desktop; consistent card dimensions (uses T01 card tokens: padding 16,
  radius 12, gap 16, border Gray-200, bg white, elevation 1); no tables; tabular numerals;
  large numbers; empty state "Run a search to see metrics." + guidance (no action — selection-
  driven per plan §7 T22).
- **Acceptance criteria:** metrics render as uniform cards, not a table; values use tabular-nums;
  empty state explains how to run a search; existing metric formatting logic (`lib/format`)
  reused; tests green.
- **Behavior preservation:** existing flows functionally identical — only display logic; no
  store/API changes.
- **Unit tests:** card layout render; tabular-nums class; empty state.
- **Integration tests:** none.
- **Regression risks:** none — presentational; reuse `lib/format` untouched.
- **Commit message:** `style(ui): metrics panel cards`
- **Parallelizable:** Yes — after T02/T06.

### T15b — History panel polish
- **Plan ref:** `UI_IMPLEMENTATION_PLAN.md §7` (T15b) + `COMPONENT_POLISH_SPEC §14/§26`
- **Goal:** polish HistoryPanel now living inside the InfoPanel.
- **Dependencies:** T02, T06.
- **Estimated time:** 1.5 h.
- **Files created:** none.
- **Files modified:** `ui/web/src/components/HistoryPanel/index.tsx` (+ `.module.css` + test)
- **Functions/classes/components:** compact cards (T01 card tokens: padding 16, radius 12, gap 16,
  border Gray-200, bg white, elevation 1); each row shows algorithm, start, goal, time, Replay
  button; newest first; hover elevation `--shadow-2` + `--motion-fast`; each row `React.memo`-
  wrapped to avoid rerenders during playback; empty state "No searches recorded yet." (no CTA —
  organic); loading state skeleton rows preserving height.
- **Acceptance criteria:** rows render newest-first; hover elevation visible; each row
  `React.memo`-wrapped — assertion: row render count is **0** across N=50 playback-step changes
  in the test (verified via render-prop spy or `react-test-renderer`'s `toJSON()` count);
  empty + loading states render; existing replay functionality preserved; tests green; build
  green.
- **Behavior preservation:** existing flows functionally identical — memo wrapper keeps
  `onReplay` callback identity stable via `useCallback` in the parent.
- **Unit tests:** memo rerender assertion; newest-first order; empty/loading states.
- **Integration tests:** manual — replay still works from the polished list.
- **Regression risks:** memo wrapper breaking callback identity — keep `onReplay` stable via
  `useCallback` in the parent.
- **Commit message:** `style(ui): history panel polish + memo rows`
- **Parallelizable:** Yes — after T02/T06.

### T17 — Timeline + animation controls polish
- **Plan ref:** `UI_IMPLEMENTATION_PLAN.md §7` (T17) + `COMPONENT_POLISH_SPEC §13` + `MOTION_SPEC §12`
- **Goal:** polish slider + controls per spec.
- **Dependencies:** T02, T07.
- **Estimated time:** 2 h.
- **Files created:** none.
- **Files modified:** `ui/web/src/components/StepTimeline/index.tsx` (+ `.module.css`);
  `ui/web/src/components/shared/AnimationControls/index.tsx` (+ `.module.css`);
  `ui/web/src/components/StepTimeline/usePlayback.ts` (if timing refactor needed)
- **Functions/classes/components:** slider large and easy to drag; current step always visible;
  optional ticks; controls square/equal-size/grouped; hover soft elevation; pressed scale 0.98;
  disabled reduced opacity; speed selector present; Play linear, Pause immediate, Restart fades
  current path and starts from step 0, Jump immediate.
- **Acceptance criteria:** all controls visually consistent (square, equal size, grouped); pressed
  scale 0.98; slider drag maps 1:1 to step index; current step + total always visible; playback
  timing uses `requestAnimationFrame`, no layout-thrash per step; existing playback tests green.
- **Behavior preservation:** existing flows functionally identical — touching `usePlayback.ts`
  is allowed only if timing refactor is needed, and must preserve existing behavior.
- **Unit tests:** slider-to-index mapping; pressed-state class.
- **Integration tests:** manual playback flow.
- **Regression risks:** touching `usePlayback.ts` timing — behavior must stay identical; only
  refactor if layout-thrash is confirmed.
- **Commit message:** `style(ui): timeline + playback controls polish`
- **Parallelizable:** Yes — after T02/T07.

### T18 — Algorithm selector polish
- **Plan ref:** `UI_IMPLEMENTATION_PLAN.md §7` (T18) + `COMPONENT_POLISH_SPEC §6`
- **Goal:** dropdown with leading icon, name + description, Real/Mock badge, searchable.
- **Dependencies:** T03, T05.
- **Estimated time:** 1.5 h.
- **Files created:** none.
- **Files modified:** `ui/web/src/components/AlgorithmSelector/index.tsx` (+ `.module.css` + test);
  `ui/web/src/components/shared/Badge/index.tsx` (reuse)
- **Functions/classes/components:** dropdown with leading icon (from T01 `lucide-react`); algorithm
  name + description; Real/Mock badge (T03 `Badge`); searchable; keyboard accessible; never
  hardcodes algorithm names (catalog comes from the store); selected value remains visible.
- **Acceptance criteria:** selector shows name, description, badge; search filters options; catalog
  still loaded once from the store; no API changes; existing AlgorithmSelector tests pass (updated
  for markup).
- **Behavior preservation:** existing flows functionally identical — catalog remains the single
  source of algorithm metadata.
- **Unit tests:** badge per catalog `mock` flag; search filter; selection display.
- **Integration tests:** none.
- **Regression risks:** hardcoding names — the catalog must remain the single source of algorithm
  metadata.
- **Commit message:** `style(ui): algorithm selector polish`
- **Parallelizable:** Yes — after T03/T05.

### T19 — Node picker polish
- **Plan ref:** `UI_IMPLEMENTATION_PLAN.md §7` (T19) + `COMPONENT_POLISH_SPEC §7`
- **Goal:** autocomplete + fuzzy matching + recent selections.
- **Dependencies:** T03, T05.
- **Estimated time:** 1.5 h.
- **Files created:** none.
- **Files modified:** `ui/web/src/components/shared/NodePicker/index.tsx` (+ `.module.css` + test)
- **Functions/classes/components:** dropdown selection + autocomplete search; fuzzy matching;
  instant filtering; max 8 visible results, scrollable; recent selections (session-only — no
  persistence API); clear button; placeholder "Choose a location..."; works alongside direct
  map/graph click selection (both freely mixable).
- **Acceptance criteria:** autocomplete filters by node id, name, street/POI; fuzzy matches
  accepted; at most 8 results visible; recent selections persist in session only; clear button
  resets picker; store selection behavior unchanged.
- **Behavior preservation:** existing flows functionally identical — store selection behavior
  unchanged; only the picker UX is enriched.
- **Unit tests:** filter by id/name/street; result cap at 8; clear resets.
- **Integration tests:** none.
- **Regression risks:** recent selections must be session-scoped only (no persistence API).
- **Commit message:** `style(ui): node picker autocomplete + fuzzy`
- **Parallelizable:** Yes — after T03/T05.

#### MS-P4 checkpoint (end of Phase P4) — see §2.

---

### PHASE P5 — Motion & accessibility

### T20 — Motion tokens everywhere + reduced motion
- **Plan ref:** `UI_IMPLEMENTATION_PLAN.md §7` (T20) + `MOTION_SPEC §4/§18/§20/§24` + `COMPONENT_POLISH_SPEC §10` + `DESIGN_TOKENS §25`
- **Goal:** every transition consumes motion tokens; reduced-motion honored globally; status
  state styling per spec.
- **Dependencies:** all P0–P4 component tasks that own module CSS — concretely:
  T01 (motion tokens), T03 (Skeleton), T06 (InfoPanel — owns the status section that absorbed
  the deleted StatusBar), T11 (MapView), T14 (Header), T15 (Metrics), T15b (History), T17
  (Timeline/Controls), T18 (AlgorithmSelector), T19 (NodePicker).
- **Estimated time:** 2.5 h.
- **Files created:** none.
- **Files modified:** all component `.module.css` files with transitions;
  `ui/web/src/components/InfoPanel/index.tsx` (+ `.module.css`) — status section state styling
  (the **deleted** `StatusBar` is no longer a target; per T04 the status section lives in
  InfoPanel); `ui/web/src/styles/theme.css` — global `prefers-reduced-motion` media query
  (motion tokens were added in T01).
- **Functions/classes/components:** allowed animations (exhaustive — anything outside is
  forbidden): opacity fades (toasts, popup open/close, status state change); translate
  (tooltip 2 px, drawer slide-in, panel expansion); scale 0.98→1 (button pressed feedback);
  spinner rotation (loading indicators); Skeleton shimmer (T03, `--motion-slow`); one-shot
  pulse (T12 current-node entry, non-infinite); SVG stroke-dashoffset path-draw (T12 RouteLine,
  respects playback speed); Fit-camera transition (T08, 220 ms, `--ease-panel`).
  Forbidden: bounce, elastic, spring, overshoot, back, and any non-listed motion.
  `prefers-reduced-motion` disables playback interpolation, panel/hover/map animations; keeps
  opacity + instant state changes. Status section: compact card layout, left icon, status text,
  optional description; colors per DESIGN_TOKENS §25 (Idle gray, Loading primary, Running info,
  Completed success, Warning warning, Failed danger); never flashes; Loading/Searching spinner;
  Success/Error fade; Finished one-shot accent pulse.
- **Acceptance criteria:** grep shows no literal `transition: … ms` outside tokens/theme (see
  §1 grep gates); reduced-motion media query disables the listed motion and UI remains usable;
  status colors per DESIGN_TOKENS §25.
- **Unit tests:** status-color mapping (class per state).
- **Integration tests:** manual — OS reduced-motion toggle changes behavior.
- **Regression risks:** sweep size — the plan explicitly allows this task to land as multiple PRs
  (one per component group); the shared media-query helper + token wiring land first.
- **Commit message:** `style(ui): token-driven motion + reduced motion + status states`
- **Parallelizable:** No (broad sweep — land as one review unit per component group).
- **Behavior preservation:** existing flows functionally identical — only transitions/easing
  change visually; state transitions, store, and API are untouched.

### T21 — Focus, keyboard nav, ARIA
- **Plan ref:** `UI_IMPLEMENTATION_PLAN.md §7` (T21) + `LAYOUT_SPEC §24`
- **Goal:** visible focus everywhere, logical tab order, ARIA coverage.
- **Dependencies:** T02 (Button/TextInput focus rings), T04 (shell tab order),
  T06 (InfoPanel focus), T11 (MapView keyboard handlers), T20 (motion-token focus transitions).
- **Estimated time:** 2 h.
- **Files created:** none.
- **Files modified:** global focus styles in `ui/web/src/styles/theme.css`; interactive components
  (buttons, selectors, timeline, canvas, map); `ui/web/src/components/MapView/index.tsx`
  (keyboard handlers)
- **Functions/classes/components:** visible focus ring on every interactive element (2 px,
  radius 8, Primary-500); tab order header → sidebar → visualization → right panel → timeline;
  ARIA labels on icon-only controls; tooltips/popups screen-reader friendly; canvas/map
  keyboard pan + selection accessible.
- **Acceptance criteria:** keyboard-only walkthrough completes (select algorithm, pick nodes, run,
  play, step, replay); focus never disappears (no `outline: none` without replacement);
  axe-style checks (or equivalent) report no critical violations.
- **Behavior preservation:** existing flows functionally identical — only focus/ARIA surface
  changes; no store/API/state-machine changes.
- **Unit tests:** axe scan on key components.
- **Integration tests:** manual keyboard-only walkthrough.
- **Regression risks:** focus rings on canvas SVG elements need `tabindex` + `focusable` handling.
- **Commit message:** `fix(ui): focus, keyboard nav, ARIA`
- **Parallelizable:** No.

#### MS-P5 checkpoint (end of Phase P5) — see §2.

---

### PHASE P6 — States & finalization

### T22 — Loading / empty / error states across regions
- **Plan ref:** `UI_IMPLEMENTATION_PLAN.md §7` (T22) + `LAYOUT_SPEC §21` + `MAP_RENDERING_SPEC §20–21` + `COMPONENT_POLISH_SPEC §23`
- **Goal:** every region gets skeleton loading, explanatory empty states, and defined error
  surfaces.
- **Dependencies:** T03 (Skeleton/EmptyState primitives), T04 (GraphPane region), T06 (InfoPanel
  region), T11 (MapView region), T14 (Header region), T15 (MetricsPanel region),
  T15b (HistoryPanel region), T18 (AlgorithmSelector region).
- **Estimated time:** 2.5 h.
- **Files created:** none.
- **Files modified:** `ui/web/src/components/InfoPanel/index.tsx` (+ `.module.css`);
  `ui/web/src/components/HistoryPanel/index.tsx` (+ `.module.css`);
  `ui/web/src/components/MetricsPanel/index.tsx` (+ `.module.css`);
  `ui/web/src/components/GraphPane/index.tsx` (+ `.module.css`);
  `ui/web/src/components/MapView/index.tsx` (+ `.module.css`);
  `ui/web/src/components/Header/index.tsx` (+ `.module.css`);
  `ui/web/src/components/AlgorithmSelector/index.tsx` (+ `.module.css`)
- **Functions/classes/components:**
  - **Empty states** explain why + offer a **primary action button** (NOT a retry — retry is
    reserved for error states) when one exists:
    - Visualization: "Load graph to begin." → primary action "Load graph" (calls `loadGraph`).
    - Metrics: "Run a search to see metrics." (no action — selection-driven).
    - History: "No searches recorded yet." (no action — organic).
    - AlgorithmSelector: "Loading catalog…" → "Catalog unavailable." on catalog failure.
  - **Error states** — the retry-surface list is exhaustive:
    - Graph load failure: error icon, message, Retry button (calls `loadGraph`).
    - Search failure: error icon + message inside InfoPanel status section; no auto-retry.
    - Catalog fetch failure: inline error indicator in AlgorithmSelector; no retry surface.
    - Version fetch failure: inline error indicator in header; no retry surface.
    - **History fetch failure:** inline error indicator in HistoryPanel; no retry surface.
    - Map tile fetch failure: centered error card on Map region; "Retry tiles" re-issues tile
      requests only (does not call the backend API).
  - Skeleton loading for history, metrics, algorithm catalog, version, header right-side —
    never blank panels.
  - Map empty/error: centered illustration/error card, layout dims but does not collapse.
  - Error states never expose stack traces.
- **Acceptance criteria:** no region shows an empty white panel while loading; every empty state
  has title + description + (when applicable) primary action button (not "retry" — retry is
  reserved for error states); every error state has icon + message + (when in the retry-surface
  list) Retry button; the retry-surface list is exhaustive; regions outside it render a
  non-actionable error indicator; map renders centered empty/error card; history fetch failure
  renders an inline indicator in HistoryPanel; **catalog, version, history, and search
  failures explicitly do NOT expose retry**; no stack traces leak to UI; tests green; build
  green.
- **Unit tests:** per-region empty/error render (visualization, metrics, history, catalog, map);
  retry-surface enforcement (only graph load + map tile failures have Retry).
- **Integration tests:** manual — kill the backend and walk each region.
- **Regression risks:** retry surface creep — only the listed retry surfaces may retry;
  StatusBar Retry rules from existing behavior preserved.
- **Commit message:** `feat(ui): loading/empty/error states across regions`
- **Parallelizable:** No.
- **Behavior preservation:** existing flows functionally identical — only display logic; no
  store/API/state-machine changes.

### T23 — Token cleanup + docs sync
- **Plan ref:** `UI_IMPLEMENTATION_PLAN.md §7` (T23)
- **Goal:** remove superseded tokens/components; sync CSS modules to final token names.
- **Dependencies:** T01, T22.
- **Estimated time:** 1 h.
- **Files created:** none.
- **Files modified:** `ui/web/src/styles/theme.css`; any CSS module with stale token names;
  `ui/web/README.md` (if present)
- **Acceptance criteria:** no unused token definitions (grep each token's usage); all component
  CSS references tokens that exist; build green.
- **Unit tests:** none.
- **Integration tests:** none.
- **Regression risks:** deleting tokens still referenced — grep before removal; keep deprecated
  aliases only if a consumer still needs them.
- **Commit message:** `refactor(ui): token cleanup + docs sync`
- **Parallelizable:** No.
- **Behavior preservation:** existing flows functionally identical — only renaming/removal of
  unused tokens; no store/API/state-machine changes.

### T24 — Cross-renderer verification
- **Plan ref:** `UI_IMPLEMENTATION_PLAN.md §7` (T24)
- **Goal:** final integration check — graph and map agree end-to-end.
- **Dependencies:** T08–T13, T14–T19 (all renderer + component tasks).
- **Estimated time:** 1.5 h.
- **Files created:** none.
- **Files modified:** `ui/web/src/components/GraphPane/index.test.tsx` (integration-style test)
- **Acceptance criteria:** run a search in Graph mode, switch to Map — identical Frame, metrics,
  history, explanation; replay a recorded run in both renderers; confirm no search rerun on
  toggle; camera preserved where possible; Graph and Map produce identical step-by-step results
  from the same SearchResult; replay works in both renderers; toggle never triggers a **backend**
  API call (tile fetches on first Map activation are allowed and verified separately by T11);
  full quality gates green.
- **Unit tests:** `GraphPane` integration-style test — toggle preserves state, frames agree.
- **Integration tests:** manual full walkthrough per the run sheet (see MS-P6).
- **Regression risks:** divergence detected only here — the integration test in GraphPane makes it
  repeatable.
- **Commit message:** `test(ui): cross-renderer integration verification`
- **Parallelizable:** No.
- **Behavior preservation:** existing flows functionally identical — verification-only task;
  if a divergence is detected here, the fix belongs to the offending earlier task, not T24.

#### MS-P6 checkpoint (end of Phase P6) — see §2.

---

## 2. Milestone checkpoints

> Gates are run from the repo root. "Manual" = a human-driven visual/UX check on ≥ 1280×800
> (plus the per-phase device-width walk below).

### MS-P0 — after T03 (Phase P0)
- [ ] `python -m pytest` green (backend untouched); `npm test` green; `npm run build` passes
- [ ] Manual: no visible UI change after token/primitives landing; icon family consistent
- [ ] Grep gate: no component CSS/TSX contains a visual value that a token already covers
      (`theme.css` excluded)

### MS-P1 — after T07 (Phase P1)
- [ ] `python -m pytest` green; `npm test` green; `npm run build` passes
- [ ] Manual: five-region layout on desktop (≥ 1440), laptop (1024–1439), tablet (768–1023);
      search, playback, replay, history functionally identical; timeline never covers canvas
- [ ] Behavior-preservation check (§§ intro): no state-transition/store/API changes
- [ ] Review focus: token compliance, layer order (where rendered), motion spec compliance

### MS-P2 — after T10 (Phase P2)
- [ ] `python -m pytest` green; `npm test` green; `npm run build` passes
- [ ] Manual: toggle Graph|Map preserves search/playback/selection; Fit uses 40 px padding;
      zoom clamped to [10, 18]; graph node states + legend match; static layers memoized
- [ ] Review focus: renderer toggle store change is the only state addition

### MS-P3 — after T13 (Phase P3)
- [ ] `python -m pytest` green; `npm test` green; `npm run build` passes
- [ ] Manual: tiles load with skeleton + fade; overlays/markers per MAP_RENDERING §7–§15;
      tooltip (hover) + popup (click) work in both renderers; Set as Start/Goal + Center Here work
- [ ] Review focus: no duplicated Frame derivation; Leaflet lifecycle cleanup

### MS-P4 — after T19 (Phase P4)
- [ ] `python -m pytest` green; `npm test` green; `npm run build` passes
- [ ] Manual: header (64 px, no search controls), metrics cards (no tables), history rows memoized
      + newest-first, timeline controls consistent, algorithm selector searchable, node picker
      fuzzy; walk UI at all three widths
- [ ] Review focus: behavior preservation end-to-end before starting P5

### MS-P5 — after T21 (Phase P5)
- [ ] `python -m pytest` green; `npm test` green; `npm run build` passes
- [ ] Manual: OS-level reduced motion disables panel/hover/map/playback interpolation; StatusBar
      colors per DESIGN_TOKENS §25; keyboard-only walkthrough completes (select algorithm, pick
      nodes, run, play, step, replay); axe checks no critical violations

### MS-P6 — after T24 (Phase P6, final)
- [ ] Full gates: `python -m pytest` green; `npm test` green; `npm run build` passes
- [ ] Manual: full cross-renderer walkthrough — search in Graph, switch to Map, identical Frame/
      metrics/history/explanation; replay recorded runs in both renderers; toggle triggers no
      **backend** API call (tile fetches on first Map activation are allowed and verified by
      T11); empty/loading/error states across every region (with backend stopped); history
      fetch failure renders inline indicator without retry
- [ ] **Behavior preservation end-to-end:** search, playback, replay, history, selection, load
      graph, export all behave identically to the pre-polish baseline (regression-tested with
      `python -m pytest` + the existing `ui/web` vitest suite)
- [ ] No unused tokens (grep); all component CSS references existing tokens
- [ ] Backend/algorithm/API diffs: none (git diff check)

---

## 3. Dependency graph

```
P0   T01 ──► T02 ──► T03
P1   T01,T02,T03 ──► T04 ──► T05 ──► T06, T07
P2   T04 ──► T08 ──► T09 ──► T10
P3   T08,T10 ──► T11 ──► T12 ──► T13
P4   T02,T03,T06,T07 ──► T14, T15, T15b, T17
     T03,T05 ──► T18, T19
P5   all above ──► T20, T21
P6   T20,T21 ──► T22 ──► T23 ──► T24
              (T22 also requires T04, T14, T15, T15b, T18 — the regions it instruments)
```

Formal edge list (child ← parents):

- T02 ← T01
- T03 ← T01, T02
- T04 ← T01, T02, T03
- T05 ← T04
- T06 ← T04, T05
- T07 ← T04
- T08 ← T04
- T09 ← T08
- T10 ← T09
- T11 ← T08, T10
- T12 ← T11
- T13 ← T09, T12
- T14 ← T02, T04
- T15 ← T02, T06
- T15b ← T02, T06
- T17 ← T02, T07
- T18 ← T03, T05
- T19 ← T03, T05
- T20 ← T01 (motion tokens), T03 (Skeleton), T06 (InfoPanel — owns status section that
        absorbed the deleted StatusBar), T11 (MapView), T14 (Header), T15 (Metrics),
        T15b (History), T17 (Timeline/Controls), T18 (AlgorithmSelector), T19 (NodePicker)
- T21 ← T02 (Button/TextInput focus rings), T04 (shell tab order), T06 (InfoPanel focus),
        T11 (MapView keyboard handlers), T20 (motion-token focus transitions)
- T22 ← T03 (Skeleton/EmptyState primitives), T04 (GraphPane region), T06 (InfoPanel region),
        T11 (MapView region), T14 (Header region), T15 (MetricsPanel region),
        T15b (HistoryPanel region), T18 (AlgorithmSelector region)
- T23 ← T01, T22
- T24 ← T08–T13, T14–T19 (all renderer + component tasks)

**Parallel development (second workstream, after the listed deps):**
- T14, T15, T15b, T17 (after T02 + the relevant P1 task)
- T18, T19 (after T03/T05)
- T20 may land as multiple PRs (one per component group) per the plan's scope note.

---

## 4. Implementation timeline

Solo critical path ≈ 42 h of engineering (plus gates). Weeks below assume ~60 % utilization with
verification; the parallel P4 lane shortens the week if a second engineer helps.

**Critical path (longest dependency chain):**

```
T01 → T02 → T03 → T04 → T05 → T06 → T08 → T09 → T10 → T11 → T12 → T13 → T22 → T23 → T24
```

Anything off this chain (T07, T14, T15, T15b, T17, T18, T19, T20, T21) can run in parallel
or be deferred without extending the calendar by more than its own duration.

| Week | Tasks | Expected deliverables | Merge points |
|---|---|---|---|
| **W1** | T01…T07 (P0 + P1) | full token set; Panel/SectionCard/Button/TextInput/Icon + Badge/Skeleton/EmptyState; five-region shell with GraphPane; sidebar SectionCards; right InfoPanel (absorbs deleted StatusBar); docked timeline | After every green task; **MS-P0**, **MS-P1** |
| **W2** | T08…T13 (P2 + P3) | renderer toggle (store state, default Map); graph states/layers polish; shared camera/fit (lib/coords refactor); Leaflet map (with leaflet CSS import) + overlays/markers + shared tooltip/popup (popup on map only) | After every green task; **MS-P2**, **MS-P3** |
| **W3** | T14, T15, T15b, T17, T18, T19 (P4) | header (read-only renderer pill); metrics cards; memoized history; timeline/controls; algorithm selector; node picker autocomplete | After every green task; **MS-P4** |
| **W4** | T20…T24 (P5 + P6) | token motion + reduced motion + status states (InfoPanel status section); focus/keyboard/ARIA; all-region loading/empty/error states (history error added); token cleanup; cross-renderer verification | After every green task; **MS-P5**, **MS-P6** = final delivery |

Second-engineer lanes (parallel, no merge conflicts): T14, T15, T15b, T17 (after T02 + P1 deps);
T18, T19 (after T03/T05); T20 component-group sweeps (the plan explicitly allows T20 to land as
multiple PRs).

---

## 5. Task → `UI_IMPLEMENTATION_PLAN.md` mapping (no orphans, no duplicates)

| Task | Plan ref (§7) | Primary spec sources |
|---|---|---|
| T01 | T01 | DESIGN_TOKENS.md; MOTION_SPEC §4/§5 |
| T02 | T02 | COMPONENT_POLISH §5/§17/§18; DESIGN_TOKENS §15 |
| T03 | T03 | MOTION_SPEC §19 |
| T04 | T04 | LAYOUT_SPEC §3/§19 |
| T05 | T05 | COMPONENT_POLISH §4; MOTION_SPEC §15 |
| T06 | T06 | LAYOUT_SPEC §13; UI_POLISH §12 |
| T07 | T07 | UI_POLISH §11 |
| T08 | T08 | LAYOUT_SPEC §9–10; MAP_RENDERING §2; MOTION_SPEC §8/§14 |
| T09 | T09 | MAP_RENDERING; DESIGN_TOKENS §5; LAYOUT_SPEC §23 |
| T10 | T10 | MAP_RENDERING §4 |
| T11 | T11 | MAP_RENDERING §3–6 |
| T12 | T12 | MAP_RENDERING §8–15; MOTION_SPEC §18 |
| T13 | T13 | MAP_RENDERING §17; MOTION_SPEC §17 |
| T14 | T14 | COMPONENT_POLISH §3; LAYOUT_SPEC §5 |
| T15 | T15 | UI_POLISH §13; COMPONENT_POLISH §11; LAYOUT_SPEC §21 |
| T15b | T15b | COMPONENT_POLISH §14/§26 |
| T17 | T17 | COMPONENT_POLISH §13; MOTION_SPEC §12 |
| T18 | T18 | COMPONENT_POLISH §6 |
| T19 | T19 | COMPONENT_POLISH §7 |
| T20 | T20 | MOTION_SPEC §4/§18/§20/§24; COMPONENT_POLISH §10; DESIGN_TOKENS §25 |
| T21 | T21 | LAYOUT_SPEC §24 |
| T22 | T22 | LAYOUT_SPEC §21; MAP_RENDERING §20–21; COMPONENT_POLISH §23 |
| T23 | T23 | — (cleanup task) |
| T24 | T24 | — (verification task) |

No task maps to more than one plan scope; every plan task T01–T24 is fully decomposed with no
overlap. Note: `UI_IMPLEMENTATION_PLAN.md` has no T16 — task numbering follows the plan verbatim
(T14, T15, T15b, T17), and `T15b` sorts directly after `T15`.

> **Footnote — `T16` absence:** the plan deliberately skips `T16` (the gap between T15b and T17).
> This decomposition preserves the gap to keep the mapping 1:1 with the plan. A future task may
> claim `T16`; until then, no `UI-T16` exists.

---

## 6. Daily implementation workflow

```
1. Pick one task from the backlog (in order; honor its Dependencies).
2. Implement it (only files listed under "Files created/modified").
3. Run the task's unit tests.
4. Run the global gates: python -m pytest && cd ui/web && npm test && npm run build.
5. Fix defects before moving on; never commit red.
6. Commit with the task's commit message (one commit per task).
7. Merge (independently mergeable).
8. Re-check the dependency graph: are any now-unblocked tasks ready to pick next?
9. Repeat.
```

Rules:
- One task at a time. If blocked, pick the next unblocked task (see parallel lanes).
- If a mismatch with the UI specs is found, update the source spec **first**, then this file.
- Any new task requires a `Plan ref`; un-mappable tasks are rejected (no orphan work).
- Verify merge-ability: after each task the branch contains exactly that task's diff.
- Behavior preservation is a hard gate: if a task changes state transitions, store semantics, or
  API calls, it is wrong and must be reverted (UI plan §2.3).
- The functional specs (`COMPONENT_SPEC.md`, `GUI_ROADMAP.md`, `MAP_CONTRACT.md`) win on any
  conflict with visual polish.

---

## 7. Change control

- This file is derived, never a source of decisions. Architecture, APIs, components, and
  responsibilities live in the frozen docs; this file only schedules their execution.
- Adding, removing, or re-scoping a task = re-mapping to `UI_IMPLEMENTATION_PLAN.md`, not a design
  change. If no plan section covers the work, it is out of scope and must be raised with the
  roadmap owner first.
