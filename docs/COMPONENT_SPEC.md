# COMPONENT_SPEC.md

**HCMC Delivery AI Search — Final Frontend Component Specification (pre-implementation)**

Version: 1.1

Owner: Hưng (frontend)

Status: **Authoritative** for every React component: purpose, responsibilities, props,
store usage, events, lifecycle, rendering/interaction flows, states, accessibility,
performance, styling references, acceptance criteria, unit-test requirements, and safe
extension.

**Compatibility contract**
- Complies with `GUI_ROADMAP.md v2.0` (`§4` architecture + store, `§8` state machine,
  `§9` animation, `§14` conventions, `§15` testing, `§16` phases),
  `IMPLEMENTATION_PLAN.md` (`§B` React arch, `§C` GraphCanvas, `§D` component specs,
  `§H` DoD), `UI_DESIGN_SYSTEM.md` (appearance — referenced, not duplicated),
  `ARCHITECTURE.md`, `MAP_CONTRACT.md` (payload shapes, snake_case fields),
  and repo naming conventions (`GUI_ROADMAP §14`).
- **Does not** change architecture, APIs, `SearchResult`, `SearchStep`, `SearchMetrics`,
  ownership, implementation phases, or backend responsibilities.
- **No backend logic invented.** Every value comes from a documented API response, the
  store, or is derived front end–only.
- Styling is referenced by section (e.g. "UI §9.3"); no colors/sizes redefined here.

---

## 0. Cross-cutting conventions (read first)

### 0.1 Folder + naming (`GUI_ROADMAP §14`, `UI §18`)
- One feature folder per component: `components/<PascalCase>/index.tsx`,
  `<same>/styles.css`, `<same>/<PascalCase>.test.tsx`.
- Components = PascalCase functions; hooks `use*`; store actions `verbObject`; selectors
  `select*`; JSON fields stay `snake_case` (UI never renames them).

### 0.2 Store (Zustand) — canonical slices (`GUI_ROADMAP §4`)

| Slice | Fields |
|---|---|
| `graph` | `geojsonNodes`, `geojsonEdges`, `bbox` |
| `search` | `selectedAlgorithm`, `start`, `goal`, `result`, `source` (`"real"`\|`"mock"`) |
| `animation` | `activeIndex`, `playing`, `speed`, `status` |
| `metrics` | (derived selector from `search.result`, front end–only) |
| `history` | `runs[]` |
| `ui` | `panelOpen`, `selectedNode`, `hoveredStep`, `modal`, `theme`, `toasts`, `route` |

Derived metric (front end–only): `hops = path.length - 1`,
`nodesVisited = visited_nodes.length`; the four numbers are copied verbatim from
`SearchResult`: `total_distance_km`, `total_time_min`, `total_cost`,
`processing_time_ms`. No new backend data.

### 0.3 Actions (the only writers)

| Action | Effect |
|---|---|
| `loadGraph()` | `GET /graph` → `graph`; `Loading → Ready` or `Error` |
| `setAlgorithm(id)` | select algorithm id |
| `setStart(id)` / `setGoal(id)` | set node ids |
| `runSearch()` | validate → `POST /search` → `result`/`source`; seed frames |
| `stepTo(i)` / `advance()` | move `animation.activeIndex` |
| `play()` / `pause()` / `restart()` / `setSpeed(m)` | playback; status transitions |
| `replayRun(runId)` | hydrate from `history` (no network) |
| `setStatus(s)` | one of 8 states (§0.4) |
| `setSelectedNode(id?)` | canvas selection |
| `setHoveredStep(i?)` | timeline hover sync |
| `selectNode(id)` | user clicks a node (feeds start/goal/inspection) |
| `setModal(open?, payload?)` | modal host |
| `pushToast(t)` / `dismissToast(id)` | notifications |
| `setTheme(mode)` | `data-theme`, persisted |

### 0.4 Status machine (`GUI_ROADMAP §8`)
`Idle · Loading · Ready · Playing · Paused · Finished · Error · Replay` — single writer
`setStatus`; mirrored by `StatusBar`.

### 0.5 Behavior rules (apply to every component)
- Never branch on an algorithm **name**; only on catalog metadata (`source`, `label`).
- Only the store persists state; presentational components are pure/fn of props + slices.
- Components never write slices directly; they dispatch actions.

---

# 1. Component specifications

## 1.1 App

**Purpose:** application bootstrap — mount providers, load the graph, own the shell error
boundary and global hosts.

**Responsibilities:** set theme (`ThemeProvider`), call `loadGraph()` once on mount, render
`Layout`, catch fatal render errors (`ErrorBoundary`), host `Modal` + `Toast`.

**Ownership:** H (UI). **Dependencies:** `ThemeProvider`, `ErrorBoundary`, `Layout`,
`Toast`, `Modal`, store.

