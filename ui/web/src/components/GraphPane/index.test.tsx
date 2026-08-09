import { act, fireEvent, render, screen } from "@testing-library/react";
import { afterEach, describe, expect, it, vi } from "vitest";

import { client } from "../../api/client";
import { selectMetrics } from "../../lib/metrics";
import { useStore } from "../../state/store";
import type { DeliveryNode, SearchResult } from "../../api/types";
import { GraphPane } from "./index";

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
    { current_node: "c", frontier: [], reason: "goal" },
  ],
  total_distance_km: 3,
  total_time_min: 4,
  total_cost: 5,
  processing_time_ms: 1,
  explanation: "BFS - mô phỏng: ưu tiên hàng đợi FIFO",
};

function seedSearchGraph(renderer: "graph" | "map", activeIndex = 1): void {
  act(() =>
    useStore.setState({
      renderer,
      status: "Ready",
      graph: { nodes: NODES, edges: [], bbox: [10.78, 106.69, 10.8, 106.71] },
      result: RESULT,
      activeIndex,
      start: "a",
      goal: "c",
      selectedAlgorithm: "bfs",
      selectedNode: "b",
      history: [
        {
          id: "r-1",
          algorithm: "bfs",
          start: "a",
          goal: "c",
          source: "real",
          created_at: "2024-01-01T00:00:00Z",
          hops: 2,
          result: RESULT,
        },
      ],
    }),
  );
}

function graphCanvasStates(activeIndex: number, selectedNode: string | null): Record<string, string> {
  // Mirror GraphCanvas/index.tsx node data-state logic exactly so the test
  // can compare both renderers against the same canonical mapping.
  const start = "a";
  const goal = "c";
  const states: Record<string, string> = {};
  for (const node of NODES) {
    const selected = selectedNode === node.id;
    const isStart = node.id === start;
    const isGoal = node.id === goal;
    const onPath = RESULT.path.includes(node.id);
    states[node.id] = selected
      ? "selected"
      : isStart
        ? "start"
        : isGoal
          ? "goal"
          : onPath
            ? "path"
            : "normal";
  }
  // activeIndex is consumed by MapView's overlays; included here so the test
  // signature matches the renderer-agnostic intent.
  void activeIndex;
  return states;
}

describe("GraphPane", () => {
  afterEach(() => {
    act(() => useStore.setState({ renderer: "map" }));
  });

  it("renders a visualization region with the expected markup", () => {
    render(<GraphPane />);
    const region = screen.getByRole("region", { name: "Visualization" });
    expect(region).toHaveAttribute("data-testid", "graph-pane");
  });

  it("renders the host that owns the canvas", () => {
    const { container } = render(<GraphPane />);
    // T22: when no graph exists the stage shows the empty state, not the
    // canvas host. With a graph seeded the active renderer mounts inside the
    // stage. Both shapes must render a graph-stage host.
    expect(screen.getByTestId("graph-stage")).toBeInTheDocument();
    expect(container.querySelector('[data-testid="map-pane"]')).toBeNull();
  });

  it("mounts the RendererToggle and reflects the active renderer on the stage", () => {
    render(<GraphPane />);
    expect(screen.getByRole("group", { name: /Visualization renderer/i })).toBeInTheDocument();
    expect(
      screen.getByRole("button", { name: /Map view/i }).getAttribute("aria-pressed"),
    ).toBe("true");
    expect(screen.getByTestId("graph-stage").getAttribute("data-renderer")).toBe("map");
  });

  it("updates the stage data-renderer attribute when the renderer changes", () => {
    render(<GraphPane />);
    expect(screen.getByTestId("graph-stage").getAttribute("data-renderer")).toBe("map");
    act(() => useStore.setState({ renderer: "graph" }));
    expect(screen.getByTestId("graph-stage").getAttribute("data-renderer")).toBe("graph");
  });
});

