import { fireEvent, render, screen } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";

import { Button } from "./index";

describe("Button", () => {
  it("renders every variant", () => {
    for (const variant of ["primary", "secondary", "ghost", "danger"] as const) {
      const { unmount } = render(<Button variant={variant}>{variant}</Button>);
      expect(screen.getByRole("button", { name: variant }).className).toContain(variant);
      unmount();
    }
  });

  it("renders every size", () => {
    for (const size of ["small", "medium", "large"] as const) {
      const { unmount } = render(<Button size={size}>{size}</Button>);
      expect(screen.getByRole("button", { name: size }).className).toContain(size);
      unmount();
    }
  });

  it("renders a spinner and disables the button while loading", () => {
    render(<Button loading>Run</Button>);
    const button = screen.getByRole("button", { name: "Run" });
    expect(button).toBeDisabled();
    expect(button).toHaveAttribute("aria-busy", "true");
    expect(button.querySelector('[aria-hidden="true"]')).not.toBeNull();
  });

  it("disables the button from the disabled prop", () => {
    render(<Button disabled>Run</Button>);
    expect(screen.getByRole("button", { name: "Run" })).toBeDisabled();
  });

  it("fires onClick when not disabled", () => {
    const spy = vi.fn();
    render(<Button onClick={spy}>Run</Button>);
    fireEvent.click(screen.getByRole("button", { name: "Run" }));
    expect(spy).toHaveBeenCalledTimes(1);
  });

  it("does not fire onClick while disabled", () => {
    const spy = vi.fn();
    render(<Button onClick={spy} disabled>Run</Button>);
    fireEvent.click(screen.getByRole("button", { name: "Run" }));
    expect(spy).not.toHaveBeenCalled();
  });
});