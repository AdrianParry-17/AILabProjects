import { act, render, screen } from "@testing-library/react";
import { afterEach, describe, expect, it, vi } from "vitest";

import { useStore } from "../../state/store";
import { InfoPanel } from "./index";

describe("InfoPanel", () => {
  afterEach(() => {
    vi.restoreAllMocks();
    act(() =>
      useStore.setState({
        status: "Idle",
        source: null,
        error: null,
        searchError: null,
        graph: null,
        result: null,
        history: [],
        historyLoading: false,
        replayRunId: null,
        replay: false,
      }),
    );
  });

  it("renders Status, Metrics and History sections with region role", () => {
    act(() => useStore.setState({ status: "Ready" }));
    const { container } = render(<InfoPanel />);
    expect(container.querySelector('[data-testid="info-panel"]')).not.toBeNull();
    expect(container.querySelector('[data-testid="info-panel"]')!.getAttribute("role")).toBe("region");
    expect(screen.getByText("Status")).toBeInTheDocument();
    expect(screen.getByText("Metrics")).toBeInTheDocument();
    expect(screen.getByText("History")).toBeInTheDocument();
  });

  it("renders the live status text from the store", () => {
    act(() => useStore.setState({ status: "Ready" }));
    render(<InfoPanel />);
    expect(screen.getByText("Ready")).toBeInTheDocument();
  });

  it("does not render search controls inside the panel", () => {
    act(() => useStore.setState({ status: "Ready" }));
    const { container } = render(<InfoPanel />);
    expect(container.querySelector('[aria-label="Search configuration"]')).toBeNull();
    expect(screen.queryByLabelText("Start Location")).not.toBeInTheDocument();
    expect(screen.queryByLabelText("Destination")).not.toBeInTheDocument();
    expect(screen.queryByRole("button", { name: /Run Search/i })).not.toBeInTheDocument();
  });

  it("renders the Retry button only when the graph failed to load", () => {
    act(() => useStore.setState({ status: "Error", error: "boom", graph: null }));
    render(<InfoPanel />);
    expect(screen.getByText("boom")).toBeInTheDocument();
    expect(screen.getByRole("button", { name: /Retry/i })).toBeInTheDocument();
  });

  it("hides history and shows a hint while the app is still loading", () => {
    act(() => useStore.setState({ status: "Idle" }));
    render(<InfoPanel />);
    expect(screen.queryByText("No searches yet")).not.toBeInTheDocument();
    expect(screen.getByText(/Run a search to record history/i)).toBeInTheDocument();
  });
});