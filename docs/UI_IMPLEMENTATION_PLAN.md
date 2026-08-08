# UI_IMPLEMENTATION_PLAN.md

Version: 1.0

Status: Implementation Plan

# 1. Purpose

This document converts the six UI specifications into a sequenced, independently
reviewable implementation plan for the Delivery AI Search web interface.

| Spec | Role |
| --- | --- |
| [UI_POLISH_SPEC.md](UI_POLISH_SPEC.md) | Overall visual philosophy, layout regions, hierarchy |
| [DESIGN_TOKENS.md](DESIGN_TOKENS.md) | Token system: colors, typography, spacing, radius, shadow, motion, z-index |
| [LAYOUT_SPEC.md](LAYOUT_SPEC.md) | Five-region layout, panel responsibilities, sizing, responsive |
| [MAP_RENDERING_SPEC.md](MAP_RENDERING_SPEC.md) | Graph + Map renderers, camera, overlays, tooltip/popup |
| [COMPONENT_POLISH_SPEC.md](COMPONENT_POLISH_SPEC.md) | Per-component appearance, behavior, accessibility |
| [MOTION_SPEC.md](MOTION_SPEC.md) | Durations, easing, animation guides, reduced motion |

# 2. Scope

## 2.1 In scope

- Design tokens (full DESIGN_TOKENS set).
- Five-region layout (header, left sidebar, center visualization, right info panel, bottom timeline).
- Renderer toggle (Graph | Map) and the Map renderer.
- Node/edge/path visualization states (8 node states, edge categories).
- Component appearance: cards, badges, skeletons, tooltips, popups, buttons, inputs.
- Motion, transitions, and `prefers-reduced-motion` support.
- Loading, empty, and error states for every region.
- Accessibility: visible focus, keyboard nav, ARIA labels.
- Right info panel (new region); history moves there.

## 2.2 Out of scope (hard constraints)

- No backend work.
- No API changes (no endpoint, body, or response changes).
- No `SearchResult` / `SearchStep` changes.
- No `MAP_CONTRACT` modifications.
- No algorithm implementation changes.
- No additional search features, benchmarks, or history data-model changes.
- No new endpoints.
- No architecture changes (store shape may gain renderer state only).

## 2.4 Environment & support matrix (locked)

- **Browser support:** latest 2 stable versions of Chrome, Edge, Firefox, Safari.
  - Pointer + wheel behaviour may differ between Safari/Firefox and Chromium; the
    Fit, wheel-zoom, and drag-pan code paths must be exercised manually on each.
- **Node / build:** same as today (`ui/web/package.json` — Vite + React + TypeScript).
- **Tile provider:** OpenStreetMap default tiles (no API key); attribution shown
  per OSM policy. If OSM is unreachable, T22 renders the centered error card with
  a "Retry tiles" affordance; no automatic fallback to a paid tile provider.
- **Widths supported:** ≥ 768 px (tablet and up). **Widths < 768 px show a centered
  "Best viewed at ≥ 768 px" notice** with the existing fixed layout underneath
  (the layout does not collapse below 768 px in this plan).

Where visual polish conflicts with the functional specs
(`COMPONENT_SPEC.md`, `GUI_ROADMAP.md`, `MAP_CONTRACT.md`),
the functional specs win.

## 2.3 Behavior-preservation rule

Every task must preserve existing behavior:

- search, playback, replay, history, selection, load graph, export.

The visual layer may restructure markup and CSS but never change
state transitions, store semantics, or API calls.

# 3. Design Targets

- Regions: header, left sidebar, center visualization, right info panel, bottom timeline.
- Visual priority: visualization > search controls > metrics > history.
- Header 64–72 px; sidebar 320–420 px; right panel 320–420 px; timeline 96–120 px.
- Graph and Map renderers consume the **same** Frame (derived from SearchStep).
- Renderer switch never reruns search, never resets playback, and preserves camera where possible.
- Motion: max 300 ms UI (400 ms ceiling), token-driven, reduced-motion respected.
- Accessibility: visible focus (2 px, radius 8, Primary-500), logical tab order, ARIA labels.
- **Performance budget (UI surface):**
  - First paint ≤ 200 ms on a cold reload (mock transport).
  - Frame advance ≤ 4 ms during playback (≥ 30 fps).
  - Renderer switch transition ≤ 220 ms (T08 fit).
  - Tile load on first Map activation: skeleton + fade; no blank white panel.
  These mirror `TASK_BREAKDOWN.md §2.6` budgets; this plan owns the *visual*
  side of those budgets.

# 4. Current-State Baseline

Known components in `ui/web/src/`:

- `App.tsx` — shell (header + body + status footer).
- `components/Sidebar`, `ControlPanel`, `AlgorithmSelector`, `shared/NodePicker`.
- `components/StatusBar`, `components/MetricsPanel`.
- `components/StepTimeline`, `shared/AnimationControls`.
- `components/HistoryPanel`, `shared/Tooltip`, `shared/EmptyState`, `shared/Spinner`.
- `components/GraphCanvas` (EdgesLayer, NodesLayer, RouteOverlay, Legend, NodeListFallback).
- `src/styles/theme.css` — token source today.

Gap vs. target:

- No right info panel region; metrics/status live in the sidebar/footer.
- No Graph | Map renderer toggle; no Map renderer (Leaflet).
- Token set is a subset of DESIGN_TOKENS.md.
- No card/badge/skeleton primitives; EmptyState exists but is minimal.

# 5. Quality Gates (run after every task)

