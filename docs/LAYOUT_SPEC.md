# LAYOUT_SPEC.md

Version: 1.0

Status: Frozen Layout Specification

Owner: GUI Team

---

# 1. Purpose

This document defines the spatial organization of the Delivery AI Search application.

It specifies:

- page regions
- panel responsibilities
- sizing
- layout hierarchy
- resizing behavior
- responsive behavior

This document complements:

- UI_POLISH_SPEC.md
- DESIGN_TOKENS.md
- COMPONENT_SPEC.md

No business logic is defined here.

---

# 2. Design Goals

The layout should prioritize:

1. Visualization
2. Search workflow
3. Search information
4. Playback
5. History

Users should always understand:

- what they are searching
- where the search is running
- what the algorithm is currently doing

without visual clutter.

---

# 3. Layout Overview

Desktop layout consists of five regions.

```

┌──────────────────────────────────────────────────────────────────────────────┐
│ Header │
├──────────────┬───────────────────────────────┬───────────────────────────────┤
│ │ │ │
│ │ │ │
│ Left Sidebar │ Visualization │ Right Panel │
│ │ │ │
│ │ │ │
├──────────────┴───────────────────────────────┴───────────────────────────────┤
│ Playback Timeline │
└──────────────────────────────────────────────────────────────────────────────┘

```

Visualization must remain the dominant area.

---

# 4. Layout Priority

Visual importance:

1. Visualization

2. Search Controls

3. Metrics

4. Playback

5. History

The visualization area must never feel secondary.

---

# 5. Header

Purpose

Global application controls.

Contains

Application title

Backend status

Connection status

Current renderer

Theme switch (optional)

Version badge

Height

64–72 px

Header must remain fixed.

Do not place search controls here.

---

# 6. Left Sidebar

Purpose

Configure searches.

Contains

Search section

Algorithm section

Execution section

Optional advanced settings

Do NOT place

Metrics

History

Timeline

Sidebar width

Preferred

360 px

Minimum

320 px

Maximum

420 px

The sidebar should scroll independently if content overflows.

---

# 7. Sidebar Sections

Organize controls into clearly separated groups.

Example

Search

- Start Location
- Destination

Algorithm

- Choose Algorithm

Execution

- Run Search
- Cancel

Optional

Advanced

Every group should have:

title

divider

consistent spacing

---

# 8. Visualization Area

This is the primary workspace.

Minimum width

60%

Preferred

70%

Maximum

Remaining available width.

The visualization should always dominate the screen.

---

# 9. Visualization Modes

Two renderers are supported.

Graph View

Current graph visualization.

Street Map View

Leaflet

OpenStreetMap

The renderer is selected using a segmented control.

Changing renderer must NOT:

restart search

reset playback

change SearchResult

Only rendering changes.

---

# 10. Renderer Toggle

Located above the visualization.

Example

Graph | Street Map

Behavior

Switch renderer instantly.

Preserve:

camera

selection

playback

active search

where possible.

---

# 11. Graph View

Displays

Nodes

Edges

Visited nodes

Current node

Final path

Frontier

Selection

No geographical tiles.

---

# 12. Street Map View

Displays

OpenStreetMap tiles

Markers

Expanded route

Animated path

Search overlay

No duplicated application state.

Both renderers consume identical SearchResult.

---

# 13. Right Information Panel

Purpose

Display search information.

Contains

Status

Metrics

Current step

Explanation

Algorithm information

Optional history preview

Do NOT place search controls here.

Preferred width

360 px

Minimum

320 px

Maximum

420 px

---

# 14. Metrics Section

Located near the top.

Always visible after search completion.

Uses compact cards.

Never uses tables.

---

# 15. Status Section

Located above metrics.

Displays

Idle

Loading

Running

Finished

Replay

Error

Should always remain visible.

---

# 16. Playback Timeline

Located at the bottom.

Spans full width.

Contains

Play

Pause

Restart

Previous

Next

Speed

Timeline slider

Current step

Step counter

Playback status

Height

96–120 px

Should remain fixed.

---

# 17. History

History is located inside the right panel.

Never inside the left sidebar.

History is a supporting feature.

It must never dominate the interface.

---

# 18. Resizing Rules

Panels resize independently.

Visualization receives remaining space.

Never shrink the visualization below 60%.

Sidebar widths remain fixed whenever possible.

---

# 19. Responsive Behavior

Desktop

≥1440 px

Three-column layout.

Laptop

1024–1439 px

Three-column layout.

Right panel may become narrower.

Tablet

768–1023 px

Sidebar collapses into drawer.

Timeline remains bottom docked.

Mobile

Not required.

---

# 20. Scroll Behavior

Header

Fixed

Timeline

Fixed

Sidebar

Scrollable

Right panel

Scrollable

Visualization

Independent pan and zoom

Avoid nested scrolling whenever possible.

---

# 21. Empty States

Visualization

Explain how to start a search.

Metrics

Explain that no search has completed.

History

Explain that no searches have been recorded.

Avoid blank white panels.

---

# 22. Loading States

Loading should preserve layout.

Use skeleton placeholders.

Never collapse sections during loading.

---

# 23. Layer Hierarchy

Graph View

Edges

↓

Visited

↓

Path

↓

Nodes

↓

Selected Node

↓

Tooltip

Street Map View

Tiles

↓

Road Overlay

↓

Visited

↓

Path

↓

Markers

↓

Tooltip

---

# 24. Focus Management

Keyboard navigation order

Header

↓

Sidebar

↓

Visualization

↓

Right Panel

↓

Timeline

Focus must always remain visible.

---

# 25. Performance Rules

Static layers

Edges

Map tiles

Roads

must not rerender unnecessarily.

Animated layers

Current node

Frontier

Visited

Path

may rerender independently.

Separate static rendering from animated rendering.

---

# 26. Future Expansion

The layout must support future additions without redesign.

Examples

Additional algorithms

Traffic overlays

Heatmaps

Multiple route comparison

Performance charts

These additions should occupy existing extension regions rather than creating new layout structures.

---

# 27. Layout Constraints

The following are prohibited.

Floating control panels

Overlapping sidebars

Hidden playback controls

Fullscreen modal workflows

Search dialogs

The primary workflow must remain visible at all times.

---

# 28. Academic Presentation

The layout should be suitable for:

AI demonstrations

Research visualization

University project defense

Algorithm comparison

The interface should resemble a visualization tool rather than a business dashboard.

---

# 29. Acceptance Criteria

A successful implementation satisfies all of the following.

✓ Visualization occupies the largest region.

✓ Search controls are grouped logically.

✓ Metrics are isolated from controls.

✓ Timeline remains docked.

✓ Graph and Street Map share the same layout.

✓ Responsive behavior preserves usability.

✓ No functionality changes.

✓ Existing APIs remain unchanged.

✓ Existing tests continue to pass.

✓ Layout supports future algorithm additions.