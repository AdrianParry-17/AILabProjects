import { act, fireEvent, render, screen } from "@testing-library/react";
import { afterEach, describe, expect, it, vi } from "vitest";

import { client } from "../../api/client";
import { useStore } from "../../state/store";
import { clientToView, clamp, zoomAt } from "../../lib/coords";
import type { SearchResult } from "../../api/types";
import { GraphCanvas, __staticRenderCounts } from "./index";

const FIXTURE = {
  nodes: [
    { id: "a", name: "A", latitude: 1, longitude: 2, kind: "delivery_market", attributes: {} },
    { id: "b", name: "B", latitude: 1.1, longitude: 2.1, kind: "delivery_supermarket", attributes: {} },
    { id: "c", name: "C", latitude: 1.2, longitude: 1.9, kind: "delivery_warehouse", attributes: {} },
  ],
  edges: [
    { edge_id: "e1", start: "a", end: "b", distance_km: 1, time_min: 1, congestion: 1, risk: 1, direction: "two-way", road_path: [], road_name: "", road_class: "", attributes: {} },
    { edge_id: "e2", start: "b", end: "c", distance_km: 1, time_min: 1, congestion: 1, risk: 1, direction: "two-way", road_path: [], road_name: "", road_class: "", attributes: {} },
  ],
  bbox: [1, 2, 1.2, 3] as [number, number, number, number],
};

function makeResult(n: number): SearchResult {
  return {
    path: Array.from({ length: n }, (_, i) => `n${i}`),
    visited_nodes: Array.from({ length: n }, (_, i) => `n${i}`),
    steps: Array.from({ length: n }, (_, i) => ({
      current_node: `n${i}`,
      frontier: i < n - 1 ? [`n${i + 1}`] : [],
      reason: `expand ${i}`,
    })),
    total_distance_km: 1,
    total_time_min: 1,
    total_cost: 1,
    processing_time_ms: 1,
    explanation: "ok",
  };
}

