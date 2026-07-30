/**
 * AppointmentDrawerTurnoSection.test.tsx — Vitest unit tests (TDD RED→GREEN).
 *
 * T-14 vitalia-fase2-valeria-agenda
 * spec_anchor: 06-tickets.yaml T-14 acceptance Q8
 *
 * Tests:
 *   - Renders date/time/doctor/service from appointment data
 *   - Status badge renders for SCHEDULED/COMPLETED/CANCELLED/NO_SHOW
 *   - Action buttons hidden when status is terminal (COMPLETED/CANCELLED/NO_SHOW)
 *   - "Reagendar" button is disabled (Q7)
 *   - "Cancelar turno" click opens confirm dialog
 *   - "No asistió" click opens confirm dialog
 *   - Dialog confirm triggers onStatusChange callback
 *   - Dialog cancel does NOT trigger onStatusChange
 *   - "Completar" click directly triggers onStatusChange("COMPLETED")
 *
 * downstream-regression-na: brand-local FE component; no cross-brand consumers
 */

import { describe, it, expect, vi, beforeEach } from "vitest";
import { render, screen, fireEvent, waitFor } from "@testing-library/react";
import { AppointmentDrawerTurnoSection } from "../AppointmentDrawerTurnoSection";
import type { Appointment } from "../../../types/agenda.types";

// ── Mocks ──────────────────────────────────────────────────────────────────────

// useTenantLocale added in F2 master-data fix — mock Clerk-dependent hook
vi.mock("@/hooks/useTenantLocale", () => ({
  useTenantLocale: () => ({
    currency: "PEN",
    timezone: "America/Lima",
    locale: "es-PE",
  }),
}));

// ── Fixtures ───────────────────────────────────────────────────────────────

const BASE_APPOINTMENT: Appointment = {
  appointmentId: "slot-123",
  patientId: "patient-456",
  patientNameMasked: "P. Hernández",
  patientDniMasked: null,
  patientPhoneMasked: null,
  patientEmailMasked: null,
  startTime: "2026-05-27T14:00:00.000Z",
  endTime: "2026-05-27T14:30:00.000Z",
  doctorId: "doc-789",
  doctorLabel: "Dr. C. Mendoza",
  serviceLabel: "Limpieza dental",
  appointmentStatus: "SCHEDULED",
  paymentStatus: "unpaid",
  origin: "walk_in",
  balanceDueCents: 5000,
  balancePaidCents: 0,
  currency: "PEN",
  currencyOverride: null,
  payments: [],
  notesInternal: null,
  lastActivityAt: null,
  lastActivityByLabel: null,
};

// ── Tests ──────────────────────────────────────────────────────────────────

