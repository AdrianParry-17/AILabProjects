import { act, useState } from "react";
import { fireEvent, render, screen } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";

import { NodePicker, type NodeOption } from "./index";

const NODES: NodeOption[] = [
  { id: "mkt-1", name: "Ben Thanh Market", keywords: "market Phuong 1 downtown" },
  { id: "mkt-2", name: "Binh Tay Market", keywords: "market district 6" },
  { id: "wh-1", name: "Saigon Port Warehouse", keywords: "warehouse port road_class:primary" },
  { id: "hosp-1", name: "City General Hospital", keywords: "hospital Nguyen Tri Phuong" },
];

describe("NodePicker (T18)", () => {
  it("renders with the spec placeholder", () => {
    render(<NodePicker label="Start" value={null} options={NODES} onChange={() => {}} />);
    expect(screen.getByPlaceholderText("Choose a location…")).toBeInTheDocument();
  });

  it("caps visible results at 8 when the input is empty", () => {
    render(<NodePicker label="Start" value={null} options={NODES} onChange={() => {}} />);
    fireEvent.focus(screen.getByRole("combobox"));
    const options = screen.getAllByRole("option");
    expect(options.length).toBeLessThanOrEqual(8);
  });

  it("filters by name using substring matching", () => {
    render(<NodePicker label="Start" value={null} options={NODES} onChange={() => {}} />);
    const input = screen.getByRole("combobox");
    fireEvent.focus(input);
    fireEvent.change(input, { target: { value: "ben" } });
    const options = screen.getAllByRole("option");
    expect(options).toHaveLength(1);
    expect(options[0]).toHaveTextContent("Ben Thanh Market");
  });

  it("filters by id substring (T18 id match)", () => {
    render(<NodePicker label="Start" value={null} options={NODES} onChange={() => {}} />);
    const input = screen.getByRole("combobox");
    fireEvent.focus(input);
    fireEvent.change(input, { target: { value: "hosp-1" } });
    const options = screen.getAllByRole("option");
    expect(options).toHaveLength(1);
    expect(options[0]).toHaveTextContent("City General Hospital");
  });

  it("filters by keyword metadata (street/POI)", () => {
    render(<NodePicker label="Start" value={null} options={NODES} onChange={() => {}} />);
    const input = screen.getByRole("combobox");
    fireEvent.focus(input);
    fireEvent.change(input, { target: { value: "phuong" } });
    const options = screen.getAllByRole("option");
    expect(options.length).toBeGreaterThanOrEqual(1);
    expect(options.some((o) => o.textContent?.includes("Hospital") || o.textContent?.includes("Ben Thanh"))).toBe(true);
  });

  it("accepts fuzzy subsequence matching", () => {
    render(<NodePicker label="Start" value={null} options={NODES} onChange={() => {}} />);
    const input = screen.getByRole("combobox");
    fireEvent.focus(input);
    // "bthnt" matches "Ben Thanh" as a subsequence (b…t…h…n…t… — yes in order).
    fireEvent.change(input, { target: { value: "bthnt" } });
    const options = screen.getAllByRole("option");
    expect(options).toHaveLength(1);
    expect(options[0]).toHaveTextContent("Ben Thanh Market");
  });

  it("shows an empty-state row when nothing matches", () => {
    render(<NodePicker label="Start" value={null} options={NODES} onChange={() => {}} />);
    const input = screen.getByRole("combobox");
    fireEvent.focus(input);
    fireEvent.change(input, { target: { value: "zzzqqq" } });
    expect(screen.getByText(/No matching locations/i)).toBeInTheDocument();
  });

  it("captures a freshly-chosen value into session recents", () => {
    function Harness(): JSX.Element {
      const [value, setValue] = useState<string | null>(null);
      return <NodePicker label="Start" value={value} options={NODES} onChange={setValue} />;
    }
    const { container } = render(<Harness />);
    const input = container.querySelector('[role="combobox"]') as HTMLInputElement;
    act(() => {
      fireEvent.focus(input);
      fireEvent.change(input, { target: { value: "ben" } });
    });
    act(() => {
      fireEvent.mouseDown(screen.getByRole("option", { name: /Ben Thanh Market/i }));
    });
    // After the pick, the recents effect has fired (value changed). Clear the
    // input to reopen the menu — the recent group exposes the chosen option.
    act(() => {
      fireEvent.input(input, { target: { value: "" } });
    });
    expect(screen.getByRole("button", { name: /Ben Thanh Market/i })).toBeInTheDocument();
  });

  it("clears the selection via the clear button", () => {
    const onChange = vi.fn();
    render(<NodePicker label="Start" value="mkt-1" options={NODES} onChange={onChange} />);
    fireEvent.click(screen.getByRole("button", { name: /Clear Start/i }));
    expect(onChange).toHaveBeenCalledWith(null);
  });

  it("ignores keyboard interactions when disabled", () => {
    const onChange = vi.fn();
    render(<NodePicker label="Start" value={null} options={NODES} disabled onChange={onChange} />);
    const input = screen.getByRole("combobox");
    fireEvent.focus(input);
    fireEvent.change(input, { target: { value: "ben" } });
    fireEvent.keyDown(input, { key: "Enter" });
    expect(onChange).not.toHaveBeenCalled();
  });
});