**Parent:** none (entry). **Children:** `ErrorBoundary → ThemeProvider → Layout`

**Props:** `{}` — none (reads URL/config only).

**Internal State:** none (store-backed).

**Zustand:** reads `status`, `theme`; dispatches `loadGraph` (mount effect), `setTheme`.

**Events:** outgoing — `loadGraph` on mount; routed `setTheme` from `Header`.
Incoming — none. Keyboard/mouse/animation: none at App scope.

**Lifecycle:**
- Mount: apply persisted/system theme; `loadGraph()` once.
- Update: re-render on `status`/`theme` change.
- Unmount: none (app-lifetime).

**Rendering Flow:** `ErrorBoundary(ThemeProvider(Layout))`; `Layout` shows `LoadingOverlay`
while first graph loads.

**Interaction Flow:** no direct user interaction; delegates via `Header`.

**Error Handling:** propagates fatal render errors to `ErrorBoundary`; graph-load error
reaches `Layout`'s error slot.

**Empty State:** n/a. **Loading State:** shell skeleton. **Disabled State:** n/a.

**Accessibility:** `role="main"` on the map region; theme toggle `aria-pressed`.

**Performance:** `React.memo` on the App/`Layout` boundary; children memoized internally.

**Styling:** UI §10 (layout), UI §17 (variables).

**Acceptance:**
- [ ] Continues only after successful single `loadGraph()`.
- [ ] Renders `Layout` inside `ThemeProvider` + `ErrorBoundary`.
- [ ] Fatal error → fallback UI, not a white screen.

**Unit tests:** boot triggers exactly one `loadGraph`; theme restore; boundary fallback.

**Future extension:** extend by adding providers; never enlarge `App`'s job.

---

## 1.2 Layout

**Purpose.** Chrome scaffold: header, map panel, sidebar, inspector/drawer, status bar.

**Responsibilities:** compose `Header`, `GraphCanvas` pane, `Sidebar`, drawer host,
`StatusBar`; apply responsive breakpoints (UI §11).

**Ownership:** UI. **Dependencies:** `Header`, `GraphCanvas`, `Sidebar`, `StatusBar`,
drawer host, store. **Parent:** `App`. **Children:** `Header`, `GraphCanvas`, `Sidebar`,
`StatusBar`, `ToastHost`.

**Props:** `{}` — derives layout from store.

**State:**

| variable | type | init | desc |
|---|---|---|---|
| `breakpoint` | `"desktop"\|"laptop"\|"tablet"\|"mobile"` | from width | grid mode |
| `drawerOpen` | boolean | false | inspector drawer (sub-1200) |

**Store:** reads `ui.panelOpen`; dispatches `setPanel`.

**Events:** window/resize → recompute breakpoint (debounced).

**Lifecycle:** mount `ResizeObserver`; update recompute; unmount dispose.

**Rendering Flow:** CSS grid — header / canvas (flex-1) / sidebar / optional drawer / status
bar, per breakpoint.

**Interaction Flow:** header buttons (theme, settings) route to store.

**Error/Loading/Empty/Disabled:** panels handle their own; Layout forwards container-level
overlay (`LoadingOverlay`).

**Accessibility:** landmarks `<header>`, `<main>`, `<aside>`, `<footer>`; consistent Tab order.

**Performance:** `React.memo`; breakpoint memoized; coarse re-render.

**Styling:** UI §10, §11.

**Acceptance:** correct layout at each breakpoint; drawer opens from header; status bar
present.

**Tests:** re-render per breakpoint; landmarks; drawer toggle.

---

## 1.3 GraphCanvas

**Purpose.** The map surface that renders graph + route + animation layers and owns
view navigation + selection.

**Responsibilities:** host `CanvasViewport` (+ `Legend`, `Tooltip`); forward selection to
store; surface empty/loading/error overlays.

**Ownership:** UI. **Dependencies:** `CanvasViewport`, `Legend`, `Tooltip`, `EmptyState`,
`ErrorBox`, store, `lib/coords`. **Parent:** `Layout`. **Children:** `CanvasViewport`,
`Legend`, `Tooltip`, overlays.

**Props:**

| name | type | req | default | description |
|---|---|---|---|---|
| `className?` | string | – | `""` | container class |
| `onSelectNode?` | `(id: string) => void` | – | – | external hook |

> Props are optional and non-essential; GraphCanvas is store-driven and reads the store
> directly (`IMPLEMENTATION_PLAN §D.1`). `onSelectNode`/`className` exist only as an escape
> hatch for future embedding/reuse.

**State:** none (delegates to `CanvasViewport`).

**Store:** reads `graph`, `frame`, `selection`, `status`; dispatches `selectNode`,
`setSelectedNode`.

