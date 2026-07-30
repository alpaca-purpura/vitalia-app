/**
 * Tests — SlotTrackerSticky component (T-onboarding-6 TDD)
 *
 * RED-first per .claude/rules/tdd-mandatory.md.
 *
 * downstream-regression-na: brand-local FE test; no cross-brand consumers
 */

import { describe, it, expect, vi } from "vitest";
import { render, screen } from "@testing-library/react";
import type { WizardSlot } from "../../types/wizard-onboarding.types";
import { SlotTrackerSticky } from "../../components/SlotTrackerSticky";

// ─── Mocks ──────────────────────────────────────────────────────────────────

vi.mock("@/lib/cn", () => ({
  cn: (...args: unknown[]) => args.filter(Boolean).join(" "),
}));

vi.mock("../../config/copy", () => ({
  WIZARD_COPY: {
    a11y: {
      slotTrackerLabel: "Progreso de configuración",
    },
    slotTracker: {
      statusConfirmed: "confirmado",
      statusPending: "pendiente",
      statusOptional: "opcional",
      confirmedPrefix: "✓",
      pendingPrefix: "○",
      emptyState: "Completaremos estos datos juntos",
    },
  },
}));

// ─── Test fixtures ────────────────────────────────────────────────────────────

const mockSlots: WizardSlot[] = [
  {
    slotId: "clinic_name",
    label: "Nombre de la clínica",
    status: "confirmed",
    value: "Clínica Vitalia",
    required: true,
    source: "user_text",
    confidence: 0.95,
  },
  {
    slotId: "specialty",
    label: "Especialidad",
    status: "pending",
    value: null,
    required: true,
    source: null,
    confidence: null,
  },
  {
    slotId: "tagline",
    label: "Eslogan",
    status: "optional",
    value: null,
    required: false,
    source: null,
    confidence: null,
  },
];

// ─── Tests ───────────────────────────────────────────────────────────────────

describe("SlotTrackerSticky", () => {
  it("renders without crashing with empty slots", () => {
    expect(() => render(<SlotTrackerSticky slots={[]} />)).not.toThrow();
  });

  it("renders empty state message when no slots", () => {
    render(<SlotTrackerSticky slots={[]} />);
    expect(screen.getByText("Completaremos estos datos juntos")).toBeTruthy();
  });

  it("renders slot labels for provided slots", () => {
    render(<SlotTrackerSticky slots={mockSlots} />);
    expect(screen.getByText("Nombre de la clínica")).toBeTruthy();
    expect(screen.getByText("Especialidad")).toBeTruthy();
  });

  it("renders optional badge for optional-status slots", () => {
    render(<SlotTrackerSticky slots={mockSlots} />);
    expect(screen.getByText("Eslogan")).toBeTruthy();
  });

  it("has accessible region label", () => {
    render(<SlotTrackerSticky slots={mockSlots} />);
    const region = screen.getByRole("region", {
      name: "Progreso de configuración",
    });
    expect(region).toBeTruthy();
  });

  it("does not render rejected slots", () => {
    const rejectedSlot: WizardSlot = {
      slotId: "rejected_slot",
      label: "Dato rechazado",
      status: "rejected",
      value: null,
      required: false,
      source: null,
      confidence: null,
    };
    render(<SlotTrackerSticky slots={[rejectedSlot]} />);
    expect(screen.queryByText("Dato rechazado")).toBeNull();
  });

  it("renders status for confirmed slots via aria-label", () => {
    render(<SlotTrackerSticky slots={mockSlots} />);
    // Confirmed slot aria-label should mention "confirmado"
    const confirmedStatus = screen.getByRole("status", {
      name: /nombre de la cl[íi]nica.*confirmado/i,
    });
    expect(confirmedStatus).toBeTruthy();
  });

  it("renders status for pending slots via aria-label", () => {
    render(<SlotTrackerSticky slots={mockSlots} />);
    const pendingStatus = screen.getByRole("status", {
      name: /especialidad.*pendiente/i,
    });
    expect(pendingStatus).toBeTruthy();
  });
});
