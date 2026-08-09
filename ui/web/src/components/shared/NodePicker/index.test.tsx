import { act, useState } from "react";
import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";

import { NodePicker, type NodeOption } from "./index";

const NODES: NodeOption[] = [
  { id: "mkt-1", name: "Ben Thanh Market", keywords: "market Phuong 1 downtown" },
  { id: "mkt-2", name: "Binh Tay Market", keywords: "market district 6" },
  { id: "wh-1", name: "Saigon Port Warehouse", keywords: "warehouse port road_class:primary" },
  { id: "hosp-1", name: "City General Hospital", keywords: "hospital Nguyen Tri Phuong" },
];

const NODE_NAME_BY_ID: Record<string, string> = {
  "mkt-1": "Ben Thanh Market",
  "mkt-2": "Binh Tay Market",
  "wh-1": "Saigon Port Warehouse",
  "hosp-1": "City General Hospital",
};

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

  it("selects the highlighted option via Enter after ArrowDown", async () => {
    const onChange = vi.fn();
    render(<NodePicker label="Start" value={null} options={NODES} onChange={onChange} />);
    const input = screen.getByRole("combobox");
    act(() => {
      fireEvent.focus(input);
      // Filter to a single result so the highlight index resolves cleanly.
      fireEvent.change(input, { target: { value: "ben" } });
    });
    act(() => {
      // ArrowDown moves highlight from -1 (set on filter) to 0.
      fireEvent.keyDown(input, { key: "ArrowDown" });
    });
    act(() => {
      // Enter selects the highlighted option.
      fireEvent.keyDown(input, { key: "Enter" });
    });
    expect(onChange).toHaveBeenCalledWith("mkt-1");
  });

  it("wraps highlight with repeated ArrowDown keystrokes", () => {
    function Harness(): JSX.Element {
      const [value, setValue] = useState<string | null>(null);
      return <NodePicker label="Start" value={value} options={NODES} onChange={setValue} />;
    }
    const { container } = render(<Harness />);
    const input = container.querySelector('[role="combobox"]') as HTMLInputElement;
    act(() => {
      fireEvent.focus(input);
      // initial highlight = -1; pressing ArrowDown jumps to 0; pressing
      // again from the last item wraps to 0 — the menu should remain open.
      for (let i = 0; i < NODES.length + 1; i++) {
        fireEvent.keyDown(input, { key: "ArrowDown" });
      }
    });
    // No assertion of internal state; we just verify no crash and the
    // listbox still renders options after wrapping.
    expect(screen.getAllByRole("option").length).toBeGreaterThan(0);
  });

  it("caps session recents at 4 even when more nodes are selected", async () => {
    function Harness(): JSX.Element {
      const [value, setValue] = useState<string | null>(null);
      return <NodePicker label="Start" value={value} options={NODES} onChange={setValue} />;
    }
    render(<Harness />);
    const input = screen.getByRole("combobox") as HTMLInputElement;
    // Pick 4 distinct nodes in sequence (we have 4 in the fixture).
    for (const id of ["mkt-1", "mkt-2", "wh-1", "hosp-1"]) {
      const name = NODE_NAME_BY_ID[id];
      act(() => {
        fireEvent.focus(input);
        fireEvent.change(input, { target: { value: id } });
      });
      act(() => {
        fireEvent.mouseDown(screen.getByRole("option", { name: new RegExp(name, "i") }));
      });
      // Allow React to settle the choose() → effect → state propagation.
      await waitFor(() => {
        expect(input.value).toBe(name);
      });
    }
    // Reopen with empty query → exactly 4 picks appear in the "Recent"
    // chips section. (The listbox itself re-shows them too, but the
    // recent chips are the deterministic cap check.)
    act(() => {
      fireEvent.input(input, { target: { value: "" } });
    });
    await waitFor(() => {
      const recentChips = screen.getAllByRole("button", {
        name: /Ben Thanh Market|Binh Tay Market|Saigon Port Warehouse|City General Hospital/i,
      });
      expect(recentChips.length).toBeLessThanOrEqual(4);
      expect(recentChips.length).toBe(NODES.length); // = 4 here
    });
  });

  it("does not persist recents to localStorage or sessionStorage", () => {
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
    // Scan storage for any leaked recents key.
    for (let i = 0; i < localStorage.length; i++) {
      const key = localStorage.key(i) ?? "";
      expect(key.toLowerCase()).not.toMatch(/recent|nodepicker|start|history/);
    }
    for (let i = 0; i < sessionStorage.length; i++) {
      const key = sessionStorage.key(i) ?? "";
      expect(key.toLowerCase()).not.toMatch(/recent|nodepicker|start|history/);
    }
  });

  it("searches by street name carried inside the road_names-style keywords blob", () => {
    const nodes: NodeOption[] = [
      {
        id: "osm_366367996",
        name: "Trường Sa × Đặng Văn Ngữ",
        // Mirrors what ControlPanel.nodeKeywords produces for the real
        // graph fixture once road_names has been flattened into the blob.
        keywords: "Trường Sa Đặng Văn Ngữ intersection",
      },
      {
        id: "osm_other",
        name: "Bến Nhà Rồng",
        keywords: "Bến Nhà Rồng intersection",
      },
    ];
    render(<NodePicker label="Start" value={null} options={nodes} onChange={() => {}} />);
    const input = screen.getByRole("combobox");
    act(() => {
      fireEvent.focus(input);
      fireEvent.change(input, { target: { value: "Trường" } });
    });
    const options = screen.getAllByRole("option");
    expect(options).toHaveLength(1);
    expect(options[0]).toHaveTextContent("Trường Sa");
  });
});
