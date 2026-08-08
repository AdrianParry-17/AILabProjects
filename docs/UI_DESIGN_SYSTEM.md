# UI_DESIGN_SYSTEM.md

**HCMC Delivery AI Search — Single Source of Truth for the GUI appearance**

Version: 1.0

Owner: Hưng (UI design + frontend)

Scope: the **entire visual language and frontend design system** for the React GUI. This
document is authoritative for *appearance only* — colors, typography, spacing, layout,
components, motion, accessibility, states, and file organization for styling.

**Compatibility contract**
- Fully compatible with `GUI_ROADMAP.md v2.0` (architecture, `§11` API contracts, `§14`
  React conventions, `§15` testing, `§16` phases), `IMPLEMENTATION_PLAN.md` (tasks, `§A`
  design tokens, `§B` React architecture, `§C` GraphCanvas, `§D` component specs),
  `ARCHITECTURE.md`, `MAP_CONTRACT.md` (payload shapes, field names, node `kind`, `[lon,
  lat]` coords), and the repo naming conventions in `GUI_ROADMAP §14`.
- This document does **not** change architecture, API contracts, implementation phases,
  ownership, or the folder structure of the application logic. It only organizes **styling**
  and **visual** concerns.
- Where an older doc made a *visual* suggestion, this document is authoritative and wins.
  Where this document must reference architecture/API, it defers to the source docs.

**Frontend stack (declared):** React · Vite · TypeScript · TailwindCSS · Zustand · SVG.

---

## 0. Styling strategy (Tailwind + roadmap compatibility)

> `GUI_ROADMAP §14` requires *"CSS Modules by default; theme variables in
> `styles/theme.css`"*. `IMPLEMENTATION_PLAN §A` already defines the design-token names and
> hex values. This section reconciles those with the declared TailwindCSS stack **without
> changing either document** — it adds the mechanics on top.

| Concern | Mechanism |
|---|---|
| Design tokens (colors, space, radius, shadows, type) | **One source: CSS variables in `ui/web/src/styles/theme.css`** (roadmap-compatible). Never duplicate a value. |
| Utility classes (layout, spacing, type) | Tailwind utilities mapped to the CSS variables via `tailwind.config.ts` (`colors: { primary: "var(--c-primary)" }` …). |
| Component-scoped / stateful styles | CSS Modules per component folder (`GraphCanvas/styles.css`), per roadmap `§14`. Modules import tokens via `var(--c-*)`. |
| Arbitrary ad-hoc styling | Forbidden. Any value not expressible by a token requires a token first. |

Rules:
1. A color/size appears in exactly one place: the token file.
2. Tailwind config maps token names to `var(--c-*)`; utilities are the default way to apply
   tokens in JSX.
3. Complex stateful styles (animation layers, drag, timeline) live in CSS Modules that read
   the same variables.
4. No hex/rgb values inside `*.tsx` or component styles. Ever.

---

## 1. Design Philosophy

**Design goals**
- Look like a **modern professional software product** (Linear, Vercel Dashboard, GitHub,
  Mapbox Studio, Figma, Notion references) — not a university assignment.
- Make the algorithm *visible*: the map, the search animation, and the metrics are the
  product. UI chrome is quiet and stays out of the way.
- Minimal, elegant, clean, modern, highly readable, animation-friendly.
- Zero dead-ends: every state (empty, loading, error, mock) is designed, not an accident.

**User experience goals**
- A user can go from *load* → *select* → *run* → *watch* → *inspect* → *replay* in seconds
  without reading a manual.
- The current algorithmic state (which node is current, what is in the frontier, the route)
  is always legible at a glance.
- Mock runs (`(mock)`) are visually distinguished but still fully usable.

**Visual identity**
- Light, airy surfaces; a crisp hairline border system; one teal primary; one amber accent
  reserved for the running route. Rounded but restrained (8 px). Typography is a tight
  system sans with tabular numerals for data.
- Identity words: *calm, precise, technical, trustworthy, human.*

**Interaction philosophy**
- **Direct manipulation on the map** is primary (click nodes, drag to pan, wheel to zoom).
- Immediate, continuous feedback (hover states, live status bar) for every action.
- Motion explains state transitions; it never decorates for its own sake.
- Progressive disclosure: advanced detail (replay, history, raw metrics) unfolds on demand.

---

## 2. Design Principles

1. **Consistency** — one token system, one component set, one motion language. Nothing is
   bespoke per panel. New UI is assembled from the primitives in this document.
2. **Hierarchy** — one primary action per surface; the map is dominant, panels secondary,
   chrome tertiary. Size, weight, color, and spacing encode rank.
3. **Minimalism** — show only what the current task needs; progressive disclosure for the
   rest. Visual noise (gradients, excessive borders, icon clutter) is prohibited.
4. **Predictability** — same controls behave the same everywhere; standard hover/active/
   focus semantics; Run is always where it was; the status bar always reflects reality.
5. **Accessibility** — WCAG AA contrast, full keyboard operation, visible focus, reduced
   motion respected, never color-only meaning (see §14).
6. **Motion** — short, purposeful, transform/opacity only; respects
   `prefers-reduced-motion`; each animation answers *what changed?* (see §13).
7. **Visual feedback** — every actionable element responds within 100 ms: hover, press,
   disabled, loading, error, success.
8. **Progressive disclosure** — the sidebar shows essentials; replay/history/metrics detail
   is one click away; tooltips deliver micro-detail on hover/focus.
9. **Error prevention** — Run stays disabled until a valid configuration exists; invalid
   inputs are prevented up front and explained inline when they do occur.

---

## 3. Color System

> Token names match `IMPLEMENTATION_PLAN §A.2`. Hex values are identical for shared tokens;
   additional tokens extend (never replace) that palette. All tokens are CSS variables.

### 3.1 Core tokens

| Token | Tailwind class | HEX | Usage |
|---|---|---|---|
| `--c-bg` | `bg-bg` | `#F7F9FB` | app background, canvas plate |
| `--c-surface` | `bg-surface` | `#FFFFFF` | panels, cards, dialogs |
| `--c-surface-2` | `bg-surface-2` | `#EEF3F5` | wells, inset wells, hover tiles |
| `--c-surface-3` | `bg-surface-3` | `#E7EDF1` | pressed wells, timeline track |
| `--c-border` | `border-border` | `#DFE5EA` | hairline borders, dividers |
| `--c-border-strong` | `border-border-strong` | `#C8D1DA` | focus-adjacent borders, active tabs |
| `--c-text` | `text-text` | `#17202A` | primary text |
| `--c-text-secondary` | `text-text-secondary` | `#5B6B7B` | secondary, captions |
| `--c-text-muted` | `text-text-muted` | `#8C99A6` | placeholders, disabled-adjacent |
| `--c-text-inverse` | `text-text-inverse` | `#FFFFFF` | text on primary/dark fills |

