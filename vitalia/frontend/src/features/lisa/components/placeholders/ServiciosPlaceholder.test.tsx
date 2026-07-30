/**
 * ServiciosPlaceholder.test.tsx — Vitest unit tests.
 * F1-S10 vitalia-fase1-empty-states — T-3
 *
 * TDD RED-first: tests written before component (per tdd-mandatory.md).
 * Tests cover:
 *   1. Default (Catálogo) state: renders 5 treatment names
 *   2. Click toggle "Escalera": EmptyState "Escalera de valor — próximamente" visible
 *   3. Click back "Catálogo": treatment cards reappear
 *
 * spec_anchor: 06-tickets.yaml T-3 acceptance validators
 *   val-fe-vitest-unit-toggle-pill, val-fe-vitest-unit-servicios (implied)
 */

import { describe, it, expect } from "vitest";
import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { ServiciosPlaceholder } from "./ServiciosPlaceholder";

describe("ServiciosPlaceholder", () => {
  it("renders Catálogo state by default with 5 treatment names visible", () => {
    render(<ServiciosPlaceholder />);

    // 4 real treatment cards
    expect(screen.getByText("Limpieza dental")).toBeInTheDocument();
    expect(screen.getByText("Blanqueamiento")).toBeInTheDocument();
    expect(screen.getByText("Implante")).toBeInTheDocument();
    expect(screen.getByText("Mantenimiento periodontal")).toBeInTheDocument();

    // 5th card: CTA "Nuevo tratamiento"
    expect(screen.getByText("Nuevo tratamiento")).toBeInTheDocument();

    // Toggle pill should be visible with both options
    expect(screen.getByText("Catálogo")).toBeInTheDocument();
    expect(screen.getByText("Escalera")).toBeInTheDocument();
  });

  it("shows description for Catálogo treatments (prices in PEN)", () => {
    render(<ServiciosPlaceholder />);

    // PEN currency amounts visible
    expect(screen.getByText("S/ 120 · 30 min")).toBeInTheDocument();
    expect(screen.getByText("S/ 380 · 60 min")).toBeInTheDocument();
    expect(screen.getByText("S/ 2,400 · 90 min")).toBeInTheDocument();
    expect(screen.getByText("S/ 180 · 45 min")).toBeInTheDocument();
  });

  it("shows EmptyState 'Escalera de valor — próximamente' after clicking Escalera toggle", async () => {
    const user = userEvent.setup();
    render(<ServiciosPlaceholder />);

    // Click the "Escalera" tab
    const escaleraTab = screen.getByRole("tab", { name: "Escalera" });
    await user.click(escaleraTab);

    // EmptyState title should appear
    expect(
      screen.getByText("Escalera de valor — próximamente"),
    ).toBeInTheDocument();

    // EmptyState description should appear
    expect(
      screen.getByText(
        "Aquí vivirán los niveles de la escalera de valor del paciente (lead magnet → consulta → tratamiento core → upsell).",
      ),
    ).toBeInTheDocument();
  });

  it("shows treatment cards again after switching back to Catálogo", async () => {
    const user = userEvent.setup();
    render(<ServiciosPlaceholder />);

    // Switch to Escalera
    const escaleraTab = screen.getByRole("tab", { name: "Escalera" });
    await user.click(escaleraTab);

    // Verify escalera state
    expect(
      screen.getByText("Escalera de valor — próximamente"),
    ).toBeInTheDocument();

    // Switch back to Catálogo
    const catalogoTab = screen.getByRole("tab", { name: "Catálogo" });
    await user.click(catalogoTab);

    // Treatment cards should be visible again
    expect(screen.getByText("Limpieza dental")).toBeInTheDocument();
    expect(screen.getByText("Blanqueamiento")).toBeInTheDocument();
    expect(screen.getByText("Implante")).toBeInTheDocument();
    expect(screen.getByText("Mantenimiento periodontal")).toBeInTheDocument();
    expect(screen.getByText("Nuevo tratamiento")).toBeInTheDocument();
  });

  it("renders header with title 'Servicios' and description", () => {
    render(<ServiciosPlaceholder />);

    expect(
      screen.getByRole("heading", { level: 2, name: "Servicios" }),
    ).toBeInTheDocument();
    expect(
      screen.getByText(
        "Catálogo de tratamientos y escalera de valor (placeholder Fase 1).",
      ),
    ).toBeInTheDocument();
  });

  it("renders CTA card with accessible label", () => {
    render(<ServiciosPlaceholder />);

    const ctaCard = screen.getByRole("button", {
      name: "Agregar nuevo tratamiento",
    });
    expect(ctaCard).toBeInTheDocument();
  });

  it("contains no PHI real data (no 8+ digit sequences)", () => {
    const { container } = render(<ServiciosPlaceholder />);
    const text = container.textContent ?? "";

    // No sequences of 8+ consecutive digits (PHI ban — arch test mirrors)
    const longDigits = /\d{8,}/;
    expect(longDigits.test(text)).toBe(false);
  });
});
