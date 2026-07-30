import { describe, it, expect } from "vitest";
import {
  parseLocalDate,
  toLocalIsoDate,
  addLocalDays,
  mondayOfWeek,
  localWeekdayIndex,
} from "../calendarDates";

describe("calendarDates — TZ-stable local date math (bug7 r4)", () => {
  it("toLocalIsoDate round-trips parseLocalDate", () => {
    expect(toLocalIsoDate(parseLocalDate("2026-06-15"))).toBe("2026-06-15");
  });

  it("addLocalDays crosses month/year boundaries", () => {
    expect(addLocalDays("2026-06-08", 6)).toBe("2026-06-14");
    expect(addLocalDays("2026-06-30", 1)).toBe("2026-07-01");
    expect(addLocalDays("2026-01-01", -1)).toBe("2025-12-31");
  });

  it("mondayOfWeek returns the real Monday for every weekday of a week", () => {
    // Week of Mon 2026-06-08 .. Sun 2026-06-14
    const expected = "2026-06-08";
    for (let d = 8; d <= 14; d++) {
      const iso = `2026-06-${String(d).padStart(2, "0")}`;
      expect(mondayOfWeek(iso)).toBe(expected);
    }
  });

  it("REGRESSION: mondayOfWeek of a Sunday-EVENING Date is Monday, not Tuesday", () => {
    // The exact failure shape: Sunday 2026-06-14 at 22:00 LOCAL. The old
    // getCurrentWeekMonday() did toISOString() after setDate → under a negative
    // UTC offset this produced 2026-06-09 (Tuesday). The fix uses local
    // components only → always the real Monday, in ANY timezone.
    const sundayEvening = new Date(2026, 5, 14, 22, 0, 0); // local Sun Jun 14 22:00
    const monday = mondayOfWeek(sundayEvening);
    expect(monday).toBe("2026-06-08");
    expect(parseLocalDate(monday).getDay()).toBe(1); // 1 = Monday (local)
  });

  it("mondayOfWeek result is ALWAYS a Monday across a full month of dates", () => {
    for (let d = 1; d <= 30; d++) {
      const m = mondayOfWeek(`2026-06-${String(d).padStart(2, "0")}`);
      expect(parseLocalDate(m).getDay(), `monday-of ${d}`).toBe(1);
    }
  });

  it("localWeekdayIndex maps 0=Mon..6=Sun", () => {
    expect(localWeekdayIndex("2026-06-08")).toBe(0); // Monday
    expect(localWeekdayIndex("2026-06-12")).toBe(4); // Friday
    expect(localWeekdayIndex("2026-06-14")).toBe(6); // Sunday
  });
});
