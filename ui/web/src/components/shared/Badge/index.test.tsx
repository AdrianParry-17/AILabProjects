import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";

import { Badge } from "./index";

describe("Badge", () => {
  it("renders each variant with an exposed class", () => {
    for (const variant of ["info", "success", "warning", "danger"] as const) {
      const { unmount } = render(<Badge variant={variant}>{variant}</Badge>);
      const badge = screen.getByText(variant);
      expect(badge.className).toContain("badge");
      expect(badge.className).toContain(variant);
      unmount();
    }
  });

  it("keeps content readable (not aria-hidden)", () => {
    render(<Badge variant="success">Mock</Badge>);
    const badge = screen.getByText("Mock");
    expect(badge).not.toHaveAttribute("aria-hidden");
  });

  it("defaults to the info variant", () => {
    render(<Badge>Info</Badge>);
    expect(screen.getByText("Info").className).toContain("info");
  });
});