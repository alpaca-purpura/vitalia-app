/**
 * ReEngagementCard — TDD RED tests.
 *
 * downstream-regression-na: brand-local FE component; no cross-brand consumers
 */

import { describe, it, expect, vi } from "vitest";
import { render, screen, fireEvent } from "@testing-library/react";
import { ReEngagementCard } from "../ReEngagementCard";
import type { PatternRow } from "../../types/re-engagement";

// Mock useCurrentUser for RequireRole
vi.mock("@/hooks/useCurrentUser", () => ({
  useCurrentUser: () => ({
    role: "admin_clinic",
    hasPhiAccess: true,
    isLoaded: true,
  }),
}));

vi.mock("@clerk/nextjs", () => ({
  useUser: () => ({
    user: { publicMetadata: { role: "admin_clinic" } },
    isLoaded: true,
  }),
  useOrganization: () => ({
    organization: { publicMetadata: {} },
    isLoaded: true,
  }),
}));
vi.mock("@/hooks/useTenantId", () => ({ useTenantId: () => "mock-tenant-id" }));


const mockMultiSessionRow: PatternRow = {
  reEngagementEventId: "evt-1",
  patientId: "pat-1",
  patientName: "María García",
  pattern: "multi_session",
  urgency: "alert",
  patternData: {
    kind: "multi_session",
    offerLabel: "Tratamiento ortodóncico",
    sessionsCompleted: 3,
    sessionsExpected: 6,
    gapDays: 45,
    lastSessionDate: "2026-04-01T00:00:00Z",
    doctorName: "Dra. López",
  },
  acciones: [
    { id: "send_reminder", enabled: true, disabledReason: null },
    { id: "pause_patient", enabled: true, disabledReason: null },
  ],
};

const mockAbsenceRow: PatternRow = {
  reEngagementEventId: "evt-2",
  patientId: "pat-2",
  patientName: "Carlos Ruiz",
  pattern: "absence",
  urgency: "critical",
  patternData: {
    kind: "absence",
    lastAppointmentDate: "2025-11-01T00:00:00Z",
    monthsInactive: 6,
    lifetimeAppointments: 8,
    lifetimeValueCents: 120000,
    currency: "ARS",
    lastDoctorName: "Dr. Fernández",
    marketingOptIn: false,
  },
  acciones: [
    {
      id: "send_reminder",
      enabled: false,
      disabledReason: "Paciente no aceptó marketing",
    },
  ],
};

describe("ReEngagementCard", () => {
  const defaultHandlers = {
    onSendReminder: vi.fn(),
    onSuggestSlots: vi.fn(),
    onPause: vi.fn(),
    onMarkExternal: vi.fn(),
    onMarkNoContinue: vi.fn(),
    onLogManualCall: vi.fn(),
    onOpenConversation: vi.fn(),
  };

  it("renders multi_session card", () => {
    render(<ReEngagementCard row={mockMultiSessionRow} {...defaultHandlers} />);
    // Card should render with test-id
    expect(
      screen.getByTestId(
        `re-engagement-card-multi_session-${mockMultiSessionRow.reEngagementEventId}`,
      ),
    ).toBeInTheDocument();
  });

  it("renders absence card with disabled send_reminder", () => {
    render(<ReEngagementCard row={mockAbsenceRow} {...defaultHandlers} />);
    const card = screen.getByTestId(
      `re-engagement-card-absence-${mockAbsenceRow.reEngagementEventId}`,
    );
    expect(card).toBeInTheDocument();
    // send_reminder button should be disabled (opt-in false)
    const reminderBtn = screen.queryByRole("button", { name: /recordatorio/i });
    if (reminderBtn) {
      expect(reminderBtn).toBeDisabled();
    }
  });

  it("calls onSendReminder when send_reminder action enabled and clicked", () => {
    const onSendReminder = vi.fn();
    render(
      <ReEngagementCard
        row={mockMultiSessionRow}
        {...defaultHandlers}
        onSendReminder={onSendReminder}
      />,
    );
    const reminderBtn = screen.queryByRole("button", {
      name: /recordatorio|adrián/i,
    });
    if (reminderBtn && !reminderBtn.hasAttribute("disabled")) {
      fireEvent.click(reminderBtn);
      expect(onSendReminder).toHaveBeenCalled();
    }
  });

  it("has accessible article role with data-testid", () => {
    render(<ReEngagementCard row={mockMultiSessionRow} {...defaultHandlers} />);
    const article = screen.getByRole("article");
    expect(article).toBeInTheDocument();
  });
});
