import { fireEvent, render, screen } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";

import { AlgorithmSelector } from "./index";

const CATALOG = [
  { id: "bfs", label: "Breadth-First Search", mock: false },
  { id: "dfs", label: "Depth-First Search", mock: true },
  { id: "ucs", label: "Uniform-Cost Search", mock: false },
];

describe("AlgorithmSelector", () => {
  it("renders exactly the catalog entries, no hardcoded names", () => {
    render(<AlgorithmSelector catalog={CATALOG} value="bfs" onChange={() => {}} />);
    fireEvent.click(screen.getByRole("combobox"));
    const options = screen.getAllByRole("option");
    expect(options.map((o) => o.textContent)).toEqual([
      expect.stringContaining("Breadth-First Search"),
      expect.stringContaining("Depth-First Search"),
      expect.stringContaining("Uniform-Cost Search"),
    ]);
  });

  it("tags only mock providers with the Mock badge (driven by catalog.mock)", () => {
    render(<AlgorithmSelector catalog={CATALOG} value="bfs" onChange={() => {}} />);
    fireEvent.click(screen.getByRole("combobox"));
    const options = screen.getAllByRole("option");
    expect(options[0]).not.toHaveTextContent("Mock");
    expect(options[1]).toHaveTextContent("Mock");
    expect(options[2]).not.toHaveTextContent("Mock");
  });

  it("filters the catalog via the search input", () => {
    render(<AlgorithmSelector catalog={CATALOG} value="bfs" onChange={() => {}} />);
    fireEvent.click(screen.getByRole("combobox"));
    const search = screen.getByPlaceholderText(/Search algorithms/i);
    fireEvent.change(search, { target: { value: "cost" } });
    const visible = screen.getAllByRole("option");
    expect(visible).toHaveLength(1);
    expect(visible[0]).toHaveTextContent("Uniform-Cost Search");
  });

  it("shows an empty-state row when no catalog entries match the query", () => {
    render(<AlgorithmSelector catalog={CATALOG} value="bfs" onChange={() => {}} />);
    fireEvent.click(screen.getByRole("combobox"));
    fireEvent.change(screen.getByPlaceholderText(/Search algorithms/i), {
      target: { value: "zzzz" },
    });
    expect(screen.getByText(/No matching algorithms/i)).toBeInTheDocument();
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

  it("shows the selected algorithm label in the trigger (T17 selection visible)", () => {
    render(<AlgorithmSelector catalog={CATALOG} value="dfs" onChange={() => {}} />);
    const trigger = screen.getByRole("combobox");
    expect(trigger).toHaveTextContent("Depth-First Search");
  });

  it("closes the dropdown when Escape is pressed in the search input and restores focus to the trigger", () => {
    render(<AlgorithmSelector catalog={CATALOG} value="bfs" onChange={() => {}} />);
    const trigger = screen.getByRole("combobox");
    fireEvent.click(trigger);
    const search = screen.getByPlaceholderText(/Search algorithms/i);
    search.focus();
    expect(document.activeElement).toBe(search);
    fireEvent.keyDown(search, { key: "Escape" });
    // Dropdown closes — the search input unmounts.
    expect(screen.queryByPlaceholderText(/Search algorithms/i)).toBeNull();
    // Trigger regains focus so keyboard users stay in the combobox.
    expect(document.activeElement).toBe(trigger);
  });

  it("keeps the trigger aria-expanded / aria-controls / listbox semantics intact across open + close", () => {
    render(<AlgorithmSelector catalog={CATALOG} value="bfs" onChange={() => {}} />);
    const trigger = screen.getByRole("combobox");
    expect(trigger.getAttribute("aria-expanded")).toBe("false");
    expect(trigger.getAttribute("aria-haspopup")).toBe("listbox");
    fireEvent.click(trigger);
    expect(trigger.getAttribute("aria-expanded")).toBe("true");
    const list = screen.getByRole("listbox", { name: /Algorithm list/i });
    expect(list).toBeInTheDocument();
    expect(trigger.getAttribute("aria-controls")).toBe(list.id);
    fireEvent.click(trigger);
    expect(trigger.getAttribute("aria-expanded")).toBe("false");
  });
});
