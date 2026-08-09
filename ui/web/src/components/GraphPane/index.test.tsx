import { act, fireEvent, render, screen } from "@testing-library/react";
import { afterEach, describe, expect, it } from "vitest";

import { useStore } from "../../state/store";
import { GraphPane } from "./index";

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
