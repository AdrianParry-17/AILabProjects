import { describe, expect, it } from "vitest";

import {
  clamp,
  clientToView,
  composeTransform,
  createProjector,
  fitBounds,
  polylinePath,
  project,
  projectPolyline,
  toBounds,
  unproject,
  zoomAt,
  type InteractiveTransform,
} from "./coords";
import type { DeliveryNode } from "../api/types";

const BOUNDS = { minLon: 0, minLat: 0, maxLon: 10, maxLat: 5 };

const NODES: DeliveryNode[] = [
  { id: "a", name: "A", latitude: 1, longitude: 1, kind: "delivery_market", attributes: {} },
  { id: "b", name: "B", latitude: 4, longitude: 9, kind: "delivery_supermarket", attributes: {} },
];

describe("clamp", () => {
  it("clamps to the bounds", () => {
    expect(clamp(0, 1, 3)).toBe(1);
    expect(clamp(5, 1, 3)).toBe(3);
    expect(clamp(2, 1, 3)).toBe(2);
  });
});

describe("toBounds", () => {
  it("unpacks bbox = [minLat, minLon, maxLat, maxLon]", () => {
    expect(toBounds([1, 2, 3, 4])).toEqual({ minLat: 1, minLon: 2, maxLat: 3, maxLon: 4 });
  });
});

describe("fitBounds", () => {
  it("returns an aspect-correct transform centred on the bbox", () => {
    const t = fitBounds(BOUNDS, 1000, 500, 0);
    const center = project((BOUNDS.minLon + BOUNDS.maxLon) / 2, (BOUNDS.minLat + BOUNDS.maxLat) / 2, t);
    expect(center.x).toBeCloseTo(500, 5);
    expect(center.y).toBeCloseTo(250, 5);
  });

  it("preserves aspect ratio when the viewport does not match the world", () => {
    const t = fitBounds(BOUNDS, 1000, 1000, 0);
    const a = project(0, 0, t);
    const b = project(10, 5, t);
    const dx = b.x - a.x;
    const dy = a.y - b.y;
    expect(dx).toBeCloseTo(dy * 2, 5); // world 10x5 => view should be 1000x500
  });

  it("applies the default 40 px padding (MAP_RENDERING_SPEC §4)", () => {
    const tight = fitBounds(BOUNDS, 1000, 500, 0);
    const padded = fitBounds(BOUNDS, 1000, 500);
    expect(padded.scale).toBeLessThan(tight.scale);
    // 40 px padding leaves 420 viewBox px of vertical room (500 - 2*40); the
    // 2:1 world is then height-bound: scale = 420/5 = 84 => visible width = 840.
    const visibleWidth = (BOUNDS.maxLon - BOUNDS.minLon) * padded.scale;
    expect(visibleWidth).toBeCloseTo(840, 5);
  });

  it("applies the same 40 px padding regardless of viewport size (aligns the two renderers)", () => {
    // The 2:1 world is height-bound in both viewports, so the visible world
    // height is exactly viewportHeight - 2*40: constant 40 px padding on every
    // axis, never a proportional margin.
    const small = fitBounds(BOUNDS, 1000, 500);
    const wide = fitBounds(BOUNDS, 2000, 1000);
    const smallVisibleHeight = (BOUNDS.maxLat - BOUNDS.minLat) * small.scale;
    const wideVisibleHeight = (BOUNDS.maxLat - BOUNDS.minLat) * wide.scale;
    expect(smallVisibleHeight).toBeCloseTo(420, 5); // 500 - 2*40
    expect(wideVisibleHeight).toBeCloseTo(920, 5); // 1000 - 2*40
    expect(wide.scale).toBeCloseTo(small.scale * (920 / 420), 5);
  });

  it("never collapses on a degenerate bbox", () => {
    const t = fitBounds({ minLon: 1, minLat: 1, maxLon: 1, maxLat: 1 }, 1000, 500);
    expect(Number.isFinite(t.scale)).toBe(true);
    expect(t.scale).toBeGreaterThan(0);
  });
});

describe("project / unproject", () => {
  it("inverts cleanly", () => {
    const t = fitBounds(BOUNDS, 1000, 500);
    const p = project(3.7, 2.4, t);
    const w = unproject(p.x, p.y, t);
    expect(w.x).toBeCloseTo(3.7, 5);
    expect(w.y).toBeCloseTo(2.4, 5);
  });
});

describe("composeTransform + zoomAt", () => {
  it("zooms in around an anchor point without drifting the world point under it", () => {
    const base: InteractiveTransform = { scale: 1, translateX: 0, translateY: 0 };
    const fit = fitBounds(BOUNDS, 1000, 500);
    const anchor = { x: 300, y: 200 };
    // World point under the anchor before zoom:
    const before = unproject(anchor.x, anchor.y, fit);
    // Zoom in around the anchor and compose with the fit transform.
    const zoomed = zoomAt(base, 2, anchor, 0.5, 4);
    const composed = composeTransform(fit, zoomed);
    // The same world point must project back to the anchor.
    const after = project(before.x, before.y, composed);
    expect(after.x).toBeCloseTo(anchor.x, 5);
    expect(after.y).toBeCloseTo(anchor.y, 5);
  });

  it("clamps zoom into the [0.5, 4] range used by GraphCanvas", () => {
    const base: InteractiveTransform = { scale: 1, translateX: 0, translateY: 0 };
    expect(zoomAt(base, 100, { x: 0, y: 0 }, 0.5, 4).scale).toBe(4);
    expect(zoomAt(base, 0.001, { x: 0, y: 0 }, 0.5, 4).scale).toBe(0.5);
  });
});

describe("createProjector + projectPolyline + polylinePath", () => {
  it("looks up ids in O(1) and projects every known node", () => {
    const t = fitBounds(BOUNDS, 1000, 500);
    const projector = createProjector(NODES, t);
    expect(projector.project("a")).toBeDefined();
    expect(projector.project("unknown")).toBeUndefined();
  });

  it("projects a polyline preserving vertex order", () => {
    const t = fitBounds(BOUNDS, 1000, 500);
    const pts = projectPolyline(
      [
        [1, 1],
        [9, 4],
      ],
      t,
    );
    expect(pts).toHaveLength(2);
    const path = polylinePath(pts);
    expect(path.split(" ")).toHaveLength(2);
  });

  it("returns an empty path string for an empty polyline", () => {
    expect(polylinePath([])).toBe("");
  });
});

describe("clientToView", () => {
  it("inverts the CTM to translate client pixels into viewBox units", () => {
    const svg = { getScreenCTM: () => ({ a: 2, b: 0, c: 0, d: 2, e: 10, f: 20 }) };
    expect(clientToView(svg, 20, 30)).toEqual({ x: 5, y: 5 });
  });

  it("falls back to the raw client point when CTM is null", () => {
    const svg = { getScreenCTM: () => null };
    expect(clientToView(svg, 7, 9)).toEqual({ x: 7, y: 9 });
  });

  it("falls back when CTM determinant is zero", () => {
    const svg = { getScreenCTM: () => ({ a: 0, b: 0, c: 0, d: 0, e: 0, f: 0 }) };
    expect(clientToView(svg, 7, 9)).toEqual({ x: 7, y: 9 });
  });
});
