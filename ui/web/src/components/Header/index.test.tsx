import { act, render, screen } from "@testing-library/react";
import { afterEach, describe, expect, it } from "vitest";

import { useStore } from "../../state/store";
import { Header } from "./index";

describe("Header (T14)", () => {
  afterEach(() => {
    act(() =>
      useStore.setState({
        backendOk: null,
        version: null,
        renderer: "map",
      }),
    );
  });

  it("renders the banner region with the brand title on the left", () => {
    render(<Header />);
    expect(screen.getByRole("banner")).toBeInTheDocument();
    expect(screen.getByText("HCMC Delivery AI Search")).toBeInTheDocument();
  });

  it("does not place search controls in the header (LAYOUT_SPEC §5)", () => {
    render(<Header />);
    expect(screen.queryByLabelText(/Start Location/i)).toBeNull();
    expect(screen.queryByLabelText(/Destination/i)).toBeNull();
    expect(screen.queryByRole("textbox")).toBeNull();
  });

  it("shows the Map renderer label by default (renderer:map is the default)", () => {
    render(<Header />);
    expect(screen.getByText("Map view")).toBeInTheDocument();
    expect(screen.queryByRole("button", { name: /Map view/i })).toBeNull();
  });

  it("reflects the Graph renderer label when the store has renderer:graph", () => {
    act(() => useStore.setState({ renderer: "graph" }));
    render(<Header />);
    expect(screen.getByText("Graph view")).toBeInTheDocument();
  });

  it("displays the API version when the store has loaded it", () => {
    act(() => useStore.setState({ version: "1.2.3" }));
    render(<Header />);
    expect(screen.getByText("v1.2.3")).toBeInTheDocument();
    expect(screen.getByLabelText("API version 1.2.3")).toBeInTheDocument();
  });

  it("reflects the backend health state on the status pill", () => {
    act(() => useStore.setState({ backendOk: true }));
    const { rerender } = render(<Header />);
    expect(screen.getByText("Backend connected")).toBeInTheDocument();

    act(() => useStore.setState({ backendOk: false }));
    rerender(<Header />);
    expect(screen.getByText("Backend offline")).toBeInTheDocument();

    act(() => useStore.setState({ backendOk: null }));
    rerender(<Header />);
    expect(screen.getByText("Checking…")).toBeInTheDocument();
  });
});
