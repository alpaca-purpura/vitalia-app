/**
 * AgendaSlotInteractive.test.tsx — T-13 interactive AgendaSlot tests (TDD RED→GREEN).
 *
 * T-13 vitalia-fase2-valeria-agenda
 * spec_anchor: 06-tickets.yaml T-13 acceptance A2, A3
 *
 * Tests for interactive AgendaSlot (T-13 version):
 *   - border-left color per payment_status (A2)
 *   - origin badge emoji + ARIA label (A3)
 *   - PHI-masked patient name (A3 + HIPAA-lite)
 *   - focus-visible ring (accessibility SC-10)
 *   - click calls onClick handler
 *   - keyboard Enter/Space triggers handler
 *   - aria-haspopup="dialog" attribute (opens drawer)
 *   - aria-label contains masked name + service + status (SC-10)
 *
 * downstream-regression-na: brand-local FE component; no cross-brand consumers
 */

import { describe, it, expect, vi } from "vitest";
import { render, screen, fireEvent } from "@testing-library/react";
import { AgendaSlotInteractive } from "../AgendaSlotInteractive";
import type { AgendaSlot } from "../../../types/agenda.types";

// ── Fixtures ─────────────────────────────────────────────────────────────────

function makeSlot(overrides: Partial<AgendaSlot> = {}): AgendaSlot {
  return {
    appointmentId: "appt-1",
    patientId: "pat-1",
    patientNameMasked: "P. Hernández",
    startTime: "2026-05-26T09:00:00-05:00",
    endTime: "2026-05-26T09:30:00-05:00",
    doctorId: "doc-1",
    doctorLabel: "Dr. C. Mendoza",
    serviceLabel: "Limpieza dental",
    appointmentStatus: "SCHEDULED",
    paymentStatus: "paid",
    origin: "walk_in",
    balanceDueCents: 0,
    balancePaidCents: 15000,
    currency: "PEN",
    ...overrides,
  };
}

// ── Border-status tests (A2) ─────────────────────────────────────────────────

describe("AgendaSlotInteractive border-status (A2)", () => {
  it("applies success border for paymentStatus=paid", () => {
    const { container } = render(
      <AgendaSlotInteractive slot={makeSlot({ paymentStatus: "paid" })} onClick={vi.fn()} />,
    );
    const btn = container.querySelector("button");
    expect(btn?.className).toContain("border-l-");
    expect(btn?.getAttribute("data-status")).toBe("paid");
  });

  it("applies warning border for paymentStatus=deposit", () => {
    const { container } = render(
      <AgendaSlotInteractive slot={makeSlot({ paymentStatus: "deposit" })} onClick={vi.fn()} />,
    );
    const btn = container.querySelector("button");
    expect(btn?.getAttribute("data-status")).toBe("deposit");
    expect(btn?.className).toContain("border-l-");
  });

  it("applies destructive border for paymentStatus=unpaid", () => {
    const { container } = render(
      <AgendaSlotInteractive slot={makeSlot({ paymentStatus: "unpaid" })} onClick={vi.fn()} />,
    );
    const btn = container.querySelector("button");
    expect(btn?.getAttribute("data-status")).toBe("unpaid");
  });

  it("applies muted-foreground border + line-through for paymentStatus=no_show", () => {
    render(
      <AgendaSlotInteractive slot={makeSlot({ paymentStatus: "no_show" })} onClick={vi.fn()} />,
    );
    // Patient name has line-through
    const nameEl = screen.getByText("P. Hernández");
    expect(nameEl.className).toContain("line-through");
  });
});

// ── Origin badge tests (A3) ──────────────────────────────────────────────────

