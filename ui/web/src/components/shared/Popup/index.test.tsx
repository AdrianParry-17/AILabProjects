import { fireEvent, render, screen } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";

import { Popup } from "./index";

const NODE = {
  id: "n1",
  name: "Test Point",
  kind: "delivery_warehouse",
  latitude: 10.7789,
  longitude: 106.7001,
};

describe("shared Popup (T13)", () => {
  it("renders location name, type and coordinates", () => {
    render(<Popup node={NODE} onSetStart={vi.fn()} onSetGoal={vi.fn()} onCenter={vi.fn()} onClose={vi.fn()} />);
    expect(screen.getByRole("dialog", { name: /Test Point/i })).toBeInTheDocument();
    expect(screen.getByText("Warehouse")).toBeInTheDocument();
    expect(screen.getByText("10.77890")).toBeInTheDocument();
    expect(screen.getByText("106.70010")).toBeInTheDocument();
  });

  it("calls the existing store actions via its callbacks (Set as Start/Goal)", () => {
    const onSetStart = vi.fn();
    const onSetGoal = vi.fn();
    const onCenter = vi.fn();
    const onClose = vi.fn();
    render(
      <Popup
        node={NODE}
        onSetStart={onSetStart}
        onSetGoal={onSetGoal}
        onCenter={onCenter}
        onClose={onClose}
      />,
    );

    fireEvent.click(screen.getByRole("button", { name: "Set as Start" }));
    expect(onSetStart).toHaveBeenCalledWith("n1");
    fireEvent.click(screen.getByRole("button", { name: "Set as Goal" }));
    expect(onSetGoal).toHaveBeenCalledWith("n1");
    fireEvent.click(screen.getByRole("button", { name: "Center Here" }));
    expect(onCenter).toHaveBeenCalledTimes(1);
  });

  it("closes via the close button and the Escape key", () => {
    const onClose = vi.fn();
    const { container } = render(
      <Popup node={NODE} onSetStart={vi.fn()} onSetGoal={vi.fn()} onCenter={vi.fn()} onClose={onClose} />,
    );
    fireEvent.click(screen.getByRole("button", { name: "Close popup" }));
    expect(onClose).toHaveBeenCalledTimes(1);

    fireEvent.keyDown(container.firstChild as Element, { key: "Escape" });
    expect(onClose).toHaveBeenCalledTimes(2);
  });
});