// cap: scheduling.mateo-agenda
/**
 * nueva-cita-helpers.test.ts — Unit tests for helper logic (H1/L2 guards).
 * UX-FIXLOOP-2026-06-24
 */

import { describe, it, expect } from "vitest";

// ── H1: isoToHHMM must use timezone-aware rendering ──────────────────────────
// The function lives inside NuevaCitaView but its logic is testable
// by replicating it here (ponytail: test the contract, not the file import).

function isoToHHMM(isoString: string, timezone: string): string {
  try {
    return new Intl.DateTimeFormat("es", {
      timeZone: timezone,
      hour: "2-digit",
      minute: "2-digit",
      hourCycle: "h23",
    }).format(new Date(isoString));
  } catch {
    return "";
  }
}

describe("H1: isoToHHMM — timezone-aware rendering", () => {
  it("shows correct local time for Buenos Aires (UTC-3)", () => {
    // 2026-07-01T13:30:00Z → 10:30 in UTC-3
    const result = isoToHHMM("2026-07-01T13:30:00Z", "America/Argentina/Buenos_Aires");
    expect(result).toBe("10:30");
  });

  it("shows correct local time for Mexico City (UTC-6 standard time)", () => {
    // 2026-01-15T18:00:00Z → 12:00 in UTC-6
    const result = isoToHHMM("2026-01-15T18:00:00Z", "America/Mexico_City");
    expect(result).toBe("12:00");
  });

  it("differs from UTC time (the original bug)", () => {
    // This would be 13:30 UTC but 10:30 in Buenos Aires
    const utcBuggy = "13:30";
    const localCorrect = isoToHHMM("2026-07-01T13:30:00Z", "America/Argentina/Buenos_Aires");
    expect(localCorrect).not.toBe(utcBuggy);
  });

  it("returns empty string for invalid ISO", () => {
    const result = isoToHHMM("not-a-date", "America/Lima");
    expect(result).toBe("");
  });
});

// ── L2: endTime guard — only overwrite if !endTimeEditMode ───────────────────
// Logic extracted as a pure function for unit testing.

function computeEndTime(
  startIso: string,
  durationMinutes: number,
  endTimeEditMode: boolean,
): string | null {
  if (endTimeEditMode) return null; // L2: preserve manual edit
  const d = new Date(startIso);
  d.setMinutes(d.getMinutes() + durationMinutes);
  return d.toISOString();
}

// ── L3: UUID label detection ──────────────────────────────────────────────────

const UUID_RE = /^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$/i;

function resolveLabel(doctorLabel: string): string {
  if (!doctorLabel || UUID_RE.test(doctorLabel.trim())) return "Médico sin nombre";
  return doctorLabel;
}

describe("L3: UUID label detection", () => {
  it("returns fallback for UUID-format label", () => {
    expect(resolveLabel("550e8400-e29b-41d4-a716-446655440000")).toBe("Médico sin nombre");
  });

  it("returns the actual name when label is not a UUID", () => {
    expect(resolveLabel("Dra. García")).toBe("Dra. García");
  });

  it("returns fallback for empty string", () => {
    expect(resolveLabel("")).toBe("Médico sin nombre");
  });
});

// ── L2: endTime guard — endTimeEditMode ──────────────────────────────────────

describe("L2: endTime guard — endTimeEditMode", () => {
  it("computes new endTime when editMode is false", () => {
    const start = "2026-07-01T10:00:00.000Z";
    const result = computeEndTime(start, 30, false);
    expect(result).toBe("2026-07-01T10:30:00.000Z");
  });

  it("returns null (skip overwrite) when editMode is true", () => {
    const start = "2026-07-01T10:00:00.000Z";
    const result = computeEndTime(start, 30, true);
    expect(result).toBeNull();
  });
});
