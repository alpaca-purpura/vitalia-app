// cap: scheduling.mateo-agenda
/**
 * FreeDoctorsList.test.tsx — Tests for T-D3 re-role (time-filtered list).
 * UPDATED: component now receives doctors[] + startHourStr + timezone.
 *          Client-side filter via isDoctorFreeAt (advisory).
 *
 * Covers: hint state (no hora), filtered results, empty after filter,
 * 1-click select, aria-pressed, no-slot-hint.
 */
import * as React from "react";
import { describe, it, expect, vi, beforeEach } from "vitest";
import { render, screen, fireEvent } from "@testing-library/react";

const mockSetSelectedDoctorId = vi.fn();
let mockSelectedDoctorId: string | null = null;

vi.mock("../../../store/nueva-cita-store", () => ({
  useNuevaCitaStore: vi.fn(
    (selector: (s: Record<string, unknown>) => unknown) =>
      selector({
        setSelectedDoctorId: mockSetSelectedDoctorId,
        selectedDoctorId: mockSelectedDoctorId,
      }),
  ),
}));

const { FreeDoctorsList } = await import("../FreeDoctorsList");

const TZ = "UTC";
const DATE = "2026-06-22";

// Doctors: d-1 has working hours 08-17, d-2 is busy 08-12 only working, d-3 no blocks
const DOCTORS = [
  {
    doctorId: "d-1",
    doctorLabel: "Dra. García",
    blocks: [
      { kind: "working_hours" as const, startTime: `${DATE}T08:00:00Z`, endTime: `${DATE}T17:00:00Z` },
    ],
  },
  {
    doctorId: "d-2",
    doctorLabel: "Dr. López",
    blocks: [
      { kind: "working_hours" as const, startTime: `${DATE}T08:00:00Z`, endTime: `${DATE}T12:00:00Z` },
    ],
  },
  {
    doctorId: "d-3",
    doctorLabel: "Dr. Sin Horario",
    blocks: [],
  },
];

const BASE_PROPS = {
  tenantId: "t-1",
  doctors: DOCTORS,
  startHourStr: "",
  timezone: TZ,
};

describe("FreeDoctorsList — T-D3 re-role", () => {
  beforeEach(() => {
    vi.clearAllMocks();
    mockSelectedDoctorId = null;
  });

  it("shows hint when startHourStr is empty (no hora set)", () => {
    render(<FreeDoctorsList {...BASE_PROPS} startHourStr="" />);
    expect(screen.getByTestId("free-doctors-no-slot")).toBeTruthy();
    expect(screen.getByText(/pon una hora/i)).toBeTruthy();
  });

  it("shows filtered doctors at 09:00 (d-1 + d-2 free, d-3 no blocks)", () => {
    render(<FreeDoctorsList {...BASE_PROPS} startHourStr="09:00" />);
    expect(screen.getByText("Dra. García")).toBeTruthy();
    expect(screen.getByText("Dr. López")).toBeTruthy();
    expect(screen.queryByText("Dr. Sin Horario")).toBeNull();
  });

  it("shows only d-1 at 13:00 (d-2 working ends at 12:00)", () => {
    render(<FreeDoctorsList {...BASE_PROPS} startHourStr="13:00" />);
    expect(screen.getByText("Dra. García")).toBeTruthy();
    expect(screen.queryByText("Dr. López")).toBeNull();
  });

  it("shows empty state when no doctors free at the given time", () => {
    render(<FreeDoctorsList {...BASE_PROPS} startHourStr="20:00" />);
    expect(screen.getByTestId("free-doctors-empty")).toBeTruthy();
    expect(screen.getByText(/no hay médicos disponibles/i)).toBeTruthy();
  });

  it("clicking a doctor button calls setSelectedDoctorId", () => {
    render(<FreeDoctorsList {...BASE_PROPS} startHourStr="09:00" />);
    fireEvent.click(screen.getByTestId("free-doctor-btn-d-1"));
    expect(mockSetSelectedDoctorId).toHaveBeenCalledWith("d-1");
  });

  it("selected doctor button has aria-pressed=true", () => {
    mockSelectedDoctorId = "d-1";
    render(<FreeDoctorsList {...BASE_PROPS} startHourStr="09:00" />);
    const btn = screen.getByTestId("free-doctor-btn-d-1");
    expect(btn.getAttribute("aria-pressed")).toBe("true");
  });

  it("unselected buttons have aria-pressed=false", () => {
    mockSelectedDoctorId = "d-1";
    render(<FreeDoctorsList {...BASE_PROPS} startHourStr="09:00" />);
    const btn2 = screen.getByTestId("free-doctor-btn-d-2");
    expect(btn2.getAttribute("aria-pressed")).toBe("false");
  });

  it("empty doctors[] + hora set → empty state", () => {
    render(<FreeDoctorsList {...BASE_PROPS} doctors={[]} startHourStr="09:00" />);
    expect(screen.getByTestId("free-doctors-empty")).toBeTruthy();
  });
});
