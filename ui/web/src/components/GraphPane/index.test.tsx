import { act, render, screen } from "@testing-library/react";
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
    expect(container.querySelector('[data-testid="map-pane"]')).not.toBeNull();
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
