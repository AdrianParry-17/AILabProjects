import { fireEvent, render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";

import { TextInput } from "./index";

describe("TextInput", () => {
  it("associates the label with the input", () => {
    render(<TextInput label="Start" />);
    const input = screen.getByLabelText("Start");
    expect(input).toBeInstanceOf(HTMLInputElement);
  });

  it("accepts controlled usage", () => {
    render(<TextInput label="Start" value="A1" onChange={() => {}} />);
    expect(screen.getByLabelText("Start")).toHaveValue("A1");
  });

  it("accepts uncontrolled usage", () => {
    render(<TextInput label="Start" />);
    const input = screen.getByLabelText("Start");
    fireEvent.change(input, { target: { value: "xyz" } });
    expect(input).toHaveValue("xyz");
  });

  it("marks the input invalid and announces error text", () => {
    render(<TextInput label="Start" invalid errorText="Node not found" />);
    const input = screen.getByLabelText("Start");
    expect(input).toHaveAttribute("aria-invalid", "true");
    expect(screen.getByRole("alert")).toHaveTextContent("Node not found");
  });

  it("is valid by default", () => {
    render(<TextInput label="Start" />);
    expect(screen.getByLabelText("Start")).not.toHaveAttribute("aria-invalid");
  });

  it("applies placeholder styling target through the placeholder attribute", () => {
    render(<TextInput label="Start" placeholder="Pick a node" />);
    expect(screen.getByLabelText("Start")).toHaveAttribute("placeholder", "Pick a node");
  });
});