**Events:**
- outgoing: `onSelectNode(id)`.
- mouse: wheel/pointer → zoom/pan (via viewport); click node → select; pointermove → hover.
- keyboard: arrows move selection; Esc clears.
- animation: frame-driven (`status` from `animation`).

**Lifecycle:** mount `CanvasViewport` sizing; unmount clear interaction listeners.

**Rendering Flow:** project once → `CanvasViewport` layers (static + route + anim) → draft
`Legend`/`Tooltip` overlays → handling `EmptyState`/`ErrorBox`/`LoadingOverlay`.

**Interaction Flow:** click → `selectNode` (store) → NodeMarker ring + ControlPanel bind;
wheel/pan → view transform; Fit → `fitBounds`.

**Error Handling:** no graph → `EmptyState`; `/graph` error → `ErrorBox` (Retry → `loadGraph`).

**Empty:** `EmptyState`. **Loading:** skeleton canvas. **Disabled:** interactions off when
`graph==null` or `status!==Ready/Playing/Paused`.

**Accessibility:** `role="img"` + `aria-label`; keyboard list fallback; selected `aria-selected`.

**Performance:** memoized layers; O(1) hit maps; frame only changes the anim layer (UI §20).

**Styling:** UI §9.1, §12.

**Acceptance:**
- [ ] 31 nodes / 70 edges painted ≤ 200 ms.
- [ ] onClick starts selection; zoom clamped 0.5–4; pan bounded.
- [ ] Empty/loading/error overlays render.
- [ ] Keyboard node list reachable.

**Unit tests:** initial render; selection event; overlay states; memoized layers; zoom bounds.

**Future:** render larger graphs by swapping only the dynamic layer to Canvas-2D behind the
same data model (UI §20).

---

## 1.4 CanvasViewport

**Purpose.** Projection + transform + the static layers; owns pan/zoom state.

**Responsibilities:** project `[lon,lat]` → view (`lib/coords.ts`); render `EdgeLayer`,
`NodeMarker` set, `RouteOverlay`; maintain `transform`; expose `fitBounds`.

**Ownership:** UI. **Dependencies:** `EdgeLayer`, `NodeMarker`, `RouteOverlay`,
`lib/coords.ts`, `lib/format.ts`. **Parent:** `GraphCanvas`. **Children:** `EdgeLayer`,
`NodeMarker`×N, `RouteOverlay`.

**Props:**

| name | type | req | default | description |
|---|---|---|---|---|
| `nodes` | `DeliveryNode[]` | yes | – | graph nodes |
| `edges` | `DeliveryEdge[]` | yes | – | edges |
| `routePoints` | `Array<[number,number]>` | no | `[]` | expanded route `[lon,lat]` |
| `frame` | `Frame?` | no | null | current animation frame |
| `selectionId` | `string?` | no | null | selected node |
| `width`/`height` | number | yes | – | (via resolver) |

**State:** `transform {x,y,scale}`; `viewBox`; `projected` (cached).

**Store:** reads `graph` slice, `frame`, `selection`; rarely writes.

**Events:** wheel (zoom, anchored), pointer pan, dblclick → fit, resize (resolver).

**Lifecycle:** mount sizes + initial `fitBounds`; update recompose projection when the graph
set changes; unsubscribe on unmount.

**Rendering Flow:** `useMemo` projection map → render edges → nodes (markers) → route →
anim overlay; memoized static groups.

**Interaction Flow:** pointer drag pans, wheel zooms around pointer, Fit restores.

**Error Handling:** none (delegated by parent).

**Accessibility:** mirror `GraphCanvas`; optional node list fallback.

**Performance:** memo static layers; `useCallback` handlers; transform-only pan/zoom; O(1)
lookup in `used`.

**Styling:** UI §13.

**Acceptance:** corrected projection within viewable bbox; pan/zoom within range; 60 fps; a11y
list.

**Tests:** projection of known coords; clamp logic; layer memo.

---

## 1.5 EdgeLayer

**Purpose.** Render graph edges as polylines (with hover emphasis).

**State:** none (projected input).

**Props:**

| Name | Type | Req | Default | Description |
|---|---|---|---|---|
| `edges` | `EdgeViewPoint[]` | yes | – | projected polylines |
| `hoverKey` | `string?` | no | null | edge to highlight |

**Store:** none.

**Events:** hover → forwarded to viewport.

**Accessibility:** whole layer `aria-hidden` (alt = text fallback).

**Performance:** `React.memo`; no re-render on frame change.

**Styling:** UI §12.1 edge token.

**Empty/Error/Loading/Disabled:** none (parent handles).

**Acceptance:** 70 edge paths rendered; hover thickens exactly one.

**Tests:** renders `edges.length`; hover applies class; memoized.

---

## 1.6 NodeMarker

**Purpose.** One POI marker: kind glyph + state ring.

**Responsibilities:** compute marker style from `state`; emit select/hover.

**Props:**

