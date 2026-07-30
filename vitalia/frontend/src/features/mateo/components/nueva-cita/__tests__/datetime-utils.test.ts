import { describe, it, expect } from "vitest";
import {
  buildIsoFromDateAndTime,
  addMinutesToIso,
  isoToHHMM,
} from "../datetime-utils";

// Buenos Aires = UTC-3 year-round (no DST) → exact round-trips.
const BA = "America/Argentina/Buenos_Aires";

describe("datetime-utils · tz composition (G#1 round 1 regression)", () => {
  it("local wall-clock → UTC respects tenant tz (08:00 BA = 11:00Z), NOT naive Z-append", () => {
    // OLD bug: `${date}T${time}:00Z` → "2026-06-29T08:00:00.000Z" (08:00 treated as UTC).
    expect(buildIsoFromDateAndTime("2026-06-29", "08:00", BA)).toBe(
      "2026-06-29T11:00:00.000Z",
    );
  });

  it("endTime autocalc shows start+duration in tenant tz: 08:00 +30 → 08:30 (was 05:30 bug)", () => {
    const start = buildIsoFromDateAndTime("2026-06-29", "08:00", BA);
    expect(start).toBeDefined();
    const end = addMinutesToIso(start!, 30);
    expect(isoToHHMM(start!, BA)).toBe("08:00");
    expect(isoToHHMM(end, BA)).toBe("08:30"); // ← the reported bug rendered 05:30 here
  });

  it("round-trips the wall clock across the day", () => {
    for (const t of ["00:00", "09:15", "13:45", "23:30"]) {
      const iso = buildIsoFromDateAndTime("2026-06-29", t, BA);
      expect(isoToHHMM(iso!, BA)).toBe(t);
    }
  });

  it("noon-local keeps the calendar day stable (Fecha value-prop off-by-one guard)", () => {
    // The Fecha picker value is built at noon-local so midnight-UTC can't shift it a day back.
    const iso = buildIsoFromDateAndTime("2026-06-29", "12:00", BA);
    const dayInTz = new Intl.DateTimeFormat("en-CA", {
      timeZone: BA,
      year: "numeric",
      month: "2-digit",
      day: "2-digit",
    }).format(new Date(iso!));
    expect(dayInTz).toBe("2026-06-29");
  });

  it("returns undefined for incomplete or invalid input", () => {
    expect(buildIsoFromDateAndTime(undefined, "08:00", BA)).toBeUndefined();
    expect(buildIsoFromDateAndTime("2026-06-29", undefined, BA)).toBeUndefined();
    expect(buildIsoFromDateAndTime("not-a-date", "08:00", BA)).toBeUndefined();
  });
});
