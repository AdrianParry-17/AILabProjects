import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";

import { Panel } from "./index";

describe("Panel", () => {
  it("renders children in semantic section markup", () => {
    const { container } = render(<Panel>content</Panel>);
    expect(container.querySelector("section")).not.toBeNull();
    expect(screen.getByText("content")).toBeInTheDocument();
  });

  it("renders title and icon in a header", () => {
    render(
      <Panel title="Algorithms" icon={<span aria-label="gear">g</span>}>
        body
      </Panel>,
    );
    expect(screen.getByRole("heading", { name: "Algorithms" })).toBeInTheDocument();
    expect(screen.getByLabelText("gear")).toBeInTheDocument();
  });

  it("renders footer slot in a footer element", () => {
    const { container } = render(<Panel footer="the footer">body</Panel>);
    expect(container.querySelector("footer")).toHaveTextContent("the footer");
  });

  it("omits header when no title is given", () => {
    const { container } = render(<Panel>body</Panel>);
    expect(container.querySelector("header")).toBeNull();
  });
});