| Name | Type | Req | Default | Description |
|---|---|---|---|---|
| `node` | `DeliveryNode` | yes | – | data (`id`, `name`, `kind`) |
| `x`,`y` | number | yes | – | view coords |
| `state` | marker state enum | yes | `idle` | styling state |
| `onSelect` | `(id)=>void` | no | – | click handler |

**State:** none.

**Store:** reads `ui.hoveredNode` (to bias). **Events:**

- outgoing: `onSelect(id)`.
- mouse: `onMouseEnter`/`onMouseLeave` → `setHoveredNode`.
- keyboard: Enter/Space selects when focused.

**View/Kind:** marker shows kind glyph (UI §12), suppressed by state.

**Accessibility:** `aria-label` `<name>`; focusable; `aria-selected`.

**Styling:** UI §12.

**Performance:** memoized per state; uses precomputed coords.

**Acceptance:** reflects state ring/glyph; focus/click work; no reprojection.

**Tests:** renders ring per state; click emits; keyboard selects.

---

## 1.7 RouteOverlay

**Purpose.** Draw the final route: polyline + halo + marching ants.

**Responsibilities:** map `geometry` to polyline; animate path on route reveal; reduced-motion
static.

**Props:**

| Name | Type | Req | Default | Description |
|---|---|---|---|---|
| `geometry` | `Array<[number,number]>` | yes | – | expanded route |
| `animate` | boolean | no | true | ants |

**State:** none (CSS-driven).

**Store:** none.

**Events:** none.

**Accessibility:** `aria-hidden`.

**Performance:** `React.memo`; rerender on geometry change only.

**Styling:** UI §12.3, §13.

**Acceptance:** polyline order matches geometry; halo; reduced-motion static.

**Tests:** render order; animation flag toggles class.

---

## 1.8 Legend

**Purpose:** show the color key for nodes/edges/route/states.

**Responsibilities:** list semantic tokens matching the map; toggle collapse.

**Props:** `{}`.

**State:** `open` (ui.hideWeights).

**Store:** none (may read `ui` for persistence).

**Events:** nothing.

**Accessibility:** ordered `<ul>`; `aria-expanded`; labels with text not color only.

**Acceptance:** lists start/goal/current/frontier/visited/edge/route; toggle.

---

# 2. Control & panels

## 2.1 Sidebar

**Purpose:** vertical navigation + panel host. **Responsibilities:** switch/show panels.
**Ownership:** UI. **Dependencies:** panel list. **Parent:** `Layout`.
**Children:** `ControlPanel`, `StepTimeline`, `MetricsPanel`, `HistoryPanel`.

**Props:** `{}`. **State:** `activePanel` (persistence via store).

**Store:** reads `ui.panelOpen` (then active panel); writes `setPanel`.

**Events:** `onActivate(panelId)`; keyboard arrows/Enter.

**Rendering Flow:** segmented ribbon → renders active panel content.

**Empty/disabled:** panel handles itself; empty nav shows `EmptyState`.

**Accessibility:** `<nav>` with `aria-current`; buttons `aria-selected`.

**Acceptance:** navigable; highlights active; drawer below 768.

---

## 2.2 ControlPanel

**Purpose:** choose start, goal, algorithm, then run.

**Responsibilities:** host two `NodeSelector` + `AlgorithmSelector`; gate & dispatch Run.

**State:**

| variable | init | desc |
|---|---|---|
| `validateMsg?` | null | inline validation text |


**Store:** reads `search` (start, goal, algorithm, busy). Writes:
`setStart`, `setGoal`, `setAlgorithm`, `runSearch`.

**Events outgoing:** none directly (invokes store action `runSearch`).
**Outgoing Events:** submit button click.

**Validation:** Run disabled unless `start && goal && !busy`.

**Error:** inline message if `start===goal` or missing; shake hint (UI §9.3).

**Disabled:** while `status !== Ready`.

**Accessibility:** `fieldset`+`legend` grouping; `aria-required`; `aria-disabled` on Run.

**Acceptance:**
- [ ] Run disabled logic correct.
- [ ] Dispatches `runSearch` with selection.
- [ ] Inline validation on invalid.

**Performance:** rerender only on relevant slices.

**Extension:** future: intermediates (add `NodeSelector` rows).

---

## 2.3 AlgorithmSelector

**Purpose:** choose from `catalog` with mock distinction.

**Responsibilities:** render options from a catalog; tag mock providers.

**Props:**

| Name | Type | Req | Default | Description |
|---|---|---|---|---|
| `catalog` | `CatalogEntry[]` | yes | – | from `client.listAlgorithms()` |
| `value` | string | yes | – | selected |
| `disabled` | boolean | no | false | |
| `onChange` | `(name:string)=>void` | no | – | |

**State:** `open`, `highlight` index.

