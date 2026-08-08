import { act, fireEvent, render, screen } from "@testing-library/react";
import { afterEach, describe, expect, it, vi } from "vitest";

import { client } from "../../api/client";
import { useStore } from "../../state/store";
import { ControlPanel } from "./index";

const FIXTURE = {
  nodes: [
    { id: "a", name: "A", latitude: 1, longitude: 2, kind: "delivery_market", attributes: {} },
    { id: "b", name: "B", latitude: 1.1, longitude: 2.1, kind: "delivery_supermarket", attributes: {} },
    { id: "c", name: "C", latitude: 1.2, longitude: 1.9, kind: "delivery_warehouse", attributes: {} },
  ],
  edges: [],
  bbox: [1, 2, 1.2, 3] as [number, number, number, number],
};

function searchFixture(): unknown {
  return {
    run: { id: "r-1", algorithm: "bfs", source: "real" },
    result: {
      path: ["a", "b"],
      visited_nodes: ["a", "b"],
      steps: [{ current_node: "a", frontier: ["b"], reason: "expand" }],
      total_distance_km: 1,
      total_time_min: 1,
      total_cost: 1,
      processing_time_ms: 1,
      explanation: "ok",
    },
    metrics: { hops: 1, nodes_visited: 2, distance_km: 1, time_min: 1, cost: 1, processing_time_ms: 1 },
    route: null,
  };
}

function readyStore(): void {
  act(() =>
    useStore.setState({
      status: "Ready",
      graph: FIXTURE,
      selectedAlgorithm: "bfs",
      busy: false,
      searchError: null,
    }),
  );
}

describe("ControlPanel", () => {
  afterEach(() => {
    vi.restoreAllMocks();
    act(() =>
      useStore.setState({
        status: "Idle",
        graph: null,
        start: null,
        goal: null,
        selectedAlgorithm: null,
        busy: false,
      }),
    );
  });

  it("keeps Run disabled until algorithm, start and goal are selected", () => {
    readyStore();
    render(<ControlPanel />);
    expect(screen.getByRole("button", { name: /Run Search/i })).toBeDisabled();
  });

  it("targets the store when start/goal are picked via the NodePickers", () => {
    readyStore();
    render(<ControlPanel />);

    fireEvent.change(screen.getByLabelText("Start Location"), { target: { value: "A" } });
    fireEvent.mouseDown(screen.getByRole("option", { name: "A" }));
    expect(useStore.getState().start).toBe("a");

    fireEvent.change(screen.getByLabelText("Destination"), { target: { value: "B" } });
    fireEvent.mouseDown(screen.getByRole("option", { name: "B" }));
    expect(useStore.getState().goal).toBe("b");
  });

  it("enables Run once algorithm, start and goal are set", () => {
    act(() => useStore.setState({ start: "a", goal: "b" }));
    readyStore();
    render(<ControlPanel />);
    expect(screen.getByRole("button", { name: /Run Search/i })).toBeEnabled();
  });

  it("disables Run when start equals goal and shows an inline alert", () => {
    act(() => useStore.setState({ start: "a", goal: "a" }));
    readyStore();
    render(<ControlPanel />);
    expect(screen.getByText(/must be different/i)).toBeInTheDocument();
    expect(screen.getByRole("button", { name: /Run Search/i })).toBeDisabled();
  });

  it("calls client.search with the chosen snake_case selection on Run", async () => {
    const searchSpy = vi.spyOn(client, "search").mockResolvedValue(searchFixture() as never);
    act(() => useStore.setState({ start: "a", goal: "b", selectedAlgorithm: "bfs" }));
    readyStore();
    render(<ControlPanel />);
    fireEvent.click(screen.getByRole("button", { name: /Run Search/i }));
    expect(searchSpy).toHaveBeenCalledWith("bfs", "a", "b", true);
  });

  it("submits on Enter when valid", async () => {
    const searchSpy = vi.spyOn(client, "search").mockResolvedValue(searchFixture() as never);
    act(() => useStore.setState({ start: "a", goal: "b", selectedAlgorithm: "bfs" }));
    readyStore();
    const { container } = render(<ControlPanel />);
    fireEvent.submit(container.querySelector("form") as HTMLFormElement);
    expect(searchSpy).toHaveBeenCalledWith("bfs", "a", "b", true);
  });

  it("stays editable after a search error so the user can fix input and retry", () => {
    act(() =>
      useStore.setState({
        status: "Error",
        graph: FIXTURE,
        start: "a",
        goal: "b",
        selectedAlgorithm: "bfs",
        busy: false,
        searchError: "SEARCH_TIMEOUT",
      }),
    );
    render(<ControlPanel />);
    expect(screen.getByLabelText("Start Location")).toBeEnabled();
    expect(screen.getByLabelText("Destination")).toBeEnabled();
    expect(screen.getByRole("button", { name: /Run Search/i })).toBeEnabled();
  });

  it("retries the search from the Error state with the corrected selection", async () => {
    const searchSpy = vi.spyOn(client, "search").mockResolvedValue(searchFixture() as never);
    act(() =>
      useStore.setState({
        status: "Error",
        graph: FIXTURE,
        start: "a",
        goal: "b",
        selectedAlgorithm: "bfs",
        busy: false,
        searchError: "SEARCH_TIMEOUT",
      }),
    );
    render(<ControlPanel />);
    fireEvent.click(screen.getByRole("button", { name: /Run Search/i }));
    expect(searchSpy).toHaveBeenCalledWith("bfs", "a", "b", true);
  });

  it("keeps the panel disabled during a graph-load error (no graph, StatusBar retry)", () => {
    act(() =>
      useStore.setState({
        status: "Error",
        graph: null,
        busy: false,
        error: "GRAPH_NOT_FOUND",
      }),
    );
    render(<ControlPanel />);
    expect(screen.getByLabelText("Start Location")).toBeDisabled();
    expect(screen.getByRole("button", { name: /Run Search/i })).toBeDisabled();
  });
});