```
python -m pytest                     # backend suite stays green (unchanged backend)
cd ui/web && npm test               # vitest suite stays green
cd ui/web && npm run build          # tsc --noEmit + vite build green

# Static grep gates (run from ui/web)
# No component CSS or TSX uses a literal color, duration, easing, or shadow value
# that a token already covers:
grep -rE "(#[0-9a-fA-F]{3,8}|rgba?\(|hsla?\()" src --include="*.css" --include="*.module.css" | grep -v "styles/theme.css"   # should be empty
grep -rE "transition:.*[0-9]+(ms|s)\b" src --include="*.css" --include="*.module.css" | grep -v "styles/theme.css"   # should be empty
```

Manual visual/UX checks (per task):

1. Existing flows (search, playback, replay, history) are functionally identical.
2. Pan / zoom / fit still work.
3. `prefers-reduced-motion` disables motion.
4. Keyboard tab order is logical; focus is visible.

# 6. Implementation Phases

| Phase | Theme | Tasks | Outcome |
| --- | --- | --- | --- |
| P0 | Token foundations | T01–T03 | Full token set + card/badge/skeleton/empty primitives |
| P1 | Layout shell | T04–T07 | Five-region shell, GraphPane, right info panel, timeline dock |
| P2 | Renderer framework | T08–T10 | Renderer toggle + Graph renderer polish (states, camera) |
| P3 | Map renderer | T11–T13 | Leaflet canvas, overlays/markers, tooltip + popup |
| P4 | Component polish | T14, T15, T15b, T17, T18, T19 (T16 intentionally absent — gap reserved for a future task; numbering preserved) | Header, sidebar, metrics, history, timeline controls, pickers |
| P5 | Motion & accessibility | T20–T21 | Motion tokens everywhere, focus/keyboard/ARIA |
| P6 | States & finalization | T22–T24 | Empty/loading/error across regions, token cleanup, cross-renderer verification |

# 7. Task List

Each task is one implementation session, independently reviewable, and ends with
all quality gates green.

## Phase P0 — Token foundations

### T01. Design token expansion

Add every missing token family to `src/styles/theme.css` per DESIGN_TOKENS.md:

- Color scales: primary/secondary/success/warning/danger/info by role; gray scale
  `Gray-50 … Gray-900`; semantic graph colors (normal/visited/current/frontier/start/goal/selected/path).
- Typography: Display XL … Caption sizes, line heights, letter spacing.
- Spacing scale: 4, 8, 12, 16, 24, 32, 40, 48, 64, 80, 96.
- Border radius: sm 4, md 8, lg 12, xl 16, round 9999.
- Border widths: hairline 1, strong 2, focus 2, selected 2.
- Elevation levels 0–4; soft shadow system.
- Opacity: disabled 40%, muted 60%, hover 8%, pressed 12%, selection 16%.
- Motion (MOTION_SPEC §4 names): `--motion-very-fast 100ms`, `--motion-fast 150ms`,
  `--motion-normal 220ms`, `--motion-slow 300ms`.
- Easing (MOTION_SPEC §5):
  - `--ease-default: ease-out` (default for almost everything).
  - `--ease-panel: cubic-bezier(0.22, 1, 0.36, 1)` (sidebar open/close, dialog).
  - `--ease-sidebar: ease-in-out` (DESIGN_TOKENS §17 sidebar easing).
  - `--ease-linear: linear` (opacity, playback interpolation).
  - Forbidden: bounce, elastic, spring, overshoot, back.
- Icon family: **locked — `lucide-react`** (chosen for tree-shakeability, current
  availability, and Stroke-only style consistent with the design language). Expose
  via a `shared/Icon` wrapper that only consumes this set. UI_POLISH §19 forbids
  mixing icon families; MAP_RENDERING §17/§27 and COMPONENT_POLISH §6/§10/§17
  all expect a single, recognizable set (leading icon on AlgorithmSelector,
  left icon on StatusBar, popup actions, etc.).
- Icon sizes 16/20/24/32; node sizes 8/12/14; button/input heights 32/40/48.
- z-index scale: canvas 0, tooltip 100, dropdown 200, sidebar overlay 300, modal 400, toast 500.
  **Layer usage (locked):**
  - canvas 0 — MapView / GraphCanvas tile or SVG layer.
  - tooltip 100 — shared `Tooltip` (hover); below popups so it doesn't intercept clicks.
  - dropdown 200 — `RendererToggle`, `AlgorithmSelector`, `NodePicker`, **popup (map
    click)** so it sits above tooltips.
  - sidebar overlay 300 — tablet sidebar drawer above body.
  - modal 400 — reserved for future error/dialog (unused today).
  - toast 500 — reserved for future notifications (unused today).
- Focus ring token: 2 px, radius 8, Primary-500.
- Card tokens: padding 16, radius 12, gap 16, border Gray-200, background white.

Files touched:

- `ui/web/src/styles/theme.css`
- `ui/web/src/main.tsx` (only if a global reset is required)
- no component files

Acceptance criteria:

- No component CSS or TSX contains a visual value that a token already exists for
  (grep check; `theme.css` excluded).
- Token names follow DESIGN_TOKENS.md naming.
- Motion tier names match MOTION_SPEC §4 (`--motion-very-fast`, `--motion-fast`,
  `--motion-normal`, `--motion-slow`).
- Easing tokens carry explicit values; panel cubic-bezier is `cubic-bezier(0.22, 1, 0.36, 1)`.
- Spacing only uses values from the 8-point scale.
- Single icon family exposed via `shared/Icon` wrapper; no raw SVG paths in components.
- Dark-mode readiness (DESIGN_TOKENS §29): every token is overridable via a
  future `[data-theme="dark"]` block — no duplicated visual values.
- `npm run build` green; existing tests green; no visible UI change.

