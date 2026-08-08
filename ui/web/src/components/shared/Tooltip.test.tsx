import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";

import { Tooltip, type TooltipLine } from "./Tooltip";

const LINES: TooltipLine[] = [
  { label: "Node", value: "n1" },
  { label: "Type", value: "Warehouse" },
  { label: "Latitude", value: "10.778900" },
  { label: "Longitude", value: "106.700100" },
];

describe("shared Tooltip (T13)", () => {
  it("shows the title and detail rows when open", () => {
    render(<Tooltip open title="Node One" lines={LINES} />);
    expect(screen.getByRole("tooltip")).toBeInTheDocument();
    expect(screen.getByText("Node One")).toBeInTheDocument();
    expect(screen.getByText("n1")).toBeInTheDocument();
    expect(screen.getByText("10.778900")).toBeInTheDocument();
    expect(screen.getByText("106.700100")).toBeInTheDocument();
  });

  it("keeps the bubble aria-hidden when not open", () => {
    render(<Tooltip title="Node One" lines={LINES} />);
    expect(screen.getByRole("tooltip")).toBeInTheDocument();
    const bubble = screen.getByLabelText("Node One").querySelector('[aria-hidden]');
    expect(bubble).not.toBeNull();
    expect(bubble?.getAttribute("data-open")).toBeNull();
    expect(bubble?.getAttribute("aria-hidden")).toBe("true");
  });

  it("renders passed-through host children", () => {
    render(
      <Tooltip open title="Node One">
        <span data-testid="host-content">host</span>
      </Tooltip>,
    );
    expect(screen.getByTestId("host-content")).toBeInTheDocument();
  });
});