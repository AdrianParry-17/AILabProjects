import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";

import { SectionCard } from "./index";

describe("SectionCard", () => {
  it("renders content in a section element", () => {
    const { container } = render(<SectionCard>content</SectionCard>);
    expect(container.querySelector("section")).not.toBeNull();
    expect(screen.getByText("content")).toBeInTheDocument();
  });

  it("renders a heading and a separator when titled", () => {
    const { container } = render(<SectionCard title="Options">content</SectionCard>);
    expect(screen.getByRole("heading", { name: "Options" })).toBeInTheDocument();
    const separator = container.querySelector('[role="separator"]');
    expect(separator).not.toBeNull();
    expect(separator).toHaveAttribute("aria-orientation", "horizontal");
  });

  it("omits heading and separator when untitled", () => {
    const { container } = render(<SectionCard>content</SectionCard>);
    expect(container.querySelector("h2")).toBeNull();
    expect(container.querySelector('[role="separator"]')).toBeNull();
  });
});