### 3.2 Brand & accent

| Token | Tailwind class | HEX | Usage |
|---|---|---|---|
| `--c-primary` | `bg-primary` `text-primary` `border-primary` | `#0E7768` | primary actions, active nav, selected pill, links |
| `--c-primary-hover` | `bg-primary-hover` | `#0A5F53` | primary hover/pressed |
| `--c-primary-soft` | `bg-primary-soft` | `rgba(14,119,104,0.10)` | selected backgrounds, soft tags |
| `--c-primary-soft-strong` | `bg-primary-soft-strong` | `rgba(14,119,104,0.16)` | selected rows on hover |
| `--c-accent` | `bg-accent` `text-accent` `stroke-accent` | `#F07A1D` | **the running route path**, key highlights |
| `--c-accent-soft` | `bg-accent-soft` | `rgba(240,122,29,0.14)` | route halo, accent chips |
| `--c-selected` | `bg-selected` `ring-selected` | `#15859C` | selected node/step ring (map & timeline) |
| `--c-selected-soft` | `bg-selected-soft` | `rgba(21,133,156,0.14)` | selected node halo |

### 3.3 Semantic

| Token | Tailwind class | HEX | Usage |
|---|---|---|---|
| `--c-success` | `text-success` `bg-success` | `#2E7D32` | `Ready`, `Finished`, success toasts |
| `--c-success-bg` | `bg-success-bg` | `#EAF4EC` | success banner/toast background |
| `--c-success-hover` | `bg-success-hover` | `#27632B` | success action hover |
| `--c-warning` | `text-warning` `bg-warning` | `#B26A00` | `(mock)` tag, `Replay`, warnings |
| `--c-warning-bg` | `bg-warning-bg` | `#FBF3E2` | warning banner background |
| `--c-warning-hover` | `bg-warning-hover` | `#8F5300` | warning action hover |
| `--c-danger` | `text-danger` `bg-danger` | `#C62828` | `Error`, destructive, invalid fields |
| `--c-danger-bg` | `bg-danger-bg` | `#FBEAEA` | error banner/inline background |
| `--c-danger-hover` | `bg-danger-hover` | `#A11F1F` | destructive hover |
| `--c-info` | `text-info` `bg-info` | `#2563EB` | informational, network status |
| `--c-info-bg` | `bg-info-bg` | `#EAF1FE` | info banner background |
| `--c-info-hover` | `bg-info-hover` | `#1D4ED8` | info action hover |

### 3.4 Graph / animation tokens

| Token | Tailwind class | HEX | Usage |
|---|---|---|---|
| `--c-edge` | `stroke-edge` | `#B9C4CE` | default graph edge |
| `--c-edge-hover` | `stroke-edge-hover` | `#94A5B3` | edge under pointer |
| `--c-node-base` | `fill-node-base` | `#FFFFFF` | unselected POI fill |
| `--c-node-stroke` | `stroke-node-stroke` | `#8C99A6` | unselected POI outline |
| `--c-start` | `fill-start` `text-start` | `#0E7768` | **start node** (solid teal, flag) |
| `--c-goal` | `fill-goal` `text-goal` | `#4338CA` | **goal node** (solid indigo, target) |
| `--c-current` | `stroke-current-node` | `#0E7768` | current-node ring during animation |
| `--c-frontier` | `fill-frontier` `text-frontier` | `#7C4DFF` | frontier markers |
| `--c-frontier-soft` | `bg-frontier-soft` | `rgba(124,77,255,0.16)` | frontier halo |
| `--c-visited` | `fill-visited` | `#AEBAC4` | visited-tint fill |
| `--c-visited-soft` | `fill-visited-soft` | `rgba(174,186,196,0.5)` | visited-tint stroke |
| `--c-route` | `stroke-route` | `#F07A1D` | final route polyline (alias of accent) |
| `--c-route-halo` | `stroke-route-halo` | `rgba(240,122,29,0.25)` | route outer halo for contrast |

> Start uses the primary teal and goal uses **indigo**, not red, so the goal never collides
> with danger red or with the amber route. Frontier is **violet**. These four (teal, indigo,
> violet, amber) are mutually distinct and differ under deuteranopia/protanopia (shapes
> reinforce color; see §12.2).

### 3.5 State tokens

| Token | Tailwind class | HEX | Usage |
|---|---|---|---|
| `--c-disabled` | `text-disabled` | `#9AA6B1` | disabled text/icon |
| `--c-disabled-bg` | `bg-disabled-bg` | `#E6EBEF` | disabled control fill |
| `--c-disabled-border` | `border-disabled-border` | `#D8E0E6` | disabled border |
| `--c-focus-ring` | (via `focus-visible`) | `rgba(14,119,102,0.28)` | keyboard focus ring (matches `--shadow-focus`) |
| `--c-overlay` | `bg-overlay` | `rgba(15,23,32,0.45)` | modal/drawer scrim |

### 3.6 Dark mode compatibility

Light is the default. Dark is a **complementary palette activated by `[data-theme="dark"]`**
on `<html>` (no backend involvement, no API change).

| Light var | Dark value | Note |
|---|---|---|
| `--c-bg` | `#0E141A` | deep neutral, not pure black |
| `--c-surface` | `#161D24` | panels |
| `--c-surface-2` | `#1E2730` | wells |
| `--c-surface-3` | `#27323D` | pressed wells |
| `--c-border` | `#2A3642` | hairline |
| `--c-border-strong` | `#3B4A58` | active borders |
| `--c-text` | `#EDF1F5` | primary text |
| `--c-text-secondary` | `#A7B3BF` | secondary |
| `--c-text-muted` | `#7C8A97` | muted |
| `--c-primary` | `#3FC7B2` | lifted for dark contrast |
| `--c-primary-hover` | `#2FB39F` | |
| `--c-accent` | `#FF9A3C` | route on dark map |
| `--c-frontier` | `#A78BFA` | lifted violet |
| `--c-goal` | `#8B7CFA` | lifted indigo |
| `--c-visited` | `#48576A` | visited tint on dark |
| `--c-edge` | `#3E4C5A` | edges on dark |
| `--c-edge-hover` | `#5A6C7D` | |

All semantic hover/bg pairs follow the same pattern (bg tint = 12% alpha of the color).
Rules: never rely on theme to convey meaning; both themes must meet WCAG AA for the same
surfaces; new tokens are added to both palettes in the same commit.

---

## 4. Typography