### T02. Panel + SectionCard + Button + TextInput primitives

Create the reusable surface primitives used by every region.

- `Panel`: white background, radius 12, hairline border (`--c-border`), soft
  elevation level 1, optional title + icon + footer slot.
- `SectionCard`: sidebar variant with padding 16, radius 12, soft elevation level 1
  (matches `Panel` per DESIGN_TOKENS elevation scale), title, divider, content; never
  transparent (COMPONENT_POLISH §5).
- `Button`: variants `primary | secondary | ghost | danger | loading | disabled`,
  height 40 px (small 32, large 48), radius 8; padding 12 horizontal;
  loading shows spinner; disabled uses opacity 40% (DESIGN_TOKENS §15,
  COMPONENT_POLISH §17). All variants consume only motion tokens.
- `TextInput`: height 40 px, radius 8, padding 12, placeholder Gray-500,
  focus primary outline; accessible label + `aria-invalid` (COMPONENT_POLISH §18).
- `Icon`: thin wrapper that only renders the chosen icon family.

Files touched:

- `ui/web/src/components/shared/Panel/index.tsx` (+ `.module.css` + test)
- `ui/web/src/components/shared/SectionCard/index.tsx` (+ `.module.css` + test)
- `ui/web/src/components/shared/Button/index.tsx` (+ `.module.css` + test)
- `ui/web/src/components/shared/TextInput/index.tsx` (+ `.module.css` + test)
- `ui/web/src/components/shared/Icon/index.tsx` (+ `.module.css` + test)
- `ui/web/package.json` (icon dependency, e.g. `lucide-react`)

Acceptance criteria:

- All five primitives consume only tokens (radius, spacing, border, shadow,
  motion, color).
- `Button` renders every variant in tests; loading + disabled states behave as
  specified; reduced-motion respected.
- `TextInput` shows focus ring (`--shadow-focus` or equivalent), validates
  ARIA props, accepts controlled and uncontrolled usage.
- `Icon` exposes only the chosen family; no raw SVG paths in components.
- Semantic HTML (`<section>`, `<header>`, `<footer>`, `<button>`, `<input>`);
  no behavior changes.
- New tests render every variant; existing suites green; build green.

### T03. Badge + Skeleton + EmptyState primitives

Create the reusable state primitives.

- `Badge`: variants (info/success/warning/danger), small, rounded (9999),
  supports Real / Mock / status content; never dominates layout.
- `Skeleton`: shimmer placeholder that preserves component dimensions;
  allowed for history, metrics, algorithm catalog, version (MOTION §19).
- `EmptyState`: icon + title + description + optional action button;
  replaces the existing minimal `shared/EmptyState`.

Files touched:

- `ui/web/src/components/shared/Badge/index.tsx` (+ `.module.css` + test)
- `ui/web/src/components/shared/Skeleton/index.tsx` (+ `.module.css` + test)
- `ui/web/src/components/shared/EmptyState/index.tsx` (+ `.module.css`; refactor)

Acceptance criteria:

- Badge renders all variants with token colors; keyboard-accessible (no `aria-hidden` on content).
- Skeleton uses `--motion-slow` pulse, fixed dimensions, `aria-hidden`, never causes layout shift.
- EmptyState includes illustration slot, title, description, and CTA; ARIA labelled.
- Existing consumers of `EmptyState` still render; all tests green.

## Phase P1 — Layout shell

### T04. Five-region app shell

Restructure `App.tsx` into the five-region layout (LAYOUT_SPEC §3):

```
Header (fixed, 64 px)
Left Sidebar | Center Visualization | Right Info Panel
Playback Timeline (docked bottom, 96–120 px)
```

- Header fixed, height 64 px, white, bottom border only.
- Body is a three-column flex/grid: sidebar | main | right panel.
- Main visualization region gets `flex: 1; min-width: 0`.
- StatusBar stops being the footer; **resolution (locked):** the existing
  `components/StatusBar/index.tsx` is **deleted** in this task. Its responsibilities
  are absorbed into a new "Status" section rendered by `InfoPanel` (T06). All future
  StatusBar polish (T20) targets the InfoPanel Status section, not a standalone
  component. This avoids a dual StatusBar/Status-section duplication.
- Timeline region spans full width beneath the body, docked, never overlapping the canvas.
- Introduce the new `GraphPane` wrapper as the visualization host
  (consumed by T08) plus its first test file (the integration test referenced by T23).

Files touched:

- `ui/web/src/App.tsx`
- `ui/web/src/styles/theme.css` (shell classes; refactor `app-*` into tokens)
- `ui/web/src/components/StatusBar/index.tsx` (move out of footer role)
- `ui/web/src/components/GraphPane/index.tsx` (+ `.module.css` + test)

Acceptance criteria:

- Five visible regions on desktop; header and timeline fixed.
- Visualization occupies the largest region (≥ 60% width).
- Responsive behavior (LAYOUT_SPEC §19):
  - Desktop ≥ 1440 px: three-column layout.
  - Laptop 1024–1439 px: three-column, narrower right panel.
  - Tablet 768–1023 px: sidebar collapses to drawer; timeline remains docked.
  - **< 768 px (mobile/narrow):** render a centered notice "Best viewed at ≥ 768 px"
    overlaying the existing layout; the layout does not collapse below 768 px in
    this plan. Out-of-scope for further responsive work.
- Search still runs, playback still works, history still loads.
- `GraphPane` test file renders the wrapper and asserts region/role markup.
- All suites green; build green.

### T05. Left Sidebar restructure

Group the sidebar into ordered section cards (COMPONENT_POLISH §4):

- Search (start, goal)
- Algorithm (algorithm selector)
- Execution (Run)
- Optional Advanced