**Store:** none (controlled); caller → `setAlgorithm`.

**Events:** `onSelect(name)`; keyboard arrows/Enter/Esc.

**Data:** `catalog` entries `{name, label, mock:boolean}` (mock ⇒ show `(mock)` tag).

**Accessibility:** `combobox`/`listbox` roles; `aria-expanded`; mock tag `text-`.

**Acceptance:** lists BFS; mock tag; keyboard; no‑op on unknown.

**Performance:** memo rows.

---

## 2.4 NodeSelector (start/goal picker)

**Purpose:** select a start/goal node by search or map click.

**Props:**

| Name | Type | Req | Default | Description |
|---|---|---|---|---|
| `label` | string | yes | – | e.g. "Start Location" |
| `value` | string? | yes | null | chosen id |
| `options` | `{id,name}[]` | yes | [] | node list |
| `onChange` | `(id)=>void` | no | – | |

**State:** `query`, `focusedIndex`, `open`.

**Store:** none (controlled); parent maps to `setStart`/`setGoal`.

**Events:** `onChange(id)`; clear; filter keys; Esc closes.

**Accessibility:** combobox + `aria-activedescendant`; live filter.

**Validation:** parent rejects `goal===start`; this component just reports.

**Acceptance:** typeahead filters; select closes; clear; disabled.

---

## 2.5 MetricsPanel

**Purpose/rendering:** numeric outcome.

**Store access:** `selectMetrics(search.result)`, `animation.status`.

**Data (from `result`):** `total_distance_km`, `total_time_min`, `total_cost`,
`processing_time_ms`, plus derived `hops`, `nodesVisited`.

**Rendering:** `<dl>` of label/value/unit (UI §9.5) with `tabular-nums`.

**Empty:** when no result → `EmptyState` "Run a search to see metrics".

**Loading:** dim/retain previous while running.

**Accessibility:** `dl`; each numeral tabular.

**Acceptance:** shows the four + two derived; units correct; empty state.

**Performance:** memo; recompute via `useMemo(selectMetrics, [result])`.

---

## 2.6 HistoryPanel

**Purpose:** list past runs and replay.

**Store access:** `history.runs`, `replayRun`.

**Render:** rows with `algorithm`, `start→goal`, time, `source` badge.

**Actions:** onClick → `replayRun(id)`.

**Empty:** `EmptyState` "No searches yet". **Loading:** skeleton.

**Accessibility:** `list` + `aria-current` on active row; replay `aria-label`.

**Performance:** memo row list; lazy-import panel.

**Acceptance:** rows; replay; empty; mock tag; no network on replay.

---

## 2.7 StepTimeline

**Purpose:** scrub the animation.

**Responsibilities:** slider + current index `n / total` + reason caption; delegate playback to
`TimelineControls`.

**Store access:** `selectSteps`, `activeIndex`, `status`; `setStatus`, `setActiveIndex`; or
`stepTo`.

**State:**

| var | init | desc |
|---|---|---|
| `hoverIx` | – | hover track position |


**Rendering:** track + fill + thumb (UI §9.7); counter; caption `reason`.

**Disabled:** when no steps or `Idle/Error`.

**Keyboard:** arrows scrub; Home/End jump.

**Accessibility:** slider role, `aria-valuetext`, focus lock when disabled.

**Performance:** bind to store; `useMemo` handle positions.

---

## 2.8 TimelineControls

**Purpose:** playback control cluster (play/pause/step/restart).

**Store access:** `animation`; `play`, `pause`, `stepTo`, `restart`.

**Disabled rules:**
- `stepTo(+n)` disabled at `Finished`/end.
- `play` disabled at `Finished` (or `idle`).
- `reset` disabled while `Idle`.

**Accessibility:** `aria-label` (Play/Pause dynamic), `aria-pressed` , disabled states.

**Performance:** memo on `status`.

---

## 2.9 AnimationEngine (controller)

Not a visual component; the **pure controller** in `services/animation.ts`.

**Model (`Frame`):** `{ current_node, frontier, reason, visited, index }`.

**Responsibilities**
- Pure reducer: `next(frame, steps)`, `isDone(activeIndex, len)`, `frameAt(activeIndex)`.
- Playback scheduler: rAF/interval beats, auto‑pause on hidden tab (`GUI_ROADMAP §9`).
- Speed scaling; reduced‑motion keeps functional timing but drops pulse CSS.

**Store access:** reads `animation`, writes `setStatus`, `setActiveIndex`.

**Events:** tick → store `advance()`; jump from timeline `stepTo`.

**Performance:** `useRef` + `useEffect` for the scheduler; never re‑create per frame; O(1).

**Acceptance (unit):** monotonic; ends at last exactly, stays at last; replay independent of
name (no `AlgorithmName` string).

---

## 2.10 StatusBar

**Purpose:** single live state line + `(mock)` marker.

