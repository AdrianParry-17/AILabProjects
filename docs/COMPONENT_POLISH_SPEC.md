# COMPONENT_POLISH_SPEC.md

Version: 1.0

Status: Frozen Component Design Specification

Owner: GUI Team

Related Documents

- UI_POLISH_SPEC.md
- DESIGN_TOKENS.md
- LAYOUT_SPEC.md
- MAP_RENDERING_SPEC.md
- COMPONENT_SPEC.md
- GUI_ROADMAP.md

---

# 1. Purpose

This document defines the visual behavior and presentation rules for every UI component.

It specifies:

- appearance
- spacing
- layout
- interaction
- accessibility
- responsiveness

This document does NOT define:

- business logic
- API behavior
- application state
- backend contracts

Those remain defined by COMPONENT_SPEC.md and GUI_ROADMAP.md.

---

# 2. Global Component Rules

All components shall follow:

✓ rounded corners

✓ subtle elevation

✓ consistent spacing

✓ smooth animation

✓ keyboard accessibility

✓ responsive layout

✓ reusable styling

Every component should look like part of the same design system.

---

# 3. Header

Purpose

Global application information.

Contains

• Application logo

• Application title

• Backend connection status

• API version

• Theme switch (optional)

• Settings (future)

Height

64 px

Behavior

Always fixed.

Never scroll.

Background

White.

Bottom border only.

Never use large shadows.

---

# 4. Sidebar

Purpose

Configure searches.

Width

Preferred

360 px

Minimum

320 px

Maximum

420 px

Layout

Vertical.

Scrollable.

Content

Search

↓

Algorithm

↓

Execution

↓

Status Summary

Spacing

24 px between sections.

Each section

Title

↓

Divider

↓

Content

---

# 5. Section Card

Every sidebar section should be rendered as a card.

Properties

Padding

16 px

Radius

12 px

Background

White

Border

Gray-200

Shadow

Level 1

Never use transparent cards.

---

# 6. Algorithm Selector

Purpose

Choose search algorithm.

Appearance

Dropdown.

Leading icon.

Algorithm badge.

Optional

Mock badge.

Behavior

Keyboard accessible.

Searchable.

Never hardcode algorithm names.

Display

Algorithm Name

↓

Description

↓

Badge

Selected value remains visible.

---

# 7. Node Picker

Supports

Map selection

Dropdown selection

Search

Autocomplete

Recent selections

Clear button

Placeholder

Choose a location...

Popup

Scrollable.

Maximum

8 visible results.

Search

Fuzzy matching.

---

# 8. Renderer Toggle

Located above visualization.

Segmented control.

Options

Map

Graph

Animated transition.

Changing renderer must never restart search.

---

# 9. Graph Canvas

Purpose

Visualize algorithm execution.

Should occupy the largest area.

Contains

Edges

Nodes

Visited

Current

Path

Selection

Graph background

Neutral Gray.

Map renderer follows MAP_RENDERING_SPEC.md.

---

# 10. Status Bar

Purpose

Always inform user about current state.

Possible states

Idle

Loading

Ready

Running

Paused

Finished

Replay

Error

Appearance

Compact card.

Left icon.

Status text.

Optional description.

Color changes according to state.

Never flash.

---

# 11. Metrics Panel

Purpose

Display search statistics.

Metrics

Distance

Travel Time

Cost

Nodes Visited

Processing Time

Hops

Layout

Grid

2 columns

Desktop

Single column

Tablet

Each metric

Icon

↓

Value

↓

Label

↓

Optional explanation

Numbers

Large typography.

Tabular numerals.

---

# 12. Timeline

Located bottom.

Contains

Playback slider

Current step

Total steps

Speed selector

Controls

Previous

Play

Pause

Restart

Next

Slider

Large.

Easy to drag.

Ticks optional.

Current step always visible.

---

# 13. Animation Controls

Buttons

Square.

Equal size.

Grouped.

Hover

Soft elevation.

Pressed

Scale 0.98.

Disabled

Reduced opacity.

---

# 14. History Panel

Purpose

Replay previous searches.

Each history item

Algorithm

↓

Start

↓

Goal

↓

Time

↓

Replay button

Cards

Compact.

Hover elevation.

Newest first.

---

# 15. Tooltip

Hover only.

Contains

Node ID

Location

Coordinates

Type

Distance (optional)

Rounded.

Shadow.

Small.

Never exceed 300 px width.

---

# 16. Popup

Click node.

Contains

Title

↓

Information

↓

Actions

Actions

Set as Start

Set as Goal

Center Here

Close

---

# 17. Button Styles

Primary

Filled.

Secondary

Outlined.

Ghost

Transparent.

Danger

Red.

Loading

Spinner.

Disabled

Reduced opacity.

All buttons

Height

40 px

Radius

8 px

---

# 18. Text Inputs

Height

40 px

Radius

8 px

Padding

12 px

Placeholder

Gray-500

Focus

Primary outline.

---

# 19. Dropdown

Animated.

Searchable when appropriate.

Maximum height

320 px

Scrollable.

Keyboard navigation required.

---

# 20. Badges

Types

Real

Mock

Status

Info

Small.

Rounded.

Never dominate layout.

---

# 21. Empty States

Every component should have an empty state.

Examples

No History

No Search Result

No Metrics

No Graph

Each empty state

Illustration

↓

Title

↓

Description

↓

Action

---

# 22. Loading States

Use skeleton loaders.

Do not replace layout with spinners.

Skeletons should preserve component dimensions.

---

# 23. Error States

Display

Error icon.

↓

Message.

↓

Retry button.

Never expose stack traces.

---

# 24. Accessibility

Every interactive component must support

Keyboard navigation

Visible focus

ARIA labels

Screen readers

Reduced motion

High contrast

---

# 25. Responsive Rules

Desktop

Three-column layout.

Laptop

Narrow right panel.

Tablet

Sidebar collapses.

History becomes collapsible.

Timeline remains visible.

---

# 26. Performance Rules

Memoize

Graph

Map overlays

Timeline

Metrics

History rows

Avoid unnecessary rerenders.

Static components must not rerender during playback.

---

# 27. Future Compatibility

The component system must support future additions.

Examples

Dijkstra

A*

DFS

Greedy

Traffic layers

Comparison mode

Heatmaps

Without redesigning existing components.

---

# 28. Component Consistency Rules

All components shall

✓ use DESIGN_TOKENS

✓ follow LAYOUT_SPEC

✓ respect MAP_RENDERING_SPEC

✓ preserve GUI_ROADMAP architecture

✓ preserve COMPONENT_SPEC behavior

No component may introduce its own design language.

---

# 29. Acceptance Criteria

A successful implementation satisfies:

✓ Consistent component spacing

✓ Unified visual hierarchy

✓ Accessible controls

✓ Responsive layout

✓ Stable rendering

✓ Smooth interactions

✓ Reusable styling

✓ Professional engineering appearance

✓ No API changes

✓ No backend changes

✓ No architecture changes