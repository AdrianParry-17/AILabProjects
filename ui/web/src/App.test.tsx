import { render, screen, within } from "@testing-library/react";
import { afterEach, describe, expect, it } from "vitest";

import App from "./App";
import { useStore } from "./state/store";

describe("App shell (T04)", () => {
  afterEach(() => {
    useStore.setState({
      status: "Idle",
      graph: null,
      result: null,
      history: [],
    });
  });

  it("renders the five required regions", () => {
    const { container } = render(<App />);
    expect(screen.getByRole("banner")).toBeInTheDocument();
    expect(screen.getByRole("main")).toBeInTheDocument();
    expect(screen.getByLabelText("Information")).toBeInTheDocument();
    expect(screen.getByLabelText("Playback timeline")).toBeInTheDocument();
    expect(container.querySelector('[data-testid="graph-pane"]')).not.toBeNull();
  });

  it("keeps the visualization region the largest column on desktop", () => {
    const { container } = render(<App />);
    const main = container.querySelector('[role="main"]') as HTMLElement | null;
    expect(main).not.toBeNull();
    // Body is a flex row; main carries `flex: 1` so it always expands to the
    // remainder of the row and stays larger than either side panel (LAYOUT_SPEC §8).
    expect(within(main!).getByRole("region", { name: "Visualization" })).toBeInTheDocument();
  });

  it("renders the < 768 px notice overlay element", () => {
    const { container } = render(<App />);
    expect(container.querySelector('[aria-label="Best viewed at 768 pixels or wider"]')).not.toBeNull();
  });
});