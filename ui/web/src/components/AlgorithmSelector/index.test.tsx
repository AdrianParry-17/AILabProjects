import { fireEvent, render, screen } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";

import { AlgorithmSelector } from "./index";

const CATALOG = [
  { id: "bfs", label: "Breadth-First Search", mock: false },
  { id: "dfs", label: "Depth-First Search", mock: true },
];

describe("AlgorithmSelector", () => {
  it("renders exactly the catalog entries, no hardcoded names", () => {
    render(<AlgorithmSelector catalog={CATALOG} value="bfs" onChange={() => {}} />);
    fireEvent.click(screen.getByRole("combobox"));
    const options = screen.getAllByRole("option");
    expect(options.map((o) => o.textContent)).toEqual([
      expect.stringContaining("Breadth-First Search"),
      expect.stringContaining("Depth-First Search"),
    ]);
  });

  it("tags only mock providers with (mock)", () => {
    render(<AlgorithmSelector catalog={CATALOG} value="bfs" onChange={() => {}} />);
    fireEvent.click(screen.getByRole("combobox"));
    const options = screen.getAllByRole("option");
    expect(options[0]).not.toHaveTextContent("(mock)");
    expect(options[1]).toHaveTextContent("(mock)");
  });

  it("selects with keyboard arrows and Enter", () => {
    const onChange = vi.fn();
    render(<AlgorithmSelector catalog={CATALOG} value="bfs" onChange={onChange} />);
    const trigger = screen.getByRole("combobox");
    fireEvent.keyDown(trigger, { key: "ArrowDown" });
    fireEvent.keyDown(trigger, { key: "Enter" });
    expect(onChange).toHaveBeenCalledWith("dfs");
  });

  it("ignores interactions when disabled", () => {
    const onChange = vi.fn();
    render(<AlgorithmSelector catalog={CATALOG} value="bfs" disabled onChange={onChange} />);
    fireEvent.keyDown(screen.getByRole("combobox"), { key: "ArrowDown" });
    fireEvent.keyDown(screen.getByRole("combobox"), { key: "Enter" });
    expect(onChange).not.toHaveBeenCalled();
  });
});