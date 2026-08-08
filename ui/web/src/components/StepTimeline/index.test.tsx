import { act, render, screen, fireEvent } from "@testing-library/react";
import { afterEach, describe, expect, it, vi } from "vitest";

import { useStore } from "../../state/store";
import type { SearchResult } from "../../api/types";
import { StepTimeline } from "./index";

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

const RESET = {
  result: null,
  status: "Idle",
  activeIndex: -1,
  playing: false,
  speed: 1,
} as const;

describe("StepTimeline store actions (play/pause/resume/step/finish)", () => {
  afterEach(() => {
    vi.restoreAllMocks();
    act(() => useStore.setState(RESET));
  });

  it("play -> pause -> resume transitions Playing <-> Paused", () => {
    act(() => useStore.setState({ result: makeResult(4), status: "Ready", activeIndex: 0, playing: false }));
    act(() => useStore.getState().play());
    expect(useStore.getState().status).toBe("Playing");
    expect(useStore.getState().playing).toBe(true);
    act(() => useStore.getState().pause());
    expect(useStore.getState().status).toBe("Paused");
    act(() => useStore.getState().play());
    expect(useStore.getState().status).toBe("Playing");
  });

  it("advanceStep is monotonic and sets Finished at the last step", () => {
    act(() => useStore.setState({ result: makeResult(3), status: "Playing", activeIndex: 0, playing: true }));
    act(() => useStore.getState().advanceStep());
    expect(useStore.getState().activeIndex).toBe(1);
    act(() => useStore.getState().advanceStep());
    expect(useStore.getState().activeIndex).toBe(2);
    expect(useStore.getState().status).toBe("Finished");
    expect(useStore.getState().playing).toBe(false);
    // further calls are stable at the end
    act(() => useStore.getState().advanceStep());
    expect(useStore.getState().activeIndex).toBe(2);
    expect(useStore.getState().status).toBe("Finished");
  });

  it("restart resets to the first step and Ready", () => {
    act(() => useStore.setState({ result: makeResult(3), status: "Paused", activeIndex: 2, playing: false }));
    act(() => useStore.getState().restart());
    expect(useStore.getState().activeIndex).toBe(0);
    expect(useStore.getState().status).toBe("Ready");
  });

  it("stepTo is a no-op while Playing", () => {
    act(() => useStore.setState({ result: makeResult(4), status: "Playing", activeIndex: 0, playing: true }));
    act(() => useStore.getState().stepTo(2));
    expect(useStore.getState().activeIndex).toBe(0);
  });

  it("stepTo works in Ready and clamps, marking Finished at the last index", () => {
    act(() => useStore.setState({ result: makeResult(4), status: "Ready", activeIndex: 0, playing: false }));
    act(() => useStore.getState().stepTo(5));
    expect(useStore.getState().activeIndex).toBe(3);
    expect(useStore.getState().status).toBe("Finished");
  });
});

describe("StepTimeline component", () => {
  afterEach(() => {
    vi.restoreAllMocks();
    act(() => useStore.setState(RESET));
  });

  it("renders nothing (null) when there are no steps", () => {
    act(() => useStore.setState({ result: null, status: "Ready", activeIndex: -1 }));
    const { container } = render(<StepTimeline />);
    expect(container).toBeEmptyDOMElement();
  });

  it("renders counter, slider and controls once a result exists", () => {
    act(() => useStore.setState({ result: makeResult(3), status: "Ready", activeIndex: 0, playing: false }));
    render(<StepTimeline />);
    expect(screen.getByText("1 / 3")).toBeInTheDocument();
    expect(screen.getByRole("slider")).toBeInTheDocument();
    expect(screen.getByRole("button", { name: /Play/i })).toBeInTheDocument();
  });

  it("scrubs to a step via the slider (stepTo/Ready)", () => {
    act(() => useStore.setState({ result: makeResult(3), status: "Ready", activeIndex: 0, playing: false }));
    render(<StepTimeline />);
    fireEvent.change(screen.getByRole("slider"), { target: { value: "2" } });
    expect(useStore.getState().activeIndex).toBe(2);
    expect(screen.getByText("3 / 3")).toBeInTheDocument();
  });

  it("renders a single-step result without crashing (no NaN% fill)", () => {
    act(() => useStore.setState({ result: makeResult(1), status: "Ready", activeIndex: 0, playing: false }));
    render(<StepTimeline />);
    expect(screen.getByText("1 / 1")).toBeInTheDocument();
    const slider = screen.getByRole("slider") as HTMLInputElement;
    // Guard: --fill must be a finite percentage (regression guard for F7).
    expect(slider.style.getPropertyValue("--fill")).not.toMatch(/NaN/i);
  });
});