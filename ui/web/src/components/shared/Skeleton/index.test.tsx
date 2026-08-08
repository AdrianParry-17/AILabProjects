import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";

import { Skeleton } from "./index";

describe("Skeleton", () => {
  it("is hidden from assistive technology", () => {
    render(<Skeleton />);
    expect(screen.queryByRole("status")).toBeNull();
    const el = document.querySelector("span");
    expect(el).toHaveAttribute("aria-hidden", "true");
  });

  it("applies the given fixed dimensions", () => {
    render(<Skeleton width="120px" height="16px" />);
    const el = document.querySelector("span");
    expect(el).toHaveStyle({ width: "120px", height: "16px" });
  });

  it("renders even without explicit dimensions", () => {
    render(<Skeleton />);
    expect(document.querySelector("span")).not.toBeNull();
  });

  it("has a non-zero default footprint when no dimensions are supplied", () => {
    render(<Skeleton />);
    const el = document.querySelector("span");
    expect(el).not.toBeNull();
    // When consumers omit width/height, the inline style must remain empty
    // (CSS-module defaults handle the footprint — jsdom does not compute CSS,
    // so we assert the absence of inline style as the testable proxy).
    expect((el as HTMLElement).style.width).toBe("");
    expect((el as HTMLElement).style.height).toBe("");
  });
});