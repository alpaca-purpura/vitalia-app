/**
 * AgendaSlot.test.tsx — Vitest unit tests (TDD RED→GREEN).
 *
 * F1-S10 vitalia-fase1-empty-states — T-7
 * spec_anchor: 06-tickets.yaml T-7 val-fe-vitest-unit-agenda-slot
 *
 * Tests:
 *   - renders paid slot con pill "✓ PAG" verbatim
 *   - renders deposit slot con pill "30%"
 *   - renders unpaid slot con pill "SIN PAGO"
 *   - renders noshow slot con pill "⚠ NO-SHOW" + line-through on patient name
 *   - renders origin icons mapping (walk-in/phone/proactive/web)
 *   - renders note when provided
 *   - does not render note element when absent
 *
 * downstream-regression-na: brand-local placeholder; no cross-brand consumers
 */

import { describe, it, expect } from "vitest";
import { render, screen } from "@testing-library/react";
import { AgendaSlot } from "./AgendaSlot";

const BASE_PROPS = {
  patient: "M. Rodríguez",
  service: "Limpieza dental",
  doctor: "Dr. C. Mendoza",
} as const;

describe("AgendaSlot", () => {
  it("renders paid slot with pill '✓ PAG'", () => {
    render(<AgendaSlot {...BASE_PROPS} status="paid" />);
    expect(screen.getByTestId("slot-pill-paid")).toBeInTheDocument();
    expect(screen.getByTestId("slot-pill-paid").textContent).toContain("PAG");
    expect(screen.getByText("M. Rodríguez")).toBeInTheDocument();
    expect(screen.getByText(/Limpieza dental/)).toBeInTheDocument();
    expect(screen.getByText(/Dr\. C\. Mendoza/)).toBeInTheDocument();
  });

  it("renders deposit slot with pill '30%'", () => {
    render(<AgendaSlot {...BASE_PROPS} status="deposit" />);
    expect(screen.getByTestId("slot-pill-deposit")).toBeInTheDocument();
    expect(screen.getByTestId("slot-pill-deposit").textContent).toBe("30%");
  });

  it("renders unpaid slot with pill 'SIN PAGO'", () => {
    render(<AgendaSlot {...BASE_PROPS} status="unpaid" />);
    expect(screen.getByTestId("slot-pill-unpaid")).toBeInTheDocument();
    expect(screen.getByTestId("slot-pill-unpaid").textContent).toBe("SIN PAGO");
  });

  it("renders noshow slot with pill '⚠ NO-SHOW' and line-through on patient name", () => {
    render(<AgendaSlot {...BASE_PROPS} status="noshow" />);
    expect(screen.getByTestId("slot-pill-noshow")).toBeInTheDocument();
    expect(screen.getByTestId("slot-pill-noshow").textContent).toContain(
      "NO-SHOW",
    );
    // Patient name has line-through class
    const patientEl = screen.getByText("M. Rodríguez");
    expect(patientEl.className).toContain("line-through");
  });

  it("renders walk-in origin icon 🚶", () => {
    render(<AgendaSlot {...BASE_PROPS} status="paid" origin="walk-in" />);
    const slot = screen.getByTestId("agenda-slot");
    expect(slot).toBeInTheDocument();
    expect(slot.textContent).toContain("🚶");
    expect(screen.getByLabelText("Origen: walk-in")).toBeInTheDocument();
  });

  it("renders phone origin icon 📞", () => {
    render(<AgendaSlot {...BASE_PROPS} status="deposit" origin="phone" />);
    const slot = screen.getByTestId("agenda-slot");
    expect(slot.textContent).toContain("📞");
    expect(screen.getByLabelText("Origen: phone")).toBeInTheDocument();
  });

  it("renders proactive origin icon ✉", () => {
    render(<AgendaSlot {...BASE_PROPS} status="deposit" origin="proactive" />);
    const slot = screen.getByTestId("agenda-slot");
    expect(slot.textContent).toContain("✉");
  });

  it("renders web origin icon 🌐", () => {
    render(<AgendaSlot {...BASE_PROPS} status="paid" origin="web" />);
    const slot = screen.getByTestId("agenda-slot");
    expect(slot.textContent).toContain("🌐");
  });

  it("renders optional note when provided", () => {
    render(
      <AgendaSlot {...BASE_PROPS} status="noshow" note="histórico 2 faltas" />,
    );
    expect(screen.getByText("histórico 2 faltas")).toBeInTheDocument();
  });

  it("does not render note element when note is absent", () => {
    const { container } = render(<AgendaSlot {...BASE_PROPS} status="paid" />);
    // No italic note paragraph should exist
    const noteEls = container.querySelectorAll(".italic");
    expect(noteEls).toHaveLength(0);
  });

  it("does not contain voseo in user-facing text", () => {
    // voseo-allowed: regex tests for absence of voseo in rendered output (technical fixture, not user-facing string)
    const { container } = render(
      <AgendaSlot {...BASE_PROPS} status="paid" origin="web" />,
    );
    const text = container.textContent ?? "";
    expect(text).not.toMatch(/tenés|podés|hacés|dejá|mirá|sos\b/i);
  });
});
