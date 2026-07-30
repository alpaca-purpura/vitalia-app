// cap: scheduling.mateo-agenda
/**
 * DayAvailabilityStrip.test.tsx — Tests for T-D3 multi-doctor swimlane strip.
 * UPDATED: component no longer calls useDayStrip; receives doctors[] as props.
 *
 * Covers: N-lane render, empty state, sin-horario, loading, error,
 * time-cursor, selected-slot highlight, lane click (onSelectDoctor).
 */
import * as React from "react";
import { describe, it, expect, vi, beforeEach } from "vitest";
import { render, screen, fireEvent } from "@testing-library/react";
import { DayAvailabilityStrip } from "../DayAvailabilityStrip";
import type { ServiceDayDoctor } from "../../../types/agenda-schema";

const MOCK_SELECT = vi.fn();

const DATE = "2026-06-22";

function doctor(id: string, hasBlocks: boolean): ServiceDayDoctor {
  return {
    doctorId: id,
    doctorLabel: `Dr. ${id}`,
    blocks: hasBlocks
      ? [
          {
            kind: "working_hours",
            startTime: `${DATE}T08:00:00Z`,
            endTime: `${DATE}T17:00:00Z`,
          },
          {
            kind: "busy",
            startTime: `${DATE}T10:00:00Z`,
            endTime: `${DATE}T11:00:00Z`,
          },
        ]
      : [],
  };
}

const BASE_PROPS = {
  doctors: [doctor("d-1", true), doctor("d-2", true)],
  isPending: false,
  isError: false,
  dateLocal: DATE,
  selectedStartIso: null,
  selectedEndIso: null,
  selectedDoctorId: null,
  onSelectDoctor: MOCK_SELECT,
  timezone: "UTC",
};

describe("DayAvailabilityStrip — T-D3 swimlane", () => {
  beforeEach(() => vi.clearAllMocks());

  it("shows loading skeleton while isPending", () => {
    render(<DayAvailabilityStrip {...BASE_PROPS} isPending={true} doctors={[]} />);
    expect(screen.getByTestId("day-strip-loading")).toBeTruthy();
  });

  it("shows error state on isError", () => {
    render(<DayAvailabilityStrip {...BASE_PROPS} isError={true} doctors={[]} />);
    expect(screen.getByTestId("day-strip-error")).toBeTruthy();
  });

  it("shows empty state when doctors:[]", () => {
    render(<DayAvailabilityStrip {...BASE_PROPS} doctors={[]} />);
    expect(screen.getByTestId("day-strip-empty")).toBeTruthy();
  });

  it("renders N swimlanes — one per doctor", () => {
    render(<DayAvailabilityStrip {...BASE_PROPS} />);
    expect(screen.getByTestId("day-strip")).toBeTruthy();
    expect(screen.getByTestId("swimlane-d-1")).toBeTruthy();
    expect(screen.getByTestId("swimlane-d-2")).toBeTruthy();
  });

  it("renders doctor label text in each lane", () => {
    render(<DayAvailabilityStrip {...BASE_PROPS} />);
    expect(screen.getByText("Dr. d-1")).toBeTruthy();
    expect(screen.getByText("Dr. d-2")).toBeTruthy();
  });

  it("clicking a lane calls onSelectDoctor with that doctor's id", () => {
    render(<DayAvailabilityStrip {...BASE_PROPS} />);
    fireEvent.click(screen.getByTestId("swimlane-d-1"));
    expect(MOCK_SELECT).toHaveBeenCalledWith("d-1");
  });

  it("selected lane has aria-pressed=true", () => {
    render(<DayAvailabilityStrip {...BASE_PROPS} selectedDoctorId="d-1" />);
    const lane = screen.getByTestId("swimlane-d-1");
    expect(lane.getAttribute("aria-pressed")).toBe("true");
    expect(screen.getByTestId("swimlane-d-2").getAttribute("aria-pressed")).toBe("false");
  });

  it("sin-horario lane shows 'Sin horario' when blocks:[]", () => {
    const props = {
      ...BASE_PROPS,
      doctors: [doctor("d-1", true), { doctorId: "d-sin", doctorLabel: "Dr. Sin", blocks: [] }],
    };
    render(<DayAvailabilityStrip {...props} />);
    expect(screen.getByText("Sin horario")).toBeTruthy();
  });

  it("renders blocks in the swimlane timeline", () => {
    render(<DayAvailabilityStrip {...BASE_PROPS} />);
    // working_hours (block-0) + busy (block-1) for d-1
    expect(screen.getByTestId("swimlane-d-1-block-0")).toBeTruthy();
    expect(screen.getByTestId("swimlane-d-1-block-1")).toBeTruthy();
  });

  it("shows time cursor when selectedStartIso is set (on lanes with blocks)", () => {
    render(
      <DayAvailabilityStrip
        {...BASE_PROPS}
        selectedStartIso={`${DATE}T09:00:00Z`}
        selectedEndIso={`${DATE}T09:30:00Z`}
      />,
    );
    expect(screen.getByTestId("swimlane-d-1-cursor")).toBeTruthy();
    expect(screen.getByTestId("swimlane-d-2-cursor")).toBeTruthy();
  });

  it("shows selected-slot highlight on the selected doctor lane only", () => {
    render(
      <DayAvailabilityStrip
        {...BASE_PROPS}
        selectedStartIso={`${DATE}T09:00:00Z`}
        selectedEndIso={`${DATE}T09:30:00Z`}
        selectedDoctorId="d-1"
      />,
    );
    expect(screen.getByTestId("swimlane-d-1-selected")).toBeTruthy();
    expect(screen.queryByTestId("swimlane-d-2-selected")).toBeNull();
  });

  it("no time cursor when selectedStartIso is null", () => {
    render(<DayAvailabilityStrip {...BASE_PROPS} selectedStartIso={null} />);
    expect(screen.queryByTestId("swimlane-d-1-cursor")).toBeNull();
  });

  it("keyboard Enter triggers onSelectDoctor", () => {
    render(<DayAvailabilityStrip {...BASE_PROPS} />);
    const lane = screen.getByTestId("swimlane-d-2");
    fireEvent.keyDown(lane, { key: "Enter" });
    expect(MOCK_SELECT).toHaveBeenCalledWith("d-2");
  });
});
