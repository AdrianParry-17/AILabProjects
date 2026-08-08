# MOTION_SPEC.md

Version: 1.0

Status: Frozen

Purpose

This document defines all motion, animation and transition rules used throughout the GUI.

Motion exists only to improve usability and visual continuity.

Animation must never reduce readability, delay interaction or distract users.

All motion should feel:

- Fast
- Smooth
- Predictable
- Consistent

---

# 1. Motion Principles

Every animation must satisfy at least one purpose:

- Explain state changes
- Preserve spatial continuity
- Guide user attention
- Improve perceived performance
- Confirm user actions

Animation must NEVER exist purely for decoration.

---

# 2. Motion Philosophy

The interface should feel like:

- Professional software
- Desktop application
- Engineering tool

NOT like:

- Mobile game
- Marketing landing page
- Presentation website

Motion should be subtle.

Less animation is preferred over excessive animation.

---

# 3. Motion Hierarchy

Motion priority:

1. Search playback
2. Map interaction
3. Selection feedback
4. Panel transitions
5. Hover states
6. Small decorative fades

---

# 4. Global Duration

Very Fast

100 ms

Used for:

Hover

Button press

Checkbox

Toggle

Fast

150 ms

Used for:

Selection

Highlight

Tooltip

Small opacity

Normal

220 ms

Used for:

Cards

Sidebar

Dialogs

Panels

Map controls

Slow

300 ms

Used for:

Drawer

Layout changes

Replay loading

Never exceed

400 ms

---

# 5. Easing

Default

ease-out

Used by almost everything.

Panel opening

cubic-bezier(0.22,1,0.36,1)

Map zoom

ease-in-out

Opacity

linear

Never use:

bounce

elastic

spring

overshoot

back

---

# 6. Allowed Animations

Only the following are allowed.

Opacity

Fade In

Fade Out

Translate

X

Y

Scale

0.98 → 1

Rotation

Only loading spinner

Nothing else may rotate.

---

# 7. Forbidden Animations

Do NOT use:

Bounce

Shake

Flip

Swing

Infinite floating

Blink

Flash

Zoom explosion

Elastic

Rubber band

Animated gradients

Background movement

Continuous motion

---

# 8. Hover Behavior

Buttons

Background

Elevation

Cursor

150ms

Cards

Shadow

Border color

No movement larger than 2px

Map Node

Increase radius slightly

Highlight stroke

Tooltip fade

Algorithm item

Background

Border

Icon color

---

# 9. Focus Animation

Keyboard focus must be visible.

Animate only:

Outline

Border

Shadow

Duration

100ms

Never animate focus position.

---

# 10. Selection Feedback

Selected Node

Outer ring

Accent color

Fade in

220ms

Selected Algorithm

Background

Border

Icon

Selected Timeline Step

Filled circle

Accent color

Current Step

Animated pulse

Pulse only once.

Never infinite.

---

# 11. Search Playback Animation

Playback is the most important animation.

Each SearchStep updates:

Current node

Visited nodes

Frontier

Path

Metrics

Status

Update order

1.

Visited

↓

2.

Frontier

↓

3.

Current Node

↓

4.

Path

↓

5.

Metrics

↓

6.

Status

Each update should appear smooth.

---

# 12. Timeline

Play

Linear

Pause

Immediate

Resume

Continue

Restart

Fade current path

Reset state

Begin from first step

Jump

Immediate

No transition across skipped steps.

---

# 13. Path Animation

When solution found

Draw route progressively.

Stroke animation

150–250ms

Never redraw the entire map.

Only animate:

Solution polyline

Current active edge

---

# 14. Map Interaction

Zoom

Smooth interpolation

Pan

Native browser performance

Fit View

220ms

Node hover

Fade tooltip

Node click

Selection ring

Map should never re-render static geometry.

---

# 15. Sidebar Animation

Open

Slide + Fade

220ms

Close

Fade + Slide

220ms

Panel expansion

Height animation

Maximum

220ms

---

# 16. Dialog Animation

Opacity

Scale

0.98 → 1

220ms

Close

Reverse

---

# 17. Tooltip Animation

Fade

100ms

Small translateY

2px

Never scale tooltips.

---

# 18. Status Bar

Loading

Spinner

Searching

Spinner

Success

Fade

Error

Fade

Finished

Accent pulse

One time only.

---

# 19. Loading Skeleton

Allowed for:

History

Metrics

Algorithm catalog

Version

Never use loading spinner for large panels if skeleton is possible.

---

# 20. Reduced Motion

If prefers-reduced-motion is enabled:

Disable:

Playback interpolation

Panel animation

Hover transitions

Map animation

Keep only:

Opacity

Instant state changes

Required accessibility animations

---

# 21. Performance Requirements

Animation must maintain:

60 FPS target

Minimum acceptable:

30 FPS

No animation may trigger:

Large layout recalculation

Mass DOM updates

SVG regeneration

Heavy React re-render

Static map layers must remain memoized.

---

# 22. React Guidelines

Prefer:

CSS transitions

Transform

Opacity

Avoid:

Animating width

Animating height repeatedly

Animating top

Animating left

Animating expensive SVG properties

Use requestAnimationFrame for playback timing.

---

# 23. Motion Consistency

Every interactive component must use identical timing.

Example

Primary Button

150ms

Secondary Button

150ms

Danger Button

150ms

Hover

150ms

Selection

220ms

Tooltip

100ms

Never invent new timings inside components.

---

# 24. Animation Tokens

Standard durations

--motion-fast: 100ms

--motion-normal: 150ms

--motion-medium: 220ms

--motion-slow: 300ms

Standard easing

--ease-default

--ease-panel

--ease-linear

All components must consume these shared tokens.

Hardcoded values are forbidden.

---

# 25. Acceptance Criteria

A polished interface should feel:

Fast

Responsive

Modern

Professional

Engineering-oriented

Animations should help users understand:

where they are,

what changed,

and what the algorithm is currently doing.

Users should notice smoothness,

not animation itself.