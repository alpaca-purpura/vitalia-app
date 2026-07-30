// cap: scheduling.mateo-agenda
/**
 * AvailabilityChip.test.tsx — TDD for T-FE-3 + UX-FIXLOOP-2 obs#3.
 * Covers: SC-sin-horario, SC-fuera-horario, SC-solape, SC-disponibilidad-falla.
 * obs#3: each status maps to a DISTINCT badge variant + contextual guidance Alert.
 */
import * as React from "react";
import { describe, it, expect, vi, beforeEach } from "vitest";
import { render, screen } from "@testing-library/react";

// ── Mock the store ──────────────────────────────────────────────────────────
const mockSetAvailabilityStatus = vi.fn();

// Zustand selector-style mock: selector receives the full store slice
vi.mock("../../../store/nueva-cita-store", () => ({
  useNuevaCitaStore: vi.fn((selector: (s: Record<string, unknown>) => unknown) =>
    selector({ setAvailabilityStatus: mockSetAvailabilityStatus }),
  ),
}));

// ── Mock useAvailabilityCheck ───────────────────────────────────────────────
const mockUseAvailabilityCheck = vi.fn();
vi.mock("../../../hooks/use-availability", () => ({
  useAvailabilityCheck: (...args: unknown[]) => mockUseAvailabilityCheck(...args),
}));

// ── Import component under test (after mocks) ──────────────────────────────
const { AvailabilityChip } = await import("../AvailabilityChip");

const BASE_PROPS = {
  tenantId: "t-1",
  // token removed — T-FE-4: hook calls getToken() fresh per-request
  doctorId: "d-1",
  startIso: "2026-06-22T10:00:00Z",
  durationMinutes: 30,
};

describe("AvailabilityChip", () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it("renders nothing when disabled (no doctorId)", () => {
    mockUseAvailabilityCheck.mockReturnValue({ data: undefined, isPending: false, isError: false });
    const { container } = render(
      <AvailabilityChip {...BASE_PROPS} doctorId={null} />,
    );
    expect(container.firstChild).toBeNull();
  });

  it("shows loading skeleton while pending", () => {
    mockUseAvailabilityCheck.mockReturnValue({ data: undefined, isPending: true, isError: false });
    render(<AvailabilityChip {...BASE_PROPS} />);
    expect(screen.getByRole("status")).toBeTruthy();
  });

  it("SC-disponibilidad-falla: shows error + retry on isError", () => {
    mockUseAvailabilityCheck.mockReturnValue({ data: undefined, isPending: false, isError: true, refetch: vi.fn() });
    render(<AvailabilityChip {...BASE_PROPS} />);
    expect(screen.getByTestId("availability-chip-error")).toBeTruthy();
    expect(screen.getByRole("button", { name: /reintentar/i })).toBeTruthy();
  });

  it("SC-disponibilidad-falla: calls refetch when retry clicked", async () => {
    const refetch = vi.fn();
    mockUseAvailabilityCheck.mockReturnValue({ data: undefined, isPending: false, isError: true, refetch });
    const { getByRole } = render(<AvailabilityChip {...BASE_PROPS} />);
    getByRole("button", { name: /reintentar/i }).click();
    expect(refetch).toHaveBeenCalledOnce();
  });

  // ── obs#3: 4 DISTINCT badge variants ────────────────────────────────────

  it("available: success badge with checkmark text + aria-live polite", () => {
    mockUseAvailabilityCheck.mockReturnValue({
      data: { status: "available", conflictLabel: null, conflictStart: null },
      isPending: false,
      isError: false,
    });
    render(<AvailabilityChip {...BASE_PROPS} />);
    const chip = screen.getByTestId("availability-chip");
    expect(chip.getAttribute("aria-live")).toBe("polite");
    expect(chip.textContent).toMatch(/disponible/i);
    // success variant → data-variant attribute
    expect(chip.querySelector("[data-variant='success']")).toBeTruthy();
  });

  it("busy: destructive badge (NOT warning) + conflict time in label", () => {
    mockUseAvailabilityCheck.mockReturnValue({
      data: { status: "busy", conflictLabel: "se solapa con 10:15", conflictStart: null },
      isPending: false,
      isError: false,
    });
    render(<AvailabilityChip {...BASE_PROPS} />);
    const chip = screen.getByTestId("availability-chip");
    expect(chip.textContent).toMatch(/10:15/);
    // destructive variant (distinct from out_of_hours warning)
    expect(chip.querySelector("[data-variant='destructive']")).toBeTruthy();
  });

  it("out_of_hours: warning badge (distinct from busy) + contextual Alert", () => {
    mockUseAvailabilityCheck.mockReturnValue({
      data: { status: "out_of_hours", conflictLabel: null, conflictStart: null },
      isPending: false,
      isError: false,
    });
    render(<AvailabilityChip {...BASE_PROPS} />);
    const chip = screen.getByTestId("availability-chip");
    expect(chip.textContent).toMatch(/horario/i);
    expect(chip.querySelector("[data-variant='warning']")).toBeTruthy();
    // contextual guidance alert
    const alert = screen.getByTestId("availability-chip-alert");
    expect(alert.textContent).toMatch(/horario de atención/i);
  });

  it("no_schedule: secondary badge (distinct from all others) + contextual Alert", () => {
    mockUseAvailabilityCheck.mockReturnValue({
      data: { status: "no_schedule", conflictLabel: null, conflictStart: null },
      isPending: false,
      isError: false,
    });
    render(<AvailabilityChip {...BASE_PROPS} />);
    const chip = screen.getByTestId("availability-chip");
    expect(chip.textContent).toMatch(/horario registrado/i);
    expect(chip.querySelector("[data-variant='secondary']")).toBeTruthy();
    // contextual guidance alert
    const alert = screen.getByTestId("availability-chip-alert");
    expect(alert.textContent).toMatch(/Mi Clínica/i);
  });

  it("busy: no contextual Alert shown (FreeDoctorsList handles guidance)", () => {
    mockUseAvailabilityCheck.mockReturnValue({
      data: { status: "busy", conflictLabel: "se solapa con 11:00", conflictStart: null },
      isPending: false,
      isError: false,
    });
    render(<AvailabilityChip {...BASE_PROPS} />);
    expect(screen.queryByTestId("availability-chip-alert")).toBeNull();
  });

  it("available: no contextual Alert shown", () => {
    mockUseAvailabilityCheck.mockReturnValue({
      data: { status: "available", conflictLabel: null, conflictStart: null },
      isPending: false,
      isError: false,
    });
    render(<AvailabilityChip {...BASE_PROPS} />);
    expect(screen.queryByTestId("availability-chip-alert")).toBeNull();
  });

  it("syncs status to store on each data change", () => {
    mockUseAvailabilityCheck.mockReturnValue({
      data: { status: "available", conflictLabel: null, conflictStart: null },
      isPending: false,
      isError: false,
    });
    render(<AvailabilityChip {...BASE_PROPS} />);
    expect(mockSetAvailabilityStatus).toHaveBeenCalledWith("available");
  });

  it("clears status in store on unmount", () => {
    mockUseAvailabilityCheck.mockReturnValue({
      data: { status: "available", conflictLabel: null, conflictStart: null },
      isPending: false,
      isError: false,
    });
    const { unmount } = render(<AvailabilityChip {...BASE_PROPS} />);
    unmount();
    expect(mockSetAvailabilityStatus).toHaveBeenLastCalledWith(null);
  });
});