**Font family**
- UI: `Inter, -apple-system, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif`.
- Mono/data: `"JetBrains Mono", ui-monospace, "SF Mono", "Cascadia Code", Consolas,
  monospace` — reserved for ids, coordinates, and code-ish readouts.
- Fonts are system-adjacent + optional local `@font-face`; no large webfont payload.

**Scale & usage**

| Token | Size | Weight | Line-height | Letter-spacing | Usage |
|---|---|---|---|---|---|
| `--fs-2xl` | 32 px | 700 | 1.2 | -0.02em | app brand, dialogs title |
| `--fs-xl` | 20 px | 600 | 1.3 | -0.01em | panel/section titles |
| `--fs-lg` | 16 px | 600 | 1.35 | 0 | card titles, key metric value |
| `--fs-md` | 14 px | 500 | 1.4 | 0 | emphasized body, buttons |
| `--fs-sm` | 13 px | 400 | 1.45 | 0 | default body, table text |
| `--fs-xs` | 11 px | 500 | 1.4 | +0.04em | captions, labels, tags, status |

**Rules**
- Headings: `--fs-xl` section titles are the largest UI text; the brand is `--fs-2xl`.
  Headings use `600/700`, no all-caps except micro-labels (letterspaced `--fs-xs`, uppercase).
- Body: `--fs-sm` default; `--fs-md` for primary actions/buttons; never below 13 px for
  interactive text, never below 11 px for any text.
- Numbers & metrics: `font-variant-numeric: tabular-nums` everywhere data is aligned
  (metrics panel, timeline counters, tables). Locale via `Intl`; Vietnamese units as text.
- Code/ids: mono at `--fs-xs`/`--fs-sm` on `--c-surface-2` chip background.
- Line-length: panels wrap at ~68ch; the explanation/message text never exceeds ~72ch.
- Hierarchy is *weight + size + color*; do not stack three differing weights in one row.

---

## 5. Spacing System

- **Base:** 4 px. Tokens: `--space-1=4`, `-2=8`, `-3=12`, `-4=16`, `-5=24`, `-6=32`,
  `-7=48`, `-8=64`.
- **Tailwind:** `p-1..p-8`, `m-1..m-8`, `gap-1..8` map to these tokens. No fractional steps
  (6/10/14 px are forbidden) except where a line-height requires it.

| Context | Value |
|---|---|
| App gutters (padding around canvas + panels) | `--space-4` (16) |
| Panel padding | `--space-4` (16) |
| Stacked panel gap (sidebar) | `--space-3` (12) |
| Control group gap | `--space-2` (8) |
| Sidebar ↔ canvas | `--space-4` (16) |
| Card padding | `--space-4` |
| Toolbar gap | `--space-2`/`--space-3` |
| Dialog padding | `--space-5` (24) |
| Table cell padding (vertical/horizontal) | `--space-2` / `--space-3` |
| Icon-to-label gap | `--space-2` (8) |
| Section title → content | `--space-3` (12) |

**Layout grid** — a 12-column CSS grid for the responsive layout (see §10); internal panel
grids use 8 px gutters on the 4 px scale.

---

## 6. Border Radius

| Token | Tailwind | Value | Usage |
|---|---|---|---|
| `--radius-sm` | `rounded-sm` | 3 px | badges, tags, chips, small indicators |
| `--radius-md` | `rounded-md` | 8 px | inputs, buttons, cards, panels, toasts |
| `--radius-lg` | `rounded-lg` | 12 px | dialogs, dropdown menus, popovers |
| `--radius-xl` | `rounded-xl` | 16 px | drawers, bottom sheets |
| `--radius-full` | `rounded-full` | 999 px | pills, toolbar icon buttons, status dots |

Rules: buttons/tags use `--radius-md`; icon buttons `--radius-md`; map overlays/tooltips
`--radius-md`; the timeline slider thumb `--radius-full`. Never mix `lg` with `full` in the
same control.

---

## 7. Shadow System

| Token | Value | Used by |
|---|---|---|
| `--shadow-1` | `0 1px 2px rgb(0 0 0 / .06)` | resting cards, panels |
| `--shadow-2` | `0 8px 24px -8px rgb(0 0 0 / .18)` | floating panels, dropdowns, popovers |
| `--shadow-tooltip` | `0 4px 12px -2px rgb(0 0 0 / .20)` | tooltips |
| `--shadow-modal` | `0 24px 64px -16px rgb(0 0 0 / .30)` | dialogs, drawers |
| `--shadow-focus` | `0 0 0 3px var(--c-focus-ring)` | keyboard focus ring (all controls) |

Rules: elevation is *border + faint shadow*, never glow. Hover states change border/background,
**not** shadow (except popover-open). Dark mode: shadow opacities rise to `.20/.35/.45`.

---

## 8. Icon System

**Choice: Lucide** (`lucide-react`, stroke-based, 24 grid, MIT, tree-shakeable) wrapped by a
thin local facade `ui/web/src/lib/icons.tsx`.

**Why Lucide**
- Stroke-consistent (1.5–2 px), modern, matches Linear/Vercel/Dashboard aesthetics.
- Tree-shakeable (bundle stays small), first-class React, no runtime CDN.
- Semantic aliases can be re-mapped in one file later without touching components.

**Usage rules**
- Default size 16 px in panels, 20 px in toolbars, 24 px in empty states.
- Icons are decorative: `aria-hidden`; semantic meaning via text/`aria-label`.
- Never recolor via hex in JSX; use `text-*`/`stroke-*` tokens.

| Purpose | Icon |
|---|---|
| Algorithm / search | `Search`, `Route`, `Workflow`, `GitBranch` |
| Run search | `Play`, `Zap` (fast) |
| Playback | `Play`, `Pause`, `StepForward`, `StepBack`, `RotateCcw` (reset) |
| History | `History`, `Clock`, `Repeat` |
| Metrics | `Gauge`, `Ruler`, `Timer`, `Coins`, `ListChecks` |
| Graph / map | `Map`, `MapPin`, `Network`, `LocateFixed` |
| Settings | `Settings`, `SlidersHorizontal` |
| Errors / warnings | `AlertCircle`, `AlertTriangle`, `XCircle` |
| Success / info | `CheckCircle2`, `Info` |
| Status / misc | `Circle` (status dot), `Tag` (mock tag), `ChevronLeft/Right/Down`, `Plus/Minus` (zoom), `Maximize2` (fit) |

---

## 9. Component Style Guide

> One folder per feature (`GUI_ROADMAP §14`): `components/<Name>/index.tsx`,
> `<Name>/styles.css`, `<Name>/<Name>.test.tsx`. All components below use the tokens above.

