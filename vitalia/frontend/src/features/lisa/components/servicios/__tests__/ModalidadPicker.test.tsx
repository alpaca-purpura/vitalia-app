// cap: lisa.servicios
// story-origin: vitalia-fase2-lisa-servicios T-5
import { describe, it, expect, vi } from "vitest";
import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { ModalidadPicker } from "../ModalidadPicker";

describe("ModalidadPicker", () => {
  it("renders the 3 modalidad options", () => {
    render(<ModalidadPicker value="unica" onChange={() => {}} />);
    expect(screen.getByTestId("mod-unica")).toBeInTheDocument();
    expect(screen.getByTestId("mod-sesiones")).toBeInTheDocument();
    expect(screen.getByTestId("mod-recurrente")).toBeInTheDocument();
  });

  it("marks the selected modalidad via data-sel=true", () => {
    render(<ModalidadPicker value="sesiones" onChange={() => {}} />);
    expect(screen.getByTestId("mod-sesiones")).toHaveAttribute("data-sel", "true");
    expect(screen.getByTestId("mod-unica")).toHaveAttribute("data-sel", "false");
  });

  it("emits onChange with the modalidad value on click", async () => {
    const user = userEvent.setup();
    const onChange = vi.fn();
    render(<ModalidadPicker value="unica" onChange={onChange} />);
    await user.click(screen.getByTestId("mod-recurrente"));
    expect(onChange).toHaveBeenCalledWith("recurrente");
  });

  it("reveals 'sesiones' detail only when modalidad=sesiones (discriminated reveal)", () => {
    const { rerender } = render(<ModalidadPicker value="unica" onChange={() => {}} />);
    expect(screen.queryByTestId("mod-detail-sesiones")).not.toBeInTheDocument();
    rerender(<ModalidadPicker value="sesiones" onChange={() => {}} />);
    expect(screen.getByTestId("mod-detail-sesiones")).toBeInTheDocument();
  });

  it("reveals 'recurrente' detail only when modalidad=recurrente (discriminated reveal)", () => {
    const { rerender } = render(<ModalidadPicker value="unica" onChange={() => {}} />);
    expect(screen.queryByTestId("mod-detail-recurrente")).not.toBeInTheDocument();
    rerender(<ModalidadPicker value="recurrente" onChange={() => {}} />);
    expect(screen.getByTestId("mod-detail-recurrente")).toBeInTheDocument();
  });
});
