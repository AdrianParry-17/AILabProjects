import { act, render, screen } from "@testing-library/react";
import { fireEvent } from "@testing-library/react";
import { afterEach, describe, expect, it, vi } from "vitest";

import { client } from "../../api/client";
import { useStore } from "../../state/store";
import { RendererToggle } from "./index";

describe("RendererToggle (T08)", () => {
  afterEach(() => {
    vi.restoreAllMocks();
    act(() => useStore.setState({ renderer: "map" }));
  });

  it("renders two mutually exclusive options with the active one pressed", () => {
    render(<RendererToggle />);
    const group = screen.getByRole("group", { name: /Visualization renderer/i });
    expect(group).toBeInTheDocument();
    const graph = screen.getByRole("button", { name: /Graph view/i });
    const map = screen.getByRole("button", { name: /Map view/i });
    expect(map.getAttribute("aria-pressed")).toBe("true");
    expect(graph.getAttribute("aria-pressed")).toBe("false");
  });

  it("updates store renderer when an option is clicked", () => {
    render(<RendererToggle />);
    fireEvent.click(screen.getByRole("button", { name: /Graph view/i }));
    expect(useStore.getState().renderer).toBe("graph");
    fireEvent.click(screen.getByRole("button", { name: /Map view/i }));
    expect(useStore.getState().renderer).toBe("map");
  });

  it("is a no-op when clicking the already-active option", () => {
    render(<RendererToggle />);
    // map is the default and already active; clicking again should not change
    // state nor trigger any transport call.
    const graphSpy = vi.spyOn(client, "getGraph");
    const searchSpy = vi.spyOn(client, "search");
    const historySpy = vi.spyOn(client, "getHistory");
    const catalogSpy = vi.spyOn(client, "listAlgorithms");
    fireEvent.click(screen.getByRole("button", { name: /Map view/i }));
    expect(useStore.getState().renderer).toBe("map");
    expect(graphSpy).not.toHaveBeenCalled();
    expect(searchSpy).not.toHaveBeenCalled();
    expect(historySpy).not.toHaveBeenCalled();
    expect(catalogSpy).not.toHaveBeenCalled();
  });

  it("never invokes the backend transport when switching renderer", () => {
    const graphSpy = vi.spyOn(client, "getGraph");
    const searchSpy = vi.spyOn(client, "search");
    const historySpy = vi.spyOn(client, "getHistory");
    const catalogSpy = vi.spyOn(client, "listAlgorithms");

    render(<RendererToggle />);
    fireEvent.click(screen.getByRole("button", { name: /Graph view/i }));
    fireEvent.click(screen.getByRole("button", { name: /Map view/i }));

    expect(graphSpy).not.toHaveBeenCalled();
    expect(searchSpy).not.toHaveBeenCalled();
    expect(historySpy).not.toHaveBeenCalled();
    expect(catalogSpy).not.toHaveBeenCalled();
  });

  it("reflects an externally-driven renderer change (e.g. after restore)", () => {
    render(<RendererToggle />);
    act(() => useStore.setState({ renderer: "graph" }));
    expect(screen.getByRole("button", { name: /Graph view/i }).getAttribute("aria-pressed")).toBe(
      "true",
    );
    expect(screen.getByRole("button", { name: /Map view/i }).getAttribute("aria-pressed")).toBe(
      "false",
    );
  });
});