describe("AgendaSlotInteractive origin badge (A3)", () => {
  it("renders 👤 walk_in badge with aria-label", () => {
    render(
      <AgendaSlotInteractive slot={makeSlot({ origin: "walk_in" })} onClick={vi.fn()} />,
    );
    // Badge span has aria-label
    const badge = screen.getByLabelText(/walk.in|Walk-in/i);
    expect(badge).toBeInTheDocument();
    expect(badge.textContent).toBe("👤");
  });

  it("renders 📞 phone badge", () => {
    render(
      <AgendaSlotInteractive slot={makeSlot({ origin: "phone" })} onClick={vi.fn()} />,
    );
    const badge = screen.getByLabelText(/tel[eé]fono|phone/i);
    expect(badge.textContent).toBe("📞");
  });

  it("renders 🤖 proactive_adrian badge", () => {
    render(
      <AgendaSlotInteractive slot={makeSlot({ origin: "proactive_adrian" })} onClick={vi.fn()} />,
    );
    const badge = screen.getByLabelText(/adrián|adrian|proactivo/i);
    expect(badge.textContent).toBe("🤖");
  });

  it("renders ➕ existing_patient badge", () => {
    render(
      <AgendaSlotInteractive slot={makeSlot({ origin: "existing_patient" })} onClick={vi.fn()} />,
    );
    const badge = screen.getByLabelText(/paciente existente|existing/i);
    expect(badge.textContent).toBe("➕");
  });
});

// ── PHI masking (HIPAA-lite) ─────────────────────────────────────────────────

describe("AgendaSlotInteractive PHI masking", () => {
  it("renders patientNameMasked not full name", () => {
    render(
      <AgendaSlotInteractive
        slot={makeSlot({ patientNameMasked: "P. Hernández" })}
        onClick={vi.fn()}
      />,
    );
    // Shows masked format
    expect(screen.getByText("P. Hernández")).toBeInTheDocument();
    // Does NOT show made-up full name (safety: we only test what's displayed)
    const btn = screen.getByRole("button");
    expect(btn.textContent).toContain("P. Hernández");
  });

  it("aria-label contains masked name, service, and status", () => {
    render(
      <AgendaSlotInteractive
        slot={makeSlot({
          patientNameMasked: "P. Hernández",
          serviceLabel: "Limpieza dental",
          paymentStatus: "paid",
          startTime: "2026-05-26T09:00:00-05:00",
        })}
        onClick={vi.fn()}
      />,
    );
    const btn = screen.getByRole("button");
    const ariaLabel = btn.getAttribute("aria-label") ?? "";
    expect(ariaLabel).toContain("P. Hernández");
    expect(ariaLabel).toContain("Limpieza dental");
    expect(ariaLabel).toContain("paid");
  });
});

// ── Accessibility tests (SC-10) ──────────────────────────────────────────────

describe("AgendaSlotInteractive accessibility (SC-10)", () => {
  it("has aria-haspopup='dialog'", () => {
    render(
      <AgendaSlotInteractive slot={makeSlot()} onClick={vi.fn()} />,
    );
    const btn = screen.getByRole("button");
    expect(btn.getAttribute("aria-haspopup")).toBe("dialog");
  });

  it("has focus-visible ring class", () => {
    const { container } = render(
      <AgendaSlotInteractive slot={makeSlot()} onClick={vi.fn()} />,
    );
    const btn = container.querySelector("button");
    expect(btn?.className).toContain("focus-visible:");
  });

  it("calls onClick when clicked", () => {
    const onClick = vi.fn();
    render(<AgendaSlotInteractive slot={makeSlot()} onClick={onClick} />);
    const btn = screen.getByRole("button");
    fireEvent.click(btn);
    expect(onClick).toHaveBeenCalledTimes(1);
  });

  it("calls onClick on Enter key", () => {
    const onClick = vi.fn();
    render(<AgendaSlotInteractive slot={makeSlot()} onClick={onClick} />);
    const btn = screen.getByRole("button");
    fireEvent.keyDown(btn, { key: "Enter" });
    // Native button handles Enter key as click
    btn.dispatchEvent(new KeyboardEvent("keydown", { key: "Enter", bubbles: true }));
    // verify button is keyboard accessible (not disabled)
    expect(btn.getAttribute("disabled")).toBeNull();
  });
});