### 9.1 GraphCanvas (map surface)
- **Purpose:** render the delivery graph, route, and animation layers.
- **Layout:** full-bleed inside `MapPane`; owns its SVG viewport; toolbar overlay top-right
  (zoom in/out/fit) as `--radius-md` pill buttons on `--c-surface` with `--shadow-2`.
- **Typography:** node labels `--fs-xs`; tooltip body `--fs-sm`.
- **Colors:** §12 (nodes/edges/route/animation). Canvas plate `--c-bg`; optional grid line
  `--c-border` at 5% alpha.
- **Hover/Focus/Disabled:** see §12.6. Node hotspots focusable (keyboard list fallback).

### 9.2 Sidebar
- **Purpose:** composition root for the control + inspection panels.
- **Layout:** width 300 px (desktop), column stack, `--space-3` gutters, scrollable.
- **Colors:** `--c-surface`; border-right `--c-border` hairline.
- **Empty:** panels render their own empty states (§15).

### 9.3 ControlPanel
- **Purpose:** start/goal/algorithm selection + Run.
- **Layout:** stacked groups: two `NodePicker` fields, `AlgorithmSelector`, Run button (full
  width, `--space-2` above).
- **Typography:** field labels `--fs-xs` uppercase letterspaced; values `--fs-sm`.
- **Colors:** fields `--c-surface` with `--c-border`; focus `--c-primary` border + focus ring.
- **Hover:** field border → `--c-border-strong`.
- **Disabled:** Run disabled = `--c-disabled-bg` + `--c-disabled` text until start & goal set.

### 9.4 AlgorithmSelector
- **Purpose:** pick an algorithm from the catalog.
- **Layout:** dropdown (`--radius-md`), list items with icon + label + `(mock)` tag.
- **Colors:** trigger `--c-surface`; active item row `--c-primary-soft` + `--c-text`; mock tag
  `--c-warning` pill on `--c-warning-bg`.
- **Focus:** item rows keyboard-navigable with `--shadow-focus` ring.

### 9.5 MetricsPanel
- **Purpose:** show `total_distance_km`, `total_time_min`, `total_cost`, `processing_time_ms`
  + explanation.
- **Layout:** two-column definition list; each metric = label (`--fs-xs`, muted) over value
  (`--fs-lg`, 600, tabular-nums).
- **Colors:** values `--c-text`; unit suffix `--c-text-muted`.
- **Empty:** empty state "Run a search to see metrics".

### 9.6 HistoryPanel
- **Purpose:** list past runs; click to replay.
- **Layout:** table-like rows: algorithm icon + name, start→goal, time ago, source tag.
- **Colors:** row hover `--c-surface-2`; mock rows show `(mock)` tag (`--c-warning`).
- **Empty:** "No searches yet."

### 9.7 StepTimeline
- **Purpose:** scrub through animation steps.
- **Layout:** a horizontal slider (track `--radius-full`, fill `--c-primary`), step counter
  `n / total` (`--fs-xs`, tabular), reason caption line (`--fs-sm`).
- **Colors:** track `--c-surface-3`; thumb `--c-primary` with `--c-surface` border; reached
  portion `--c-primary`; unreached `--c-border-strong`.
- **Hover:** thumb grows 4→6 px. **Disabled:** during `Loading`/`Idle`.

### 9.8 AnimationControls
- **Purpose:** play / pause / step-forward / step-back / reset.
- **Layout:** icon-button cluster (`--radius-full` or `--radius-md`), 36 px targets.
- **Colors:** idle `--c-text-secondary` on `--c-surface-2`; hover `--c-primary`; playing state
  swaps Play→Pause (primary fill, white icon).
- **Disabled:** at start/end boundaries buttons disabled per §13.5.

### 9.9 StatusBar
- **Purpose:** single live line of truth (`Idle/Loading/Ready/Playing/Paused/Finished/Error/
  Replay`) + `(mock)` marker.
- **Layout:** full-width bar, 40 px tall, left status dot + text, right optional action
  (Retry on Error).
- **Colors:** per state — dot uses success/warning/info/danger tokens; text `--c-text-secondary`.
- **aria:** `aria-live="polite"` (see §14).

### 9.10 Buttons
- Variants: `primary` (`--c-primary` → hover `--c-primary-hover`, white text), `secondary`
  (`--c-surface` + `--c-border`), `ghost` (transparent), `danger` (`--c-danger` → hover
  `--c-danger-hover`), `danger-ghost`.
- Sizes: `sm` 28 px / `md` 36 px / `lg` 44 px tall; horizontal padding `--space-3`/`--space-4`.
- All: `--radius-md`, 500 weight, `:active` scale 0.98, focus ring `--shadow-focus`.
- Disabled: `--c-disabled-bg` + `--c-disabled` text, cursor not-allowed.

### 9.11 Inputs / Selects / NodePicker
- Height 36 px, `--radius-md`, `--c-surface`, 1 px `--c-border`, padding `--space-3`; labels
  above (`--fs-xs`, letterspaced, `--c-text-secondary`).
- Focus: 1 px `--c-primary` border + `--shadow-focus`. Placeholder `--c-text-muted`.
- Error: 1 px `--c-danger` border + `--c-danger` label. Disabled: `--c-disabled-bg`.

### 9.12 Dropdowns (menus, selectors)
- Trigger = input/select style. Menu: `--c-surface`, `--shadow-2`, `--radius-lg`, 1 px
  `--c-border`, items 36 px tall, hover `--c-surface-2`, active `--c-primary-soft`.

### 9.13 Cards
- `--c-surface`, 1 px `--c-border`, `--radius-md`, padding `--space-4`, `--shadow-1`.
- Title row: icon 16 px + `--fs-lg` 600; optional right-side action (ghost icon).

### 9.14 Tables
- Header row `--fs-xs` letterspaced uppercase, `--c-text-muted`, `--c-border` bottom.
- Cells `--fs-sm`, `--space-2`/`--space-3` padding, zebra off (use hover instead).
- Row hover `--c-surface-2`; numeric cells tabular-nums right-aligned.

### 9.15 Badges / tags
- `--radius-sm`, `--fs-xs` 500, padding `2px 6px`. Styles: `neutral` (surface-2/text-secondary),
  `success`, `warning` (mock tag), `info`, `danger`, `primary-soft`.

### 9.16 Dialogs / modals
- `--radius-lg`, `--c-surface`, `--shadow-modal`, max-width 480 px, padding `--space-5`;
  scrim `--c-overlay`; header `--fs-xl` 600; footer right-aligned actions.