**Store:** `status`, `source`.

**Rendering:** dot + short text per state (UI §9.9).

**Accessibility:** `role="status"`, `aria-live="polite"`.

**States table:**

| Status | dot | text |
|---|---|---|
| Idle/Loading | muted/spinner | `Loading…` |
| Ready | success | `Ready` |
| Paused/Playing | primary → dot | `Playing` / `Paused` |
| Finished | success | `Finished` |
| Error | danger | `Error — retry` |
| Replay | warning | `Replay of <run>` + `(mock)` when mock |

**Acceptance:** correct per state; mock indicator; live.

---

## 2.11 SearchSummary

**Purpose:** a compact summary line of the outcome ("best path", cost, time) on `Finished`.

**Store:** `selectMetrics`, `result.explanation`.

**Rendering:** headline + inline metrics (UI §9).

**Empty:** none if not `Finished`.

**Accessibility:** `p` with `aria-live` when the result changes.

---

## 2.12 SearchDescription

**Purpose:** show `explanation` (Vietnamese), including any `(mô phỏng)` content (mock path).

**Store:** `result.explanation`.

**Rendering:** plain text paragraph; strikethrough nothing; respecting `- mô phỏng…` marker.

**Empty:** hidden when no result. **Long:** line-clamp when `ui.collapsed`.

**Accessibility:** standard text.

---

## 2.13 Toast

**Purpose:** transient notification; en masse via `ui.toasts`.

**Props:**

| Name | Type | Req | Default | Description |
|---|---|---|---|---|
| `toast` | `{id, kind, title, message?, action?}` | yes | – | one notice |
| `onDismiss` | `(id)=>void` | no | – | |

**State:** `exiting`.

**Store:** `dismissToast`.

**Timer:** auto-dismiss: success 3s, others 4s; close button always.

**Accessibility:** `role="status"` for success/info; `role="alert"` for danger/warning.

**Performance:** `React.memo`; exit transition; reduce on motion.

---

## 2.14 LoadingOverlay

**Purpose:** cover a pane while blocked.

**Props:**

| Name | Type | Req | Default | Description |
|---|---|---|---|---|
| `show` | boolean | yes | – | visibility |
| `label?` | string | no | `Loading…` | text |

**Store:** `status` (derive show) optional.

**Accessibility:** `role="progressbar"`, `aria-valuetext`.

**Reduced motion:** shimmer disabled.

---

## 2.15 ErrorBoundary

**Purpose:** catch render/child errors gracefully.

**Props:** `{children, fallback?}`.

**State:** `hasError`, `message`.

**Accessibility:** `role="alert"`.

**Behavior:** on error, log + render fallback (or retry). **Unit:** alternate throw test.

---

## 2.16 EmptyState

**Purpose:** describe an empty/inactive region.

**Props:**

| Name | Type | Req | Default | Description |
|---|---|---|---|---|
| `title` | string | yes | – | message |
| `subtitle?` | string | no | – | hint |
| `icon?` | RN | no | – | visual |
| `action?` | `{label, onClick}` | no | – | CTA |

**Accessibility:** `role="status"`; if static decorative, `presentation` + `aria-label`.

---

## 2.17 Tooltip

**Purpose:** micro‑detail.

**Props:**

| Name | Type | Req | Default | Description |
|---|---|---|---|---|
| `text` | string | yes | – | |
| `position?` | `top\|bottom\|left\|right` | no | `top` | |
| `delay?` | number | no | 100 | ms |

**Store:** none. **Accessibility:** `aria-describedby`; Esc dismiss; reduced-motion fade‑only.

---

## 2.18 Modal

**Purpose:** focus‑trapped dialog.

**Props:**

| Name | Type | Req | Default | Description |
|---|---|---|---|---|
| `open` | boolean | yes | – | |
| `title` | string | yes | – | |
| `onClose` | ()=>void | yes | – | |
| `children` | RN | yes | – | |
| `width?` | string | no | auto | |

**Lifecycle:** focus trap; Esc; scrim click close; restore focus.

**Accessibility:** `role="dialog"`, `aria-modal`, `aria-labelledby`; `role="presentation"` trap.

**Reduced motion:** fade only.

---

## 2.19 Spinner

**Purpose.** Indeterminate progress indicator.

**Responsibilities:** render a bounded spinning ring for blocking operations; honour reduced
motion (static ring).

**Ownership:** shared. **Dependencies:** none. **Parent:** any (used by `Button`, overlays,
`NodeMarker` inner). **Children:** none.

**Props:**

| name | type | req | default | description |
|---|---|---|---|---|
| `size?` | `'sm'\|'md'\|'lg'` | – | `'md'` | ring diameter |

**Internal State:** none.

**Zustand:** none.

**Events:** none.

**Lifecycle:** none.

