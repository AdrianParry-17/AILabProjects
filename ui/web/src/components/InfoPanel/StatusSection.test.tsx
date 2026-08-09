import { act, render } from "@testing-library/react";
import { afterEach, describe, expect, it } from "vitest";

import { useStore } from "../../state/store";
import { StatusSection } from "./StatusSection";

/** Map of every status value the store can hold → the data-state the dot
 *  exposes. The mapping must stay in sync with StatusSection.module.css
 *  which paints each `data-state` with the DESIGN_TOKENS §25 status color.
 *  The set is the exact `Status` union in state/store.ts. */
const EXPECTED_DATA_STATE: Readonly<Record<string, string>> = {
  Idle: "Idle",
  Loading: "Loading",
  Ready: "Ready",
  Playing: "Playing",
  Paused: "Paused",
  Finished: "Finished",
  Error: "Error",
  Replay: "Replay",
};

const ALL_STATUSES = Object.keys(EXPECTED_DATA_STATE);

describe("InfoPanel status dot — color mapping (T20, DESIGN_TOKENS §25)", () => {
  afterEach(() => {
    act(() =>
      useStore.setState({
        status: "Idle",
        source: null,
        error: null,
        searchError: null,
        graph: null,
      }),
    );
  });

  it("emits the expected data-state on the dot for every supported status", () => {
    for (const status of ALL_STATUSES) {
      act(() => useStore.setState({ status: status as never }));
      const { container, unmount } = render(<StatusSection />);
      const dot = container.querySelector(
        '[data-testid="status-section"] span[aria-hidden="true"]',
      );
      expect(dot, `dot rendered for ${status}`).not.toBeNull();
      expect(dot?.getAttribute("data-state"), `data-state for ${status}`).toBe(status);
      unmount();
    }
  });

  it("role=status with aria-live=polite announces state changes", () => {
    act(() => useStore.setState({ status: "Ready" }));
    const { container } = render(<StatusSection />);
    const root = container.querySelector('[data-testid="status-section"]');
    expect(root?.getAttribute("role")).toBe("status");
    expect(root?.getAttribute("aria-live")).toBe("polite");
  });
});