### 9.17 Tooltips
- `--fs-sm`, `--c-surface` (or dark `#17202A` w/ inverse text on map), `--shadow-tooltip`,
  `--radius-md`, 4–6 px offset; appear ≤ 100 ms, dismiss on leave/Esc.

---

## 10. Layout System

### Desktop layout (≥ 1200 px)
```
┌──────────────────────────────────────────────────────────────┐
│ Header      brand · connection  · settings         36–48 px  │
├────────────────────────────┬───────────────┬────────────────┤
│                            │  Sidebar      │  Inspector     │
│      MapPane (flex 1)      │  300 px       │  (320 px,      │
│      GraphCanvas           │  ControlPanel │   bottom-drawer│
│      toolbar overlay       │  Timeline     │   on <1200)    │
│                            │  Metrics      │                │
│                            │  History      │                │
├────────────────────────────┴───────────────┴────────────────┤
│ StatusBar                                         40 px      │
└──────────────────────────────────────────────────────────────┘
```
- **Sidebar width:** 300 px fixed (`--space-?` not applicable; use `width: 300px`).
- **Canvas size:** flexible (flex 1), minimum 0 (no min-width), full height minus chrome.
- **Inspector:** 320 px on ≥ 1200; collapses to a bottom drawer (`--radius-xl`) below 1200.
- **Bottom timeline:** the StepTimeline + AnimationControls live in the sidebar top area and
  as a floating bottom sheet over the canvas during playback (position `absolute`, `--shadow-2`).
- **Min supported resolution:** 1280 × 800. Layout must be usable, not merely scrollable.
- **Max width:** content never exceeds 1920 px (centered plate with `--c-bg` margins).
- **Z-index scale:** canvas toolbar 10 · sidebar 20 · drawer 30 · modal scrim 40 · modal 50 ·
  toast 60 · tooltip 70.

---

## 11. Responsive Design

| Breakpoint | Tailwind | Behavior |
|---|---|---|
| `desktop` | `≥1200 px` | 3-column (§10) |
| `laptop` | `1024–1199 px` | 2-column: map + sidebar; inspector → drawer |
| `tablet` | `768–1023 px` | sidebar 280 px; timeline collapses to a floating bottom sheet |
| `mobile (future)` | `<768 px` | single column; canvas full-bleed; panels stack; toolbar docks bottom |

- Breakpoints: `sm 640 / md 768 / lg 1024 / xl 1200 / 2xl 1536`.
- Never hide workflow-critical controls; on small widths the timeline becomes a compact,
  always-visible bottom bar (44 px).
- Canvas keeps a pointer-friendly min zoom; text never shrinks below 11 px.

---

## 12. Graph Visualization Style

### 12.1 Static nodes & edges
- **Node size:** base radius 6 px (SVG view units); selected/current scale ×1.5; POI icons
  (glyph per kind) drawn inside a 20 px circle at default zoom.
- **Node fill:** `--c-node-base` (white) with `--c-node-stroke` 1.5 px outline. Unselected.
- **Node colors by kind** (POI glyphs, subtle hue only for *kinds*, never for state):

| Kind | Hue (fill) | Note |
|---|---|---|
| `delivery_market` | `#E8B4B8` | warm |
| `delivery_supermarket` | `#F4E2C8` | sand |
| `delivery_bus_station` | `#C9D9F2` | cool blue |
| `delivery_hospital` | `#F6D5E2` | rose |
| `delivery_university` | `#D8E6CE` | sage |
| `delivery_warehouse` | `#D5D0E6` | lavender |
| `delivery_airport` | `#CFE3DE` | mint |

  Kind color is *always* overridden by state color (§12.2). Road nodes (`intersection`,
  `gateway`, `bridge_access`) use `--c-node-stroke` without fill when road graph renders.
- **Edge:** `--c-edge` 1.5 px stroke, round caps; `--c-edge-hover` 2 px under pointer.
- **Route highlight:** `--c-route` 4 px stroke with a 7 px `--c-route-halo` underlay; animated
  marching-ants white dashes (2 px) on top (see §13.6).

### 12.2 State colors (authoritative, applied over everything)

| State | Fill | Stroke/Ring | Shape cue |
|---|---|---|---|
| Start | `--c-start` solid | white 2 px | flag glyph |
| Goal | `--c-goal` solid | white 2 px | target glyph |
| Current | `--c-node-base` | `--c-current` 3 px pulsing ring | ring expands |
| Frontier | `--c-frontier` | `--c-frontier-soft` halo | soft dot + pulse |
| Visited | `--c-visited-soft` | `--c-visited` | reduced alpha |
| Selected | `--c-node-base` | `--c-selected` 3 px ring | static ring |
| On final path | `--c-node-base` | `--c-route` ring | ring = route color |

Shape always accompanies color (flags, rings, halos) so no state depends on hue alone.

### 12.3 Animation layer (per frame)
- One frame = one `SearchStep` (`current_node`, `frontier`, `reason`) — consumed by
  `services/animation.ts`; UI never touches algorithm identity (`GUI_ROADMAP §9`).
- `current_node` → pulsing `--c-current` ring; `frontier` → `--c-frontier` dots with halos;
  visited nodes accumulate `--c-visited` tint; `path` (when completed) → route overlay.
- Layer order (bottom→top): edges → visited tint → nodes → frontier → route → current ring
  → tooltips (matches `IMPLEMENTATION_PLAN §C.2`).

### 12.4 Selection & hover
- Hover: node scales to 1.15 + `--c-border-strong` ring + tooltip (name, kind, id); edges
  thicken to 2.5 px and shift to `--c-edge-hover`.
- Selection: click sets `selected` (persistent ring `--c-selected`) and drives the
  NodePicker/start–goal wiring; `aria-selected` set on the SVG node group.

### 12.5 Zoom & pan
- Wheel (and pinch on touch) zooms 0.5–4 anchored at the pointer; drag (or Space+drag) pans,
  clamped to `fitBounds` + 4% margin; `Fit` button / double-click fits the graph.
- All transform-only (SVG `<g>` `transform`), never re-projecting per frame.

### 12.6 Canvas states
- **Empty:** bbox dashed skeleton + `EmptyState` overlay ("Choose start & goal, then Run").
- **Loading:** dashed bbox skeleton with shimmer + spinner.
- **Error:** `ErrorBox` overlay centered on the canvas.

---

## 13. Animation Guidelines

> Motion is functional. Default duration **180 ms**, `cubic-bezier(0.2, 0, 0, 1)`
> (ease-out-quart-like). On `prefers-reduced-motion: reduce` → **0 ms** everywhere.