- 24 px between sections; each section = title + divider + content.
- Width 320–420 px (preferred 360); independent vertical scroll.
- Metrics and History are removed from the sidebar (they move to the right panel in T06).

Files touched:

- `ui/web/src/components/Sidebar/index.tsx` (+ `.module.css`)
- `ui/web/src/components/ControlPanel/index.tsx` (+ `.module.css`) — regroup content

Acceptance criteria:

- Sidebar shows only search configuration; no metrics/history inside.
- Sections visually separated with titles and dividers; spacing uses 8-point tokens.
- Sidebar **drawer** animation (tablet 768–1023 px only; desktop sidebar is fixed
  per T04, not a drawer) honors MOTION §15: open/close 220 ms slide + fade with
  `--ease-panel`. **Advanced section** height-expansion animation is capped at
  220 ms on all widths.
- No store/API changes; existing ControlPanel tests still pass (or updated only for markup).

### T06. Right Information Panel

Create the right panel region (LAYOUT_SPEC §13, UI_POLISH §12):

- Status section (top, always visible).
- Metrics section (compact cards; below status).
- Search explanation / current node / current frontier.
- History panel (moved from sidebar; supporting role, never dominant).
- Preferred width 360 px (320–420); scrolls independently; contains no search controls.

Files touched:

- `ui/web/src/components/InfoPanel/index.tsx` (+ `.module.css` + test)
- `ui/web/src/components/Sidebar/index.tsx` (remove history)
- `ui/web/src/components/HistoryPanel/index.tsx` (consumer unchanged)

Acceptance criteria:

- Right panel shows status, metrics, explanation, and history after search.
- No search controls in the panel.
- History still replays runs; existing history tests green.

### T07. Playback timeline dock

Ensure the timeline is docked at the bottom, spanning full width:

- Height 96–120 px when active.
- Contains play/pause/restart/prev/next, speed, progress slider, current step,
  step count, playback status (UI_POLISH §11).
- Never covers the visualization; hides gracefully when no result exists.

Files touched:

- `ui/web/src/components/StepTimeline/index.tsx` (+ `.module.css`)
- `ui/web/src/components/shared/AnimationControls/index.tsx` (+ `.module.css`)
- `ui/web/src/App.tsx` (dock placement)

Acceptance criteria:

- Timeline occupies its own docked region; canvas untouched by timeline overlays.
- All required controls present and functional (existing playback logic unchanged).
- Reduced-motion respected; tests green; build green.

## Phase P2 — Renderer framework

### T08. Renderer toggle (Graph | Map)

Add a segmented control above the visualization (LAYOUT_SPEC §9–10):

- Store `renderer: "graph" | "map"` in the store (new state, no API change).
- Switching renderer must NOT rerun search, reset playback, or change SearchResult.
- Switching renderer must NOT trigger any **backend API call** (`/graph`, `/search`,
  `/history`, `/algorithms`, `/version`, `/health`). Switching to Map for the first
  time **does** fetch OpenStreetMap tiles from the third-party tile server; this is
  expected and is not a backend API call. Toggling back to Graph drops the map but
  preserves state.
- Camera/selection preserved where possible.
- Default renderer: Map (MAP_RENDERING_SPEC §2) — graph mode still reachable.

Files touched:

- `ui/web/src/components/RendererToggle/index.tsx` (+ `.module.css` + test)
- `ui/web/src/state/store.ts` (renderer state + setter)
- `ui/web/src/components/GraphPane/index.tsx` (renders toggle + active renderer)

Acceptance criteria:

- Toggle switches renderers instantly with animated transition (MOTION §8/§14).
- Search state, playback position, and selected node survive a switch.
- Fit View transition is 220 ms with `--ease-panel` (MOTION §14).
- New store test asserts renderer transitions; no **backend** API calls are
  triggered by `setRenderer()` (tile fetches on first Map activation are acceptable
  and are guarded separately in T11).

### T09. Graph renderer polish (states + layers)

Polish GraphCanvas per MAP_RENDERING_SPEC + DESIGN_TOKENS §5:

- 8 node states visually distinct: normal, start, goal, visited, current, path,
  frontier, selected (differ by color, size, border, opacity; sizes 8/12/14).
- Edge categories: normal, visited, current traversal, final path — final path
  has strongest emphasis (wider, accent color, subtle glow).
- Layer order (LAYOUT_SPEC §23): edges → visited → path → nodes → selected → tooltip.
- Static layers (edges, base nodes) memoized and separate from animated layers.
- Graph background neutral gray (canvas Gray-50).

Files touched:

- `ui/web/src/components/GraphCanvas/index.tsx` (+ `.module.css`)
- `ui/web/src/components/GraphCanvas/RouteOverlay.tsx` (align states to tokens)
- `ui/web/src/components/GraphCanvas/Legend.tsx` (keep in sync with new colors)

Acceptance criteria:

- Each node state has a distinct, token-driven style; legend matches rendering.
- Final path edges are visually strongest; layer order correct.
- Re-renders limited to animated layers during playback. **Assertion:** static-layer
  components (Edges, base Nodes) render **0 times** across N=50 playback steps in
  the test (verified via render-prop spy or `react-test-renderer`'s `toJSON()` count);
  only the animated current-node and route overlay may re-render.
- All existing GraphCanvas tests pass (updated expectations only for colors/markup).

### T10. Shared camera + fit rules (graph + map)

Apply camera rules to **both** renderers (MAP_RENDERING_SPEC §4):

- Initial camera fits graph bounds automatically; never zooms to world.
- Fit padding 40 px; zoom clamped to [10, 18] equivalents.
- Fit button, wheel zoom, double-click zoom, drag, keyboard already exist — keep behavior.
- Graph renderer uses its existing SVG viewBox + transform stack.
- Map renderer uses the Leaflet `map.fitBounds(bounds, { padding: [40, 40] })` API.

Files touched:

- `ui/web/src/lib/coords.ts` (bounds/fit helpers; pure, reusable by either renderer)
- `ui/web/src/components/GraphCanvas/index.tsx`

Note: `ui/web/src/components/MapView/index.tsx` does not exist until T11. The fit helper
is wired into MapView in **T11**, not here. T10 only refactors `lib/coords.ts` and updates
the GraphCanvas to consume the new helper.

Acceptance criteria:

- Initial view and Fit use 40 px padding in both renderers; zoom stays within [10, 18].
- Camera is preserved across renderer switches where the graph fits.
- Existing pan/zoom tests green; map camera is unit-testable via the pure helper.

## Phase P3 — Map renderer

### T11. Leaflet map canvas

Create the street-map renderer (MAP_RENDERING_SPEC §3–6):

- Leaflet + OpenStreetMap tiles.
- Interactions: mouse wheel zoom, drag, double-click zoom, touch pinch, keyboard, Fit.
- Initial camera fits graph bounds (40 px padding), min zoom 10, max zoom 18.
- Loading state: skeleton map + fade, never a blank white panel.
- Top-right floating controls: +, −, Fit, Locate Graph.

Files touched:

- `ui/web/src/components/MapView/index.tsx` (+ `.module.css` + test)
- `ui/web/src/components/MapView/useLeaflet.ts` (init/lifecycle hook)
- `ui/web/package.json` (add leaflet dependency)

Acceptance criteria:

- Tiles render; map interactions work; fit button works.
- No graph/search logic inside MapView — pure presentational shell.
- `leaflet/dist/leaflet.css` imported exactly once (at `main.tsx` or at the top of
  `MapView/index.tsx`) so tile layers style correctly in production.
- jsdom-safe tests (map init guarded); all suites green; build green.

### T12. Map overlays + markers

Draw the graph on top of the tiles (MAP_RENDERING_SPEC §8–15):

- Road graph: 2 px, gray-400, 55% opacity, lightweight.
- Animated path: bright blue, 5 px, rounded caps/joins, small glow, drawn
  progressively; never flashes.
- Visited nodes: small circles r 5, primary blue, 35% opacity, accumulate.
- Current node: r 8, white border, blue fill, soft one-shot pulse.
- Start marker: large green pin, persistent. Goal marker: large red pin, persistent.
- Overlay order: tiles → road graph → animated route → visited → current → markers.
- Labels hidden by default; shown on hover/selection/search.
- Node interaction styles (MAP_RENDERING §14):
  - Hover: white halo (subtle ring), tooltip fades in (T13).
  - Selected: blue outline (`--c-selected` or equivalent).
  - Keyboard focus: dashed outline; visible focus ring follows T21.
  - Current node soft pulse fires once on entry, never infinite (MOTION §18).

Files touched:

- `ui/web/src/components/MapView/Overlays.tsx` (+ `.module.css`)
- `ui/web/src/components/MapView/RouteLine.tsx`
- `ui/web/src/components/MapView/useFrameSync.ts` — thin wrapper that calls the
  existing `frameAt(steps, activeIndex)` from `ui/web/src/services/animation.ts`
  (no duplication of Frame derivation).

Acceptance criteria:

- Overlay order matches MAP_RENDERING_SPEC §7.
- Start/goal markers persistent; visited nodes accumulate per SearchStep.
- Route draws progressively at the **current playback rate** (respects the speed
  selector from T17; never faster than the timeline beat), synced with the timeline.
- The map consumes the exact same Frame as the graph renderer — no duplicated state.

### T13. Tooltip + Popup (shared)

- Tooltip (hover): node name, id, type, coordinates, optional distance; small
  rounded card, max width 300 px; 100 ms fade + 2 px translateY (MOTION §17).
- Popup (click): location name, node type, lat/lon, actions Set as Start,
  Set as Goal, Center Here, Close (MAP_RENDERING_SPEC §17).
- Popup actions call existing store actions; keyboard accessible.

Files touched:

- `ui/web/src/components/shared/Tooltip/index.tsx` (+ `.module.css`; polish existing)
- `ui/web/src/components/shared/Popup/index.tsx` (+ `.module.css` + test)
- `ui/web/src/components/GraphCanvas/index.tsx` (wire tooltip)
- `ui/web/src/components/MapView/index.tsx` (wire tooltip + popup)

Acceptance criteria:

- Hover shows tooltip; click shows popup; both keyboard-reachable.
- **Popup is rendered only by MapView** (per MAP_RENDERING §17). GraphCanvas receives
  only the shared `Tooltip` on hover/selection; there is no popup in graph mode.
- "Set as Start/Goal" and "Center Here" work in both renderers (the underlying store
  actions are shared).
- All tooltips/popups respect `prefers-reduced-motion`; tests green.

## Phase P4 — Component polish

### T14. Header

Polish the header (COMPONENT_POLISH §3, LAYOUT_SPEC §5):

- Height 64 px, fixed, white, bottom border only, no large shadows.
- App logo + title left; right side: backend status, API version, **read-only** renderer
  indicator pill.
- No search controls in the header.
- **Renderer-control ownership:** the Header's renderer pill is a **read-only indicator**
  (label + active renderer) and is not a control. The only interactive renderer control
  is the segmented `RendererToggle` in `GraphPane` (T08). Clicking the pill is a no-op
  (or scrolls to / focuses the toggle — decide in T14). This avoids two affordances
  for the same state in different regions.

Files touched:

- `ui/web/src/components/Header/index.tsx` (+ `.module.css` + test)
- `ui/web/src/App.tsx` (use Header)

Acceptance criteria:

- Header shows title, backend status, version, active renderer (as a read-only indicator
  pill — **not** a control).
- No search controls; existing health/version data reused (no API change).
- The renderer pill's interactive behavior (no-op vs scroll-to-toggle) is decided during
  implementation; documented behavior must not duplicate `RendererToggle`'s role.

### T15. Metrics panel polish

Metrics as compact cards (UI_POLISH §13, COMPONENT_POLISH §11):

- Each card: icon, title, value, unit.
- 2-column grid on desktop; consistent card dimensions; no tables.
- Tabular numerals; large numbers.
- Empty state: "No search completed" message + guidance (LAYOUT_SPEC §21).

Files touched:

- `ui/web/src/components/MetricsPanel/index.tsx` (+ `.module.css` + test)

Acceptance criteria:

- Metrics render as uniform cards, not a table.
- Values use tabular-nums; empty state explains how to run a search.
- Existing metric formatting logic (lib/format) reused; tests green.

### T15b. History panel polish

Polish the HistoryPanel now living inside the InfoPanel (COMPONENT_POLISH §14, §26):

- Compact cards; each row shows algorithm, start, goal, time, Replay button.
- Newest first.
- Hover elevation (`--shadow-2`) and `--motion-fast` transition.
- Each row is memoized (React.memo) to avoid rerenders during playback
  (COMPONENT_POLISH §26 explicit requirement).
- Empty state: "No searches recorded yet." (no CTA — organic).
- Loading state: skeleton rows that preserve height.

Files touched:

- `ui/web/src/components/HistoryPanel/index.tsx` (+ `.module.css` + test)

Acceptance criteria:

- Rows render newest-first; hover elevation visible.
- Each row is `React.memo`-wrapped; React DevTools / test confirms no
  rerender when `activeIndex` changes during playback.
- Empty + loading states render; existing replay functionality preserved.
- Tests green; build green.

### T17. Timeline + animation controls polish

- Slider large and easy to drag; current step always visible; optional ticks.
- Controls: square, equal-size, grouped; hover soft elevation; pressed scale 0.98;
  disabled reduced opacity (COMPONENT_POLISH §13).
- Speed selector present; Play linear, Pause immediate, Restart fades current
  path and starts from step 0, Jump immediate (MOTION §12).

Files touched:

- `ui/web/src/components/StepTimeline/index.tsx` (+ `.module.css`)
- `ui/web/src/components/shared/AnimationControls/index.tsx` (+ `.module.css`)
- `ui/web/src/components/StepTimeline/usePlayback.ts` (if timing refactor needed)

Acceptance criteria:

- All controls visually consistent (square, equal size, grouped); pressed scale 0.98.
- Slider drag maps 1:1 to step index; current step + total always visible.
- Playback timing uses `requestAnimationFrame`; no layout-thrash per step.
- Existing playback tests green.

### T18. Algorithm selector polish

- Dropdown with leading icon, algorithm name + description, Real/Mock badge.
- Searchable; keyboard accessible; never hardcodes algorithm names
  (catalog comes from the store, as today).
- Selected value remains visible (COMPONENT_POLISH §6).

Files touched:

- `ui/web/src/components/AlgorithmSelector/index.tsx` (+ `.module.css` + test)
- `ui/web/src/components/shared/Badge/index.tsx` (reuse)

Acceptance criteria:

- Selector shows name, description, badge; search filters options.
- Catalog still loaded once from the store; no API changes.
- Existing AlgorithmSelector tests pass (updated for markup).

### T19. Node picker polish

- Dropdown selection + autocomplete search; fuzzy matching; instant filtering.
- Max 8 visible results; scrollable; recent selections; clear button.
- Placeholder "Choose a location...".
- Works alongside direct map/graph click selection (both methods freely mixable).

Files touched:

- `ui/web/src/components/shared/NodePicker/index.tsx` (+ `.module.css` + test)

Acceptance criteria:

- Autocomplete filters by node id, name, street/POI; fuzzy matches accepted.
- At most 8 results visible; recent selections persist in session only.
- Clear button resets picker; store selection behavior unchanged.

## Phase P5 — Motion & accessibility

### T20. Motion tokens everywhere + reduced motion

- Every transition/animation consumes the motion tokens (MOTION §4, §24);
  no hardcoded durations/easing in components.
- Allowed animations (exhaustive list — anything outside is forbidden):
  - Opacity fades (toasts, popup open/close, status state change).
  - Translate (tooltip 2 px, drawer slide-in, panel expansion).
  - Scale 0.98→1 (button pressed feedback).
  - Spinner rotation (loading indicators).
  - Skeleton shimmer (T03; uses `--motion-slow`).
  - One-shot pulse (T12 current-node entry; non-infinite).
  - SVG stroke-dashoffset path-draw (T12 RouteLine; respects playback speed).
  - Fit-camera transition (T08; 220 ms with `--ease-panel`).
  Forbidden: bounce, elastic, spring, overshoot, back, and any non-listed motion.
- `prefers-reduced-motion`: disable playback interpolation, panel/hover/map
  animations; keep opacity and instant state changes (MOTION §20).
- Status bar (COMPONENT_POLISH §10): compact card layout, left icon, status
  text, optional description; color by state per DESIGN_TOKENS §25
  (Idle gray, Loading primary, Running info, Completed success, Warning
  warning, Failed danger); never flash. Motion per §18:
  Loading/Searching spinner; Success/Error fade; Finished one-shot accent pulse.
- Scope note: this task may land as multiple PRs (one per component group)
  if the CSS sweep is too large for a single session. The shared media-query
  helper and token wiring land first; per-component sweeps follow.

Files touched:

- all component `.module.css` files with transitions
- `ui/web/src/components/StatusBar/index.tsx` (+ `.module.css`) — state styling
- `ui/web/src/styles/theme.css` — motion tokens (already added in T01) and the
  global `prefers-reduced-motion` media query

Acceptance criteria:

- Grep shows no literal `transition: … ms` outside tokens/theme.
- Reduced-motion media query disables the listed motion; UI remains usable.
- Status colors per DESIGN_TOKENS §25 (Idle gray, Loading primary, Running info,
  Completed success, Warning warning, Failed danger).

### T21. Focus, keyboard nav, ARIA

- Visible focus ring on every interactive element (2 px, radius 8, Primary-500).
- Tab order: header → sidebar → visualization → right panel → timeline (LAYOUT §24).
- ARIA labels on icon-only controls; tooltips/popups screen-reader friendly.
- Canvas/Map keyboard pan and selection accessible.

Files touched:

- global focus styles in `ui/web/src/styles/theme.css`
- interactive components (buttons, selectors, timeline, canvas, map)
- `ui/web/src/components/MapView/index.tsx` (keyboard handlers)

Acceptance criteria:

- Keyboard-only walkthrough completes: select algorithm, pick nodes, run, play,
  step, replay.
- Focus never disappears (no `outline: none` without replacement).
- axe-style checks (or equivalent) report no critical violations.

## Phase P6 — States & finalization

### T22. Loading / empty / error states across regions

- Every region gets skeleton loading (history, metrics, algorithm catalog,
  version, header right-side) — never blank panels; layout preserved during
  loading.
- **Empty states** explain why + offer a primary action when one exists:
  - Visualization: "Load graph to begin." → **primary action button** "Load graph"
    (calls `loadGraph`; this is an empty-state action, not a retry).
  - Metrics: "Run a search to see metrics." (no action — selection-driven).
  - History: "No searches recorded yet." (no action — organic).
  - AlgorithmSelector: "Loading catalog…" → empty copy "Catalog unavailable." if
    catalog fails (no retry surface — see error states below).
- **Error states** (LAYOUT_SPEC §21 + MAP_RENDERING §21) — the retry-surface list is
  exhaustive:
  - Graph load failure: error icon, message, **Retry button** (calls `loadGraph`).
  - Search failure: error icon + message inside InfoPanel status section; **no
    auto-retry** (per existing behavior; see StatusBar Retry rules).
  - Catalog fetch failure: **inline error indicator in AlgorithmSelector**; no retry
    surface.
  - Version fetch failure: **inline error indicator in header**; no retry surface.
  - **History fetch failure: inline error indicator in HistoryPanel; no retry
    surface** (added — previously undefined).
  - Map tile fetch failure: centered error card on the Map region; "Retry tiles" button
    re-issues tile requests only (does not call the backend API).
- Map empty / error states (MAP_RENDERING §20/§21): centered illustration /
  error card; layout dims but does not collapse.
- Error states never expose stack traces (COMPONENT_POLISH §23).

Files touched:

- `ui/web/src/components/InfoPanel/index.tsx` (+ `.module.css`)
- `ui/web/src/components/HistoryPanel/index.tsx` (+ `.module.css`)
- `ui/web/src/components/MetricsPanel/index.tsx` (+ `.module.css`)
- `ui/web/src/components/GraphPane/index.tsx` (+ `.module.css`)
- `ui/web/src/components/MapView/index.tsx` (+ `.module.css`)
- `ui/web/src/components/Header/index.tsx` (+ `.module.css`)
- `ui/web/src/components/AlgorithmSelector/index.tsx` (+ `.module.css`)
- `ui/web/src/components/shared/Skeleton/index.tsx` (reuse)
- `ui/web/src/components/shared/EmptyState/index.tsx` (reuse)

Acceptance criteria:

- No region shows an empty white panel while loading; skeletons appear in
  history, metrics, algorithm catalog, version, and header right-side slots.
- Every empty state has title + description + (when applicable) **primary action
  button** (not a "retry" — retry is reserved for error states).
- Every error state has icon + message + (when in the retry-surface list above) Retry
  button. The retry-surface list is exhaustive; regions outside it render a
  non-actionable error indicator.
- History fetch failure renders an inline indicator in HistoryPanel; the catalog,
  version, history, and search failures explicitly do **not** expose retry.
- Map renders centered empty/error card per MAP_RENDERING §20/§21.
- No stack traces leak to UI.
- Tests green; build green.

### T23. Token cleanup + docs sync

- Remove tokens/components superseded by the new primitives.
- Sync component module CSS to the final token names.
- Update `ui/web/README.md` component index if it exists.

Files touched:

- `ui/web/src/styles/theme.css`
- any CSS module with stale token names
- `ui/web/README.md` (if present)

Acceptance criteria:

- No unused token definitions (grep for each token's usage).
- All component CSS references tokens that exist.
- Build green.

### T24. Cross-renderer verification

Final integration check (manual + automated):

- Run a search in Graph mode; switch to Map; verify identical Frame, metrics,
  history, explanation.
- Replay a recorded run in both renderers.
- Confirm no search rerun on toggle; camera preserved where possible.

Files touched:

- `ui/web/src/components/GraphPane/index.test.tsx` (integration-style test)

Acceptance criteria:

- Graph and Map produce identical step-by-step results from the same SearchResult.
- Replay works in both renderers; toggle never triggers a network call.
- Full quality gates green.

# 8. Dependency Graph

```
P0  T01 ──> T02 ──> T03
P1  T01,T02,T03 ──> T04 ──> T05 ──> T06, T07
P2  T04 ──> T08 ──> T09 ──> T10
P3  T08,T10 ──> T11 ──> T12 ──> T13
P4  T02,T03,T06,T07 ──> T14, T15, T15b, T17
    T03,T05 ──> T18, T19
P5  all above ──> T20, T21
P6  T20,T21 ──> T22 ──> T23 ──> T24
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
- T20 ← T01 (motion tokens), T03 (Skeleton), T06 (InfoPanel), T11 (MapView),
        T14 (Header), T15 (Metrics), T15b (History), T17 (Timeline/Controls),
        T18 (AlgorithmSelector), T19 (NodePicker)
- T21 ← T04, T11, T20
- T22 ← T03 (Skeleton/EmptyState primitives), T04 (GraphPane region), T06 (InfoPanel
        region), T11 (MapView region), T14 (Header region), T15 (MetricsPanel region),
        T15b (HistoryPanel region), T18 (AlgorithmSelector region)
- T23 ← T01, T22
- T24 ← T08–T13, T14–T19 (all renderer + component tasks)

# 9. Estimated Files Touched (totals, approximate)

Counts are approximate; per-component style/test files are included for new components.
Modified files include CSS-module companions and any callers required for refactors.

| Phase | New files (approx.) | Modified files (approx.) | Est. tests added |
| --- | --- | --- | --- |
| P0 | 15 (5 primitives × 3 + Badge/Skeleton × 3 + EmptyState refactor) | 2 (theme.css, main.tsx) | 7 |
| P1 | 4 (GraphPane × 3 + InfoPanel × 1) | 6 | 3 |
| P2 | 3 (MapView/Overlays, RouteLine, useFrameSync consumers) | 5 | 4 |
| P3 | 9 (MapView × 3 + Overlays × 3 + RouteLine × 1 + useFrameSync × 1 + Popup × 3 — adjust for cross-list) | 4 | 6 |
| P4 | 3 (Header × 3) | 8 (MetricsPanel, HistoryPanel, StepTimeline, AnimationControls, AlgorithmSelector, NodePicker, Sidebar reuse, App) | 6 |
| P5 | 0 | 13 (all `.module.css` with transitions + StatusBar/InfoPanel status section + theme.css media query) | 2 |
| P6 | 0 | 9 (InfoPanel, HistoryPanel, MetricsPanel, GraphPane, MapView, Header, AlgorithmSelector + theme.css + README) | 2 |
| **Total** | **~30–35** | **~45–50** | **~30** |

No backend, algorithm, or API files are touched in any phase.

Notes on the new count vs. the original draft:

- P0 +1 new file and +1 test (T02 now ships `Button`, `TextInput`, and
  `Icon` in addition to `Panel` and `SectionCard`).
- P4 +3 new files and +1 test (T15b adds a dedicated `HistoryPanel` polish
  task with its own module + test).
- P5 +1 modified file (T20 now also touches `HistoryPanel` and the history
  polish surface from T15b).
- P6 +1 modified file (T22 also covers the new primitives).

# 10. Review Ritual

- One branch per task (or per phase when the phase is a single review unit).
- Every task lands with: quality gates green (§5), no backend/API diffs,
  existing tests intact (or updated only for markup/colors), new tests for new behavior.
- Review focuses on: token compliance, behavior preservation, layer order,
  motion spec compliance, accessibility.
- Phase checkpoints: at the end of P0, P1, P2, P3, and P4, the reviewer also
  walks the live UI on desktop, laptop, and tablet widths and confirms the
  behavior-preservation check (§2.3) end-to-end before merging the next phase.

# 11. Assumptions & Decisions

- Map library: **Leaflet + OpenStreetMap** (MAP_RENDERING_SPEC §3 allows Leaflet;
  MapLibre is the alternative if a WebGL canvas is preferred later).
- Renderer default vs. order:
  - Default renderer on first load: **Map** (MAP_RENDERING_SPEC §2).
  - Segmented control order: **Graph | Map** (UI_POLISH §8 example order).
- Status placement (resolved): the right info panel owns the Status section
  (LAYOUT_SPEC §13/§15), not the sidebar. COMPONENT_POLISH §4 lists
  "Status Summary" inside the sidebar, but LAYOUT_SPEC §13/§15 is the
  layout authority and explicitly assigns Status to the right panel.
  The plan follows LAYOUT_SPEC. Sidebar (T05) therefore contains only
  Search / Algorithm / Execution / Optional Advanced groups.
- Dark mode: optional per DESIGN_TOKENS §29 — not in scope for this plan;
  T01 ensures tokens are overridable for a future `[data-theme="dark"]` block.
- Timeline hides when no result exists, preserving the current "no playback" behavior.
- Node picker "recent selections" are session-scoped only (no persistence API).
- Motion tier names follow MOTION_SPEC §4 verbatim (`--motion-very-fast`,
  `--motion-fast`, `--motion-normal`, `--motion-slow`) rather than the
  generic DESIGN_TOKENS §16 Fast/Normal/Slow labels. The motion spec is
  the dedicated motion authority.

# 12. Glossary

| Term | Meaning |
| --- | --- |
| Frame | Derived animation state (visited/current/frontier/path) from SearchStep |
| Renderer | Active mode: `graph` or `map` |
| GraphPane | Visualization region wrapper hosting the renderer toggle + active renderer |
| SectionCard | Sidebar section primitive (title + divider + content) |
| InfoPanel | Right-side information region (status, metrics, explanation, history) |
| Skeleton | Layout-preserving loading placeholder |

---
