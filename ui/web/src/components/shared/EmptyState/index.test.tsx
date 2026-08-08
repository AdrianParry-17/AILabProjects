import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";

import { EmptyState } from "./index";

describe("EmptyState", () => {
  it("renders title and subtitle as a status region", () => {
    const { container } = render(<EmptyState title="No searches yet" subtitle="Runs appear here." />);
    expect(container.querySelector('[role="status"]')).not.toBeNull();
    expect(screen.getByText("No searches yet")).toBeInTheDocument();
    expect(screen.getByText("Runs appear here.")).toBeInTheDocument();
  });

  it("supports the description alias for the subtitle", () => {
    render(<EmptyState title="No graph" description="Data is missing." />);
    expect(screen.getByText("Data is missing.")).toBeInTheDocument();
  });

  it("renders an illustration slot", () => {
    render(<EmptyState title="Empty" icon={<span aria-label="empty icon">i</span>} />);
    expect(screen.getByLabelText("empty icon")).toBeInTheDocument();
  });

  it("renders an optional action CTA", () => {
    render(<EmptyState title="Empty" action={<button type="button">Try again</button>} />);
    expect(screen.getByRole("button", { name: "Try again" })).toBeInTheDocument();
  });

  it("omits subtitle, illustration and action when absent", () => {
    render(<EmptyState title="Empty" />);
    expect(screen.queryByRole("button")).not.toBeInTheDocument();
    expect(document.querySelectorAll("p")).toHaveLength(1);
  });
});