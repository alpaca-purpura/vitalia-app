// cap: scheduling.mateo-agenda
/**
 * availability-filter.test.ts — Unit tests for isDoctorFreeAt + filterFreeDoctors.
 * T-D3 vitalia-fase2-mateo-nueva-cita delta.
 *
 * Half-open [start, end) semantics (RN-2): back-to-back appointments must be free.
 * Advisory only (RN-10): tests validate advisory logic, not server authority.
 * Timezone: "UTC" throughout (avoids DST arithmetic in unit tests).
 */

import { describe, it, expect } from "vitest";
import { isDoctorFreeAt, filterFreeDoctors } from "../availability-filter";
import type { DayBlockItem, ServiceDayDoctor } from "../../types/agenda-schema";

// ── Fixtures ───────────────────────────────────────────────────────────────

const TZ = "UTC";
const DATE = "2026-06-22";

function block(kind: DayBlockItem["kind"], startH: number, endH: number): DayBlockItem {
  return {
    kind,
    startTime: `${DATE}T${String(startH).padStart(2, "0")}:00:00Z`,
    endTime:   `${DATE}T${String(endH).padStart(2, "0")}:00:00Z`,
  };
}

const WORKING = block("working_hours", 8, 18);
const BUSY_10_11 = block("busy", 10, 11);

function doctor(
  id: string,
  blocks: DayBlockItem[],
): ServiceDayDoctor {
  return { doctorId: id, doctorLabel: `Dr. ${id}`, blocks };
}

// ── isDoctorFreeAt ─────────────────────────────────────────────────────────

describe("isDoctorFreeAt", () => {
  it("free at time within working_hours and no busy blocks", () => {
    expect(isDoctorFreeAt([WORKING], "09:00", TZ)).toBe(true);
  });

  it("not free when no working_hours block covers the time", () => {
    expect(isDoctorFreeAt([WORKING], "18:00", TZ)).toBe(false); // end of working = excluded (half-open)
  });

  it("not free when busy block overlaps (half-open: 10:00 ≤ 10:30 < 11:00)", () => {
    expect(isDoctorFreeAt([WORKING, BUSY_10_11], "10:30", TZ)).toBe(false);
  });

  it("RN-2 back-to-back free: busy ends at 11:00, query at 11:00 is free", () => {
    // half-open [10, 11): target=11 → NOT busy
    expect(isDoctorFreeAt([WORKING, BUSY_10_11], "11:00", TZ)).toBe(true);
  });

  it("RN-2 back-to-back free: busy starts at 10:00, query at exactly 10:00 is busy", () => {
    // half-open [10, 11): target=10 → busy
    expect(isDoctorFreeAt([WORKING, BUSY_10_11], "10:00", TZ)).toBe(false);
  });

  it("returns false for empty blocks (no working_hours)", () => {
    expect(isDoctorFreeAt([], "09:00", TZ)).toBe(false);
  });

  it("returns false for only busy blocks (no working_hours)", () => {
    expect(isDoctorFreeAt([BUSY_10_11], "10:30", TZ)).toBe(false);
  });

  it("returns false for invalid timeHHMM", () => {
    expect(isDoctorFreeAt([WORKING], "", TZ)).toBe(false);
    expect(isDoctorFreeAt([WORKING], "invalid", TZ)).toBe(false);
  });

  it("free at start of working hours (half-open: 8:00 is included)", () => {
    expect(isDoctorFreeAt([WORKING], "08:00", TZ)).toBe(true);
  });
});

// ── filterFreeDoctors ──────────────────────────────────────────────────────

describe("filterFreeDoctors", () => {
  const d1 = doctor("d1", [WORKING]);
  const d2 = doctor("d2", [WORKING, BUSY_10_11]);
  const d3 = doctor("d3", []); // sin horario

  it("returns [] when timeHHMM is empty (no hora selected)", () => {
    expect(filterFreeDoctors([d1, d2], "", TZ)).toEqual([]);
  });

  it("returns only free doctors at the given time", () => {
    // At 10:30: d1 is free, d2 is busy
    const result = filterFreeDoctors([d1, d2], "10:30", TZ);
    expect(result.map((d) => d.doctorId)).toEqual(["d1"]);
  });

  it("RN-2: at 11:00 (back-to-back), d2 is free again", () => {
    const result = filterFreeDoctors([d1, d2], "11:00", TZ);
    expect(result.map((d) => d.doctorId)).toEqual(["d1", "d2"]);
  });

  it("returns [] when no doctors match (e.g., all busy)", () => {
    const result = filterFreeDoctors([d2], "10:30", TZ);
    expect(result).toEqual([]);
  });

  it("sin horario doctor never appears in filtered results", () => {
    const result = filterFreeDoctors([d1, d3], "09:00", TZ);
    expect(result.map((d) => d.doctorId)).toEqual(["d1"]);
  });
});