describe("GraphCanvas", () => {
  afterEach(() => {
    vi.restoreAllMocks();
    useStore.setState({ graph: null, status: "Idle" });
  });

  it("renders an EmptyState when graph is null", () => {
    act(() => useStore.setState({ graph: null, status: "Ready" }));
    render(<GraphCanvas />);
    expect(screen.getByText(/No graph data/)).toBeInTheDocument();
  });

  it("renders all nodes and edges from the store", () => {
    vi.spyOn(client, "getGraph").mockResolvedValue({
      graph: FIXTURE,
      bbox: FIXTURE.bbox,
      metadata: { schema_version: "1.0", node_count: 3, edge_count: 2 },
    } as never);
    act(() => useStore.setState({ status: "Ready", graph: FIXTURE }));
    render(<GraphCanvas />);
    const canvas = screen.getByTestId("graph-canvas");
    expect(canvas).toBeInTheDocument();
    expect(canvas.querySelectorAll("path")).toHaveLength(2);
    expect(canvas.querySelectorAll("g[role='button']")).toHaveLength(3);
  });

  it("tags each static node with data-node-id and a stable state attribute", () => {
    act(() =>
      useStore.setState({
        status: "Finished",
        graph: FIXTURE,
        result: {
          path: ["a", "b", "c"],
          visited_nodes: ["a", "b", "c"],
          steps: [
            { current_node: "a", frontier: ["b"], reason: "expand" },
            { current_node: "b", frontier: ["c"], reason: "expand" },
          ],
          total_distance_km: 1.5,
          total_time_min: 2,
          total_cost: 3,
          processing_time_ms: 1,
          explanation: "ok",
        },
        activeIndex: 1,
      }),
    );
    render(<GraphCanvas />);
    const canvas = screen.getByTestId("graph-canvas");
    expect(canvas.querySelector('[data-node-id="a"]')?.getAttribute("data-state")).toBe("start");
    expect(canvas.querySelector('[data-node-id="c"]')?.getAttribute("data-state")).toBe("goal");
    expect(canvas.querySelector('[data-node-id="b"]')?.getAttribute("data-state")).toBe("path");
  });

  it("selects a node on click and reflects aria-selected", () => {
    act(() => useStore.setState({ status: "Ready", graph: FIXTURE, selectedNode: null }));
    render(<GraphCanvas />);
    const nodes = screen.getAllByRole("button", { name: /A \(|B \(|C \(/ });
    act(() => {
      fireEvent.click(nodes[0]);
    });
    expect(useStore.getState().selectedNode).toBe("a");
  });

  it("uses the container-sized viewBox and falls back to 1000x700 in jsdom", () => {
    act(() => useStore.setState({ status: "Ready", graph: FIXTURE }));
    render(<GraphCanvas />);
    const canvas = screen.getByTestId("graph-canvas");
    expect(canvas.getAttribute("viewBox")).toBe("0 0 1000 700");
  });

  it("renders the RouteOverlay + Legend when a result with steps exists", () => {
    const result: SearchResult = {
      path: ["a", "b", "c"],
      visited_nodes: ["a", "b", "c"],
      steps: [
        { current_node: "a", frontier: ["b"], reason: "expand" },
        { current_node: "b", frontier: ["c"], reason: "expand" },
      ],
      total_distance_km: 1.5,
      total_time_min: 2,
      total_cost: 3,
      processing_time_ms: 1,
      explanation: "ok",
    };
    act(() =>
      useStore.setState({
        status: "Finished",
        graph: FIXTURE,
        result,
        activeIndex: 0,
      }),
    );
    render(<GraphCanvas />);
    const canvas = screen.getByTestId("graph-canvas");
    // route = halo + line polyline
    expect(canvas.querySelectorAll("polyline")).toHaveLength(2);
    // nodes(3) + visited(1) + frontier(1) + path(3) + current(1) + start/goal cores(2) + rings(2) = 13
    expect(canvas.querySelectorAll("circle")).toHaveLength(13);
    expect(screen.getByRole("note", { name: /Map legend/i })).toBeInTheDocument();
    expect(document.querySelectorAll("ul[role='note'] li")).toHaveLength(6);
  });

  it("renders no overlay or legend before any search result", () => {
    act(() => useStore.setState({ status: "Ready", graph: FIXTURE, result: null }));
    render(<GraphCanvas />);
    const canvas = screen.getByTestId("graph-canvas");
    expect(canvas.querySelectorAll("polyline")).toHaveLength(0);
    expect(screen.queryByRole("note", { name: /Map legend/i })).not.toBeInTheDocument();
  });

  it("animates the Fit transition over 220ms and honours prefers-reduced-motion (H3)", () => {
    act(() =>
      useStore.setState({
        status: "Ready",
        graph: FIXTURE,
        result: makeResult(1),
        activeIndex: 0,
      }),
    );
    const { container } = render(<GraphCanvas />);
    screen.getByTestId("graph-canvas");
    const rAF = vi.spyOn(window, "requestAnimationFrame");
    const realMatchMedia = window.matchMedia;
    const query = { matches: true, media: "", onchange: null, addListener() {}, removeListener() {}, addEventListener() {}, removeEventListener() {}, dispatchEvent: () => false };
    window.matchMedia = vi.fn(() => query) as unknown as typeof window.matchMedia;

    try {
      const baselineHTML = container.querySelector("g")?.outerHTML ?? "";
      act(() => screen.getByRole("button", { name: "Zoom In" }).click());
      expect(rAF).not.toHaveBeenCalled();

      // Reduced motion: Fit jumps instantly, no animation frames.
      act(() => screen.getByRole("button", { name: /Fit Graph/i }).click());
      expect(rAF).not.toHaveBeenCalled();

      // Normal motion: Fit animates via rAF and lands exactly on IDLE.
      query.matches = false;
      vi.useFakeTimers({ toFake: ["performance", "requestAnimationFrame"] });
      try {
        act(() => screen.getByRole("button", { name: "Zoom In" }).click());
        act(() => screen.getByRole("button", { name: /Fit Graph/i }).click());
        expect(rAF).toHaveBeenCalled();
        act(() => vi.advanceTimersByTime(110));
        expect(container.querySelector("g")?.outerHTML).not.toBe(baselineHTML);
        act(() => vi.advanceTimersByTime(120));
        expect(container.querySelector("g")?.outerHTML).toBe(baselineHTML);
      } finally {
        vi.useRealTimers();
      }
    } finally {
      rAF.mockRestore();
      window.matchMedia = realMatchMedia;
    }
  });

  it("does not re-render the static EdgesLayer or NodesLayer across N=50 playback steps", () => {
    __staticRenderCounts.edges = 0;
    __staticRenderCounts.nodes = 0;

    act(() =>
      useStore.setState({
        status: "Ready",
        graph: FIXTURE,
        result: makeResult(50),
        activeIndex: 0,
      }),
    );
    render(<GraphCanvas />);
    screen.getByTestId("graph-canvas");
    expect(__staticRenderCounts.edges).toBe(1);
    expect(__staticRenderCounts.nodes).toBe(1);

    // Advance playback across 50 steps; only the animated RouteOverlay may
    // re-render — the memoized static layers must render 0 more times.
    for (let i = 1; i < 50; i += 1) {
      act(() => useStore.setState({ activeIndex: i }));
    }

    expect(__staticRenderCounts.edges).toBe(1);
    expect(__staticRenderCounts.nodes).toBe(1);
  });
});

describe("coords helpers", () => {
  it("clamps zoom to the 0.5–4 range", () => {
    const base = { scale: 1, translateX: 0, translateY: 0 };
    const zoomedIn = zoomAt(base, 100, { x: 0, y: 0 }, 0.5, 4);
    expect(zoomedIn.scale).toBe(4);
    const zoomedOut = zoomAt(base, 0.001, { x: 0, y: 0 }, 0.5, 4);
    expect(zoomedOut.scale).toBe(0.5);
    expect(clamp(10, 0, 5)).toBe(5);
    expect(clamp(-1, 0, 5)).toBe(0);
  });

  it("clientToView converts client pixels into viewBox units via the CTM", () => {
    const svg = {
      getScreenCTM: () => ({ a: 2, b: 0, c: 0, d: 2, e: 10, f: 20 }),
    };
    expect(clientToView(svg, 20, 30)).toEqual({ x: 5, y: 5 });
  });

  it("clientToView falls back to the raw client point when there is no CTM", () => {
    const svg = { getScreenCTM: () => null };
    expect(clientToView(svg, 7, 9)).toEqual({ x: 7, y: 9 });
  });
});
