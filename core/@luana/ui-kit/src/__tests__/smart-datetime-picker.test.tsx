/**
 * smart-datetime-picker.test.tsx — additive `showTime` prop coverage.
 * Locks the date-only contract (showTime={false}) + regression-guards the
 * default (time section present) protecting existing consumers.
 * The tz/UTC value math is exercised live (Chrome) per #37.
 */
import { describe, expect, it } from "vitest";
import { fireEvent, render, screen, within } from "@testing-library/react";
import { SmartDateTimePicker } from "../smart-datetime-picker";

const VALUE = "2026-06-22T12:00:00.000Z";
const TZ = "America/Buenos_Aires"; // value 12:00Z → 09:00 local
// Fixed far-past value: its rendered month (Jan 2020) is entirely before today
// regardless of when the suite runs → no calendar-day assertion drifts.
const PAST_VALUE = "2020-01-15T12:00:00.000Z";

// Open the popover (single trigger button) → return the calendar's day buttons.
function openCalendarDays() {
  fireEvent.click(screen.getByRole("button")); // only the trigger exists before opening
  return within(screen.getByRole("grid")).getAllByRole("button");
}

describe("SmartDateTimePicker · showTime", () => {
  it("showTime={false} → trigger is date-only (no time) + time section not rendered when open", () => {
    render(
      <SmartDateTimePicker value={VALUE} onChange={() => {}} timezone={TZ} showTime={false} />,
    );
    const trigger = screen.getByRole("button");
    // date-only format dd/MM/yyyy — no ":" time component
    expect(trigger).toHaveTextContent("22/06/2026");
    expect(trigger.textContent).not.toContain(":");
    // open the popover → calendar present, but TimePicker (aria-label "Hora — *") absent
    fireEvent.click(trigger);
    expect(screen.getByRole("grid")).toBeInTheDocument(); // calendar rendered (popover open)
    expect(screen.queryByLabelText("Hora — hora")).not.toBeInTheDocument();
  });

  it("default (showTime omitted) → trigger shows date + time, time section rendered (regression guard)", () => {
    render(<SmartDateTimePicker value={VALUE} onChange={() => {}} timezone={TZ} />);
    const trigger = screen.getByRole("button");
    expect(trigger).toHaveTextContent("22/06/2026 09:00");
    fireEvent.click(trigger);
    expect(screen.getByLabelText("Hora — hora")).toBeInTheDocument();
  });
});

describe("SmartDateTimePicker · disablePast", () => {
  it("disablePast={true} → past days are disabled (Jan 2020 month entirely before today)", () => {
    render(
      <SmartDateTimePicker value={PAST_VALUE} onChange={() => {}} timezone={TZ} disablePast />,
    );
    const days = openCalendarDays();
    // The rendered month is wholly in the past → at least one day button is disabled.
    expect(days.some((b) => (b as HTMLButtonElement).disabled)).toBe(true);
  });

  it("default (disablePast omitted) → no day is disabled (open-closed regression guard)", () => {
    render(<SmartDateTimePicker value={PAST_VALUE} onChange={() => {}} timezone={TZ} />);
    const days = openCalendarDays();
    expect(days.every((b) => !(b as HTMLButtonElement).disabled)).toBe(true);
  });
});
