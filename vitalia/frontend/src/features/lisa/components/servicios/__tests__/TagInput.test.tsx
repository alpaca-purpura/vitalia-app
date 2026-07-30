// cap: lisa.servicios
// story-origin: vitalia-fase2-lisa-servicios T-5
import { describe, it, expect, vi } from "vitest";
import { render, screen, fireEvent } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { TagInput } from "../TagInput";

describe("TagInput", () => {
  it("renders a chip per tag", () => {
    render(<TagInput value={["carillas", "fundas"]} onChange={() => {}} />);
    expect(screen.getByTestId("tag-carillas")).toBeInTheDocument();
    expect(screen.getByTestId("tag-fundas")).toBeInTheDocument();
  });

  it("adds a tag on Enter", () => {
    const onChange = vi.fn();
    render(<TagInput value={["carillas"]} onChange={onChange} />);
    const input = screen.getByLabelText("Palabras clave");
    fireEvent.change(input, { target: { value: "fundas" } });
    fireEvent.keyDown(input, { key: "Enter" });
    expect(onChange).toHaveBeenCalledWith(["carillas", "fundas"]);
  });

  it("does NOT add a duplicate tag (case-insensitive)", () => {
    const onChange = vi.fn();
    render(<TagInput value={["Carillas"]} onChange={onChange} />);
    const input = screen.getByLabelText("Palabras clave");
    fireEvent.change(input, { target: { value: "carillas" } });
    fireEvent.keyDown(input, { key: "Enter" });
    expect(onChange).not.toHaveBeenCalled();
  });

  it("removes a tag via its chip delete button", async () => {
    const user = userEvent.setup();
    const onChange = vi.fn();
    render(<TagInput value={["carillas", "fundas"]} onChange={onChange} />);
    await user.click(screen.getByTestId("tag-del-carillas"));
    expect(onChange).toHaveBeenCalledWith(["fundas"]);
  });

  it("does NOT add an empty/whitespace tag", () => {
    const onChange = vi.fn();
    render(<TagInput value={[]} onChange={onChange} />);
    const input = screen.getByLabelText("Palabras clave");
    fireEvent.change(input, { target: { value: "   " } });
    fireEvent.keyDown(input, { key: "Enter" });
    expect(onChange).not.toHaveBeenCalled();
  });
});