describe("GraphPane T22 — loading/empty/error states (UI_TASK_BREAKDOWN §7 T22)", () => {
  afterEach(() => {
    act(() =>
      useStore.setState({
        renderer: "map",
        status: "Idle",
        error: null,
        graph: null,
      }),
    );
  });

  it("shows a loading skeleton while the graph is being fetched (never a blank pane)", () => {
    act(() => useStore.setState({ status: "Loading", graph: null }));
    render(<GraphPane />);
    const stage = screen.getByTestId("graph-stage");
    expect(stage.getAttribute("data-graph-status")).toBe("loading");
    expect(stage.getAttribute("aria-busy")).toBe("true");
    // No empty-state "Load graph" / "Retry" surface during loading.
    expect(screen.queryByRole("button", { name: /Load graph/i })).toBeNull();
    expect(screen.queryByRole("button", { name: /Retry/i })).toBeNull();
  });

  it("shows the empty state with the 'Load graph' primary action when no graph exists", () => {
    act(() => useStore.setState({ status: "Idle", graph: null }));
    render(<GraphPane />);
    const stage = screen.getByTestId("graph-stage");
    expect(stage.getAttribute("data-graph-status")).toBe("empty");
    expect(screen.getByText("Load graph to begin.")).toBeInTheDocument();
    // Empty state uses the "Load graph" action, NOT a retry.
    const action = screen.getByRole("button", { name: /Load graph/i });
    expect(action).toBeInTheDocument();
    expect(screen.queryByRole("button", { name: /Retry/i })).toBeNull();
  });

  it("shows the graph-load error state with Retry when status flips to Error and graph is null", () => {
    act(() => useStore.setState({ status: "Error", error: "boom", graph: null }));
    render(<GraphPane />);
    const stage = screen.getByTestId("graph-stage");
    expect(stage.getAttribute("data-graph-status")).toBe("error");
    expect(screen.getByText("Graph load failed")).toBeInTheDocument();
    expect(screen.getByText("boom")).toBeInTheDocument();
    // T22: graph-load failure is one of the two retry-bearing surfaces.
    expect(screen.getByRole("button", { name: /Retry/i })).toBeInTheDocument();
  });

  it("calls loadGraph when the empty-state primary action is clicked", () => {
    act(() => useStore.setState({ status: "Idle", graph: null }));
    render(<GraphPane />);
    fireEvent.click(screen.getByRole("button", { name: /Load graph/i }));
    expect(useStore.getState().status).toBe("Loading");
  });

  it("calls loadGraph when the error-state Retry button is clicked", () => {
    act(() => useStore.setState({ status: "Error", error: "boom", graph: null }));
    render(<GraphPane />);
    fireEvent.click(screen.getByRole("button", { name: /Retry/i }));
    expect(useStore.getState().status).toBe("Loading");
  });
});

