// cap: lisa.servicios
// story-origin: vitalia-fase2-lisa-servicios T-5
import { describe, it, expect } from "vitest";
import { render, screen } from "@testing-library/react";
import { ChipOrigen } from "../ChipOrigen";

describe("ChipOrigen", () => {
  it("renders the standard-service name when origen=estandar", () => {
    render(<ChipOrigen origen="estandar" standardName="Diseño de sonrisa" />);
    const chip = screen.getByTestId("chip-origen");
    expect(chip).toHaveAttribute("data-origen", "estandar");
    expect(chip).toHaveTextContent("Diseño de sonrisa");
  });

  it("renders 'Estándar' when origen=estandar without a name", () => {
    render(<ChipOrigen origen="estandar" />);
    expect(screen.getByTestId("chip-origen")).toHaveTextContent("Estándar");
  });

  it("renders 'Personalizado' when origen=personalizado", () => {
    render(<ChipOrigen origen="personalizado" />);
    const chip = screen.getByTestId("chip-origen");
    expect(chip).toHaveAttribute("data-origen", "personalizado");
    expect(chip).toHaveTextContent("Personalizado");
  });

  it("exposes a descriptive title for the estandar link", () => {
    render(<ChipOrigen origen="estandar" standardName="Diseño de sonrisa" />);
    expect(screen.getByTestId("chip-origen")).toHaveAttribute(
      "title",
      'Vinculado a la biblioteca estándar: "Diseño de sonrisa"',
    );
  });
});