| Animation | Duration | Easing | Notes |
|---|---|---|---|
| Hover (node/edge/control) | 120 ms | ease-out | transform/color only |
| Panel open/collapse | 200 ms | ease-out | transform + opacity |
| Drawer (inspector) | 220 ms | ease-out | translateY |
| Dropdown/popover | 160 ms | ease-out | opacity + translateY(4px) |
| Tooltip | 100 ms | ease-out | opacity only |
| Modal | 200 ms in / 160 ms out | ease-out | scale .98→1 + fade |
| StepTimeline transition | 180 ms | ease-out | thumb + fill width |
| Route reveal | 600 ms | linear | marching-ants dashoffset, one sweep |
| Current-node pulse | 900 ms loop | ease-in-out | ring radius + opacity loop |
| Frontier pulse | 900 ms loop | ease-in-out | dot + halo loop |
| Progress (metrics count-up) | 500 ms | ease-out | tabular number roll |
| Loading shimmer | 1.2 s loop | linear | monotone sweep on skeleton |

Rules:
- Only two looping animations exist (node pulse, loading shimmer) and they stop when the
  state ends; no infinite decorative motion.
- Animate only `transform` and `opacity` (plus `dashoffset` for the route); never `top/left/
  width` layout properties except the timeline fill.
- Playback cadence: 1 step per 600 ms default, adjustable 0.5×–4×; auto-pause when the tab
  is hidden (`GUI_ROADMAP §9`); one frame commit per beat; cancel `rAF` on pause.

---

## 14. Accessibility

- **Keyboard:** full tab order; arrows move node selection / scrub timeline; Enter/Space
  activate; Esc closes overlays/dropdowns; visible focus ring (`--shadow-focus`) everywhere.
- **Focus ring:** `:focus-visible` only; 3 px `var(--c-focus-ring)`; never `outline: none`
  without a replacement.
- **Contrast:** body ≥ 4.5:1; large text & UI chrome ≥ 3:1 (WCAG AA) in both themes.
- **ARIA:** landmarks (`<main>`, `<nav>`, `<aside>`); `StatusBar` `aria-live="polite"`;
  `(mock)` tag = text, not just color; icons `aria-hidden`; canvas exposes `role="img"`
  + a keyboard-reachable node list fallback; timeline is a slider with `aria-valuetext`.
- **Reduced motion:** all §13 animations collapse to 0 ms; the route reveals instantly.
- **Color-blind considerations:** state never relies on hue alone — rings/halos/shapes carry
  meaning (flags, targets, dots); the teal/indigo/violet/amber set is distinct under
  protanopia/deuteranopia; mock/success/error also emit text.
- **Touch:** targets ≥ 44×44 px; node hotspots ≥ 24 px hit area.

---

## 15. Loading / Empty / Error States

| State | Trigger | UI |
|---|---|---|
| Loading graph | `loadGraph()` running | canvas bbox skeleton + shimmer; StatusBar `Loading…`; controls disabled |
| Loading search | `POST /search` in flight | Run button spinner; StatusBar `Searching…`; panels show previous result dimmed |
| No history | empty `history.runs` | HistoryPanel `EmptyState` — "No searches yet" + hint icon |
| No graph | `/graph` 503 (`GRAPH_NOT_FOUND`, roadmap §7) | full-canvas `ErrorBox` with Retry (see next) |
| Invalid search | start==goal?/missing | inline field errors (`--c-danger` border + message); Run stays disabled |
| Search failed | API error envelope | `ErrorBox` (title + code + message + Retry); status `Error` |
| Timeout | `504 SEARCH_TIMEOUT` | `ErrorBox` "Search timed out" + Retry; Retry reuses last config |
| Network disconnected | fetch throws | banner (info/danger) "Connection lost — retrying…" + StatusBar `Error`; auto-retry with backoff up to 3 |

All use shared `ErrorBox`/`EmptyState` primitives (`IMPLEMENTATION_PLAN §D.9`); no panel
duplicates them.

---

## 16. Notification System

| Type | Style | Rules |
|---|---|---|
| **Toast** | top-right stack; `--c-surface`, `--shadow-2`, `--radius-md`, 44 px min; auto-dismiss 4 s (success 3 s); slide-in 200 ms | success/warning/info/danger variants with icon + `--fs-sm` text + optional action |
| **Banner** | top, under header; full width; colored bg (`--c-success-bg`/`--c-warning-bg`/`--c-danger-bg`/`--c-info-bg`) + 1 px left accent; dismissible | persistent states (connection lost, mock notice) |
| **Inline error** | under the offending field/panel; `--fs-sm`, `--c-danger` text on `--c-danger-bg` well | form/run errors, recovery guidance |
| **Status badge** | in StatusBar/rows; dot + `--fs-xs` label | `(mock)`, `real`, `Replay`, connection |

Rules: max 3 toasts; one banner at a time; toasts must not block the canvas toolbar; all
notifications are `role="status"`/`role="alert"` appropriate and keyboard-dismissible.

---

## 17. Theme Variables

### 17.1 CSS variables (`ui/web/src/styles/theme.css`)

