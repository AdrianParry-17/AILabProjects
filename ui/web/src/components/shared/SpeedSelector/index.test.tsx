import { fireEvent, render, screen } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";

import { SpeedSelector } from "./index";

const OPTIONS = [0.5, 1, 2, 4] as const;

describe("SpeedSelector (T16)", () => {
  it("renders a group of one button per option, each with the correct label", () => {
    render(<SpeedSelector options={OPTIONS} value={1} onChange={() => {}} />);
    const group = screen.getByRole("group", { name: "Playback speed" });
    expect(group).toBeInTheDocument();
    for (const option of OPTIONS) {
      expect(
        screen.getByRole("button", { name: `${option}× speed` }),
      ).toBeInTheDocument();
    }
  });

  it("marks only the matching option aria-pressed=true and the rest false", () => {
    render(<SpeedSelector options={OPTIONS} value={2} onChange={() => {}} />);
    for (const option of OPTIONS) {
      const btn = screen.getByRole("button", { name: `${option}× speed` });
      expect(btn.getAttribute("aria-pressed")).toBe(option === 2 ? "true" : "false");
    }
  });

  it("calls onChange with the clicked speed value", () => {
    const onChange = vi.fn();
    render(<SpeedSelector options={OPTIONS} value={1} onChange={onChange} />);
    fireEvent.click(screen.getByRole("button", { name: "2× speed" }));
    expect(onChange).toHaveBeenCalledWith(2);
  });

  it("disables every option button when disabled=true and ignores clicks", () => {
    const onChange = vi.fn();
    render(
      <SpeedSelector options={OPTIONS} value={1} onChange={onChange} disabled />,
    );
    for (const option of OPTIONS) {
      const btn = screen.getByRole("button", { name: `${option}× speed` });
      expect(btn).toBeDisabled();
      fireEvent.click(btn);
    }
    expect(onChange).not.toHaveBeenCalled();
  });
});