**Rendering Flow:** render a `div` with `role` handled by consumer.

**Accessibility:** no implicit role; consumers add `aria-label`/`aria-busy`; reduced motion
pauses the spin (UI §13).

**Styling:** UI §9.10 (Spinner), UI §13.4.

**Acceptance:** renders ring; `size` variants; reduced-motion static.

**Unit tests:** size class; reduced-motion class when the media query matches.

**Future:** no change needed; extend via token.

---

## 2.20 SettingsPanel (future)

**Purpose:** preferences (theme, playback speed, language, storage).

**Ownership:** UI. **Not part of v1.** Design + tests locked in UI §16; wires into `ui.modal`
when built. Extend without touching panels.

---

## 2.21 ThemeProvider

**Purpose:** set `data-theme` on `<html>` + persist.

**Props:** `{children, storageKey?}`.

**State:** `theme`.

**Effect:** apply; persyst; read OS default first load.

**Accessibility:** doesn't disallow user override; respects `prefers-color-scheme`.

**Performance:** reads/writes minimal.

---

# 3. COMPONENT TREE

```
<App/>
└─ <ErrorBoundary>
   └─ <ThemeProvider>
      └─ <Layout>
         ├─ <Header>                      (brand, source badge, theme toggle, settings)
         ├─ <GraphCanvas>
         │   ├─ <CanvasViewport>
         │   │   ├─ <EdgeLayer>×1         (static)
         │   │   ├─ <NodeMarker>×N        (per-state POI)
         │   │   └─ <RouteOverlay>        (route + halo + ants)
         │   ├─ <Legend />
         │   ├─ <Tooltip />               (map hover)
         │   ├─ <LoadingOverlay />
         │   └─ <EmptyState>/<ErrorBox>   (conditionally)
         ├─ <Sidebar>
         │   ├─ <ControlPanel>
         │   │   ├─ <NodeSelector label="Start" />
         │   │   ├─ <NodeSelector label="Goal" />
         │   │   └─ <AlgorithmSelector />
         │   ├─ <StepTimeline>└─ <TimelineControls />
         │   ├─ <MetricsPanel>
         │   │   ├─ <SearchSummary />
         │   │   └─ <SearchDescription />
         │   └─ <HistoryPanel>
         ├─ <StatusBar />
         ├─ <Toast />          (host)
         └─ <Modal />          (host)
Shared (used anywhere): EmptyState, Spinner, Tooltip, Modal, Toast, ErrorBoundary, ThemeProvider.
```

# 4. EVENT FLOW

```
User
  ↓  (click node / select start+goal / pick algorithm / press Play / hover / keyboard)
Component      (ControlPanel, NodeSelector, AlgorithmSelector, GraphCanvas, StepTimeline,
                TimelineControls, NodeMarker)
  ↓  (dispatch action)
Store (Zustand)  action → validate → (async) → api
  ↓  http
API    (client.ts → GET /graph · POST /search · POST /history…)
  ↓  JSON (MAP_CONTRACT shapes)
Store  (status Loading → Ready; store graph/search/result; seed frames)
  ↓  reactive slices
 GraphCanvas (nodes/edges/route/frame)  ·  MetricsPanel  ·  HistoryPanel
  ↓  playback beat per frame
AnimationEngine (pure reducer) → advance() → Store frame → GraphCanvas anim layer + StepTimeline
  ↓ replay
HistoryPanel → replayRun(run) → hydrate same slices (no network)
```

# 5. STATE FLOW

```
graph      loadGraph()  → GET /graph → { geojsonNodes, geojsonEdges, bbox } → canvas
search     setAlgorithm/setStart/setGoal → validate → runSearch() → POST /search → result/source
animation  (derived from `search.result`): frames + activeIndex + status → StepTimeline/anim
history    runs[] recorded on each search; replayRun() re-hydrates `search` + `animation`
ui         selection (selectedNode), hoverStep, panelOpen, modal, toasts, theme, route
```
`metrics` is derived from `search.result` (never stored separately).

# 6. DATA FLOW

```
API payloads            client.ts types (snake_case, MAP_CONTRACT)
 ├─ DeliveryGraph        → graph slice > selectors > CanvasViewport (NodeMarker/EdgeLayer)
 ├─ SearchResult         → search slice → MetricSelector → MetricsPanel / SearchSummary / SearchDescription
 ├─ ExpandedRoute        → ui.route → RouteOverlay
 └─ (history replay)     → search slice (no transport)
  │
  ▼
 serialization (none to change fields; projections in lib/coords)
  ▼
 store slices (single store)
  ▼
 components via narrow selectors (memoized derivations)
 ```

# 7. COMPONENT DEPENDENCY GRAPH (transitive)