```css
:root {
  /* color (core) */
  --c-bg: #F7F9FB;            --c-surface: #FFFFFF;      --c-surface-2: #EEF3F5;
  --c-surface-3: #E7EDF1;     --c-border: #DFE5EA;       --c-border-strong: #C8D1DA;
  --c-text: #17202A;          --c-text-secondary: #5B6B7B; --c-text-muted: #8C99A6;
  --c-text-inverse: #FFFFFF;
  /* color (brand) */
  --c-primary: #0E7768;       --c-primary-hover: #0A5F53;
  --c-primary-soft: rgba(14,119,104,0.10); --c-primary-soft-strong: rgba(14,119,104,0.16);
  --c-accent: #F07A1D;        --c-accent-soft: rgba(240,122,29,0.14);
  --c-selected: #15859C;      --c-selected-soft: rgba(21,133,156,0.14);
  /* color (semantic) */
  --c-success: #2E7D32;       --c-success-bg: #EAF4EC;    --c-success-hover: #27632B;
  --c-warning: #B26A00;       --c-warning-bg: #FBF3E2;    --c-warning-hover: #8F5300;
  --c-danger: #C62828;        --c-danger-bg: #FBEAEA;     --c-danger-hover: #A11F1F;
  --c-info: #2563EB;          --c-info-bg: #EAF1FE;       --c-info-hover: #1D4ED8;
  /* color (graph) */
  --c-edge: #B9C4CE;          --c-edge-hover: #94A5B3;
  --c-node-base: #FFFFFF;     --c-node-stroke: #8C99A6;
  --c-start: #0E7768;         --c-goal: #4338CA;
  --c-current: #0E7768;       --c-frontier: #7C4DFF;      --c-frontier-soft: rgba(124,77,255,0.16);
  --c-visited: #AEBAC4;       --c-visited-soft: rgba(174,186,196,0.5);
  --c-route: #F07A1D;         --c-route-halo: rgba(240,122,29,0.25);
  /* color (state) */
  --c-disabled: #9AA6B1;      --c-disabled-bg: #E6EBEF;   --c-disabled-border: #D8E0E6;
  --c-focus-ring: rgba(14,119,102,0.28); --c-overlay: rgba(15,23,32,0.45);

  /* typography */
  --font-sans: "Inter", -apple-system, "Segoe UI", Roboto, sans-serif;
  --font-mono: "JetBrains Mono", ui-monospace, Consolas, monospace;
  --fs-2xl: 32px; --fs-xl: 20px; --fs-lg: 16px; --fs-md: 14px; --fs-sm: 13px; --fs-xs: 11px;

  /* space (4px scale) */
  --space-1: 4px; --space-2: 8px; --space-3: 12px; --space-4: 16px;
  --space-5: 24px; --space-6: 32px; --space-7: 48px; --space-8: 64px;

  /* radius */
  --radius-sm: 3px; --radius-md: 8px; --radius-lg: 12px; --radius-xl: 16px; --radius-full: 999px;

  /* shadow */
  --shadow-1: 0 1px 2px rgb(0 0 0 / .06);
  --shadow-2: 0 8px 24px -8px rgb(0 0 0 / .18);
  --shadow-tooltip: 0 4px 12px -2px rgb(0 0 0 / .20);
  --shadow-modal: 0 24px 64px -16px rgb(0 0 0 / .30);
  --shadow-focus: 0 0 0 3px var(--c-focus-ring);

  /* motion */
  --dur-1: 120ms; --dur-2: 180ms; --dur-3: 220ms; --dur-4: 600ms;
  --ease-out: cubic-bezier(0.2, 0, 0, 1);
  --ease-loop: cubic-bezier(0.45, 0, 0.55, 1);
}
```

Dark overrides live in the same file under `[data-theme="dark"]` (see §3.6).

### 17.2 Tailwind tokens (`tailwind.config.ts`)

```ts
import type { Config } from "tailwindcss";
export default {
  darkMode: ["class", '[data-theme="dark"]'],
  theme: {
    extend: {
      colors: {
        bg: "var(--c-bg)", surface: "var(--c-surface)", "surface-2": "var(--c-surface-2)",
        "surface-3": "var(--c-surface-3)", border: "var(--c-border)",
        "border-strong": "var(--c-border-strong)",
        text: "var(--c-text)", "text-secondary": "var(--c-text-secondary)",
        "text-muted": "var(--c-text-muted)", "text-inverse": "var(--c-text-inverse)",
        primary: "var(--c-primary)", "primary-hover": "var(--c-primary-hover)",
        "primary-soft": "var(--c-primary-soft)", "primary-soft-strong": "var(--c-primary-soft-strong)",
        accent: "var(--c-accent)", "accent-soft": "var(--c-accent-soft)",
        selected: "var(--c-selected)", "selected-soft": "var(--c-selected-soft)",
        success: "var(--c-success)", "success-bg": "var(--c-success-bg)",
        warning: "var(--c-warning)", "warning-bg": "var(--c-warning-bg)",
        danger: "var(--c-danger)", "danger-bg": "var(--c-danger-bg)",
        info: "var(--c-info)", "info-bg": "var(--c-info-bg)",
        start: "var(--c-start)", goal: "var(--c-goal)",
        current: "var(--c-current)", frontier: "var(--c-frontier)",
        visited: "var(--c-visited)", route: "var(--c-route)",
        disabled: "var(--c-disabled)", "disabled-bg": "var(--c-disabled-bg)",
        overlay: "var(--c-overlay)",
      },
      fontFamily: { sans: "var(--font-sans)", mono: "var(--font-mono)" },
      fontSize: {
        "2xl": "var(--fs-2xl)", xl: "var(--fs-xl)", lg: "var(--fs-lg)",
        md: "var(--fs-md)", sm: "var(--fs-sm)", xs: "var(--fs-xs)",
      },
      spacing: { 1: "var(--space-1)", 2: "var(--space-2)", 3: "var(--space-3)", 4: "var(--space-4)",
                 5: "var(--space-5)", 6: "var(--space-6)", 7: "var(--space-7)", 8: "var(--space-8)" },
      borderRadius: {
        sm: "var(--radius-sm)", md: "var(--radius-md)", lg: "var(--radius-lg)",
        xl: "var(--radius-xl)", full: "var(--radius-full)",
      },
      boxShadow: {
        "1": "var(--shadow-1)", "2": "var(--shadow-2)", tooltip: "var(--shadow-tooltip)",
        modal: "var(--shadow-modal)", focus: "var(--shadow-focus)",
      },
      transitionDuration: { 1: "var(--dur-1)", 2: "var(--dur-2)", 3: "var(--dur-3)", 4: "var(--dur-4)" },
    },
  },
} satisfies Config;
```

---

## 18. File Structure (styling organization)

> Extends `GUI_ROADMAP §4` and `IMPLEMENTATION_PLAN §B.2`; does not move application logic.

```
ui/web/src/
├─ styles/
│  ├─ theme.css           # THE single token file (§17.1) — all CSS variables + dark overrides
│  ├─ base.css            # reset, base element styles, focus-visible global ring
│  └─ utilities.css       # non-Tailwind helpers (tabular-nums, scrollbars, reduced-motion)
├─ lib/
│  ├─ icons.tsx           # Lucide facade (one mapping file, §8)
│  └─ coords.ts / format.ts / filter.ts   # logic (owned per IMPLEMENTATION_PLAN §B.2)
├─ assets/                # images, favicon, logo SVGs (no CSS)
└─ components/
   ├─ shared/
   │   ├─ Button/  Select/  NodePicker/  ErrorBox/  EmptyState/  Spinner/  Tooltip/
   │   ├─ StatusDot/  Toast/  Banner/  Modal/
   │   └─ styles.css per feature folder
   ├─ GraphCanvas/  (index.tsx, styles.css, <Name>.test.tsx)
   ├─ Sidebar/  ControlPanel/  AlgorithmSelector/  StepTimeline/
   ├─ MetricsPanel/  HistoryPanel/  StatusBar/  AnimationControls/
   └─ ...one folder per component, each with its own styles.css (CSS Modules)
```

**Rules**
- `styles/theme.css` is the only file that may declare tokens; `base.css` the only file with
  global element selectors.
- Component styles live **next to the component** in its folder (`styles.css`, CSS Modules),
  per roadmap `§14`.
