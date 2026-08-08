# DESIGN_TOKENS.md

Version: 1.0

Status: Frozen Design Tokens

Owner: GUI Team

---

# 1. Purpose

This document defines every reusable design token used by the web interface.

Its purpose is to ensure every screen uses the same visual language.

Design tokens are the single source of truth for:

- colors
- typography
- spacing
- sizing
- radius
- borders
- shadows
- elevation
- animation
- z-index
- opacity

No component should introduce custom visual values when an existing token already exists.

If additional tokens are required, they must be added here first.

---

# 2. Design Philosophy

The application represents an AI Search visualization platform.

Visual characteristics:

- professional
- technical
- modern
- lightweight
- research-oriented
- minimal

Avoid:

- excessive gradients
- excessive glassmorphism
- flashy neon colors
- marketing landing-page appearance
- game-like interfaces

The interface should resemble engineering software rather than a commercial dashboard.

---

# 3. Color System

## 3.1 Brand Colors

Primary

Purpose

Primary actions

Algorithm selection

Active controls

Links

Accent borders

```
Primary-50
Primary-100
Primary-200
Primary-300
Primary-400
Primary-500
Primary-600
Primary-700
Primary-800
Primary-900
```

Default UI color

Primary-500

---

Secondary

Used for

secondary actions

hover states

supporting controls

---

Success

Used for

Completed search

Success notification

Completed animation

Valid status

---

Warning

Used for

Mock algorithms

Performance warning

Missing data

---

Danger

Used for

Errors

API failure

Validation failure

---

Info

Used for

Current node

Hints

Information cards

---

# 4. Neutral Palette

Neutral colors should dominate the interface.

Do not overuse accent colors.

```
Gray-50
Gray-100
Gray-200
Gray-300
Gray-400
Gray-500
Gray-600
Gray-700
Gray-800
Gray-900
```

Background should primarily use:

Gray-50

Cards:

White

Borders:

Gray-200

Text:

Gray-900

Secondary text:

Gray-600

Disabled:

Gray-400

---

# 5. Semantic Colors

## Graph

Normal Node

Neutral

Visited

Success

Current

Info

Frontier

Primary

Start

Success

Goal

Danger

Selected

Primary

Path

Warning

---

Street Map

Road

Gray

Current Path

Primary

Visited Path

Success

Traffic Overlay

Warning

Unavailable Road

Danger

---

# 6. Typography

Font Family

Inter

Fallback

system-ui

Segoe UI

Roboto

sans-serif

---

Weights

Regular

400

Medium

500

Semibold

600

Bold

700

Avoid using more than four font weights.

---

# 7. Font Scale

Display XL

40 px

Display

32 px

Heading

28 px

Title

22 px

Subtitle

18 px

Body

16 px

Small

14 px

Caption

12 px

---

# 8. Line Height

Display

120%

Heading

130%

Body

150%

Caption

140%

---

# 9. Letter Spacing

Default

0

Heading

-0.02em

Caption

0.02em

---

# 10. Spacing System

Use an 8-point grid.

Allowed spacing values

```
4
8
12
16
24
32
40
48
64
80
96
```

No arbitrary spacing values are allowed.

---

# 11. Border Radius

Small

4 px

Medium

8 px

Large

12 px

XL

16 px

Round

9999 px

Cards should use

12 px

Buttons

8 px

Inputs

8 px

Badges

9999 px

---

# 12. Border Width

Hairline

1 px

Strong

2 px

Focus

2 px

Selected

2 px

---

# 13. Elevation

Level 0

Flat

Level 1

Cards

Level 2

Dropdown

Popover

Level 3

Modal

Level 4

Toast

Avoid excessive shadows.

---

# 14. Shadow System

Small

Cards

Medium

Dropdown

Large

Modal

Extra Large

Floating panels

Shadows should be soft.

Never use heavy black shadows.

---

# 15. Opacity

Disabled

40%

Muted

60%

Hover Overlay

8%

Pressed Overlay

12%

Selection Overlay

16%

---

# 16. Motion Tokens

Fast

150 ms

Normal

200 ms

Slow

300 ms

Maximum UI animation

300 ms

Playback animation timing is defined separately in ANIMATION_SPEC.md.

---

# 17. Easing

Default

ease-out

Hover

ease-out

Sidebar

ease-in-out

Dialog

ease-out

---

# 18. Icon Sizes

Small

16 px

Normal

20 px

Medium

24 px

Large

32 px

Avoid icons larger than 32 px inside normal UI.

---

# 19. Avatar / Node Sizes

Graph Node

8 px

Selected Node

12 px

Current Node

14 px

Goal

12 px

Start

12 px

---

# 20. Button Sizes

Small

32 px

Default

40 px

Large

48 px

Primary actions should use

40 px

---

# 21. Input Sizes

Default height

40 px

Compact

32 px

Padding

12 px

---

# 22. Card Tokens

Padding

16 px

Radius

12 px

Gap

16 px

Border

Gray-200

Background

White

---

# 23. Panel Tokens

Sidebar

Background

White

Inspector

White

Timeline

White

Canvas

Gray-50

---

# 24. Divider Tokens

Thickness

1 px

Color

Gray-200

Never use decorative dividers.

---

# 25. Status Colors

Idle

Gray

Loading

Primary

Running

Info

Completed

Success

Warning

Warning

Failed

Danger

---

# 26. Focus Ring

Keyboard focus must always be visible.

Width

2 px

Radius

8 px

Color

Primary-500

---

# 27. Scrollbars

Thin

Rounded

Neutral

Avoid custom decorative scrollbars.

---

# 28. Z-Index

Canvas

0

Tooltip

100

Dropdown

200

Sidebar Overlay

300

Modal

400

Toast

500

---

# 29. Dark Mode

Dark mode is optional.

If implemented later:

Tokens must be overridden rather than duplicated.

Component logic must remain unchanged.

---

# 30. Token Usage Rules

Components must consume existing tokens.

Do not hardcode:

colors

font sizes

spacing

radius

shadow

opacity

transition duration

If a required token does not exist, add it here first.

---

# 31. Acceptance Criteria

A valid implementation satisfies:

✓ Consistent spacing

✓ Consistent typography

✓ Unified color usage

✓ No arbitrary visual values

✓ Components reuse existing tokens

✓ Visual consistency across the application

✓ Future UI extensions require no redesign