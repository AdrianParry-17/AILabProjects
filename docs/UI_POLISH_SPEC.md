# UI_POLISH_SPEC.md

Version: 1.0

Status: Design Specification

---

# 1. Purpose

This document defines the visual polishing requirements for the Delivery AI Search application.

Its purpose is to improve usability, readability, visual hierarchy, and user experience without changing the underlying application architecture or business logic.

This document is complementary to:

- UI_DESIGN_SYSTEM.md
- COMPONENT_SPEC.md
- GUI_ROADMAP.md
- MAP_CONTRACT.md
- CONVENTION.md

If conflicts occur, functional specifications always take precedence over visual polish.

---

# 2. Non-goals

The following are explicitly OUT OF SCOPE.

- No backend modifications.
- No API changes.
- No SearchResult changes.
- No SearchStep changes.
- No MAP_CONTRACT modifications.
- No Redux architecture changes.
- No algorithm implementation changes.
- No additional search features.
- No benchmark implementation.
- No history redesign.
- No new endpoints.

UI polish must never change application behavior.

---

# 3. Overall Design Philosophy

The application should resemble a professional AI visualization platform instead of a CRUD dashboard.

Keywords:

- modern
- minimal
- technical
- research-oriented
- clean
- information-dense
- interactive

Avoid:

- colorful gradients everywhere
- oversized cards
- excessive glassmorphism
- cartoon appearance
- marketing landing-page aesthetics

The interface should feel similar to professional developer tools.

---

# 4. Application Layout

Desktop layout consists of five regions.

-------------------------------------------------

Top Header

-------------------------------------------------

Left Sidebar

Center Visualization

Right Information Panel

-------------------------------------------------

Bottom Playback Timeline

-------------------------------------------------

Every region must have a clear responsibility.

---

# 5. Header

Contains:

Application title

Backend status

Traffic mode

Current renderer

Theme toggle (optional)

Version badge (optional)

The header must remain compact.

Maximum height:

72 px

Do not place search controls inside the header.

---

# 6. Left Sidebar

Purpose:

Configure a search.

Contains only:

Start node

Goal node

Algorithm selector

Run button

Optional advanced settings

Do NOT place metrics here.

Do NOT place history here.

Use grouped sections with visible spacing.

Example groups:

Search

Algorithm

Advanced

Execution

---

# 7. Center Visualization

The visualization area is the primary focus.

Minimum width:

60% of screen

Preferred:

65–75%

It must support two rendering modes.

Mode 1

Graph View

Current graph renderer.

Mode 2

Street Map View

Leaflet

OpenStreetMap tiles

Road network

Animated path overlay

Both modes must consume the exact same SearchResult.

No duplicated state.

---

# 8. Graph / Map Toggle

Provide a segmented control.

Example

Graph | Map

Switching renderer must never rerun search.

Only rendering changes.

Playback continues.

Camera state should be preserved when possible.

---

# 9. Node Rendering

Different node states must be visually distinguishable.

Normal

Start

Goal

Visited

Current

Path

Frontier

Selection

Each state should differ by:

color

size

border

opacity

Optional glow may be used.

---

# 10. Edge Rendering

Support:

normal edges

visited edges

current traversal

final path

Final path must have the strongest emphasis.

---

# 11. Playback Timeline

Playback remains docked at bottom.

Must include:

Play

Pause

Restart

Previous

Next

Speed

Progress slider

Current step

Step count

Status

Timeline should never cover the visualization.

---

# 12. Right Information Panel

Displays search results only.

Contains:

Status

Metrics

Search explanation

Current node

Current frontier

Optional algorithm notes

Avoid placing configuration controls here.

---

# 13. Metrics

Metrics are presented using compact cards.

Each card contains:

Icon

Title

Value

Unit

Cards should use consistent dimensions.

Do not use tables.

---

# 14. Visual Hierarchy

Priority:

1

Visualization

2

Search controls

3

Metrics

4

History

Avoid making every panel equally prominent.

---

# 15. Typography

Use only four levels.

Display

Heading

Body

Caption

Avoid more than four font weights.

---

# 16. Color Usage

Primary

Interactive controls

Secondary

Supporting controls

Success

Completed search

Warning

Mock algorithm

Danger

Errors

Neutral

Background

Avoid excessive accent colors.

---

# 17. Card Design

Cards should have:

consistent padding

consistent radius

subtle borders

light shadows

Avoid floating elements everywhere.

---

# 18. Spacing

Follow an 8 px spacing system.

Allowed spacing:

4

8

12

16

24

32

48

Avoid arbitrary values.

---

# 19. Icons

Use a single icon family.

Icons should assist recognition only.

Never replace text labels.

---

# 20. Motion

Animations should be subtle.

Maximum duration:

300 ms

Playback animation is independent from UI animation.

Respect prefers-reduced-motion.

---

# 21. Loading States

Use skeletons.

Never show empty white panels.

Loading should preserve layout.

---

# 22. Empty States

Each empty panel should explain:

why it is empty

what action the user should perform

---

# 23. Accessibility

Keyboard navigation

Visible focus

ARIA labels

Sufficient contrast

Reduced motion

Screen reader friendly

---

# 24. Responsive Layout

Desktop

1440+

Laptop

1024–1439

Tablet

768–1023

Mobile is not required.

---

# 25. Performance

Do not rerender the graph unnecessarily.

Memoize expensive components.

Separate static layers from animated layers.

Avoid layout thrashing.

---

# 26. Internationalization

Application language:

English

Exceptions:

Vietnamese location names

Vietnamese road names

Vietnamese district names

Vietnamese POI names

Everything else must remain English.

Example:

Choose Algorithm

Start Location

Destination

Run Search

Metrics

Playback

History

But:

Quận 1

Đường Nguyễn Huệ

Đại học Bách Khoa

---

# 27. Academic Presentation

The application should be suitable for:

AI algorithm demonstrations

University presentations

Final project defense

Research visualization

Avoid styles resembling commercial dashboards.

---

# 28. Reference Images

Reference screenshots are provided only for inspiration.

They must never be copied directly.

Allowed inspiration:

layout

spacing

hierarchy

card grouping

visual emphasis

Not allowed:

pixel-perfect copies

identical colors

identical branding

identical component shapes

---

# 29. Acceptance Criteria

A successful polish satisfies all of the following.

✓ Existing functionality remains unchanged.

✓ MAP_CONTRACT remains unchanged.

✓ SearchResult remains unchanged.

✓ SearchStep remains unchanged.

✓ All existing tests continue to pass.

✓ The UI becomes more readable.

✓ Visualization becomes the primary focus.

✓ Graph and Map rendering are both available.

✓ English UI is preserved.

✓ Vietnamese location names are preserved.

✓ Performance is not degraded.

✓ Accessibility is maintained.