- `lib/icons.tsx` is the only place components may import icons from.

---

## 19. Naming Conventions

| Thing | Convention | Example |
|---|---|---|
| Component folders | PascalCase | `GraphCanvas/`, `ControlPanel/` |
| Component files | `index.tsx` + `<Name>.tsx` tests | `GraphCanvas/index.tsx`, `GraphCanvas/GraphCanvas.test.tsx` |
| Component functions | PascalCase | `export function GraphCanvas()` |
| Hooks | `use` + camelCase | `useGraphCanvas`, `useRunSearch` |
| Store actions | `verbObject` camelCase | `runSearch`, `advanceStep`, `loadGraph` |
| Selectors | `select` + camelCase | `selectVisibleNodes`, `selectFrameAt` |
| CSS Module class | `block__element--modifier` (BEM-lite) | `timeline__track--active` |
| Tailwind classes | utilities only; token-based | `bg-surface`, `text-text-secondary`, `rounded-md` |
| CSS variables | `--c-*` color, `--fs-*` type, `--space-*` spacing, `--radius-*`, `--shadow-*`, `--dur-*` | `--c-primary`, `--fs-sm`, `--space-3` |
| Icons | PascalCase component names from Lucide | `Play`, `StepForward`, `AlertCircle` |
| JSON/API fields | snake_case (never touched by UI) | `total_distance_km`, `current_node` |
| Mock marker | literal `(mock)` (text, not only a color) | `(mock)` |

---

## 20. Performance Guidelines

- **Animation limits:** one looped pulse per state; max 2 simultaneous looping animations;
  all transition work on `transform/opacity`; playback targets ≥ 30 fps, ≤ 4 ms frame work
  (`GUI_ROADMAP` performance budgets).
- **DOM limits:** static SVG element count for 31 nodes / 70 edges ≈ 150 nodes; stay under
  1,500 DOM nodes per view; no scans — use `Map<id, …>` lookups (§12/C).
- **SVG rules:** memoize the static layer (nodes/edges/route); re-render only the animation
  layer per frame; `pointer-events` only on interactive groups; precompute coordinates once.
- **Canvas rules (future):** if a larger graph ever exceeds the SVG budget, move only the
  dynamic layer to Canvas-2D behind the same data model — never both for the same layer.
- **Re-render prevention:** narrow Zustand selectors; `React.memo` on leaf presentational
  components; `useMemo` for derived values; `useCallback` for callbacks to memoized children
  (`IMPLEMENTATION_PLAN §F`).
- **Lazy loading:** `HistoryPanel` (and heavy export helpers) via `React.lazy` + `Suspense`;
  core shell + GraphCanvas in the critical bundle; vendor chunk (react) long-cached.
- **Budgets (verify per phase):** first paint ≤ 200 ms; frame ≤ 4 ms; `GET /graph` ≤ 150 ms;
  `POST /search` p95 ≤ 300 ms (service-side).

---

## 21. Future Extensibility

- **New algorithms:** appear automatically via the `AlgorithmCatalog` — the selector renders
  the catalog, the tag `(mock)` reflects `source`. The design system adds **no** per-algorithm
  color/icon; the only identifier is the catalog label. Zero UI redesign.
- **New panels:** add a component folder under `components/`, a slice in the store, and a
  sidebar slot. It must consume only existing tokens/`shared` primitives.
- **New metrics:** come as new JSON fields (snake_case) on the serialization side; the
  MetricsPanel renders rows from a field map — adding a row is data-driven, no layout change.
- **New themes:** add a `[data-theme="…"]` override block in `styles/theme.css`; no component
  changes. Dark is the first instance of this mechanism.
- **Rules:** never hard-code a color/size/name in a component; never branch on an algorithm
  name in the UI (`GUI_ROADMAP §1`); any new visual element must first exist as a token.

---

## 22. Design Checklist (pre-merge)

Every UI component, before merging, must pass all of:

- [ ] Uses tokens only — no hex/rgb/px literals outside `theme.css`/`base.css`.
- [ ] Renders all four states explicitly: default, hover/focus, disabled, loading.
- [ ] Empty and error variants handled via shared `EmptyState`/`ErrorBox` (no local copies).
- [ ] Keyboard operable; visible `:focus-visible` ring; correct `aria-*` attributes.
- [ ] `prefers-reduced-motion` honored (no required motion).
- [ ] Color not the only signal; shapes/text accompany state (mock tag, goal/start).
- [ ] Contrast ≥ WCAG AA in both light and dark themes.
- [ ] Numeric values use tabular numerals; units/labels per §4.
- [ ] Spacing/radius/shadow from tokens; fits §10 layout and breakpoints.
- [ ] No infinite/looping decoration beyond the two permitted loops (§13).
- [ ] Component test present (`<Name>.test.tsx`) covering default + state renders.
- [ ] No new dependency for styling/iconing (Lucide facade or shared primitives only).

---

## 23. Definition of Done (UI-specific)

A UI change is done only when **all** of these hold:

- [ ] Matches `GUI_ROADMAP.md` architecture (`§4` folders, `§14` conventions) and
      `IMPLEMENTATION_PLAN.md` tasks — no architecture/API/phase/ownership changes.
- [ ] Consumes `MAP_CONTRACT.md` payloads as-is (snake_case fields; no renames).
- [ ] `styles/theme.css` is the only token source; Tailwind config in sync.
- [ ] `pytest` (backend suite) still green — the UI change touched no Python.
- [ ] `npm test` green (vitest) for the touched components; `npm run build` passes.
- [ ] Design checklist (§22) all boxes ticked.
- [ ] Manual pass on a real run (BFS real) and a mock run (`(mock)` tag visible,
      replay works, status bar correct) on ≥ 1280×800.
- [ ] Performance budgets met for touched surfaces (first paint, frame cost, bundle).
- [ ] No dead CSS / unused tokens introduced; tokens only added with both themes.

---

## 24. References

| Doc | Role for the UI |
|---|---|
| `docs/GUI_ROADMAP.md` | architecture, state machine, animation input, `§14`/`§15` conventions |
| `docs/IMPLEMENTATION_PLAN.md` | tasks/sessions, `§A` tokens, `§B` React arch, `§C` GraphCanvas, `§D` components |
| `docs/ARCHITECTURE.md` | dependency flow (UI is the top layer) |
| `docs/MAP_CONTRACT.md` | payload shapes, node `kind`, coordinate rules, edge cases |
| `docs/DELIVERY_GRAPH.md` | node kinds + invariants that drive `§12.1` |
| `CONVENTION.md` (referenced) | general repo conventions (UI naming per roadmap `§14`) |
