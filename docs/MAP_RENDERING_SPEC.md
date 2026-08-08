# MAP_RENDERING_SPEC.md

Version: 1.0

Status: Frozen UI Specification

Related Documents

- UI_POLISH_SPEC.md
- DESIGN_SYSTEM_V2.md
- LAYOUT_SPEC.md
- COMPONENT_POLISH_SPEC.md
- MOTION_SPEC.md
- GUI_ROADMAP.md
- MAP_CONTRACT.md

---

# 1. Goal

The map must become the visual center of the application.

Instead of looking like an SVG drawing,
the graph should appear as a real navigation map.

The graph visualization must remain accurate while becoming much easier to read.

This specification changes presentation only.

No backend contract changes.

No algorithm changes.

No SearchResult changes.

No SearchStep changes.

---

# 2. Rendering Modes

The application shall support two rendering modes.

## Mode A

Real Street Map

Uses:

OpenStreetMap
(MapLibre or Leaflet)

Shows

- roads
- buildings
- parks
- rivers
- labels

Graph overlays on top.

---

## Mode B

Graph Only

Shows

- nodes
- edges

No map tiles.

Useful for debugging.

---

A segmented control switches between them.

```
Map | Graph
```

Default:

Map

---

# 3. Map Library

Preferred

MapLibre GL JS

Alternative

Leaflet

Do NOT use Google Maps.

---

# 4. Camera

Initial camera

Automatically fit graph bounds.

Never zoom to world.

Padding

40 px

Maximum zoom

18

Minimum zoom

10

---

# 5. Interaction

Supported

✓ mouse wheel zoom

✓ drag

✓ double click zoom

✓ touch pinch

✓ keyboard

✓ Fit button

---

# 6. Controls

Top-right

Small floating controls

□ +

□ –

□ Fit

□ Locate Graph

Do NOT place controls inside sidebar.

---

# 7. Overlay Order

Lowest

Map Tiles

↓

Road Graph

↓

Animated Route

↓

Visited Nodes

↓

Current Node

↓

Selected Start/Goal

↓

Tooltips

Highest

Popup

---

# 8. Road Rendering

Road graph should look lightweight.

Width

2 px

Color

Gray 400

Opacity

55%

No heavy black lines.

---

# 9. Animated Path

Current solution

Bright blue

Width

5 px

Rounded caps

Rounded joins

Glow

Small outer glow

Animation

Draw progressively.

Never flash.

---

# 10. Visited Nodes

Small circles

Radius

5 px

Fill

Primary Blue

Opacity

35%

Visited nodes accumulate.

---

# 11. Current Node

Current animation node

Radius

8 px

White border

Blue fill

Soft pulse

Only one current node exists.

---

# 12. Start Node

Large marker.

Green.

Pin icon.

Persistent.

---

# 13. Goal Node

Large marker.

Red.

Pin icon.

Persistent.

---

# 14. Selected Node

Hovered

White halo

Selected

Blue outline

Keyboard focus

Dashed outline

---

# 15. Labels

Normal rendering

Hide labels.

Only show

hover

selection

search

Avoid clutter.

---

# 16. Tooltip

Hover

Shows

Name

Node ID

Type

Coordinates

Distance (optional)

Layout

Simple card

Shadow

Rounded

---

# 17. Popup

Click node

Popup

Large

Contains

Location Name

Node Type

Latitude

Longitude

Actions

Select as Start

Select as Goal

Center Here

---

# 18. Route Animation

Route drawing

Smooth.

Constant speed.

No teleport.

Node highlight

Synchronised with SearchStep.

---

# 19. SearchStep Synchronization

Every SearchStep updates

Visited nodes

↓

Current node

↓

Timeline

↓

StatusBar

↓

Metrics

Animation source

ONLY SearchStep

Never infer extra states.

---

# 20. Empty State

If no graph

Centered illustration

Title

No graph loaded

Subtitle

Load graph to begin.

Button

Reload

---

# 21. Error State

Graph load failed.

Map dims.

Error card appears centered.

Retry button.

---

# 22. Loading State

Skeleton map

Fade

Progress spinner

No flashing.

---

# 23. Node Selection Modes

Support two methods.

Method A

Click directly on map.

Method B

Dropdown search.

User can freely mix both.

---

# 24. Search

Search box

Autocomplete

Supports

Node ID

Location Name

Street

POI

Fuzzy search

Instant filtering

---

# 25. Minimap (Optional)

Future enhancement.

Not required now.

---

# 26. Performance

Target

60 FPS

Map interaction

Smooth.

Animation

Never blocks UI.

Graph rendering

Memoized.

Avoid rerendering static edges.

---

# 27. Accessibility

Keyboard navigation.

ARIA labels.

Visible focus.

Reduced motion.

High contrast compatible.

---

# 28. Responsive

Desktop

Map dominant.

Tablet

Sidebar collapsible.

Mobile

Full-screen map.

Bottom sheet controls.

---

# 29. Visual Quality Checklist

The interface should feel closer to

✓ Google Maps

✓ Mapbox Studio

✓ ArcGIS Dashboard

Not

✗ classroom SVG

✗ graph editor

✗ debugging canvas

---

# 30. Acceptance Criteria

The map shall

✓ render real OSM tiles

✓ overlay graph accurately

✓ animate SearchStep

✓ highlight visited nodes

✓ show current node

✓ display Start/Goal markers

✓ support click selection

✓ support dropdown selection

✓ support Fit

✓ support zoom

✓ support pan

✓ remain smooth

✓ preserve MAP_CONTRACT

✓ preserve backend APIs

✓ preserve SearchResult

✓ preserve SearchStep

✓ introduce no backend changes