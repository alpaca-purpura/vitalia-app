/**
 * AgendaToolbar.test.tsx — Vitest unit tests (TDD RED→GREEN).
 *
 * F1-S10 vitalia-fase1-empty-states — T-7
 * spec_anchor: 06-tickets.yaml T-7 val-fe-vitest-unit-agenda-toolbar
 *
 * Tests:
 *   - renders week label "Semana 26-31 May 2026" (default)
 *   - period toggle shows Día/Semana/Mes buttons
 *   - period toggle Semana is active by default (aria-checked=true)
 *   - click Día changes active period
 *   - click Mes changes active period
 *   - click "Crear cita" opens dropdown
 *   - dropdown shows 3 CTA items (Walk-in, Reserva por teléfono, Reagendar proactivamente)
 *   - click dropdown item closes dropdown
 *   - renders Hoy button
 *
 * downstream-regression-na: brand-local placeholder; no cross-brand consumers
 */

import { describe, it, expect } from "vitest";
import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { AgendaToolbar } from "./AgendaToolbar";

describe("AgendaToolbar", () => {
  it("renders default week label", () => {
    render(<AgendaToolbar />);
    expect(screen.getByText("Semana 26-31 May 2026")).toBeInTheDocument();
  });

  it("renders custom week label", () => {
    render(<AgendaToolbar weekLabel="Semana 2-8 Jun 2026" />);
    expect(screen.getByText("Semana 2-8 Jun 2026")).toBeInTheDocument();
  });

  it("renders period toggle buttons Día, Semana, Mes", () => {
    render(<AgendaToolbar />);
    expect(screen.getByTestId("period-toggle-day")).toBeInTheDocument();
    expect(screen.getByTestId("period-toggle-week")).toBeInTheDocument();
    expect(screen.getByTestId("period-toggle-month")).toBeInTheDocument();
    expect(screen.getByTestId("period-toggle-day").textContent).toBe("Día");
    expect(screen.getByTestId("period-toggle-week").textContent).toBe("Semana");
    expect(screen.getByTestId("period-toggle-month").textContent).toBe("Mes");
  });

  it("Semana is active by default (aria-checked=true)", () => {
    render(<AgendaToolbar />);
    expect(screen.getByTestId("period-toggle-week")).toHaveAttribute(
      "aria-checked",
      "true",
    );
    expect(screen.getByTestId("period-toggle-day")).toHaveAttribute(
      "aria-checked",
      "false",
    );
    expect(screen.getByTestId("period-toggle-month")).toHaveAttribute(
      "aria-checked",
      "false",
    );
  });

  it("clicking Día makes it active", async () => {
    const user = userEvent.setup();
    render(<AgendaToolbar />);
    await user.click(screen.getByTestId("period-toggle-day"));
    expect(screen.getByTestId("period-toggle-day")).toHaveAttribute(
      "aria-checked",
      "true",
    );
    expect(screen.getByTestId("period-toggle-week")).toHaveAttribute(
      "aria-checked",
      "false",
    );
  });

  it("clicking Mes makes it active", async () => {
    const user = userEvent.setup();
    render(<AgendaToolbar />);
    await user.click(screen.getByTestId("period-toggle-month"));
    expect(screen.getByTestId("period-toggle-month")).toHaveAttribute(
      "aria-checked",
      "true",
    );
    expect(screen.getByTestId("period-toggle-week")).toHaveAttribute(
      "aria-checked",
      "false",
    );
  });

  it("clicking Crear cita opens dropdown", async () => {
    const user = userEvent.setup();
    render(<AgendaToolbar />);
    expect(screen.queryByTestId("agenda-cta-dropdown")).not.toBeInTheDocument();
    await user.click(screen.getByTestId("agenda-cta-crear-cita"));
    expect(screen.getByTestId("agenda-cta-dropdown")).toBeInTheDocument();
  });

  it("dropdown shows 3 CTA items", async () => {
    const user = userEvent.setup();
    render(<AgendaToolbar />);
    await user.click(screen.getByTestId("agenda-cta-crear-cita"));
    expect(screen.getByText("Walk-in")).toBeInTheDocument();
    expect(screen.getByText("Reserva por teléfono")).toBeInTheDocument();
    expect(screen.getByText("Reagendar proactivamente")).toBeInTheDocument();
  });

  it("clicking a dropdown item closes the dropdown", async () => {
    const user = userEvent.setup();
    render(<AgendaToolbar />);
    await user.click(screen.getByTestId("agenda-cta-crear-cita"));
    expect(screen.getByTestId("agenda-cta-dropdown")).toBeInTheDocument();
    await user.click(screen.getByText("Walk-in"));
    expect(screen.queryByTestId("agenda-cta-dropdown")).not.toBeInTheDocument();
  });

  it("renders Hoy button", () => {
    render(<AgendaToolbar />);
    expect(screen.getByTestId("agenda-today-btn")).toBeInTheDocument();
    expect(screen.getByTestId("agenda-today-btn").textContent).toContain("Hoy");
  });

  it("renders navigation arrows", () => {
    render(<AgendaToolbar />);
    expect(
      screen.getByRole("button", { name: "Período anterior" }),
    ).toBeInTheDocument();
    expect(
      screen.getByRole("button", { name: "Período siguiente" }),
    ).toBeInTheDocument();
  });

  it("does not contain voseo in user-facing text", () => {
    // voseo-allowed: regex tests for absence of voseo in rendered output (technical fixture, not user-facing string)
    const { container } = render(<AgendaToolbar />);
    const text = container.textContent ?? "";
    expect(text).not.toMatch(/tenés|podés|hacés|dejá|mirá|sos\b/i);
  });
});