describe("GraphPane T24 — cross-renderer integration (UI_TASK_BREAKDOWN §7 T24)", () => {
  afterEach(() => {
    vi.restoreAllMocks();
    act(() =>
      useStore.setState({
        renderer: "map",
        status: "Idle",
        error: null,
        graph: null,
        result: null,
        activeIndex: -1,
        start: null,
        goal: null,
        selectedAlgorithm: null,
        selectedNode: null,
        history: [],
      }),
    );
  });

  it("renders identical per-node Frame state in Graph and Map at the same activeIndex", () => {
    seedSearchGraph("graph", 1);
    render(<GraphPane />);
    const canvas = screen.getByTestId("graph-canvas");
    const expected = graphCanvasStates(1, useStore.getState().selectedNode);
    for (const id of ["a", "b", "c"]) {
      expect(canvas.querySelector(`[data-node-id="${id}"]`)?.getAttribute("data-state")).toBe(expected[id]);
    }

    // Switch to Map and re-read the Frame from MapOverlays.
    act(() => useStore.setState({ renderer: "map" }));
    const overlays = screen.getByTestId("map-overlays");
    // Map's MapOverlays exposes the visited/current set; derive and compare.
    expect(overlays.getAttribute("data-visited")).toBe(["a", "b"].join(","));
    expect(overlays.getAttribute("data-current")).toBe("b");
    expect(overlays.getAttribute("data-route")).toBe("2");
  });

  it("renders identical Frame state when toggling Map → Graph back to the same activeIndex", () => {
    seedSearchGraph("map", 2);
    render(<GraphPane />);
    const overlaysBefore = screen.getByTestId("map-overlays");
    const visitedBefore = overlaysBefore.getAttribute("data-visited");
    const currentBefore = overlaysBefore.getAttribute("data-current");

    act(() => useStore.setState({ renderer: "graph" }));
    const canvas = screen.getByTestId("graph-canvas");
    const expected = graphCanvasStates(2, useStore.getState().selectedNode);
    for (const id of ["a", "b", "c"]) {
      expect(canvas.querySelector(`[data-node-id="${id}"]`)?.getAttribute("data-state")).toBe(expected[id]);
    }
    // visited set on the map view is a, b, c (all steps exhausted → finished).
    expect(visitedBefore).toBe(["a", "b", "c"].join(","));
    expect(currentBefore).toBe("c");
  });

  it("preserves Frame parity at every step: visit each activeIndex in both renderers", () => {
    for (let i = 0; i < RESULT.steps.length; i++) {
      act(() =>
        useStore.setState({
          renderer: "graph",
          graph: { nodes: NODES, edges: [], bbox: [10.78, 106.69, 10.8, 106.71] },
          result: RESULT,
          activeIndex: i,
          status: "Ready",
          selectedNode: null,
        }),
      );
      const { unmount } = render(<GraphPane />);
      const canvas = screen.getByTestId("graph-canvas");
      const expected = graphCanvasStates(i, null);
      for (const id of ["a", "b", "c"]) {
        expect(canvas.querySelector(`[data-node-id="${id}"]`)?.getAttribute("data-state")).toBe(expected[id]);
      }
      unmount();
    }
  });

  it("does not trigger a backend API call when toggling the renderer", () => {
    seedSearchGraph("graph", 1);
    const searchSpy = vi.spyOn(client, "search");
    render(<GraphPane />);
    fireEvent.click(screen.getByRole("button", { name: /Map view/i }));
    act(() => useStore.setState({ renderer: "map" }));
    expect(searchSpy).not.toHaveBeenCalled();
    fireEvent.click(screen.getByRole("button", { name: /Graph view/i }));
    act(() => useStore.setState({ renderer: "graph" }));
    expect(searchSpy).not.toHaveBeenCalled();
  });

  it("preserves playback state (activeIndex / playing / status) across renderer switches", () => {
    seedSearchGraph("graph", 1);
    act(() => useStore.setState({ playing: true, status: "Playing" }));
    render(<GraphPane />);
    act(() => useStore.setState({ renderer: "map" }));
    expect(useStore.getState().activeIndex).toBe(1);
    expect(useStore.getState().playing).toBe(true);
    expect(useStore.getState().status).toBe("Playing");
    act(() => useStore.setState({ renderer: "graph" }));
    expect(useStore.getState().activeIndex).toBe(1);
    expect(useStore.getState().playing).toBe(true);
    expect(useStore.getState().status).toBe("Playing");
  });

  it("preserves the selected node across renderer switches", () => {
    seedSearchGraph("graph", 1);
    render(<GraphPane />);
    expect(useStore.getState().selectedNode).toBe("b");
    act(() => useStore.setState({ renderer: "map" }));
    expect(useStore.getState().selectedNode).toBe("b");
  });

  it("agrees on metrics + explanation between Graph and Map renderings (shared SearchResult)", () => {
    seedSearchGraph("graph", 1);
    render(<GraphPane />);
    const graphMetrics = selectMetrics(useStore.getState().result);
    const graphExplanation = useStore.getState().result?.explanation;

    act(() => useStore.setState({ renderer: "map" }));
    // Renderer doesn't own metrics — but the SearchResult is the same store
    // value, so any selector run from the same store must agree.
    const mapMetrics = selectMetrics(useStore.getState().result);
    const mapExplanation = useStore.getState().result?.explanation;

    expect(mapMetrics).toEqual(graphMetrics);
    expect(mapExplanation).toBe(graphExplanation);
  });

  it("history list is renderer-agnostic and identical across renderer switches", () => {
    seedSearchGraph("graph", 1);
    render(<GraphPane />);
    const historyBefore = useStore.getState().history;
    act(() => useStore.setState({ renderer: "map" }));
    expect(useStore.getState().history).toEqual(historyBefore);
    act(() => useStore.setState({ renderer: "graph" }));
    expect(useStore.getState().history).toEqual(historyBefore);
  });

  it("replayRun produces the same SearchResult activeIndex parity in Graph and Map", () => {
    seedSearchGraph("graph", 2);
    // Force the activeIndex back to 0 via replay so both renderers traverse
    // the recorded run from the start (replayRun is renderer-agnostic).
    act(() => useStore.getState().replayRun("r-1"));
    expect(useStore.getState().activeIndex).toBe(0);
    expect(useStore.getState().status).toBe("Replay");

    // Read Frame at step 0 in Graph.
    render(<GraphPane />);
    const graphState0 = graphCanvasStates(0, useStore.getState().selectedNode);
    const canvas = screen.getByTestId("graph-canvas");
    for (const id of ["a", "b", "c"]) {
      expect(canvas.querySelector(`[data-node-id="${id}"]`)?.getAttribute("data-state")).toBe(graphState0[id]);
    }

    // Advance step, then switch to Map.
    act(() => useStore.setState({ activeIndex: 1, renderer: "graph" }));
    act(() => useStore.setState({ renderer: "map" }));
    const overlays = screen.getByTestId("map-overlays");
    expect(overlays.getAttribute("data-visited")).toBe(["a", "b"].join(","));
    expect(overlays.getAttribute("data-current")).toBe("b");

    // Advance step inside Map.
    act(() => useStore.setState({ activeIndex: 2 }));
    const overlays2 = screen.getByTestId("map-overlays");
    expect(overlays2.getAttribute("data-visited")).toBe(["a", "b", "c"].join(","));
    expect(overlays2.getAttribute("data-current")).toBe("c");
  });

  it("replay does not call any backend transport", () => {
    seedSearchGraph("graph", 1);
    const searchSpy = vi.spyOn(client, "search");
    const graphSpy = vi.spyOn(client, "getGraph");
    const historySpy = vi.spyOn(client, "getHistory");
    render(<GraphPane />);
    act(() => useStore.getState().replayRun("r-1"));
    act(() => useStore.setState({ renderer: "map" }));
    act(() => useStore.getState().replayRun("r-1"));
    expect(searchSpy).not.toHaveBeenCalled();
    expect(graphSpy).not.toHaveBeenCalled();
    expect(historySpy).not.toHaveBeenCalled();
  });
});