```
App → Layout → {Header, GraphCanvas, Sidebar, StatusBar, Toast·Modal hosts}
GraphCanvas → CanvasViewport → {EdgeLayer, NodeMarker N, RouteOverlay}
GraphCanvas → {Legend, Tooltip, EmptyState, ErrorBox, LoadingOverlay}
Sidebar → {ControlPanel, StepTimeline, MetricsPanel, HistoryPanel}
ControlPanel → {NodeSelector ×2, AlgorithmSelector}
MetricsPanel → {SearchSummary, SearchDescription}
StepTimeline → TimelineControls
Shared → {Spinner, EmptyState, ErrorBox, StatusDot, Tooltip, Modal, Toast, Badge, Button}
Navigation: no component imports `algorithms.*`; only `client` + store.
```

# 8. FILE OWNERSHIP

| Path | Owns |
|---|---|
| `ui/web/src/App.tsx` | App |
| `ui/web/src/components/AppFrame/Layout.tsx` | Layout, Header, drawer host |
| `ui/web/src/components/GraphCanvas/` | GraphCanvas, CanvasViewport, EdgeLayer, NodeMarker, RouteOverlay, Legend |
| `ui/web/src/components/Sidebar/` | Sidebar |
| `ui/web/src/components/ControlPanel/` | ControlPanel, NodeSelector, AlgorithmSelector |
| `ui/web/src/components/StepTimeline/` | StepTimeline, TimelineControls |
| `ui/web/src/components/MetricsPanel/` | MetricsPanel, SearchSummary, SearchDescription |
| `ui/web/src/components/HistoryPanel/` | HistoryPanel |
| `ui/web/src/components/StatusBar/` | StatusBar |
| `ui/web/src/components/shared/` | Toast, LoadingOverlay, ErrorBoundary, Modal, Spinner, Tooltip, EmptyState, ThemeProvider, StatusDot, Button |
| `ui/web/src/services/animation.ts` | AnimationEngine (pure) |
| `ui/web/src/lib/` | coords.ts, format.ts, icons.tsx, storage.ts, selector snacks |
| `ui/web/src/styles/theme.css` | tokens (UI §17) |

# 9. IMPLEMENTATION ORDER (→ IMPLEMENTATION_PLAN.md)

| Order | Component | Task (plan) |
|---|---|---|
| 1 | App, Layout, ThemeProvider, LoadingOverlay | 1.3 (shell+store) |
| 2 | GraphCanvas, CanvasViewport, EdgeLayer, NodeMarker, Legend, Tooltip, EmptyState, ErrorBox | 1.4 |
| 3 | client /search, ControlPanel, NodeSelector, AlgorithmSelector | 2.1 / 2.3 |
| 4 | AnimationEngine + unit tests | 2.4 |
| 5 | StepTimeline, TimelineControls | 2.5 |
| 6 | MetricsPanel, SearchSummary, SearchDescription, HistoryPanel | 2.6 |
| 7 | StatusBar mock tag, StatusBar complete | 3.3 / 2.x |
| 8 | SearchSummary/Description polish, SettingsPanel placeholder | 4.4 |

Each row keeps `pytest` + `ruff` + `npm test` + `npm run build` green.

# 10. DEFINITION OF DONE

| Component | DoD |
|---|---|
| App | mounts; single `loadGraph`; boundary; theme |
| Layout | 3 breakpoints; drawer; landmarks |
| GraphCanvas/Viewport | 31/70 ≤200 ms; zoom/pan/select; empty/loading/error; memo layers |
| NodeMarker | state styling; focusable; click emits |
| EdgeLayer | renders N edges; hover; memo |
| RouteOverlay | polyline + halo; reduced‑motion static |
| Legend | color key list; collapse |
| ControlPanel | run gates; inline validation; dispatches action |
| NodeSelector | filter/select/clear/disabled |
| AlgorithmSelector | catalog + mock tag + change |
| StepTimeline | slider + counter; disabled; no‑steps |
| TimelineControls | play/pause/step; boundary rules |
| AnimationEngine | pure reducer tests; monotonic; end; replay; no‑name |
| MetricsPanel | fields + units; empty |
| HistoryPanel | rows; replay; empty; mock badge |
| StatusBar | 8 states; `(mock)`; aria-live |
| Summary/Description | text render; empty |
| Toast/Modal/LoadingOverlay/Boundary/EmptySpace/Tooltip/Spinner | tested; a11y; reduced‑motion |
| ThemeProvider | toggle+persist+system; no flash |

**Global:** `pytest` green (no Python), `ruff`, `npm test`, `npm run build`; visual parity to
`UI_DESIGN_SYSTEM`; no dead styles; no algorithm-name branching.

---

_Read with `UI_DESIGN_SYSTEM.md` (§3/§9/§12/§13), `IMPLEMENTATION_PLAN.md` (§B/§D), `GUI_ROADMAP.md` (§4/§8/§9), `MAP_CONTRACT.md`._