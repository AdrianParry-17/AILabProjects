import { act, render, screen } from "@testing-library/react";
import { afterEach, describe, expect, it } from "vitest";

import type { DeliveryNode, SearchResult } from "../../api/types";
import { frameAt } from "../../services/animation";
import { useStore } from "../../state/store";
import { MapView } from "./index";

const NODES: DeliveryNode[] = [
  { id: "a", name: "Alpha", latitude: 10.8, longitude: 106.69, kind: "delivery_supermarket", attributes: {} },
  { id: "b", name: "Beta", latitude: 10.79, longitude: 106.7, kind: "delivery_market", attributes: {} },
  { id: "c", name: "Gamma", latitude: 10.78, longitude: 106.71, kind: "delivery_warehouse", attributes: {} },
];

const RESULT: SearchResult = {
  path: ["a", "b", "c"],
  visited_nodes: ["a", "b", "c"],
  steps: [
    { current_node: "a", frontier: ["b"], reason: "expand a" },
    { current_node: "b", frontier: ["c"], reason: "expand b" },
  ],
  total_distance_km: 3,
  total_time_min: 4,
  total_cost: 5,
  processing_time_ms: 1,
  explanation: "ok",
};

describe("MapView (P3 T11-T13)", () => {
  afterEach(() => {
    useStore.setState({
      graph: null,
      status: "Idle",
      error: null,
      result: null,
      activeIndex: -1,
      playing: false,
      start: null,
      goal: null,
      selectedNode: null,
    });
  });

  function seedReady() {
    act(() =>
      useStore.setState({
        status: "Ready",
        graph: { nodes: NODES, edges: [], bbox: [10.78, 106.69, 10.8, 106.71] },
        result: RESULT,
        activeIndex: 0,
        start: "a",
        goal: "c",
      }),
    );
  }

  it("renders safely in the test environment (leaflet init guarded)", () => {
    seedReady();
    const { container } = render(<MapView />);
    expect(screen.getByTestId("map-view")).toBeInTheDocument();
    // jsdom: the leaflet canvas element exists but leaflet never initialised.
    expect(container.querySelector('[data-testid="map-canvas"]')).not.toBeNull();
    expect(container.querySelector(".leaflet-container")).toBeNull();
    // Loading fade stays until the tile layer reports a load in a real browser.
    expect(screen.queryByTestId("map-skeleton")).not.toBeNull();
  });

  it("consumes the exact same Frame as the Graph renderer (shared frameAt)", () => {
    seedReady();
    render(<MapView />);
    const overlays = screen.getByTestId("map-overlays");
    const expected = frameAt(RESULT.steps, 0);

    expect(overlays.getAttribute("data-visited")).toBe(expected.visitedIds.join(","));
    expect(overlays.getAttribute("data-current")).toBe(expected.current ?? "");
    expect(overlays.getAttribute("data-route")).toBe("1"); // only path[0] visited yet

    act(() => useStore.setState({ activeIndex: 1 }));
    const second = frameAt(RESULT.steps, 1);
    const after = screen.getByTestId("map-overlays");
    expect(after.getAttribute("data-visited")).toBe(second.visitedIds.join(","));
    expect(after.getAttribute("data-current")).toBe(second.current ?? "");
    expect(after.getAttribute("data-route")).toBe("2");
  });

  it("derives start/goal markers from the search result path", () => {
    seedReady();
    render(<MapView />);
    const overlays = screen.getByTestId("map-overlays");
    expect(overlays.getAttribute("data-start")).toBe("a");
    expect(overlays.getAttribute("data-goal")).toBe("c");
  });

  it("falls back to the store start/goal selection when there is no result", () => {
    act(() =>
      useStore.setState({
        status: "Ready",
        graph: { nodes: NODES, edges: [], bbox: [10.78, 106.69, 10.8, 106.71] },
        result: null,
        activeIndex: -1,
        start: "b",
        goal: "b",
      }),
    );
    render(<MapView />);
    const overlays = screen.getByTestId("map-overlays");
    expect(overlays.getAttribute("data-start")).toBe("b");
    expect(overlays.getAttribute("data-goal")).toBe("b");
  });

  it("mounting does not trigger search or reset playback", () => {
    seedReady();
    render(<MapView />);
    expect(useStore.getState().activeIndex).toBe(0);
    expect(useStore.getState().playing).toBe(false);
    expect(useStore.getState().result).toBe(RESULT);
    expect(useStore.getState().start).toBe("a");
  });
});