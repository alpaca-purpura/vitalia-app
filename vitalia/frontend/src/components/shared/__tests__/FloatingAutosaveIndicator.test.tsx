// cap: clinics.lisa.doctores
import { render, screen } from "@testing-library/react";
import { describe, it, expect } from "vitest";
import { FloatingAutosaveIndicator } from "../FloatingAutosaveIndicator";

describe("FloatingAutosaveIndicator", () => {
  it("is always visible at idle with the friendly hint (Chris: 'se vea siempre')", () => {
    render(<FloatingAutosaveIndicator status="idle" />);
    const el = screen.getByTestId("autosave-indicator");
    expect(el).toBeInTheDocument();
    expect(el).toHaveAttribute("data-state", "idle");
    expect(el).toHaveTextContent("Los cambios se guardan automáticamente");
  });

  it("shows 'Guardando…' while saving", () => {
    render(<FloatingAutosaveIndicator status="saving" />);
    expect(screen.getByTestId("autosave-indicator")).toHaveTextContent("Guardando…");
  });

  it("shows 'Guardado' (+ relative time when savedAt given)", () => {
    const { rerender } = render(<FloatingAutosaveIndicator status="saved" />);
    expect(screen.getByTestId("autosave-indicator")).toHaveTextContent("Guardado");
    rerender(<FloatingAutosaveIndicator status="saved" savedAt={new Date()} />);
    expect(screen.getByTestId("autosave-indicator")).toHaveTextContent(/Guardado (ahora mismo|hace)/);
  });

  it("shows an error message on error", () => {
    render(<FloatingAutosaveIndicator status="error" />);
    expect(screen.getByTestId("autosave-indicator")).toHaveTextContent("Error al guardar");
  });

  it("shows 'Cambios sin guardar' when dirty", () => {
    render(<FloatingAutosaveIndicator status="dirty" />);
    expect(screen.getByTestId("autosave-indicator")).toHaveTextContent("Cambios sin guardar");
  });

  it("uses role=status + aria-live=polite for screen readers", () => {
    render(<FloatingAutosaveIndicator status="saving" />);
    const el = screen.getByTestId("autosave-indicator");
    expect(el).toHaveAttribute("role", "status");
    expect(el).toHaveAttribute("aria-live", "polite");
  });
});
