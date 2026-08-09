import { fireEvent, render, screen } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";

import { formatTimeAgo } from "../../lib/format";
import type { HistoryRun } from "../../api/types";
import { HistoryPanel } from "./index";

const RUNS: HistoryRun[] = [
  {
    id: "r-1",
    algorithm: "bfs",
    start: "a",
    goal: "z",
    source: "real",
    created_at: "2024-01-01T00:00:00Z",
    hops: 4,
  },
  {
    id: "r-2",
    algorithm: "dfs",
    start: "b",
    goal: "z",
    source: "mock",
    created_at: "2024-01-02T00:00:00Z",
    hops: 7,
  },
];

describe("HistoryPanel", () => {
  it("renders each run with algorithm, route, hops and time ago", () => {
    render(<HistoryPanel history={RUNS} onReplay={() => {}} />);
    expect(screen.getByText("bfs")).toBeInTheDocument();
    expect(screen.getByText("dfs")).toBeInTheDocument();
    expect(screen.getByText("a → z")).toBeInTheDocument();
    expect(screen.getByText("4 hops")).toBeInTheDocument();
    expect(screen.getAllByText(formatTimeAgo("2024-01-01T00:00:00Z")).length).toBeGreaterThan(0);
  });

  it("tags mock runs with a badge", () => {
    render(<HistoryPanel history={RUNS} onReplay={() => {}} />);
    expect(screen.getByText("mock")).toBeInTheDocument();
  });

  it("resolves the algorithm name via labelFor", () => {
    render(
      <HistoryPanel
        history={RUNS}
        labelFor={(id) => (id === "bfs" ? "Breadth-First Search" : id)}
        onReplay={() => {}}
      />,
    );
    expect(screen.getByText("Breadth-First Search")).toBeInTheDocument();
  });

  it("exposes a replay aria-label on each row", () => {
    render(<HistoryPanel history={RUNS} onReplay={() => {}} />);
    const rows = screen.getAllByRole("button");
    expect(rows).toHaveLength(RUNS.length);
    expect(rows[0]).toHaveAccessibleName("Replay bfs run from a to z");
  });

  it("marks the active row with aria-current", () => {
    render(<HistoryPanel history={RUNS} activeRunId="r-2" onReplay={() => {}} />);
    expect(screen.getByRole("button", { name: "Replay dfs run from b to z" })).toHaveAttribute(
      "aria-current",
      "true",
    );
  });

  it("renders a skeleton while loading instead of the empty state", () => {
    render(<HistoryPanel history={[]} loading onReplay={() => {}} />);
    expect(screen.getByRole("status", { name: "Loading history" })).toBeInTheDocument();
    expect(screen.queryByText("No searches yet")).not.toBeInTheDocument();
  });

  it("calls onReplay with the clicked run id", () => {
    const onReplay = vi.fn();
    render(<HistoryPanel history={RUNS} onReplay={onReplay} />);
    fireEvent.click(screen.getAllByRole("button")[0]);
    expect(onReplay).toHaveBeenCalledWith("r-1");
  });

  it("renders the empty state when there are no runs", () => {
    render(<HistoryPanel history={[]} onReplay={() => {}} />);
    expect(screen.getByText("No searches recorded yet.")).toBeInTheDocument();
  });
});

describe("HistoryPanel T22 — inline error indicator (UI_TASK_BREAKDOWN §7 T22)", () => {
  it("shows an inline error indicator (NO retry) when historyError is set", () => {
    render(<HistoryPanel history={[]} historyError="Could not load history." onReplay={() => {}} />);
    expect(screen.getByTestId("history-error")).toBeInTheDocument();
    expect(screen.getByText("Could not load history.")).toBeInTheDocument();
    // T22: history failure is NOT a retry-bearing surface.
    expect(screen.queryByRole("button", { name: /Retry/i })).toBeNull();
  });

  it("prefers an inline error over the empty state when both could apply", () => {
    render(<HistoryPanel history={[]} historyError="boom" onReplay={() => {}} />);
    expect(screen.getByTestId("history-error")).toBeInTheDocument();
    expect(screen.queryByText(/No searches recorded yet/i)).toBeNull();
  });

  it("prefers the loading skeleton over the inline error when loading and historyError are both set", () => {
    render(<HistoryPanel history={[]} loading historyError="boom" onReplay={() => {}} />);
    expect(screen.getByRole("status", { name: "Loading history" })).toBeInTheDocument();
    expect(screen.queryByTestId("history-error")).toBeNull();
  });
});
