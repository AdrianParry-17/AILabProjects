import { describe, expect, it } from "vitest";

import type { DeliveryEdge, DeliveryNode } from "../../api/types";
import { edgeLatLngs, progressiveRoute } from "./Overlays";

const NODES = new Map<string, DeliveryNode>(
  [
    { id: "a", name: "A", latitude: 10.8, longitude: 106.69, kind: "delivery_market", attributes: {} },
    { id: "b", name: "B", latitude: 10.79, longitude: 106.7, kind: "delivery_market", attributes: {} },
  ].map((n) => [n.id, n]),
);

describe("MapOverlays helpers (T12)", () => {
  it("progressiveRoute returns 0 when nothing on the path is visited", () => {
    expect(progressiveRoute(["a", "b", "c"], [])).toBe(0);
    expect(progressiveRoute(null, ["a"])).toBe(0);
  });

  it("progressiveRoute counts only the visited path prefix", () => {
    expect(progressiveRoute(["a", "b", "c"], ["a"])).toBe(1);
    expect(progressiveRoute(["a", "b", "c"], ["a", "b"])).toBe(2);
    expect(progressiveRoute(["a", "b", "c"], ["a", "b", "c"])).toBe(3);
    // Gap: "c" visited but "b" is not → progressive drawing stops at "a".
    expect(progressiveRoute(["a", "b", "c"], ["a", "c"])).toBe(1);
  });

  it("edgeLatLngs falls back to the start/end node coordinates", () => {
    const edge: DeliveryEdge = {
      edge_id: "e1",
      start: "a",
      end: "b",
      distance_km: 1,
      time_min: 1,
      congestion: 1,
      risk: 1,
      direction: "two-way",
      road_path: [],
      road_name: "",
      road_class: "",
      attributes: {},
    };
    expect(edgeLatLngs(edge, NODES)).toEqual([
      [10.8, 106.69],
      [10.79, 106.7],
    ]);
  });

  it("edgeLatLngs prefers the embedded road geometry", () => {
    const edge: DeliveryEdge = {
      edge_id: "e1",
      start: "a",
      end: "b",
      distance_km: 1,
      time_min: 1,
      congestion: 1,
      risk: 1,
      direction: "two-way",
      road_path: [],
      road_name: "",
      road_class: "",
      attributes: { geometry: [[106.5, 10.5], [106.6, 10.6]] },
    };
    expect(edgeLatLngs(edge, NODES)).toEqual([
      [10.5, 106.5],
      [10.6, 106.6],
    ]);
  });

  it("edgeLatLngs returns null when an endpoint is unknown", () => {
    const edge: DeliveryEdge = {
      edge_id: "e3",
      start: "a",
      end: "zz",
      distance_km: 1,
      time_min: 1,
      congestion: 1,
      risk: 1,
      direction: "two-way",
      road_path: [],
      road_name: "",
      road_class: "",
      attributes: {},
    };
    expect(edgeLatLngs(edge, NODES)).toBeNull();
  });
});