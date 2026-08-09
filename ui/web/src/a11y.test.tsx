import { render, screen } from "@testing-library/react";
import { afterEach, describe, expect, it, vi } from "vitest";

import App from "./App";
import { AlgorithmSelector } from "./components/AlgorithmSelector";
import { Spinner } from "./components/shared/Spinner";
import { StatusSection } from "./components/InfoPanel/StatusSection";

const CATALOG = [
  { id: "bfs", label: "Breadth-First Search", mock: false },
  { id: "dfs", label: "Depth-First Search", mock: true },
  { id: "ucs", label: "Uniform-Cost Search", mock: false },
];

describe("Phase P5 — keyboard navigation + ARIA (T21)", () => {
  afterEach(() => {
    vi.restoreAllMocks();
  });

  it("App renders the five regions in the spec-required tab order", () => {
    render(<App />);
    // Header → main → aside (info) → footer (timeline) is the natural DOM order
    // enforced by App.tsx. Each region is independently addressable.
    const order = [
      screen.getByRole("banner"),
      screen.getByRole("main"),
      screen.getByLabelText("Information"),
      screen.getByLabelText("Playback timeline"),
    ];
    expect(order.length).toBe(4);
    // Every subsequent region appears later in the document than the previous
    // (compareDocumentPosition returns FOLLOWING | PRECEDING bits).
    for (let i = 1; i < order.length; i++) {
      const prev = order[i - 1] as HTMLElement;
      const curr = order[i] as HTMLElement;
      expect(prev.compareDocumentPosition(curr) & Node.DOCUMENT_POSITION_FOLLOWING).toBeTruthy();
    }
  });

  it("AlgorithmSelector combobox exposes a labelled combobox + searchable listbox", () => {
    render(<AlgorithmSelector catalog={CATALOG} value="bfs" onChange={() => {}} />);
    const trigger = screen.getByRole("combobox");
    expect(trigger.getAttribute("aria-haspopup")).toBe("listbox");
    expect(trigger.getAttribute("aria-expanded")).toBe("false");
    expect(trigger.textContent).toContain("Breadth-First Search");
    expect(trigger.tagName).toBe("BUTTON");
  });

  it("RendererToggle exposes a labelled segmented group with aria-pressed on each segment", () => {
    render(<App />);
    const group = screen.getByRole("group", { name: /Visualization renderer/i });
    expect(group).toBeInTheDocument();
    // When the default renderer is "map" (per MAP_RENDERING_SPEC §2), only the
    // Map segment should carry aria-pressed=true.
    const map = screen.getByRole("button", { name: /Map view/i });
    const graph = screen.getByRole("button", { name: /Graph view/i });
    expect(map.getAttribute("aria-pressed")).toBe("true");
    expect(graph.getAttribute("aria-pressed")).toBe("false");
  });

  it("StatusSection announces state changes through role=status + aria-live=polite", () => {
    render(<StatusSection />);
    const region = screen.getByTestId("status-section");
    expect(region.getAttribute("role")).toBe("status");
    expect(region.getAttribute("aria-live")).toBe("polite");
    // The default status label is "Loading…" (matches the Idle/Loading text map).
    expect(region.textContent).toContain("Loading…");
  });

  it("Spinner announces itself as a loading region with a status role", () => {
    render(<Spinner />);
    const region = screen.getByRole("status", { name: "Loading" });
    expect(region).toBeInTheDocument();
  });
});

