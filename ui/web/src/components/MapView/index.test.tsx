import { act, fireEvent, render, screen } from "@testing-library/react";
import { afterEach, describe, expect, it, vi } from "vitest";

import type { DeliveryNode, SearchResult } from "../../api/types";
import { frameAt } from "../../services/animation";
import { useStore } from "../../state/store";
import { MapView, resolveHoverPoint } from "./index";

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

  it("keeps the map host mounted through search Loading→Ready (no orphaned Leaflet instance)", () => {
    seedReady();
    render(<MapView />);
    const hostBefore = screen.getByTestId("map-canvas");

    act(() => useStore.setState({ status: "Loading" }));
    expect(screen.getByTestId("map-skeleton")).toBeInTheDocument();
    const hostDuring = screen.getByTestId("map-canvas");
    expect(hostDuring).toBe(hostBefore);

    act(() => useStore.setState({ status: "Ready" }));
    const hostAfter = screen.getByTestId("map-canvas");
    expect(hostAfter).toBe(hostBefore);
  });

  it("keeps the map host mounted through Error and recovery (F1) — error overlay is owned by GraphPane", () => {
    seedReady();
    render(<MapView />);
    const hostBefore = screen.getByTestId("map-canvas");

    // T22: graph-load error rendering moved to GraphPane; MapView only mounts
    // the Leaflet host. The map host must stay mounted when status flips to
    // Error and recover when status returns to Ready.
    act(() => useStore.setState({ status: "Error", error: "boom" }));
    expect(screen.getByTestId("map-canvas")).toBe(hostBefore);
    expect(screen.queryByTestId("map-tile-error")).toBeNull();

    act(() => useStore.setState({ status: "Ready", error: null }));
    expect(screen.getByTestId("map-canvas")).toBe(hostBefore);
    expect(screen.queryByTestId("map-tile-error")).toBeNull();
    expect(screen.getByTestId("map-overlays")).toBeInTheDocument();
  });

  it("renders an empty host when no graph exists; visualization loading is owned by GraphPane (T22)", () => {
    act(() =>
      useStore.setState({
        status: "Loading",
        graph: null,
        result: RESULT,
        activeIndex: 1,
      }),
    );
    const { container } = render(<MapView />);
    expect(screen.getByTestId("map-view")).toBeInTheDocument();
    // MapView stays empty while the visualization region skeleton renders in
    // GraphPane; the map canvas is not mounted without a graph.
    expect(screen.queryByTestId("map-canvas")).toBeNull();
    expect(screen.queryByTestId("map-skeleton")).toBeNull();
    expect(container.querySelector(".leaflet-container")).toBeNull();

    // Search-style status flip: Loading → Ready must not reset search state.
    act(() =>
      useStore.setState({
        status: "Ready",
        graph: { nodes: NODES, edges: [], bbox: [10.78, 106.69, 10.8, 106.71] },
      }),
    );
    expect(useStore.getState().result).toBe(RESULT);
    expect(useStore.getState().activeIndex).toBe(1);
    const overlays = screen.getByTestId("map-overlays");
    const expected = frameAt(RESULT.steps, 1);
    expect(overlays.getAttribute("data-visited")).toBe(expected.visitedIds.join(","));
  });

  it("exposes a keyboard-reachable node list that selects the same node as a marker click", () => {
    seedReady();
    render(<MapView />);
    const row = screen.getByRole("button", { name: /Alpha/i });
    fireEvent.click(row);
    expect(useStore.getState().selectedNode).toBe("a");
    expect(row.getAttribute("aria-pressed")).toBe("true");
  });

  it("keeps the node list wired to the same popup/selection path as markers", () => {
    seedReady();
    render(<MapView />);
    fireEvent.click(screen.getByRole("button", { name: /Beta/i }));
    expect(useStore.getState().selectedNode).toBe("b");
  });
});

describe("resolveHoverPoint (T13/F8)", () => {
  const NODE: DeliveryNode = {
    id: "n",
    name: "N",
    latitude: 10.8,
    longitude: 106.69,
    kind: "delivery_market",
    attributes: {},
  };

  it("prefers the explicit Leaflet container point when provided", () => {
    expect(resolveHoverPoint(null, NODE, { x: 3, y: 4 })).toEqual({ x: 3, y: 4 });
  });

  it("derives the anchor from node coordinates when the marker passed none (pins/current)", () => {
    const view = {
      map: { latLngToContainerPoint: () => ({ x: 17, y: 29 }) },
    } as unknown as Parameters<typeof resolveHoverPoint>[0];
    expect(resolveHoverPoint(view, NODE, null)).toEqual({ x: 17, y: 29 });
  });

  it("returns null when there is no anchor to derive", () => {
    expect(resolveHoverPoint(null, NODE, null)).toBeNull();
    expect(resolveHoverPoint(null, null, null)).toBeNull();
  });
});

describe("MapView T22 — tile-only error overlay (UI_TASK_BREAKDOWN §7 T22)", () => {
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

  it("MapView does not own the graph-load Retry surface (T22 — moved to GraphPane)", () => {
    act(() =>
      useStore.setState({
        status: "Error",
        error: "boom",
        graph: { nodes: NODES, edges: [], bbox: [10.78, 106.69, 10.8, 106.71] },
      }),
    );
    render(<MapView />);
    // The legacy graph-load error overlay no longer lives inside MapView.
    expect(screen.queryByTestId("map-error")).toBeNull();
    expect(screen.queryByRole("button", { name: "Retry" })).toBeNull();
  });

  it("MapView does not call loadGraph from any of its Retry buttons (only tile retry is local)", () => {
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
    const spy = vi.spyOn(useStore.getState(), "loadGraph");
    render(<MapView />);
    // No "Retry" surface owned by MapView (graph-load retry moved to GraphPane).
    expect(screen.queryByRole("button", { name: /Retry/i })).toBeNull();
    // The NodeListFallback rows are buttons and selecting one goes through
    // store actions (selectNode / setStart / setGoal), not loadGraph.
    fireEvent.click(screen.getByRole("button", { name: /Alpha/i }));
    expect(spy).not.toHaveBeenCalled();
    spy.mockRestore();
  });
});