describe("AppointmentDrawerTurnoSection", () => {
  const mockOnStatusChange = vi.fn();

  beforeEach(() => {
    vi.clearAllMocks();
  });

  it("renders doctor label and service label", () => {
    render(
      <AppointmentDrawerTurnoSection
        appointment={BASE_APPOINTMENT}
        onStatusChange={mockOnStatusChange}
        isUpdating={false}
      />,
    );
    expect(screen.getByText("Dr. C. Mendoza")).toBeInTheDocument();
    expect(screen.getByText("Limpieza dental")).toBeInTheDocument();
  });

  it("renders SCHEDULED status badge as 'Agendado'", () => {
    render(
      <AppointmentDrawerTurnoSection
        appointment={BASE_APPOINTMENT}
        onStatusChange={mockOnStatusChange}
        isUpdating={false}
      />,
    );
    expect(screen.getByText("Agendado")).toBeInTheDocument();
  });

  it("renders COMPLETED status badge as 'Completado' with no action buttons", () => {
    render(
      <AppointmentDrawerTurnoSection
        appointment={{ ...BASE_APPOINTMENT, appointmentStatus: "COMPLETED" }}
        onStatusChange={mockOnStatusChange}
        isUpdating={false}
      />,
    );
    expect(screen.getByText("Completado")).toBeInTheDocument();
    expect(screen.queryByRole("button", { name: /cancelar turno/i })).not.toBeInTheDocument();
    expect(screen.queryByRole("button", { name: /no asistió/i })).not.toBeInTheDocument();
    expect(screen.queryByRole("button", { name: /completar/i })).not.toBeInTheDocument();
  });

  it("renders CANCELLED status badge as 'Cancelado' with no action buttons", () => {
    render(
      <AppointmentDrawerTurnoSection
        appointment={{ ...BASE_APPOINTMENT, appointmentStatus: "CANCELLED" }}
        onStatusChange={mockOnStatusChange}
        isUpdating={false}
      />,
    );
    expect(screen.getByText("Cancelado")).toBeInTheDocument();
    expect(screen.queryByRole("button", { name: /cancelar turno/i })).not.toBeInTheDocument();
  });

  it("renders NO_SHOW status badge as 'No asistió' with no action buttons", () => {
    render(
      <AppointmentDrawerTurnoSection
        appointment={{ ...BASE_APPOINTMENT, appointmentStatus: "NO_SHOW" }}
        onStatusChange={mockOnStatusChange}
        isUpdating={false}
      />,
    );
    expect(screen.getByText("No asistió")).toBeInTheDocument();
    expect(screen.queryByRole("button", { name: /no asistió/i })).not.toBeInTheDocument();
  });

  it("Reagendar button is disabled (Q7)", () => {
    render(
      <AppointmentDrawerTurnoSection
        appointment={BASE_APPOINTMENT}
        onStatusChange={mockOnStatusChange}
        isUpdating={false}
      />,
    );
    const btn = screen.getByRole("button", { name: /reagendar/i });
    expect(btn).toBeDisabled();
  });

  it("'Cancelar turno' click opens confirm dialog (Q8)", async () => {
    render(
      <AppointmentDrawerTurnoSection
        appointment={BASE_APPOINTMENT}
        onStatusChange={mockOnStatusChange}
        isUpdating={false}
      />,
    );
    fireEvent.click(screen.getByRole("button", { name: /cancelar turno/i }));
    await waitFor(() => {
      expect(screen.getByRole("dialog")).toBeInTheDocument();
      expect(screen.getByText(/cancelar este turno/i)).toBeInTheDocument();
    });
  });

  it("'No asistió' click opens confirm dialog (Q8)", async () => {
    render(
      <AppointmentDrawerTurnoSection
        appointment={BASE_APPOINTMENT}
        onStatusChange={mockOnStatusChange}
        isUpdating={false}
      />,
    );
    fireEvent.click(screen.getByRole("button", { name: /no asistió/i }));
    await waitFor(() => {
      expect(screen.getByRole("dialog")).toBeInTheDocument();
      expect(screen.getByText(/marcar como no asistió/i)).toBeInTheDocument();
    });
  });

  it("confirm 'Cancelar turno' triggers onStatusChange('CANCELLED')", async () => {
    render(
      <AppointmentDrawerTurnoSection
        appointment={BASE_APPOINTMENT}
        onStatusChange={mockOnStatusChange}
        isUpdating={false}
      />,
    );
    fireEvent.click(screen.getByRole("button", { name: /cancelar turno/i }));
    await waitFor(() => screen.getByRole("dialog"));

    // There may be multiple — the dialog one is the last occurrence inside the dialog
    const allCancelBtns = screen.getAllByRole("button", { name: /cancelar turno/i });
    // Last one is the confirm button in dialog
    fireEvent.click(allCancelBtns[allCancelBtns.length - 1]);
    expect(mockOnStatusChange).toHaveBeenCalledWith("CANCELLED");
  });

  it("'Volver' in confirm dialog does NOT trigger onStatusChange", async () => {
    render(
      <AppointmentDrawerTurnoSection
        appointment={BASE_APPOINTMENT}
        onStatusChange={mockOnStatusChange}
        isUpdating={false}
      />,
    );
    fireEvent.click(screen.getByRole("button", { name: /cancelar turno/i }));
    await waitFor(() => screen.getByRole("dialog"));

    fireEvent.click(screen.getByRole("button", { name: /volver/i }));
    expect(mockOnStatusChange).not.toHaveBeenCalled();
  });

  it("'Completar' click directly triggers onStatusChange('COMPLETED')", () => {
    render(
      <AppointmentDrawerTurnoSection
        appointment={BASE_APPOINTMENT}
        onStatusChange={mockOnStatusChange}
        isUpdating={false}
      />,
    );
    fireEvent.click(screen.getByRole("button", { name: /completar/i }));
    expect(mockOnStatusChange).toHaveBeenCalledWith("COMPLETED");
  });
});
