// cap: lisa.servicios
// story-origin: vitalia-fase2-lisa-servicios T-5
import { describe, it, expect, vi } from "vitest";
import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { RungPicker } from "../RungPicker";

describe("RungPicker", () => {
  it("renders the 5 value-ladder rungs with medical labels (RN-2 override)", () => {
    render(<RungPicker value="TRANSFORMACION" onChange={() => {}} />);
    expect(screen.getByText("Gancho gratuito")).toBeInTheDocument();
    expect(screen.getByText("Primera visita")).toBeInTheDocument();
    expect(screen.getByText("Tratamiento principal")).toBeInTheDocument();
    expect(screen.getByText("Premium")).toBeInTheDocument();
    expect(screen.getByText("Plan/convenio")).toBeInTheDocument();
  });

  it("marks the selected rung via data-sel=true", () => {
    render(<RungPicker value="TRANSFORMACION" onChange={() => {}} />);
    const selected = screen.getByTestId("rung-TRANSFORMACION");
    expect(selected).toHaveAttribute("data-sel", "true");
  });

  it("emits onChange with the rung value when a rung is clicked", async () => {
    const user = userEvent.setup();
    const onChange = vi.fn();
    render(<RungPicker value="ACTIVACION" onChange={onChange} />);
    await user.click(screen.getByTestId("rung-MAXIMIZACION"));
    expect(onChange).toHaveBeenCalledWith("MAXIMIZACION");
  });

  it("does NOT emit onChange and disables rungs when locked (RN-31 read-only)", async () => {
    const user = userEvent.setup();
    const onChange = vi.fn();
    render(<RungPicker value="TRANSFORMACION" onChange={onChange} locked />);
    const rung = screen.getByTestId("rung-MAXIMIZACION");
    expect(rung).toBeDisabled();
    await user.click(rung);
    expect(onChange).not.toHaveBeenCalled();
  });
});
