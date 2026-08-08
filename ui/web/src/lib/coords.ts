/**
 * Coordinate utilities (IMPLEMENTATION_PLAN.md §C.3).
 *
 * World space is WGS84 lon/lat; view space is SVG units with `x = lon`,
 * `y = -lat`. `fitBounds` scales the graph into a viewBox with a margin while
 * keeping the aspect ratio correct; pan/zoom (Task-009) composes transforms on
 * top of the same model.
 */

import type { DeliveryNode } from "../api/types";

export interface Bounds {
  minLon: number;
  minLat: number;
  maxLon: number;
  maxLat: number;
}

/** Bbox is `[min_lat, min_lon, max_lat, max_lon]` (§11). */
export function toBounds(bbox: readonly [number, number, number, number]): Bounds {
  const [minLat, minLon, maxLat, maxLon] = bbox;
  return { minLat, minLon, maxLat, maxLon };
}

export interface ViewTransform {
  /** World units -> view units. */
  scale: number;
  /** View x at world lon = 0. */
  offsetX: number;
  /** View y at world lat = 0 (lat grows up, so this is the y-axis anchor). */
  offsetY: number;
}

/** Fit the world bbox into `width x height` view units with fixed pixel padding (aspect-correct).
 *  Padding is in viewBox pixels (per axis) so the two renderers stay aligned at any
 *  viewport size (MAP_RENDERING_SPEC §4: 40 px padding). */
export function fitBounds(
  bounds: Bounds,
  width: number,
  height: number,
  padding = 40,
): ViewTransform {
  const worldWidth = Math.max(bounds.maxLon - bounds.minLon, Number.EPSILON);
  const worldHeight = Math.max(bounds.maxLat - bounds.minLat, Number.EPSILON);
  const availWidth = Math.max(width - 2 * padding, Number.EPSILON);
  const availHeight = Math.max(height - 2 * padding, Number.EPSILON);
  const scale = Math.min(availWidth / worldWidth, availHeight / worldHeight);

  const centerLon = (bounds.minLon + bounds.maxLon) / 2;
  const centerLat = (bounds.minLat + bounds.maxLat) / 2;
  const offsetX = width / 2 - centerLon * scale;
  const offsetY = height / 2 + centerLat * scale;

  return { scale, offsetX, offsetY };
}

export interface Point {
  x: number;
  y: number;
}

/** Project a lon/lat world point into view units. */
export function project(lon: number, lat: number, t: ViewTransform): Point {
  return { x: t.offsetX + lon * t.scale, y: t.offsetY - lat * t.scale };
}

/** Inverse of `project`; used by pan/zoom (Task-009). */
export function unproject(x: number, y: number, t: ViewTransform): Point {
  return { x: (x - t.offsetX) / t.scale, y: (t.offsetY - y) / t.scale };
}

/** Something that exposes an SVG CTM (an `SVGSVGElement` in the browser). */
export interface HasScreenCtm {
  getScreenCTM(): { a: number; b: number; c: number; d: number; e: number; f: number } | null;
}

/**
 * Convert a client (screen) coordinate into viewBox units of an SVG (Task-009,
 * §C.4). Pointer events report client pixels, but pan/zoom state lives in
 * viewBox units; `getScreenCTM().inverse()` is the exact bridge. Falls back to
 * the raw client point when no CTM is available (jsdom, detached nodes).
 */
export function clientToView(svg: HasScreenCtm, clientX: number, clientY: number): Point {
  const ctm = svg.getScreenCTM();
  if (!ctm) return { x: clientX, y: clientY };
  const det = ctm.a * ctm.d - ctm.c * ctm.b;
  if (det === 0) return { x: clientX, y: clientY };
  return {
    x: (ctm.d * clientX - ctm.c * clientY - ctm.d * ctm.e + ctm.c * ctm.f) / det,
    y: (-ctm.b * clientX + ctm.a * clientY + ctm.b * ctm.e - ctm.a * ctm.f) / det,
  };
}

/** Precomputed id -> view-point map for O(1) node lookups (no scans per frame). */
export interface Projector {
  project(nodeId: string): Point | undefined;
}

export function createProjector(nodes: readonly DeliveryNode[], t: ViewTransform): Projector {
  const positions = new Map<string, Point>();
  for (const node of nodes) {
    positions.set(node.id, project(node.longitude, node.latitude, t));
  }
  return { project: (nodeId) => positions.get(nodeId) };
}

/** Project a `[lon, lat][]` polyline into view points. */
export function projectPolyline(coordinates: readonly number[][], t: ViewTransform): Point[] {
  return coordinates.map(([lon, lat]) => project(lon, lat, t));
}

/** SVG path string for a list of view points. */
export function polylinePath(points: readonly Point[]): string {
  if (points.length === 0) return "";
  return points.map((p) => `${p.x.toFixed(2)},${p.y.toFixed(2)}`).join(" ");
}

export interface InteractiveTransform {
  scale: number;
  translateX: number;
  translateY: number;
}

/** Compose a pan/zoom transform on top of a world->view fit (§C.4). */
export function composeTransform(
  fit: ViewTransform,
  interactive: InteractiveTransform,
): ViewTransform {
  return {
    scale: fit.scale * interactive.scale,
    offsetX: fit.offsetX * interactive.scale + interactive.translateX,
    offsetY: fit.offsetY * interactive.scale + interactive.translateY,
  };
}

/** Zoom `interactive` by `factor` anchored at a view-space point (pointer). */
export function zoomAt(
  interactive: InteractiveTransform,
  factor: number,
  anchor: Point,
  minScale = 0.5,
  maxScale = 4,
): InteractiveTransform {
  const scale = clamp(interactive.scale * factor, minScale, maxScale);
  const k = scale / interactive.scale;
  return {
    scale,
    translateX: anchor.x - k * (anchor.x - interactive.translateX),
    translateY: anchor.y - k * (anchor.y - interactive.translateY),
  };
}

export function clamp(value: number, min: number, max: number): number {
  return Math.min(max, Math.max(min, value));
}