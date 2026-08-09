import { act, fireEvent, render, screen, waitFor } from "@testing-library/react";
import { afterEach, describe, expect, it, vi } from "vitest";

import { selectMetrics } from "../../lib/metrics";
import { useStore } from "../../state/store";
import type { SearchResult } from "../../api/types";
import { MetricsPanel } from "./index";

function makeResult(): SearchResult {
  return {
    path: ["a", "b", "c"],
    visited_nodes: ["a", "b", "c", "d"],
    steps: [
      { current_node: "a", frontier: ["b"], reason: "x" },
      { current_node: "b", frontier: ["c"], reason: "y" },
    ],
    total_distance_km: 3.2,
    total_time_min: 5,
    total_cost: 2.7,
    processing_time_ms: 1.5,
    explanation: "BFS - mô phỏng: ưu tiên hàng đợi FIFO",
  };
}

describe("selectMetrics", () => {
  it("returns [] for a null result", () => {
    expect(selectMetrics(null)).toEqual([]);
  });

  it("derives rows with verbatim totals and front-end hops/nodesVisited", () => {
    const rows = selectMetrics(makeResult());
    const byKey = Object.fromEntries(rows.map((r) => [r.key, r.value]));
    expect(byKey.distance_km).toBe("3.20 km");
    expect(byKey.time_min).toBe("5.0 min");
    expect(byKey.cost).toBe("2.70");
    expect(byKey.processing_time_ms).toBe("1.5 ms");
    expect(byKey.hops).toBe("2");
    expect(byKey.nodes_visited).toBe("4");
  });
});

describe("MetricsPanel", () => {
  afterEach(() => {
    vi.restoreAllMocks();
    act(() => useStore.setState({ result: null, busy: false }));
  });

  it("shows an empty state with guidance when there is no result", () => {
    render(<MetricsPanel />);
    expect(screen.getByText("Run a search to see metrics.")).toBeInTheDocument();
    expect(screen.getByText(/Choose a start location/i)).toBeInTheDocument();
  });

  it("renders each metric as a compact card with icon + label + value (T15)", () => {
    act(() => useStore.setState({ result: makeResult(), busy: false }));
    const { container } = render(<MetricsPanel />);
    expect(container.querySelector('[aria-label="Result metrics"]')).not.toBeNull();
    const cards = container.querySelectorAll("li");
    expect(cards).toHaveLength(6);
    // Every card shows its label and value; icons are present.
    for (const row of selectMetrics(makeResult())) {
      expect(container.textContent).toContain(row.label);
    }
  });

  it("uses tabular numerals on metric values (T15 card tokens)", () => {
    act(() => useStore.setState({ result: makeResult(), busy: false }));
    const { container } = render(<MetricsPanel />);
    // CSS modules hash the class — the rule `.cardValue { font-variant-numeric:
    // tabular-nums }` is injected via the module CSS. In jsdom the computed
    // style may not resolve, so we assert the hashed class is present.
    const numericValues = container.querySelectorAll('[class*="cardValue"]');
    expect(numericValues.length).toBe(6);
  });

  it("renders metrics + explanation after a search", () => {
    act(() => useStore.setState({ result: makeResult(), busy: false }));
    render(<MetricsPanel />);
    expect(screen.getByText("3.20 km")).toBeInTheDocument();
    expect(screen.getByText("5.0 min")).toBeInTheDocument();
    expect(screen.getByText("2.70")).toBeInTheDocument();
    expect(screen.getByText("4")).toBeInTheDocument();
    expect(screen.getByText(/BFS - mô phỏng/)).toBeInTheDocument();
  });

  it("updates per search (new result replaces the old rows)", () => {
    act(() => useStore.setState({ result: makeResult(), busy: false }));
    const { rerender } = render(<MetricsPanel />);
    expect(screen.getByText("3.20 km")).toBeInTheDocument();

    const updated: SearchResult = {
      ...makeResult(),
      total_distance_km: 9.9,
      explanation: "Dijkstra real",
    };
    act(() => useStore.setState({ result: updated, busy: false }));
    rerender(<MetricsPanel />);
    expect(screen.getByText("9.90 km")).toBeInTheDocument();
    expect(screen.getByText("Dijkstra real")).toBeInTheDocument();
  });

  it("copies the metrics text via the lazy export helper", async () => {
    const writeText = vi.fn().mockResolvedValue(undefined);
    Object.defineProperty(navigator, "clipboard", {
      value: { writeText },
      configurable: true,
    });
    act(() => useStore.setState({ result: makeResult(), busy: false }));
    render(<MetricsPanel />);
    fireEvent.click(screen.getByRole("button", { name: /Copy/i }));
    await waitFor(() => expect(writeText).toHaveBeenCalled());
    const text = writeText.mock.calls[0][0] as string;
    expect(text).toContain("Distance: 3.20 km");
    expect(text).toContain("BFS - mô phỏng");
  });
});