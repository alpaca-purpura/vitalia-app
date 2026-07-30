// cap: clinics.lisa.doctores
// story-origin: vitalia-fase2-lisa-doctores
/**
 * SC-D3F-3 — formatRecurrenceSummary correctness tests.
 *
 * Verifies that the FE formatRecurrenceSummary function produces human summaries
 * matching the expected semantics per RN-D3F-1 (mirrors BE format_recurrence_summary).
 *
 * Coverage:
 *   - Preset "none" → "Bloque único"
 *   - Preset "daily" (7 days, interval=1) → "todos los días"
 *   - Preset "weekly" (1 day, interval=1) → "cada semana el {día}"
 *   - Preset "biweekly" (1 day, interval=2) → "cada 2 semanas el {día}"
 *   - Custom: Mon+Thu every 2 weeks × 8 → contains "lunes y jueves" + "8 veces"
 *   - Custom: 3 days weekly → list with "y"
 *   - Custom interval=3 → "cada 3 semanas"
 *   - End condition open_ended → "indefinidamente"
 *   - End condition end_date → "hasta el {date}"
 *   - End condition occurrences=1 → "1 vez" (singular)
 */

import { describe, it, expect } from "vitest";
import { formatRecurrenceSummary } from "../BloquePopover";

describe("SC-D3F-3 — formatRecurrenceSummary", () => {
  it('preset=none → "Bloque único"', () => {
    expect(
      formatRecurrenceSummary({
        repeatPreset: "none",
        daysOfWeek: [],
        interval: 1,
        endConditionKind: "open_ended",
      }),
    ).toBe("Bloque único");
  });

  it('preset=daily → "Se repite todos los días, indefinidamente"', () => {
    const result = formatRecurrenceSummary({
      repeatPreset: "daily",
      daysOfWeek: [0, 1, 2, 3, 4, 5, 6],
      interval: 1,
      endConditionKind: "open_ended",
    });
    expect(result).toContain("todos los días");
    expect(result).toContain("indefinidamente");
  });

  it('preset=weekly, Monday → "cada semana el lunes"', () => {
    const result = formatRecurrenceSummary({
      repeatPreset: "weekly",
      daysOfWeek: [0], // Monday
      interval: 1,
      endConditionKind: "open_ended",
    });
    expect(result).toContain("cada semana");
    expect(result).toContain("lunes");
    expect(result).toContain("indefinidamente");
  });

  it('preset=biweekly, Thursday → "cada 2 semanas el jueves"', () => {
    const result = formatRecurrenceSummary({
      repeatPreset: "biweekly",
      daysOfWeek: [3], // Thursday
      interval: 2,
      endConditionKind: "open_ended",
    });
    expect(result).toContain("cada 2 semanas");
    expect(result).toContain("jueves");
  });

  it("SC-D3F-3 core: Mon+Thu every 2 weeks × 8 → contains day names + count", () => {
    // RN-D3F-1: "Se repite cada 2 semanas los lunes y jueves, 8 veces"
    const result = formatRecurrenceSummary({
      repeatPreset: "custom",
      daysOfWeek: [0, 3], // Monday + Thursday
      interval: 2,
      endConditionKind: "occurrences",
      occurrences: 8,
    });
    expect(result).toContain("lunes");
    expect(result).toContain("jueves");
    expect(result).toContain("8 repeticiones");
    expect(result).toContain("cada 2 semanas");
  });

  it("3 days weekly: includes y before last day", () => {
    const result = formatRecurrenceSummary({
      repeatPreset: "custom",
      daysOfWeek: [0, 2, 4], // Monday, Wednesday, Friday
      interval: 1,
      endConditionKind: "open_ended",
    });
    expect(result).toContain("lunes");
    expect(result).toContain("miércoles");
    expect(result).toContain("viernes");
    expect(result).toContain(" y ");
  });

  it("custom interval=3 → 'cada 3 semanas'", () => {
    const result = formatRecurrenceSummary({
      repeatPreset: "custom",
      daysOfWeek: [1], // Tuesday
      interval: 3,
      endConditionKind: "open_ended",
    });
    expect(result).toContain("cada 3 semanas");
    expect(result).toContain("martes");
  });

  it("end_date → 'hasta el {date}'", () => {
    const result = formatRecurrenceSummary({
      repeatPreset: "weekly",
      daysOfWeek: [0],
      interval: 1,
      endConditionKind: "end_date",
      endDate: "2026-12-31",
    });
    expect(result).toContain("hasta el 2026-12-31");
  });

  it("occurrences=1 → singular '1 repetición'", () => {
    const result = formatRecurrenceSummary({
      repeatPreset: "weekly",
      daysOfWeek: [2],
      interval: 1,
      endConditionKind: "occurrences",
      occurrences: 1,
    });
    // bug7 round-6: "repeticiones" (ciclos del patrón), no "veces"
    expect(result).toContain("1 repetición");
    expect(result).not.toContain("1 repeticiones");
  });

  it("occurrences=4 → plural '4 repeticiones'", () => {
    const result = formatRecurrenceSummary({
      repeatPreset: "weekly",
      daysOfWeek: [4],
      interval: 1,
      endConditionKind: "occurrences",
      occurrences: 4,
    });
    expect(result).toContain("4 repeticiones");
  });

  it("2-day summary uses 'los X y Y' format (W1: plural uses 'los', not 'el')", () => {
    const result = formatRecurrenceSummary({
      repeatPreset: "custom",
      daysOfWeek: [0, 4], // Monday + Friday
      interval: 1,
      endConditionKind: "open_ended",
    });
    // BE outputs "los lunes y viernes" for plural days — FE must match (W1 fix)
    expect(result).toMatch(/los lunes y viernes/);
  });
});
