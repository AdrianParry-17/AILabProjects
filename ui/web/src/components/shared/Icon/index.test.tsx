import { describe, expect, it } from "vitest";
import { render, screen } from "@testing-library/react";
import { AlertTriangle } from "lucide-react";

import { Icon } from "./index";

describe("Icon", () => {
  it("renders an accessible labelled icon", () => {
    render(<Icon icon={AlertTriangle} label="warning" />);
    const el = screen.getByRole("img", { name: "warning" });
    expect(el.querySelector("svg")).not.toBeNull();
  });

  it("marks icons without a label as decorative", () => {
    const { container } = render(<Icon icon={AlertTriangle} />);
    expect(container.querySelector('[aria-hidden="true"]')).not.toBeNull();
  });

  it("applies the requested size class for every size", () => {
    for (const size of ["sm", "md", "lg", "xl"] as const) {
      const { container, unmount } = render(<Icon icon={AlertTriangle} size={size} />);
      expect(container.querySelector("span")?.className).toContain(size);
      unmount();
    }
  });
});